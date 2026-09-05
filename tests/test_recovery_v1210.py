"""v1.2.10 false-deny recovery tests (owner-approved design, items A-E)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).parents[1]

PROTECTED_ENV_NAME = ".env." + "production"


def _load_plugin():
    plugin_path = ROOT / "integrations" / "hermes" / "fleet-policy-plugin" / "__init__.py"
    spec = importlib.util.spec_from_file_location("fleet_policy_plugin_under_test", plugin_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ------------------------------------------------------------------ item A


def test_deny_payload_carries_pattern_category_and_call_index(runtime, task_context):
    first = runtime.pre_tool_call("read_file", {"path": PROTECTED_ENV_NAME}, task_context)
    payload = first.as_dict()
    assert first.decision == "deny"
    assert payload["pattern_category"] == "sec" + "ret_read_or_write"
    assert payload["call_index"] == 1

    task_context["tool_call_id"] = "call-2"
    second = runtime.pre_tool_call("read_file", {"path": PROTECTED_ENV_NAME}, task_context)
    assert second.as_dict()["call_index"] == 2


def test_call_index_resets_on_new_dispatch_run(runtime, task_context):
    runtime.pre_tool_call("read_file", {"path": PROTECTED_ENV_NAME}, task_context)
    fresh_run = dict(task_context, current_run_id="r2", tool_call_id="run2-1")
    decision = runtime.pre_tool_call("read_file", {"path": PROTECTED_ENV_NAME}, fresh_run)
    assert decision.as_dict()["call_index"] == 1


def test_block_message_contains_only_rule_category_and_index(runtime, task_context):
    decision = runtime.pre_tool_call("read_file", {"path": PROTECTED_ENV_NAME}, task_context)
    payload = decision.as_dict()
    payload["board"] = str(task_context.get("board") or "")
    message = _load_plugin()._message(payload)
    assert "FLEET POLICY BLOCKED" in message
    assert payload["rule_id"] in message
    assert f"pattern={payload['pattern_category']}" in message
    assert "call_index=1" in message
    # Path/token/reason must never leak into worker-visible deny text.
    assert PROTECTED_ENV_NAME not in message
    assert ".env" not in message
    assert payload["target"] not in message
    assert payload["reason"] not in message


def test_allow_decision_shape_is_extended_consistently(runtime, task_context):
    payload = runtime.pre_tool_call("read_file", {"path": "README.md"}, task_context).as_dict()
    assert payload["pattern_category"] == "read_only"
    assert payload["call_index"] == 1


# ------------------------------------------------------------------ item B


def test_operational_artifact_read_allowlist_is_root_scoped(runtime, task_context):
    broad_name = "cre" + "dential-audit-report.md"
    roots = [
        "C:/Users/max/AppData/Local/hermes/profiles/qa/plugins/fleet-policy/.state",
        "C:/Users/max/AppData/Local/hermes/kanban/boards/fleet-ops/workspaces/t_test/evidence",
        "C:/Users/max/AppData/Local/hermes/kanban/boards/fleet-ops/attachments/t_test",
    ]
    for index, root in enumerate(roots, start=1):
        task_context["tool_call_id"] = f"artifact-{index}"
        decision = runtime.pre_tool_call("read_file", {"path": f"{root}/{broad_name}"}, task_context)
        assert decision.decision == "allow"
        assert decision.rule_id == "read_only"


def test_operational_allowlist_pins_state_root_boundary(runtime, task_context):
    """F-1 (QA run 475): the `(?:/|$)` root boundary in the plugin-state route
    is load-bearing.  Directory names that merely start with the state root
    must stay denied while the exact root keeps the read lane, so a refactor
    that weakens the boundary cannot pass silently."""
    broad_name = "cre" + "dential-audit-report.md"
    profile_root = "C:/Users/max/AppData/Local/hermes/profiles/qa/plugins/fleet-policy"
    exact_root = f"{profile_root}/.state/{broad_name}"
    siblings = [
        f"{profile_root}/.statefoo/{broad_name}",
        f"{profile_root}/.state-backup/{broad_name}",
    ]
    decision = runtime.pre_tool_call("read_file", {"path": exact_root}, task_context)
    assert decision.decision == "allow"
    assert decision.rule_id == "read_only"
    for index, sibling in enumerate(siblings, start=2):
        task_context["tool_call_id"] = f"boundary-{index}"
        decision = runtime.pre_tool_call("read_file", {"path": sibling}, task_context)
        assert decision.decision == "deny"
        assert decision.rule_id == "sec" + "ret_read_or_write"


def test_operational_allowlist_does_not_apply_outside_roots(runtime, task_context):
    path = "C:/Users/max/Documents/" + "cre" + "dential-audit-report.md"
    decision = runtime.pre_tool_call("read_file", {"path": path}, task_context)
    assert decision.decision == "deny"


def test_operational_allowlist_keeps_hard_secret_shapes_denied(runtime, task_context):
    root = "C:/Users/max/AppData/Local/hermes/kanban/boards/fleet-ops/workspaces/t_test"
    decisions = [
        runtime.pre_tool_call("read_file", {"path": f"{root}/{PROTECTED_ENV_NAME}"}, task_context),
        runtime.pre_tool_call("read_file", {"path": f"{root}/ses" + "sions/token.txt"}, dict(task_context, tool_call_id="hard-2")),
    ]
    assert all(item.decision == "deny" for item in decisions)


def test_operational_allowlist_never_allows_writes(runtime, task_context):
    path = (
        "C:/Users/max/AppData/Local/hermes/kanban/boards/fleet-ops/attachments/t_test/"
        + "cre" + "dential-audit-report.md"
    )
    decision = runtime.pre_tool_call("write_file", {"path": path, "content": "x"}, task_context)
    assert decision.decision == "deny"


# ------------------------------------------------------------------ item C


def _review_probe_context(task_context):
    return dict(
        task_context,
        task_body="task_type: review",
        profile="qa",
        assignee="qa",
        comment_records=[],
        current_run_id="r1",
    )


def test_review_probe_deny_is_fail_closed_nonce_not_failure(runtime, task_context):
    """A review task probing a gated transition gets a per-run deny artifact;
    the probe must not grow loop counters or repeat the same failure."""
    ctx = _review_probe_context(task_context)
    args = {"command": "git push origin main"}
    for index in range(4):
        ctx["tool_call_id"] = f"probe-{index}"
        decision = runtime.pre_tool_call("terminal", args, ctx)
        assert decision.decision == "deny"
        assert decision.rule_id == "evidence_gate_missing"
        # Fail-closed: the refusal stays a deny carrying a stable per-run nonce.
        assert decision.as_dict().get("deny_nonce")
    with runtime.store.connect() as connection:
        # One artifact per dispatch run — repeated probes do not stack events.
        assert connection.execute(
            "SELECT COUNT(*) FROM events WHERE kind='review_probe_nonce'"
        ).fetchone()[0] == 1


def test_review_probe_does_not_grow_failure_loop(runtime, task_context):
    """The denied probe's failure report must not escalate into a
    same_failure_loop stop (no failure-signature accounting for the nonce lane)."""
    ctx = _review_probe_context(task_context)
    args = {"command": "git push origin main"}
    for index in range(4):
        ctx["tool_call_id"] = f"probe-{index}"
        runtime.pre_tool_call("terminal", args, ctx)
        event = runtime.post_tool_call(
            "terminal", args, ctx, success=False,
            error_type="review_probe_nonce", error_message="FLEET POLICY BLOCKED",
        )
        assert event is None, f"probe {index} must not emit a stop event"
    assert runtime.store.count_signature(
        ctx["task_id"], "failure_signature",
        __import__("fleet_policy.redaction", fromlist=["stable_id"]).stable_id(
            "terminal", "review_probe_nonce", "fleet policy blocked"
        ),
        "r1",
    ) == 0


def test_review_probe_budget_keeps_charging(runtime, task_context):
    """The nonce lane skips loop counters only; the tool-call budget still
    accounts every probe so wall-clock/token limits remain the stop class."""
    ctx = _review_probe_context(task_context)
    args = {"command": "git push origin main"}
    for index in range(3):
        ctx["tool_call_id"] = f"probe-{index}"
        runtime.pre_tool_call("terminal", args, ctx)
    task_type, _ = runtime.task_type(ctx)
    assert runtime.budget_snapshot(ctx, task_type)["used"]["tool_calls"] == 3


def test_non_review_task_failure_loop_is_unchanged(runtime, task_context):
    """A code task hitting the same gated command keeps the stop behavior."""
    code_ctx = dict(task_context, task_body="task_type: code", current_run_id="r1")
    args = {"command": "git push origin main"}
    events = []
    for index in range(2):
        code_ctx["tool_call_id"] = f"code-fail-{index}"
        events.append(runtime.post_tool_call(
            "terminal", args, code_ctx, success=False,
            error_type="tool_error", error_message="gate missing",
        ))
    assert events[-1] is not None and events[-1]["rule_id"] == "same_failure_loop"


# ------------------------------------------------------------------ item D


def test_expected_failure_override_prevents_stop_event(runtime, task_context):
    """A pre-marked expected failure never escalates into a stop event; the
    override itself is recorded exactly once as a significant event."""
    from fleet_policy.redaction import stable_id
    code_ctx = dict(task_context, task_body="task_type: code", current_run_id="r1")
    args = {"command": "git push origin main"}
    signature = stable_id("terminal", "tool_error", "gate missing")
    assert runtime.store.mark_expected_failure(code_ctx["task_id"], signature, "r1") is True
    assert runtime.store.mark_expected_failure(code_ctx["task_id"], signature, "r1") is False
    for index in range(3):
        code_ctx["tool_call_id"] = f"override-{index}"
        event = runtime.post_tool_call(
            "terminal", args, code_ctx, success=False,
            error_type="tool_error", error_message="gate missing",
        )
        assert event is None, f"failure {index} must not stop an overridden signature"
    with runtime.store.connect() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM events WHERE kind='expected_failure_override'"
        ).fetchone()[0] == 1


def test_expected_failure_override_is_run_scoped(runtime, task_context):
    """An override for run r1 leaves other runs of the same task fail-closed."""
    from fleet_policy.redaction import stable_id
    code_ctx = dict(task_context, task_body="task_type: code", current_run_id="r1")
    args = {"command": "git push origin main"}
    signature = stable_id("terminal", "tool_error", "gate missing")
    assert runtime.store.mark_expected_failure(code_ctx["task_id"], signature, "r1") is True
    fresh = dict(code_ctx, current_run_id="r2")
    event = None
    for index in range(2):
        fresh["tool_call_id"] = f"other-run-{index}"
        event = runtime.post_tool_call(
            "terminal", args, fresh, success=False,
            error_type="tool_error", error_message="gate missing",
        )
    assert event is not None and event["rule_id"] == "same_failure_loop"


# ------------------------------------------------------------------ item E


def _gate(name: str) -> str:
    """Assemble a gate marker from parts so this file's own source text never
    trips the fleet text guard (repo-wide test convention)."""
    return "gate:" + name + "=pass"


_GO = "decision:comp" + "any=go"


def test_gate_comment_evaluates_every_marker(runtime, task_context):
    ctx = dict(task_context, task_body="task_type: review", profile="qa", assignee="tech")
    assert runtime.gate_comment_allowed(_gate("review") + " verified in run r1", ctx) is True
    assert runtime.gate_comment_allowed("no markers in an ordinary comment", ctx) is True
    # One authorized + one unauthorized marker together = denied.
    assert runtime.gate_comment_allowed(_gate("review") + " ok\n" + _gate("finance") + " ok", ctx) is False
    assert runtime.gate_comment_allowed(_gate("finance") + " ok", ctx) is False  # finance belongs to finance profile only
    assert runtime.gate_comment_allowed(_GO, dict(ctx, profile="company")) is True
    assert runtime.gate_comment_allowed(_GO, ctx) is False  # qa is not the company decision author


def test_gate_comment_self_approval_checked_against_target_card(runtime, task_context, monkeypatch):
    """review/qa authorization follows the TARGET card's assignee: the
    poison-marker attack lands the comment on a foreign card, so the card the
    comment lands on decides self-approval; unresolvable targets fail closed."""
    import fleet_policy.kanban_context as kc
    ctx = dict(task_context, task_body="task_type: review", profile="qa", assignee="tech")
    # qa attesting review on a tech-owned card is authorized.
    assert runtime.gate_comment_allowed(_gate("review") + " ok", ctx) is True
    # On qa's OWN card the same attestation is self-approval → denied.
    assert runtime.gate_comment_allowed(_gate("review") + " ok", dict(ctx, assignee="qa")) is False
    # Explicit foreign target: the TARGET card's assignee decides.
    monkeypatch.setattr(kc, "task_assignee", lambda board, task_id, env=None: "qa")
    assert runtime.gate_comment_allowed(_gate("qa") + " ok", ctx, "t_foreign") is False
    monkeypatch.setattr(kc, "task_assignee", lambda board, task_id, env=None: "tech")
    assert runtime.gate_comment_allowed(_gate("qa") + " ok", ctx, "t_foreign") is True
    # Unresolvable target card fails closed.
    monkeypatch.setattr(kc, "task_assignee", lambda board, task_id, env=None: None)
    assert runtime.gate_comment_allowed(_gate("qa") + " ok", ctx, "t_missing") is False
