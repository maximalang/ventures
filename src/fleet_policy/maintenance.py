"""v1.2.42 — built-in event retention, verified archive, and DB size guard.

Root cause (2026-10-07 deny-triage stall, fleet-fast-watch): the policy event
store grew unbounded (2.8 GB at the incident, 513 MB after the emergency
manual trim) because retention existed only as a hand-run CLI command and the
schema never shipped the events(created_at) hot-path index. This module makes
the storage manifesto a built-in feature of the storage layer:

- retention runs from plugin hooks (register / kanban_task_claimed) and the
  operator CLI, throttled by the maintenance_state ledger — never dependent
  on an external cron;
- expired events are exported to compressed JSONL with a sha256 sidecar and
  the archive is verified (hash + gzip decode + row count) BEFORE any row is
  deleted, so history stays restorable for legal/incident review;
- a size guard warns at the soft cap and forces an immediate retention run at
  the hard cap, notifying through the existing significant-event lane
  (notification_outbox -> drain-notifications), deduplicated per UTC day;
- a maintenance failure never crashes the gate: maybe_run() returns a report
  dict and never raises.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .redaction import stable_id
from .storage import PolicyStore, utc_now

DEFAULTS: dict[str, Any] = {
    "events_days": 90,
    "call_history_days": 30,
    "approvals_days": 365,
    # None = sibling of the live database (<db dir>/fleet-policy-archive);
    # a relative config value resolves against the runtime root.
    "archive_dir": None,
    "interval_hours": 24,
    "batch_size": 10000,
    "max_batches": 20,
    "soft_cap_mb": 100,
    "hard_cap_mb": 300,
    "vacuum_freelist_pages": 10000,
    "vacuum_max_pages": 65536,
    "notify_board": "fleet-ops",
    "notify_task_id": "",
}

LAST_RUN_KEY = "retention_last_run_epoch"


def resolved(config: dict[str, Any]) -> dict[str, Any]:
    """Merge the optional config ``retention`` section over DEFAULTS.

    Unknown keys are ignored and every key is optional, so a v1.2.38 config
    keeps working unchanged (code defaults carry the spec values)."""
    merged = dict(DEFAULTS)
    raw = config.get("retention") if isinstance(config, dict) else None
    if isinstance(raw, dict):
        for key, value in raw.items():
            if key in merged and value is not None:
                merged[key] = value
    return merged


def _epoch(value: str | None) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _archive_root(store: PolicyStore, cfg: dict[str, Any]) -> Path:
    raw_value = cfg.get("archive_dir")
    if not raw_value:
        return store.path.parent / "fleet-policy-archive"
    raw = Path(str(raw_value))
    if raw.is_absolute():
        return raw
    # Convention: the store lives at <root>/.state/fleet-policy.db, so a
    # relative archive_dir resolves against the runtime root.
    return (store.path.parent.parent / raw).resolve()


def _write_archive_batch(rows: list, archive_dir: Path, seq: int) -> tuple[Path, str]:
    """Write one batch as deterministic gzip JSONL next to a .tmp marker,
    then atomically rename. Returns (path, sha256-of-file-bytes)."""
    stamp = utc_now().replace("-", "").replace(":", "")
    first = str(rows[0]["event_id"])
    last = str(rows[-1]["event_id"])
    name = f"events-{stamp}-{seq:03d}-{stable_id(first, last)[:8]}.jsonl.gz"
    target = archive_dir / name
    tmp = archive_dir / (name + ".tmp")
    digest = hashlib.sha256()
    try:
        with tmp.open("wb") as raw_handle:
            # mtime=0 keeps archives byte-deterministic: the same rows always
            # produce the same sha256, which makes cross-copy audit trivial.
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0) as stream:
                for row in rows:
                    payload = {key: row[key] for key in row.keys()}
                    stream.write((json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
        data = tmp.read_bytes()
        digest.update(data)
        sha = digest.hexdigest()
        sidecar = target.with_name(target.name + ".sha256")
        sidecar.write_text(f"{sha}  {name}\n", encoding="ascii")
        tmp.replace(target)
        return target, sha
    except Exception:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def verify_archive(path: Path, expected_rows: int) -> tuple[bool, str]:
    """Read-back verification gate for deletion: the archived file's sha256
    must match its sidecar AND the gzip stream must decode to exactly
    ``expected_rows`` lines. Rows are deleted only after this passes."""
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        sha = digest.hexdigest()
        sidecar = path.with_name(path.name + ".sha256").read_text(encoding="ascii").split()[0]
        if sha != sidecar:
            return False, sha
        rows = 0
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            for _line in stream:
                rows += 1
        return rows == expected_rows, sha
    except (OSError, ValueError, EOFError):
        return False, ""


def _archive_expired_events(store: PolicyStore, cfg: dict[str, Any], cutoff: str,
                            report: dict[str, Any]) -> int:
    archive_dir = _archive_root(store, cfg)
    archive_dir.mkdir(parents=True, exist_ok=True)
    batch_size = int(cfg["batch_size"])
    archived = 0
    for seq in range(int(cfg["max_batches"])):
        rows = store.events_before(cutoff, batch_size)
        if not rows:
            break
        path, sha = _write_archive_batch(rows, archive_dir, seq)
        ok, verified_sha = verify_archive(path, len(rows))
        if not ok or verified_sha != sha:
            # Fail closed: keep every row, surface the defect, retry next tick.
            report.setdefault("errors", []).append(f"archive verification failed: {path.name}")
            break
        removed = store.delete_events_by_ids([str(row["event_id"]) for row in rows])
        archived += removed
        with (archive_dir / "manifest.jsonl").open("a", encoding="utf-8") as manifest:
            manifest.write(json.dumps({
                "file": path.name, "sha256": sha, "rows": removed,
                "first_created_at": rows[0]["created_at"],
                "last_created_at": rows[-1]["created_at"],
                "archived_at": utc_now(),
            }, sort_keys=True) + "\n")
        report.setdefault("archives", []).append({"file": path.name, "rows": removed, "sha256": sha})
        if len(rows) < batch_size:
            break
    return archived


def _notify_size_guard(store: PolicyStore, cfg: dict[str, Any], context: dict[str, Any] | None,
                       level: str, size_bytes: int) -> bool:
    """Emit one significant event per UTC day per level through the existing
    notification lane. Significance requires a deliverable binding: the
    configured standing card, else the hook context's task; without either the
    event stays audit-only instead of parking an undeliverable outbox row."""
    cap_mb = int(cfg[f"{level}_cap_mb"])
    day = utc_now()[:10]
    board = str(cfg.get("notify_board") or "")
    task_id = str(cfg.get("notify_task_id") or "")
    if not task_id and context:
        task_id = str(context.get("task_id") or "")
        board = board or str(context.get("board") or "")
    payload = {
        "decision": "warn",
        "rule_id": f"db_size_{level}_cap",
        "reason": f"fleet-policy event store at {size_bytes // (1024 * 1024)} MB ({level} cap {cap_mb} MB)",
        "action": "maintenance",
        "target": "events",
        "task_id": task_id,
        "board": board,
    }
    return store.record_event(
        stable_id("db_size_guard", level, day), day,
        task_id or None, "maintenance_size_guard", payload, bool(board and task_id),
    )


def maybe_run(store: PolicyStore, config: dict[str, Any], *,
              context: dict[str, Any] | None = None, force: bool = False,
              now: datetime | None = None, source: str = "") -> dict[str, Any]:
    """Throttled maintenance tick. Called from plugin hooks (register,
    kanban_task_claimed) and the operator CLI. Never raises: the gate must
    survive a broken maintenance path, so every failure lands in the report."""
    report: dict[str, Any] = {
        "ran": False, "forced": bool(force), "source": source,
        "archived_events": 0, "deleted": {}, "notices": [],
    }
    try:
        cfg = resolved(config)
        now = now or datetime.now(timezone.utc)
        size_before = store.db_size_bytes()
        report["db_size_bytes"] = size_before
        soft = int(cfg["soft_cap_mb"]) * 1024 * 1024
        hard = int(cfg["hard_cap_mb"]) * 1024 * 1024

        last = _epoch(store.maintenance_get(LAST_RUN_KEY))
        due = (now.timestamp() - last) >= int(cfg["interval_hours"]) * 3600
        forced_by_size = size_before >= hard
        if forced_by_size:
            if _notify_size_guard(store, cfg, context, "hard", size_before):
                report["notices"].append("hard")
        if not force and not due and not forced_by_size:
            report["skipped"] = "interval"
            return report

        report["ran"] = True
        cutoff = (now - timedelta(days=int(cfg["events_days"]))).isoformat(timespec="seconds").replace("+00:00", "Z")
        report["archived_events"] = _archive_expired_events(store, cfg, cutoff, report)
        report["deleted"] = store.retention(
            int(cfg["events_days"]), int(cfg["call_history_days"]), int(cfg["approvals_days"]),
            now=now, skip_events=True,
        )
        store.wal_checkpoint_truncate()
        freelist = store.freelist_pages()
        report["freelist_pages"] = freelist
        if freelist >= int(cfg["vacuum_freelist_pages"]):
            store.incremental_vacuum(min(freelist, int(cfg["vacuum_max_pages"])))
        store.maintenance_set(LAST_RUN_KEY, str(now.timestamp()))

        size_after = store.db_size_bytes()
        report["db_size_bytes_after"] = size_after
        if "hard" not in report["notices"] and size_after >= soft:
            if _notify_size_guard(store, cfg, context, "soft", size_after):
                report["notices"].append("soft")
        store.record_event(
            stable_id("maintenance_run", utc_now(), source), utc_now(), None,
            "maintenance_run", {
                "source": source, "archived_events": report["archived_events"],
                "db_size_bytes": size_before, "db_size_bytes_after": size_after,
                "errors": report.get("errors", []),
            }, False,
        )
    except Exception as exc:  # the gate never crashes on maintenance
        report["error"] = f"{type(exc).__name__}: {exc}"
    return report
