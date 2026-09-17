from __future__ import annotations

import json
import subprocess

import pytest

from fleet_policy.projector import HermesProjector
from fleet_policy.storage import PolicyStore

BOARD = "fleet-ops"


def _payload(*, task_id: str = "t_retry", board: str = BOARD, **extra) -> dict[str, str]:
    return {
        "task_id": task_id,
        "board": board,
        "decision": "approval_required",
        "rule_id": "mass_outreach",
        **extra,
    }


def _task_result(command, status: str = "running") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, 0, json.dumps({"task": {"status": status}}), "")


def _is_task_lookup(command) -> bool:
    return command[:2] == ["hermes", "kanban"]


def _store_with_events(tmp_path, count: int = 1, **payload_extra) -> PolicyStore:
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    for number in range(count):
        store.record_event(
            f"event-{number}",
            "run-1",
            "t_retry",
            "policy_decision",
            _payload(**payload_extra),
            True,
        )
    return store


def _outbox_row(store: PolicyStore, event_id: str):
    with store.connect() as connection:
        return connection.execute("SELECT * FROM notification_outbox WHERE event_id=?", (event_id,)).fetchone()


def _clear_backoff(store: PolicyStore, event_id: str = "event-0") -> None:
    with store.connect() as connection:
        connection.execute("UPDATE notification_outbox SET next_retry_at=NULL WHERE event_id=?", (event_id,))


def test_failed_delivery_increments_attempts_and_preserves_claim_safety(tmp_path):
    """Transient failure → attempts+1, pending, claim fields cleared, single durable row."""
    attempts = {"n": 0}

    def runner(command, timeout):
        if _is_task_lookup(command):
            return _task_result(command)
        attempts["n"] += 1
        raise OSError("transient transport failure")

    store = _store_with_events(tmp_path)
    assert HermesProjector(runner).drain_company(store) == 0
    row = _outbox_row(store, "event-0")
    assert row["status"] == "pending"
    assert row["attempt_count"] == 1
    assert row["last_error"] == "transient transport failure"
    assert row["claim_token"] is None
    assert row["claimed_at"] is None
    # Bounded backoff: an immediate re-drain must not retry yet.
    assert HermesProjector(runner).drain_company(store) == 0
    assert attempts["n"] == 1
    assert _outbox_row(store, "event-0")["attempt_count"] == 1
    with store.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM notification_outbox").fetchone()[0] == 1


def test_successful_delivery_marks_sent_and_finalizes_accounting(tmp_path):
    """Success → sent with sent_at; no failed attempts recorded; claim cleared."""

    def runner(command, timeout):
        if _is_task_lookup(command):
            return _task_result(command)
        return subprocess.CompletedProcess(command, 0, "ok", "")

    store = _store_with_events(tmp_path)
    assert HermesProjector(runner).drain_company(store) == 1
    row = _outbox_row(store, "event-0")
    assert row["status"] == "sent"
    assert row["sent_at"] is not None
    assert row["attempt_count"] == 0
    assert row["claim_token"] is None
    assert store.pending_notifications() == []


def test_backoff_is_bounded_exponential_between_attempts(tmp_path):
    """A failed row becomes eligible again only after its bounded backoff window."""
    attempts = {"n": 0}

    def runner(command, timeout):
        if _is_task_lookup(command):
            return _task_result(command)
        attempts["n"] += 1
        raise OSError(f"down-{attempts['n']}")

    store = _store_with_events(tmp_path)
    projector = HermesProjector(runner)

    assert projector.drain_company(store) == 0
    row = _outbox_row(store, "event-0")
    assert row["attempt_count"] == 1
    assert row["next_retry_at"] is not None

    # Backoff window: an immediate re-drain must not attempt again.
    assert projector.drain_company(store) == 0
    assert attempts["n"] == 1
    assert _outbox_row(store, "event-0")["attempt_count"] == 1

    # Expiry of the backoff window makes the row eligible exactly once more.
    _clear_backoff(store)
    assert projector.drain_company(store) == 0
    assert attempts["n"] == 2
    assert _outbox_row(store, "event-0")["attempt_count"] == 2


