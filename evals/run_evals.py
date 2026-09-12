#!/usr/bin/env python3
"""run_evals.py — live LLM-judge harness for Company OS text-output evals.

Runs the frozen rubric judge (fleet rail of the qa profile) over YAML
scenarios, prints a scorecard, and applies the regression gate:
  mean(benchmark scenarios, all rubrics) >= 3.5
  AND no rubric mean dropped >10% vs evals/baseline.json
  AND canary (spoiled brief) is detected as bad.

Usage (from repo root):
  python evals/run_evals.py                          # live run + gate
  python evals/run_evals.py --record-baseline        # re-record baseline.json
  python evals/run_evals.py --judge-model glm-5.2    # alternate rail model

Requires the fleet rail key in HERMES_CUSTOM_CUSTOM_API_KEY (qa-profile
rail; never the text author's own profile). Hermetic unit tests for the
parsing/aggregation/gate logic live in tests/test_evals_harness.py and run
in CI without network or keys.

Pattern adapted (not ported) from SenteLabsAI/OpenExecutive (Apache-2.0,
head b071101) per owner decision 07.09.2026 — attribution in evals/README.md.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import yaml  # noqa: E402

from evals.gate import (  # noqa: E402
    KIND_BENCHMARK,
    KIND_CANARY,
    KIND_REFERENCE,
    VALID_KINDS,
    ScenarioResult,
    baseline_from_results,
    evaluate_gate,
    format_scorecard,
    load_baseline,
)
from evals.judge import (  # noqa: E402
    JUDGE_PROMPT_SHA256,
    JudgeError,
    JudgeUsage,
    judge_brief,
)


def load_scenarios(path: Path) -> tuple[list[dict], dict]:
    with open(path, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    scenarios = doc.get("scenarios") or []
    if not scenarios:
        raise SystemExit(f"no scenarios in {path}")
    ids = set()
    for sc in scenarios:
        sid = sc.get("id")
        if not sid:
            raise SystemExit(f"scenario without id: {sc!r}")
        if sid in ids:
            raise SystemExit(f"duplicate scenario id: {sid}")
        ids.add(sid)
        kind = sc.get("kind")
        if kind not in VALID_KINDS:
            raise SystemExit(f"scenario {sid}: invalid kind {kind!r} (expected one of {VALID_KINDS})")
        if not (sc.get("brief") or "").strip():
            raise SystemExit(f"scenario {sid}: empty brief")
        if kind == KIND_CANARY and not sc.get("twin_of"):
            raise SystemExit(f"canary scenario {sid}: twin_of is required")
    # twin references must resolve
    for sc in scenarios:
        twin = sc.get("twin_of")
        if twin and twin not in ids:
            raise SystemExit(f"scenario {sc['id']}: twin_of {twin!r} not found")
    return scenarios, doc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Company OS eval harness v1")
    parser.add_argument("--scenarios", default=str(REPO_ROOT / "evals" / "scenarios.yaml"))
    parser.add_argument("--rubrics", default=str(REPO_ROOT / "evals" / "rubrics.yaml"))
    parser.add_argument("--baseline", default=str(REPO_ROOT / "evals" / "baseline.json"))
    parser.add_argument("--judge-model", default=None, help="override rail judge model")
    parser.add_argument("--record-baseline", action="store_true", help="write baseline.json from this run")
    parser.add_argument("--no-gate", action="store_true", help="skip gate verdict (informational run)")
    args = parser.parse_args(argv)

    with open(args.rubrics, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    judge_cfg = cfg["judge"]
    gate_cfg = cfg.get("gate") or {}
    budget_cfg = cfg.get("budget") or {}

    frozen_sha = judge_cfg.get("prompt_sha256")
    if frozen_sha and frozen_sha != JUDGE_PROMPT_SHA256:
        print(
            f"FATAL: judge prompt drift — rubrics.yaml pins {frozen_sha} "
            f"but judge.py computes {JUDGE_PROMPT_SHA256}. Bump rubric_version "
            "and re-record the baseline consciously.",
            file=sys.stderr,
        )
        return 2

    model = args.judge_model or judge_cfg.get("model")
    base_url = judge_cfg.get("base_url")
    key_env = judge_cfg.get("key_env")
    max_tokens = int(budget_cfg.get("max_total_tokens", 200_000))

    scenarios, _doc = load_scenarios(Path(args.scenarios))
    baseline_path = Path(args.baseline)
    baseline = load_baseline(baseline_path) if baseline_path.exists() and not args.record_baseline else None

    usage = JudgeUsage()
    results: list[ScenarioResult] = []
    for sc in scenarios:
        sid = sc["id"]
        print(f"judging {sid} ({sc['kind']}) ...", flush=True)
        try:
            verdict = judge_brief(
                sc["brief"],
                model=model,
                base_url=base_url,
                key_env=key_env,
                usage=usage,
                budget_tokens=max_tokens,
            )
        except JudgeError as exc:
            print(f"FATAL: judge failed on {sid}: {exc}", file=sys.stderr)
            return 3
        results.append(
            ScenarioResult(
                scenario_id=sid,
                kind=sc["kind"],
                scores=verdict.scores,
                reasoning=verdict.reasoning,
                twin_of=sc.get("twin_of", ""),
            )
        )
        print(f"  scores={verdict.scores} usage={usage.as_dict()}", flush=True)

    report = evaluate_gate(
        results,
        baseline,
        benchmark_min_mean=float(gate_cfg.get("benchmark_min_mean", 3.5)),
        rubric_max_relative_drop=float(gate_cfg.get("rubric_max_relative_drop", 0.10)),
        canary_max_mean=float(gate_cfg.get("canary_max_mean", 2.5)),
        canary_min_evidence_drop_vs_twin=float(gate_cfg.get("canary_min_evidence_drop_vs_twin", 1.0)),
        total_tokens=usage.total_tokens,
        max_total_tokens=max_tokens,
    )

    print()
    print(format_scorecard(results, report))
    print(f"\ntoken usage: {usage.as_dict()} (budget {max_tokens})")

    if args.record_baseline:
        payload = baseline_from_results(
            results,
            judge_model=model,
            judge_prompt_sha256=JUDGE_PROMPT_SHA256,
            rubric_version=int(cfg.get("rubric_version", 1)),
            recorded_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            budget_used=usage.as_dict(),
        )
        baseline_path.write_text(
            __import__("json").dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"baseline recorded -> {baseline_path}")

    if args.no_gate:
        return 0
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
