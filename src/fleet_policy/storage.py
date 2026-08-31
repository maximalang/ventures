from __future__ import annotations

import json
import os
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
CREATE TABLE IF NOT EXISTS capabilities(
  capability_id TEXT PRIMARY KEY, project TEXT NOT NULL, kind TEXT NOT NULL,
  scope TEXT NOT NULL, status TEXT NOT NULL, granted_by TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_capabilities_project_status ON capabilities(project,status);
CREATE TABLE IF NOT EXISTS financial_ledger(
  event_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, project TEXT NOT NULL,
  amount_rub INTEGER NOT NULL, capability_id TEXT NOT NULL, status TEXT NOT NULL,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_financial_project_month ON financial_ledger(project,created_at,status);
"""

# v1.2 F1: dispatch-run-scoped accounting. The cumulative budget_ledger and
# call_history stay as the audit trail; enforcement reads run_budget and
# run_state for the CURRENT dispatch run only.
SCHEMA_V3 = """
CREATE TABLE IF NOT EXISTS run_budget(
  task_id TEXT NOT NULL, run_key TEXT NOT NULL, metric TEXT NOT NULL,
  amount INTEGER NOT NULL, event_id TEXT NOT NULL, created_at TEXT NOT NULL,
  PRIMARY KEY(task_id, run_key, metric, event_id)
);
CREATE INDEX IF NOT EXISTS idx_run_budget_lookup ON run_budget(task_id, run_key, metric);
CREATE TABLE IF NOT EXISTS run_state(
  task_id TEXT PRIMARY KEY, run_key TEXT NOT NULL, claimed_at INTEGER NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS run_call_history(
  event_id TEXT NOT NULL, task_id TEXT NOT NULL, run_key TEXT NOT NULL,
  call_signature TEXT NOT NULL, failure_signature TEXT, success INTEGER,
  created_at TEXT NOT NULL, PRIMARY KEY(task_id, run_key, event_id)
);
CREATE INDEX IF NOT EXISTS idx_run_calls_sig ON run_call_history(task_id,run_key,call_signature,created_at);
CREATE INDEX IF NOT EXISTS idx_run_calls_failure ON run_call_history(task_id,run_key,failure_signature,created_at);
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
        connection.execute("PRAGMA busy_timeout=10000")
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    #: Tables guaranteed by SCHEMA_V3. A store can carry the v3 migration
    #: marker while some of these tables are absent (half-applied DDL left
    #: the database permanently half-migrated); migrate() self-heals that
    #: shape idempotently. Regression: post-release canary C6, 2026-08-31.
    V3_TABLES = ("run_budget", "run_state", "run_call_history")

    def migrate(self) -> None:
        with self.connect() as connection:
            # Journal mode is a database-level setup operation. Re-running it on
            # every hot-path connection requires an exclusive lock and can make
            # concurrent workers exceed Hermes' 30s pre-tool hook timeout.
            connection.execute("PRAGMA journal_mode=WAL")
            row = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'").fetchone()
            if row is not None and connection.execute("SELECT version FROM schema_migrations WHERE version=3").fetchone() is not None:
                self._heal_v3_tables(connection)
                return
            connection.executescript(SCHEMA)
            connection.execute("INSERT OR IGNORE INTO schema_migrations(version,applied_at) VALUES(1,?)", (utc_now(),))
            connection.execute("INSERT OR IGNORE INTO schema_migrations(version,applied_at) VALUES(2,?)", (utc_now(),))
            connection.executescript(SCHEMA_V3)
            connection.execute("INSERT OR IGNORE INTO schema_migrations(version,applied_at) VALUES(3,?)", (utc_now(),))

    def _heal_v3_tables(self, connection: sqlite3.Connection) -> None:
        """Create any SCHEMA_V3 tables missing despite the v3 marker.

        Idempotent IF NOT EXISTS DDL only — never drops or rewrites rows,
        so it is safe to run on every connection of a healthy store (cheap
        sqlite_master read first) and heals half-migrated stores in place.
        """
        present = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if all(name in present for name in self.V3_TABLES):
            return
        connection.executescript(SCHEMA_V3)

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

    def delete_event(self, event_id: str) -> bool:
        """Release a non-significant idempotency claim after failed delivery."""
        with self.connect() as connection:
            cursor = connection.execute(
                "DELETE FROM events WHERE event_id=? AND significant=0", (event_id,)
            )
            return cursor.rowcount == 1

    # ------------------------------------------------------------------ budgets
    def add_budget(self, task_id: str, metric: str, amount: int, event_id: str, run_key: str | None = None) -> bool:
        """Record spend. With run_key: current-run ledger (enforced). Without:
        cumulative legacy ledger (audit trail; still enforced for backward
        compatibility with rows recorded before v1.2)."""
        with self.connect() as connection:
            if run_key:
                cursor = connection.execute(
                    "INSERT OR IGNORE INTO run_budget(task_id,run_key,metric,amount,event_id,created_at) VALUES(?,?,?,?,?,?)",
                    (task_id, run_key, metric, int(amount), event_id, utc_now()),
                )
            else:
                cursor = connection.execute(
                    "INSERT OR IGNORE INTO budget_ledger(task_id,metric,amount,event_id,created_at) VALUES(?,?,?,?,?)",
                    (task_id, metric, int(amount), event_id, utc_now()),
                )
            return cursor.rowcount == 1

    def budget(self, task_id: str) -> dict[str, int]:
        """Cumulative audit view across all runs."""
        result = {"tokens": 0, "tool_calls": 0, "retries": 0}
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT metric,SUM(amount) AS total FROM budget_ledger WHERE task_id=? GROUP BY metric", (task_id,)
            )
            for row in rows:
                result[str(row["metric"])] = int(row["total"] or 0)
        return result

    def budget_for_run(self, task_id: str, run_key: str | None) -> dict[str, int]:
        """Enforcement view for the current dispatch run only."""
        result = {"tokens": 0, "tool_calls": 0, "retries": 0}
        if not run_key:
            return self.budget(task_id)
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT metric,SUM(amount) AS total FROM run_budget WHERE task_id=? AND run_key=? GROUP BY metric",
                (task_id, run_key),
            )
            for row in rows:
                metric = str(row["metric"])
                result[metric] = int(row["total"] or 0)
        return result

    # --------------------------------------------------------------- run state
    def touch_run(self, task_id: str, run_key: str, now_epoch: int) -> int:
        """Register the current dispatch run. A changed run_key resets the
        wall-clock baseline and idle-turn counter. Returns claimed_at epoch."""
        with self.connect() as connection:
            row = connection.execute("SELECT run_key,claimed_at FROM run_state WHERE task_id=?", (task_id,)).fetchone()
            if row is None:
                connection.execute(
                    "INSERT OR IGNORE INTO run_state(task_id,run_key,claimed_at,updated_at) VALUES(?,?,?,?)",
                    (task_id, run_key, int(now_epoch), utc_now()),
                )
                connection.execute(
                    "INSERT OR IGNORE INTO task_state(task_id,idle_turns,updated_at) VALUES(?,0,?)", (task_id, utc_now())
                )
                return int(now_epoch)
            if str(row["run_key"]) != str(run_key):
                connection.execute(
                    "UPDATE run_state SET run_key=?,claimed_at=?,updated_at=? WHERE task_id=?",
                    (run_key, int(now_epoch), utc_now(), task_id),
                )
                connection.execute(
                    "INSERT OR IGNORE INTO task_state(task_id,idle_turns,updated_at) VALUES(?,0,?)", (task_id, utc_now())
                )
                connection.execute("UPDATE task_state SET idle_turns=0,updated_at=? WHERE task_id=?", (utc_now(), task_id))
                return int(now_epoch)
            return int(row["claimed_at"])

    def claimed_at(self, task_id: str) -> int | None:
        with self.connect() as connection:
            row = connection.execute("SELECT claimed_at FROM run_state WHERE task_id=?", (task_id,)).fetchone()
            return int(row["claimed_at"]) if row else None

    # ------------------------------------------------------------------- calls
    def add_call(self, event_id: str, task_id: str, call_signature: str,
                 failure_signature: str | None, success: bool, run_key: str | None = None) -> bool:
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO call_history(event_id,task_id,call_signature,failure_signature,success,created_at) VALUES(?,?,?,?,?,?)",
                (event_id, task_id, call_signature, failure_signature, int(success), utc_now()),
            )
            if run_key:
                connection.execute(
                    "INSERT OR IGNORE INTO run_call_history(event_id,task_id,run_key,call_signature,failure_signature,success,created_at) VALUES(?,?,?,?,?,?,?)",
                    (event_id, task_id, run_key, call_signature, failure_signature, int(success), utc_now()),
                )
            return cursor.rowcount == 1

    def count_signature(self, task_id: str, column: str, value: str, run_key: str | None = None) -> int:
        if column not in {"call_signature", "failure_signature"}:
            raise ValueError("unsupported signature column")
        with self.connect() as connection:
            if run_key:
                row = connection.execute(
                    f"SELECT COUNT(*) AS count FROM run_call_history WHERE task_id=? AND {column}=?"
                    " AND run_key=?", (task_id, value, run_key)
                ).fetchone()
            else:
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

    # --------------------------------------------------------------- approvals
    def ensure_approval(self, rule_key: str, task_id: str, action: str, target: str, hashed_args: str) -> bool:
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO approvals(rule_key,task_id,action,target,args_hash,status,created_at) VALUES(?,?,?,?,?,'pending',?)",
                (rule_key, task_id, action, target, hashed_args, utc_now()),
            )
            return cursor.rowcount == 1

    def decide_approval(self, rule_key: str, approved: bool, decided_by: str) -> bool:
        # Defense in depth: dispatcher workers cannot approve through a direct
        # Python import even if the terminal command evades the textual policy.
        # The authoritative operator CLI runs outside HERMES_KANBAN_TASK.
        if os.environ.get("HERMES_KANBAN_TASK"):
            return False
        status = "approved" if approved else "rejected"
        with self.connect() as connection:
            cursor = connection.execute(
                "UPDATE approvals SET status=?,decided_at=?,decided_by=? WHERE rule_key=? AND status='pending'",
                (status, utc_now(), decided_by, rule_key),
            )
            return cursor.rowcount == 1

    def consume_exact_approval(self, task_id: str, action: str, target: str, hashed_args: str) -> bool:
        if os.environ.get("HERMES_KANBAN_TASK") and os.environ.get("HERMES_KANBAN_TASK") == task_id:
            pass
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT rule_key,status FROM approvals WHERE task_id=? AND action=? AND target=? AND args_hash=?"
                " ORDER BY created_at LIMIT 1",
                (task_id, action, target, hashed_args),
            ).fetchone()
            if row is None or row["status"] != "approved":
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

    def grant_capability(self, capability_id: str, project: str, kind: str, scope: str, granted_by: str) -> bool:
        if os.environ.get("HERMES_KANBAN_TASK"):
            return False
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT OR REPLACE INTO capabilities VALUES(?,?,?,?,?,?,?)",
                (capability_id, project, kind, scope, "active", granted_by, utc_now()),
            )
            return cursor.rowcount == 1

    def capability_active(self, capability_id: str, project: str) -> bool:
        with self.connect() as connection:
            return connection.execute(
                "SELECT 1 FROM capabilities WHERE capability_id=? AND project=? AND status='active'",
                (capability_id, project),
            ).fetchone() is not None

    def monthly_spend(self, project: str, month_prefix: str) -> int:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT COALESCE(SUM(amount_rub),0) AS total FROM financial_ledger "
                "WHERE project=? AND created_at LIKE ? AND status IN ('reserved','settled')",
                (project, month_prefix + "%"),
            ).fetchone()
            return int(row["total"] or 0)

    def reserve_spend(self, event_id: str, task_id: str, project: str, amount_rub: int, capability_id: str) -> bool:
        now = utc_now()
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO financial_ledger VALUES(?,?,?,?,?,'reserved',?,?)",
                (event_id, task_id, project, int(amount_rub), capability_id, now, now),
            )
            return cursor.rowcount == 1

    def authorize_and_reserve_spend(self, event_id: str, task_id: str, project: str,
                                    amount_rub: int, capability_id: str,
                                    max_transaction: int, max_monthly: int) -> str:
        """Atomically validate capability/limits and reserve spend."""
        now = utc_now()
        month = now[:7]
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if connection.execute(
                "SELECT 1 FROM capabilities WHERE capability_id=? AND project=? AND status='active'",
                (capability_id, project),
            ).fetchone() is None:
                return "capability_missing"
            total = int(connection.execute(
                "SELECT COALESCE(SUM(amount_rub),0) FROM financial_ledger "
                "WHERE project=? AND created_at LIKE ? AND status IN ('reserved','settled')",
                (project, month + "%"),
            ).fetchone()[0] or 0)
            if amount_rub > max_transaction:
                return "transaction_over"
            if total + amount_rub > max_monthly:
                return "monthly_over"
            connection.execute(
                "INSERT OR IGNORE INTO financial_ledger VALUES(?,?,?,?,?,'reserved',?,?)",
                (event_id, task_id, project, int(amount_rub), capability_id, now, now),
            )
            return "reserved"

    def settle_spend(self, event_id: str, success: bool) -> bool:
        status = "settled" if success else "released"
        with self.connect() as connection:
            cursor = connection.execute(
                "UPDATE financial_ledger SET status=?,updated_at=? WHERE event_id=? AND status='reserved'",
                (status, utc_now(), event_id),
            )
            return cursor.rowcount == 1

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
            for table, days in (("events", event_days), ("call_history", call_days), ("approvals", approval_days), ("budget_ledger", call_days), ("financial_ledger", approval_days)):
                cutoff = (now - timedelta(days=days)).isoformat(timespec="seconds").replace("+00:00", "Z")
                cursor = connection.execute(f"DELETE FROM {table} WHERE created_at < ?", (cutoff,))
                deleted[table] = cursor.rowcount
            # run_budget follows the call-history horizon but is pruned outside
            # the returned shape so v1.x callers keep a stable report dict.
            call_cutoff = (now - timedelta(days=call_days)).isoformat(timespec="seconds").replace("+00:00", "Z")
            connection.execute("DELETE FROM run_budget WHERE created_at < ?", (call_cutoff,))
            connection.execute("DELETE FROM run_call_history WHERE created_at < ?", (call_cutoff,))
            event_cutoff = (now - timedelta(days=event_days)).isoformat(timespec="seconds").replace("+00:00", "Z")
            cursor = connection.execute(
                "DELETE FROM notification_outbox WHERE status!='pending' AND created_at < ?", (event_cutoff,)
            )
            deleted["notification_outbox"] = cursor.rowcount
            cursor = connection.execute("DELETE FROM task_state WHERE updated_at < ?", (event_cutoff,))
            deleted["task_state"] = cursor.rowcount
        return deleted
