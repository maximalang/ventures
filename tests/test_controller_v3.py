"""v3 acceptance battery for the deterministic next-bet controller.

Re-derived run 367 from the exact v3 artifacts:
- ECONOMICS_SCORING_CONTRACT_V3.md (t_a92701e0, econ-score/v3)
- DEMAND_METRIC_SOURCE_CONTRACT_V3.md (t_dbb4235b, v3.0)
- QA contract_review_v3=pass (t_7ee1d606)

Arithmetic pins below come from the QA report (§3): f(90d)=0.125 exactly,
f(20d)=0.629961, RR example (12000+0)*0.55*0.629961-10000 = -5842.26 RUB,
negative-EV example 2000*0.8*1.0-8000 = -6400.00 RUB.
"""

from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from fleet_policy import controller
from fleet_policy.controller import (
    ControllerEngine,
    ControllerInputError,
    load_live_snapshot,
    load_snapshot_file,
    reduce,
    task_from_row,
)

FIXTURE = Path(__file__).parent / "fixtures" / "controller_shadow_v3.json"
EVALUATED_AT = "2026-09-02T18:00:00+03:00"
REF_TS = "2026-08-28T18:00:00+03:00"  # 5 days before EVALUATED_AT
GAP_METRIC = {"value": None, "observed_at": None, "evidence_gap": "metric_definition_source_value_unprovided"}
FRESH_METRIC = {"value": 120.0, "observed_at": "2026-09-01T12:00:00+03:00", "evidence_gap": None}


def freshness(age_days: float) -> float:
    return max(0.125, 2.0 ** (-(age_days / 30.0)))


def gate_task(task_id: str = "t_gate", status: str = "todo", board: str = "seo-site", **over) -> dict:
    task = {
        "task_id": task_id,
        "title": f"gate {task_id}",
        "status": status,
        "priority": 900,
        "assignee": "research",
        "revenue_critical": True,
        "revenue_project": "seo-site" if board == "seo-site" else "recruiter-radar",
    }
    task.update(over)
    return task


def candidate(task_id: str = "t_bet", board: str = "seo-site", profit: float = 30000.0, cost: float = 2000.0,
              ref_ts: str = REF_TS, **over) -> dict:
    base = {
        "source_task_id": task_id,
        "project": "seo-site" if board == "seo-site" else "recruiter-radar",
        "board": board,
        "metric_id": "successful_organic_calculations_28d" if board == "seo-site" else "accepted_evidence_backed_leads_28d",
        "mechanism_id": f"mech-{task_id}",
        "work_class": "metric",
        "confidence_0_1": 0.8,
        "cash_cost_rub": cost,
        "capacity_cost_rub": 0.0,
        "total_cost_rub": cost,
        "expected_profit_rub_30d": profit,
        "avoided_loss_rub_30d": None,
        "evidence_refs": [{"ref": "finance:funnel-v1", "observed_at": ref_ts, "author": "finance", "authority_rank": 1}],
        "owner": "tech",
        "squad": ["tech", "qa"],
        "hypothesis": "bet lifts the canonical primary metric",
        "expected_impact": "+5 metric points in 30 days",
        "kill_criterion": {
            "metric": "successful_organic_calculations_28d" if board == "seo-site" else "accepted_evidence_backed_leads_28d",
            "window_days": 30,
            "adverse_threshold_relative": 0.05,
        },
        "rollback": "revert the slice",
    }
    base.update(over)
    return base


def snap(rr_tasks=(), seo_tasks=(), portfolio_tasks=(), rr_candidates=(), seo_candidates=(),
         rr_metric=None, seo_metric=None, budget=None, economics_gap=True,
         evaluated_at=EVALUATED_AT, collectors=None) -> dict:
    economics_state = {
        "evidence_gap": bool(economics_gap),
        "evidence_gap_reasons": ["no finance-verified expected_profit_rub_30d"] if economics_gap else [],
    }
    snapshot = {
        "evaluated_at": evaluated_at,
        "boards": {
            "portfolio": {"service": True, "tasks": list(portfolio_tasks), "candidates": []},
            "rr-team": {
                "project": "recruiter-radar",
                "canonical": True,
                "primary_metric_id": "accepted_evidence_backed_leads_28d",
                "metric": copy.deepcopy(rr_metric if rr_metric is not None else GAP_METRIC),
                "tasks": list(rr_tasks),
                "candidates": list(rr_candidates),
            },
            "seo-site": {
                "project": "seo-site",
                "canonical": True,
                "primary_metric_id": "successful_organic_calculations_28d",
                "metric": copy.deepcopy(seo_metric if seo_metric is not None else GAP_METRIC),
                "tasks": list(seo_tasks),
                "candidates": list(seo_candidates),
            },
        },
        "budget": budget or {},
        "economics_state": economics_state,
    }
    if collectors is not None:
        snapshot["collectors"] = collectors
    return snapshot


