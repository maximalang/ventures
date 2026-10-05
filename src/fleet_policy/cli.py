from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

from . import __version__
from .drift import approval_drift
from .projector import HermesProjector
from .runtime import FleetPolicyRuntime


def _find_runtime_root(start: Path) -> Path:
    """Find the nearest release bundle or source root above ``start``."""
    resolved = start.resolve()
    current = resolved if resolved.is_dir() else resolved.parent
    for candidate in (current, *current.parents):
        if (candidate / "RELEASE-MANIFEST.json").is_file():
            return candidate
        if (candidate / "src" / "fleet_policy").is_dir():
            return candidate
    raise FileNotFoundError(
        f"cannot locate fleet-policy runtime root from {resolved}; "
        "expected RELEASE-MANIFEST.json or src/fleet_policy in an ancestor"
    )


def default_root(arguments: dict | argparse.Namespace) -> Path:
    """Portable self-contained default root for the bundle checkout or install.

    Resolution order: explicit ``--root`` argument, ``HERMES_VENTURES_ROOT``,
    then the repository/install root that contains ``src/fleet_policy`` next to
    this module. The fallback never pins a machine-specific absolute path, so
    the same bundle runs unchanged on any host (F-02).
    """
    explicit = arguments.get("root") if isinstance(arguments, dict) else getattr(arguments, "root", None)
    if explicit:
        return Path(str(explicit))
    override = os.environ.get("HERMES_VENTURES_ROOT")
    if override:
        return Path(override)
    return _find_runtime_root(Path(__file__))


# ---------------------------------------------------------------------------
# v1.2.37 FP-read-lane (card t_e393b6e8, RR-3/RR-4a): sanctioned READ-ONLY
# diagnostics route for policy state. Workers must never need ad-hoc
# heredoc/multiline sqlite probes against control-plane stores (they fail
# closed by design and burned whole runs on 04.10). These commands open the
# policy store with sqlite3 `mode=ro` — no schema migration, no directory
# creation, no write of any kind — and never mutate board state.
# ---------------------------------------------------------------------------


def _read_only_store_path(arguments: argparse.Namespace) -> Path:
    return default_root(arguments) / ".state" / "fleet-policy.db"


def _ro_connection(path: Path) -> sqlite3.Connection | None:
    """mode=ro connection (no create, no migrate); None when absent."""
    if not path.is_file():
        return None
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=5)
    connection.row_factory = sqlite3.Row
    return connection


def _store_error(path: Path) -> int:
    print(json.dumps({"ok": False, "error": "policy store not found", "store": str(path)},
                     ensure_ascii=False))
    return 1


def cmd_events(args: argparse.Namespace) -> int:
    """Read-only: list policy events as NDJSON (newest first)."""
    path = _read_only_store_path(args)
    connection = _ro_connection(path)
    if connection is None:
        return _store_error(path)
    query = "SELECT event_id, correlation_id, task_id, kind, payload_json, created_at FROM events WHERE created_at >= ?"
    params: list[object] = [str(args.since or "")]
    if args.task:
        query += " AND task_id = ?"
        params.append(str(args.task))
    if args.kind:
        query += " AND kind = ?"
        params.append(str(args.kind))
    limit = max(1, min(int(args.limit or 50), 500))
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    try:
        rows = connection.execute(query, params).fetchall()
    finally:
        connection.close()
    emitted = 0
    for row in rows:
        try:
            payload = json.loads(row["payload_json"])
        except (json.JSONDecodeError, TypeError):
            payload = {"raw": row["payload_json"]}
        if args.rule and str(payload.get("rule_id") or "") != str(args.rule):
            continue
        if args.decision and str(payload.get("decision") or "") != str(args.decision):
            continue
        print(json.dumps({
            "event_id": row["event_id"],
            "created_at": row["created_at"],
            "task_id": row["task_id"],
            "kind": row["kind"],
            "payload": payload,
        }, ensure_ascii=False, sort_keys=True))
        emitted += 1
    print(json.dumps({"ok": True, "emitted": emitted, "store": str(path)}, ensure_ascii=False))
    return 0


