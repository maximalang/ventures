#!/usr/bin/env python3
"""Alert triage v1 for the hooks-tunnel fleet-alert route.

README
======

Purpose
    Thin stdin -> stdout alert triage for the Hermes hooks-tunnel contour:
    dedup (sha256 of the normalized text, 24 h TTL), rate limit
    (30 deliveries per rolling minute, TG channel "Bot Chat"), quiet hours
    (23:00-08:00 RTZ, Europe/Moscow == fixed UTC+3, no DST since 2014) and
    severity routing. Stdlib only (sqlite3, hashlib, json, argparse).

Severity routing
    urgent       -> delivered immediately; the ONLY severity delivered
                    during quiet hours (critical-incident exception)
    high         -> delivered inside the window; during quiet hours the
                    alert is deferred and flushed by the next ``process``
                    run outside quiet hours
    medium / low -> queued into the daily digest (a 09:00 RTZ cron runs
                    ``digest``; scheduling itself is out of scope here)

Usage
    python alert_triage.py process < events.jsonl   # one JSON object per line
    python alert_triage.py digest                   # flush queued medium/low

    Options (both commands):
      --db PATH    state DB (default: alert_triage.db next to this module)
      --now ISO    processing-time override, ISO-8601 (tests / cron replay)

Event format (JSONL, one object per line)
    {"severity": "high", "text": "...", "source": "...", "ts": "..."}
    ``severity`` and ``text`` are required; ``source``/``ts`` are optional
    metadata echoed into the output.

Output (JSON lines on stdout)
    process:
      {"action": "deliver", ...}             routed onward (tunnel -> TG)
      {"action": "digest", ...}              queued for the daily digest
      {"action": "deferred", ...}            quiet hours; flushed later
      {"action": "rate_limited", ...}        30/min budget spent; flushed later
      {"action": "suppress_duplicate", ...}  same normalized text within 24 h
      {"action": "invalid", ...}             unparsable line / bad severity
      Pending deferred / rate_limited alerts are flushed first (as extra
      "deliver" lines with "source": "pending") when a ``process`` run has
      delivery budget; urgent pending items flush even during quiet hours.
    digest:
      one {"action": "digest_report", "count": N, "items": [...]} line when
      there are queued items; no output otherwise (cron-friendly).

Wiring into hooks-tunnel (route fleet-alert)
    The fleet-alert route handler serializes the incoming webhook alert as
    a single JSONL line and pipes it through this module; the tunnel already
    forwards stdout to the TG channel, so every emitted "deliver" /
    "digest_report" line lands in "Bot Chat". One-line pipe in the route
    handler:

        alert_jsonl | python scripts/hooks-tunnel/alert_triage.py process

    plus a daily 09:00 RTZ cron for ``digest``. State lives in
    alert_triage.db (SQLite) next to this module. NOTE: the live tunnel is
    NOT modified by this module; wiring is a separate step after review.

Attribution
    Pattern: SenteLabsAI/OpenExecutive (Apache-2.0, head b071101),
    alerts/pipeline.py - rate limit, dedup, severity, quiet hours.
    Independent thin reimplementation for the Hermes contour; no code was
    copied. Dedup here keys on sha256 of the normalized text instead of
    external_id because the fleet-alert webhook does not guarantee a
    stable id.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

# --- policy constants (company decision, card t_e0059fc0) -----------------
RTZ = timezone(timedelta(hours=3), name="RTZ")  # Europe/Moscow, fixed UTC+3
QUIET_START_HOUR = 23  # quiet hours: [23:00, 08:00) RTZ
QUIET_END_HOUR = 8
DEDUP_TTL = timedelta(hours=24)
RATE_LIMIT = 30  # deliveries per rolling window (TG channel "Bot Chat")
RATE_WINDOW = timedelta(minutes=1)
SEVERITIES = ("low", "medium", "high", "urgent")
DIGEST_SEVERITIES = ("low", "medium")

DEFAULT_DB = Path(__file__).resolve().with_name("alert_triage.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ts           TEXT NOT NULL,             -- processing time, ISO UTC
    severity     TEXT NOT NULL,
    text         TEXT NOT NULL,
    source       TEXT NOT NULL DEFAULT '',
    ts_event     TEXT NOT NULL DEFAULT '',
    hash         TEXT NOT NULL DEFAULT '',
    action       TEXT NOT NULL,             -- deliver|digest|deferred|rate_limited
    delivered    INTEGER NOT NULL DEFAULT 0,
    delivered_ts TEXT                       -- ISO UTC; set when actually emitted
);
CREATE INDEX IF NOT EXISTS idx_events_hash ON events (hash, ts);
CREATE INDEX IF NOT EXISTS idx_events_pending ON events (delivered, action);
CREATE INDEX IF NOT EXISTS idx_events_rate ON events (action, delivered, delivered_ts);
"""


