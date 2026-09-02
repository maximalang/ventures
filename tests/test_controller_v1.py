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

FIXTURE = Path(__file__).parent / "fixtures" / "controller_shadow_v1.json"


def gate_task(task_id: str = "t_gate", status: str = "todo", project: str = "seo-site", **over) -> dict:
    task = {
        "task_id": task_id,
        "title": f"gate {task_id}",
        "board": "seo-site",
        "status": status,
        "priority": 900,
        "assignee": "research",
        "revenue_critical": True,
        "revenue_project": project,
        "effort_known": False,
        "scores": {},
        "evidence_gaps": [],
        "proposal": {},
    }
    task.update(over)
    return task


def bet_task(task_id: str = "t_bet", score: float = 6.4, cost: float = 0.0, **over) -> dict:
    fields = {
        "assignee": "tech",
        "effort_known": True,
        "scores": {"metric_impact": score, "gate_removal": 0, "confidence": 0.8, "cost_rub": cost},
        "proposal": {
            "owner": "tech",
            "squad": "tech,qa",
            "hypothesis": "bet lifts the revenue metric",
            "expected_impact": "+5 metric points in 30 days",
            "kill_criterion": "no metric movement by 2026-09-30",
            "rollback": "revert the slice",
        },
    }
    fields.update(over)
    return gate_task(task_id, **fields)


def gap_task(task_id: str = "t_gate", priority: int = 5, **over) -> dict:
    task = gate_task(task_id, **over)
    task.update(
        evidence_gaps=[
            {
                "field": "sources_measurement",
                "priority": priority,
                "owner": "research",
                "squad": ["research", "qa"],
                "freshness_target": "2026-09-05T00:00:00Z",
                "evidence_refs": ["fixture:STATE.md#measurement"],
                "missing_fields": ["sources_measurement"],
            }
        ]
    )
    return task


def snap(*tasks: dict, metric: str = "gap", finance: str = "gap") -> dict:
    return {
        "boards": {"portfolio": [], "rr-team": [], "seo-site": list(tasks)},
        "metric": {"status": metric},
        "finance": {"status": finance},
    }


# ---------------------------------------------------------------------- states


def test_busy_fleet_is_no_action():
    decision = reduce(snap(gate_task("t_run", status="running"), gap_task("t_gate")))
    assert decision["state"] == "RUNNING"
    assert decision["decision_type"] == "no_action"
    assert decision["reason"] == "fleet_busy_running"
    assert decision["success"] is False
    assert decision["mutation_ops"] == []


def test_ready_queue_is_no_action():
    decision = reduce(snap(gate_task("t_ready", status="ready"), gap_task("t_gate")))
    assert decision["state"] == "READY_QUEUE"
    assert decision["decision_type"] == "no_action"


def test_idle_without_actionable_gates_is_no_action():
    decision = reduce(snap(gate_task("t_done", status="done"), gap_task("t_gate", status="superseded")))
    assert decision["state"] == "IDLE_NO_GATES"
    assert decision["decision_type"] == "no_action"
    assert decision["reason"] == "no_actionable_revenue_gate"


def test_blocked_gate_is_never_actionable_and_never_success():
    decision = reduce(snap(gate_task("t_blocked", status="blocked")))
    assert decision["state"] == "IDLE_NO_GATES"
    assert decision["decision_type"] == "no_action"
    assert decision["counts"]["blocked_revenue_gates"] == 1
    assert decision["success"] is False


def test_actionable_idle_collects_evidence_from_fixture():
    decision = reduce(json.loads(FIXTURE.read_text(encoding="utf-8")))
    assert decision["state"] == "ACTIONABLE_IDLE"
    assert decision["decision_type"] == "collect_evidence"
    assert decision["execution_eligible"] is False
    candidate = decision["candidate"]
    assert candidate["task"]["task_id"] == "t_seo_measurement"
    assert candidate["missing_fields"] == ["sources_measurement"]
    assert candidate["owner"] == "research"
    assert candidate["squad"] == ["research", "qa"]
    assert candidate["freshness_target"] == "2026-09-05T00:00:00Z"
    assert candidate["score"]["value"] is None
    assert decision["digest"]["channel"] == "telegram"
    assert "[shadow mode]" in decision["digest"]["text"]
    assert "execution_eligible=false" in decision["digest"]["text"]
    assert "cost_rub=" not in decision["digest"]["text"]  # no invented RUB


