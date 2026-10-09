#!/usr/bin/env python3
"""Cascade disposition reporter (shadow mode).

Read-only. For a superseded/killed/no-go root task, walk its open descendants
and compute a topological disposition report per RC6 / reliability-plan §F.
This tool NEVER mutates the board; it prints a JSON report that reviewers
use to drive disposition. Live apply remains a company/owner action.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

# Reuse the controller's pure helpers and CLI without importing a package.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import blocked_state_controller as bsc  # noqa: E402


def _descendants(board: str, root_id: str, cli) -> list[dict]:
    """Collect all descendants of root_id across every status (read-only)."""
    seen: set[str] = set()
    out: list[dict] = []
    frontier = [root_id]
    statuses = ["todo", "ready", "running", "blocked", "triage", "review", "done", "archived"]
    by_id: dict[str, dict] = {}
    for status in statuses:
        for t in cli(board, ["list", "--status", status], 60) or []:
            if isinstance(t, dict) and t.get("id"):
                by_id[str(t["id"])] = t
    # Build child->parent edges from show() parents where available.
    while frontier:
        current = frontier.pop()
        for tid, t in by_id.items():
            if tid in seen or tid == root_id:
                continue
            parents = t.get("parents") or []
            if current in parents or (t.get("parent_id") and t.get("parent_id") == current):
                seen.add(tid)
                out.append(t)
                frontier.append(tid)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Shadow cascade disposition report (read-only).")
    parser.add_argument("--board", required=True)
    parser.add_argument("--root", required=True, help="Root task id")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    cli = bsc.run_cli
    root_show = cli(args.board, ["show", args.root], 45)
    root = (root_show or {}).get("task") or {"id": args.root}
    descendants = _descendants(args.board, args.root, cli)
    report = bsc.compute_cascade_disposition(root, descendants)
    report["mode"] = "shadow_read_only"
    print(json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
