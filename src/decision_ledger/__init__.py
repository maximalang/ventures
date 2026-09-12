"""decision_ledger — thin decision ledger for the Hermes/Kanban company OS.

Records every material company decision (go / no-go / iterate / kill) with
hypothesis, confidence, expected impact, cost, kill criterion, kanban task id
and evidence refs, then tracks the outcome (open / hit / missed / killed) so
later briefings carry decision history.

Pattern attribution: inspired by the episodic memory system of
SenteLabsAI/OpenExecutive (Apache-2.0) — decisions persisted in SQLite with
an outcome field and the 8 most recent decisions injected into every new
briefing. This package is an original implementation for maximalang/ventures;
no OpenExecutive source code is copied. See README.md in this directory.
"""

from __future__ import annotations

from decision_ledger.store import (
    BRIEF_LIMIT_DEFAULT,
    VALID_DECISIONS,
    VALID_OUTCOMES,
    VALID_SCOPES,
    LedgerError,
    add_decision,
    build_brief,
    connect,
    default_db_path,
    initialize,
    list_decisions,
    review_outcome,
)

__version__ = "1.0.0"

__all__ = [
    "BRIEF_LIMIT_DEFAULT",
    "VALID_DECISIONS",
    "VALID_OUTCOMES",
    "VALID_SCOPES",
    "LedgerError",
    "add_decision",
    "build_brief",
    "connect",
    "default_db_path",
    "initialize",
    "list_decisions",
    "review_outcome",
    "__version__",
]
