"""SQLite store for the decision ledger.

Pattern attribution
-------------------
The episodic decision-ledger pattern — company decisions persisted in SQLite
with an outcome field and the last N decisions injected into every new
briefing — is inspired by SenteLabsAI/OpenExecutive (Apache License 2.0),
see ``packages/core/openexecutive/memory/episodic.py`` and the "Memory
System" section of ``docs/architecture.md`` in that repository
(head b071101). This module is an original implementation written for the
maximalang/ventures company OS (Hermes/Kanban fleet); no source code was
copied from OpenExecutive.

Storage
-------
A single dedicated SQLite file. Default location:
``<repo-root>/.state/decision-ledger.db`` (gitignored). Override with the
``DECISION_LEDGER_DB`` environment variable or an explicit ``db_path``
argument. The ledger never reads or writes any other state database.
"""

from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1

VALID_SCOPES = ("portfolio", "venture")
VALID_DECISIONS = ("go", "no-go", "iterate", "kill")
VALID_OUTCOMES = ("open", "hit", "missed", "killed")

#: Number of recent decisions injected into a brief (OpenExecutive pattern).
BRIEF_LIMIT_DEFAULT = 8

ENV_DB_PATH = "DECISION_LEDGER_DB"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    scope TEXT NOT NULL CHECK (scope IN ('portfolio', 'venture')),
    venture TEXT NOT NULL DEFAULT '',
    hypothesis TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('go', 'no-go', 'iterate', 'kill')),
    confidence REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    expected_impact TEXT NOT NULL DEFAULT '',
    cost_rub REAL NOT NULL DEFAULT 0.0,
    kill_criterion TEXT NOT NULL DEFAULT '',
    kanban_task_id TEXT NOT NULL DEFAULT '',
    evidence_refs TEXT NOT NULL DEFAULT '[]',
    outcome_status TEXT NOT NULL DEFAULT 'open'
        CHECK (outcome_status IN ('open', 'hit', 'missed', 'killed')),
    outcome_reviewed_at TEXT,
    outcome_note TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_decisions_id_desc ON decisions(id);
CREATE INDEX IF NOT EXISTS idx_decisions_outcome ON decisions(outcome_status);
CREATE INDEX IF NOT EXISTS idx_decisions_scope ON decisions(scope, venture);
"""


class LedgerError(ValueError):
    """Raised when a ledger write or review is invalid."""


def utc_now_iso() -> str:
    """Current UTC time as a sortable ISO-8601 string (second precision)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def default_db_path() -> Path:
    """Resolve the ledger database path.

    Priority: ``DECISION_LEDGER_DB`` environment variable, else
    ``<repo-root>/.state/decision-ledger.db`` where repo-root is derived
    from this file's location (``src/decision_ledger/store.py`` → two
    levels up). The layout is intentionally host-specific (owner decision
    07.09.2026): the env override exists for tests and ad-hoc use.
    """
    env = os.environ.get(ENV_DB_PATH)
    if env:
        return Path(env)
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / ".state" / "decision-ledger.db"


@contextmanager
def connect(db_path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    """Open a short-lived connection, commit on success, always close."""
    path = Path(db_path) if db_path is not None else default_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def initialize(db_path: str | Path | None = None) -> None:
    """Create the schema if absent. Idempotent; safe to call on every run."""
    with connect(db_path) as conn:
        conn.executescript(SCHEMA_SQL)


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    raw_refs = data.get("evidence_refs") or "[]"
    try:
        refs = json.loads(raw_refs)
    except (TypeError, json.JSONDecodeError):
        refs = []
    if not isinstance(refs, list):
        refs = []
    data["evidence_refs"] = refs
    return data


def _normalize_evidence_refs(evidence_refs: Sequence[str] | str | None) -> str:
    if evidence_refs is None:
        return "[]"
    if isinstance(evidence_refs, str):
        try:
            parsed = json.loads(evidence_refs)
        except json.JSONDecodeError as exc:
            raise LedgerError(f"evidence_refs string must be a JSON array: {exc}") from exc
        if not isinstance(parsed, list):
            raise LedgerError("evidence_refs JSON must be an array")
        return json.dumps(parsed, ensure_ascii=False)
    if isinstance(evidence_refs, Sequence):
        return json.dumps(list(evidence_refs), ensure_ascii=False)
    raise LedgerError("evidence_refs must be a list of strings or a JSON array string")


def add_decision(
    *,
    scope: str,
    hypothesis: str,
    decision: str,
    confidence: float,
    venture: str = "",
    expected_impact: str = "",
    cost_rub: float = 0.0,
    kill_criterion: str = "",
    kanban_task_id: str = "",
    evidence_refs: Sequence[str] | str | None = None,
    ts: str | None = None,
    db_path: str | Path | None = None,
) -> int:
    """Validate and persist one decision row. Returns the new row id."""
    if scope not in VALID_SCOPES:
        raise LedgerError(f"scope must be one of {VALID_SCOPES}, got {scope!r}")
    if decision not in VALID_DECISIONS:
        raise LedgerError(f"decision must be one of {VALID_DECISIONS}, got {decision!r}")
    if not hypothesis or not hypothesis.strip():
        raise LedgerError("hypothesis must be a non-empty string")
    if scope == "venture" and not venture.strip():
        raise LedgerError("venture is required when scope=venture")
    try:
        confidence_value = float(confidence)
    except (TypeError, ValueError) as exc:
        raise LedgerError(f"confidence must be a number, got {confidence!r}") from exc
    if not 0.0 <= confidence_value <= 1.0:
        raise LedgerError(f"confidence must be within 0..1, got {confidence_value}")
    try:
        cost_value = float(cost_rub)
    except (TypeError, ValueError) as exc:
        raise LedgerError(f"cost_rub must be a number, got {cost_rub!r}") from exc
    if cost_value < 0.0:
        raise LedgerError(f"cost_rub must be >= 0, got {cost_value}")
    refs_json = _normalize_evidence_refs(evidence_refs)

    initialize(db_path)
    with connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO decisions (
                ts, scope, venture, hypothesis, decision, confidence,
                expected_impact, cost_rub, kill_criterion, kanban_task_id,
                evidence_refs
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ts or utc_now_iso(),
                scope,
                venture.strip(),
                hypothesis.strip(),
                decision,
                confidence_value,
                expected_impact,
                cost_value,
                kill_criterion,
                kanban_task_id,
                refs_json,
            ),
        )
        return int(cursor.lastrowid or 0)


