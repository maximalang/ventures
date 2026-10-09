"""v1.2.42 — built-in retention, verified archive, size guard, hot-path indexes.

Root cause (fleet-ops t_1d99b96b, 2026-10-07 incident): the policy event
store grew without bound (no retention, no size guard, no events(created_at)
index in the shipped schema), so window queries full-scanned the largest
table until deny-triage timed out. These tests lock the fix:

- schema v5 heals every install (fresh, legacy, hand-patched) idempotently;
- retention archives expired events to verified JSONL.gz + sha256 BEFORE any
  deletion, and is a no-op when nothing expired;
- the size guard warns at the soft cap and forces retention at the hard cap
  through the significant-event lane, deduplicated per UTC day;
- a broken maintenance path returns an error report and never raises.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from fleet_policy import cli, maintenance
from fleet_policy.maintenance import (
    CONSECUTIVE_FAILURES_KEY,
    LAST_FAILURE_KEY,
    LAST_RUN_KEY,
    maybe_run,
    resolved,
    verify_archive,
)
from fleet_policy.storage import PolicyStore


def _ts(days_ago: int) -> str:
    moment = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return moment.isoformat(timespec="seconds").replace("+00:00", "Z")


def _insert_events(store: PolicyStore, prefix: str, count: int, days_ago: int) -> None:
    with store.connect() as connection:
        connection.executemany(
            "INSERT INTO events VALUES(?,?,?,?,?,?,?)",
            [
                (f"{prefix}-{index}", "corr", "t", "deny", 0, json.dumps({"index": index}), _ts(days_ago))
                for index in range(count)
            ],
        )


def _event_count(store: PolicyStore) -> int:
    with store.connect() as connection:
        return int(connection.execute("SELECT COUNT(*) FROM events").fetchone()[0])


def _user_event_count(store: PolicyStore) -> int:
    """Events excluding the maintenance tick's own audit rows."""
    with store.connect() as connection:
        return int(connection.execute("SELECT COUNT(*) FROM events WHERE kind != 'maintenance_run'").fetchone()[0])


def _outbox_payloads(store: PolicyStore) -> list[dict]:
    return [json.loads(row["payload_json"]) for row in store.pending_notifications()]


def _config(**overrides) -> dict:
    return {"retention": {"events_days": 90, "call_history_days": 30, "approvals_days": 365, **overrides}}


# --- schema v5 / migration idempotency ----------------------------------------

def test_v5_heals_a_legacy_store_that_lost_the_index(tmp_path):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    with store.connect() as connection:
        connection.execute("DROP INDEX idx_events_created")
        connection.execute("DROP INDEX idx_events_kind_created")
        connection.execute("DELETE FROM schema_migrations WHERE version=5")
    store.migrate()
    store.migrate()
    with store.connect() as connection:
        indexes = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='index'")}
        markers = {row[0] for row in connection.execute("SELECT version FROM schema_migrations")}
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"idx_events_created", "idx_events_kind_created"} <= indexes
    assert 5 in markers
    assert "maintenance_state" in tables


def test_window_query_uses_the_created_index(tmp_path):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    _insert_events(store, "plan", 3000, days_ago=1)
    with store.connect() as connection:
        plan = connection.execute(
            "EXPLAIN QUERY PLAN SELECT event_id FROM events WHERE created_at > ?", ("2020-01-01",)
        ).fetchall()
    detail = " ".join(str(row[-1]) for row in plan)
    assert "idx_events_created" in detail


# --- retention: archive-before-delete, verified --------------------------------

