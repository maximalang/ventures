from __future__ import annotations

from fleet_policy.redaction import args_hash


def test_missing_task_type_denies(runtime, task_context):
    task_context["task_body"] = "no marker"
    decision = runtime.pre_tool_call("read_file", {"path": "README.md"}, task_context)
    assert (decision.decision, decision.rule_id) == ("deny", "missing_or_unknown_task_type")


def test_unknown_task_type_denies(runtime, task_context):
    task_context["task_body"] = "task_type: unknown"
    decision = runtime.pre_tool_call("read_file", {"path": "README.md"}, task_context)
    assert decision.decision == "deny"


def test_allow_and_normalized_decision(runtime, task_context):
    decision = runtime.pre_tool_call("read_file", {"path": "README.md"}, task_context)
    payload = decision.as_dict()
    assert payload["decision"] == "allow"
    assert set(payload) == {"decision", "rule_id", "reason", "task_id", "project", "profile", "action", "target", "args_hash", "timestamp", "budget_snapshot", "approval_card"}


def test_approval_binding_one_time_and_payload_change(runtime, task_context):
    args = {"command": "deploy production release-a"}
    first = runtime.pre_tool_call("terminal", args, task_context)
    assert first.decision == "approval_required"
    key = first.approval_card["rule_key"]
    assert runtime.store.decide_approval(key, True, "user")

    task_context["tool_call_id"] = "call-2"
    allowed = runtime.pre_tool_call("terminal", args, task_context)
    assert (allowed.decision, allowed.rule_id) == ("allow", "approved_once")

    task_context["tool_call_id"] = "call-3"
    replay = runtime.pre_tool_call("terminal", args, task_context)
    assert replay.decision == "approval_required"

    changed = dict(args, command="deploy production release-b")
    task_context["tool_call_id"] = "call-4"
    invalid = runtime.pre_tool_call("terminal", changed, task_context)
    assert invalid.decision == "approval_required"
    assert invalid.args_hash != args_hash(args)


def test_rejected_approval_never_allows(runtime, task_context):
    decision = runtime.pre_tool_call("terminal", {"command": "git push origin main"}, task_context)
    assert runtime.store.decide_approval(decision.approval_card["rule_key"], False, "user")
    task_context["tool_call_id"] = "next"
    again = runtime.pre_tool_call("terminal", {"command": "git push origin main"}, task_context)
    assert again.decision == "approval_required"


def test_identical_call_loop(runtime, task_context):
    args = {"path": "README.md"}
    for index in range(3):
        task_context["tool_call_id"] = f"read-{index}"
        assert runtime.pre_tool_call("read_file", args, task_context).decision == "allow"
        runtime.post_tool_call("read_file", args, task_context, success=True)
    task_context["tool_call_id"] = "read-4"
    stopped = runtime.pre_tool_call("read_file", args, task_context)
    assert (stopped.decision, stopped.rule_id) == ("deny", "identical_call_loop")


def test_same_failure_signature_stops(runtime, task_context):
    args = {"command": "python build.py"}
    for index in range(2):
        task_context["tool_call_id"] = f"fail-{index}"
        event = runtime.post_tool_call("terminal", args, task_context, success=False, error_type="tool_error", error_message="boom 42")
    assert event["rule_id"] == "same_failure_loop"


def test_tool_call_budget_exhaustion(runtime, task_context):
    limit = runtime.config["budgets"]["code"]["tool_calls"]
    runtime.store.add_budget("t_test", "tool_calls", limit, "seed")
    decision = runtime.pre_tool_call("write_file", {"path": "x.txt", "content": "x"}, task_context)
    assert (decision.decision, decision.rule_id) == ("deny", "budget_exhausted")
    assert decision.budget_snapshot["used"]["tool_calls"] >= limit


def test_token_budget_and_idle_stop(runtime, task_context):
    runtime.store.add_budget("t_test", "tokens", 179999, "seed")
    task_context["api_request_id"] = "api-1"
    payload = runtime.post_api_request(task_context, {"input_tokens": 1, "output_tokens": 1}, 1)
    assert payload["rule_id"] == "budget_exhausted"

    fresh = dict(task_context, task_id="t_idle", task_body="task_type: review")
    for index in range(3):
        fresh["api_request_id"] = f"idle-{index}"
        idle_payload = runtime.post_api_request(fresh, {}, 0)
    assert idle_payload["rule_id"] == "idle_turn_loop"


def test_retry_budget_uses_kanban_limit(runtime, task_context):
    task_context["max_retries"] = 1
    # First error of a class is a marker, not a retry — only a repeated error
    # consumes budget, so provider fallback chains do not burn it.
    task_context["api_request_id"] = "api-error-1"
    assert runtime.api_request_error(task_context, RuntimeError("failure")) is None
    task_context["api_request_id"] = "api-error-2"
    payload = runtime.api_request_error(task_context, RuntimeError("failure again"))
    assert payload["rule_id"] == "retry_budget_exhausted"


def test_provider_fallback_chain_does_not_consume_retries(runtime, task_context):
    # zai 429 -> codex 429 -> custom: distinct errors within one healthy turn.
    task_context["api_request_id"] = "fb-1"
    assert runtime.api_request_error(task_context, ConnectionError("zai 429")) is None
    task_context["api_request_id"] = "fb-2"
    assert runtime.api_request_error(task_context, TimeoutError("codex 429")) is None
    assert runtime.store.budget(task_context["task_id"]).get("retries", 0) == 0


def test_monetary_cost_is_not_fake_zero(runtime, task_context):
    snapshot = runtime.budget_snapshot(task_context, "code")
    assert snapshot["monetary_cost"] == {"status": "unavailable", "amount": None, "currency": None}
