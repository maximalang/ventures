"""v1.2.16 board-resolve contract tests for gate attestation (t_1b74f401).

Incident (fleet-ops, 2026-09-07 20:33-20:38Z, policy events for t_b817cf9b):
a qa worker posting ``gate:review=pass`` was denied ``gate_forgery`` when the
target card lived on a board other than the worker-context board, because the
v1.2.10 item E guard probed only ``task_assignee(context.board, target)`` and
failed closed on the miss. Evidence: task_events 11893/11894 (auto-block) and
11804; the ci-gate marker (no target lookup) landed one minute later (comment
2696) while the review marker never did.

Contracts pinned here:
- a foreign-board target card IS resolvable for authorization (worker board,
  then the explicit call ``board`` argument, then sibling board registries);
- a legit cross-board attestation is allowed (the incident shape);
- self-approval on the target card stays denied (own-card and foreign-card);
- a card that exists in no board registry stays denied (fail closed);
- an explicit HERMES_KANBAN_DB pin keeps single-store fail-closed semantics.
"""
from __future__ import annotations

import sqlite3

import pytest

from fleet_policy.kanban_context import task_assignee, task_assignee_resolved

BOARD_DB = "kan" + "ban.db"


def _make_board_db(path, cards):
    """cards: {task_id: (assignee, status)} — minimal board registry."""
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "CREATE TABLE tasks(id TEXT PRIMARY KEY, assignee TEXT, status TEXT)"
        )
        for task_id, (assignee, status) in cards.items():
            connection.execute(
                "INSERT INTO tasks(id, assignee, status) VALUES(?,?,?)",
                (task_id, assignee, status),
            )
        connection.commit()
    finally:
        connection.close()
    return path


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Two board registries: default (worker's own qa card) and fleet-ops."""
    home = tmp_path / "hermes"
    _make_board_db(
        home / BOARD_DB,
        {"t_worker_card": ("qa", "running")},
    )
    _make_board_db(
        home / "kanban" / "boards" / "fleet-ops" / BOARD_DB,
        {"t_merge_card": ("company", "todo")},
    )
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.delenv("HERMES_KANBAN_DB", raising=False)
    return home


def _qa_worker_context(task_context, board):
    return dict(
        task_context,
        task_id="t_worker_card",
        board=board,
        profile="qa",
        assignee="qa",
        task_status="running",
        comment_records=[],
        tool_call_id="probe-1",
    )


# ------------------------------------------------------- incident shapes


def test_crossboard_review_attestation_allowed(sandbox, runtime, task_context):
    # Incident: qa worker (context board default) attests the review gate on a
    # fleet-ops merge card assigned to company. Must NOT be gate_forgery.
    context = _qa_worker_context(task_context, board="default")
    decision = runtime.pre_tool_call(
        "kanban_comment",
        {"task_id": "t_merge_card", "text": "gate:review=pass"},
        context,
    )
    assert decision.decision == "allow", decision


def test_explicit_board_argument_resolves_target(sandbox, runtime, task_context):
    # The call itself carries the target board — the guard must read it.
    context = _qa_worker_context(task_context, board="default")
    decision = runtime.pre_tool_call(
        "kanban_comment",
        {"task_id": "t_merge_card", "board": "fleet-ops", "text": "gate:review=pass"},
        context,
    )
    assert decision.decision == "allow", decision


def test_same_context_board_attestation_still_allowed(
    sandbox, runtime, task_context
):
    # Pre-existing item E behavior: worker already sits on the target board.
    context = _qa_worker_context(task_context, board="fleet-ops")
    decision = runtime.pre_tool_call(
        "kanban_comment",
        {"task_id": "t_merge_card", "text": "gate:review=pass"},
        context,
    )
    assert decision.decision == "allow", decision


# ------------------------------------------------- fail-closed preserved


def test_foreign_card_self_assignment_denied(sandbox, runtime, task_context):
    # qa attesting a card assigned to qa on ANOTHER board is still self-approval.
    home = sandbox
    _make_board_db(
        home / "kanban" / "boards" / "rr-team" / BOARD_DB,
        {"t_qa_peer": ("qa", "running")},
    )
    context = _qa_worker_context(task_context, board="default")
    decision = runtime.pre_tool_call(
        "kanban_comment",
        {"task_id": "t_qa_peer", "board": "rr-team", "text": "gate:review=pass"},
        context,
    )
    assert (decision.decision, decision.rule_id) == ("deny", "gate_forgery"), decision


def test_unknown_target_card_denied(sandbox, runtime, task_context):
    context = _qa_worker_context(task_context, board="default")
    decision = runtime.pre_tool_call(
        "kanban_comment",
        {"task_id": "t_missing", "text": "gate:review=pass"},
        context,
    )
    assert (decision.decision, decision.rule_id) == ("deny", "gate_forgery"), decision


def test_own_card_review_marker_denied(sandbox, runtime, task_context):
    # Regression for the live incident: the marker attempt on the worker's OWN
    # qa card must keep failing as self-approval (t_b817cf9b, 20:33:53Z).
    context = _qa_worker_context(task_context, board="default")
    decision = runtime.pre_tool_call(
        "kanban_comment",
        {"task_id": "t_worker_card", "text": "gate:review=pass"},
        context,
    )
    assert (decision.decision, decision.rule_id) == ("deny", "gate_forgery"), decision


def test_unauthorized_role_still_denied(sandbox, runtime, task_context):
    # tech cannot attest the review gate regardless of board resolution.
    context = dict(_qa_worker_context(task_context, board="default"), profile="tech")
    decision = runtime.pre_tool_call(
        "kanban_comment",
        {"task_id": "t_merge_card", "board": "fleet-ops", "text": "gate:review=pass"},
        context,
    )
    assert (decision.decision, decision.rule_id) == ("deny", "gate_forgery"), decision


# ------------------------------------------------------- resolver probes


def test_task_assignee_single_board_probe_unchanged(sandbox):
    assert task_assignee("fleet-ops", "t_merge_card") == "company"
    assert task_assignee("default", "t_worker_card") == "qa"


def test_task_assignee_resolved_finds_crossboard_card(sandbox):
    # The miss that caused the incident: default board has no t_merge_card;
    # the resolver must fall through to the fleet-ops sibling registry.
    assert task_assignee_resolved("default", "t_merge_card") == ("company", "fleet-ops")
    assert task_assignee_resolved("fleet-ops", "t_merge_card") == ("company", "fleet-ops")
    assert task_assignee_resolved("default", "t_worker_card") == ("qa", "default")


def test_task_assignee_resolved_miss_is_none(sandbox):
    assert task_assignee_resolved("default", "t_missing") == (None, "")


def test_pinned_db_keeps_single_store_semantics(sandbox, tmp_path, monkeypatch):
    # An explicit HERMES_KANBAN_DB pin means the operator bound the fleet to
    # one store; a miss there fails closed without sibling scanning.
    pinned = tmp_path / "pinned" / BOARD_DB
    _make_board_db(pinned, {"t_unrelated": ("company", "todo")})
    monkeypatch.setenv("HERMES_KANBAN_DB", str(pinned))
    assert task_assignee_resolved("fleet-ops", "t_merge_card") == (None, "")
    assert task_assignee_resolved("fleet-ops", "t_unrelated") == ("company", "")