def test_retention_archives_verifies_then_deletes(tmp_path):
    store = PolicyStore(tmp_path / ".state" / "fleet-policy.db")
    store.migrate()
    _insert_events(store, "old", 250, days_ago=120)
    _insert_events(store, "new", 50, days_ago=1)
    report = maybe_run(store, _config(), force=True, source="test")
    assert report["ran"] is True and "error" not in report
    assert report["archived_events"] == 250
    assert _user_event_count(store) == 50
    archive_dir = store.path.parent / "fleet-policy-archive"
    files = sorted(archive_dir.glob("events-*.jsonl.gz"))
    assert len(files) == 1
    sidecar = files[0].with_name(files[0].name + ".sha256").read_text(encoding="ascii").split()[0]
    assert sidecar == hashlib.sha256(files[0].read_bytes()).hexdigest()
    with gzip.open(files[0], "rt", encoding="utf-8") as stream:
        archived_ids = [json.loads(line)["event_id"] for line in stream]
    assert len(archived_ids) == 250
    assert {name.split("-")[0] for name in archived_ids} == {"old"}
    manifest = (archive_dir / "manifest.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(manifest) == 1
    entry = json.loads(manifest[0])
    assert entry["rows"] == 250 and entry["sha256"] == sidecar
    # remaining rows are the fresh ones
    with store.connect() as connection:
        remaining = {row[0] for row in connection.execute("SELECT event_id FROM events WHERE kind != 'maintenance_run'")}
    assert all(name.startswith("new-") for name in remaining)


def test_retention_is_idempotent_when_nothing_expired(tmp_path):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    _insert_events(store, "old", 100, days_ago=120)
    first = maybe_run(store, _config(), force=True, source="test")
    assert first["archived_events"] == 100
    archive_dir = store.path.parent / "fleet-policy-archive"
    files_after_first = sorted(archive_dir.glob("events-*.jsonl.gz"))
    second = maybe_run(store, _config(), force=True, source="test")
    assert second["archived_events"] == 0
    assert sorted(archive_dir.glob("events-*.jsonl.gz")) == files_after_first


def test_verify_archive_rejects_tampered_bytes(tmp_path):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    _insert_events(store, "old", 10, days_ago=120)
    report = maybe_run(store, _config(), force=True, source="test")
    assert report["archived_events"] == 10
    archive = next((store.path.parent / "fleet-policy-archive").glob("events-*.jsonl.gz"))
    ok, sha = verify_archive(archive, 10)
    assert ok and len(sha) == 64
    blob = bytearray(archive.read_bytes())
    blob[-8] ^= 0xFF  # corrupt the gzip tail (CRC region)
    archive.write_bytes(bytes(blob))
    ok, _ = verify_archive(archive, 10)
    assert not ok


def test_failed_verification_keeps_every_row(tmp_path, monkeypatch):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    _insert_events(store, "old", 40, days_ago=120)
    monkeypatch.setattr(maintenance, "verify_archive", lambda path, rows: (False, ""))
    report = maybe_run(store, _config(), force=True, source="test")
    assert _user_event_count(store) == 40
    assert report["archived_events"] == 0
    assert report["errors"], "verification failure must surface in the report"


# --- scheduling / throttling ----------------------------------------------------

def test_interval_throttle_and_force_bypass(tmp_path):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    first = maybe_run(store, _config(), source="test")
    assert first["ran"] is True
    second = maybe_run(store, _config(), source="test")
    assert second.get("skipped") == "interval" and second["ran"] is False
    third = maybe_run(store, _config(), force=True, source="test")
    assert third["ran"] is True
    assert store.maintenance_get(LAST_RUN_KEY) is not None


def test_maintenance_never_raises_on_broken_archive_root(tmp_path):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    _insert_events(store, "old", 5, days_ago=120)
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("occupied", encoding="utf-8")
    report = maybe_run(store, _config(archive_dir=str(blocker)), force=True, source="test")
    assert "error" in report
    assert _event_count(store) == 5  # fail closed: nothing deleted


# --- size guard ------------------------------------------------------------------

def test_soft_cap_warns_once_per_day_via_significant_lane(tmp_path, monkeypatch):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    monkeypatch.setattr(store, "db_size_bytes", lambda: 150 * 1024 * 1024)
    context = {"task_id": "t_ctx", "board": "fleet-ops"}
    first = maybe_run(store, _config(), force=True, context=context, source="test")
    assert "soft" in first["notices"]
    rows = _outbox_payloads(store)
    assert len(rows) == 1
    assert rows[0]["rule_id"] == "db_size_soft_cap"
    assert rows[0]["board"] == "fleet-ops" and rows[0]["task_id"] == "t_ctx"
    second = maybe_run(store, _config(), force=True, context=context, source="test")
    assert "soft" not in second["notices"]
    assert len(store.pending_notifications()) == 1


def test_hard_cap_forces_retention_past_the_interval(tmp_path, monkeypatch):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    assert maybe_run(store, _config(), source="test")["ran"] is True  # sets the interval mark
    _insert_events(store, "old", 20, days_ago=120)
    monkeypatch.setattr(store, "db_size_bytes", lambda: 400 * 1024 * 1024)
    context = {"task_id": "t_ctx", "board": "fleet-ops"}
    report = maybe_run(store, _config(), context=context, source="test")  # NOT forced by caller
    assert report["ran"] is True
    assert report["archived_events"] == 20
    assert "hard" in report["notices"] and "soft" not in report["notices"]
    rules = {payload["rule_id"] for payload in _outbox_payloads(store)}
    assert rules == {"db_size_hard_cap"}


def test_size_guard_stays_audit_only_without_a_binding(tmp_path, monkeypatch):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    monkeypatch.setattr(store, "db_size_bytes", lambda: 500 * 1024 * 1024)
    config = _config(notify_board="fleet-ops", notify_task_id="")
    report = maybe_run(store, config, force=True, context=None, source="test")
    assert report["ran"] is True
    assert store.pending_notifications() == []  # no undeliverable outbox rows


# --- bounded growth under a simulated dispatcher storm ---------------------------

def test_thirty_day_storm_stays_bounded(tmp_path):
    store = PolicyStore(tmp_path / ".state" / "fleet-policy.db")
    store.migrate()
    per_day = 2000
    # Keep/expiry rows sit >= 2 days away from the 14-day cutoff so the
    # second-resolution timestamp boundary can never flake the split.
    keep_days = range(1, 14)
    drop_days = range(16, 32)
    with store.connect() as connection:
        for day in list(keep_days) + list(drop_days):
            connection.executemany(
                "INSERT INTO events VALUES(?,?,?,?,?,?,?)",
                [
                    (f"storm-{day}-{index}", "c", "t", "deny", 0, json.dumps({"i": index}), _ts(day))
                    for index in range(per_day)
                ],
            )
    assert _event_count(store) == (len(keep_days) + len(drop_days)) * per_day
    report = maybe_run(store, _config(events_days=14), force=True, source="test")
    assert "error" not in report
    assert report["archived_events"] == len(drop_days) * per_day
    assert _user_event_count(store) == len(keep_days) * per_day
    assert store.db_size_bytes() < 100 * 1024 * 1024  # soft cap, by a wide margin
    archive_dir = store.path.parent / "fleet-policy-archive"
    archived_rows = 0
    for file in archive_dir.glob("events-*.jsonl.gz"):
        with gzip.open(file, "rt", encoding="utf-8") as stream:
            archived_rows += sum(1 for _ in stream)
    assert archived_rows == len(drop_days) * per_day


# --- QA boundary locks (PR #63 NO-GO F1-F3, t_218bc548 comment 6212) -----------

def _auto_vacuum_mode(path: Path) -> int:
    with sqlite3.connect(path) as connection:
        return int(connection.execute("PRAGMA auto_vacuum").fetchone()[0])


def _fill_and_drain_events(store: PolicyStore, count: int) -> None:
    blob = json.dumps({"payload": "x" * 512})
    with store.connect() as connection:
        connection.executemany(
            "INSERT INTO events VALUES(?,?,?,?,?,?,?)",
            [(f"fat-{index}", "corr", "t", "deny", 0, blob, _ts(1)) for index in range(count)],
        )
        connection.execute("DELETE FROM events")


def test_fresh_store_runs_incremental_auto_vacuum(tmp_path):
    path = tmp_path / "fresh.db"
    PolicyStore(path).migrate()
    assert _auto_vacuum_mode(path) == 2


def test_full_vacuum_converts_a_legacy_store_and_enables_reclamation(tmp_path):
    """F1: a legacy auto_vacuum=0 store must converge to INCREMENTAL through
    the advertised one-time conversion (migrate + operator full vacuum), and
    subsequent incremental_vacuum must physically return pages — the bounded
    -growth claim for legacy installs depends on it."""
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE legacy_marker(id INTEGER)")
        assert int(connection.execute("PRAGMA auto_vacuum").fetchone()[0]) == 0
    store = PolicyStore(path)
    store.migrate()
    # migrate() only stages the mode on its own connection; the legacy store
    # stays NONE until the operator full vacuum commits it.
    assert _auto_vacuum_mode(path) == 0
    store.full_vacuum()
    assert _auto_vacuum_mode(path) == 2
    _fill_and_drain_events(store, 2000)
    freelist_before = store.freelist_pages()
    assert freelist_before > 0
    store.wal_checkpoint_truncate()
    size_before = path.stat().st_size
    store.incremental_vacuum(freelist_before)
    store.wal_checkpoint_truncate()
    assert store.freelist_pages() < freelist_before
    assert path.stat().st_size < size_before


def test_incremental_vacuum_noops_on_a_legacy_mode_none_store(tmp_path):
    """Negative control for the F1 conversion proof: without full_vacuum the
    same delete leaves the freed pages trapped in mode NONE — exactly the
    defect F1 made permanent for legacy installs."""
    path = tmp_path / "none.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE legacy_marker(id INTEGER)")
    store = PolicyStore(path)
    store.migrate()
    assert _auto_vacuum_mode(path) == 0
    _fill_and_drain_events(store, 2000)
    freelist_before = store.freelist_pages()
    assert freelist_before > 0
    store.incremental_vacuum(freelist_before)
    assert store.freelist_pages() == freelist_before


