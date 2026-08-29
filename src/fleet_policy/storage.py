from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events(
  event_id TEXT PRIMARY KEY, correlation_id TEXT NOT NULL, task_id TEXT, kind TEXT NOT NULL,
  significant INTEGER NOT NULL DEFAULT 0, payload_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_task_created ON events(task_id, created_at);
CREATE TABLE IF NOT EXISTS budget_ledger(
  task_id TEXT NOT NULL, metric TEXT NOT NULL, amount INTEGER NOT NULL, event_id TEXT NOT NULL,
  created_at TEXT NOT NULL, PRIMARY KEY(task_id, metric, event_id)
);
CREATE INDEX IF NOT EXISTS idx_budget_task_metric ON budget_ledger(task_id, metric);
CREATE TABLE IF NOT EXISTS call_history(
  event_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, call_signature TEXT NOT NULL,
  failure_signature TEXT, success INTEGER, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_calls_task_sig ON call_history(task_id, call_signature, created_at);
CREATE INDEX IF NOT EXISTS idx_calls_task_failure ON call_history(task_id, failure_signature, created_at);
CREATE TABLE IF NOT EXISTS task_state(
  task_id TEXT PRIMARY KEY, idle_turns INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS approvals(
  rule_key TEXT PRIMARY KEY, task_id TEXT NOT NULL, action TEXT NOT NULL, target TEXT NOT NULL,
  args_hash TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
  decided_at TEXT, consumed_at TEXT, decided_by TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_approval_binding ON approvals(task_id, action, target, args_hash);
CREATE TABLE IF NOT EXISTS notification_outbox(
  event_id TEXT PRIMARY KEY, payload_json TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT NOT NULL, sent_at TEXT
);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class PolicyStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=10000")
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def migrate(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)
            connection.execute("INSERT OR IGNORE INTO schema_migrations(version,applied_at) VALUES(1,?)", (utc_now(),))

    def record_event(self, event_id: str, correlation_id: str, task_id: str | None, kind: str,
                     payload: dict[str, Any], significant: bool = False) -> bool:
        from .redaction import stable_json
        encoded = stable_json(payload)
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO events(event_id,correlation_id,task_id,kind,significant,payload_json,created_at) VALUES(?,?,?,?,?,?,?)",
                (event_id, correlation_id, task_id, kind, int(significant), encoded, utc_now()),
            )
            if cursor.rowcount and significant:
                connection.execute(
                    "INSERT OR IGNORE INTO notification_outbox(event_id,payload_json,created_at) VALUES(?,?,?)",
                    (event_id, encoded, utc_now()),
                )
            return cursor.rowcount == 1

    def add_budget(self, task_id: str, metric: str, amount: int, event_id: str) -> bool:
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO budget_ledger(task_id,metric,amount,event_id,created_at) VALUES(?,?,?,?,?)",
                (task_id, metric, int(amount), event_id, utc_now()),
            )
            return cursor.rowcount == 1

    def budget(self, task_id: str) -> dict[str, int]:
        result = {"tokens": 0, "tool_calls": 0, "retries": 0}
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT metric,SUM(amount) AS total FROM budget_ledger WHERE task_id=? GROUP BY metric", (task_id,)
            )
            for row in rows:
                result[str(row["metric"])] = int(row["total"] or 0)
        return result

    def add_call(self, event_id: str, task_id: str, call_signature: str,
                 failure_signature: str | None, success: bool) -> bool:
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO call_history(event_id,task_id,call_signature,failure_signature,success,created_at) VALUES(?,?,?,?,?,?)",
                (event_id, task_id, call_signature, failure_signature, int(success), utc_now()),
            )
            return cursor.rowcount == 1

    def count_signature(self, task_id: str, column: str, value: str) -> int:
        if column not in {"call_signature", "failure_signature"}:
            raise ValueError("unsupported signature column")
        with self.connect() as connection:
            row = connection.execute(
                f"SELECT COUNT(*) AS count FROM call_history WHERE task_id=? AND {column}=?", (task_id, value)
            ).fetchone()
            return int(row["count"])

    def set_idle_turns(self, task_id: str, *, increment: bool) -> int:
        with self.connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO task_state(task_id,idle_turns,updated_at) VALUES(?,0,?)", (task_id, utc_now())
            )
            if increment:
                connection.execute("UPDATE task_state SET idle_turns=idle_turns+1,updated_at=? WHERE task_id=?", (utc_now(), task_id))
            else:
                connection.execute("UPDATE task_state SET idle_turns=0,updated_at=? WHERE task_id=?", (utc_now(), task_id))
            row = connection.execute("SELECT idle_turns FROM task_state WHERE task_id=?", (task_id,)).fetchone()
            return int(row["idle_turns"])

    def ensure_approval(self, rule_key: str, task_id: str, action: str, target: str, hashed_args: str) -> bool:
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO approvals(rule_key,task_id,action,target,args_hash,status,created_at) VALUES(?,?,?,?,?,'pending',?)",
                (rule_key, task_id, action, target, hashed_args, utc_now()),
            )
            return cursor.rowcount == 1

    def decide_approval(self, rule_key: str, approved: bool, decided_by: str) -> bool:
        status = "approved" if approved else "rejected"
        with self.connect() as connection:
            cursor = connection.execute(
                "UPDATE approvals SET status=?,decided_at=?,decided_by=? WHERE rule_key=? AND status='pending'",
                (status, utc_now(), decided_by, rule_key),
            )
            return cursor.rowcount == 1

    def consume_exact_approval(self, task_id: str, action: str, target: str, hashed_args: str) -> bool:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT rule_key FROM approvals WHERE task_id=? AND action=? AND target=? AND args_hash=? AND status='approved'",
                (task_id, action, target, hashed_args),
            ).fetchone()
            if row is None:
                return False
            cursor = connection.execute(
                "UPDATE approvals SET status='consumed',consumed_at=? WHERE rule_key=? AND status='approved'",
                (utc_now(), row["rule_key"]),
            )
            return cursor.rowcount == 1

    def approval(self, rule_key: str) -> sqlite3.Row | None:
        with self.connect() as connection:
            return connection.execute("SELECT * FROM approvals WHERE rule_key=?", (rule_key,)).fetchone()

    def pending_notifications(self) -> list[sqlite3.Row]:
        with self.connect() as connection:
            return list(connection.execute("SELECT * FROM notification_outbox WHERE status='pending' ORDER BY created_at,event_id"))

    def mark_notification(self, event_id: str, status: str) -> bool:
        with self.connect() as connection:
            cursor = connection.execute(
                "UPDATE notification_outbox SET status=?,sent_at=? WHERE event_id=? AND status='pending'",
                (status, utc_now(), event_id),
            )
            return cursor.rowcount == 1

    def retention(self, event_days: int, call_days: int, approval_days: int,
                  now: datetime | None = None) -> dict[str, int]:
        now = now or datetime.now(timezone.utc)
        deleted: dict[str, int] = {}
        with self.connect() as connection:
            for table, days in (("events", event_days), ("call_history", call_days), ("approvals", approval_days)):
                cutoff = (now - timedelta(days=days)).isoformat(timespec="seconds").replace("+00:00", "Z")
                cursor = connection.execute(f"DELETE FROM {table} WHERE created_at < ?", (cutoff,))
                deleted[table] = cursor.rowcount
        return deleted
