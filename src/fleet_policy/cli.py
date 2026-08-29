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
