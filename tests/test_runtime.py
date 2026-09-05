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
    assert set(payload) == {"decision", "rule_id", "reason", "task_id", "project", "profile", "action", "target", "args_hash", "timestamp", "budget_snapshot", "approval_card", "pattern_category", "call_index", "deny_nonce"}
    # v1.2.10 item C: deny_nonce is reserved for the review-probe lane and
    # must stay None on ordinary decisions.
    assert payload["deny_nonce"] is None


def test_approval_binding_one_time_and_payload_change(runtime, task_context, monkeypatch):
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    args = {"command": "mass outreach to 5000 contacts"}
    first = runtime.pre_tool_call("terminal", args, task_context)
    assert first.decision == "approval_required"
    key = first.approval_card["rule_key"]
    assert runtime.store.decide_approval(key, True, "user", confirm_code=key[-8:])

    task_context["tool_call_id"] = "call-2"
    allowed = runtime.pre_tool_call("terminal", args, task_context)
    assert (allowed.decision, allowed.rule_id) == ("allow", "approved_once")

    task_context["tool_call_id"] = "call-3"
    replay = runtime.pre_tool_call("terminal", args, task_context)
    assert replay.decision == "approval_required"

    changed = dict(args, command="mass outreach to 6000 contacts")
    task_context["tool_call_id"] = "call-4"
    invalid = runtime.pre_tool_call("terminal", changed, task_context)
    assert invalid.decision == "approval_required"
    assert invalid.args_hash != args_hash(args)


def test_rejected_approval_never_allows(runtime, task_context, monkeypatch):
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    decision = runtime.pre_tool_call("terminal", {"command": "mass outreach to 5000 contacts"}, task_context)
    key = decision.approval_card["rule_key"]
    assert runtime.store.decide_approval(key, False, "user", confirm_code=key[-8:])
    task_context["tool_call_id"] = "next"
    again = runtime.pre_tool_call("terminal", {"command": "mass outreach to 5000 contacts"}, task_context)
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


def test_same_failure_stop_is_scoped_to_each_dispatch_run(runtime, task_context):
    # Run 206's stop class: a terminal Git-object check fails twice with the
    # same normalized error. A later genuine dispatch must get a fresh stop,
    # while a third failure in that same run must not emit a second event.
    args = {"command": "git cat-file -e ee3448f4^{commit}"}
    first_run = dict(task_context, current_run_id="206")
    for index in range(2):
        first_run["tool_call_id"] = f"run-206-fail-{index}"
        first = runtime.post_tool_call(
            "terminal", args, first_run, success=False,
            error_type="tool_error", error_message="fatal: Not a valid object name 'ee3448f4^{commit}'",
        )
    assert first["rule_id"] == "same_failure_loop"
    assert first["run_key"] == "206"

    new_run = dict(task_context, current_run_id="207")
    for index in range(2):
        new_run["tool_call_id"] = f"run-207-fail-{index}"
        second = runtime.post_tool_call(
            "terminal", args, new_run, success=False,
            error_type="tool_error", error_message="fatal: Not a valid object name 'ee3448f4^{commit}'",
        )
    assert second["rule_id"] == "same_failure_loop"
    assert second["run_key"] == "207"

    new_run["tool_call_id"] = "run-207-fail-2"
    assert runtime.post_tool_call(
        "terminal", args, new_run, success=False,
        error_type="tool_error", error_message="fatal: Not a valid object name 'ee3448f4^{commit}'",
    ) is None
    with runtime.store.connect() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM events WHERE kind='anti_loop_stop'"
        ).fetchone()[0] == 2
        assert connection.execute("SELECT COUNT(*) FROM notification_outbox").fetchone()[0] == 2


def test_tool_call_budget_exhaustion(runtime, task_context):
    limit = runtime.config["budgets"]["code"]["tool_calls"]
    runtime.store.add_budget("t_test", "tool_calls", limit, "seed", "r1")
    decision = runtime.pre_tool_call("write_file", {"path": "x.txt", "content": "x"}, task_context)
    assert (decision.decision, decision.rule_id) == ("deny", "budget_exhausted")
    assert decision.budget_snapshot["used"]["tool_calls"] >= limit