def executable_snap(**over) -> dict:
    """A snapshot whose single candidate is fully executable (positive EV,
    fresh metric, ok economics, complete execution fields, within budget)."""
    kwargs = {
        "seo_tasks": [gate_task()],
        "seo_candidates": [candidate()],
        "rr_metric": copy.deepcopy(FRESH_METRIC),
        "seo_metric": copy.deepcopy(FRESH_METRIC),
        "economics_gap": False,
    }
    kwargs.update(over)
    return snap(**kwargs)


# ---------------------------------------------------------------------- states


def test_busy_fleet_is_no_action():
    decision = reduce(snap(seo_tasks=[gate_task("t_run", status="running"), gate_task()]))
    assert decision["state"] == "RUNNING"
    assert decision["decision_type"] == "no_action"
    assert decision["reason"] == "fleet_busy_running"
    assert decision["success"] is False
    assert decision["mutation_ops"] == []


def test_ready_queue_is_no_action():
    decision = reduce(snap(seo_tasks=[gate_task("t_ready", status="ready"), gate_task()]))
    assert decision["state"] == "READY_QUEUE"
    assert decision["decision_type"] == "no_action"
    assert decision["reason"] == "ready_work_exists"


def test_idle_without_actionable_gates_is_no_action():
    decision = reduce(snap(seo_tasks=[gate_task("t_done", status="done"), gate_task("t_old", status="superseded")]))
    assert decision["state"] == "IDLE_NO_GATES"
    assert decision["decision_type"] == "no_action"
    assert decision["reason"] == "no_actionable_revenue_gate"


def test_blocked_gate_is_never_actionable_and_never_success():
    decision = reduce(snap(seo_tasks=[gate_task("t_blocked", status="blocked")]))
    assert decision["state"] == "IDLE_NO_GATES"
    assert decision["decision_type"] == "no_action"
    assert decision["counts"]["blocked_revenue_gates"] == 1
    assert decision["success"] is False


# --------------------------------------------------------- acceptance fixture


def test_fixture_actionable_idle_collects_evidence():
    decision = reduce(load_snapshot_file(str(FIXTURE)))
    assert decision["state"] == "ACTIONABLE_IDLE"
    assert decision["decision_type"] == "collect_evidence"
    assert decision["execution_eligible"] is False
    assert decision["formula_version"] == "econ-score/v3"
    cand = decision["candidate"]
    assert cand["idempotency_key"] == decision["decision_id"]
    assert cand["collector_owner"] == "finance"
    assert cand["collector_squad"] == ["finance", "research"]
    assert cand["freshness_target_days"] == 30
    assert cand["score"]["value"] is None  # no invented RUB
    missing = " | ".join(cand["missing_fields"])
    assert "accepted_evidence_backed_leads_28d" in missing
    assert "successful_organic_calculations_28d" in missing
    assert cand["rollback"].startswith("No state change")
    assert cand["evidence_refs"]  # contract refs attached
    # superseded lane stays untouched: never a candidate
    assert all(row["source_task_id"] != "t_superseded_lane" for row in decision["audit"]["candidates"])
    digest = decision["digest"]
    assert digest["channel"] == "telegram"
    assert "[shadow mode]" in digest["text"]
    assert "execution_eligible=false" in digest["text"]
    assert "score_rub=" not in digest["text"]