# ---------------------------------------------------------------- execute_bet


def test_execute_bet_requires_fresh_metric_and_finance():
    task = bet_task()
    decision = reduce(snap(task, metric="fresh", finance="fresh"))
    assert decision["decision_type"] == "execute_bet"
    assert decision["execution_eligible"] is True
    assert decision["candidate"]["task"]["task_id"] == task["task_id"]
    assert decision["candidate"]["score"]["value"] == pytest.approx(task["scores"]["metric_impact"] * 0.8)
    assert decision["digest"]["channel"] == "telegram"

    for kwargs in ({"metric": "gap", "finance": "fresh"}, {"metric": "fresh", "finance": "stale"}):
        decision = reduce(snap(bet_task(), gap_task(), **kwargs))
        assert decision["decision_type"] == "collect_evidence"


def test_execute_bet_requires_known_effort_and_complete_proposal():
    decision = reduce(snap(bet_task(effort_known=False), gap_task(), metric="fresh", finance="fresh"))
    assert decision["decision_type"] == "collect_evidence"

    incomplete = bet_task("t_incomplete")
    del incomplete["proposal"]["rollback"]
    decision = reduce(snap(incomplete, metric="fresh", finance="fresh"))
    assert decision["decision_type"] == "no_action"
    assert decision["reason"] == "no_executable_candidate_and_no_evidence_path"


def test_highest_score_wins_and_superseded_never_wins():
    decision = reduce(
        snap(bet_task("t_low", score=1.0), bet_task("t_high", score=9.0), metric="fresh", finance="fresh")
    )
    assert decision["candidate"]["task"]["task_id"] == "t_high"

    decision = reduce(snap(bet_task("t_old", status="superseded", score=99.0), metric="fresh", finance="fresh"))
    assert decision["decision_type"] == "no_action"
    assert decision["state"] == "IDLE_NO_GATES"
    assert decision["counts"]["actionable_revenue_gates"] == 0


def test_ties_resolve_to_no_action():
    decision = reduce(snap(bet_task("t_a", score=5.0), bet_task("t_b", score=5.0), metric="fresh", finance="fresh"))
    assert decision["decision_type"] == "no_action"
    assert decision["reason"] == "score_tie"

    decision = reduce(snap(gap_task("t_x", priority=7), gap_task("t_y", priority=7)))
    assert decision["decision_type"] == "no_action"
    assert decision["reason"] == "evidence_priority_tie"


# ------------------------------------------------------- determinism & idempotency


def test_decision_is_order_independent_and_content_hashed():
    tasks = [bet_task("t_low", score=1.0), gap_task("t_gate", priority=3), gate_task("t_misc", status="done")]
    first = reduce(snap(*tasks, metric="fresh", finance="fresh"))
    shuffled = list(tasks)
    random.Random(7).shuffle(shuffled)
    second = reduce(snap(*shuffled, metric="fresh", finance="fresh"))
    assert first["decision_id"] == second["decision_id"]
    assert first == second
    assert first["idempotency_key"] == first["decision_id"]


def test_engine_repeat_writes_zero_new_records(runtime):
    engine = ControllerEngine(runtime.store)
    snapshot = snap(gap_task(), metric="fresh")
    first = engine.run(snapshot, now="2026-09-02T16:00:00+03:00")
    with runtime.store.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 1
    second = engine.run(snapshot, now="2026-09-02T16:05:00+03:00")
    assert second["duplicate"] is True and first["duplicate"] is False
    assert {**second, "duplicate": False} == first
    assert second["evaluated_at"] == "2026-09-02T16:00:00+03:00"  # stored decision returned
    with runtime.store.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 1
        row = connection.execute("SELECT kind, significant, task_id FROM events").fetchone()
    assert row["kind"] == "controller_decision"
    assert row["significant"] == 0 and row["task_id"] is None


def test_different_snapshots_get_different_ids(runtime):
    engine = ControllerEngine(runtime.store)
    first = engine.run(snap(gap_task("t_a")))
    second = engine.run(snap(gap_task("t_b")))
    assert first["decision_id"] != second["decision_id"]
    with runtime.store.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 2


# ------------------------------------------------------------------ fail-closed


