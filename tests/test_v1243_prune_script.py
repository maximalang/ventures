"""v1.2.43 — tests for scripts/prune_policy_db.py (card t_40022daf D2-b).

The one-time operator prune must back up the live store (byte snapshot +
sha256 MANIFEST) BEFORE any deletion, archive expired events to verified
JSONL.gz, delete, VACUUM, and re-verify every archive sidecar afterwards.
All tests run against a synthetic store in tmp_path — the live store is a
protected path and is never touched here.
"""
from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import shutil
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "prune_policy_db.py"
SOURCE_ROOT = Path(__file__).parents[1]


def load_module():
    spec = importlib.util.spec_from_file_location("prune_policy_db_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def fake_root(tmp_path):
    root = tmp_path / "ventures"
    (root / "config").mkdir(parents=True)
    shutil.copy(SOURCE_ROOT / "config" / "fleet-policy.yaml", root / "config" / "fleet-policy.yaml")
    module = load_module()
    from fleet_policy.runtime import FleetPolicyRuntime

    runtime = FleetPolicyRuntime(root)
    old = (datetime.now(timezone.utc) - timedelta(days=200)).isoformat(timespec="seconds").replace("+00:00", "Z")
    new = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(timespec="seconds").replace("+00:00", "Z")
    with runtime.store.connect() as db:
        for index in range(50):
            db.execute(
                "INSERT INTO events VALUES(?,?,?,?,0,?,?)",
                (f"old-{index:03d}", f"corr-{index}", "t_old", "policy_decision", "{}", old),
            )
        for index in range(5):
            db.execute(
                "INSERT INTO events VALUES(?,?,?,?,0,?,?)",
                (f"new-{index:03d}", f"corr-n{index}", "t_new", "policy_decision", "{}", new),
            )
        db.execute(
            "INSERT INTO call_history VALUES(?,?,?,?,?,?)",
            ("call-old-1", "t_old", "sig", None, 1, old),
        )
    return root


def test_dry_run_touches_nothing(fake_root):
    module = load_module()
    db_path = fake_root / ".state" / "fleet-policy.db"
    size_before = db_path.stat().st_size
    report = module.run(fake_root, dry_run=True)
    assert report["dry_run"] is True
    assert report["pre"]["counts"]["events"] == 55
    assert len(report["steps"]) == 4
    assert db_path.stat().st_size == size_before
    assert not (fake_root / ".state" / "fleet-policy-backups").exists()


def test_prune_backup_archive_delete_vacuum_verify(fake_root):
    module = load_module()
    db_path = fake_root / ".state" / "fleet-policy.db"
    report = module.run(fake_root, dry_run=False)

    assert "aborted" not in report, report.get("aborted")

    # backup + manifest
    backup_dir = Path(report["backup_dir"])
    backup_db = backup_dir / "fleet-policy.db"
    assert backup_db.is_file()
    manifest = json.loads((backup_dir / "MANIFEST.json").read_text(encoding="utf-8"))
    entry = next(item for item in manifest["artifacts"] if item["file"] == "fleet-policy.db")
    digest = hashlib.sha256(backup_db.read_bytes()).hexdigest()
    assert entry["sha256"] == digest
    sidecar_lines = (backup_dir / "MANIFEST.sha256").read_text(encoding="ascii")
    assert digest in sidecar_lines
    # the backup preserves the pre-prune rows
    with sqlite3.connect(str(backup_db)) as backup:
        assert backup.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 55

    # expired events archived then deleted; fresh rows stay. The forced
    # maintenance tick itself writes one audit event (kind=maintenance_run),
    # so assertions key on the seeded id prefixes, not the absolute count.
    with sqlite3.connect(str(db_path)) as db:
        assert db.execute("SELECT COUNT(*) FROM events WHERE event_id LIKE 'new-%'").fetchone()[0] == 5
        assert db.execute("SELECT COUNT(*) FROM events WHERE event_id LIKE 'old-%'").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM call_history").fetchone()[0] == 0

    # archive files are valid gzip JSONL with matching sidecars
    archive_dir = fake_root / ".state" / "fleet-policy-archive"
    archives = sorted(archive_dir.glob("events-*.jsonl.gz"))
    assert archives, "expected at least one archive batch"
    archived_rows = 0
    for path in archives:
        sidecar = path.with_name(path.name + ".sha256").read_text(encoding="ascii").split()[0]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == sidecar
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            archived_rows += sum(1 for _line in stream)
    assert archived_rows == 50
    assert (archive_dir / "manifest.jsonl").is_file()

    # post-run re-verification recorded in the report and all-ok
    assert report["archive_reverify"]
    assert all(item["ok"] for item in report["archive_reverify"])
    # counts delta: 50 expired rows deleted minus the one maintenance_run
    # audit event the tick writes itself = 49.
    assert report["counts_delta"]["events"] == 49
    assert report["size_delta_bytes"] >= 0
    assert (backup_dir / "PRUNE-REPORT.json").is_file()


def test_prune_preserves_protected_state_tables_exactly(fake_root):
    """QA F1 (t_40022daf D2-b): the one-time prune must never delete from the
    protected state tables — even rows far older than every retention
    horizon (500 days here, beyond approvals_days=365). Asserts exact row
    CONTENT preservation (not just counts) plus the report's
    state_preservation assertion surface."""
    module = load_module()
    db_path = fake_root / ".state" / "fleet-policy.db"
    ancient = (datetime.now(timezone.utc) - timedelta(days=500)).isoformat(timespec="seconds").replace("+00:00", "Z")
    protected_tables = ("task_state", "run_state", "approvals", "notification_outbox")

    def dump(db):
        snapshot = {
            table: db.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in protected_tables
        }
        snapshot["maintenance_probe"] = db.execute(
            "SELECT value FROM maintenance_state WHERE key='custom_probe'"
        ).fetchone()
        return snapshot

    with sqlite3.connect(str(db_path)) as db:
        db.execute("INSERT INTO task_state VALUES(?,?,?)", ("ancient-task", 3, ancient))
        db.execute("INSERT INTO run_state VALUES(?,?,?,?)", ("ancient-task", "rk-1", 1, ancient))
        db.execute(
            "INSERT INTO approvals(rule_key,task_id,action,target,args_hash,status,created_at) VALUES(?,?,?,?,?,?,?)",
            ("ancient-approval", "t", "terminal", "deploy", "h", "rejected", ancient),
        )
        db.execute(
            "INSERT INTO notification_outbox(event_id,payload_json,status,created_at) VALUES(?,?,?,?)",
            ("ancient-note-failed", "{}", "failed", ancient),
        )
        db.execute(
            "INSERT INTO notification_outbox(event_id,payload_json,status,created_at) VALUES(?,?,?,?)",
            ("ancient-note-pending", "{}", "pending", ancient),
        )
        db.execute("INSERT INTO maintenance_state VALUES(?,?,?)", ("custom_probe", "keep-me", ancient))
        before = dump(db)

    report = module.run(fake_root, dry_run=False)
    assert "aborted" not in report, report.get("aborted")

    with sqlite3.connect(str(db_path)) as db:
        after = dump(db)
    # exact content preservation, not just row counts
    assert after == before

    preservation = report["state_preservation"]
    assert set(preservation) == set(protected_tables)
    assert all(check["ok"] for check in preservation.values())
    assert all(check["pre"] == check["post"] for check in preservation.values())
    assert preservation["approvals"]["pre"] == 1
    assert preservation["notification_outbox"]["pre"] == 2
    assert preservation["task_state"]["pre"] == 1
    assert preservation["run_state"]["pre"] == 1
    # the ledger prune still happened (the fixture's 200-day-old call row)
    assert report["maintenance"]["deleted"]["call_history"] == 1
    # and the protected tables report zero deletions under preserve_state
    assert report["maintenance"]["deleted"]["approvals"] == 0
    assert report["maintenance"]["deleted"]["task_state"] == 0
    assert report["maintenance"]["deleted"]["notification_outbox"] == 0

def test_prune_state_preservation_tripwire_aborts(fake_root, monkeypatch):
    """The report's assertion surface is a real tripwire: if post-prune
    protected counts ever move, the run must report aborted (exit 1)."""
    module = load_module()
    db_path = fake_root / ".state" / "fleet-policy.db"
    with sqlite3.connect(str(db_path)) as db:
        db.execute(
            "INSERT INTO task_state VALUES(?,?,?)",
            ("doomed-task", 1, datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")),
        )
    real_preservation = module._state_preservation

    def lying_preservation(pre_counts, post_counts):
        result = real_preservation(pre_counts, post_counts)
        result["task_state"] = {"pre": 1, "post": 0, "ok": False}
        return result

    monkeypatch.setattr(module, "_state_preservation", lying_preservation)
    report = module.run(fake_root, dry_run=False)
    assert report.get("aborted", "").startswith("state preservation violated for: task_state")
    assert report["state_preservation"]["task_state"]["ok"] is False


def test_prune_aborts_cleanly_when_archive_dir_unwritable(fake_root, monkeypatch):
    module = load_module()
    from fleet_policy import maintenance

    def broken_write(rows, archive_dir, seq):
        raise OSError("simulated archive failure")

    monkeypatch.setattr(maintenance, "_write_archive_batch", broken_write)
    db_path = fake_root / ".state" / "fleet-policy.db"
    report = module.run(fake_root, dry_run=False)
    # maintenance surfaced the failure; the prune stopped before vacuum and
    # reported abort; the rows are still present (fail-closed archive path).
    assert report.get("aborted") or report["maintenance"].get("error") or report["maintenance"].get("errors")
    with sqlite3.connect(str(db_path)) as db:
        assert db.execute("SELECT COUNT(*) FROM events").fetchone()[0] >= 50