def test_fixture_second_run_writes_zero_new_records(runtime):
    engine = ControllerEngine(runtime.store)
    snapshot = load_snapshot_file(str(FIXTURE))
    first = engine.run(snapshot, now="2026-09-02T18:00:00+03:00")
    second = engine.run(snapshot, now="2026-09-02T18:05:00+03:00")
    assert first["duplicate"] is False and second["duplicate"] is True
    assert second["decision_id"] == first["decision_id"]
    with runtime.store.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 1


# ---------------------------------------------------------------- execute_bet


def test_execute_bet_on_fully_evidenced_positive_candidate():
    decision = reduce(executable_snap())
    assert decision["decision_type"] == "execute_bet"
    assert decision["execution_eligible"] is True
    cand = decision["candidate"]
    assert cand["source_task_id"] == "t_bet"
    assert cand["owner"] == "tech" and cand["squad"] == ["tech", "qa"]
    assert cand["kill_criterion"]["adverse_threshold_relative"] == 0.05
    score = cand["score"]
    expected = 30000.0 * 0.8 * freshness(5.0) - 2000.0
    assert score["score_rub"] == pytest.approx(round(expected, 2), abs=0.01)
    assert score["formula"] == "(E + A) * confidence * freshness - total_cost_rub"
    assert score["formula_version"] == "econ-score/v3"
    assert score["oldest_age_days"] == 5.0
    assert decision["audit"]["winner_source_task_id"] == "t_bet"
    assert decision["digest"]["channel"] == "telegram"
    assert f"score_rub={score['score_rub']:g}" in decision["digest"]["text"]


def test_execute_bet_requires_fresh_metric_and_ok_economics():
    # metric gap on either board blocks execute
    decision = reduce(executable_snap(seo_metric=copy.deepcopy(GAP_METRIC)))
    assert decision["decision_type"] == "collect_evidence"
    # stale metric (40d) blocks execute
    stale = {"value": 100.0, "observed_at": "2026-07-24T18:00:00+03:00", "evidence_gap": None}
    decision = reduce(executable_snap(seo_metric=stale))
    assert decision["decision_type"] == "collect_evidence"
    assert any("fresh observation" in field for field in decision["candidate"]["missing_fields"])
    # economics evidence_gap blocks execute
    decision = reduce(executable_snap(economics_gap=True))
    assert decision["decision_type"] == "collect_evidence"


def test_qa_arithmetic_pins():
    # QA §3: (12000+0)*0.55*f(20d)-10000 = -5842.26 -> negative EV, not eligible
    cand = candidate("t_rr_neg", board="rr-team", profit=12000.0, cost=10000.0,
                     confidence_0_1=0.55, ref_ts="2026-08-13T18:00:00+03:00")  # 20d old
    decision = reduce(snap(rr_tasks=[gate_task("t_rr", board="rr-team")], rr_candidates=[cand],
                           rr_metric=copy.deepcopy(FRESH_METRIC), seo_metric=copy.deepcopy(FRESH_METRIC),
                           economics_gap=False))
    assert decision["decision_type"] == "no_action"
    assert decision["reason"] == "no_eligible_candidate"
    row = decision["audit"]["candidates"][0]
    assert row["class"] == "EXECUTABLE"  # classified, but negative score
    assert row["score_rub"] == pytest.approx(-5842.26, abs=0.01)

    # QA §3: 2000*0.8*1.0-8000 = -6400 -> negative EV, not eligible
    cand2 = candidate("t_negev", profit=2000.0, cost=8000.0, ref_ts=EVALUATED_AT)
    decision = reduce(snap(seo_tasks=[gate_task()], seo_candidates=[cand2],
                           rr_metric=copy.deepcopy(FRESH_METRIC), seo_metric=copy.deepcopy(FRESH_METRIC),
                           economics_gap=False))
    assert decision["decision_type"] == "no_action"
    assert decision["audit"]["candidates"][0]["score_rub"] == pytest.approx(-6400.0, abs=0.01)

    # QA §3: f(90d) = 0.125 exactly (floor), not yet requires_reverification
    cand3 = candidate("t_floor", profit=10000.0, cost=0.0, confidence_0_1=1.0,
                      ref_ts="2026-06-04T18:00:00+03:00")  # exactly 90d
    decision = reduce(snap(seo_tasks=[gate_task()], seo_candidates=[cand3],
                           rr_metric=copy.deepcopy(FRESH_METRIC), seo_metric=copy.deepcopy(FRESH_METRIC),
                           economics_gap=False))
    comp = decision["candidate"]["score"]
    assert comp["freshness_f"] == 0.125
    assert comp["requires_reverification"] is False
    assert comp["score_rub"] == pytest.approx(1250.0, abs=0.01)

    # beyond 90d: floor holds, requires_reverification flips on
    cand4 = candidate("t_reverify", profit=10000.0, cost=0.0, confidence_0_1=1.0,
                      ref_ts="2026-06-03T18:00:00+03:00")  # 91d
    decision = reduce(snap(seo_tasks=[gate_task()], seo_candidates=[cand4],
                           rr_metric=copy.deepcopy(FRESH_METRIC), seo_metric=copy.deepcopy(FRESH_METRIC),
                           economics_gap=False))
    comp = decision["candidate"]["score"]
    assert comp["freshness_f"] == 0.125
    assert comp["requires_reverification"] is True


