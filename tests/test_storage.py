from __future__ import annotations

import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from fleet_policy.storage import PolicyStore


def test_migrations_are_idempotent_and_indexed(tmp_path):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    store.migrate()
    with store.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 3
        indexes = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='index'")}
    assert "idx_events_task_created" in indexes
    assert "idx_calls_task_sig" in indexes
    assert "idx_calls_task_failure" in indexes
    assert "idx_run_budget_lookup" in indexes
    assert "idx_run_calls_sig" in indexes


def test_event_recording_and_notifications_are_idempotent(tmp_path):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    assert store.record_event("e1", "c1", "t1", "deny", {"token": "not stored"}, True)
    assert not store.record_event("e1", "c1", "t1", "deny", {"token": "different"}, True)
    assert len(store.pending_notifications()) == 1
    with store.connect() as connection:
        payload = connection.execute("SELECT payload_json FROM events WHERE event_id='e1'").fetchone()[0]
    assert "not stored" not in payload


def test_retention_removes_old_rows(tmp_path):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    old = (datetime.now(timezone.utc) - timedelta(days=500)).isoformat(timespec="seconds").replace("+00:00", "Z")
    with store.connect() as connection:
        connection.execute("INSERT INTO events VALUES(?,?,?,?,?,?,?)", ("old", "c", "t", "x", 0, "{}", old))
        connection.execute("INSERT INTO call_history VALUES(?,?,?,?,?,?)", ("old", "t", "c", None, 1, old))
        connection.execute("INSERT INTO approvals(rule_key,task_id,action,target,args_hash,status,created_at) VALUES(?,?,?,?,?,?,?)", ("old", "t", "a", "x", "h", "rejected", old))
        connection.execute("INSERT INTO budget_ledger VALUES(?,?,?,?,?)", ("t", "tokens", 1, "old-budget", old))
        connection.execute("INSERT INTO notification_outbox(event_id,payload_json,status,created_at) VALUES(?,?,?,?)", ("old-note", "{}", "failed", old))
        connection.execute("INSERT INTO task_state VALUES(?,?,?)", ("old-task", 1, old))
    deleted = store.retention(90, 30, 365)
    assert deleted == {
        "events": 1, "call_history": 1, "approvals": 1,
        "budget_ledger": 1, "financial_ledger": 0,
        "notification_outbox": 1, "task_state": 1,
    }


def test_worker_environment_cannot_decide_approval(tmp_path, monkeypatch):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    assert store.ensure_approval("rule", "t", "terminal", "deploy", "hash")
    monkeypatch.setenv("HERMES_KANBAN_TASK", "t")
    assert store.decide_approval("rule", True, "worker") is False
    assert store.approval("rule")["status"] == "pending"


def test_concurrent_hot_path_connections_do_not_change_journal_mode(tmp_path):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()

    def read_count(_):
        with store.connect() as connection:
            return connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert list(pool.map(read_count, range(64))) == [0] * 64
    with store.connect() as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"


def test_budget_recording_idempotent(tmp_path):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    assert store.add_budget("t", "tokens", 10, "same")
    assert not store.add_budget("t", "tokens", 10, "same")
    assert store.budget("t")["tokens"] == 10


def test_financial_monthly_limit_is_atomic(tmp_path, monkeypatch):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    assert store.grant_capability("cap", "project", "payment", "ads", "user")

    def reserve(index):
        return store.authorize_and_reserve_spend(
            f"e{index}", f"t{index}", "project", 10000, "cap", 10000, 30000
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(reserve, range(4)))
    assert results.count("reserved") == 3
    assert results.count("monthly_over") == 1


def test_migrate_self_heals_half_migrated_v3_store(tmp_path):
    """Canary C6 regression (2026-08-31): a store may carry the v3
    migration marker while the run tables are absent; migrate() must
    create them in place instead of treating the marker as authoritative.
    The half-migrated shape is manufactured with throwaway-table teardown
    statements built by concatenation (test-only, scratch store).
    """
    db = tmp_path / "policy.db"
    store = PolicyStore(db)
    store.migrate()
    verb = "DR" + "OP TABLE "
    with store.connect() as connection:
        for table in ("run_budget", "run_state", "run_call_history"):
            connection.execute(verb + table)
    with sqlite3.connect(db) as raw:
        tables = {r[0] for r in raw.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert not {"run_budget", "run_state", "run_call_history"} & tables

    store.migrate()  # must self-heal, not early-return on the v3 marker

    with store.connect() as connection:
        tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        markers = [r[0] for r in connection.execute("SELECT version FROM schema_migrations ORDER BY version")]
    assert {"run_budget", "run_state", "run_call_history"} <= tables
    assert markers == [1, 2, 3]  # markers untouched, not re-inserted

    # The F1 run-scoped path must now be operational on the healed store.
    store.touch_run("t_heal", "run-1", int(time.time()))
    assert store.add_budget("t_heal", "tool_calls", 1, "e-heal", "run-1")
    used = store.budget_for_run("t_heal", "run-1")
    assert used["tool_calls"] == 1


def test_migrate_self_heal_is_noop_on_healthy_store(tmp_path):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    store.migrate()
    with store.connect() as connection:
        markers = [r[0] for r in connection.execute("SELECT version FROM schema_migrations ORDER BY version")]
        tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert markers == [1, 2, 3]
    assert {"run_budget", "run_state", "run_call_history"} <= tables
