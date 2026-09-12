"""v1.2.13 M-E: board lifecycle tools are exempt from anti-loop collapse.

Defect class (observed in production runs): a worker whose executive calls get
denied twice (terminal → same_failure_loop, repeated read → identical_call_loop)
loses its ONLY coordination channel — the lifecycle transition (complete /
block / comment / heartbeat) is itself counted as a repeated failing call and
collapsed, stranding the card with no way to hand off. Run 655 hit exactly this
on repeated board-read calls.

Contract under test:
- lifecycle calls never fire identical_call_loop (pre) or same_failure_loop
  (post), no matter how many identical repeats or identical failures accrue;
- after two executive terminal-denies the lifecycle transition stays allow;
- executive tools (terminal) keep FULL collapse guarding — same threshold,
  same stop classes;
- the exemption is not a budget exemption: lifecycle calls still charge the
  tool-call ledger and still deny on budget_exhausted, so a runaway lifecycle
  loop remains bounded;
- the call/failure ledger still records every lifecycle repeat (audit intact).
"""
from __future__ import annotations

from fleet_policy.policy import LIFECYCLE_TOOLS, is_lifecycle_tool
from fleet_policy.redaction import args_hash, stable_id
from fleet_policy.runtime import FleetPolicyRuntime


def _signature_count(runtime, task_context, column, tool_name, arguments, *, failure=None):
    target = FleetPolicyRuntime._target(tool_name, arguments)
    if column == "call_signature":
        value = stable_id(tool_name, args_hash(arguments), target)
    else:
        normalized = " ".join(str(failure or "").lower().split())[:300]
        value = stable_id(tool_name, args_hash(arguments), "tool_error", normalized)
    run_key = runtime._run_key(task_context) or None
    return runtime.store.count_signature(task_context["task_id"], column, value, run_key)


def test_lifecycle_namespace_membership_is_normalized():
    assert is_lifecycle_tool("kanban_complete")
    assert is_lifecycle_tool("kanban_heartbeat")
    assert is_lifecycle_tool("functions.kanban_show")  # namespaced direct call
    assert not is_lifecycle_tool("terminal")
    assert not is_lifecycle_tool("write_file")
    assert not is_lifecycle_tool("read_file")
    assert not is_lifecycle_tool("kanban_db_poke")  # unknown names stay out
    assert "kanban_request_review" in LIFECYCLE_TOOLS
    assert "kanban_request_changes" in LIFECYCLE_TOOLS


def test_identical_lifecycle_reads_never_collapse(runtime, task_context):
    # Run-655 replay: the same board read repeated past max_identical_calls.
    args = {"task_id": task_context["task_id"]}
    for index in range(5):
        task_context["tool_call_id"] = f"show-{index}"
        decision = runtime.pre_tool_call("kanban_show", args, task_context)
        assert decision.decision == "allow", (index, decision.rule_id)
        runtime.post_tool_call("kanban_show", args, task_context, success=True)
    # The ledger still counts every repeat (audit intact) — only the deny is
    # suppressed.
    assert _signature_count(runtime, task_context, "call_signature", "kanban_show", args) >= 5
    task_context["tool_call_id"] = "show-6"
    assert runtime.pre_tool_call("kanban_show", args, task_context).decision == "allow"


def test_identical_executive_calls_still_collapse(runtime, task_context):
    # Control: the exemption does not leak to executive/read tooling.
    args = {"path": "README.md"}
    for index in range(3):
        task_context["tool_call_id"] = f"read-{index}"
        assert runtime.pre_tool_call("read_file", args, task_context).decision == "allow"
        runtime.post_tool_call("read_file", args, task_context, success=True)
    task_context["tool_call_id"] = "read-4"
    stopped = runtime.pre_tool_call("read_file", args, task_context)
    assert (stopped.decision, stopped.rule_id) == ("deny", "identical_call_loop")


def test_lifecycle_failures_never_fire_same_failure_loop(runtime, task_context):
    args = {"task_id": task_context["task_id"], "note": "still alive"}
    events = []
    for index in range(4):
        task_context["tool_call_id"] = f"hb-{index}"
        events.append(runtime.post_tool_call(
            "kanban_heartbeat", args, task_context, success=False,
            error_type="tool_error", error_message="board unreachable",
        ))
    assert all(event is None for event in events), events
    # Failure signature rows are still recorded for audit.
    assert _signature_count(
        runtime, task_context, "failure_signature", "kanban_heartbeat", args,
        failure="board unreachable",
    ) == 4
    with runtime.store.connect() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM events WHERE kind='anti_loop_stop'"
        ).fetchone()[0] == 0


def test_executive_failures_still_fire_same_failure_loop(runtime, task_context):
    args = {"command": "python build.py"}
    for index in range(2):
        task_context["tool_call_id"] = f"fail-{index}"
        event = runtime.post_tool_call(
            "terminal", args, task_context, success=False,
            error_type="tool_error", error_message="boom 42",
        )
    assert event is not None and event["rule_id"] == "same_failure_loop"


def test_lifecycle_transition_stays_allow_after_executive_denies(runtime, task_context):
    # The production stranding class: two identical terminal failures fire the
    # executive stop; the worker must STILL be able to hand off via lifecycle
    # transitions afterwards.
    args = {"command": "git cat-file -e deadbeef^{commit}"}
    for index in range(2):
        task_context["tool_call_id"] = f"term-{index}"
        event = runtime.post_tool_call(
            "terminal", args, task_context, success=False,
            error_type="tool_error", error_message="fatal: Not a valid object name",
        )
    assert event is not None and event["rule_id"] == "same_failure_loop"

    for tool, arguments in (
        ("kanban_comment", {"task_id": task_context["task_id"], "body": "handoff: blocked by denied step"}),
        ("kanban_block", {"reason": "executive step denied twice; needs owner decision"}),
        ("kanban_complete", {"summary": "delivered scope; evidence in comment thread"}),
        ("kanban_heartbeat", {"note": "alive"}),
    ):
        task_context["tool_call_id"] = f"lc-{tool}"
        decision = runtime.pre_tool_call(tool, arguments, task_context)
        assert decision.decision == "allow", (tool, decision.rule_id, decision.reason)


def test_lifecycle_calls_still_charge_budget_and_respect_exhaustion(runtime, task_context):
    # The exemption is anti-collapse only: the tool-call ledger still charges
    # every lifecycle call, and a hard-exhausted budget still denies it.
    args = {"note": "alive"}
    task_context["tool_call_id"] = "hb-budget-1"
    runtime.pre_tool_call("kanban_heartbeat", args, task_context)
    limit = runtime.config["budgets"]["code"]["tool_calls"]
    runtime.store.add_budget(task_context["task_id"], "tool_calls", limit, "seed", runtime._run_key(task_context))
    task_context["tool_call_id"] = "hb-budget-2"
    stopped = runtime.pre_tool_call("kanban_heartbeat", args, task_context)
    assert (stopped.decision, stopped.rule_id) == ("deny", "budget_exhausted")