# --- time / text helpers ----------------------------------------------------
def parse_now(value: str | None) -> datetime:
    """Processing time as aware UTC datetime; --now accepts ISO-8601."""
    if value is None:
        return datetime.now(timezone.utc)
    text = value.strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat()


def normalize_text(text: str) -> str:
    """Dedup normalization: strip, casefold-level lower, collapse whitespace.

    Deliberately conservative (no digit/hex masking): the kill criterion for
    v1 is <5% false-positive swallowing, and masking volatile ids would merge
    genuinely distinct alerts (e.g. two different PR numbers).
    """
    return " ".join(str(text).strip().lower().split())


def fingerprint(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()


def is_quiet_hours(now: datetime) -> bool:
    """True inside [23:00, 08:00) RTZ (Europe/Moscow, fixed UTC+3)."""
    local = now.astimezone(RTZ)
    return local.hour >= QUIET_START_HOUR or local.hour < QUIET_END_HOUR


# --- state ------------------------------------------------------------------
def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


def _prune(conn: sqlite3.Connection, now: datetime) -> None:
    """Drop finished rows past the dedup TTL; pending rows are never pruned."""
    cutoff = _iso(now - DEDUP_TTL)
    conn.execute(
        "DELETE FROM events WHERE delivered = 1 AND ts < ?", (cutoff,)
    )


def _duplicate_seen(conn: sqlite3.Connection, digest_hex: str, now: datetime) -> bool:
    cutoff = _iso(now - DEDUP_TTL)
    row = conn.execute(
        "SELECT 1 FROM events WHERE hash = ? AND ts >= ? LIMIT 1",
        (digest_hex, cutoff),
    ).fetchone()
    return row is not None


def _deliveries_in_window(conn: sqlite3.Connection, now: datetime) -> int:
    cutoff = _iso(now - RATE_WINDOW)
    row = conn.execute(
        "SELECT COUNT(*) FROM events"
        " WHERE action = 'deliver' AND delivered = 1 AND delivered_ts >= ?",
        (cutoff,),
    ).fetchone()
    return int(row[0]) if row else 0


def _insert(
    conn: sqlite3.Connection,
    now: datetime,
    event: dict,
    action: str,
    *,
    delivered: bool,
    delivered_ts: datetime | None = None,
) -> None:
    conn.execute(
        "INSERT INTO events (ts, severity, text, source, ts_event, hash,"
        " action, delivered, delivered_ts)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            _iso(now),
            event["severity"],
            event["text"],
            event.get("source", "") or "",
            event.get("ts", "") or "",
            fingerprint(event["text"]),
            action,
            1 if delivered else 0,
            _iso(delivered_ts) if delivered_ts is not None else None,
        ),
    )


def _emit_base(row_action: str, event: dict, now: datetime) -> dict:
    out = {
        "action": row_action,
        "severity": event["severity"],
        "text": event["text"],
        "processed_at": _iso(now),
    }
    if event.get("source"):
        out["source"] = event["source"]
    if event.get("ts"):
        out["ts_event"] = event["ts"]
    return out


# --- core pipeline ----------------------------------------------------------
def _flush_pending(
    conn: sqlite3.Connection, now: datetime, budget: int, quiet: bool
) -> tuple[list[dict], int]:
    """Re-emit deferred / rate_limited alerts while delivery budget allows.

    Outside quiet hours every pending item may flush; during quiet hours only
    pending urgent items (the critical-incident exception).
    """
    results: list[dict] = []
    if budget <= 0:
        return results, budget
    sql = (
        "SELECT id, severity, text, source, ts_event FROM events"
        " WHERE delivered = 0 AND action IN ('deferred', 'rate_limited')"
    )
    params: tuple = ()
    if quiet:
        sql += " AND severity = 'urgent'"
    sql += " ORDER BY id"
    rows = conn.execute(sql, params).fetchall()
    for row_id, severity, text, source, ts_event in rows:
        if budget <= 0:
            break
        conn.execute(
            "UPDATE events SET delivered = 1, delivered_ts = ? WHERE id = ?",
            (_iso(now), row_id),
        )
        out = {
            "action": "deliver",
            "source": "pending",
            "severity": severity,
            "text": text,
            "processed_at": _iso(now),
        }
        if source:
            out["alert_source"] = source
        if ts_event:
            out["ts_event"] = ts_event
        results.append(out)
        budget -= 1
    return results, budget


