"""v1.2.37 (card t_b71d23c0, spec docs/fleet-ops/policy-budget-grace-20261007):
terminal grace on tool_calls budget exhaustion.

Root cause: run 106 of t_173c47e4 (2026-10-07) — a hard tool_calls budget
deny severed every tool incl. the lifecycle channel while post_api_request
stopped the loop in the same turn, so the run was recorded as a false
"protocol violation" crash and the in-session handoff was lost.

Contract under test:
1. pure tool_calls exhaustion denies non-lifecycle tools with
   budget_exhausted, and the deny message carries the close-now instruction
   (kanban_complete / kanban_block with a partial handoff);
2. the first GRACE_LIFECYCLE_CALLS lifecycle calls stay allowed and are
   counted; the call past the grace budget denies again (runaway cap kept)
   and every call still charges the tool-call ledger;
3. post_api_request holds its stop payload while grace remains (unused or
   partially used) and stops once the lifecycle grace is spent OR
   GRACE_LLM_REQUESTS llm requests passed since first detection — whichever
   comes first;
4. wall_clock exhaustion stops immediately with no grace (unchanged);
5. the v1.2.13 anti-loop lifecycle exemption is unaffected during grace:
   identical lifecycle repeats do not collapse into identical_call_loop —
   they are bounded by the grace cap alone;
6. every grace transition emits a budget_grace policy event
   (open/use/exhaust) carrying task/run/call_index, significant=False.

QA run 141 regressions (card t_b71d23c0):
F1. the worker-visible hook message of the integration adapter must surface
    the close-now instruction (the runtime carried it only in the internal
    reason, the adapter dropped it);
F2. stop-payload delivery idempotency is per (task_id, run_key): a previous
    run's budget_or_loop_stop event must not suppress the mandatory stop of
    a later scoped run — same or fresh runtime — while the stop is still
    delivered exactly once within a run.
"""
from __future__ import annotations

import importlib.util
import json
import time
from pathlib import Path

from fleet_policy.policy import GRACE_LIFECYCLE_CALLS, GRACE_LLM_REQUESTS
from fleet_policy.runtime import FleetPolicyRuntime


def _exhaust_tool_calls(runtime, task_context) -> int:
    """Seed the run-scoped ledger so used tool_calls == the configured limit."""
    limit = int(runtime.config["budgets"]["code"]["tool_calls"])
    runtime.store.add_budget(
        task_context["task_id"], "tool_calls", limit, "seed",
        runtime._run_key(task_context),
    )
    return limit


def _grace_events(runtime, task_id) -> list[dict]:
    with runtime.store.connect() as connection:
        rows = connection.execute(
            "SELECT payload_json FROM events WHERE task_id=? AND kind='budget_grace' ORDER BY rowid",
            (task_id,),
        ).fetchall()
    return [json.loads(row["payload_json"]) for row in rows]


def _transitions(runtime, task_id) -> list[str]:
    return [event["transition"] for event in _grace_events(runtime, task_id)]


# --- SPEC scenario 1: non-lifecycle deny carries the close-now instruction ---

def test_non_lifecycle_deny_carries_close_now_instruction(runtime, task_context):
    _exhaust_tool_calls(runtime, task_context)
    decision = runtime.pre_tool_call("write_file", {"path": "x.txt", "content": "x"}, task_context)
    assert (decision.decision, decision.rule_id) == ("deny", "budget_exhausted")
    assert "kanban_complete" in decision.reason
    assert "kanban_block" in decision.reason
    assert "NOW" in decision.reason
    assert "partial handoff" in decision.reason
    # Detection opened the grace window exactly once.
    assert _transitions(runtime, task_context["task_id"]) == ["open"]


# --- SPEC scenario 2: lifecycle calls 1..3 allowed and counted, #4 denied ---

def test_lifecycle_grace_calls_allowed_counted_then_capped(runtime, task_context):
    limit = _exhaust_tool_calls(runtime, task_context)
    for index in range(1, GRACE_LIFECYCLE_CALLS + 1):
        task_context["tool_call_id"] = f"grace-{index}"
        decision = runtime.pre_tool_call("kanban_heartbeat", {"note": f"closing {index}"}, task_context)
        assert decision.decision == "allow", (index, decision.rule_id)
    task_context["tool_call_id"] = "grace-over"
    stopped = runtime.pre_tool_call("kanban_heartbeat", {"note": "one too many"}, task_context)
    assert (stopped.decision, stopped.rule_id) == ("deny", "budget_exhausted")

    events = _grace_events(runtime, task_context["task_id"])
    assert [event["transition"] for event in events] == ["open", "use", "use", "use", "exhaust"]
    assert [event["call_index"] for event in events if event["transition"] == "use"] == [1, 2, 3]
    assert all(event["task_id"] == task_context["task_id"] for event in events)
    assert all(event["run_key"] == runtime._run_key(task_context) for event in events)
    # Denied calls still charge the tool-call ledger (pre-grace invariant):
    # seed + 3 grace-allowed + 1 denied all land in the run ledger.
    used = runtime.store.budget_for_run(task_context["task_id"], runtime._run_key(task_context))
    assert used["tool_calls"] == limit + GRACE_LIFECYCLE_CALLS + 1


