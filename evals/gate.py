"""Scorecard aggregation and regression gate for Company OS evals.

Gate rules (frozen by card t_b8a7c165 / owner decision 07.09.2026):
1. Mean over benchmark scenarios (all 5 rubrics) >= 3.5.
2. No rubric mean (benchmark scenarios) fell more than 10% vs baseline.
3. Canary detection: spoiled brief mean <= 2.5 AND its evidence_grounding
   is at least 1.0 point below its benchmark twin's.
4. Total judge token usage <= configured budget.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from evals.judge import RUBRIC_IDS

KIND_BENCHMARK = "benchmark"
KIND_REFERENCE = "reference"
KIND_CANARY = "canary"
VALID_KINDS = (KIND_BENCHMARK, KIND_REFERENCE, KIND_CANARY)


@dataclass
class ScenarioResult:
    scenario_id: str
    kind: str
    scores: dict[str, int]
    reasoning: str = ""
    twin_of: str = ""

    @property
    def mean(self) -> float:
        vals = [self.scores[r] for r in RUBRIC_IDS]
        return sum(vals) / len(vals)


@dataclass
class Check:
    name: str
    passed: bool
    detail: str


@dataclass
class GateReport:
    passed: bool
    checks: list[Check] = field(default_factory=list)
    benchmark_mean: float | None = None
    rubric_means: dict[str, float] = field(default_factory=dict)
    scenario_means: dict[str, float] = field(default_factory=dict)


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def aggregate(results: list[ScenarioResult]) -> tuple[float | None, dict[str, float], dict[str, float]]:
    """Return (benchmark_mean, rubric_means over benchmark, per-scenario means)."""
    bench = [r for r in results if r.kind == KIND_BENCHMARK]
    bench_mean = mean([s for r in bench for s in r.scores.values()]) if bench else None
    rubric_means: dict[str, float] = {}
    for rid in RUBRIC_IDS:
        vals = [float(r.scores[rid]) for r in bench]
        rubric_means[rid] = mean(vals)
    scenario_means = {r.scenario_id: round(r.mean, 4) for r in results}
    return bench_mean, rubric_means, scenario_means


def evaluate_gate(
    results: list[ScenarioResult],
    baseline: dict[str, Any] | None,
    *,
    benchmark_min_mean: float = 3.5,
    rubric_max_relative_drop: float = 0.10,
    canary_max_mean: float = 2.5,
    canary_min_evidence_drop_vs_twin: float = 1.0,
    total_tokens: int = 0,
    max_total_tokens: int = 200_000,
) -> GateReport:
    checks: list[Check] = []
    bench_mean, rubric_means, scenario_means = aggregate(results)

    # 1. mean floor over benchmark scenarios
    if bench_mean is None:
        checks.append(Check("mean_floor", False, "no benchmark scenarios in corpus"))
    else:
        ok = bench_mean >= benchmark_min_mean
        checks.append(
            Check(
                "mean_floor",
                ok,
                f"benchmark mean {bench_mean:.3f} vs floor {benchmark_min_mean}",
            )
        )

    # 2. per-rubric regression vs baseline
    if baseline is not None:
        base_rubrics = baseline.get("rubric_means") or {}
        for rid in RUBRIC_IDS:
            base_val = base_rubrics.get(rid)
            if base_val is None:
                checks.append(Check(f"rubric_regression:{rid}", False, "rubric missing from baseline"))
                continue
            run_val = rubric_means.get(rid, 0.0)
            if base_val <= 0:
                checks.append(Check(f"rubric_regression:{rid}", run_val >= 0, f"baseline value invalid: {base_val}"))
                continue
            drop = (base_val - run_val) / base_val
            ok = drop <= rubric_max_relative_drop
            checks.append(
                Check(
                    f"rubric_regression:{rid}",
                    ok,
                    f"run {run_val:.3f} vs baseline {base_val:.3f} (drop {drop:.1%}, limit {rubric_max_relative_drop:.0%})",
                )
            )

    # 3. canary detection
    canaries = [r for r in results if r.kind == KIND_CANARY]
    if not canaries:
        checks.append(Check("canary_detection", False, "no canary scenario in corpus"))
    by_id = {r.scenario_id: r for r in results}
    for can in canaries:
        ok_mean = can.mean <= canary_max_mean
        checks.append(
            Check(
                f"canary_mean:{can.scenario_id}",
                ok_mean,
                f"canary mean {can.mean:.3f} vs max {canary_max_mean}",
            )
        )
        twin = by_id.get(can.twin_of) if can.twin_of else None
        if twin is None:
            checks.append(
                Check(
                    f"canary_evidence_drop:{can.scenario_id}",
                    False,
                    f"twin scenario {can.twin_of!r} not found in results",
                )
            )
        else:
            drop = twin.scores["evidence_grounding"] - can.scores["evidence_grounding"]
            ok_drop = drop >= canary_min_evidence_drop_vs_twin
            checks.append(
                Check(
                    f"canary_evidence_drop:{can.scenario_id}",
                    ok_drop,
                    f"evidence_grounding twin {twin.scores['evidence_grounding']} - canary {can.scores['evidence_grounding']} = {drop} (min {canary_min_evidence_drop_vs_twin})",
                )
            )

    # 4. budget
    ok_budget = total_tokens <= max_total_tokens
    checks.append(
        Check("budget", ok_budget, f"total tokens {total_tokens} vs budget {max_total_tokens}")
    )

    passed = all(c.passed for c in checks)
    return GateReport(
        passed=passed,
        checks=checks,
        benchmark_mean=bench_mean,
        rubric_means=rubric_means,
        scenario_means=scenario_means,
    )


def baseline_from_results(
    results: list[ScenarioResult],
    *,
    judge_model: str,
    judge_prompt_sha256: str,
    rubric_version: int,
    recorded_at: str,
    budget_used: dict[str, int] | None = None,
) -> dict[str, Any]:
    bench_mean, rubric_means, scenario_means = aggregate(results)
    return {
        "schema_version": 1,
        "recorded_at": recorded_at,
        "judge_model": judge_model,
        "judge_prompt_sha256": judge_prompt_sha256,
        "rubric_version": rubric_version,
        "benchmark_mean": round(bench_mean, 4) if bench_mean is not None else None,
        "rubric_means": {k: round(v, 4) for k, v in rubric_means.items()},
        "scenario_means": scenario_means,
        "scenarios": {
            r.scenario_id: {"kind": r.kind, "scores": r.scores, "mean": round(r.mean, 4)}
            for r in results
        },
        "budget_used": budget_used or {},
    }


def load_baseline(path: str | Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("schema_version") != 1:
        raise ValueError(f"unsupported baseline schema_version: {data.get('schema_version')!r}")
    return data


def format_scorecard(results: list[ScenarioResult], report: GateReport | None = None) -> str:
    lines = []
    header = f"{'scenario':44s} {'kind':10s} " + " ".join(f"{r[:9]:>9s}" for r in RUBRIC_IDS) + f" {'mean':>6s}"
    lines.append(header)
    lines.append("-" * len(header))
    for res in results:
        row = f"{res.scenario_id:44s} {res.kind:10s} " + " ".join(f"{res.scores[r]:>9d}" for r in RUBRIC_IDS) + f" {res.mean:>6.2f}"
        lines.append(row)
    if report is not None:
        lines.append("")
        if report.benchmark_mean is not None:
            lines.append(f"benchmark mean: {report.benchmark_mean:.3f}")
        for rid in RUBRIC_IDS:
            lines.append(f"rubric mean {rid:22s}: {report.rubric_means.get(rid, 0.0):.3f}")
        lines.append("")
        for check in report.checks:
            mark = "PASS" if check.passed else "FAIL"
            lines.append(f"[{mark}] {check.name}: {check.detail}")
        lines.append("")
        lines.append("GATE: " + ("PASS" if report.passed else "FAIL"))
    return "\n".join(lines)
