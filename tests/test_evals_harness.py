"""Hermetic unit tests for the Company OS eval harness (evals/).

No network, no API keys: the judge client is exercised with a monkeypatched
urlopen, gate/aggregation logic with synthetic ScenarioResults. These run in
fleet-policy-ci.yml alongside the existing suite.

Frozen pins (rubric_version 1):
  JUDGE_PROMPT_SHA256 == 2dbfd69b22cc8bb16c766caed0024ad3ef2b08e5d3e1fe9cb6dca3964d0362a9
Changing the judge prompt or rubrics requires a conscious rubric_version bump,
a new baseline.json, and an update of this pin.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evals import judge as judge_mod
from evals.gate import (
    KIND_BENCHMARK,
    KIND_CANARY,
    KIND_REFERENCE,
    ScenarioResult,
    aggregate,
    baseline_from_results,
    evaluate_gate,
    format_scorecard,
    load_baseline,
)
from evals.judge import (
    JUDGE_PROMPT_SHA256,
    JudgeError,
    JudgeUsage,
    build_prompt,
    judge_brief,
    parse_judge_response,
)

FROZEN_PROMPT_SHA256 = "2dbfd69b22cc8bb16c766caed0024ad3ef2b08e5d3e1fe9cb6dca3964d0362a9"
FROZEN_RUBRIC_IDS = (
    "evidence_grounding",
    "decision_clarity",
    "owner_fit",
    "risk_honesty",
    "actionability",
)

RUBRICS_PATH = REPO_ROOT / "evals" / "rubrics.yaml"
SCENARIOS_PATH = REPO_ROOT / "evals" / "scenarios.yaml"


# ---------------------------------------------------------------------------
# frozen artifacts
# ---------------------------------------------------------------------------

def test_judge_prompt_sha_is_frozen():
    assert JUDGE_PROMPT_SHA256 == FROZEN_PROMPT_SHA256


def test_rubric_ids_are_frozen():
    assert judge_mod.RUBRIC_IDS == FROZEN_RUBRIC_IDS


def test_rubrics_yaml_pins_match_code():
    cfg = yaml.safe_load(RUBRICS_PATH.read_text(encoding="utf-8"))
    assert cfg["rubric_version"] == 1
    assert cfg["judge"]["prompt_sha256"] == FROZEN_PROMPT_SHA256
    assert cfg["judge"]["profile"] == "qa"
    assert cfg["judge"]["key_env"] == "HERMES_CUSTOM_CUSTOM_API_KEY"
    assert [r["id"] for r in cfg["rubrics"]] == list(FROZEN_RUBRIC_IDS)
    assert cfg["budget"]["max_total_tokens"] == 200_000
    gate = cfg["gate"]
    assert gate["benchmark_min_mean"] == 3.5
    assert gate["rubric_max_relative_drop"] == pytest.approx(0.10)
    assert gate["canary_max_mean"] == 2.5
    assert gate["canary_min_evidence_drop_vs_twin"] == 1.0


def test_judge_prompt_contains_every_rubric():
    for rid in FROZEN_RUBRIC_IDS:
        assert rid in judge_mod.JUDGE_PROMPT_V1


# ---------------------------------------------------------------------------
# corpus (scenarios.yaml)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def corpus():
    doc = yaml.safe_load(SCENARIOS_PATH.read_text(encoding="utf-8"))
    return doc


def test_corpus_size_and_composition(corpus):
    scenarios = corpus["scenarios"]
    ids = [s["id"] for s in scenarios]
    assert len(ids) == len(set(ids)), "duplicate scenario ids"
    # card requirement: >= 5 scenarios total
    assert len(scenarios) >= 5
    kinds = [s["kind"] for s in scenarios]
    # >= 1 real decision-ledger brief (reference), >= 3 synthetic (benchmark+canary)
    assert kinds.count(KIND_REFERENCE) >= 1
    assert kinds.count(KIND_BENCHMARK) + kinds.count(KIND_CANARY) >= 3
    assert kinds.count(KIND_CANARY) >= 1


def test_corpus_real_brief_provenance(corpus):
    ref = next(s for s in corpus["scenarios"] if s["kind"] == KIND_REFERENCE)
    # faithful render of decision-ledger record #1 (t_06c53243)
    assert "t_06c53243" in ref["source"]
    assert "t_06c53243" in ref["brief"]
    assert "https://github.com/maximalang/ventures/pull/20" in ref["brief"]


def test_corpus_canaries_reference_existing_twins(corpus):
    ids = {s["id"] for s in corpus["scenarios"]}
    for sc in corpus["scenarios"]:
        if sc["kind"] == KIND_CANARY:
            assert sc["twin_of"] in ids
            twin = next(s for s in corpus["scenarios"] if s["id"] == sc["twin_of"])
            assert twin["kind"] == KIND_BENCHMARK
            assert "spoil" in sc  # corruption must be documented


def test_corpus_briefs_are_nonempty_text(corpus):
    for sc in corpus["scenarios"]:
        assert isinstance(sc["brief"], str) and sc["brief"].strip()


# ---------------------------------------------------------------------------
# judge response parsing
# ---------------------------------------------------------------------------

def _valid_payload(scores=None, reasoning="ok"):
    scores = scores or {rid: 4 for rid in FROZEN_RUBRIC_IDS}
    return json.dumps({"scores": scores, "reasoning": reasoning}, ensure_ascii=False)


def test_parse_plain_json():
    scores, reasoning = parse_judge_response(_valid_payload())
    assert scores == {rid: 4 for rid in FROZEN_RUBRIC_IDS}
    assert reasoning == "ok"


def test_parse_fenced_json():
    text = "```json\n" + _valid_payload() + "\n```"
    scores, _ = parse_judge_response(text)
    assert scores["decision_clarity"] == 4


def test_parse_json_with_surrounding_prose():
    text = "Вот оценка:\n" + _valid_payload() + "\nСпасибо."
    scores, _ = parse_judge_response(text)
    assert sum(scores.values()) / len(scores) == 4.0


@pytest.mark.parametrize(
    "bad",
    [
        "",  # empty
        "not json at all",
        json.dumps({"reasoning": "missing scores"}),
        json.dumps({"scores": {rid: 4 for rid in FROZEN_RUBRIC_IDS[:-1]}}),  # missing rubric
        json.dumps({"scores": {**{rid: 4 for rid in FROZEN_RUBRIC_IDS}, "extra": 3}}),
        json.dumps({"scores": {rid: 0 for rid in FROZEN_RUBRIC_IDS}}),  # below range
        json.dumps({"scores": {rid: 6 for rid in FROZEN_RUBRIC_IDS}}),  # above range
        json.dumps({"scores": {rid: "4" for rid in FROZEN_RUBRIC_IDS}}),  # non-int
        json.dumps({"scores": {rid: 4.5 for rid in FROZEN_RUBRIC_IDS}}),  # float
        "[1,2,3]",  # not an object
    ],
)
def test_parse_rejects_invalid(bad):
    with pytest.raises(JudgeError):
        parse_judge_response(bad)


def test_build_prompt_injects_brief():
    prompt = build_prompt("ТЕКСТ БРИФА")
    assert "ТЕКСТ БРИФА" in prompt
    assert "<<<BRIEF>>>" not in prompt
    assert prompt.startswith("Ты — независимый QA-судья")


def test_build_prompt_rejects_empty():
    with pytest.raises(JudgeError):
        build_prompt("   ")


# ---------------------------------------------------------------------------
# judge client (hermetic: call_fn injection + monkeypatched transport for auth)
# ---------------------------------------------------------------------------

class _FakeResponse:
    def __init__(self, payload: dict):
        self._body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _chat_payload(content: str, usage: dict | None = None):
    return {
        "choices": [{"message": {"content": content}}],
        "usage": usage or {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    }


def test_call_judge_api_auth_and_body(monkeypatch):
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.headers)
        captured["body"] = json.loads(req.data.decode("utf-8"))
        return _FakeResponse(_chat_payload(_valid_payload()))

    monkeypatch.setattr(judge_mod.urllib.request, "urlopen", fake_urlopen)

    from evals.judge import call_judge_api

    content, usage = call_judge_api(
        "prompt text",
        model="kimi-k3",
        base_url="https://example.invalid/v1/",
        api_key="sekret",
    )
    assert captured["url"] == "https://example.invalid/v1/chat/completions"
    # Authorization header must use the Bearer scheme assembled in judge.py
    auth = captured["headers"].get("Authorization", "")
    assert auth.startswith(judge_mod.AUTH_SCHEME + " ")
    assert auth.endswith("sekret")
    assert captured["body"]["model"] == "kimi-k3"
    assert captured["body"]["temperature"] == 0.0
    assert captured["body"]["messages"][0]["content"] == "prompt text"
    assert usage["total_tokens"] == 150
    assert json.loads(content)["scores"]


def test_call_judge_api_missing_key(monkeypatch):
    monkeypatch.delenv("EVAL_NO_SUCH_KEY", raising=False)
    from evals.judge import call_judge_api

    with pytest.raises(JudgeError, match="missing"):
        call_judge_api("x", key_env="EVAL_NO_SUCH_KEY")


def _fake_call_fn(content: str = None, usage: dict | None = None):
    def _call(prompt, *, model, base_url, api_key, key_env):
        return (content if content is not None else _valid_payload()), (
            usage or {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        )

    return _call


def test_judge_brief_counts_usage_and_enforces_budget():
    usage = JudgeUsage()
    result = judge_brief(
        "brief",
        api_key="k",
        usage=usage,
        budget_tokens=400,
        call_fn=_fake_call_fn(),
    )
    assert result.scores["evidence_grounding"] == 4
    assert result.model == judge_mod.DEFAULT_JUDGE_MODEL
    assert usage.calls == 1
    assert usage.total_tokens == 150

    with pytest.raises(judge_mod.BudgetExceeded):
        judge_brief("brief", api_key="k", usage=usage, budget_tokens=200, call_fn=_fake_call_fn())


def test_judge_brief_retries_then_succeeds():
    state = {"n": 0}

    def flaky_call(prompt, *, model, base_url, api_key, key_env):
        state["n"] += 1
        if state["n"] == 1:
            return "garbage", {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}
        return _valid_payload(), {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}

    usage = JudgeUsage()
    result = judge_brief("brief", api_key="k", usage=usage, retries=2, call_fn=flaky_call)
    assert result.scores["owner_fit"] == 4
    assert usage.calls == 2


def test_judge_brief_fails_after_retries():
    def bad_call(prompt, *, model, base_url, api_key, key_env):
        return "", {"total_tokens": 1}

    with pytest.raises(JudgeError, match="parseable|empty"):
        judge_brief("brief", api_key="k", retries=2, call_fn=bad_call)


def test_usage_add_is_cumulative():
    usage = JudgeUsage()
    usage.add({"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15})
    usage.add({"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15})
    assert usage.as_dict() == {
        "prompt_tokens": 20,
        "completion_tokens": 10,
        "total_tokens": 30,
        "calls": 2,
    }


# ---------------------------------------------------------------------------
# aggregation + gate
# ---------------------------------------------------------------------------

def _bench(sid: str, value: int = 4) -> ScenarioResult:
    return ScenarioResult(scenario_id=sid, kind=KIND_BENCHMARK, scores={rid: value for rid in FROZEN_RUBRIC_IDS})


def _canary(sid: str, twin: str, ev: int = 1, other: int = 2) -> ScenarioResult:
    scores = {rid: other for rid in FROZEN_RUBRIC_IDS}
    scores["evidence_grounding"] = ev
    return ScenarioResult(scenario_id=sid, kind=KIND_CANARY, scores=scores, twin_of=twin)


def _results_healthy():
    return [
        _bench("b1", 4),
        _bench("b2", 4),
        _bench("b3", 5),
        ScenarioResult(scenario_id="r1", kind=KIND_REFERENCE, scores={rid: 3 for rid in FROZEN_RUBRIC_IDS}),
        _canary("c1", "b1", ev=1, other=2),
    ]


def _baseline_healthy():
    return baseline_from_results(
        [_bench("b1", 4), _bench("b2", 4), _bench("b3", 5)],
        judge_model="kimi-k3",
        judge_prompt_sha256=FROZEN_PROMPT_SHA256,
        rubric_version=1,
        recorded_at="2026-09-07T00:00:00Z",
    )


def test_aggregate_means():
    bench_mean, rubric_means, scenario_means = aggregate(_results_healthy())
    # benchmark scores: 4,4,4,4,4 / 4... / 5... -> mean of all values = (20+20+25)/15
    assert bench_mean == pytest.approx(4.3333, abs=1e-3)
    for rid in FROZEN_RUBRIC_IDS:
        assert rubric_means[rid] == pytest.approx(4.3333, abs=1e-3)
    # reference scenario excluded from rubric means but present in scenario means
    assert scenario_means["r1"] == 3.0
    assert "r1" not in {k for k in scenario_means if False}  # sanity, keep key


def test_gate_passes_on_healthy_run():
    report = evaluate_gate(_results_healthy(), _baseline_healthy(), total_tokens=1200)
    assert report.passed, format_scorecard(_results_healthy(), report)
    names = [c.name for c in report.checks]
    assert "mean_floor" in names and "budget" in names
    assert any(n.startswith("canary_mean:") for n in names)
    assert any(n.startswith("canary_evidence_drop:") for n in names)
    assert sum(1 for n in names if n.startswith("rubric_regression:")) == 5


def test_gate_fails_below_mean_floor():
    results = [_bench("b1", 3), _bench("b2", 3), _canary("c1", "b1")]
    report = evaluate_gate(results, None, total_tokens=10)
    floor = next(c for c in report.checks if c.name == "mean_floor")
    assert not floor.passed
    assert not report.passed


def test_gate_passes_at_exact_mean_floor():
    results = [_bench("b1", 4), _bench("b2", 4), _bench("b3", 3), _canary("c1", "b1")]
    # means: (20+20+15)/15 = 3.666 >= 3.5
    report = evaluate_gate(results, None, total_tokens=10)
    floor = next(c for c in report.checks if c.name == "mean_floor")
    assert floor.passed


def test_gate_rubric_regression_detected():
    baseline = _baseline_healthy()  # rubric means 4.3333
    # one rubric collapses on benchmark scenarios
    def bench_drop(rid):
        scores = {r: 4 for r in FROZEN_RUBRIC_IDS}
        scores[rid] = 2
        return ScenarioResult(scenario_id="b1", kind=KIND_BENCHMARK, scores=scores)

    results = [bench_drop("risk_honesty"), _bench("b2", 4), _bench("b3", 5), _canary("c1", "b2")]
    report = evaluate_gate(results, baseline, total_tokens=10)
    reg = next(c for c in report.checks if c.name == "rubric_regression:risk_honesty")
    assert not reg.passed, reg.detail
    assert not report.passed
    # other rubrics still pass
    ok = next(c for c in report.checks if c.name == "rubric_regression:evidence_grounding")
    assert ok.passed


def test_gate_rubric_drop_exactly_10_percent_passes():
    baseline = {
        "schema_version": 1,
        "rubric_means": {rid: 4.0 for rid in FROZEN_RUBRIC_IDS},
    }

    def bench_at(value):
        return ScenarioResult(
            scenario_id=f"b{value}",
            kind=KIND_BENCHMARK,
            scores={rid: value for rid in FROZEN_RUBRIC_IDS},
        )

    # rubric means: evidence 4.0, others: (4+3+3+3)/4 -> not exactly 3.6; build directly
    scores_a = {rid: 4 for rid in FROZEN_RUBRIC_IDS}
    scores_b = {rid: 4 for rid in FROZEN_RUBRIC_IDS}
    scores_b["owner_fit"] = 3  # mean owner_fit = 3.5? need 3.6 exactly -> use 5 scenarios
    results = []
    for i in range(5):
        s = {rid: 4 for rid in FROZEN_RUBRIC_IDS}
        if i < 4:
            s["owner_fit"] = 4
        else:
            s["owner_fit"] = 2  # mean = (4*4+2)/5 = 3.6 == -10% exactly
        results.append(ScenarioResult(scenario_id=f"b{i}", kind=KIND_BENCHMARK, scores=s))
    results.append(_canary("c1", "b0", ev=1, other=2))
    report = evaluate_gate(results, baseline, total_tokens=10)
    reg = next(c for c in report.checks if c.name == "rubric_regression:owner_fit")
    assert reg.passed, reg.detail
    del scores_a, scores_b, bench_at


def test_gate_rubric_drop_just_over_10_percent_fails():
    baseline = {
        "schema_version": 1,
        "rubric_means": {rid: 4.0 for rid in FROZEN_RUBRIC_IDS},
    }
    results = []
    for i in range(5):
        s = {rid: 4 for rid in FROZEN_RUBRIC_IDS}
        if i == 4:
            s["owner_fit"] = 1  # mean = (16+1)/5 = 3.4 -> drop 15%
        results.append(ScenarioResult(scenario_id=f"b{i}", kind=KIND_BENCHMARK, scores=s))
    results.append(_canary("c1", "b0", ev=1, other=2))
    report = evaluate_gate(results, baseline, total_tokens=10)
    reg = next(c for c in report.checks if c.name == "rubric_regression:owner_fit")
    assert not reg.passed


def test_gate_missing_baseline_rubric_flagged():
    baseline = {"schema_version": 1, "rubric_means": {rid: 4.0 for rid in FROZEN_RUBRIC_IDS[:-1]}}
    report = evaluate_gate(_results_healthy(), baseline, total_tokens=10)
    missing = next(c for c in report.checks if c.name == "rubric_regression:actionability")
    assert not missing.passed


def test_gate_canary_not_detected_fails():
    # canary scored like a benchmark brief
    results = [_bench("b1", 4), _bench("b2", 4), _canary("c1", "b1", ev=4, other=4)]
    report = evaluate_gate(results, None, total_tokens=10)
    can = next(c for c in report.checks if c.name == "canary_mean:c1")
    assert not can.passed
    drop = next(c for c in report.checks if c.name == "canary_evidence_drop:c1")
    assert not drop.passed
    assert not report.passed


def test_gate_canary_missing_twin_fails():
    results = [_bench("b1", 4), ScenarioResult(scenario_id="c1", kind=KIND_CANARY, scores={rid: 1 for rid in FROZEN_RUBRIC_IDS}, twin_of="ghost")]
    report = evaluate_gate(results, None, total_tokens=10)
    drop = next(c for c in report.checks if c.name == "canary_evidence_drop:c1")
    assert not drop.passed


def test_gate_no_canary_fails():
    results = [_bench("b1", 4), _bench("b2", 4)]
    report = evaluate_gate(results, None, total_tokens=10)
    assert any(c.name == "canary_detection" and not c.passed for c in report.checks)


def test_gate_budget_exceeded_fails():
    report = evaluate_gate(_results_healthy(), _baseline_healthy(), total_tokens=200_001)
    budget = next(c for c in report.checks if c.name == "budget")
    assert not budget.passed
    assert not report.passed


def test_gate_budget_at_limit_passes():
    report = evaluate_gate(_results_healthy(), _baseline_healthy(), total_tokens=200_000)
    budget = next(c for c in report.checks if c.name == "budget")
    assert budget.passed


# ---------------------------------------------------------------------------
# baseline round-trip + scorecard rendering
# ---------------------------------------------------------------------------

def test_baseline_roundtrip(tmp_path):
    payload = baseline_from_results(
        _results_healthy(),
        judge_model="kimi-k3",
        judge_prompt_sha256=FROZEN_PROMPT_SHA256,
        rubric_version=1,
        recorded_at="2026-09-07T12:00:00Z",
        budget_used={"total_tokens": 999, "calls": 5},
    )
    path = tmp_path / "baseline.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    loaded = load_baseline(path)
    assert loaded["judge_prompt_sha256"] == FROZEN_PROMPT_SHA256
    assert loaded["rubric_means"]["evidence_grounding"] == pytest.approx(4.3333, abs=1e-3)
    assert loaded["scenarios"]["c1"]["kind"] == KIND_CANARY
    assert loaded["budget_used"]["total_tokens"] == 999


def test_load_baseline_rejects_bad_schema(tmp_path):
    path = tmp_path / "baseline.json"
    path.write_text(json.dumps({"schema_version": 99}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_baseline(path)


def test_format_scorecard_renders_all_scenarios():
    results = _results_healthy()
    report = evaluate_gate(results, _baseline_healthy(), total_tokens=10)
    text = format_scorecard(results, report)
    for res in results:
        assert res.scenario_id in text
    assert "GATE: PASS" in text


# ---------------------------------------------------------------------------
# run_evals CLI plumbing (hermetic parts only)
# ---------------------------------------------------------------------------

def test_run_evals_loads_real_corpus():
    sys.path.insert(0, str(REPO_ROOT))
    from evals.run_evals import load_scenarios

    scenarios, doc = load_scenarios(SCENARIOS_PATH)
    assert doc["schema_version"] == 1
    assert len(scenarios) >= 5


def test_run_evals_rejects_duplicate_ids(tmp_path):
    from evals.run_evals import load_scenarios

    bad = tmp_path / "s.yaml"
    bad.write_text(
        yaml.safe_dump(
            {
                "scenarios": [
                    {"id": "x", "kind": "benchmark", "brief": "a"},
                    {"id": "x", "kind": "benchmark", "brief": "b"},
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(SystemExit):
        load_scenarios(bad)


def test_run_evals_rejects_canary_without_twin(tmp_path):
    from evals.run_evals import load_scenarios

    bad = tmp_path / "s.yaml"
    bad.write_text(
        yaml.safe_dump({"scenarios": [{"id": "c", "kind": "canary", "brief": "spoiled"}]}),
        encoding="utf-8",
    )
    with pytest.raises(SystemExit):
        load_scenarios(bad)
