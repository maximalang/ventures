from __future__ import annotations

import argparse
import json
import os
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
    spend = sub.add_parser("spend-status")
    spend.add_argument("--project", required=True)
    sub.add_parser("retention")
    sub.add_parser("status")
    sub.add_parser("drift-check")
    bundle = sub.add_parser("build-bundle")
    bundle.add_argument("--output", required=True)
    verify = sub.add_parser("verify-bundle")
    verify.add_argument("--bundle", required=True)
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
        missing = approval_drift(default_root(args), runtime.config)
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
