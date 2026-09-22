"""Regression test for v1.2.29 head-binding deadlock hotfix.
Складывает tech в tests/ ветки hotfix; QA прогоняет на точном head.

Ловит дефект v1.2.12 C1: missing_gates() читает context["head"], но kanban_context.py
никогда не заполняет "head" => expected_head всегда пуст => fail-closed => ВСЕ
evidence-gated категории непроходимы для воркеров независимо от корректных маркеров.

Тест ПАДАЕТ на v1.2.24..v1.2.28 (до hotfix) и ПРОХОДИТ после.
"""
import pytest

# fixture `runtime` берётся из conftest плагина (FleetPolicyRuntime с живым config).
# Локального override НЕ нужно: прежний runtime(plugin_runtime) shadow-ил conftest
# и падал на сборе — плагин-фикстуры не имеют публичного API `plugin_runtime`.


H = "2cbba7c763deabaf4e2c4e602017caa941a522f2"


def _records(head=H, with_go=True, go_head=None):
    gh = go_head if go_head is not None else head
    recs = [
        {"author": "qa", "body": f"gate:ci=pass\nhead={head} task_type: ops"},
        {"author": "qa", "body": f"gate:qa=pass\nhead={head} task_type: ops"},
        {"author": "operations", "body": f"gate:backup=pass\nhead={head} task_type: ops"},
        {"author": "operations", "body": f"gate:rollback=pass\nhead={head} task_type: ops"},
    ]
    if with_go:
        recs.append({"author": "company", "body": f"decision:company=go\nhead={gh} task_type: ops"})
    return recs


def _ctx(recs):
    return {"comment_records": recs, "assignee": "company", "task_body": "task_type: ops"}


def test_deploy_gate_passes_without_external_head(runtime):
    """PRIMARY regression: маркеры + go на одном head, context БЕЗ 'head' => гейт проходит."""
    assert runtime.missing_gates("deploy_external_runtime", _ctx(_records())) == []


def test_foreign_head_go_fails_closed(runtime):
    """Security: decision:company=go на чужом head => expected_head чужой => fail-closed."""
    recs = _records(go_head="ffffffffffffffffffffffffffffffffffffffff")
    assert runtime.missing_gates("deploy_external_runtime", _ctx(recs)) == ["ci", "qa", "backup", "rollback"]


def test_unbound_marker_fails_closed(runtime):
    """Security: gate PASS без head-привязки => fail-closed."""
    recs = _records()
    recs[0] = {"author": "qa", "body": "gate:ci=pass\ntask_type: ops"}  # no head
    assert runtime.missing_gates("deploy_external_runtime", _ctx(recs)) == ["ci"]


def test_no_go_anchor_fails_closed(runtime):
    """Security: нет decision:company=go => expected_head пуст => fail-closed."""
    recs = _records(with_go=False)
    assert runtime.missing_gates("deploy_external_runtime", _ctx(recs)) == ["ci", "qa", "backup", "rollback"]


def test_explicit_context_head_match_passes(runtime):
    """Back-compat: explicit context['head'] совпадает с маркерами => pass."""
    ctx = _ctx(_records()); ctx["head"] = H
    assert runtime.missing_gates("deploy_external_runtime", ctx) == []


def test_explicit_context_head_mismatch_fails(runtime):
    """Back-compat: explicit context['head'] не совпадает => fail-closed (context wins)."""
    ctx = _ctx(_records()); ctx["head"] = "abcdef0123456789"
    assert runtime.missing_gates("deploy_external_runtime", ctx) == ["ci", "qa", "backup", "rollback"]


def test_later_no_go_overrides(runtime):
    """Security: более поздний decision:company=no-go переопределяет все PASS."""
    recs = _records() + [{"author": "company", "body": f"decision:company=no-go\nhead={H} task_type: ops"}]
    assert runtime.missing_gates("deploy_external_runtime", _ctx(recs)) == ["ci", "qa", "backup", "rollback"]


def test_all_gated_categories_satisfiable(runtime):
    """Blast-radius guard: КАЖДАЯ evidence-gated категория удовлетворима при корректных маркерах
    своего набора (no external head)."""
    full = _records() + [
        {"author": "qa", "body": f"gate:review=pass\nhead={H} task_type: ops"},
        {"author": "operations", "body": f"gate:scope=pass\nhead={H} task_type: ops"},
        {"author": "finance", "body": f"gate:finance=pass\nhead={H} task_type: ops"},
    ]
    ctx = _ctx(full)
    for cat in runtime.EVIDENCE_GATED_CATEGORIES:
        assert runtime.missing_gates(cat, ctx) == [], f"{cat} должен быть удовлетворим"