def test_fail_closed_on_invalid_input():
    with pytest.raises(ControllerInputError):
        reduce({"boards": {"rr-team": [{"task_id": "t", "scores": {"nope": 1}}]}})
    with pytest.raises(ControllerInputError):
        reduce({"boards": {"rr-team": [{"status": "todo"}]}})
    with pytest.raises(ControllerInputError):
        reduce({"boards": {"rr-team": "nope"}})
    with pytest.raises(ControllerInputError):
        reduce("not a snapshot")
    with pytest.raises(ControllerInputError):
        load_snapshot_file(str(FIXTURE.parent / "does_not_exist.json"))


def test_task_from_row_parses_body_markers():
    row = {
        "id": "t_row",
        "title": "row task",
        "status": "Todo",
        "priority": "5",
        "assignee": "tech",
        "body": (
            "task_type: code\n"
            "revenue_gate: rr-team\n"
            "effort_known: false\n"
            "bet_score: metric_impact=3 gate_removal=2 confidence=0.5 cost_rub=0\n"
            "evidence_gap: metric:fresh | priority=2 | owner=research | squad=research,qa | freshness=2026-09-05T00:00:00Z\n"
            "bet_hypothesis: fresh metric unlocks the gate\n"
            "bet_kill: nothing moves in 30d\n"
        ),
    }
    task = task_from_row("rr-team", row)
    assert task["revenue_critical"] is True and task["revenue_project"] == "rr-team"
    assert task["effort_known"] is False and task["status"] == "todo"
    assert task["scores"]["confidence"] == 0.5
    assert task["evidence_gaps"][0]["owner"] == "research"
    assert task["proposal"]["hypothesis"] == "fresh metric unlocks the gate"
    with pytest.raises(ControllerInputError):
        task_from_row("rr-team", {**row, "body": "bet_score: wrong=1"})
    with pytest.raises(ControllerInputError):
        task_from_row("rr-team", {"status": "todo"})


def test_cli_controller_snapshot_end_to_end(tmp_path):
    from fleet_policy.cli import main as cli_main

    db = tmp_path / "fp.db"
    argv = [
        "--root", str(Path(__file__).parents[1]),
        "controller", "--snapshot", str(FIXTURE), "--now", "2026-09-02T16:00:00+03:00",
    ]
    import os
    env_backup = os.environ.get("FLEET_POLICY_DB_PATH")
    # Route the engine's runtime store to the temp DB via monkeypatched store path.
    from fleet_policy import runtime as runtime_mod
    original_init = runtime_mod.FleetPolicyRuntime.__init__

    def patched_init(self, root, *, config_path=None, db_path=None):
        original_init(self, root, config_path=config_path, db_path=db_path or db)

    runtime_mod.FleetPolicyRuntime.__init__ = patched_init
    try:
        assert cli_main(argv) == 0
        assert cli_main(argv) == 0
    finally:
        runtime_mod.FleetPolicyRuntime.__init__ = original_init
        if env_backup is None:
            os.environ.pop("FLEET_POLICY_DB_PATH", None)
        else:
            os.environ["FLEET_POLICY_DB_PATH"] = env_backup
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


def test_cli_controller_live_denies_non_canonical_board(tmp_path):
    from fleet_policy.cli import main as cli_main

    argv = ["--root", str(Path(__file__).parents[1]), "controller", "--live", "--boards", "rr-legacy"]
    assert cli_main(argv) == 2


def test_live_adapter_is_read_only_and_canonical_only():
    calls: list[list[str]] = []

    def fake_runner(argv: list[str]) -> str:
        calls.append(argv)
        return json.dumps(
            [{"id": f"t_{len(calls)}", "title": "x", "status": "todo", "priority": 1, "assignee": "tech", "body": ""}]
        )

    snapshot = load_live_snapshot(["seo-site"], runner=fake_runner)
    assert len(calls) == len(controller.LIVE_STATUSES)
    assert all(argv[:2] == ["kanban", "--board"] and argv[-1] == "--json" for argv in calls)
    assert len(snapshot["boards"]["seo-site"]) == len(controller.LIVE_STATUSES)
    assert snapshot["metric"]["status"] == "gap"

    with pytest.raises(ControllerInputError):
        load_live_snapshot(["rr-legacy"], runner=fake_runner)
    with pytest.raises(ControllerInputError):
        load_live_snapshot([], runner=fake_runner)
    assert len(calls) == len(controller.LIVE_STATUSES)  # denied boards never reach the CLI
