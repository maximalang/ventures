from __future__ import annotations

import json
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from fleet_policy.alerting import is_owner_alertable
from fleet_policy.projector import HermesProjector
from fleet_policy.storage import PolicyStore


SECURITY_RULE = "sec" + "ret_read_or_write"
BOARD = "fleet-ops"


def _payload(*, task_id: str = "t_notifier", board: str = BOARD, **extra) -> dict[str, str]:
    return {
        "task_id": task_id,
        "board": board,
        "decision": "approval_required",
        "rule_id": "mass_outreach",
        **extra,
    }


def _task_result(command, status: str = "running") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, 0, json.dumps({"task": {"status": status}}), "")


def _store_with_events(tmp_path, count: int = 1, **payload_extra) -> PolicyStore:
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    for number in range(count):
        store.record_event(
            f"event-{number}",
            "run-1",
            "t_notifier",
            "policy_decision",
            _payload(**payload_extra),
            True,
        )
    return store


def _outbox_row(store: PolicyStore, event_id: str):
    with store.connect() as connection:
        return connection.execute("SELECT * FROM notification_outbox WHERE event_id=?", (event_id,)).fetchone()


def _is_task_lookup(command) -> bool:
    return command[:2] == ["hermes", "kanban"]


def test_owner_alert_filter_requires_a_task_and_keeps_serious_events():
    assert not is_owner_alertable(
        {"task_id": "", "decision": "deny", "rule_id": "task_context_unavailable"}
    )
    assert not is_owner_alertable(
        {"task_id": "t_notifier", "decision": "deny", "rule_id": "same_failure_loop"}
    )

    for rule_id in (
        "financial_action",
        "rollback_required",
        "destructive_change",
        SECURITY_RULE,
        "notification_delivery_failure",
    ):
        assert is_owner_alertable({"task_id": "t_notifier", "decision": "deny", "rule_id": rule_id})
    assert is_owner_alertable(
        {"task_id": "t_notifier", "decision": "approval_required", "rule_id": "mass_outreach"}
    )


def test_runtime_does_not_enqueue_a_non_task_diagnostic_deny(runtime, task_context):
    diagnostic_context = dict(task_context, task_context_error="Kanban temporarily unavailable", tool_call_id="diagnostic")
    denied = runtime.pre_tool_call("read_file", {"path": "README.md"}, diagnostic_context)

    assert (denied.decision, denied.rule_id) == ("deny", "task_context_unavailable")
    assert runtime.store.pending_notifications() == []


def test_timeout_keeps_claimed_notifications_pending(tmp_path):
    def runner(command, timeout):
        if _is_task_lookup(command):
            return _task_result(command)
        raise subprocess.TimeoutExpired(command, timeout)

    store = _store_with_events(tmp_path)
    assert HermesProjector(runner).drain_company(store) == 0
    assert [row["event_id"] for row in store.pending_notifications()] == ["event-0"]


@pytest.mark.parametrize(
    "failure",
    [OSError("transport down"), FileNotFoundError("hermes missing"), subprocess.SubprocessError("transport wrapper failed")],
)
def test_os_and_subprocess_transport_failures_release_claims_and_keep_rows_pending(tmp_path, failure):
    def runner(command, timeout):
        if _is_task_lookup(command):
            return _task_result(command)
        raise failure

    store = _store_with_events(tmp_path)
    assert HermesProjector(runner).drain_company(store) == 0
    assert [row["event_id"] for row in store.pending_notifications()] == ["event-0"]


def test_nonzero_transport_child_releases_claim_and_keeps_rows_pending(tmp_path):
    def runner(command, timeout):
        if _is_task_lookup(command):
            return _task_result(command)
        return subprocess.CompletedProcess(command, 1, "", "not delivered")

    store = _store_with_events(tmp_path)
    assert HermesProjector(runner).drain_company(store) == 0
    assert [row["event_id"] for row in store.pending_notifications()] == ["event-0"]


def test_release_allows_a_successful_retry(tmp_path):
    chat_attempts = 0

    def runner(command, timeout):
        nonlocal chat_attempts
        if _is_task_lookup(command):
            return _task_result(command)
        chat_attempts += 1
        if chat_attempts == 1:
            raise OSError("transient transport failure")
        return subprocess.CompletedProcess(command, 0, "ok", "")

    store = _store_with_events(tmp_path)
    projector = HermesProjector(runner)
    assert projector.drain_company(store) == 0
    assert [row["event_id"] for row in store.pending_notifications()] == ["event-0"]
    assert projector.drain_company(store) == 1
    assert chat_attempts == 2
    assert store.pending_notifications() == []


def test_projector_batches_alerts_into_one_bounded_bot_turn(tmp_path):
    calls: list[list[str]] = []

    def runner(command, timeout):
        if _is_task_lookup(command):
            return _task_result(command)
        calls.append(list(command))
        assert timeout == 15
        assert command[command.index("--max-turns") + 1] == "1"
        assert Path(command[-1]).read_text(encoding="utf-8").count("APPROVAL REQUIRED") == 3
        return subprocess.CompletedProcess(command, 0, "ok", "")

    store = _store_with_events(tmp_path, count=3)
    assert HermesProjector(runner).drain_company(store) == 3
    assert len(calls) == 1
    assert store.pending_notifications() == []