def test_maintenance_cli_fails_on_archive_verification_error(runtime, monkeypatch, capsys):
    """F2: a maintenance run whose report carries errors is failed
    maintenance — the process exit status must be nonzero."""
    _insert_events(runtime.store, "expired", 1, days_ago=120)
    monkeypatch.setattr(maintenance, "verify_archive", lambda path, rows: (False, "injected-failure"))
    monkeypatch.setattr(cli, "FleetPolicyRuntime", lambda root: runtime)
    exit_code = cli.main(["--root", str(runtime.root), "maintenance"])
    report = json.loads(capsys.readouterr().out)
    assert report["errors"], report
    assert report["archived_events"] == 0
    assert exit_code == 1
    # fail closed: the expired row is retained and the success throttle was
    # NOT consumed by the failed run.
    assert _user_event_count(runtime.store) == 1
    assert runtime.store.maintenance_get(LAST_RUN_KEY) is None


def test_failed_archive_does_not_consume_the_success_throttle(tmp_path, monkeypatch):
    """F3: a failed archival is retried on the next tick (the source contract
    on the fail-closed path), not throttled away by a success stamp."""
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    _insert_events(store, "old", 3, days_ago=120)
    real_verify = maintenance.verify_archive
    monkeypatch.setattr(maintenance, "verify_archive", lambda path, rows: (False, "injected-failure"))
    moment = datetime.now(timezone.utc)
    first = maybe_run(store, _config(), now=moment, source="test-failure")
    assert first["ran"] is True and first["errors"]
    # the failed attempt is ledgered for observability, the success throttle
    # is not stamped
    assert first["consecutive_failures"] == 1
    assert store.maintenance_get(LAST_RUN_KEY) is None
    assert store.maintenance_get(CONSECUTIVE_FAILURES_KEY) == "1"
    assert store.maintenance_get(LAST_FAILURE_KEY) is not None
    monkeypatch.setattr(maintenance, "verify_archive", real_verify)
    second = maybe_run(store, _config(), now=moment + timedelta(minutes=1), source="test-recovery")
    assert second["ran"] is True
    assert second["archived_events"] == 3
    assert store.maintenance_get(LAST_RUN_KEY) is not None
    assert store.maintenance_get(CONSECUTIVE_FAILURES_KEY) == "0"

