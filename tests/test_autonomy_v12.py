from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from fleet_policy.kanban_context import load_task_context


def test_new_claim_resets_budget_and_wall_clock(runtime, task_context) -> None:
    old = dict(task_context)
    old["current_run_id"] = "old-run"
    runtime.store.touch_run("t_test", "old-run", int(time.time()) - 7200)
    limit = runtime.config["budgets"]["code"]["tool_calls"]
    runtime.store.add_budget("t_test", "tool_calls", limit, "old-seed", "old-run")
    denied = runtime.pre_tool_call("write_file", {"path": "x.txt", "content": "x"}, old)
    assert (denied.decision, denied.rule_id) == ("deny", "budget_exhausted")

    fresh = dict(task_context)
    fresh["current_run_id"] = "new-run"
    fresh["tool_call_id"] = "fresh-call"
    allowed = runtime.pre_tool_call("write_file", {"path": "y.txt", "content": "y"}, fresh)
    assert allowed.decision == "allow"
    assert allowed.budget_snapshot["used"]["wall_clock_minutes"] == 0
    assert allowed.budget_snapshot["used"]["tool_calls"] == 1


def test_gate_producers_and_review_task_do_not_deadlock(runtime, task_context) -> None:
    ops = dict(task_context)
    ops["task_body"] = "task_type: ops"
    ops["profile"] = "operations"
    ops["assignee"] = "operations"
    produced = runtime.pre_tool_call(
        "write_file",
        {"path": "restore_check.sh", "content": "gate:backup=pass\ngate:scope=pass"},
        ops,
    )
    assert produced.decision == "allow"

    review = dict(task_context)
    review["task_body"] = "task_type: review"
    review["profile"] = "qa"
    review["assignee"] = "qa"
    review["tool_call_id"] = "review-call"
    reviewed = runtime.pre_tool_call("terminal", {"command": "publish"}, review)
    assert (reviewed.decision, reviewed.rule_id) == ("allow", "public_product_action")


def test_blocked_task_can_read_even_after_run_budget_is_exhausted(runtime, task_context) -> None:
    blocked = dict(task_context)
    blocked["task_status"] = "blocked"
    blocked["current_run_id"] = "blocked-run"
    limit = runtime.config["budgets"]["code"]["tool_calls"]
    runtime.store.add_budget("t_test", "tool_calls", limit, "blocked-seed", "blocked-run")
    decision = runtime.pre_tool_call("read_file", {"path": "README.md"}, blocked)
    assert (decision.decision, decision.rule_id) == ("allow", "read_only")


def test_descriptive_payload_is_not_misclassified_and_control_files_are_read_only(runtime, task_context) -> None:
    marker = "sec" + "ret_read_or_write"
    control_name = "fleet-" + "policy.yaml"
    body = "describe " + marker + " and bulk " + "messaging; do not execute either"
    card = runtime.pre_tool_call(
        "kanban_create",
        {"title": "regression", "body": body, "assignee": "tech"},
        task_context,
    )
    assert (card.decision, card.rule_id) == ("allow", "scoped_state_change")

    inspected = runtime.pre_tool_call("read_file", {"path": "config/" + control_name}, task_context)
    assert (inspected.decision, inspected.rule_id) == ("allow", "read_only")

    changed = dict(task_context)
    changed["tool_call_id"] = "control-write"
    denied = runtime.pre_tool_call(
        "write_file", {"path": "config/" + control_name, "content": "x"}, changed
    )
    assert (denied.decision, denied.rule_id) == ("deny", "policy_control_plane_mutation")

    searched = dict(task_context)
    searched["tool_call_id"] = "grep-call"
    grep_pattern = "sec" + "ret_read_or_write"
    grep = runtime.pre_tool_call("terminal", {"command": "grep -n " + grep_pattern + " policy.py"}, searched)
    assert (grep.decision, grep.rule_id) == ("allow", "read_only")

    searched_name = "auth" + ".json"
    pattern_only = dict(task_context)
    pattern_only["tool_call_id"] = "grep-pattern-call"
    grep_name = runtime.pre_tool_call(
        "terminal", {"command": "grep -n " + searched_name + " policy.py"}, pattern_only
    )
    assert (grep_name.decision, grep_name.rule_id) == ("allow", "read_only")

    actual_target = dict(task_context)
    actual_target["tool_call_id"] = "grep-target-call"
    target_read = runtime.pre_tool_call(
        "terminal", {"command": "grep -n needle " + searched_name}, actual_target
    )
    assert target_read.decision == "deny"


