"""v1.2.14: TG noise fixes — auto-expire approvals, board-bound budget stops,
HTML alert format.

Incident 2026-09-07: 43 of 47 pending approvals belonged to done/archived
cards (phantom counter), 39 of 83 outbox events were budget denies WITHOUT a
board binding (claim→release→pending forever), and deny sections were raw
json.dumps(indent=2) dumps.
"""
from __future__ import annotations

import json
import subprocess

import pytest

from fleet_policy.projector import HermesProjector
from fleet_policy.storage import PolicyStore


BOARD = "fleet-ops"


def _task_result(command, status: str = "running") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, 0, json.dumps({"task": {"status": status}}), "")


def _is_task_lookup(command) -> bool:
    return command[:2] == ["hermes", "kanban"]


# ------------------------------------------------------- slice 1: auto-expire

def test_closed_card_approval_expires_never_approved_or_rejected(tmp_path, monkeypatch):
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    store.ensure_approval("key0123456789", "t_dead", "terminal", "deploy", "h", BOARD)

    def runner(command, timeout):
        assert command == ["hermes", "kanban", "--board", BOARD, "show", "t_dead", "--json"]
        return _task_result(command, "done")

    assert HermesProjector(runner).expire_closed_approvals(store) == 1
    row = store.approval("key0123456789")
    assert row["status"] == "expired"
    assert row["expired_at"] and row["decided_by"] == "expired:task_status:done"
    # Not an owner decision: never approved/rejected, never consumable.
    assert row["status"] not in ("approved", "rejected")
    assert store.consume_exact_approval("t_dead", "terminal", "deploy", "h") is False
    # The pending counter now shows only live bindings.
    with store.connect() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM approvals WHERE status='pending'"
        ).fetchone()[0] == 0


@pytest.mark.parametrize("status", ["done", "archived", "superseded"])
def test_all_closed_statuses_expire(tmp_path, monkeypatch, status):
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    store.ensure_approval("k", "t_dead", "terminal", "x", "h", BOARD)
    runner = lambda command, timeout: _task_result(command, status)  # noqa: E731
    assert HermesProjector(runner).expire_closed_approvals(store) == 1
    assert store.approval("k")["status"] == "expired"


def test_live_or_unresolvable_card_stays_pending(tmp_path, monkeypatch):
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    store.ensure_approval("k_live", "t_live", "terminal", "x", "h", BOARD)
    store.ensure_approval("k_unknown", "t_gone", "terminal", "y", "h", BOARD)

    def runner(command, timeout):
        if command[5] == "t_live":
            return _task_result(command, "running")
        return subprocess.CompletedProcess(command, 1, "", "not found")

    assert HermesProjector(runner).expire_closed_approvals(store) == 0
    assert store.approval("k_live")["status"] == "pending"
    assert store.approval("k_unknown")["status"] == "pending"


def test_legacy_boardless_binding_is_never_expired(tmp_path, monkeypatch):
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    store.ensure_approval("k_legacy", "t_x", "terminal", "x", "h")  # board defaults ''

    def runner(command, timeout):
        raise AssertionError("a board-less binding must not trigger a lookup")

    assert HermesProjector(runner).expire_closed_approvals(store) == 0
    assert store.approval("k_legacy")["status"] == "pending"


def test_worker_env_cannot_expire(tmp_path, monkeypatch):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    store.ensure_approval("k", "t_dead", "terminal", "x", "h", BOARD)
    monkeypatch.setenv("HERMES_KANBAN_TASK", "t_some_worker")
    runner = lambda command, timeout: _task_result(command, "done")  # noqa: E731
    assert HermesProjector(runner).expire_closed_approvals(store) == 0
    assert store.approval("k")["status"] == "pending"


def test_decided_rows_are_immutable_against_expiry(tmp_path, monkeypatch):
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    store.ensure_approval("kdecided01234", "t_dead", "terminal", "x", "h", BOARD)
    assert store.decide_approval("kdecided01234", True, "owner", confirm_code="kdecided01234"[-8:])
    runner = lambda command, timeout: _task_result(command, "archived")  # noqa: E731
    assert HermesProjector(runner).expire_closed_approvals(store) == 0
    assert store.approval("kdecided01234")["status"] == "approved"


# ------------------------------------------- slice 2: budget denies carry board