def test_max_attempts_dead_letters_without_delivery(tmp_path):
    """Permanent failure: attempt N fails → row dead-letters instead of retrying forever."""
    attempts = {"n": 0}

    def runner(command, timeout):
        if _is_task_lookup(command):
            return _task_result(command)
        attempts["n"] += 1
        raise OSError(f"permanent down #{attempts['n']}")

    store = _store_with_events(tmp_path)
    projector = HermesProjector(runner)

    for expected in range(1, 4):
        _clear_backoff(store)
        assert projector.drain_company(store) == 0
        row = _outbox_row(store, "event-0")
        assert row["attempt_count"] == expected
        assert row["status"] == "pending"
    assert attempts["n"] == 3

    _clear_backoff(store)
    assert projector.drain_company(store) == 0
    assert attempts["n"] == 4

    row = _outbox_row(store, "event-0")
    assert row["status"] == "dead"
    assert row["resolved_at"] is not None
    assert "permanent down #4" in row["last_error"]

    # Dead rows are terminal: never delivered, never re-claimed.
    _clear_backoff(store)
    assert projector.drain_company(store) == 0
    assert attempts["n"] == 4
    assert _outbox_row(store, "event-0")["status"] == "dead"
    assert store.pending_notifications() == []


def test_expired_pending_row_dead_letters_without_delivery(tmp_path):
    """Expiry: an old pending row past its delivery deadline goes dead, never sent."""
    chat_calls: list[list[str]] = []

    def runner(command, timeout):
        if _is_task_lookup(command):
            return _task_result(command)
        chat_calls.append(list(command))
        return subprocess.CompletedProcess(command, 0, "ok", "")

    store = _store_with_events(tmp_path)
    with store.connect() as connection:
        connection.execute(
            "UPDATE notification_outbox SET created_at='2026-09-01T00:00:00Z' WHERE event_id='event-0'"
        )

    assert HermesProjector(runner).drain_company(store) == 0
    assert chat_calls == []
    row = _outbox_row(store, "event-0")
    assert row["status"] == "dead"
    assert row["resolved_at"] is not None
    assert row["attempt_count"] == 0
    assert "expired" in row["suppression_reason"].lower()


def test_notification_counters_split_delivery_accounting(tmp_path):
    """Queued/delivered/dead/suppressed are separate, derived from the outbox."""

    def runner(command, timeout):
        if _is_task_lookup(command):
            return _task_result(command)
        return subprocess.CompletedProcess(command, 0, "ok", "")

    store = _store_with_events(tmp_path, count=4)

    counts = store.notification_counts()
    assert counts == {"queued": 4, "delivered": 0, "dead": 0, "suppressed": 0}

    assert HermesProjector(runner).drain_company(store) == 4
    counts = store.notification_counts()
    assert counts == {"queued": 0, "delivered": 4, "dead": 0, "suppressed": 0}

    with store.connect() as connection:
        connection.execute(
            "UPDATE notification_outbox SET status='dead',resolved_at='2026-09-17T00:00:00Z' WHERE event_id='event-0'"
        )
        connection.execute(
            "UPDATE notification_outbox SET status='suppressed',resolved_at='2026-09-17T00:00:00Z' WHERE event_id='event-1'"
        )
    counts = store.notification_counts()
    assert counts == {"queued": 0, "delivered": 2, "dead": 1, "suppressed": 1}


def test_malformed_payload_row_is_released_not_counted_as_an_attempt(tmp_path):
    """A malformed payload never reached a transport: release to pending, no attempt."""
    store = _store_with_events(tmp_path)
    with store.connect() as connection:
        connection.execute(
            "UPDATE notification_outbox SET payload_json='{not-json' WHERE event_id='event-0'"
        )

    chat_calls: list[list[str]] = []

    def runner(command, timeout):
        if _is_task_lookup(command):
            return _task_result(command)
        chat_calls.append(list(command))
        return subprocess.CompletedProcess(command, 0, "ok", "")

    assert HermesProjector(runner).drain_company(store) == 0
    assert chat_calls == []
    row = _outbox_row(store, "event-0")
    assert row["status"] == "pending"
    assert row["attempt_count"] == 0


def test_outbox_accounting_surfaces_in_status_counts(tmp_path, capsys, monkeypatch):
    """Observability: the CLI status block reports all four delivery counters."""
    import fleet_policy.cli as cli_module

    store = _store_with_events(tmp_path, count=2)

    class _FakeRuntime:
        def __init__(self, root):
            self.root = root
            self.store = store

    monkeypatch.setattr(cli_module, "FleetPolicyRuntime", _FakeRuntime)
    monkeypatch.setattr(cli_module.sys, "argv", ["fleet-policy", "status"])

    assert cli_module.main() == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["notifications_queued"] == 2
    assert printed["notifications_delivered"] == 0
    assert printed["notifications_dead"] == 0
    assert printed["notifications_suppressed"] == 0