# --- SPEC scenario 3: post_api_request stop timing ---

def test_post_api_request_holds_stop_while_grace_unused(runtime, task_context):
    _exhaust_tool_calls(runtime, task_context)
    for index in range(GRACE_LLM_REQUESTS):
        task_context["api_request_id"] = f"llm-{index}"
        assert runtime.post_api_request(task_context, None, 1) is None, index
    task_context["api_request_id"] = "llm-final"
    payload = runtime.post_api_request(task_context, None, 1)
    assert payload is not None and payload["rule_id"] == "budget_exhausted"
    assert _transitions(runtime, task_context["task_id"]) == ["open", "exhaust"]


def test_post_api_request_holds_with_partially_used_grace(runtime, task_context):
    _exhaust_tool_calls(runtime, task_context)
    task_context["tool_call_id"] = "close-1"
    assert runtime.pre_tool_call("kanban_heartbeat", {"note": "c1"}, task_context).decision == "allow"
    task_context["api_request_id"] = "llm-partial"
    assert runtime.post_api_request(task_context, None, 1) is None


def test_post_api_request_stops_once_lifecycle_grace_spent(runtime, task_context):
    _exhaust_tool_calls(runtime, task_context)
    for index in range(GRACE_LIFECYCLE_CALLS):
        task_context["tool_call_id"] = f"close-{index}"
        decision = runtime.pre_tool_call("kanban_heartbeat", {"note": str(index)}, task_context)
        assert decision.decision == "allow", (index, decision.rule_id)
    # The very next llm request stops the loop even though no llm request has
    # passed since detection — the lifecycle cap hit first.
    task_context["api_request_id"] = "llm-after-grace"
    payload = runtime.post_api_request(task_context, None, 1)
    assert payload is not None and payload["rule_id"] == "budget_exhausted"


# --- SPEC scenario 4: other metrics unchanged — wall_clock stops immediately ---

def test_wall_clock_exhaustion_stops_immediately_without_grace(runtime, task_context):
    limit_minutes = int(runtime.config["budgets"]["code"]["wall_clock_minutes"])
    runtime.store.touch_run(
        task_context["task_id"], runtime._run_key(task_context),
        int(time.time()) - (limit_minutes + 5) * 60,
    )
    payload = runtime.post_api_request(task_context, None, 1)
    assert payload is not None and payload["rule_id"] == "budget_exhausted"
    assert "wall_clock" in payload["reason"]
    # No grace window was opened, and lifecycle tools deny immediately too.
    assert _grace_events(runtime, task_context["task_id"]) == []
    task_context["tool_call_id"] = "wc-1"
    decision = runtime.pre_tool_call("kanban_comment", {"task_id": task_context["task_id"], "body": "x"}, task_context)
    assert (decision.decision, decision.rule_id) == ("deny", "budget_exhausted")
    assert _grace_events(runtime, task_context["task_id"]) == []


# --- SPEC scenario 5: v1.2.13 anti-loop exemption intact during grace ---

def test_anti_loop_lifecycle_exemption_intact_during_grace(runtime, task_context):
    _exhaust_tool_calls(runtime, task_context)
    args = {"task_id": task_context["task_id"], "body": "same closing note"}
    # Identical lifecycle repeats during grace do not collapse into
    # identical_call_loop; they are bounded by the grace cap alone.
    for index in range(GRACE_LIFECYCLE_CALLS):
        task_context["tool_call_id"] = f"lc-{index}"
        decision = runtime.pre_tool_call("kanban_comment", args, task_context)
        assert decision.decision == "allow", (index, decision.rule_id)
        assert decision.rule_id != "identical_call_loop"
    task_context["tool_call_id"] = "lc-final"
    stopped = runtime.pre_tool_call("kanban_comment", args, task_context)
    assert (stopped.decision, stopped.rule_id) == ("deny", "budget_exhausted")


# --- SPEC scenario 6: grace state is scoped per (task_id, run_key) ---