def test_token_budget_and_idle_stop(runtime, task_context):
    runtime.store.add_budget("t_test", "tokens", 179999, "seed", "r1")
    task_context["api_request_id"] = "api-1"
    payload = runtime.post_api_request(task_context, {"input_tokens": 1, "output_tokens": 1}, 1)
    assert payload["rule_id"] == "budget_exhausted"

    fresh = dict(task_context, task_id="t_idle", task_body="task_type: review")
    for index in range(3):
        fresh["api_request_id"] = f"idle-{index}"
        idle_payload = runtime.post_api_request(fresh, {}, 0)
    assert idle_payload["rule_id"] == "idle_turn_loop"


def test_api_errors_do_not_block_the_worker(runtime, task_context):
    # Retry enforcement is dispatcher-owned (kanban.failure_limit / task
    # max_retries). Hermes fires api_request_error once per failed provider in
    # the fallback chain within a single healthy turn, so the plugin must log
    # the error without consuming any retry budget or blocking the worker.
    task_context["max_retries"] = 1
    task_context["api_request_id"] = "api-error-1"
    assert runtime.api_request_error(task_context, RuntimeError("failure")) is None
    task_context["api_request_id"] = "api-error-2"
    assert runtime.api_request_error(task_context, RuntimeError("failure again")) is None
    assert runtime.store.budget(task_context["task_id"]).get("retries", 0) == 0


def test_provider_fallback_chain_does_not_consume_retries(runtime, task_context):
    # zai 429 -> codex 429 -> custom: distinct errors within one healthy turn.
    task_context["api_request_id"] = "fb-1"
    assert runtime.api_request_error(task_context, ConnectionError("zai 429")) is None
    task_context["api_request_id"] = "fb-2"
    assert runtime.api_request_error(task_context, TimeoutError("codex 429")) is None
    assert runtime.store.budget(task_context["task_id"]).get("retries", 0) == 0


def test_token_budget_counts_generated_tokens_only(runtime, task_context):
    # prompt_tokens is the full re-sent context per request; counting it would
    # exhaust a healthy worker in a handful of calls. Only completion counts.
    runtime.store.add_budget("t_test", "tokens", 119990, "seed")
    task_context["api_request_id"] = "api-ctx-heavy"
    payload = runtime.post_api_request(
        task_context, {"prompt_tokens": 150000, "completion_tokens": 5}, 1
    )
    assert payload is None
    assert runtime.store.budget("t_test")["tokens"] == 119995


def test_missing_request_id_does_not_collapse_token_events(runtime, task_context):
    task_context.pop("api_request_id", None)
    runtime.post_api_request(task_context, {"completion_tokens": 5}, 1)
    runtime.post_api_request(task_context, {"completion_tokens": 5}, 1)
    assert runtime.store.budget(task_context["task_id"])["tokens"] == 10


def test_api_error_dict_records_real_type(runtime, task_context):
    task_context["api_request_id"] = "dict-error"
    runtime.api_request_error(task_context, {"type": "rate_limit", "message": "hidden"})
    with runtime.store.connect() as connection:
        payload = connection.execute(
            "SELECT payload_json FROM events WHERE kind='api_request_error' ORDER BY created_at DESC LIMIT 1"
        ).fetchone()[0]
    assert '"error":"rate_limit"' in payload
    assert "hidden" not in payload


def test_main_merge_is_autonomous_after_independent_gates(runtime, task_context):
    args = {"command": "git push origin main"}
    blocked = runtime.pre_tool_call("terminal", args, task_context)
    assert (blocked.decision, blocked.rule_id) == ("deny", "evidence_gate_missing")
    task_context["comment_records"] = [
        {"author": "tech", "body": "gate:ci=pass"},
        {"author": "qa", "body": "gate:review=pass"},
        {"author": "operations", "body": "gate:rollback=pass"},
    ]
    task_context["tool_call_id"] = "main-ready"
    allowed = runtime.pre_tool_call("terminal", args, task_context)
    assert (allowed.decision, allowed.rule_id) == ("allow", "release_to_protected_branch")


def test_deploy_and_publish_use_evidence_not_user_approval(runtime, task_context):
    deploy_args = {"command": "deploy production"}
    assert runtime.pre_tool_call("terminal", deploy_args, task_context).rule_id == "evidence_gate_missing"
    task_context["comment_records"] = [
        {"author": "tech", "body": "gate:ci=pass"},
        {"author": "qa", "body": "gate:qa=pass"},
        {"author": "operations", "body": "gate:backup=pass"},
        {"author": "operations", "body": "gate:rollback=pass"},
    ]
    task_context["tool_call_id"] = "deploy-ready"
    assert runtime.pre_tool_call("terminal", deploy_args, task_context).decision == "allow"
    publish_context = dict(task_context, tool_call_id="publish-ready", comment_records=[
        {"author": "qa", "body": "gate:review=pass\ngate:qa=pass"},
    ])
    assert runtime.pre_tool_call("terminal", {"command": "publish product launch"}, publish_context).decision == "allow"