def list_decisions(
    *,
    scope: str | None = None,
    venture: str | None = None,
    outcome_status: str | None = None,
    limit: int | None = None,
    db_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Return decisions newest-first, optionally filtered and limited."""
    if scope is not None and scope not in VALID_SCOPES:
        raise LedgerError(f"scope filter must be one of {VALID_SCOPES}, got {scope!r}")
    if outcome_status is not None and outcome_status not in VALID_OUTCOMES:
        raise LedgerError(
            f"outcome_status filter must be one of {VALID_OUTCOMES}, got {outcome_status!r}"
        )
    if limit is not None and limit <= 0:
        raise LedgerError(f"limit must be positive, got {limit}")

    initialize(db_path)
    query = "SELECT * FROM decisions"
    conditions: list[str] = []
    params: list[Any] = []
    if scope is not None:
        conditions.append("scope = ?")
        params.append(scope)
    if venture is not None:
        conditions.append("venture = ?")
        params.append(venture)
    if outcome_status is not None:
        conditions.append("outcome_status = ?")
        params.append(outcome_status)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC"
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
    with connect(db_path) as conn:
        rows = conn.execute(query, params).fetchall()
    return [_row_to_dict(row) for row in rows]


def get_decision(decision_id: int, db_path: str | Path | None = None) -> dict[str, Any] | None:
    """Fetch one decision by id, or None when absent."""
    initialize(db_path)
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,)).fetchone()
    return _row_to_dict(row) if row is not None else None


def review_outcome(
    decision_id: int,
    *,
    outcome_status: str,
    note: str = "",
    db_path: str | Path | None = None,
) -> dict[str, Any] | None:
    """Close (or reopen) the outcome of one decision.

    Sets ``outcome_status``, ``outcome_reviewed_at`` (UTC now) and
    ``outcome_note``. Returns the updated row, or None when the id is unknown.
    """
    if outcome_status not in VALID_OUTCOMES:
        raise LedgerError(
            f"outcome_status must be one of {VALID_OUTCOMES}, got {outcome_status!r}"
        )
    initialize(db_path)
    with connect(db_path) as conn:
        cursor = conn.execute(
            """
            UPDATE decisions
               SET outcome_status = ?,
                   outcome_reviewed_at = ?,
                   outcome_note = ?
             WHERE id = ?
            """,
            (outcome_status, utc_now_iso(), note, decision_id),
        )
        if cursor.rowcount == 0:
            return None
        row = conn.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,)).fetchone()
    return _row_to_dict(row) if row is not None else None


def _format_recent_line(row: dict[str, Any]) -> str:
    where = row["scope"] if row["scope"] == "portfolio" else f"venture:{row['venture']}"
    task = f" task={row['kanban_task_id']}" if row["kanban_task_id"] else ""
    return (
        f"- #{row['id']} {row['ts']} [{where}] {row['decision']} "
        f"(conf {row['confidence']:.2f}, cost {row['cost_rub']:.0f} RUB) — "
        f"{row['hypothesis']} | outcome: {row['outcome_status']}{task}"
    )


def _format_open_line(row: dict[str, Any]) -> str:
    kill = row["kill_criterion"] or "n/a"
    task = row["kanban_task_id"] or "n/a"
    return (
        f"- #{row['id']} {row['ts']} {row['decision']} — {row['hypothesis']} "
        f"| expected: {row['expected_impact'] or 'n/a'} | kill criterion: {kill} "
        f"| task: {task}"
    )


def build_brief(limit: int = BRIEF_LIMIT_DEFAULT, db_path: str | Path | None = None) -> str:
    """Render the decision brief: last ``limit`` decisions + all open outcomes.

    Plain text, ready for injection into the owner digest or a decision
    briefing (OpenExecutive ``format_for_prompt`` pattern, thin rework).
    """
    if limit <= 0:
        raise LedgerError(f"limit must be positive, got {limit}")
    recent = list_decisions(limit=limit, db_path=db_path)
    open_rows = list_decisions(outcome_status="open", db_path=db_path)

    lines = [
        f"# Decision brief — last {limit} decisions (generated {utc_now_iso()})",
        "",
        "## Recent decisions",
    ]
    lines.extend(_format_recent_line(row) for row in recent)
    if not recent:
        lines.append("- none recorded yet")
    lines += ["", f"## Open outcomes ({len(open_rows)})"]
    lines.extend(_format_open_line(row) for row in open_rows)
    if not open_rows:
        lines.append("- none")
    return "\n".join(lines)