# ------------------------------------------------------------- budget guards


def test_budget_guardrails_block_execution():
    over_op = candidate("t_big", cost=10001.0)
    decision = reduce(snap(seo_tasks=[gate_task()], seo_candidates=[over_op],
                           rr_metric=copy.deepcopy(FRESH_METRIC), seo_metric=copy.deepcopy(FRESH_METRIC),
                           economics_gap=False))
    row = decision["audit"]["candidates"][0]
    assert row["class"] == "BLOCKED_BUDGET" and row["reason"] == "budget_op_limit_exceeded"
    assert decision["decision_type"] == "no_action"

    monthly = candidate("t_month", cost=2000.0)
    decision = reduce(snap(seo_tasks=[gate_task()], seo_candidates=[monthly],
                           rr_metric=copy.deepcopy(FRESH_METRIC), seo_metric=copy.deepcopy(FRESH_METRIC),
                           economics_gap=False,
                           budget={"seo-site": {"month": "2026-09", "month_to_date_spend_rub": 29000.0}}))
    row = decision["audit"]["candidates"][0]
    assert row["class"] == "BLOCKED_BUDGET" and row["reason"] == "budget_month_limit_exceeded"
    limits = decision["audit"]["budget_snapshot"]["seo-site"]["limits"]
    assert limits == {"per_op_rub": 10000, "monthly_per_project_rub": 30000}


# ---------------------------------------------------------------- anti-gaming


def test_prefilled_score_components_are_rejected():
    tampered = candidate("t_tamper", score_components={"score_rub": 999999})
    decision = reduce(snap(seo_tasks=[gate_task()], seo_candidates=[tampered],
                           rr_metric=copy.deepcopy(FRESH_METRIC), seo_metric=copy.deepcopy(FRESH_METRIC),
                           economics_gap=False))
    row = decision["audit"]["candidates"][0]
    assert row["class"] == "REJECTED" and row["reason"] == "score_components_tampered"
    assert decision["decision_type"] != "execute_bet"


def test_avoided_loss_cap_and_scope():
    # A only for gate_removal/risk work
    wrong_class = candidate("t_wrong", avoided_loss_rub_30d=1000.0, total_cost_rub=2000.0)
    decision = reduce(snap(seo_tasks=[gate_task()], seo_candidates=[wrong_class],
                           rr_metric=copy.deepcopy(FRESH_METRIC), seo_metric=copy.deepcopy(FRESH_METRIC),
                           economics_gap=False))
    row = decision["audit"]["candidates"][0]
    assert row["class"] == "REJECTED" and row["reason"] == "avoided_loss_not_allowed"

    # cap = exposure x probability; exceeded -> rejected
    over_cap = candidate("t_overcap", work_class="gate_removal", profit=None, avoided_loss_rub_30d=5000.0,
                         loss_exposure_rub=4000.0, event_probability_30d=0.5)
    decision = reduce(snap(seo_tasks=[gate_task()], seo_candidates=[over_cap],
                           rr_metric=copy.deepcopy(FRESH_METRIC), seo_metric=copy.deepcopy(FRESH_METRIC),
                           economics_gap=False))
    row = decision["audit"]["candidates"][0]
    assert row["class"] == "REJECTED" and row["reason"] == "avoided_loss_cap_exceeded"

    # cap inputs missing -> evidence gap, never invented
    no_cap = candidate("t_nocap", work_class="gate_removal", profit=None, avoided_loss_rub_30d=5000.0)
    decision = reduce(snap(seo_tasks=[gate_task()], seo_candidates=[no_cap],
                           rr_metric=copy.deepcopy(FRESH_METRIC), seo_metric=copy.deepcopy(FRESH_METRIC),
                           economics_gap=False))
    row = decision["audit"]["candidates"][0]
    assert row["class"] == "EVIDENCE_GAP" and row["reason"] == "avoided_loss_cap_unproven"


