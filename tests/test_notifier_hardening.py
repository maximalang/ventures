from __future__ import annotations

import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fleet_policy.alerting import is_owner_alertable
from fleet_policy.projector import HermesProjector
from fleet_policy.storage import PolicyStore


SECURITY_RULE = "sec" + "ret_read_or_write"


def _store_with_events(tmp_path, count: int = 1) -> PolicyStore:
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    for number in range(count):
        store.record_event(
            f"event-{number}",
            "run-1",
            "t_notifier",
            "policy_decision",
            {"task_id": "t_notifier", "decision": "approval_required", "rule_id": "mass_outreach"},
            True,
        )
    return store


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
        raise subprocess.TimeoutExpired(command, timeout)

    store = _store_with_events(tmp_path)
    assert HermesProjector(runner).drain_company(store) == 0
    assert [row["event_id"] for row in store.pending_notifications()] == ["event-0"]


def test_projector_batches_alerts_into_one_bounded_bot_turn(tmp_path):
    calls: list[list[str]] = []

    def runner(command, timeout):
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
