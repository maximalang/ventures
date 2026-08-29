from __future__ import annotations

import argparse
import json
from pathlib import Path

from .drift import approval_drift
from .projector import HermesProjector
from .runtime import FleetPolicyRuntime


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="fleet-policy")
    result.add_argument("--root", default="C:/Users/max/Desktop/all/ventures")
    sub = result.add_subparsers(dest="command", required=True)
    approve = sub.add_parser("approve")
    approve.add_argument("rule_key")
    approve.add_argument("--by", default="user")
    reject = sub.add_parser("reject")
    reject.add_argument("rule_key")
    reject.add_argument("--by", default="user")
    sub.add_parser("drain-notifications")
    suppress = sub.add_parser("fail-notifications")
    suppress.add_argument("--all-pending", action="store_true")
    grant = sub.add_parser("grant-capability")
    grant.add_argument("capability_id")
    grant.add_argument("--project", required=True)
    grant.add_argument("--kind", required=True)
    grant.add_argument("--scope", required=True)
    grant.add_argument("--by", default="user")
    spend = sub.add_parser("spend-status")
    spend.add_argument("--project", required=True)
    sub.add_parser("retention")
    sub.add_parser("status")
    sub.add_parser("drift-check")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    runtime = FleetPolicyRuntime(Path(args.root))
    if args.command in {"approve", "reject"}:
        ok = runtime.store.decide_approval(args.rule_key, args.command == "approve", args.by)
        print(json.dumps({"ok": ok, "rule_key": args.rule_key, "decision": args.command}, ensure_ascii=False))
        return 0 if ok else 2
    if args.command == "drain-notifications":
        sent = HermesProjector().drain_company(runtime.store, profile=runtime.config["notifications"]["profile"])
        print(json.dumps({"sent": sent}))
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
        missing = approval_drift(Path(args.root), runtime.config)
        print(json.dumps({"ok": not missing, "missing": missing}, ensure_ascii=False, sort_keys=True))
        return 0 if not missing else 1
    with runtime.store.connect() as connection:
        counts = {
            "events": connection.execute("SELECT COUNT(*) FROM events").fetchone()[0],
            "approvals_pending": connection.execute("SELECT COUNT(*) FROM approvals WHERE status='pending'").fetchone()[0],
            "notifications_pending": connection.execute("SELECT COUNT(*) FROM notification_outbox WHERE status='pending'").fetchone()[0],
        }
    print(json.dumps(counts, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
