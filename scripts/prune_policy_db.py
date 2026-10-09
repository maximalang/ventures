"""prune_policy_db.py — OPERATOR-ONLY one-time prune of the live fleet-policy
event store (card t_40022daf, DEFECT-2b; built on the v1.2.42 maintenance
machinery of card t_1d99b96b).

WHO RUNS THIS: the company OPERATOR session (interactive, non-worker), the
same contract as deploy_policy.sh. A dispatcher worker touching the live
store is denied by the policy gate itself (`**/.state/fleet-policy.db*` is a
protected path) — intentional.

WHAT IT DOES, in order, each step verified before the next:
  1. pre-flight read: db size, page/freelist stats, per-table row counts;
  2. byte backup: SQLite online-backup API snapshot into
     `<db dir>/fleet-policy-backups/prune-<UTC stamp>/fleet-policy.db`,
     then MANIFEST.json + MANIFEST.sha256 over every artifact in the dir;
  3. maintenance tick (forced, preserve_state=True): expired events
     archived to verified JSONL.gz + .sha256 sidecars BEFORE deletion,
     expired rows of the ledger tables (call_history / run_call_history /
     budget_ledger / run_budget / financial_ledger) deleted per the
     retention config, WAL checkpoint; the protected state tables
     (task_state / run_state / approvals / notification_outbox) are never
     deleted from — their horizon expiry stays the scheduled tick's job;
  4. full VACUUM (activates auto_vacuum on legacy stores);
  5. post-checks: size/counts delta, every archive sidecar re-verified,
     report JSON printed and written next to the backup.

Usage:
  python scripts/prune_policy_db.py --root C:/Users/max/Desktop/all/ventures --dry-run
  python scripts/prune_policy_db.py --root C:/Users/max/Desktop/all/ventures --yes

Rollback: stop writers, copy the backup over the live path, restart the
gateway. The backup is a consistent snapshot (backup API), not a file copy
of a live WAL pair.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from fleet_policy.maintenance import verify_archive  # noqa: E402
from fleet_policy.runtime import FleetPolicyRuntime  # noqa: E402

TABLES = (
    "events", "call_history", "run_call_history", "budget_ledger",
    "run_budget", "financial_ledger", "task_state", "run_state",
    "approvals", "notification_outbox", "maintenance_state",
)

# Protected state tables (card t_40022daf D2-b acceptance): the one-time
# prune must leave these byte-for-byte intact. The forced maintenance tick
# runs with preserve_state=True so retention never issues a DELETE against
# them; the report captures pre/post counts and the tripwire below aborts
# the run if any of them moved. maintenance_state is deliberately NOT in
# this set: the tick legitimately stamps its own throttle keys there — it
# is covered by TABLES preflight counts for observability only.
PROTECTED_STATE_TABLES = (
    "task_state", "run_state", "approvals", "notification_outbox",
)


def _state_preservation(pre_counts: dict[str, int], post_counts: dict[str, int]) -> dict[str, dict[str, Any]]:
    """Per-protected-table before/after counts with an ok flag. This is the
    report's assertion surface for the D2-b acceptance (state tables
    unchanged): a False ok anywhere must abort the run below."""
    return {
        table: {
            "pre": int(pre_counts.get(table, 0)),
            "post": int(post_counts.get(table, 0)),
            "ok": int(pre_counts.get(table, 0)) == int(post_counts.get(table, 0)),
        }
        for table in PROTECTED_STATE_TABLES
    }


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _table_counts(db: sqlite3.Connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in TABLES:
        try:
            counts[table] = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        except sqlite3.Error:
            counts[table] = -1
    return counts


def _preflight(db_path: Path) -> dict:
    uri = f"file:{db_path.as_posix()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as db:
        report = {
            "db_path": str(db_path),
            "db_size_bytes": db_path.stat().st_size,
            "page_count": db.execute("PRAGMA page_count").fetchone()[0],
            "freelist_pages": db.execute("PRAGMA freelist_count").fetchone()[0],
            "counts": _table_counts(db),
        }
    return report


def _write_manifest(backup_dir: Path, extra: dict) -> dict:
    entries = []
    for path in sorted(backup_dir.rglob("*")):
        if path.is_file() and path.name not in {"MANIFEST.json", "MANIFEST.sha256"}:
            entries.append({
                "file": path.relative_to(backup_dir).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            })
    manifest = {"created_at": _utc_stamp(), **extra, "artifacts": entries}
    (backup_dir / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [f"{item['sha256']}  {item['file']}" for item in entries]
    (backup_dir / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="ascii")
    return manifest


def run(root: Path, *, dry_run: bool) -> dict:
    runtime = FleetPolicyRuntime(root)
    db_path = runtime.store.path
    report: dict = {"root": str(root), "dry_run": dry_run, "steps": []}
    pre = _preflight(db_path)
    report["pre"] = pre
    backup_dir = db_path.parent / "fleet-policy-backups" / f"prune-{_utc_stamp()}"
    report["backup_dir"] = str(backup_dir)
    if dry_run:
        report["steps"] = [
            "backup: sqlite3 backup API snapshot + MANIFEST sha256",
            "maintenance: forced tick (archive expired events w/ verify, ledger retention, state tables preserved, wal checkpoint)",
            "vacuum: full VACUUM (activates auto_vacuum on legacy stores)",
            "post: size/counts delta + archive sidecar re-verify + report file",
        ]
        return report

    # step 2 — verified backup before any deletion
    backup_dir.mkdir(parents=True, exist_ok=False)
    backup_db = backup_dir / "fleet-policy.db"
    with runtime.store.connect() as source, sqlite3.connect(str(backup_db)) as target:
        source.backup(target)
    report["backup_sha256"] = _sha256(backup_db)
    report["backup_bytes"] = backup_db.stat().st_size

    # step 3 — forced maintenance tick (archive -> verify -> delete) in the
    # one-time-prune posture: the ledger backlog drains per the retention
    # config, the protected state tables are never deleted from
    # (preserve_state=True).
    maintenance_report = runtime.maybe_maintenance(
        None, force=True, source="one-time-prune", preserve_state=True
    )
    report["maintenance"] = maintenance_report
    if maintenance_report.get("error") or maintenance_report.get("errors"):
        report["aborted"] = "maintenance reported errors; DB left unvacuumed, backup intact"
        report["state_preservation"] = _state_preservation(
            report["pre"]["counts"], _preflight(db_path)["counts"]
        )
        _write_manifest(backup_dir, {"aborted": True, "db_path": str(db_path)})
        return report

    # step 4 — full vacuum
    runtime.store.full_vacuum()

    # step 5 — post-checks: re-verify every archive sidecar produced by the run
    archive_dir = db_path.parent / "fleet-policy-archive"
    reverify = []
    for item in maintenance_report.get("archives", []):
        path = archive_dir / item["file"]
        ok, sha = verify_archive(path, int(item["rows"]))
        reverify.append({"file": item["file"], "ok": bool(ok and sha == item["sha256"])})
    report["archive_reverify"] = reverify
    if not all(item["ok"] for item in reverify):
        report["aborted"] = "archive re-verification failed post-run; rows already deleted, restore from backup if needed"
        _write_manifest(backup_dir, {"aborted": True, "db_path": str(db_path)})
        return report

    post = _preflight(db_path)
    report["post"] = post
    # Tripwire (card t_40022daf D2-b acceptance, QA F1): the protected state
    # tables must come through the prune with their row counts exactly
    # intact. preserve_state=True makes the deletion structurally
    # impossible; this assertion is the loud alarm if that ever regresses.
    preservation = _state_preservation(report["pre"]["counts"], post["counts"])
    report["state_preservation"] = preservation
    violated = [table for table, check in preservation.items() if not check["ok"]]
    if violated:
        report["aborted"] = (
            "state preservation violated for: " + ", ".join(violated)
            + "; restore from the backup snapshot before re-running"
        )
        _write_manifest(backup_dir, {"aborted": True, "db_path": str(db_path), "state_preservation": preservation})
        return report
    report["size_delta_bytes"] = pre["db_size_bytes"] - post["db_size_bytes"]
    report["counts_delta"] = {
        table: pre["counts"].get(table, 0) - post["counts"].get(table, 0) for table in TABLES
    }
    _write_manifest(backup_dir, {"db_path": str(db_path), "prune_report_size_delta_bytes": report["size_delta_bytes"]})
    (backup_dir / "PRUNE-REPORT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="one-time verified prune of the live fleet-policy store")
    parser.add_argument("--root", required=True, help="ventures root containing .state/fleet-policy.db")
    parser.add_argument("--dry-run", action="store_true", help="pre-flight only; no writes")
    parser.add_argument("--yes", action="store_true", help="execute the prune (operator confirmation)")
    args = parser.parse_args(argv)
    if not args.dry_run and not args.yes:
        parser.error("refusing to run: pass --dry-run for pre-flight or --yes to execute")
    report = run(Path(args.root), dry_run=args.dry_run)
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    if report.get("aborted"):
        return 1
    maintenance = report.get("maintenance") or {}
    return 1 if maintenance.get("error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