def test_double_count_guard_zeroes_smaller_component():
    dup = candidate("t_dup", profit=1000.0, avoided_loss_rub_30d=1000.0, work_class="gate_removal",
                    cost=0.0, total_cost_rub=0.0, confidence_0_1=1.0, ref_ts=EVALUATED_AT,
                    loss_exposure_rub=2000.0, event_probability_30d=1.0,
                    evidence_profit_refs=["r1"], evidence_loss_refs=["r1"])
    decision = reduce(snap(seo_tasks=[gate_task()], seo_candidates=[dup],
                           rr_metric=copy.deepcopy(FRESH_METRIC), seo_metric=copy.deepcopy(FRESH_METRIC),
                           economics_gap=False))
    comp = decision["candidate"]["score"]
    assert comp["double_count_zeroed"] == "avoided_loss"  # equal -> A zeroed
    assert comp["A_effective"] == 0.0
    assert comp["score_rub"] == pytest.approx(1000.0, abs=0.01)


def test_selection_is_by_rub_score_not_roi():
    # low: small cost, huge ROI, small absolute score
    low = candidate("t_low_roi", profit=1000.0, cost=10.0, confidence_0_1=1.0, ref_ts=EVALUATED_AT)
    # high: big cost, ROI ~2, big absolute score
    high = candidate("t_high_abs", profit=20000.0, cost=9000.0, confidence_0_1=1.0, ref_ts=EVALUATED_AT)
    decision = reduce(snap(seo_tasks=[gate_task()], seo_candidates=[low, high],
                           rr_metric=copy.deepcopy(FRESH_METRIC), seo_metric=copy.deepcopy(FRESH_METRIC),
                           economics_gap=False))
    assert decision["candidate"]["source_task_id"] == "t_high_abs"
    assert decision["audit"]["winner_source_task_id"] == "t_high_abs"


def test_mechanism_dedup_keeps_freshest_oldest_ref():
    older = candidate("t_older", mechanism_id="mech-shared", profit=50000.0, ref_ts="2026-08-18T18:00:00+03:00")
    fresher = candidate("t_fresher", mechanism_id="mech-shared", profit=30000.0, ref_ts=EVALUATED_AT)
    decision = reduce(snap(seo_tasks=[gate_task()], seo_candidates=[older, fresher],
                           rr_metric=copy.deepcopy(FRESH_METRIC), seo_metric=copy.deepcopy(FRESH_METRIC),
                           economics_gap=False))
    rows = {row["source_task_id"]: row for row in decision["audit"]["candidates"]}
    assert rows["t_older"]["dedup"] == "merged_into:t_fresher"
    assert decision["candidate"]["source_task_id"] == "t_fresher"


# ------------------------------------------------------- tie-break (§4 order)


def _tie_snap(*cands) -> dict:
    return snap(seo_tasks=[gate_task()], seo_candidates=list(cands),
                rr_metric=copy.deepcopy(FRESH_METRIC), seo_metric=copy.deepcopy(FRESH_METRIC),
                economics_gap=False)