def cmd_task(args: argparse.Namespace) -> int:
    """Read-only: resolved policy view of one card.

    Replaces the ad-hoc board-db heredoc probes workers fell back to:
    classification (task_type + marker problems), company anchor, gate
    records (author/verdict only), budgets, runs and approvals.
    """
    from .config import load_config
    from .kanban_context import load_task_context
    from .policy import infer_task_type
    from .runtime import FleetPolicyRuntime

    task_id = str(args.task_id or os.environ.get("HERMES_KANBAN_TASK") or "").strip()
    if not task_id:
        print(json.dumps({"ok": False, "error": "task id is required (--id or HERMES_KANBAN_TASK)"},
                         ensure_ascii=False))
        return 2
    config = load_config(default_root(args) / "config" / "fleet-policy.yaml")
    board = str(args.board or os.environ.get("HERMES_KANBAN_BOARD") or "").strip() or None
    context = load_task_context({"task_id": task_id, "board": board}, config.get("projects", {}))
    task_type, marker_error = infer_task_type(
        context.get("task_body"), context.get("comments"), context.get("skills")
    )
    anchor = None
    gate_records: list[dict] = []
    for record in context.get("comment_records") or []:
        author = str(record.get("author") or "")
        body = str(record.get("body") or "")
        for line in FleetPolicyRuntime._attestation_lines(body):
            if line == "decision:company=go" or line.startswith("decision:company=go "):
                head_match = FleetPolicyRuntime._BINDING_HEAD.search(body)
                anchor = {"author": author, "decision": "go",
                          "head": head_match.group(1) if head_match else None}
            elif line.startswith("decision:company=no-go"):
                anchor = {"author": author, "decision": "no-go", "head": None}
            marker = re.match(r"^gate:([a-z_]+)=(pass|fail)\b", line)
            if marker:
                gate_records.append({"author": author, "gate": marker.group(1),
                                     "verdict": marker.group(2)})
    budgets: dict[str, int] = {}
    runs: list[dict] = []
    approvals: list[dict] = []
    idle_turns = None
    path = _read_only_store_path(args)
    connection = _ro_connection(path)
    if connection is not None:
        try:
            for row in connection.execute(
                "SELECT metric, SUM(amount) AS amount FROM budget_ledger WHERE task_id=? GROUP BY metric",
                (task_id,),
            ):
                budgets[str(row["metric"])] = int(row["amount"] or 0)
            for row in connection.execute(
                "SELECT run_key, claimed_at FROM run_state WHERE task_id=?", (task_id,)
            ):
                runs.append({"run_key": str(row["run_key"]), "claimed_at": int(row["claimed_at"] or 0)})
            for row in connection.execute(
                "SELECT rule_key, action, status, created_at, decided_by FROM approvals "
                "WHERE task_id=? ORDER BY created_at DESC LIMIT 50",
                (task_id,),
            ):
                approvals.append({key: row[key] for key in row.keys()})
            row = connection.execute(
                "SELECT idle_turns FROM task_state WHERE task_id=?", (task_id,)
            ).fetchone()
            idle_turns = int(row["idle_turns"]) if row else None
        except sqlite3.Error as exc:
            budgets = {"error": str(exc)}  # type: ignore[assignment]
        finally:
            connection.close()
    print(json.dumps({
        "ok": True,
        "task_id": task_id,
        "board": context.get("board"),
        "project": context.get("project"),
        "profile": context.get("profile"),
        "status": context.get("task_status"),
        "assignee": context.get("assignee"),
        "task_type": task_type,
        "task_type_error": marker_error or context.get("task_context_error"),
        "anchor": anchor,
        "gate_records": gate_records,
        "budget_totals": budgets,
        "runs": runs,
        "idle_turns": idle_turns,
        "approvals": approvals,
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    """Read-only: one event by id, approvals of a task, or effective config."""
    if args.event_id:
        path = _read_only_store_path(args)
        connection = _ro_connection(path)
        if connection is None:
            return _store_error(path)
        try:
            row = connection.execute(
                "SELECT event_id, correlation_id, task_id, kind, payload_json, created_at "
                "FROM events WHERE event_id=?",
                (str(args.event_id),),
            ).fetchone()
        finally:
            connection.close()
        if row is None:
            print(json.dumps({"ok": False, "error": "event not found",
                              "event_id": str(args.event_id)}, ensure_ascii=False))
            return 1
        record = {key: row[key] for key in row.keys()}
        try:
            record["payload"] = json.loads(record.pop("payload_json"))
        except (json.JSONDecodeError, TypeError):
            pass
        record["ok"] = True
        print(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.approvals_task:
        path = _read_only_store_path(args)
        connection = _ro_connection(path)
        if connection is None:
            return _store_error(path)
        try:
            rows = connection.execute(
                "SELECT rule_key, task_id, action, target, status, created_at, decided_at, "
                "decided_by, board FROM approvals WHERE task_id=? ORDER BY created_at DESC LIMIT 200",
                (str(args.approvals_task),),
            ).fetchall()
        finally:
            connection.close()
        print(json.dumps({"ok": True, "task_id": str(args.approvals_task),
                          "approvals": [{key: row[key] for key in row.keys()} for row in rows]},
                         ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    from .config import load_config
    from .runtime import FleetPolicyRuntime
    config = load_config(default_root(args) / "config" / "fleet-policy.yaml")
    print(json.dumps({
        "ok": True,
        "version": __version__,
        "config": config,
        "gate_authors": {gate: sorted(authors) for gate, authors in FleetPolicyRuntime.GATE_AUTHORS.items()},
        "evidence_gated_categories": sorted(FleetPolicyRuntime.EVIDENCE_GATED_CATEGORIES),
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="fleet-policy")
    result.add_argument("--root", default=None, help="Repository root; defaults to HERMES_VENTURES_ROOT or the installed bundle root.")
    result.add_argument("--version", action="store_true")
    sub = result.add_subparsers(dest="command")
    approve = sub.add_parser("approve")
    approve.add_argument("rule_key")
    approve.add_argument("--by", default="user")
    approve.add_argument("--confirm", default=None,
                         help="Interactive owner confirmation: the last 8 characters of the binding's rule_key.")
    reject = sub.add_parser("reject")
    reject.add_argument("rule_key")
    reject.add_argument("--by", default="user")
    reject.add_argument("--confirm", default=None,
                        help="Interactive owner confirmation: the last 8 characters of the binding's rule_key.")
    revoke = sub.add_parser("revoke")
    revoke.add_argument("rule_key")
    revoke.add_argument("--by", default="user")
    revoke.add_argument("--confirm", default=None,
                        help="Interactive owner confirmation: the last 8 characters of the binding's rule_key.")
    sub.add_parser("drain-notifications")
    suppress = sub.add_parser("fail-notifications")
    suppress.add_argument("--all-pending", action="store_true")
    grant = sub.add_parser("grant-capability")
    grant.add_argument("capability_id")
    grant.add_argument("--project", required=True)
    grant.add_argument("--kind", required=True)
    grant.add_argument("--scope", required=True)
    grant.add_argument("--by", default="user")
    override = sub.add_parser("override-expected-failure")
    override.add_argument("task_id")
    override.add_argument("failure_signature")
    override.add_argument("--run-key", default=None,
                          help="Scope the override to one dispatch run; omit for the whole task.")
    override.add_argument("--confirm", default=None,
                          help="Operator confirmation: the last 8 characters of the override binding key.")
    override.add_argument("--by", default="user")
    spend = sub.add_parser("spend-status")
    spend.add_argument("--project", required=True)
    sub.add_parser("retention")
    sub.add_parser("status")
    sub.add_parser("drift-check")
    bundle = sub.add_parser("build-bundle")
    bundle.add_argument("--output", required=True)
    verify = sub.add_parser("verify-bundle")
    verify.add_argument("--bundle", required=True)
    attestation_build = sub.add_parser("build-release-attestation")
    attestation_build.add_argument("--input", required=True, help="Evidence JSON (all fields explicit; gates are never inferred).")
    attestation_build.add_argument("--output", required=True, help="Destination path for RELEASE-ATTESTATION.json (atomic write).")
    attestation_verify = sub.add_parser("verify-release-attestation")
    attestation_verify.add_argument("--input", required=True, help="Attestation artifact to verify.")
    # v1.2.37 FP-read-lane: sanctioned read-only diagnostics (no migrate, no
    # store writes — mode=ro only).
    events = sub.add_parser("events", help="Read-only: list policy events as NDJSON.")
    events.add_argument("--task", default=None, help="Filter by task_id.")
    events.add_argument("--kind", default=None, help="Filter by event kind, e.g. policy_decision.")
    events.add_argument("--rule", default=None, help="Filter by payload rule_id.")
    events.add_argument("--decision", default=None, help="Filter by payload decision (allow/deny/approval_required).")
    events.add_argument("--since", default=None, help="ISO-8601 created_at lower bound, e.g. 2026-10-04.")
    events.add_argument("--limit", type=int, default=50, help="Max events (1..500, default 50).")
    task_view = sub.add_parser("task", help="Read-only: resolved policy view of one card.")
    task_view.add_argument("--id", dest="task_id", default=None, help="Task id; defaults to HERMES_KANBAN_TASK.")
    task_view.add_argument("--board", default=None, help="Board slug; defaults to HERMES_KANBAN_BOARD.")
    show = sub.add_parser("show", help="Read-only: one event / approvals of a task / effective config.")
    show.add_argument("--event", dest="event_id", default=None, help="Event id to dump in full.")
    show.add_argument("--approvals-for", dest="approvals_task", default=None, help="List approval bindings of a task.")
    show.add_argument("--config", dest="show_config", action="store_true", help="Print the effective operational config.")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.version:
        print(json.dumps({"version": __version__}))
        return 0
    if not args.command:
        parser().error("a command is required")

    if args.command == "build-bundle":
        from .release_bundle import build_release_bundle
        files = build_release_bundle(default_root(args), Path(args.output))
        print(json.dumps({"output": str(Path(args.output)), "files": len(files)}, ensure_ascii=False))
        return 0
    if args.command == "verify-bundle":
        from .release_bundle import verify_release_bundle
        files = verify_release_bundle(Path(args.bundle))
        print(json.dumps({"bundle": str(Path(args.bundle)), "files": len(files), "ok": True}, ensure_ascii=False))
        return 0
    if args.command == "build-release-attestation":
        from .release_attestation import AttestationError, build_attestation_file
        try:
            digest = build_attestation_file(Path(args.input), Path(args.output))
        except AttestationError as exc:
            print(json.dumps({"ok": False, "errors": exc.errors}, ensure_ascii=False, sort_keys=True))
            return 1
        print(json.dumps({"ok": True, "output": str(Path(args.output)), "attestation_sha256": digest},
                         ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "verify-release-attestation":
        from .release_attestation import AttestationError, verify_attestation_file
        try:
            artifact = verify_attestation_file(Path(args.input))
        except AttestationError as exc:
            print(json.dumps({"ok": False, "errors": exc.errors}, ensure_ascii=False, sort_keys=True))
            return 1
        print(json.dumps({"ok": True, "input": str(Path(args.input)),
                          "attestation_sha256": artifact["attestation_sha256"]},
                         ensure_ascii=False, sort_keys=True))
        return 0

    # v1.2.37 FP-read-lane: read-only views never construct FleetPolicyRuntime
    # (its store.migrate() writes); they open the store mode=ro directly.
    if args.command == "events":
        return cmd_events(args)
    if args.command == "task":
        return cmd_task(args)
    if args.command == "show":
        if not (args.event_id or args.approvals_task or args.show_config):
            print(json.dumps({"ok": False, "error": "show requires --event, --approvals-for or --config"},
                             ensure_ascii=False))
            return 2
        return cmd_show(args)

    runtime = FleetPolicyRuntime(default_root(args))
    if args.command in {"approve", "reject"}:
        if not sys.stdin.isatty():
            print(json.dumps({"ok": False, "rule_key": args.rule_key,
                              "reason": "approval decisions require an interactive owner terminal (no TTY)"},
                             ensure_ascii=False))
            return 2
        ok = runtime.store.decide_approval(args.rule_key, args.command == "approve", args.by,
                                           confirm_code=args.confirm)
        payload = {"ok": ok, "rule_key": args.rule_key, "decision": args.command}
        if not ok:
            payload["reason"] = "binding missing, already decided, or confirmation code invalid (expected the binding's last 8 characters)"
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if ok else 2
    if args.command == "revoke":
        if not sys.stdin.isatty():
            print(json.dumps({"ok": False, "rule_key": args.rule_key,
                              "reason": "revocation requires an interactive owner terminal (no TTY)"},
                             ensure_ascii=False))
            return 2
        ok = runtime.store.revoke_approval(args.rule_key, args.by, confirm_code=args.confirm)
        payload = {"ok": ok, "rule_key": args.rule_key, "decision": "revoked"}
        if not ok:
            payload["reason"] = "binding missing, already consumed/rejected/revoked, or confirmation code invalid"
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if ok else 2
    if args.command == "drain-notifications":
        projector = HermesProjector()
        # v1.2.14: expire approval bindings whose cards are provably closed
        # BEFORE draining, so the delivered counters and the owner's inbox
        # only ever describe live work. Failures here are non-fatal: the
        # drain below still runs on the untouched store.
        try:
            expired = projector.expire_closed_approvals(runtime.store)
        except Exception:
            expired = 0
        sent = projector.drain_company(runtime.store, profile=runtime.config["notifications"]["profile"])
        print(json.dumps({"sent": sent, "approvals_expired": expired}))
        return 0
    if args.command == "fail-notifications":
        if getattr(args, "all_pending", False):
            failed = sum(1 for row in runtime.store.pending_notifications() if runtime.store.mark_notification(row["event_id"], "failed"))
            print(json.dumps({"failed": failed}))
            return 0
        print(json.dumps({"ok": False, "reason": "pass --all-pending"}))
        return 2
    if args.command == "grant-capability":
        ok = runtime.store.grant_capability(args.capability_id, args.project, args.kind, args.scope, args.by)
        print(json.dumps({"ok": ok, "capability_id": args.capability_id, "project": args.project}))
        return 0 if ok else 2
    if args.command == "override-expected-failure":
        if os.environ.get("HERMES_KANBAN_TASK"):
            print(json.dumps({"ok": False, "reason": "expected-failure overrides cannot be made from a dispatcher worker context"}, ensure_ascii=False))
            return 2
        ok = runtime.store.mark_expected_failure(args.task_id, args.failure_signature, args.run_key,
                                                 confirm_code=args.confirm)
        payload = {"ok": ok, "task_id": args.task_id, "failure_signature": args.failure_signature, "run_key": args.run_key}
        if not ok:
            payload["reason"] = "override already recorded (idempotent), or confirmation code invalid (expected the binding key's last 8 characters)"
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if ok else 2
    if args.command == "spend-status":
        from datetime import datetime, timezone
        month = datetime.now(timezone.utc).strftime("%Y-%m")
        spent = runtime.store.monthly_spend(args.project, month)
        limit = int(runtime.config["financial_mandate"]["max_monthly_per_project"])
        print(json.dumps({"project": args.project, "month": month, "spent_rub": spent, "remaining_rub": max(0, limit-spent), "limit_rub": limit}))
        return 0
    if args.command == "retention":
        cfg = runtime.config["retention"]
        print(json.dumps(runtime.store.retention(cfg["events_days"], cfg["call_history_days"], cfg["approvals_days"])))
        return 0
    if args.command == "drift-check":
        missing = approval_drift(default_root(args), runtime.config)
        print(json.dumps({"ok": not missing, "missing": missing}, ensure_ascii=False, sort_keys=True))
        return 0 if not missing else 1
    with runtime.store.connect() as connection:
        counts = {
            "events": connection.execute("SELECT COUNT(*) FROM events").fetchone()[0],
            "approvals_pending": connection.execute("SELECT COUNT(*) FROM approvals WHERE status='pending'").fetchone()[0],
            "notifications_pending": connection.execute("SELECT COUNT(*) FROM notification_outbox WHERE status='pending'").fetchone()[0],
        }
    counts.update({f"notifications_{name}": value for name, value in runtime.store.notification_counts().items()})
    print(json.dumps(counts, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
