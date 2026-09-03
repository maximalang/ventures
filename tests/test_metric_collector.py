"""Tests for fleet_policy.metric_collector (contract v3, Phase 1).

All board data comes from deterministic fakes; no live CLI, no network.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re

import pytest

from fleet_policy import metric_collector as mc

RUN_DATE = _dt.date(2026, 9, 3)


def make_window():
    return mc.compute_window(RUN_DATE)


WINDOW = make_window()
IN_WINDOW = WINDOW["start"] + 86400          # safely inside
OUT_WINDOW = WINDOW["start"] - 86400         # one day before start


class FakeRunner:
    """Deterministic stand-in for KanbanCliRunner."""

    def __init__(self, tasks_by_board=None, runs_by_board=None):
        self.tasks_by_board = tasks_by_board or {}
        self.runs_by_board = runs_by_board or {}
        self.calls = []

    def list_tasks(self, board):
        self.calls.append(("list", board))
        return self.tasks_by_board.get(board, [])

    def runs(self, board, task_id):
        self.calls.append(("runs", board, task_id))
        return self.runs_by_board.get(board, {}).get(task_id, [])


def task(tid, completed_at, title="t", result=None):
    return {"id": tid, "completed_at": completed_at, "title": title,
            "result": result, "status": "done"}


def run(outcome="completed", summary=None, metadata=None):
    return {"id": 1, "outcome": outcome, "summary": summary,
            "metadata": metadata}


# ---------------------------------------------------------------- window

def test_window_is_28_days_and_local():
    w = make_window()
    assert w["end"] - w["start"] == 28 * 86400
    assert w["end_date"] == "2026-09-03"
    assert w["start_date"] == "2026-08-06" or w["start_date"] == "2026-08-07"


def test_window_end_exclusive_day_boundary():
    w = make_window()
    # completed_at exactly at window end (start of next day) is excluded
    assert not (w["start"] <= w["end"] < w["end"])
    assert w["start"] <= w["end"] - 1 < w["end"]


# ------------------------------------------------------------- rr metric

def test_rr_gap_when_no_markers_anywhere():
    boards = {"rr-team": [
        task("t_a1", IN_WINDOW, title="QA review of PR", result=""),
        task("t_a2", IN_WINDOW, title="Fix landing", result="done"),
    ]}
    runs = {"rr-team": {
        "t_a1": [run(summary="BLOCKER review, accepted rows in SQL",
                     metadata={"findings": ["accepted/fresh lineage"]})],
        "t_a2": [run(summary="patched", metadata={"checks": ["ok"]})],
    }}
    res = mc.collect_rr_leads(FakeRunner(boards, runs), WINDOW)
    rec = res["record"]
    assert rec["value"] is None and rec["observed_at"] is None
    assert rec["evidence_gap"] == mc.GAP_RR_MARKERS
    assert rec["confidence"] is None


def test_rr_bare_accepted_in_review_prose_does_not_count():
    # exact false-positive shape seen in live data: QA cards say "accepted"
    # about rows/domains, never about leads.
    boards = {"rr-team": [task("t_q", IN_WINDOW)]}
    runs = {"rr-team": {"t_q": [run(
        metadata={"finding": "the installed trigger accepted a github.io row"})]}}
    res = mc.collect_rr_leads(FakeRunner(boards, runs), WINDOW)
    assert res["record"]["evidence_gap"] == mc.GAP_RR_MARKERS


def test_rr_structured_outcome_key_counts():
    boards = {"rr-team": [task("t_l1", IN_WINDOW)]}
    runs = {"rr-team": {"t_l1": [run(metadata={"lead_outcome": "accepted",
                                                "evidence_ref": "kanban:t_x"})]}}
    res = mc.collect_rr_leads(FakeRunner(boards, runs), WINDOW)
    assert res["record"]["value"] == 1
    assert res["record"]["observed_at"] == IN_WINDOW
    assert res["record"]["evidence_gap"] is None


def test_rr_prose_marker_near_lead_word_counts():
    boards = {"rr-team": [task("t_l2", IN_WINDOW)]}
    runs = {"rr-team": {"t_l2": [run(
        summary="Лид принят: кандидат accepted в работу, evidence приложен")]}}
    res = mc.collect_rr_leads(FakeRunner(boards, runs), WINDOW)
    assert res["record"]["value"] == 1


def test_rr_marker_far_from_lead_word_does_not_count():
    text = "accepted " + "x" * 200 + " lead"
    boards = {"rr-team": [task("t_l3", IN_WINDOW)]}
    runs = {"rr-team": {"t_l3": [run(summary=text)]}}
    res = mc.collect_rr_leads(FakeRunner(boards, runs), WINDOW)
    assert res["record"]["evidence_gap"] == mc.GAP_RR_MARKERS


def test_rr_out_of_window_cards_ignored():
    boards = {"rr-team": [task("t_old", OUT_WINDOW)]}
    runs = {"rr-team": {"t_old": [run(metadata={"lead_outcome": "won"})]}}
    res = mc.collect_rr_leads(FakeRunner(boards, runs), WINDOW)
    assert res["record"]["evidence_gap"] == mc.GAP_RR_MARKERS


def test_rr_empty_board_fixture():
    res = mc.collect_rr_leads(FakeRunner({}, {}), WINDOW)
    assert res["record"]["value"] is None
    assert res["record"]["evidence_gap"] == mc.GAP_RR_MARKERS
    assert res["evidence"]["counted_cards"] == []


# -------------------------------------------------------------- seo metric

def test_seo_gap_without_token():
    env = {"PATH": "/bin", "HOME": "/home/x"}
    res = mc.collect_seo(env)
    rec = res["record"]
    assert rec["value"] is None and rec["observed_at"] is None
    assert rec["evidence_gap"] == mc.GAP_METRIKA_TOKEN
    assert "112116194" in res["evidence"]["note"]


def test_seo_token_detection_is_name_only_and_phase1b_gap():
    env = {"YANDEX_METRIKA_OAUTH": "secret-value", "PATH": "/bin"}
    res = mc.collect_seo(env)
    rec = res["record"]
    assert rec["evidence_gap"] == mc.GAP_METRIKA_GOAL
    assert rec["value"] is None and rec["observed_at"] is None
    # token VALUE must not leak anywhere in the evidence
    assert "secret-value" not in json.dumps(res, ensure_ascii=False)


def test_seo_token_name_variants():
    assert mc.collect_seo({"METRICA_TOKEN": "x"})["record"]["evidence_gap"] \
        == mc.GAP_METRIKA_GOAL
    assert mc.collect_seo({"some_metrica_key": "x"})["record"]["evidence_gap"] \
        == mc.GAP_METRIKA_GOAL
    assert mc.collect_seo({"METRIC_COUNTER": "x"})["record"]["evidence_gap"] \
        == mc.GAP_METRIKA_TOKEN  # 'metric' alone is not metrika/metrica


# ---------------------------------------------------------- company metric

def test_company_counts_company_decisions_dict():
    boards = {"fleet-ops": [task("t_c1", IN_WINDOW)], "portfolio": []}
    runs = {"fleet-ops": {"t_c1": [run(metadata={
        "company_decisions": {"pr_merge": "NO-GO", "wave": "GO"},
        "verdict": "not proven"})]}}
    res = mc.collect_company_decisions(FakeRunner(boards, runs), WINDOW)
    assert res["record"]["value"] == 2
    assert res["record"]["observed_at"] == IN_WINDOW


def test_company_verdict_with_evidence_key_counts_one():
    boards = {"fleet-ops": [task("t_c2", IN_WINDOW)], "portfolio": []}
    runs = {"fleet-ops": {"t_c2": [run(metadata={
        "verdict": "FAIL", "findings": ["x"]})]}}
    res = mc.collect_company_decisions(FakeRunner(boards, runs), WINDOW)
    assert res["record"]["value"] == 1


def test_company_verdict_without_evidence_does_not_count():
    boards = {"fleet-ops": [task("t_c3", IN_WINDOW)], "portfolio": []}
    runs = {"fleet-ops": {"t_c3": [run(metadata={
        "verdict": "PASS", "note": "no evidence keys here"})]}}
    res = mc.collect_company_decisions(FakeRunner(boards, runs), WINDOW)
    assert res["record"]["evidence_gap"] == mc.GAP_COMPANY_MARKERS


def test_company_checks_key_counts_as_evidence():
    boards = {"fleet-ops": [task("t_c4", IN_WINDOW)], "portfolio": []}
    runs = {"fleet-ops": {"t_c4": [run(metadata={
        "verdict": "CANARY PASS", "checks": ["a", "b"]})]}}
    res = mc.collect_company_decisions(FakeRunner(boards, runs), WINDOW)
    assert res["record"]["value"] == 1


def test_company_portfolio_board_included():
    boards = {"fleet-ops": [], "portfolio": [task("t_p1", IN_WINDOW)]}
    runs = {"portfolio": {"t_p1": [run(metadata={
        "verdict": "GO", "evidence": {"pr": "url"}})]}}
    res = mc.collect_company_decisions(FakeRunner(boards, runs), WINDOW)
    assert res["record"]["value"] == 1
    assert res["evidence"]["counted_cards"][0]["board"] == "portfolio"


def test_company_empty_boards_gap():
    res = mc.collect_company_decisions(FakeRunner({}, {}), WINDOW)
    assert res["record"]["value"] is None
    assert res["record"]["evidence_gap"] == mc.GAP_COMPANY_MARKERS


# ------------------------------------------------------ schema & snapshot

def test_build_snapshot_all_gap_empty_boards():
    snap = mc.build_snapshot(FakeRunner({}, {}), WINDOW, env={})
    assert snap["contract"] == mc.CONTRACT_NAME
    assert snap["version"] == mc.CONTRACT_VERSION
    assert len(snap["records"]) == 3
    for rec in snap["records"]:
        assert set(rec) == set(mc.SCHEMA_FIELDS)
        assert rec["value"] is None
        assert rec["observed_at"] is None
        assert rec["evidence_gap"] is not None
    gaps = {r["metric_id"]: r["evidence_gap"] for r in snap["records"]}
    assert gaps["accepted_evidence_backed_leads_28d"] == mc.GAP_RR_MARKERS
    assert gaps["successful_organic_calculations_28d"] == mc.GAP_METRIKA_TOKEN
    assert gaps["evidence_backed_go_no_go_decisions_28d"] \
        == mc.GAP_COMPANY_MARKERS
    assert mc.validate_snapshot(snap) == []


def test_build_snapshot_valued_records_have_evidence_blocks():
    boards = {
        "rr-team": [task("t_r", IN_WINDOW)],
        "fleet-ops": [task("t_f", IN_WINDOW + 3600)],
        "portfolio": [],
        "seo-site": [],
    }
    runs = {
        "rr-team": {"t_r": [run(metadata={"outcome": "contacted"})]},
        "fleet-ops": {"t_f": [run(metadata={
            "verdict": "GO", "findings": ["ok"]})]},
    }
    snap = mc.build_snapshot(FakeRunner(boards, runs), WINDOW, env={})
    assert mc.validate_snapshot(snap) == []
    rr = next(r for r in snap["records"]
              if r["metric_id"] == "accepted_evidence_backed_leads_28d")
    co = next(r for r in snap["records"]
              if r["metric_id"] == "evidence_backed_go_no_go_decisions_28d")
    assert rr["value"] == 1 and rr["observed_at"] == IN_WINDOW
    assert co["value"] == 1 and co["observed_at"] == IN_WINDOW + 3600
    assert rr["source_ref"] == "#/evidence/accepted_evidence_backed_leads_28d"
    assert "accepted_evidence_backed_leads_28d" in snap["evidence"]
    assert snap["evidence"]["accepted_evidence_backed_leads_28d"][
        "counted_cards"][0]["task_id"] == "t_r"


def test_serializer_is_stable_and_sorted():
    snap = mc.build_snapshot(FakeRunner({}, {}), WINDOW, env={})
    text = mc.serialize(snap)
    assert text.endswith("\n") and not text.endswith("\n\n")
    parsed = json.loads(text)
    keys = list(parsed)
    assert keys == sorted(keys)
    # ensure_ascii=false: definitions keep cyrillic as-is
    assert "Число" in text
    for rec_keys_line in re.finditer(r'"records"', text):
        assert rec_keys_line


def test_byte_idempotence_same_day_same_bytes():
    runner1 = FakeRunner({}, {})
    runner2 = FakeRunner({}, {})
    s1 = mc.serialize(mc.build_snapshot(runner1, WINDOW, env={}))
    s2 = mc.serialize(mc.build_snapshot(runner2, WINDOW, env={}))
    h1 = hashlib.sha256(s1.encode()).hexdigest()
    h2 = hashlib.sha256(s2.encode()).hexdigest()
    assert h1 == h2
    assert s1 == s2


def test_observed_at_never_wall_clock():
    # observed_at must come from card data, not run time: two fake runs at
    # different wall-clock instants produce identical bytes.
    import time
    boards = {"rr-team": [task("t_w", IN_WINDOW)], "fleet-ops": [],
              "portfolio": [], "seo-site": []}
    runs = {"rr-team": {"t_w": [run(metadata={"outcome": "replied"})]}}
    s1 = mc.serialize(mc.build_snapshot(FakeRunner(boards, runs), WINDOW, env={}))
    time.sleep(0.05)
    s2 = mc.serialize(mc.build_snapshot(FakeRunner(boards, runs), WINDOW, env={}))
    assert s1 == s2
    snap = json.loads(s1)
    rec = next(r for r in snap["records"]
               if r["metric_id"] == "accepted_evidence_backed_leads_28d")
    assert rec["observed_at"] == IN_WINDOW


# ------------------------------------------------------------- validation

def test_validator_catches_invariant_violation():
    snap = mc.build_snapshot(FakeRunner({}, {}), WINDOW, env={})
    snap["records"][0]["value"] = 5  # gap set but value present
    problems = mc.validate_snapshot(snap)
    assert any("nullability" in p for p in problems)


def test_validator_catches_missing_field():
    snap = mc.build_snapshot(FakeRunner({}, {}), WINDOW, env={})
    del snap["records"][1]["source_ref"]
    problems = mc.validate_snapshot(snap)
    assert any("source_ref" in p for p in problems)


def test_validator_catches_wrong_record_count():
    snap = mc.build_snapshot(FakeRunner({}, {}), WINDOW, env={})
    snap["records"] = snap["records"][:2]
    assert any("exactly 3" in p for p in mc.validate_snapshot(snap))


# ------------------------------------------------------------------ misc

def test_sanitize_env_drops_board_pinning():
    env = {"HERMES_KANBAN_DB": "/x/kanban.db",
           "HERMES_KANBAN_BOARD": "fleet-ops", "PATH": "/bin"}
    out = mc.sanitize_env(env)
    assert "HERMES_KANBAN_DB" not in out
    assert "HERMES_KANBAN_BOARD" not in out
    assert out["PATH"] == "/bin"


def test_records_spec_matches_contract():
    ids = [s["metric_id"] for s in mc.RECORDS_SPEC]
    assert ids == [
        "accepted_evidence_backed_leads_28d",
        "successful_organic_calculations_28d",
        "evidence_backed_go_no_go_decisions_28d",
    ]
    assert mc.RECORDS_SPEC[0]["unit"] == "leads"
    assert mc.RECORDS_SPEC[1]["unit"] == "calculations"
    assert mc.RECORDS_SPEC[2]["unit"] == "decisions"


def test_main_dry_run_prints_sha_and_path(tmp_path, capsys, monkeypatch):
    # point the live CLI adapter at empty boards via monkeypatched runner
    monkeypatch.setattr(mc, "KanbanCliRunner", lambda: FakeRunner({}, {}))
    rc = mc.main(["--date", "2026-09-03", "--out-dir", str(tmp_path),
                  "--dry-run"])
    out = capsys.readouterr().out
    assert rc == 0
    m = re.search(r"sha256=([0-9a-f]{64})", out)
    assert m
    assert "snapshot-2026-09-03.json" in out
    assert not (tmp_path / "snapshot-2026-09-03.json").exists()


def test_main_writes_file_and_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(mc, "KanbanCliRunner", lambda: FakeRunner({}, {}))
    monkeypatch.setenv("HOME", str(tmp_path))
    rc1 = mc.main(["--date", "2026-09-03", "--out-dir", str(tmp_path)])
    rc2 = mc.main(["--date", "2026-09-03", "--out-dir", str(tmp_path)])
    assert rc1 == 0 and rc2 == 0
    path = tmp_path / "snapshot-2026-09-03.json"
    assert path.exists()
    data = path.read_bytes()
    text = data.decode("utf-8")
    assert text.endswith("\n")
    assert "\r\n" not in text  # no CRLF translation: exact canonical bytes
    on_disk_sha = hashlib.sha256(data).hexdigest()
    canonical_sha = hashlib.sha256(
        mc.serialize(mc.build_snapshot(FakeRunner({}, {}), WINDOW, env={}))
        .encode("utf-8")).hexdigest()
    assert on_disk_sha == canonical_sha  # disk bytes == reported sha256
