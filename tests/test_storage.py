from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

from fleet_policy.storage import PolicyStore


def test_migrations_are_idempotent_and_indexed(tmp_path):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    store.migrate()
    with store.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 1
        indexes = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='index'")}
    assert "idx_events_task_created" in indexes
    assert "idx_calls_task_sig" in indexes


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
    deleted = store.retention(90, 30, 365)
    assert deleted == {"events": 1, "call_history": 1, "approvals": 1}


def test_budget_recording_idempotent(tmp_path):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    assert store.add_budget("t", "tokens", 10, "same")
    assert not store.add_budget("t", "tokens", 10, "same")
    assert store.budget("t")["tokens"] == 10