def test_maybe_run_preserve_state_never_deletes_state_rows(tmp_path):
    """v1.2.44 (t_40022daf D2-b, QA F1): the one-time operator prune posture
    (preserve_state=True) drains the ledger backlog but never deletes from
    the protected state tables — even rows older than every horizon."""
    store = PolicyStore(tmp_path / ".state" / "fleet-policy.db")
    store.migrate()
    old = _ts(500)
    _insert_events(store, "old", 10, days_ago=120)
    with store.connect() as connection:
        connection.execute("INSERT INTO task_state VALUES(?,?,?)", ("old-task", 2, old))
        connection.execute("INSERT INTO run_state VALUES(?,?,?,?)", ("old-task", "rk", 1, old))
        connection.execute(
            "INSERT INTO approvals(rule_key,task_id,action,target,args_hash,status,created_at) VALUES(?,?,?,?,?,?,?)",
            ("old-appr", "t", "terminal", "deploy", "h", "rejected", old),
        )
        connection.execute(
            "INSERT INTO notification_outbox(event_id,payload_json,status,created_at) VALUES(?,?,?,?)",
            ("old-note", "{}", "failed", old),
        )
        connection.execute(
            "INSERT INTO call_history VALUES(?,?,?,?,?,?)", ("old-call", "t", "sig", None, 1, old)
        )
    report = maybe_run(store, _config(), force=True, source="test", preserve_state=True)
    assert report["ran"] is True and "error" not in report
    assert report["archived_events"] == 10
    assert report["deleted"]["call_history"] == 1
    assert report["deleted"]["approvals"] == 0
    assert report["deleted"]["task_state"] == 0
    assert report["deleted"]["notification_outbox"] == 0
    with store.connect() as connection:
        for table in ("task_state", "run_state", "approvals", "notification_outbox"):
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 1