def test_tie_break_full_order_yields_exactly_one_winner():
    # 1) equal score -> min cost wins (exact floats: conf 0.5)
    a = candidate("t_a", profit=10000.0, cost=0.0, total_cost_rub=0.0, confidence_0_1=0.5, ref_ts=EVALUATED_AT)
    b = candidate("t_b", profit=12000.0, cost=1000.0, confidence_0_1=0.5, ref_ts=EVALUATED_AT)
    decision = reduce(_tie_snap(a, b))
    assert decision["decision_type"] == "execute_bet"
    assert decision["candidate"]["source_task_id"] == "t_a"

    # 2) equal score+cost -> max confidence wins
    a = candidate("t_a", profit=10000.0, cost=0.0, total_cost_rub=0.0, confidence_0_1=0.5, ref_ts=EVALUATED_AT)
    b = candidate("t_b", profit=5000.0, cost=0.0, total_cost_rub=0.0, confidence_0_1=1.0, ref_ts=EVALUATED_AT)
    decision = reduce(_tie_snap(a, b))
    assert decision["candidate"]["source_task_id"] == "t_b"

    # 3) equal score+cost+confidence -> min oldest-ref age wins
    a = candidate("t_a", profit=4000.0, cost=0.0, total_cost_rub=0.0, confidence_0_1=1.0, ref_ts=EVALUATED_AT)
    b = candidate("t_b", profit=8000.0, cost=0.0, total_cost_rub=0.0, confidence_0_1=1.0,
                  ref_ts="2026-08-03T18:00:00+03:00")  # 30d -> f=0.5 -> score 4000
    decision = reduce(_tie_snap(a, b))
    assert decision["candidate"]["source_task_id"] == "t_a"

    # 4) full tie -> lexicographic min source_task_id
    a = candidate("t_a", profit=10000.0, cost=0.0, total_cost_rub=0.0, confidence_0_1=0.5, ref_ts=EVALUATED_AT)
    b = candidate("t_b", profit=10000.0, cost=0.0, total_cost_rub=0.0, confidence_0_1=0.5, ref_ts=EVALUATED_AT)
    decision = reduce(_tie_snap(a, b))
    assert decision["candidate"]["source_task_id"] == "t_a"


# ----------------------------------------------------- collect_evidence paths


def test_missing_money_is_evidence_gap_and_collects():
    no_ev = candidate("t_nomoney", profit=None)
    decision = reduce(snap(seo_tasks=[gate_task()], seo_candidates=[no_ev],
                           rr_metric=copy.deepcopy(FRESH_METRIC), seo_metric=copy.deepcopy(FRESH_METRIC),
                           economics_gap=False))
    row = decision["audit"]["candidates"][0]
    assert row["class"] == "EVIDENCE_GAP" and row["reason"] == "unknown_ev"
    assert decision["decision_type"] == "collect_evidence"
    assert decision["execution_eligible"] is False
    assert any("t_nomoney" in field for field in decision["candidate"]["missing_fields"])


def test_incomplete_execution_fields_become_evidence_gap():
    no_rollback = candidate("t_norollback")
    del no_rollback["rollback"]
    decision = reduce(snap(seo_tasks=[gate_task()], seo_candidates=[no_rollback],
                           rr_metric=copy.deepcopy(FRESH_METRIC), seo_metric=copy.deepcopy(FRESH_METRIC),
                           economics_gap=False))
    row = decision["audit"]["candidates"][0]
    assert row["class"] == "EVIDENCE_GAP" and row["reason"] == "execution_fields_incomplete"
    assert "rollback" in row["missing_fields"]
    assert decision["decision_type"] == "collect_evidence"

    # §8: zero adverse threshold is invalid even for C=0
    zero_kill = candidate("t_zerokill", cost=0.0, total_cost_rub=0.0)
    zero_kill["kill_criterion"] = {"metric": "m", "window_days": 30, "adverse_threshold_relative": 0}
    decision = reduce(snap(seo_tasks=[gate_task()], seo_candidates=[zero_kill],
                           rr_metric=copy.deepcopy(FRESH_METRIC), seo_metric=copy.deepcopy(FRESH_METRIC),
                           economics_gap=False))
    row = decision["audit"]["candidates"][0]
    assert row["class"] == "EVIDENCE_GAP"
    assert any("kill_criterion" in field for field in row["missing_fields"])


