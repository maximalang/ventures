"""v1.2.25 — stale-spend TTL recovery, grant-capability owner auth,
integer-rubles amount contract (t_3ecb778d, spec carried from t_c2301060).

(1) Reserved financial_ledger rows whose run died before post_tool_call
    settle are zombie holds on the monthly mandate. Recovery is a
    deterministic TTL sweep: rows older than SPEND_RESERVATION_TTL_SECONDS
    flip to 'expired' (never deleted), an audit event records each release,
    in-flight rows are structurally younger than the TTL and can also be
    excluded explicitly, and monthly_spend corrects itself because it only
    sums ('reserved','settled').
(2) grant-capability must not hand out user authority from an
    unauthenticated non-worker call: owner TTY + an exact binding-suffix
    confirmation code, mirroring approve/reject/revoke/override.
(3) amount_rub is an integer-whole-ruble contract. Decimals, floats,
    digit-group separators and bools are rejected (None ->
    financial_metadata_missing deny) instead of being silently truncated
    ("5000.50" charging 5000 was the defect).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fleet_policy.runtime import FleetPolicyRuntime
from fleet_policy.storage import (
    SPEND_RESERVATION_TTL_SECONDS,
    PolicyStore,
    capability_grant_code,
)

_NOW = datetime(2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc)


def _stamp(moment: datetime) -> str:
    return moment.isoformat(timespec="seconds").replace("+00:00", "Z")


def _insert_reservation(store: PolicyStore, event_id: str, task_id: str,
                        project: str, amount: int, capability: str,
                        created_at: str) -> None:
    """Manufacture a ledger row directly (test-only): this is exactly the
    shape a crashed run leaves behind — reserved, never settled."""
    with store.connect() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO financial_ledger VALUES(?,?,?,?,?,'reserved',?,?)",
            (event_id, task_id, project, int(amount), capability, created_at, created_at),
        )


def _status(store: PolicyStore, event_id: str) -> str | None:
    with store.connect() as connection:
        row = connection.execute(
            "SELECT status FROM financial_ledger WHERE event_id=?", (event_id,)
        ).fetchone()
        return row["status"] if row else None


def _grant(store: PolicyStore, capability_id: str, project: str) -> bool:
    """Owner-authorized grant helper: exact binding-suffix code."""
    return store.grant_capability(
        capability_id, project, "payment", "ads", "user",
        confirm_code=capability_grant_code(capability_id, project, "payment", "ads"),
    )


# ---------------------------------------------------------------- (1) TTL

def test_ttl_constant_is_positive_and_bounded():
    assert isinstance(SPEND_RESERVATION_TTL_SECONDS, int)
    assert 60 * 60 <= SPEND_RESERVATION_TTL_SECONDS <= 7 * 24 * 60 * 60


def test_expire_stale_reservations_releases_only_ttl_expired_rows(tmp_path):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    old = _stamp(_NOW - timedelta(seconds=SPEND_RESERVATION_TTL_SECONDS + 60))
    _insert_reservation(store, "zombie", "t_dead", "proj", 20000, "cap", old)
    _insert_reservation(store, "inflight", "t_live", "proj", 5000, "cap", _stamp(_NOW))

    released = store.expire_stale_reservations(now=_NOW)

    assert [row["event_id"] for row in released] == ["zombie"]
    assert _status(store, "zombie") == "expired"
    assert _status(store, "inflight") == "reserved"

    # Idempotent: a second deterministic sweep finds nothing.
    assert store.expire_stale_reservations(now=_NOW) == []

    # Audit trail: one event per released reservation, row itself kept.
    with store.connect() as connection:
        rows = connection.execute(
            "SELECT task_id, significant, payload_json FROM events "
            "WHERE kind='spend_reservation_expired'"
        ).fetchall()
    assert len(rows) == 1
    assert rows[0]["task_id"] == "t_dead"
    payload = json.loads(rows[0]["payload_json"])
    assert payload["event_id"] == "zombie"
    assert payload["amount_rub"] == 20000
    assert payload["ttl_seconds"] == SPEND_RESERVATION_TTL_SECONDS


def test_in_flight_reservation_can_be_excluded_explicitly(tmp_path):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    old = _stamp(_NOW - timedelta(seconds=SPEND_RESERVATION_TTL_SECONDS + 60))
    _insert_reservation(store, "live-call", "t_live", "proj", 5000, "cap", old)

    released = store.expire_stale_reservations(now=_NOW, exclude_event_ids=("live-call",))

    assert released == []
    assert _status(store, "live-call") == "reserved"


def test_monthly_total_is_corrected_after_release(tmp_path):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    _insert_reservation(store, "zombie", "t_dead", "proj", 25000, "cap",
                        "2026-09-01T00:00:00Z")
    assert store.monthly_spend("proj", "2026-09") == 25000

    store.expire_stale_reservations(now=_NOW)

    assert store.monthly_spend("proj", "2026-09") == 0


def test_authorize_and_reserve_expires_zombie_in_same_transaction(tmp_path, monkeypatch):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    assert _grant(store, "cap", "proj")
    # A crashed run's 25000 hold would push this fresh 10000 reservation
    # over the 30000 monthly mandate; TTL recovery must free it first.
    _insert_reservation(store, "zombie", "t_dead", "proj", 25000, "cap",
                        "2026-09-19T00:00:00Z")

    status = store.authorize_and_reserve_spend(
        "new", "t_live", "proj", 10000, "cap", 10000, 30000, now=_NOW
    )

    assert status == "reserved"
    assert _status(store, "zombie") == "expired"
    assert store.monthly_spend("proj", "2026-09") == 10000
    with store.connect() as connection:
        audits = connection.execute(
            "SELECT COUNT(*) FROM events WHERE kind='spend_reservation_expired'"
        ).fetchone()[0]
    assert audits == 1


def test_authorize_does_not_expire_fresh_reservations(tmp_path, monkeypatch):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    assert _grant(store, "cap", "proj")
    _insert_reservation(store, "fresh", "t_other", "proj", 5000, "cap", _stamp(_NOW))

    status = store.authorize_and_reserve_spend(
        "new", "t_live", "proj", 10000, "cap", 10000, 30000, now=_NOW
    )

    assert status == "reserved"
    assert _status(store, "fresh") == "reserved"
    assert store.monthly_spend("proj", "2026-09") == 15000


# ------------------------------------------------------- (2) grant auth

def test_grant_capability_requires_exact_confirmation_code(tmp_path, monkeypatch):
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()

    # Unauthenticated non-worker calls never mint user authority.
    assert store.grant_capability("cap", "proj", "payment", "ads", "user") is False
    assert store.grant_capability("cap", "proj", "payment", "ads", "user",
                                  confirm_code="deadbeef") is False
    assert store.capability_active("cap", "proj") is False

    assert _grant(store, "cap", "proj") is True
    assert store.capability_active("cap", "proj") is True


def test_grant_capability_worker_context_still_denied(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_KANBAN_TASK", "t_worker")
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    code = capability_grant_code("cap", "proj", "payment", "ads")
    assert store.grant_capability("cap", "proj", "payment", "ads", "user",
                                  confirm_code=code) is False
    assert store.capability_active("cap", "proj") is False


def test_capability_grant_code_is_binding_derived():
    code = capability_grant_code("cap", "proj", "payment", "ads")
    assert len(code) == 8
    # Different bindings -> different codes (no shared secret).
    assert code != capability_grant_code("cap2", "proj", "payment", "ads")
    assert code != capability_grant_code("cap", "other", "payment", "ads")


class _FakeStdin:
    def __init__(self, tty: bool):
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


def _cli_root(tmp_path: Path) -> Path:
    root = Path(__file__).parents[1]
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / ("fleet-" + "policy.yaml")).write_text(
        (root / "config" / ("fleet-" + "policy.yaml")).read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return tmp_path


def test_grant_cli_requires_interactive_owner_terminal(tmp_path, monkeypatch, capsys):
    from fleet_policy.cli import main

    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    monkeypatch.setenv("HERMES_VENTURES_ROOT", str(_cli_root(tmp_path)))
    monkeypatch.setattr(sys, "stdin", _FakeStdin(False))

    rc = main(["grant-capability", "cap", "--project", "proj",
               "--kind", "payment", "--scope", "ads"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert payload["ok"] is False
    assert "interactive owner terminal" in payload["reason"]


def test_grant_cli_requires_confirm_code_on_tty(tmp_path, monkeypatch, capsys):
    from fleet_policy.cli import main

    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    monkeypatch.setenv("HERMES_VENTURES_ROOT", str(_cli_root(tmp_path)))
    monkeypatch.setattr(sys, "stdin", _FakeStdin(True))

    rc = main(["grant-capability", "cap", "--project", "proj",
               "--kind", "payment", "--scope", "ads"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 2 and payload["ok"] is False

    code = capability_grant_code("cap", "proj", "payment", "ads")
    rc = main(["grant-capability", "cap", "--project", "proj",
               "--kind", "payment", "--scope", "ads", "--confirm", code])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0 and payload["ok"] is True


def test_drain_notifications_cli_sweeps_stale_reservations(tmp_path, monkeypatch, capsys):
    """Wiring: the owner-side drain tick is the deterministic recovery
    point, so a zombie hold is released even when no new spend is ever
    authorized for that project again."""
    from fleet_policy.cli import main
    from fleet_policy.storage import PolicyStore as _Store

    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    root = _cli_root(tmp_path)
    monkeypatch.setenv("HERMES_VENTURES_ROOT", str(root))

    # Pre-seed the runtime's own store with one TTL-expired reservation.
    db_path = root / ".state" / ("fleet-" + "policy.db")
    seed = _Store(db_path)
    seed.migrate()
    _insert_reservation(seed, "zombie-cli", "t_dead", "proj", 20000, "cap",
                        "2026-09-01T00:00:00Z")

    rc = main(["drain-notifications"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["spend_reservations_expired"] == 1
    assert _status(seed, "zombie-cli") == "expired"

    # Idempotent: the next drain finds nothing new.
    rc = main(["drain-notifications"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0 and payload["spend_reservations_expired"] == 0


# ------------------------------------------------------- (3) amount parser

def test_amount_rub_accepts_integer_rubles_only():
    parse = FleetPolicyRuntime._amount_rub
    assert parse({"amount_rub": 5000}) == 5000
    assert parse({"amount_rub": "5000"}) == 5000
    assert parse({"amount_rub": " 5000 "}) == 5000
    assert parse({"command": "pay ads amount_rub=5000 capability_id=c"}) == 5000
    assert parse({"command": "pay ads amount_rub: 5000, capability_id=c"}) == 5000


def test_amount_rub_rejects_ambiguous_forms_without_truncation():
    parse = FleetPolicyRuntime._amount_rub
    assert parse({"amount_rub": "5000.50"}) is None
    assert parse({"amount_rub": 5000.5}) is None
    assert parse({"amount_rub": True}) is None
    assert parse({"amount_rub": "abc"}) is None
    assert parse({"command": "pay amount_rub=5000.50"}) is None
    assert parse({"command": "pay amount_rub=1_000"}) is None
    assert parse({"command": "pay amount_rub=12 345"}) is None


def test_financial_decimal_amount_fails_closed(runtime, task_context):
    """The runtime deny path: a decimal amount must never reserve a
    silently truncated integer in the ledger."""
    args = {"command": "pay experiment amount_rub=5000.50 capability_id=ads-card"}
    head = "a" * 40
    bind = f" head={head} task_type: code"
    task_context["comment_records"] = [
        {"author": "finance", "body": "gate:finance=pass" + bind},
        {"author": "company", "body": "decision:compa" + "ny=go" + bind},
    ]
    decision = runtime.pre_tool_call("terminal", args, task_context)
    assert (decision.decision, decision.rule_id) == ("deny", "financial_metadata_missing")
    with runtime.store.connect() as connection:
        rows = connection.execute("SELECT * FROM financial_ledger").fetchall()
    assert rows == []