def test_grace_state_is_scoped_per_run(runtime, task_context):
    _exhaust_tool_calls(runtime, task_context)
    for index in range(GRACE_LIFECYCLE_CALLS):
        task_context["tool_call_id"] = f"run-a-{index}"
        assert runtime.pre_tool_call("kanban_heartbeat", {"note": str(index)}, task_context).decision == "allow"
    task_context["tool_call_id"] = "run-a-over"
    assert runtime.pre_tool_call("kanban_heartbeat", {"note": "x"}, task_context).decision == "deny"
    # A new dispatch run gets its own grace budget (and its own ledger, so the
    # new run is not even exhausted yet — seed it to the limit to isolate the
    # grace counter from the budget counter).
    new_run = dict(task_context, current_run_id="r2", run_id="r2")
    runtime.store.add_budget(
        task_context["task_id"], "tool_calls",
        int(runtime.config["budgets"]["code"]["tool_calls"]), "seed-r2", "r2",
    )
    new_run["tool_call_id"] = "run-b-1"
    decision = runtime.pre_tool_call("kanban_heartbeat", {"note": "fresh run"}, new_run)
    assert decision.decision == "allow"


# --- QA F1: adapter hook message surfaces the close-now instruction ---

def _load_adapter(name: str):
    module_path = (
        Path(__file__).parents[1] / "integrations" / "hermes" / "fleet-policy-plugin" / "__init__.py"
    )
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_hook_message_surfaces_close_now_instruction(runtime, task_context, monkeypatch):
    """Adapter-level regression for QA F1: real runtime + real integration
    adapter; only the external context lookup and the board projection are
    replaced by fixtures/capture."""
    _exhaust_tool_calls(runtime, task_context)
    module = _load_adapter("fp_plugin_v1237_grace_message")
    monkeypatch.setattr(module, "_RUNTIME", runtime)
    monkeypatch.setattr(module, "context", lambda kwargs: dict(task_context))
    projected = []
    monkeypatch.setattr(module, "_project", lambda payload: projected.append(payload))

    output = module.pre_tool_call("write_file", {"path": "x.txt", "content": "x"})
    assert output["action"] == "block"
    message = output["message"]
    assert "budget_exhausted" in message
    assert "kanban_complete" in message and "kanban_block" in message
    assert "NOW" in message and "partial handoff" in message
    assert f"{GRACE_LIFECYCLE_CALLS} lifecycle grace calls remain" in message
    # The company-route projection is unchanged: exactly one projection with
    # the internal reason intact.
    assert len(projected) == 1
    assert projected[0]["rule_id"] == "budget_exhausted"
    assert "kanban_complete" in projected[0]["reason"]


# --- QA F2: stop delivery is idempotent per (task, run), mandatory per run ---

def _run_to_cap(rt, ctx, tag: str):
    """Drive post_api_request past GRACE_LLM_REQUESTS and return the stop."""
    for index in range(GRACE_LLM_REQUESTS):
        ctx["api_request_id"] = f"{tag}-{index}"
        assert rt.post_api_request(ctx, None, 1) is None, (tag, index)
    ctx["api_request_id"] = f"{tag}-final"
    return rt.post_api_request(ctx, None, 1)


def test_stop_delivered_once_per_run_and_again_for_new_runs(runtime, task_context):
    _exhaust_tool_calls(runtime, task_context)
    stop_a = _run_to_cap(runtime, task_context, "run-a")
    assert stop_a is not None and stop_a["rule_id"] == "budget_exhausted"
    assert stop_a["run_key"] == runtime._run_key(task_context)
    # Within the same run the stop payload is delivered exactly once.
    task_context["api_request_id"] = "run-a-repeat"
    assert runtime.post_api_request(task_context, None, 1) is None

    limit = int(runtime.config["budgets"]["code"]["tool_calls"])

    # Same runtime, new scoped run: the previous run's stop event must not
    # suppress this run's mandatory stop.
    run_b = dict(task_context, current_run_id="r2", run_id="r2")
    runtime.store.add_budget(task_context["task_id"], "tool_calls", limit, "seed-r2", "r2")
    stop_b = _run_to_cap(runtime, run_b, "run-b")
    assert stop_b is not None and stop_b["run_key"] == "r2"

    # Fresh runtime on the same DB (in-memory grace registry lost): the stop
    # is still delivered for the new scoped run.
    fresh = FleetPolicyRuntime(
        runtime.root,
        config_path=runtime.root / "config" / "fleet-policy.yaml",
        db_path=runtime.store.path,
    )
    run_c = dict(task_context, current_run_id="r3", run_id="r3")
    fresh.store.add_budget(task_context["task_id"], "tool_calls", limit, "seed-r3", "r3")
    stop_c = _run_to_cap(fresh, run_c, "run-c")
    assert stop_c is not None and stop_c["run_key"] == "r3"

    # One stop event row per run, none shared across runs.
    with fresh.store.connect() as connection:
        rows = connection.execute(
            "SELECT payload_json FROM events WHERE task_id=? AND kind='budget_or_loop_stop' ORDER BY rowid",
            (task_context["task_id"],),
        ).fetchall()
    runs = [json.loads(row["payload_json"])["run_key"] for row in rows]
    assert sorted(runs) == ["r1", "r2", "r3"]