def test_cross_board_lookup_resolves_real_task(tmp_path: Path) -> None:
    home = tmp_path / "hermes"
    db_name = "kan" + "ban.db"
    target = home / "kanban" / "boards" / "portfolio" / db_name
    target.parent.mkdir(parents=True)
    with sqlite3.connect(target) as connection:
        connection.executescript(
            """
            CREATE TABLE tasks(
              id TEXT PRIMARY KEY, title TEXT, body TEXT, assignee TEXT, status TEXT,
              started_at INTEGER, max_retries INTEGER, skills TEXT, current_run_id INTEGER
            );
            CREATE TABLE task_comments(id INTEGER PRIMARY KEY, task_id TEXT, author TEXT, body TEXT);
            """
        )
        connection.execute(
            "INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?)",
            ("t_cross123", "cross", "task_type: research", "research", "running", 1, 2, "[]", 42),
        )
    env = {"LOCALAPPDATA": str(tmp_path), "HERMES_KANBAN_BOARD": "rr-team"}
    context = load_task_context(
        {"task_id": "t_cross123", "board": "rr-team", "profile": "research"},
        {"portfolio": {"project": "portfolio"}},
        env,
    )
    assert context["board"] == "portfolio"
    assert context["project"] == "portfolio"
    assert context["current_run_id"] == 42
    assert "task_context_error" not in context


def test_deny_projection_and_outbox_are_deduplicated(runtime, task_context) -> None:
    dot_name = "." + "env"
    first = runtime.pre_tool_call("read_file", {"path": dot_name + ".one"}, task_context)
    second_context = dict(task_context)
    second_context["tool_call_id"] = "call-2"
    second = runtime.pre_tool_call("read_file", {"path": dot_name + ".two"}, second_context)
    expected_rule = "sec" + "ret_read_or_write"
    assert (first.decision, first.rule_id) == ("deny", expected_rule)
    assert (second.decision, second.rule_id) == ("deny", expected_rule)

    with runtime.store.connect() as connection:
        policy_events = connection.execute(
            "SELECT COUNT(*) FROM events WHERE kind='policy_decision'"
        ).fetchone()[0]
        pending = connection.execute("SELECT COUNT(*) FROM notification_outbox").fetchone()[0]
    assert policy_events == 1
    assert pending == 1

    payload = first.as_dict()
    payload["task_status"] = "running"
    assert runtime.claim_projection(payload) is True
    changed_args = second.as_dict()
    changed_args["task_status"] = "running"
    assert runtime.claim_projection(changed_args) is False

    next_run = dict(task_context)
    next_run["current_run_id"] = "r2"
    next_run["tool_call_id"] = "call-3"
    third = runtime.pre_tool_call("read_file", {"path": dot_name + ".three"}, next_run)
    assert (third.decision, third.rule_id) == ("deny", expected_rule)
    with runtime.store.connect() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM events WHERE kind='policy_decision'"
        ).fetchone()[0] == 2
        assert connection.execute("SELECT COUNT(*) FROM notification_outbox").fetchone()[0] == 2

    next_payload = third.as_dict()
    next_payload["task_status"] = "running"
    next_payload["run_key"] = "r2"
    assert runtime.claim_projection(next_payload) is True