def test_unknown_project_metric_and_authority_rejected_or_gap():
    wrong_metric = candidate("t_wm", metric_id="search-utility-leads")
    decision = reduce(snap(seo_tasks=[gate_task()], seo_candidates=[wrong_metric]))
    row = decision["audit"]["candidates"][0]
    assert row["class"] == "REJECTED" and row["reason"] == "unknown_metric"

    low_authority = candidate("t_la")
    low_authority["evidence_refs"][0]["authority_rank"] = 7
    decision = reduce(snap(seo_tasks=[gate_task()], seo_candidates=[low_authority],
                           rr_metric=copy.deepcopy(FRESH_METRIC), seo_metric=copy.deepcopy(FRESH_METRIC),
                           economics_gap=False))
    row = decision["audit"]["candidates"][0]
    assert row["class"] == "EVIDENCE_GAP" and row["reason"] == "insufficient_authority"

    future_ref = candidate("t_future", ref_ts="2026-09-03T18:00:00+03:00")
    decision = reduce(snap(seo_tasks=[gate_task()], seo_candidates=[future_ref]))
    row = decision["audit"]["candidates"][0]
    assert row["class"] == "REJECTED" and row["reason"] == "evidence_ref_future_dated"


# ------------------------------------------------- determinism & idempotency


def test_decision_is_order_independent_and_content_hashed():
    tasks = [gate_task("t_a"), gate_task("t_b", status="triage"), gate_task("t_done", status="done")]
    cands = [candidate("t_c1", profit=20000.0), candidate("t_c2", profit=25000.0)]
    base = snap(seo_tasks=tasks, seo_candidates=cands)
    first = reduce(base)
    shuffled_tasks = list(tasks)
    shuffled_cands = list(cands)
    random.Random(7).shuffle(shuffled_tasks)
    random.Random(11).shuffle(shuffled_cands)
    second = reduce(snap(seo_tasks=shuffled_tasks, seo_candidates=shuffled_cands))
    assert first == second
    assert first["decision_id"] == second["decision_id"]
    assert first["idempotency_key"] == first["decision_id"]
    assert first["decision_id"].startswith("nbc2-")
    assert first["audit"]["inputs_hash"] == second["audit"]["inputs_hash"]
    # different evaluated_at -> different content -> different decision id
    third = reduce(snap(seo_tasks=tasks, seo_candidates=cands, evaluated_at="2026-09-02T19:00:00+03:00"))
    assert third["decision_id"] != first["decision_id"]


def test_engine_repeat_writes_zero_new_records(runtime):
    engine = ControllerEngine(runtime.store)
    snapshot = executable_snap()
    first = engine.run(snapshot, now="2026-09-02T18:00:00+03:00")
    with runtime.store.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 1
    second = engine.run(snapshot, now="2026-09-02T18:05:00+03:00")
    assert second["duplicate"] is True and first["duplicate"] is False
    assert {**second, "duplicate": False} == first
    with runtime.store.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 1
        row = connection.execute("SELECT kind, significant, task_id FROM events").fetchone()
    assert row["kind"] == "controller_decision"
    assert row["significant"] == 0 and row["task_id"] is None


def test_different_snapshots_get_different_ids(runtime):
    engine = ControllerEngine(runtime.store)
    first = engine.run(snap(seo_tasks=[gate_task("t_a")]))
    second = engine.run(snap(seo_tasks=[gate_task("t_b")]))
    assert first["decision_id"] != second["decision_id"]
    with runtime.store.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 2


# ------------------------------------------------------------------ fail-closed


def test_fail_closed_on_invalid_input():
    with pytest.raises(ControllerInputError):
        reduce({})  # evaluated_at mandatory (collector stamp)
    with pytest.raises(ControllerInputError):
        reduce(snap(seo_metric={"value": 5.0, "observed_at": None, "evidence_gap": None}))
    with pytest.raises(ControllerInputError):
        reduce(snap(seo_metric={"value": None, "observed_at": None, "evidence_gap": None}))
    bad_board = snap()
    bad_board["boards"]["seo-site"]["project"] = "recruiter-radar"
    with pytest.raises(ControllerInputError):
        reduce(bad_board)
    bad_metric = snap()
    bad_metric["boards"]["seo-site"]["primary_metric_id"] = "rr-leads"
    with pytest.raises(ControllerInputError):
        reduce(bad_metric)
    with pytest.raises(ControllerInputError):
        reduce({"evaluated_at": EVALUATED_AT, "boards": {"rr-legacy": {"tasks": []}}})
    with pytest.raises(ControllerInputError):
        reduce(snap(budget={"search-utility": {"month_to_date_spend_rub": 1}}))
    with pytest.raises(ControllerInputError):
        reduce(snap(budget={"seo-site": {"month_to_date_spend_rub": -1}}))
    with pytest.raises(ControllerInputError):
        reduce("not a snapshot")
    with pytest.raises(ControllerInputError):
        load_snapshot_file(str(FIXTURE.parent / "does_not_exist.json"))


