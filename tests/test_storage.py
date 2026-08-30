from __future__ import annotations

import sqlite3
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