def _parse_event(line: str) -> tuple[dict | None, str | None]:
    line = line.strip()
    if not line:
        return None, None  # skip blank lines silently
    try:
        event = json.loads(line)
    except (json.JSONDecodeError, ValueError) as exc:
        return None, f"unparsable JSON: {exc}"
    if not isinstance(event, dict):
        return None, "event is not a JSON object"
    severity = event.get("severity")
    if severity not in SEVERITIES:
        return None, f"severity {severity!r} not in {SEVERITIES}"
    text = event.get("text")
    if not isinstance(text, str) or not text.strip():
        return None, "missing or empty 'text'"
    return event, None


def process_stream(
    db_path: str | Path, lines: Iterable[str], now: datetime
) -> list[dict]:
    """Triage JSONL events; pure stdin->stdout core (state in SQLite)."""
    now = now.astimezone(timezone.utc)
    quiet = is_quiet_hours(now)
    conn = connect(db_path)
    try:
        _prune(conn, now)
        budget = RATE_LIMIT - _deliveries_in_window(conn, now)
        results, budget = _flush_pending(conn, now, budget, quiet)

        for line in lines:
            event, error = _parse_event(line)
            if event is None:
                if error is not None:
                    results.append(
                        {
                            "action": "invalid",
                            "reason": error,
                            "line": line.strip()[:200],
                            "processed_at": _iso(now),
                        }
                    )
                continue

            digest_hex = fingerprint(event["text"])
            if _duplicate_seen(conn, digest_hex, now):
                out = _emit_base("suppress_duplicate", event, now)
                out["reason"] = "same normalized text within 24h"
                out["hash"] = digest_hex
                results.append(out)
                continue

            severity = event["severity"]
            if severity in DIGEST_SEVERITIES:
                _insert(conn, now, event, "digest", delivered=False)
                out = _emit_base("digest", event, now)
                out["reason"] = "queued for daily digest (09:00 RTZ)"
                results.append(out)
                continue

            # high / urgent delivery path
            if quiet and severity != "urgent":
                _insert(conn, now, event, "deferred", delivered=False)
                out = _emit_base("deferred", event, now)
                out["reason"] = "quiet hours (23:00-08:00 RTZ); flush at next window"
                results.append(out)
                continue

            if budget <= 0:
                _insert(conn, now, event, "rate_limited", delivered=False)
                out = _emit_base("rate_limited", event, now)
                out["reason"] = f"rate limit {RATE_LIMIT}/min reached; flush later"
                results.append(out)
                continue

            _insert(conn, now, event, "deliver", delivered=True, delivered_ts=now)
            results.append(_emit_base("deliver", event, now))
            budget -= 1

        conn.commit()
        return results
    finally:
        conn.close()


def build_digest(db_path: str | Path, now: datetime) -> list[dict]:
    """Flush queued medium/low alerts as one digest_report line (or nothing)."""
    now = now.astimezone(timezone.utc)
    conn = connect(db_path)
    try:
        _prune(conn, now)
        rows = conn.execute(
            "SELECT id, severity, text, source, ts_event, ts FROM events"
            " WHERE delivered = 0 AND action = 'digest' ORDER BY id"
        ).fetchall()
        if not rows:
            return []
        items = []
        for _row_id, severity, text, source, ts_event, ts in rows:
            item = {"severity": severity, "text": text, "queued_at": ts}
            if source:
                item["source"] = source
            if ts_event:
                item["ts_event"] = ts_event
            items.append(item)
        conn.execute(
            "UPDATE events SET delivered = 1, delivered_ts = ?"
            " WHERE delivered = 0 AND action = 'digest'",
            (_iso(now),),
        )
        conn.commit()
        return [
            {
                "action": "digest_report",
                "generated_at": _iso(now),
                "count": len(items),
                "items": items,
            }
        ]
    finally:
        conn.close()


# --- CLI --------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="alert_triage.py",
        description="Alert triage v1: dedup 24h, rate limit 30/min,"
        " quiet hours 23:00-08:00 RTZ.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("process", "digest"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--db", default=str(DEFAULT_DB), help="state DB path")
        cmd.add_argument(
            "--now", default=None, help="processing time override (ISO-8601)"
        )
    args = parser.parse_args(argv)
    now = parse_now(args.now)

    if args.command == "process":
        results = process_stream(args.db, sys.stdin, now)
    else:
        results = build_digest(args.db, now)

    for record in results:
        print(json.dumps(record, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
