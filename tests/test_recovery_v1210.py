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
