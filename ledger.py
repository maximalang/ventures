#!/usr/bin/env python3
"""ledger.py — CLI for the decision ledger (add | list | review-outcome | brief).

Pattern attribution: the episodic decision-ledger pattern (decisions in
SQLite with outcome tracking, recent decisions injected into briefings) is
inspired by SenteLabsAI/OpenExecutive (Apache-2.0,
packages/core/openexecutive/memory/episodic.py). This CLI is an original
implementation for maximalang/ventures — see src/decision_ledger/README.md.

Examples:
  python ledger.py add --scope venture --venture rr --decision go \
      --hypothesis "landing rewrite lifts signup CTR" --confidence 0.7 \
      --expected-impact "+15% CTR" --cost-rub 30000 \
      --kill-criterion "CTR below baseline in 14 days" \
      --kanban-task-id t_4dbcd5da --evidence-ref "https://example/pr/1"
  python ledger.py list --outcome open --limit 20
  python ledger.py review-outcome 3 --outcome hit --note "CTR +18% measured"
  python ledger.py brief --limit 8

The database path defaults to <repo-root>/.state/decision-ledger.db and can
be overridden with --db or the DECISION_LEDGER_DB environment variable.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from decision_ledger.store import (  # noqa: E402
    BRIEF_LIMIT_DEFAULT,
    VALID_DECISIONS,
    VALID_OUTCOMES,
    VALID_SCOPES,
    LedgerError,
    add_decision,
    build_brief,
    default_db_path,
    list_decisions,
    review_outcome,
)


def _add_parser(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("add", help="record a decision")
    parser.add_argument("--scope", required=True, choices=VALID_SCOPES)
    parser.add_argument("--venture", default="", help="required when --scope venture")
    parser.add_argument("--hypothesis", required=True)
    parser.add_argument("--decision", required=True, choices=VALID_DECISIONS)
    parser.add_argument("--confidence", required=True, type=float, help="0..1")
    parser.add_argument("--expected-impact", default="")
    parser.add_argument("--cost-rub", default=0.0, type=float)
    parser.add_argument("--kill-criterion", default="")
    parser.add_argument("--kanban-task-id", default="")
    parser.add_argument(
        "--evidence-ref",
        action="append",
        default=[],
        dest="evidence_refs",
        help="URL/SHA/path reference; repeatable",
    )
    parser.add_argument("--db", default=None)


def _list_parser(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("list", help="list decisions (newest first)")
    parser.add_argument("--scope", choices=VALID_SCOPES)
    parser.add_argument("--venture")
    parser.add_argument("--outcome", choices=VALID_OUTCOMES, dest="outcome_status")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--db", default=None)


def _review_parser(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("review-outcome", help="set the outcome of one decision")
    parser.add_argument("id", type=int)
    parser.add_argument("--outcome", required=True, choices=VALID_OUTCOMES, dest="outcome_status")
    parser.add_argument("--note", default="")
    parser.add_argument("--db", default=None)


def _brief_parser(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser(
        "brief",
        help=f"last N decisions + open outcomes (default N={BRIEF_LIMIT_DEFAULT})",
    )
    parser.add_argument("--limit", type=int, default=BRIEF_LIMIT_DEFAULT)
    parser.add_argument("--db", default=None)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ledger.py", description="Decision ledger CLI (see module docstring)"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    _add_parser(sub)
    _list_parser(sub)
    _review_parser(sub)
    _brief_parser(sub)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    db = Path(args.db) if getattr(args, "db", None) else default_db_path()
    try:
        if args.command == "add":
            decision_id = add_decision(
                scope=args.scope,
                venture=args.venture,
                hypothesis=args.hypothesis,
                decision=args.decision,
                confidence=args.confidence,
                expected_impact=args.expected_impact,
                cost_rub=args.cost_rub,
                kill_criterion=args.kill_criterion,
                kanban_task_id=args.kanban_task_id,
                evidence_refs=args.evidence_refs,
                db_path=db,
            )
            print(f"added decision #{decision_id} -> {db}")
            return 0
        if args.command == "list":
            rows = list_decisions(
                scope=args.scope,
                venture=args.venture,
                outcome_status=args.outcome_status,
                limit=args.limit,
                db_path=db,
            )
            if args.json:
                print(json.dumps(rows, ensure_ascii=False, indent=2))
                return 0
            if not rows:
                print("no decisions recorded")
                return 0
            for row in rows:
                print(json.dumps(row, ensure_ascii=False))
            return 0
        if args.command == "review-outcome":
            updated = review_outcome(
                args.id, outcome_status=args.outcome_status, note=args.note, db_path=db
            )
            if updated is None:
                print(f"decision #{args.id} not found", file=sys.stderr)
                return 2
            print(
                f"decision #{args.id} outcome={updated['outcome_status']} "
                f"reviewed_at={updated['outcome_reviewed_at']}"
            )
            return 0
        if args.command == "brief":
            print(build_brief(limit=args.limit, db_path=db))
            return 0
    except LedgerError as exc:
        print(f"ledger error: {exc}", file=sys.stderr)
        return 2
    return 2  # unreachable: argparse enforces a valid command


if __name__ == "__main__":
    raise SystemExit(main())
