"""Unit tests for the decision ledger (src/decision_ledger, ledger.py).

All tests use a tmp_path database so they never touch
.state/decision-ledger.db on any host.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from decision_ledger.store import (
    BRIEF_LIMIT_DEFAULT,
    LedgerError,
    add_decision,
    build_brief,
    connect,
    default_db_path,
    initialize,
    list_decisions,
    review_outcome,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
LEDGER_CLI = REPO_ROOT / "ledger.py"

VALID_ROW = {
    "scope": "venture",
    "venture": "rr",
    "hypothesis": "landing rewrite lifts signup CTR",
    "decision": "go",
    "confidence": 0.7,
    "expected_impact": "+15% CTR",
    "cost_rub": 30000.0,
    "kill_criterion": "CTR below baseline in 14 days",
    "kanban_task_id": "t_4dbcd5da",
    "evidence_refs": ["https://example/pr/1", "sha256:abcd"],
}


def _add(db_path: Path, **overrides) -> int:
    row = {**VALID_ROW, **overrides}
    return add_decision(db_path=db_path, **row)


@pytest.fixture
def db(tmp_path: Path) -> Path:
    path = tmp_path / "ledger.db"
    initialize(path)
    return path


class TestSchemaAndStorage:
    def test_default_db_path_uses_state_dir_or_env(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        env_db = tmp_path / "env-override.db"
        monkeypatch.setenv("DECISION_LEDGER_DB", str(env_db))
        assert default_db_path() == env_db
        monkeypatch.delenv("DECISION_LEDGER_DB")
        resolved = default_db_path()
        assert resolved.name == "decision-ledger.db"
        assert resolved.parent.name == ".state"
        # repo root derived from src/decision_ledger/store.py → two levels up
        assert resolved.parents[1] == REPO_ROOT

    def test_initialize_is_idempotent(self, db: Path) -> None:
        initialize(db)
        initialize(db)
        with connect(db) as conn:
            tables = {
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
        assert "decisions" in tables

    def test_schema_rejects_bad_scope_and_decision(self, db: Path) -> None:
        with connect(db) as conn, pytest.raises(Exception):
            conn.execute(
                "INSERT INTO decisions (ts, scope, venture, hypothesis, decision, "
                "confidence, expected_impact, cost_rub, kill_criterion, "
                "kanban_task_id, evidence_refs) VALUES "
                "('now', 'galaxy', '', 'h', 'go', 0.5, '', 0, '', '', '[]')"
            )
        with connect(db) as conn, pytest.raises(Exception):
            conn.execute(
                "INSERT INTO decisions (ts, scope, venture, hypothesis, decision, "
                "confidence, expected_impact, cost_rub, kill_criterion, "
                "kanban_task_id, evidence_refs) VALUES "
                "('now', 'portfolio', '', 'h', 'maybe', 0.5, '', 0, '', '', '[]')"
            )
        with connect(db) as conn, pytest.raises(Exception):
            conn.execute(
                "INSERT INTO decisions (ts, scope, venture, hypothesis, decision, "
                "confidence, expected_impact, cost_rub, kill_criterion, "
                "kanban_task_id, evidence_refs) VALUES "
                "('now', 'portfolio', '', 'h', 'go', 1.5, '', 0, '', '', '[]')"
            )


class TestValidation:
    def test_add_returns_id_and_persists_row(self, db: Path) -> None:
        decision_id = _add(db)
        assert decision_id == 1
        rows = list_decisions(db_path=db)
        assert len(rows) == 1
        row = rows[0]
        assert row["id"] == 1
        assert row["scope"] == "venture"
        assert row["venture"] == "rr"
        assert row["decision"] == "go"
        assert row["confidence"] == pytest.approx(0.7)
        assert row["cost_rub"] == pytest.approx(30000.0)
        assert row["kanban_task_id"] == "t_4dbcd5da"
        assert row["evidence_refs"] == ["https://example/pr/1", "sha256:abcd"]
        assert row["outcome_status"] == "open"
        assert row["outcome_reviewed_at"] is None
        assert row["ts"].endswith("Z")

    @pytest.mark.parametrize("scope", ["", "galaxy", "Portfolio"])
    def test_rejects_bad_scope(self, db: Path, scope: str) -> None:
        with pytest.raises(LedgerError, match="scope"):
            _add(db, scope=scope)

    @pytest.mark.parametrize("decision", ["", "maybe", "GO"])
    def test_rejects_bad_decision(self, db: Path, decision: str) -> None:
        with pytest.raises(LedgerError, match="decision"):
            _add(db, decision=decision)

    @pytest.mark.parametrize("hypothesis", ["", "   "])
    def test_rejects_empty_hypothesis(self, db: Path, hypothesis: str) -> None:
        with pytest.raises(LedgerError, match="hypothesis"):
            _add(db, hypothesis=hypothesis)

    def test_venture_required_for_venture_scope(self, db: Path) -> None:
        with pytest.raises(LedgerError, match="venture"):
            _add(db, venture="")
        # portfolio scope does not need a venture (a rejected insert does not
        # consume the AUTOINCREMENT sequence, so this id may be 1)
        assert _add(db, scope="portfolio", venture="") >= 1

    @pytest.mark.parametrize("confidence", [-0.1, 1.1, "high"])
    def test_rejects_confidence_out_of_range(self, db: Path, confidence) -> None:
        with pytest.raises(LedgerError, match="confidence"):
            _add(db, confidence=confidence)

    @pytest.mark.parametrize("cost", [-1.0, "free"])
    def test_rejects_bad_cost(self, db: Path, cost) -> None:
        with pytest.raises(LedgerError, match="cost_rub"):
            _add(db, cost_rub=cost)

    def test_evidence_refs_accepts_list_and_json_string(self, db: Path) -> None:
        assert _add(db, evidence_refs=["a", "b"]) == 1
        assert _add(db, evidence_refs='["c"]') == 2
        assert list_decisions(db_path=db)[0]["evidence_refs"] == ["c"]
        assert list_decisions(db_path=db)[1]["evidence_refs"] == ["a", "b"]

    def test_evidence_refs_rejects_bad_json(self, db: Path) -> None:
        with pytest.raises(LedgerError, match="evidence_refs"):
            _add(db, evidence_refs="not-json")
        with pytest.raises(LedgerError, match="evidence_refs"):
            _add(db, evidence_refs='{"not": "an array"}')


class TestListAndFilter:
    def test_list_newest_first(self, db: Path) -> None:
        _add(db, hypothesis="first")
        _add(db, hypothesis="second")
        _add(db, hypothesis="third")
        rows = list_decisions(db_path=db)
        assert [row["hypothesis"] for row in rows] == ["third", "second", "first"]

    def test_list_filters(self, db: Path) -> None:
        _add(db, scope="portfolio", venture="")
        _add(db, venture="rr")
        _add(db, venture="seo-site")
        assert len(list_decisions(db_path=db)) == 3
        assert len(list_decisions(scope="portfolio", db_path=db)) == 1
        assert len(list_decisions(venture="rr", db_path=db)) == 1
        assert len(list_decisions(outcome_status="open", db_path=db)) == 3

    def test_list_limit(self, db: Path) -> None:
        for i in range(5):
            _add(db, hypothesis=f"h{i}")
        assert len(list_decisions(limit=2, db_path=db)) == 2
        with pytest.raises(LedgerError, match="limit"):
            list_decisions(limit=0, db_path=db)

    def test_list_rejects_bad_filters(self, db: Path) -> None:
        with pytest.raises(LedgerError, match="scope"):
            list_decisions(scope="galaxy", db_path=db)
        with pytest.raises(LedgerError, match="outcome_status"):
            list_decisions(outcome_status="done", db_path=db)


class TestReviewOutcome:
    def test_review_sets_outcome_and_timestamp(self, db: Path) -> None:
        decision_id = _add(db)
        updated = review_outcome(
            decision_id, outcome_status="hit", note="CTR +18%", db_path=db
        )
        assert updated is not None
        assert updated["outcome_status"] == "hit"
        assert updated["outcome_note"] == "CTR +18%"
        assert updated["outcome_reviewed_at"] is not None
        assert updated["outcome_reviewed_at"].endswith("Z")

    @pytest.mark.parametrize("status", ["open", "hit", "missed", "killed"])
    def test_review_accepts_all_valid_statuses(self, db: Path, status: str) -> None:
        decision_id = _add(db)
        updated = review_outcome(decision_id, outcome_status=status, db_path=db)
        assert updated is not None and updated["outcome_status"] == status

    def test_review_rejects_bad_status(self, db: Path) -> None:
        decision_id = _add(db)
        with pytest.raises(LedgerError, match="outcome_status"):
            review_outcome(decision_id, outcome_status="done", db_path=db)

    def test_review_unknown_id_returns_none(self, db: Path) -> None:
        assert review_outcome(999, outcome_status="hit", db_path=db) is None

    def test_reviewed_row_leaves_open_filter(self, db: Path) -> None:
        decision_id = _add(db)
        review_outcome(decision_id, outcome_status="missed", db_path=db)
        assert list_decisions(outcome_status="open", db_path=db) == []
        assert len(list_decisions(outcome_status="missed", db_path=db)) == 1


class TestBrief:
    def test_brief_contains_recent_and_open_sections(self, db: Path) -> None:
        _add(db, hypothesis="alpha hypothesis")
        _add(db, hypothesis="beta hypothesis")
        brief = build_brief(db_path=db)
        assert "Recent decisions" in brief
        assert "Open outcomes (2)" in brief
        assert "alpha hypothesis" in brief
        assert "beta hypothesis" in brief
        assert "kill criterion: CTR below baseline in 14 days" in brief
        assert "task: t_4dbcd5da" in brief

    def test_brief_limit_caps_recent_section(self, db: Path) -> None:
        for i in range(12):
            _add(db, hypothesis=f"h{i}")
        brief = build_brief(limit=BRIEF_LIMIT_DEFAULT, db_path=db)
        # last 8 shown in recent section; all 12 open in outcomes section
        assert "Open outcomes (12)" in brief
        assert "h11" in brief and "h4" in brief
        recent_section = brief.split("## Open outcomes")[0]
        assert "h3" not in recent_section

    def test_brief_empty_ledger(self, db: Path) -> None:
        brief = build_brief(db_path=db)
        assert "none recorded yet" in brief
        assert "Open outcomes (0)" in brief

    def test_brief_rejects_nonpositive_limit(self, db: Path) -> None:
        with pytest.raises(LedgerError, match="limit"):
            build_brief(limit=0, db_path=db)


class TestCli:
    def _run(self, *args: str, db: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(LEDGER_CLI), *args, "--db", str(db)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

    def test_cli_add_list_review_brief_roundtrip(self, db: Path) -> None:
        add = self._run(
            "add",
            "--scope", "venture",
            "--venture", "rr",
            "--decision", "go",
            "--hypothesis", "cli hypothesis",
            "--confidence", "0.6",
            "--expected-impact", "+10% MRR",
            "--cost-rub", "15000",
            "--kill-criterion", "no movement in 30 days",
            "--kanban-task-id", "t_cli",
            "--evidence-ref", "https://example/1",
            db=db,
        )
        assert add.returncode == 0, add.stderr
        assert "added decision #1" in add.stdout

        listed = self._run("list", "--json", db=db)
        assert listed.returncode == 0, listed.stderr
        rows = __import__("json").loads(listed.stdout)
        assert rows[0]["hypothesis"] == "cli hypothesis"
        assert rows[0]["confidence"] == pytest.approx(0.6)

        reviewed = self._run("review-outcome", "1", "--outcome", "hit", "--note", "measured", db=db)
        assert reviewed.returncode == 0, reviewed.stderr
        assert "outcome=hit" in reviewed.stdout

        brief = self._run("brief", db=db)
        assert brief.returncode == 0, brief.stderr
        assert "cli hypothesis" in brief.stdout
        assert "Open outcomes (0)" in brief.stdout

    def test_cli_add_validation_failure_exits_2(self, db: Path) -> None:
        bad = self._run(
            "add",
            "--scope", "venture",
            "--venture", "",
            "--decision", "go",
            "--hypothesis", "h",
            "--confidence", "0.5",
            db=db,
        )
        assert bad.returncode == 2
        assert "ledger error" in bad.stderr

    def test_cli_review_unknown_id_exits_2(self, db: Path) -> None:
        result = self._run("review-outcome", "42", "--outcome", "hit", db=db)
        assert result.returncode == 2
        assert "not found" in result.stderr

    def test_cli_module_docstring_documents_attribution(self) -> None:
        spec = importlib.util.spec_from_file_location("ledger_cli_under_test", LEDGER_CLI)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        doc = module.__doc__ or ""
        assert "SenteLabsAI/OpenExecutive" in doc
        assert "Apache-2.0" in doc