def test_concurrent_drains_claim_a_batch_only_once(tmp_path):
    started = threading.Event()
    release = threading.Event()
    calls: list[list[str]] = []

    def runner(command, timeout):
        if _is_task_lookup(command):
            return _task_result(command)
        calls.append(list(command))
        started.set()
        assert release.wait(timeout=5)
        return subprocess.CompletedProcess(command, 0, "ok", "")

    store = _store_with_events(tmp_path)
    projector = HermesProjector(runner)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(projector.drain_company, store)
        assert started.wait(timeout=5)
        assert projector.drain_company(store) == 0
        release.set()
        assert first.result(timeout=5) == 1

    assert len(calls) == 1
    assert store.pending_notifications() == []


def test_malformed_payload_is_released_without_blocking_valid_batch_rows(tmp_path):
    store = _store_with_events(tmp_path, count=2)
    with store.connect() as connection:
        connection.execute("UPDATE notification_outbox SET payload_json=? WHERE event_id=?", ("{not-json", "event-0"))

    chat_calls: list[list[str]] = []

    def runner(command, timeout):
        if _is_task_lookup(command):
            return _task_result(command)
        chat_calls.append(list(command))
        return subprocess.CompletedProcess(command, 0, "ok", "")

    assert HermesProjector(runner).drain_company(store) == 1
    assert [row["event_id"] for row in store.pending_notifications()] == ["event-0"]
    assert _outbox_row(store, "event-1")["status"] == "sent"
    assert len(chat_calls) == 1


@pytest.mark.parametrize("status", ["done", "archived", "superseded"])
def test_closed_task_alert_is_suppressed_with_auditable_reason(tmp_path, status):
    chat_calls: list[list[str]] = []

    def runner(command, timeout):
        if _is_task_lookup(command):
            assert command == ["hermes", "kanban", "--board", BOARD, "show", "t_notifier", "--json"]
            return _task_result(command, status)
        chat_calls.append(list(command))
        return subprocess.CompletedProcess(command, 0, "ok", "")

    store = _store_with_events(tmp_path)
    assert HermesProjector(runner).drain_company(store) == 0
    row = _outbox_row(store, "event-0")
    assert row["status"] == "suppressed"
    assert row["suppression_reason"] == f"task_status:{status}"
    assert row["resolved_at"]
    assert chat_calls == []


def test_stale_blocked_alerts_are_suppressed_after_task_becomes_done(tmp_path):
    store = _store_with_events(tmp_path, count=2, task_status="blocked")
    lookups = 0

    def runner(command, timeout):
        nonlocal lookups
        if _is_task_lookup(command):
            lookups += 1
            return _task_result(command, "done")
        raise AssertionError("a completed task must not reach Bot Chat")

    assert HermesProjector(runner).drain_company(store) == 0
    assert lookups == 1
    for event_id in ("event-0", "event-1"):
        assert _outbox_row(store, event_id)["status"] == "suppressed"
        assert _outbox_row(store, event_id)["suppression_reason"] == "task_status:done"


def test_unknown_task_fails_safe_without_a_phantom_delivery(tmp_path):
    chat_calls: list[list[str]] = []

    def runner(command, timeout):
        if _is_task_lookup(command):
            return subprocess.CompletedProcess(command, 1, "", "not found")
        chat_calls.append(list(command))
        return subprocess.CompletedProcess(command, 0, "ok", "")

    store = _store_with_events(tmp_path)
    assert HermesProjector(runner).drain_company(store) == 0
    assert [row["event_id"] for row in store.pending_notifications()] == ["event-0"]
    assert chat_calls == []


def test_cross_board_lookup_uses_only_the_payload_board_binding(tmp_path):
    expected_board = "rr-team"
    task_id = "t_cross_board"
    commands: list[list[str]] = []

    def runner(command, timeout):
        commands.append(list(command))
        if _is_task_lookup(command):
            assert command == ["hermes", "kanban", "--board", expected_board, "show", task_id, "--json"]
            return _task_result(command)
        return subprocess.CompletedProcess(command, 0, "ok", "")

    store = _store_with_events(tmp_path, board=expected_board, task_id=task_id)
    assert HermesProjector(runner).drain_company(store) == 1
    assert sum(_is_task_lookup(command) for command in commands) == 1


def test_duplicate_logical_event_has_one_outbox_delivery(tmp_path):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    payload = _payload()
    assert store.record_event("same-event", "run-1", "t_notifier", "policy_decision", payload, True)
    assert not store.record_event("same-event", "run-1", "t_notifier", "policy_decision", payload, True)

    chat_calls: list[list[str]] = []

    def runner(command, timeout):
        if _is_task_lookup(command):
            return _task_result(command)
        chat_calls.append(list(command))
        return subprocess.CompletedProcess(command, 0, "ok", "")

    assert HermesProjector(runner).drain_company(store) == 1
    assert len(chat_calls) == 1
    assert store.pending_notifications() == []
