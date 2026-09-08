"""Unit tests for scripts/hooks-tunnel/alert_triage.py (v1).

All time-sensitive behaviour is driven through the explicit ``now`` argument
of process_stream()/build_digest(), so tests are deterministic without
sleeping or monkeypatching the clock.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks-tunnel"))

import alert_triage as at  # noqa: E402


# --- fixtures ---------------------------------------------------------------
@pytest.fixture()
def db(tmp_path: Path) -> Path:
    return tmp_path / "alert_triage.db"


@pytest.fixture()
def day(db: Path) -> Path:
    """Noon RTZ (09:00 UTC) - inside the delivery window."""
    return db


def run(db: Path, events: list[dict], now: str) -> list[dict]:
    lines = [json.dumps(e, ensure_ascii=False) for e in events]
    return at.process_stream(db, lines, at.parse_now(now))


DAY_NOON = "2026-09-07T09:00:00+00:00"  # 12:00 RTZ - window
NIGHT = "2026-09-07T22:30:00+00:00"  # 01:30 RTZ next day - quiet hours
MORNING = "2026-09-08T05:30:00+00:00"  # 08:30 RTZ - window opened


def ev(severity: str, text: str, **kw) -> dict:
    return {"severity": severity, "text": text, **kw}


# --- dedup -------------------------------------------------------------------
def test_duplicate_within_24h_suppressed(db):
    first = run(db, [ev("high", "CI failed on PR 42")], DAY_NOON)
    assert first[0]["action"] == "deliver"
    again = run(db, [ev("high", "CI failed on PR 42")], DAY_NOON)
    assert again[0]["action"] == "suppress_duplicate"
    assert again[0]["hash"] == at.fingerprint("CI failed on PR 42")


def test_dedup_normalizes_case_and_whitespace(db):
    run(db, [ev("high", "Disk  Space\tLow")], DAY_NOON)
    second = run(db, [ev("high", "disk space low")], DAY_NOON)
    assert second[0]["action"] == "suppress_duplicate"


def test_dedup_distinguishes_distinct_payloads(db):
    run(db, [ev("high", "CI failed on PR 42")], DAY_NOON)
    other = run(db, [ev("high", "CI failed on PR 43")], DAY_NOON)
    assert other[0]["action"] == "deliver"  # no digit masking -> not swallowed


def test_dedup_expires_after_24h(db):
    run(db, [ev("high", "nightly backup overdue")], DAY_NOON)
    late = "2026-09-08T09:30:00+00:00"  # +24.5h
    again = run(db, [ev("high", "nightly backup overdue")], late)
    assert again[0]["action"] == "deliver"


def test_suppressed_duplicate_does_not_reopen_ttl(db):
    # The 24h window is measured from the FIRST sighting: a repeated
    # duplicate must not extend suppression forever.
    run(db, [ev("high", "stale alarm")], DAY_NOON)
    dup = run(db, [ev("high", "stale alarm")], "2026-09-08T08:00:00+00:00")
    assert dup[0]["action"] == "suppress_duplicate"
    out = run(db, [ev("high", "stale alarm")], "2026-09-08T09:30:00+00:00")
    # 24h after FIRST sighting -> TTL expired even though a dup arrived
    assert out[0]["action"] == "deliver"


# --- severity routing --------------------------------------------------------
def test_urgent_delivered_immediately_in_window(db):
    out = run(db, [ev("urgent", "production down")], DAY_NOON)
    assert out[0]["action"] == "deliver"


def test_high_delivered_in_window(db):
    out = run(db, [ev("high", "queue lag > 10m")], DAY_NOON)
    assert out[0]["action"] == "deliver"


def test_medium_and_low_go_to_digest_queue(db):
    out = run(
        db,
        [ev("medium", "disk 78%"), ev("low", "cert renews in 21d")],
        DAY_NOON,
    )
    assert [r["action"] for r in out] == ["digest", "digest"]


def test_digest_flushes_queued_items_once(db):
    run(db, [ev("medium", "disk 78%"), ev("low", "cert renews in 21d")], DAY_NOON)
    digest = at.build_digest(db, at.parse_now(DAY_NOON))
    assert len(digest) == 1
    assert digest[0]["action"] == "digest_report"
    assert digest[0]["count"] == 2
    assert [i["severity"] for i in digest[0]["items"]] == ["medium", "low"]
    # second call: queue empty -> no output (cron-friendly)
    assert at.build_digest(db, at.parse_now(DAY_NOON)) == []


# --- quiet hours -------------------------------------------------------------
@pytest.mark.parametrize(
    "now,expected",
    [
        ("2026-09-07T19:59:00+00:00", False),  # 22:59 RTZ
        ("2026-09-07T20:00:00+00:00", True),  # 23:00 RTZ
        ("2026-09-07T23:30:00+00:00", True),  # 02:30 RTZ
        ("2026-09-08T04:59:00+00:00", True),  # 07:59 RTZ
        ("2026-09-08T05:00:00+00:00", False),  # 08:00 RTZ
    ],
)
def test_quiet_hours_boundaries(now, expected):
    assert at.is_quiet_hours(at.parse_now(now)) is expected


def test_urgent_delivered_during_quiet_hours(db):
    out = run(db, [ev("urgent", "DB primary lost quorum")], NIGHT)
    assert out[0]["action"] == "deliver"


def test_high_deferred_during_quiet_hours(db):
    out = run(db, [ev("high", "queue lag > 10m")], NIGHT)
    assert out[0]["action"] == "deferred"


def test_deferred_high_flushes_next_window(db):
    run(db, [ev("high", "queue lag > 10m")], NIGHT)
    out = run(db, [], MORNING)  # empty batch still flushes pending
    assert len(out) == 1
    assert out[0]["action"] == "deliver"
    assert out[0]["source"] == "pending"
    assert out[0]["text"] == "queue lag > 10m"


def test_medium_low_during_quiet_hours_still_queue_for_digest(db):
    out = run(db, [ev("medium", "disk 78%")], NIGHT)
    assert out[0]["action"] == "digest"


# --- rate limit ----------------------------------------------------------------
def test_rate_limit_30_per_minute(db):
    events = [ev("high", f"alert number {i}") for i in range(35)]
    out = run(db, events, DAY_NOON)
    actions = [r["action"] for r in out]
    assert actions.count("deliver") == 30
    assert actions.count("rate_limited") == 5


def test_rate_limited_items_flush_in_next_window(db):
    events = [ev("high", f"alert number {i}") for i in range(35)]
    run(db, events, DAY_NOON)
    later = "2026-09-07T09:02:00+00:00"  # window rolled
    out = run(db, [], later)
    assert len(out) == 5
    assert all(r["action"] == "deliver" and r["source"] == "pending" for r in out)


def test_rate_budget_shared_with_pending_flush(db):
    # 30 deliveries in window 1; window 2: 5 pending + 30 new -> only 25 new fit
    run(db, [ev("high", f"a{i}") for i in range(35)], DAY_NOON)
    second = "2026-09-07T09:02:00+00:00"
    out = run(db, [ev("high", f"b{i}") for i in range(30)], second)
    pending = [r for r in out if r.get("source") == "pending"]
    delivered_new = [r for r in out if r["action"] == "deliver" and r.get("source") != "pending"]
    limited = [r for r in out if r["action"] == "rate_limited"]
    assert len(pending) == 5
    assert len(delivered_new) == 25
    assert len(limited) == 5


def test_urgent_during_quiet_hours_counts_against_rate_limit(db):
    events = [ev("urgent", f"incident {i}") for i in range(32)]
    out = run(db, events, NIGHT)
    actions = [r["action"] for r in out]
    assert actions.count("deliver") == 30
    assert actions.count("rate_limited") == 2


def test_pending_urgent_flushes_during_quiet_hours_only(db):
    # high deferred at night stays deferred while quiet; urgent pending flushes
    run(db, [ev("high", "night queue lag")], NIGHT)
    out = run(db, [], "2026-09-07T23:30:00+00:00")  # still quiet
    assert out == []  # high pending does NOT flush during quiet hours


# --- validation ----------------------------------------------------------------
def test_invalid_lines_reported_not_crashing(db):
    lines = [
        "not json at all",
        json.dumps({"severity": "critical", "text": "unknown severity"}),
        json.dumps({"severity": "high", "text": "   "}),
        "",  # blank line skipped silently
        json.dumps({"severity": "high", "text": "good one"}),
    ]
    out = at.process_stream(db, lines, at.parse_now(DAY_NOON))
    actions = [r["action"] for r in out]
    assert actions == ["invalid", "invalid", "invalid", "deliver"]
    assert "severity" in out[1]["reason"]


def test_source_and_ts_event_echoed(db):
    out = run(
        db,
        [ev("urgent", "host down", source="prom", ts="2026-09-07T08:59:00Z")],
        DAY_NOON,
    )
    assert out[0]["source"] == "prom"
    assert out[0]["ts_event"] == "2026-09-07T08:59:00Z"


def test_normalization_and_fingerprint_stability():
    assert at.normalize_text("  A  B\tc\n") == "a b c"
    assert at.fingerprint("Disk LOW") == at.fingerprint("disk low")
    assert len(at.fingerprint("x")) == 64


def test_parse_now_accepts_z_suffix_and_naive_utc():
    assert at.parse_now("2026-09-07T12:00:00Z").hour == 12
    assert at.parse_now("2026-09-07T12:00:00").hour == 12  # naive -> UTC
    assert at.parse_now("2026-09-07T15:00:00+03:00").hour == 12