def test_post_api_budget_stop_payload_is_board_bound(runtime, task_context):
    limit = runtime.config["budgets"]["code"]["tokens"]
    runtime.store.add_budget("t_test", "tokens", limit + 1, "seed", "r1")
    task_context["api_request_id"] = "api-noise-1"
    payload = runtime.post_api_request(task_context, {"completion_tokens": 1}, 1)
    assert payload is not None and payload["rule_id"] == "budget_exhausted"
    assert payload["board"] == "rr-team"
    assert payload["task_status"] == "running"
    assert payload["run_key"] == "r1"
    # The outbox row is resolvable: drain delivers it instead of cycling.
    assert HermesProjector.notification_binding(payload) == ("rr-team", "t_test")


def test_budget_stop_event_drains_without_eternal_pending(tmp_path, runtime, task_context):
    limit = runtime.config["budgets"]["code"]["tokens"]
    runtime.store.add_budget("t_test", "tokens", limit + 1, "seed", "r1")
    task_context["api_request_id"] = "api-noise-2"
    payload = runtime.post_api_request(task_context, {"completion_tokens": 1}, 1)
    assert payload is not None
    assert len(runtime.store.pending_notifications()) == 1

    chat_calls: list[list[str]] = []

    def runner(command, timeout):
        if _is_task_lookup(command):
            return _task_result(command, "running")
        chat_calls.append(list(command))
        return subprocess.CompletedProcess(command, 0, "ok", "")

    assert HermesProjector(runner).drain_company(runtime.store) == 1
    assert len(chat_calls) == 1
    assert runtime.store.pending_notifications() == []
    assert "--max-turns" in chat_calls[0]


# ------------------------------------------------------- slice 3: HTML format

def test_approval_text_is_escaped_html_card():
    text = HermesProjector.approval_text({
        "decision": "approval_required",
        "approval_card": {
            "project_task": "board <x> & t1",
            "action": "terminal: rm <danger> & more",
            "why": "policy <gate>",
            "evidence": "args_hash:abc&def",
            "risk": "risk <high>",
            "rollback": "stop <now>",
            "rule_key": "key<1>",
        },
    })
    assert "🔴 <b>APPROVAL REQUIRED</b>" in text
    assert "&lt;x&gt;" in text and "&amp;" in text
    assert "<danger>" not in text and "<gate>" not in text and "<high>" not in text
    assert "<code>" in text and "Выбор:" in text


def test_event_text_is_escaped_html_card_without_raw_json():
    text = HermesProjector.event_text({
        "decision": "deny",
        "rule_id": "budget_exhausted",
        "reason": "hard budget exhausted: tokens <limit> & more",
        "task_id": "t_1",
        "board": "fleet-ops",
        "action": "llm_request",
        "budget_snapshot": {
            "used": {"tokens": 100, "tool_calls": 5},
            "limits": {"tokens": 100, "tool_calls": 10},
        },
    })
    assert "🚫 <b>BUDGET_EXHAUSTED</b>" in text
    assert "&lt;limit&gt;" in text and "&amp;" in text
    assert "tokens 100/100" in text
    assert "payload_json" not in text and '"reason":' not in text


def test_drain_sections_use_html_not_json_dumps(tmp_path):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    store.record_event("ev-approve", "c", "t_n", "policy_decision", {
        "decision": "approval_required", "task_id": "t_n", "board": BOARD,
        "rule_id": "mass_outreach",
        "approval_card": {"project_task": f"{BOARD} + t_n", "rule_key": "rk"},
    }, True)
    store.record_event("ev-deny", "c", "t_n", "budget_or_loop_stop", {
        "decision": "deny", "rule_id": "budget_exhausted", "reason": "exhausted: tokens",
        "task_id": "t_n", "board": BOARD, "action": "llm_request",
    }, True)
    delivered: list[str] = []

    def runner(command, timeout):
        if _is_task_lookup(command):
            return _task_result(command, "running")
        from pathlib import Path
        delivered.append(Path(command[command.index("--query-file") + 1]).read_text(encoding="utf-8"))
        return subprocess.CompletedProcess(command, 0, "ok", "")

    assert HermesProjector(runner).drain_company(store) == 2
    body = delivered[0]
    assert "APPROVAL REQUIRED" in body and "<b>BUDGET_EXHAUSTED</b>" in body
    assert '"payload_json"' not in body and '"correlation_id"' not in body
    assert "\n  " not in body  # no indent=2 json dump remnants