def test_ordinary_implementation_and_review_are_not_pre_gated(runtime, task_context):
    # These actions create the artifacts later consumed by CI/review/backup
    # gates. Requiring those gates here would deadlock the lifecycle.
    for index, task_type in enumerate(("code", "review", "ops")):
        context = dict(
            task_context,
            task_body=f"task_type: {task_type}",
            tool_call_id=f"ordinary-{index}",
            comment_records=[],
        )
        decision = runtime.pre_tool_call(
            "write_file",
            {"path": f"src/change-{task_type}.txt", "content": "bounded"},
            context,
        )
        assert (decision.decision, decision.rule_id) == ("allow", "scoped_state_change")


def test_protected_transitions_remain_fail_closed_for_review_tasks(runtime, task_context):
    review_context = dict(
        task_context,
        task_body="task_type: review",
        profile="qa",
        assignee="qa",
        tool_call_id="review-cannot-merge",
        comment_records=[],
    )
    merge = runtime.pre_tool_call("terminal", {"command": "git push origin main"}, review_context)
    assert (merge.decision, merge.rule_id) == ("deny", "evidence_gate_missing")

    review_context["tool_call_id"] = "review-cannot-deploy"
    deploy = runtime.pre_tool_call("terminal", {"command": "deploy production"}, review_context)
    assert (deploy.decision, deploy.rule_id) == ("deny", "evidence_gate_missing")


def test_workers_cannot_forge_role_gates(runtime, task_context):
    forged_cli = runtime.pre_tool_call(
        "terminal", {"command": "hermes kanban comment t_x gate:review=pass --author qa"}, task_context
    )
    assert (forged_cli.decision, forged_cli.rule_id) == ("deny", "gate_forgery")
    forged_tool = runtime.pre_tool_call("kanban_comment", {"text": "gate:review=pass"}, task_context)
    assert (forged_tool.decision, forged_tool.rule_id) == ("deny", "gate_forgery")
    qa_context = dict(task_context, profile="qa", assignee="tech", tool_call_id="qa-gate")
    valid = runtime.pre_tool_call("kanban_comment", {"text": "gate:review=pass"}, qa_context)
    assert valid.decision == "allow"


def test_negated_gate_text_does_not_satisfy_gate(runtime, task_context):
    task_context["comment_records"] = [
        {"author": "tech", "body": "gate:ci=pass NOT achieved"},
        {"author": "qa", "body": "expected gate:review=pass but regressions remain"},
        {"author": "operations", "body": "gate:rollback=pass"},
    ]
    decision = runtime.pre_tool_call("terminal", {"command": "git push origin main"}, task_context)
    assert (decision.decision, decision.rule_id) == ("deny", "evidence_gate_missing")


def test_financial_mandate_requires_gates_capability_and_limits(runtime, task_context, monkeypatch):
    args = {"command": "pay experiment amount_rub=5000 capability_id=ads-card"}
    task_context["comment_records"] = [
        {"author": "finance", "body": "gate:finance=pass"},
        {"author": "company", "body": "decision:company=go"},
    ]
    missing_cap = runtime.pre_tool_call("terminal", args, task_context)
    assert (missing_cap.decision, missing_cap.rule_id) == ("approval_required", "new_paid_capability_or_payment_rail")
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    assert runtime.store.grant_capability("ads-card", "recruiter-radar", "payment", "ads-only", "user")
    task_context["tool_call_id"] = "spend-1"
    allowed = runtime.pre_tool_call("terminal", args, task_context)
    assert allowed.decision == "allow"
    runtime.post_tool_call("terminal", args, task_context, success=True)
    assert runtime.store.monthly_spend("recruiter-radar", __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m")) == 5000
    over = {"command": "pay experiment amount_rub=11000 capability_id=ads-card"}
    task_context["tool_call_id"] = "spend-over"
    decision = runtime.pre_tool_call("terminal", over, task_context)
    assert (decision.decision, decision.rule_id) == ("approval_required", "financial_over_budget")


def test_monetary_cost_is_not_fake_zero(runtime, task_context):
    snapshot = runtime.budget_snapshot(task_context, "code")
    assert snapshot["monetary_cost"] == {"status": "unavailable", "amount": None, "currency": None}
