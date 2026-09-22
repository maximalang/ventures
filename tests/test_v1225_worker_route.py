"""v1.2.25: deny с маршрутом who=worker НЕ паркует карту.

Канон 17.09 «deny = пауза, не стоп»: worker-исправимые классы
(evidence_gate_missing, same_failure_loop, identical_call_loop,
worker_code_execution) возвращают блок вызова с маршрутом, но карта
остаётся running — воркер продолжает в этом же ране. company/owner-классы
паркуют карту через _project с CONTINUATION-контрактом.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from fleet_policy.storage import PolicyStore


def _load_plugin(name: str):
    module_path = Path(__file__).parents[1] / "integrations" / "hermes" / "fleet-policy-plugin" / "__init__.py"
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fake_decision_payload(rule_id: str, remediation: dict | None) -> dict:
    payload = {
        "decision": "deny", "rule_id": rule_id, "reason": "test",
        "task_id": "t_v1225a", "project": "fleet-ops", "profile": "tech",
        "action": "terminal", "target": "git", "args_hash": "abc123",
        "timestamp": "2026-09-21T22:00:00Z", "budget_snapshot": {},
        "pattern_category": rule_id, "call_index": 1, "deny_nonce": None,
    }
    if remediation:
        payload["remediation"] = remediation
    return payload


def _wire(module, monkeypatch, tmp_path):
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    runtime = module.runtime()
    monkeypatch.setattr(runtime, "store", store)
    monkeypatch.setattr(module, "_RUNTIME", runtime)
    calls = []
    monkeypatch.setattr(
        module._PROJECTOR, "comment_and_block",
        lambda board, task_id, message, *, block: calls.append((board, task_id, message, block)) or {"block": 0},
    )
    return runtime, store, calls


def test_worker_route_denies_block_call_without_parking_card(tmp_path, monkeypatch):
    module = _load_plugin("fp_plugin_worker_route")
    runtime, store, calls = _wire(module, monkeypatch, tmp_path)

    worker_classes = ["evidence_gate_missing", "same_failure_loop", "identical_call_loop", "worker_code_execution"]
    for rule_id in worker_classes:
        from fleet_policy.models import remediation_for
        rem = remediation_for(rule_id)
        assert rem and rem["who"] == "worker", f"{rule_id} must be a worker route"
        payload = _fake_decision_payload(rule_id, rem)
        # имитируем решение рантайма: pre_tool_call возвращает deny
        class _D:
            decision = "deny"
            def as_dict(self_inner):
                return dict(payload)
        monkeypatch.setattr(runtime, "pre_tool_call", lambda *a, **k: _D())
        monkeypatch.setenv("HERMES_KANBAN_BOARD", "fleet-ops")
        result = module.pre_tool_call(tool_name="terminal", args={"command": "git push origin main"})
        assert result["action"] == "block"
        assert "next_step=" in result["message"]
        assert "[continues: worker]" in result["message"]
    # ни одна worker-остановка не спроецировала block на карту
    assert calls == []


def test_company_route_denies_still_park_card_with_continuation(tmp_path, monkeypatch):
    module = _load_plugin("fp_plugin_company_route")
    runtime, store, calls = _wire(module, monkeypatch, tmp_path)

    from fleet_policy.models import remediation_for
    rule_id = "missing_or_unknown_task_type"
    rem = remediation_for(rule_id)
    assert rem and rem["who"] == "company"
    payload = _fake_decision_payload(rule_id, rem)
    class _D:
        decision = "deny"
        def as_dict(self_inner):
            return dict(payload)
    monkeypatch.setattr(runtime, "pre_tool_call", lambda *a, **k: _D())
    monkeypatch.setenv("HERMES_KANBAN_BOARD", "fleet-ops")
    result = module.pre_tool_call(tool_name="terminal", args={"command": "git push origin main"})
    assert result["action"] == "block"
    assert len(calls) == 1
    assert calls[0][0] == "fleet-ops" and calls[0][1] == "t_v1225a" and calls[0][3] is True
    assert "next_step=" in calls[0][2]


def test_message_and_continuation_format():
    module = _load_plugin("fp_plugin_message_fmt")
    payload = _fake_decision_payload("evidence_gate_missing", {"how": "собери evidence", "who": "worker"})
    msg = module._message(payload)
    assert msg.startswith("FLEET POLICY BLOCKED [evidence_gate_missing]")
    assert "next_step=собери evidence [continues: worker]" in msg
    assert module._continuation(payload) == "CONTINUATION[who=worker]: собери evidence"
    # без remediation — сообщения без next_step, continuation None
    bare = _fake_decision_payload("unknown_rule", None)
    assert "next_step" not in module._message(bare)
    assert module._continuation(bare) is None


def test_owner_route_secret_denies_park_card(tmp_path, monkeypatch):
    module = _load_plugin("fp_plugin_owner_route")
    runtime, store, calls = _wire(module, monkeypatch, tmp_path)
    from fleet_policy.models import remediation_for
    rem = remediation_for("secret_read_or_write")
    assert rem and rem["who"] == "owner"
    payload = _fake_decision_payload("secret_read_or_write", rem)
    class _D:
        decision = "deny"
        def as_dict(self_inner):
            return dict(payload)
    monkeypatch.setattr(runtime, "pre_tool_call", lambda *a, **k: _D())
    monkeypatch.setenv("HERMES_KANBAN_BOARD", "fleet-ops")
    result = module.pre_tool_call(tool_name="read_file", args={"path": "." + "env"})
    assert result["action"] == "block"
    assert len(calls) == 1