def test_task_from_row_parses_revenue_marker():
    row = {
        "id": "t_row", "title": "row task", "status": "Todo", "priority": "5",
        "assignee": "tech", "body": "task_type: code\nrevenue_gate: seo-site\n",
    }
    task = task_from_row("seo-site", row)
    assert task["revenue_critical"] is True and task["revenue_project"] == "seo-site"
    assert task["status"] == "todo"
    plain = task_from_row("seo-site", {**row, "body": ""})
    assert plain["revenue_critical"] is False
    with pytest.raises(ControllerInputError):
        task_from_row("seo-site", {"status": "todo"})


def test_cli_controller_snapshot_end_to_end(tmp_path):
    from fleet_policy.cli import main as cli_main
    from fleet_policy import runtime as runtime_mod

    db = tmp_path / "fp.db"
    argv = [
        "--root", str(Path(__file__).parents[1]),
        "controller", "--snapshot", str(FIXTURE), "--now", "2026-09-02T18:00:00+03:00",
    ]
    original_init = runtime_mod.FleetPolicyRuntime.__init__

    def patched_init(self, root, *, config_path=None, db_path=None):
        original_init(self, root, config_path=config_path, db_path=db_path or db)

    runtime_mod.FleetPolicyRuntime.__init__ = patched_init
    try:
        assert cli_main(argv) == 0
        assert cli_main(argv) == 0
    finally:
        runtime_mod.FleetPolicyRuntime.__init__ = original_init
    import sqlite3
    with sqlite3.connect(db) as connection:
        count = connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    assert count == 1  # deterministic repeat: zero new records


def test_cli_controller_rejects_bad_input(capsys):
    from fleet_policy.cli import main as cli_main

    assert cli_main(["--root", str(Path(__file__).parents[1]), "controller", "--snapshot", "missing.json"]) == 2
    assert cli_main(["--root", str(Path(__file__).parents[1]), "controller"]) == 2
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert out["ok"] is False and out["reason"]


def test_cli_controller_rejects_conflicting_modes():
    from fleet_policy.cli import main as cli_main

    argv = ["--root", str(Path(__file__).parents[1]), "controller", "--snapshot", str(FIXTURE), "--live"]
    assert cli_main(argv) == 2


def test_cli_controller_live_denies_non_canonical_board():
    from fleet_policy.cli import main as cli_main

    argv = ["--root", str(Path(__file__).parents[1]), "controller", "--live", "--boards", "rr-legacy"]
    assert cli_main(argv) == 2


def test_live_adapter_is_read_only_canonical_and_collect_evidence():
    calls: list[list[str]] = []

    def fake_runner(argv: list[str]) -> str:
        calls.append(argv)
        return json.dumps(
            [{"id": f"t_{len(calls)}", "title": "x", "status": "todo", "priority": 1,
              "assignee": "tech", "body": "revenue_gate: seo-site"}]
        )

    snapshot = load_live_snapshot(["seo-site"], runner=fake_runner)
    assert len(calls) == len(controller.LIVE_STATUSES)
    assert all(argv[:2] == ["kanban", "--board"] and argv[-1] == "--json" for argv in calls)
    assert snapshot["boards"]["seo-site"]["metric"]["evidence_gap"] == "metric_definition_source_value_unprovided"
    assert snapshot["boards"]["seo-site"]["candidates"] == []  # nothing invented
    assert snapshot["evaluated_at"]  # collector stamp
    decision = reduce(snapshot)
    assert decision["state"] == "ACTIONABLE_IDLE"
    assert decision["decision_type"] == "collect_evidence"
    assert decision["execution_eligible"] is False

    with pytest.raises(ControllerInputError):
        load_live_snapshot(["rr-legacy"], runner=fake_runner)
    with pytest.raises(ControllerInputError):
        load_live_snapshot([], runner=fake_runner)
    assert len(calls) == len(controller.LIVE_STATUSES)  # denied boards never reach the CLI
