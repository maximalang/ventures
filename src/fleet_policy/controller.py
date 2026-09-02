"""Company OS deterministic next-bet controller — SHADOW mode, econ-score/v3.

Re-derived run 367 (task t_8f2f6d0d, retry contract of 2026-09-02 22:36 RTZ)
from the exact v3 contract artifacts (all QA-verified, contract_review_v3=pass
in t_7ee1d606):

- ECONOMICS_SCORING_CONTRACT_V3.md (finance, t_a92701e0)
  sha256 ed5b0848adc421d8adcf06e7c27633d73c179ceb23f060a08c5b342111584bef
- economics_scoring_fixture_v3.json (finance, t_a92701e0)
  sha256 a222cf4370a4d7a0ea372e9592fe49f9caba90c5cac31f1f5bed8f8555f7d79a
- DEMAND_METRIC_SOURCE_CONTRACT_V3.md (research, t_dbb4235b)
  sha256 7922ee61dff8e53811efa5b0df2b39c0842a06bc988aaab1bb5733bf7151e977

Semantics (contract section numbers refer to ECONOMICS_SCORING_CONTRACT_V3):

- pure reducer over a collector-produced snapshot; ``evaluated_at`` is part of
  the snapshot (the collector stamps it) so the reducer stays deterministic
  and content-hashed; the controller never queries runtime stores, live
  databases or secrets (demand contract v3 section 4);
- formula (§3): ``score_rub = (E + A) * confidence * freshness - C`` where
  C = cash + evidence-backed capacity cost is NOT discounted; freshness
  ``f = 2 ** (-oldest_age_days / 30)`` with floor 0.125 at age >= 90 days and
  ``requires_reverification`` beyond 90 days; age is taken over the OLDEST
  mandatory evidence ref;
- candidates are classified (§2) into EXECUTABLE / EVIDENCE_GAP /
  BLOCKED_BUDGET / REJECTED; money is never invented — any missing monetary
  evidence keeps the candidate in EVIDENCE_GAP (§5 rule 1);
- winner (§4) is the argmax of the full deterministic order: max score_rub,
  min total_cost_rub, max confidence, min oldest-ref age, lexicographic min
  source_task_id — exactly one winner or ``no_action``, never chance;
- anti-gaming (§5): double-count guard zeroes the smaller of E/A when both
  are backed by a shared evidence ref (A when equal); avoided-loss A is
  admissible only for gate_removal/risk work and capped at independently
  evidenced loss exposure x event probability over 30 days; one mechanism =
  one candidate (duplicates merge, freshest OLDEST ref wins); selection is by
  RUB score, never ROI (efficiency is diagnostic only, capped at 100); any
  pre-filled ``score_components`` is tampering -> REJECTED;
- budget guardrails (§6): 10 000 RUB per operation and 30 000 RUB per
  calendar month per project (APPROVALS.md) -> BLOCKED_BUDGET, owner required;
- zero-cost (§7): cash_cost_rub = 0 is legal, but capacity cost above zero
  without evidence is EVIDENCE_GAP; zero cost never waives kill/rollback;
- kill (§8): every executable candidate carries a kill criterion object with
  a metric, an observation window and an explicit NONZERO adverse threshold
  (also for C = 0), plus a reversible rollback;
- decision mapping (§11 / demand contract v3 §5): exactly one of
  ``execute_bet`` / ``collect_evidence`` / ``no_action``; at most ONE
  idempotent ``collect_evidence`` recommendation with
  ``execution_eligible=false`` and no invented RUB;
- fixed fleet rule (task body): ``running == 0`` and ``ready == 0`` while a
  revenue-critical ``triage``/``todo`` gate exists is ``ACTIONABLE_IDLE`` and
  is never reported as success (``success`` is a constant ``False``);
- canonical identities (§0): project and board are separate fields; scoring
  exists only for ``recruiter-radar``/``rr-team`` (metric
  ``accepted_evidence_backed_leads_28d``) and ``seo-site``/``seo-site``
  (metric ``successful_organic_calculations_28d``); ``rr-*`` wildcards and
  ``search-utility`` are never accepted; all money is RUB;
- output is a Telegram-only digest payload; the controller never creates,
  promotes, unblocks, archives or deletes tasks and never alters cron/config;
- decisions are content-hashed (``decision_id`` = idempotency key); the
  engine is append-only into the existing events store — an identical repeat
  run writes zero new records and returns the stored decision;
- live input is read-only via the official ``hermes kanban list --json`` CLI
  (no direct kanban database access); canonical boards restricted to
  ``rr-team`` and ``seo-site``.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

CONTROLLER_VERSION = "next-bet-shadow/2.0"
FORMULA_VERSION = "econ-score/v3"
FORMULA_TEXT = "(E + A) * confidence * freshness - total_cost_rub"
MODE = "shadow"
DECISION_PREFIX = "nbc2-"

CANONICAL_BOARDS = frozenset({"rr-team", "seo-site"})
# board -> (project registry key, canonical primary metric id); fixed by the
# owner decision of 2026-09-02 and recorded in DEMAND_METRIC_SOURCE_CONTRACT_V3.
CANONICAL_PAIRS = {
    "rr-team": ("recruiter-radar", "accepted_evidence_backed_leads_28d"),
    "seo-site": ("seo-site", "successful_organic_calculations_28d"),
}
CANONICAL_PROJECTS = frozenset(pair[0] for pair in CANONICAL_PAIRS.values())

# Statuses queried by the live adapter (read-only ``hermes kanban list``).
LIVE_STATUSES = ("todo", "triage", "running", "ready", "blocked")
ACTIONABLE_STATUSES = frozenset({"todo", "triage"})

# Candidate classes (§2).
EXECUTABLE = "EXECUTABLE"
EVIDENCE_GAP = "EVIDENCE_GAP"
BLOCKED_BUDGET = "BLOCKED_BUDGET"
REJECTED = "REJECTED"

# Budget guardrails (§6, APPROVALS.md autonomous authority).
MAX_COST_PER_OP_RUB = 10_000
MAX_MONTHLY_PER_PROJECT_RUB = 30_000

# Freshness (§3): 30-day horizon half-life, floor 0.125 at age >= 90 days.
HORIZON_DAYS = 30.0
FRESHNESS_FLOOR = 0.125
REVERIFICATION_AGE_DAYS = 90.0
# Execute gate: a board metric observation older than the 30-day horizon is
# not fresh (unit-consistent with the scoring horizon; §3).
METRIC_FRESHNESS_DAYS = 30.0
EFFICIENCY_CAP = 100.0

DEFAULT_COLLECTOR_OWNER = "finance"
DEFAULT_COLLECTOR_SQUAD = ("finance", "research")
DEFAULT_FRESHNESS_TARGET_DAYS = 30
# Gap code recorded by DEMAND_METRIC_SOURCE_CONTRACT_V3 §6 while no collector
# snapshot exists for a project.
METRIC_GAP_CODE = "metric_definition_source_value_unprovided"

GATE_REMOVAL_CLASSES = frozenset({"gate_removal", "risk"})

# Static evidence refs for the single collect_evidence recommendation: the
# exact contract artifacts this reducer is derived from.
CONTRACT_EVIDENCE_REFS = (
    "ECONOMICS_SCORING_CONTRACT_V3.md (t_a92701e0, econ-score/v3)",
    "economics_scoring_fixture_v3.json (t_a92701e0)",
    "DEMAND_METRIC_SOURCE_CONTRACT_V3.md (t_dbb4235b, v3.0)",
    "QA contract_review_v3=pass (t_7ee1d606)",
)

Runner = Callable[[list[str]], str]


class ControllerInputError(ValueError):
    """Fail-closed validation error for snapshot or live input."""


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------


def _is_num(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _clean_str(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _round2(value: float) -> float:
    return round(float(value) + 0.0, 2)


def _parse_ts(value: Any, field: str) -> datetime:
    if not _clean_str(value):
        raise ControllerInputError(f"{field} must be a non-empty ISO timestamp")
    raw = str(value).strip()
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ControllerInputError(f"{field} is not a valid ISO timestamp: {raw!r}") from exc
    if parsed.tzinfo is None:
        raise ControllerInputError(f"{field} must carry a UTC offset: {raw!r}")
    return parsed


# --------------------------------------------------------------------------
# input normalization (fail-closed)
# --------------------------------------------------------------------------


def _validate_task(board: str, task: Any) -> dict:
    if not isinstance(task, dict):
        raise ControllerInputError(f"task on board {board} must be an object")
    task_id = _clean_str(task.get("task_id"))
    if not task_id:
        raise ControllerInputError(f"task_id missing on board {board}")
    status = _clean_str(task.get("status"))
    if not status:
        raise ControllerInputError(f"status missing for {task_id}")
    try:
        priority = int(task.get("priority") or 0)
    except (TypeError, ValueError) as exc:
        raise ControllerInputError(f"bad priority for {task_id}") from exc
    return {
        "task_id": task_id,
        "title": str(task.get("title") or ""),
        "board": board,
        "status": status.lower(),
        "priority": priority,
        "assignee": _clean_str(task.get("assignee")),
        "revenue_critical": bool(task.get("revenue_critical")),
        "revenue_project": _clean_str(task.get("revenue_project")),
    }


def _validate_metric(board: str, metric: Any) -> dict:
    if not isinstance(metric, dict):
        raise ControllerInputError(f"metric record for board {board} must be an object")
    value = metric.get("value")
    observed_raw = metric.get("observed_at")
    gap = metric.get("evidence_gap")
    if value is not None and not _is_num(value):
        raise ControllerInputError(f"metric value for board {board} must be a number or null")
    # Nullability invariant (demand contract v3 §2): value and observed_at are
    # null iff evidence_gap is set.
    if (value is None) != (observed_raw is None):
        raise ControllerInputError(f"metric record for board {board} breaks the value/observed_at nullability invariant")
    if (value is None) != (gap is not None):
        raise ControllerInputError(f"metric record for board {board} breaks the evidence_gap nullability invariant")
    if gap is not None and not _clean_str(gap):
        raise ControllerInputError(f"metric evidence_gap for board {board} must be null or a non-empty code")
    observed_at = _parse_ts(observed_raw, f"metric.observed_at for board {board}") if observed_raw is not None else None
    return {
        "value": float(value) if value is not None else None,
        "observed_at": str(observed_raw).strip() if observed_raw is not None else None,
        "observed_at_dt": observed_at,
        "evidence_gap": _clean_str(gap) or None,
    }


def _validate_canonical_board(name: str, raw: dict) -> dict:
    project, metric_id = CANONICAL_PAIRS[name]
    got_project = _clean_str(raw.get("project"))
    if got_project != project:
        raise ControllerInputError(
            f"board {name} must belong to project {project!r} (got {got_project!r}); "
            "project and board are separate fields and canonical pairs are fixed"
        )
    got_metric = _clean_str(raw.get("primary_metric_id"))
    if got_metric != metric_id:
        raise ControllerInputError(f"board {name} must use primary metric {metric_id!r} (got {got_metric!r})")
    if "canonical" in raw and raw.get("canonical") is not True:
        raise ControllerInputError(f"board {name} is canonical; the flag must be true when present")
    if "metric" not in raw:
        raise ControllerInputError(f"board {name} must carry its metric record (demand contract v3 §2)")
    tasks = raw.get("tasks") or []
    if not isinstance(tasks, list):
        raise ControllerInputError(f"board {name} tasks must be a list")
    candidates = raw.get("candidates") or []
    if not isinstance(candidates, list):
        raise ControllerInputError(f"board {name} candidates must be a list")
    for candidate in candidates:
        if not isinstance(candidate, dict) or not _clean_str(candidate.get("source_task_id")):
            raise ControllerInputError(f"candidate on board {name} must be an object with source_task_id")
    return {
        "service": False,
        "project": project,
        "primary_metric_id": metric_id,
        "metric": _validate_metric(name, raw.get("metric")),
        "tasks": [_validate_task(name, task) for task in tasks],
        "candidates": list(candidates),
    }


def _validate_service_board(name: str, raw: dict) -> dict:
    if raw.get("candidates"):
        raise ControllerInputError(f"service board {name} cannot carry scored candidates")
    tasks = raw.get("tasks") or []
    if not isinstance(tasks, list):
        raise ControllerInputError(f"service board {name} tasks must be a list")
    return {
        "service": True,
        "project": _clean_str(raw.get("project")),
        "primary_metric_id": None,
        "metric": None,
        "tasks": [_validate_task(name, task) for task in tasks],
        "candidates": [],
    }


def _validate_budget(budget: Any) -> dict:
    if not isinstance(budget, dict):
        raise ControllerInputError("budget must be an object")
    normalized: dict[str, dict] = {}
    for project, entry in budget.items():
        if project not in CANONICAL_PROJECTS:
            raise ControllerInputError(f"budget project {project!r} is not a registered canonical project")
        if not isinstance(entry, dict):
            raise ControllerInputError(f"budget entry for {project} must be an object")
        spend = entry.get("month_to_date_spend_rub", 0)
        if not _is_num(spend) or spend < 0:
            raise ControllerInputError(f"budget month_to_date_spend_rub for {project} must be a number >= 0")
        normalized[project] = {
            "month": _clean_str(entry.get("month")),
            "month_to_date_spend_rub": float(spend),
        }
    return normalized


def _validate_collectors(collectors: Any) -> dict:
    defaults = {
        "owner": DEFAULT_COLLECTOR_OWNER,
        "squad": list(DEFAULT_COLLECTOR_SQUAD),
        "freshness_target_days": DEFAULT_FRESHNESS_TARGET_DAYS,
    }
    if collectors is None:
        return defaults
    if not isinstance(collectors, dict):
        raise ControllerInputError("collectors must be an object")
    owner = _clean_str(collectors.get("owner")) or defaults["owner"]
    squad_raw = collectors.get("squad")
    if squad_raw is not None:
        if not isinstance(squad_raw, list) or not all(_clean_str(item) for item in squad_raw):
            raise ControllerInputError("collectors.squad must be a list of non-empty strings")
        defaults["squad"] = [_clean_str(item) for item in squad_raw]
    days = collectors.get("freshness_target_days")
    if days is not None:
        if not _is_num(days) or days <= 0:
            raise ControllerInputError("collectors.freshness_target_days must be a positive number")
        defaults["freshness_target_days"] = int(days)
    defaults["owner"] = owner
    return defaults


def _validate_snapshot(snapshot: Any) -> dict:
    if not isinstance(snapshot, dict):
        raise ControllerInputError("snapshot must be an object")
    evaluated_at_raw = snapshot.get("evaluated_at")
    evaluated_at = _parse_ts(evaluated_at_raw, "evaluated_at")
    boards_raw = snapshot.get("boards")
    if boards_raw is None:
        boards_raw = {}
    if not isinstance(boards_raw, dict):
        raise ControllerInputError("boards must be an object")
    boards: dict[str, dict] = {}
    for name, raw in boards_raw.items():
        name = str(name)
        if not isinstance(raw, dict):
            raise ControllerInputError(f"board {name} must be an object")
        if name in CANONICAL_BOARDS:
            boards[name] = _validate_canonical_board(name, raw)
        elif raw.get("service") is True:
            boards[name] = _validate_service_board(name, raw)
        else:
            raise ControllerInputError(
                f"board {name!r} is not canonical ({sorted(CANONICAL_BOARDS)}) and not marked service"
            )
    economics_state = snapshot.get("economics_state")
    if economics_state is not None and not isinstance(economics_state, dict):
        raise ControllerInputError("economics_state must be an object")
    return {
        "evaluated_at": str(evaluated_at_raw).strip(),
        "evaluated_at_dt": evaluated_at,
        "boards": boards,
        "budget": _validate_budget(snapshot.get("budget")),
        "economics_state": dict(economics_state) if isinstance(economics_state, dict) else None,
        "collectors": _validate_collectors(snapshot.get("collectors")),
    }


# --------------------------------------------------------------------------
# live adapter (read-only via the official kanban CLI)
# --------------------------------------------------------------------------


def _default_runner(argv: list[str]) -> str:
    completed = subprocess.run(
        ["hermes", *argv], capture_output=True, text=True, check=False, timeout=120
    )
    if completed.returncode != 0:
        raise ControllerInputError(f"kanban CLI failed: {completed.stderr.strip()[:200]}")
    return completed.stdout


def task_from_row(board: str, row: dict) -> dict:
    """Normalize one ``kanban list --json`` row into a fleet-state task dict.

    Task bodies may carry the revenue marker::

        revenue_gate: <project registry key>

    which marks the task revenue-critical. Scoring inputs (proposals) are
    collector-produced snapshot data, never task-body markers.
    """
    if not isinstance(row, dict):
        raise ControllerInputError("task row must be an object")
    task_id = _clean_str(row.get("id") or row.get("task_id"))
    if not task_id:
        raise ControllerInputError("task_id missing")
    revenue_project = ""
    for raw_line in str(row.get("body") or "").splitlines():
        match = re.match(r"^revenue_gate:\s*(.+)$", raw_line.strip())
        if match:
            revenue_project = match.group(1).strip()
            break
    try:
        priority = int(row.get("priority") or 0)
    except (TypeError, ValueError) as exc:
        raise ControllerInputError(f"bad priority for {task_id}") from exc
    return {
        "task_id": task_id,
        "title": str(row.get("title") or ""),
        "board": board,
        "status": _clean_str(row.get("status")).lower(),
        "priority": priority,
        "assignee": _clean_str(row.get("assignee")),
        "revenue_critical": bool(revenue_project),
        "revenue_project": revenue_project,
    }


def load_live_snapshot(boards: list[str], runner: Runner | None = None) -> dict:
    """Build the v3 snapshot read-only from the official kanban CLI.

    The adapter is a collector: it stamps ``evaluated_at`` with the current
    UTC time. Fleet-state rows come from the CLI; metric records mirror
    DEMAND_METRIC_SOURCE_CONTRACT_V3 §6 (no collector snapshot exists yet, so
    value/observed_at stay null under the stable gap code) and no candidates
    are invented.
    """
    run = runner or _default_runner
    unknown = [board for board in boards if board not in CANONICAL_BOARDS]
    if not boards or unknown:
        raise ControllerInputError(f"boards must be a non-empty subset of {sorted(CANONICAL_BOARDS)}")
    collected: dict[str, dict] = {}
    for board in boards:
        tasks: list[dict] = []
        for status in LIVE_STATUSES:
            argv = ["kanban", "--board", board, "list", "--status", status, "--json"]
            stdout = run(argv)
            try:
                rows = json.loads(stdout)
            except json.JSONDecodeError as exc:
                raise ControllerInputError(f"non-JSON kanban output for {board}/{status}") from exc
            if not isinstance(rows, list):
                raise ControllerInputError(f"kanban output must be a list for {board}/{status}")
            tasks.extend(task_from_row(board, row) for row in rows)
        project, metric_id = CANONICAL_PAIRS[board]
        collected[board] = {
            "project": project,
            "canonical": True,
            "primary_metric_id": metric_id,
            "metric": {"value": None, "observed_at": None, "evidence_gap": METRIC_GAP_CODE},
            "tasks": tasks,
            "candidates": [],
        }
    return {
        "evaluated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "boards": collected,
        "budget": {},
        "economics_state": {
            "evidence_gap": True,
            "reasons": ["no collector snapshot exists for either project (DEMAND_METRIC_SOURCE_CONTRACT_V3 §7.3)"],
        },
    }


def load_snapshot_file(path: str) -> dict:
    """Load and validate a snapshot JSON file (deterministic input)."""
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ControllerInputError(f"cannot read snapshot: {exc}") from exc
    try:
        snapshot = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ControllerInputError(f"snapshot is not valid JSON: {exc}") from exc
    _validate_snapshot(snapshot)
    return snapshot


# --------------------------------------------------------------------------
# candidate classification and scoring (econ-score/v3)
# --------------------------------------------------------------------------


def _candidate_row(candidate: dict, board: str, **fields: Any) -> dict:
    row = {
        "source_task_id": _clean_str(candidate.get("source_task_id")),
        "board": board,
        "project": _clean_str(candidate.get("project")),
        "mechanism_id": _clean_str(candidate.get("mechanism_id")) or None,
        "class": REJECTED,
        "reason": None,
        "score_rub": None,
        "score_components": {},
        "missing_fields": [],
        "execution_gate": None,
        "dedup": None,
        "_raw_score": None,
        "_total_cost_rub": None,
        "_confidence": None,
        "_oldest_age_days": None,
    }
    row.update(fields)
    return row


def _parse_refs(candidate: dict, evaluated_at: datetime) -> tuple[list[dict] | None, str | None]:
    refs = candidate.get("evidence_refs")
    if refs is None:
        return [], None
    if not isinstance(refs, list):
        return None, "evidence_refs_invalid"
    parsed: list[dict] = []
    for ref in refs:
        if not isinstance(ref, dict) or not _clean_str(ref.get("ref")):
            return None, "evidence_ref_invalid"
        raw_ts = ref.get("observed_at")
        try:
            observed = _parse_ts(raw_ts, "evidence_ref.observed_at")
        except ControllerInputError:
            return None, "evidence_ref_invalid"
        if observed > evaluated_at:
            return None, "evidence_ref_future_dated"
        age_days = (evaluated_at - observed).total_seconds() / 86400.0
        parsed.append(
            {
                "ref": _clean_str(ref.get("ref")),
                "author": _clean_str(ref.get("author")),
                "authority_rank": ref.get("authority_rank"),
                "age_days": age_days,
            }
        )
    return parsed, None


def _execution_fields(candidate: dict) -> list[str]:
    """Missing execution fields (§1/§8: owner, squad, hypothesis, kill, rollback)."""
    missing: list[str] = []
    if not _clean_str(candidate.get("owner")):
        missing.append("owner")
    squad = candidate.get("squad")
    squad_ok = (
        (isinstance(squad, list) and any(_clean_str(item) for item in squad))
        or _clean_str(squad)
    )
    if not squad_ok:
        missing.append("squad")
    if not _clean_str(candidate.get("hypothesis")):
        missing.append("hypothesis")
    if not _clean_str(candidate.get("rollback")):
        missing.append("rollback")
    kill = candidate.get("kill_criterion")
    kill_ok = isinstance(kill, dict) and _clean_str(kill.get("metric"))
    if kill_ok:
        window = kill.get("window_days")
        threshold = kill.get("adverse_threshold_relative")
        kill_ok = _is_num(window) and window > 0 and _is_num(threshold) and threshold > 0
    if not kill_ok:
        # §8: the kill criterion needs a metric, a window and an explicit
        # NONZERO adverse threshold — also (and especially) for C = 0.
        missing.append("kill_criterion(metric,window_days,adverse_threshold_relative>0)")
    return missing


def _classify_candidate(
    board_name: str,
    entry: dict,
    candidate: dict,
    evaluated_at: datetime,
    budget: dict,
    economics_gap: bool,
) -> dict:
    """Classify one proposal per econ-score/v3 §1–§8. Never raises: malformed
    candidates become REJECTED/EVIDENCE_GAP audit rows (snapshot-structural
    problems are rejected earlier by validation)."""

    def rejected(reason: str, missing: list[str] | None = None) -> dict:
        return _candidate_row(candidate, board_name, **{"class": REJECTED, "reason": reason, "missing_fields": missing or []})

    def gap(reason: str, missing: list[str] | None = None) -> dict:
        return _candidate_row(candidate, board_name, **{"class": EVIDENCE_GAP, "reason": reason, "missing_fields": missing or []})

    project = _clean_str(candidate.get("project"))
    board = _clean_str(candidate.get("board")) or board_name
    expected_project, expected_metric = CANONICAL_PAIRS.get(board_name, ("", ""))
    if board != board_name or project != expected_project or (project, board) not in {
        (p, b) for b, (p, _m) in CANONICAL_PAIRS.items()
    }:
        return rejected("unknown_project_board")
    metric_id = _clean_str(candidate.get("metric_id"))
    if metric_id != expected_metric:
        return rejected("unknown_metric")
    if candidate.get("score_components"):
        # §5 rule 7: manual score_components edits are tampering.
        return rejected("score_components_tampered")
    mechanism_id = _clean_str(candidate.get("mechanism_id"))
    if not mechanism_id:
        return rejected("mechanism_id_missing")

    confidence = candidate.get("confidence_0_1")
    if not _is_num(confidence) or confidence < 0 or confidence > 1:
        return rejected("confidence_out_of_range")

    cash = candidate.get("cash_cost_rub")
    if not _is_num(cash) or cash < 0:
        return rejected("cash_cost_invalid")
    capacity = candidate.get("capacity_cost_rub")
    if capacity is not None and (not _is_num(capacity) or capacity < 0):
        return rejected("capacity_cost_invalid")
    total = candidate.get("total_cost_rub")
    if not _is_num(total) or total < 0:
        return rejected("total_cost_invalid")
    expected_total = float(cash) + (float(capacity) if capacity is not None else 0.0)
    if abs(float(total) - expected_total) > 1e-9:
        return rejected("total_cost_mismatch")

    profit = candidate.get("expected_profit_rub_30d")
    if profit is not None and (not _is_num(profit) or profit < 0):
        return rejected("expected_profit_invalid")
    avoided = candidate.get("avoided_loss_rub_30d")
    if avoided is not None and (not _is_num(avoided) or avoided < 0):
        return rejected("avoided_loss_invalid")
    work_class = _clean_str(candidate.get("work_class")) or "metric"
    if avoided is not None and work_class not in GATE_REMOVAL_CLASSES:
        # §5 rule 3: avoided loss only for gate_removal/risk work.
        return rejected("avoided_loss_not_allowed")

    refs, ref_error = _parse_refs(candidate, evaluated_at)
    if ref_error:
        return rejected(ref_error)

    if profit is None and avoided is None:
        # §3: unknown EV is never eligible; the controller invents nothing.
        return gap("unknown_ev", ["expected_profit_rub_30d", "avoided_loss_rub_30d"])
    if (profit is not None or avoided is not None) and not refs:
        return gap("money_without_evidence", ["evidence_refs"])
    if capacity is not None and float(capacity) > 0 and not refs:
        # §7: capacity cost without an evidenced rate ledger is a gap.
        return gap("capacity_cost_without_evidence", ["capacity_cost_rub evidence"])
    if any(not (isinstance(ref["authority_rank"], int) and 1 <= ref["authority_rank"] <= 4) for ref in refs):
        # §2(г): evidence of insufficient authority (demand contract v3 §3).
        return gap("insufficient_authority", ["evidence_refs.authority_rank"])

    avoided_cap = None
    if avoided is not None:
        exposure = candidate.get("loss_exposure_rub")
        probability = candidate.get("event_probability_30d")
        if exposure is None or probability is None:
            return gap("avoided_loss_cap_unproven", ["loss_exposure_rub", "event_probability_30d"])
        if not _is_num(exposure) or exposure < 0 or not _is_num(probability) or probability < 0 or probability > 1:
            return rejected("avoided_loss_cap_invalid")
        avoided_cap = float(exposure) * float(probability)
        if float(avoided) > avoided_cap + 1e-9:
            # §5 rule 3: A capped at independently evidenced exposure x probability.
            return rejected("avoided_loss_cap_exceeded")

    # §5 rule 2: double-count guard — E and A must rest on different mechanisms.
    profit_eff = float(profit) if profit is not None else 0.0
    avoided_eff = float(avoided) if avoided is not None else 0.0
    double_count_zeroed = None
    if profit is not None and avoided is not None:
        profit_refs = {_clean_str(ref) for ref in (candidate.get("evidence_profit_refs") or [])}
        loss_refs = {_clean_str(ref) for ref in (candidate.get("evidence_loss_refs") or [])}
        if profit_refs & loss_refs:
            if profit_eff <= avoided_eff:
                if profit_eff == avoided_eff:
                    avoided_eff, double_count_zeroed = 0.0, "avoided_loss"
                else:
                    profit_eff, double_count_zeroed = 0.0, "expected_profit"
            else:
                avoided_eff, double_count_zeroed = 0.0, "avoided_loss"

    oldest_age = max((ref["age_days"] for ref in refs), default=None)
    freshness = 1.0
    requires_reverification = False
    if oldest_age is not None:
        freshness = max(FRESHNESS_FLOOR, 2.0 ** (-(oldest_age / HORIZON_DAYS)))
        requires_reverification = oldest_age > REVERIFICATION_AGE_DAYS

    total_f = float(total)
    score = (profit_eff + avoided_eff) * float(confidence) * freshness - total_f

    components = {
        "formula": FORMULA_TEXT,
        "formula_version": FORMULA_VERSION,
        "E": float(profit) if profit is not None else None,
        "A": float(avoided) if avoided is not None else None,
        "E_effective": _round2(profit_eff),
        "A_effective": _round2(avoided_eff),
        "confidence": float(confidence),
        "oldest_age_days": _round2(oldest_age) if oldest_age is not None else None,
        "freshness_f": round(freshness, 6),
        "requires_reverification": requires_reverification,
        "cash_cost_rub": float(cash),
        "capacity_cost_rub": float(capacity) if capacity is not None else None,
        "total_cost_rub": total_f,
        "double_count_zeroed": double_count_zeroed,
        "avoided_loss_cap_rub": _round2(avoided_cap) if avoided_cap is not None else None,
        # §5 rule 4: diagnostic only, capped, never used for ranking.
        "efficiency_capped_100": min(_round2(score / max(total_f, 1.0)), EFFICIENCY_CAP),
        "score_rub": _round2(score),
    }

    missing_execution = _execution_fields(candidate)
    if missing_execution:
        return _candidate_row(
            candidate,
            board_name,
            **{
                "class": EVIDENCE_GAP,
                "reason": "execution_fields_incomplete",
                "missing_fields": missing_execution,
                "score_rub": _round2(score),
                "score_components": components,
                "_raw_score": score,
                "_total_cost_rub": total_f,
                "_confidence": float(confidence),
                "_oldest_age_days": oldest_age,
            },
        )

    spend = budget.get(project, {}).get("month_to_date_spend_rub", 0.0)
    if total_f > MAX_COST_PER_OP_RUB:
        return _candidate_row(
            candidate,
            board_name,
            **{
                "class": BLOCKED_BUDGET,
                "reason": "budget_op_limit_exceeded",
                "score_rub": _round2(score),
                "score_components": components,
                "_raw_score": score,
                "_total_cost_rub": total_f,
                "_confidence": float(confidence),
                "_oldest_age_days": oldest_age,
            },
        )
    if spend + total_f > MAX_MONTHLY_PER_PROJECT_RUB:
        return _candidate_row(
            candidate,
            board_name,
            **{
                "class": BLOCKED_BUDGET,
                "reason": "budget_month_limit_exceeded",
                "score_rub": _round2(score),
                "score_components": components,
                "_raw_score": score,
                "_total_cost_rub": total_f,
                "_confidence": float(confidence),
                "_oldest_age_days": oldest_age,
            },
        )

    # Execute gate (company design decision 2026-09-02): execute_bet only when
    # the board metric snapshot and the finance inputs are fresh/authoritative/
    # non-gap.
    metric = entry["metric"]
    gate = "pass"
    if metric["value"] is None:
        gate = f"metric_gap:{metric['evidence_gap']}"
    else:
        metric_age = (evaluated_at - metric["observed_at_dt"]).total_seconds() / 86400.0
        if metric_age > METRIC_FRESHNESS_DAYS:
            gate = "metric_stale"
        elif economics_gap:
            gate = "economics_gap"

    return _candidate_row(
        candidate,
        board_name,
        **{
            "class": EXECUTABLE,
            "reason": None,
            "score_rub": _round2(score),
            "score_components": components,
            "execution_gate": gate,
            "_raw_score": score,
            "_total_cost_rub": total_f,
            "_confidence": float(confidence),
            "_oldest_age_days": oldest_age,
        },
    )


def _public_audit_row(row: dict) -> dict:
    return {
        "source_task_id": row["source_task_id"],
        "board": row["board"],
        "project": row["project"],
        "mechanism_id": row["mechanism_id"],
        "class": row["class"],
        "reason": row["reason"],
        "score_rub": row["score_rub"],
        "score_components": row["score_components"],
        "missing_fields": row["missing_fields"],
        "execution_gate": row["execution_gate"],
        "dedup": row["dedup"],
    }


# --------------------------------------------------------------------------
# pure reducer
# --------------------------------------------------------------------------


def _economics_state_gap(clean: dict) -> bool:
    economics = clean.get("economics_state")
    if not economics:
        return False
    if bool(economics.get("evidence_gap")):
        return True
    return bool(economics.get("evidence_gap_reasons"))


def _collect_missing_fields(clean: dict, rows: list[dict], evaluated_at: datetime) -> list[str]:
    """Deterministic list of missing-evidence fields for the single
    collect_evidence recommendation (§11)."""
    fields: list[str] = []
    for board_name in sorted(clean["boards"]):
        entry = clean["boards"][board_name]
        if entry["service"]:
            continue
        metric = entry["metric"]
        if metric["value"] is None:
            fields.append(
                f"{board_name}: primary metric {entry['primary_metric_id']} "
                f"definition/unit/source/value/observed_at (evidence_gap={metric['evidence_gap']})"
            )
        else:
            age = (evaluated_at - metric["observed_at_dt"]).total_seconds() / 86400.0
            if age > METRIC_FRESHNESS_DAYS:
                fields.append(
                    f"{board_name}: primary metric {entry['primary_metric_id']} fresh observation "
                    f"(current age {_round2(age)}d > {int(METRIC_FRESHNESS_DAYS)}d horizon)"
                )
    economics = clean.get("economics_state")
    if economics and _economics_state_gap(clean):
        reasons = economics.get("reasons") or economics.get("evidence_gap_reasons") or []
        if reasons:
            fields.extend(f"economics_state: {reason}" for reason in reasons)
        else:
            fields.append("economics_state: evidence_gap")
    for row in sorted(rows, key=lambda r: (r["board"], r["source_task_id"])):
        if row["class"] == EVIDENCE_GAP:
            missing = ", ".join(row["missing_fields"]) if row["missing_fields"] else row["reason"]
            fields.append(f"{row['board']}:{row['source_task_id']}: {row['reason']} ({missing})")
    return fields


def _digest(state: str, decision_type: str, reason: str | None, decision: dict) -> dict:
    parts = [f"[shadow mode] state={state} decision={decision_type} formula={FORMULA_VERSION}"]
    candidate = decision.get("candidate")
    if decision_type == "execute_bet" and candidate is not None:
        score = candidate["score"]
        parts += [
            f"bet={candidate['source_task_id']} project={candidate['project']} board={candidate['board']}",
            f"metric={candidate['metric_id']}",
            f"score_rub={score['score_rub']:g} total_cost_rub={score['total_cost_rub']:g}",
            f"owner={candidate['owner']} squad={','.join(candidate['squad'])}",
            f"hypothesis={candidate['hypothesis']}",
            f"expected_impact={candidate['expected_impact']}",
            f"kill={candidate['kill_criterion']['metric']} window={candidate['kill_criterion']['window_days']}d "
            f"threshold={candidate['kill_criterion']['adverse_threshold_relative']}",
            f"rollback={candidate['rollback']}",
        ]
    elif decision_type == "collect_evidence" and candidate is not None:
        parts += [
            f"collector={candidate['collector_owner']} squad={','.join(candidate['collector_squad'])}",
            f"missing_fields={len(candidate['missing_fields'])}",
            f"freshness_target_days={candidate['freshness_target_days']}",
            "execution_eligible=false",
        ]
    elif reason:
        parts.append(f"reason={reason}")
    return {"channel": "telegram", "text": "\n".join(parts)}


def _canonical_hash(payload: dict) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def reduce(snapshot: dict) -> dict:
    """Pure reducer: v3 snapshot -> shadow decision dict."""
    clean = _validate_snapshot(snapshot)
    evaluated_at: datetime = clean["evaluated_at_dt"]
    boards = clean["boards"]
    budget = clean["budget"]
    economics_gap = _economics_state_gap(clean)

    all_tasks = [task for entry in boards.values() for task in entry["tasks"]]
    running = sum(1 for task in all_tasks if task["status"] == "running")
    ready = sum(1 for task in all_tasks if task["status"] == "ready")
    actionable = [
        task
        for task in all_tasks
        if task["revenue_critical"] and task["status"] in ACTIONABLE_STATUSES
    ]
    blocked_gates = sum(1 for task in all_tasks if task["revenue_critical"] and task["status"] == "blocked")
    counts = {
        "running": running,
        "ready": ready,
        "actionable_revenue_gates": len(actionable),
        "blocked_revenue_gates": blocked_gates,
    }

    if running:
        state = "RUNNING"
    elif ready:
        state = "READY_QUEUE"
    elif not actionable:
        state = "IDLE_NO_GATES"
    else:
        state = "ACTIONABLE_IDLE"

    # Audit every candidate deterministically (sorted board order).
    rows: list[dict] = []
    for board_name in sorted(boards):
        entry = boards[board_name]
        for candidate in sorted(entry["candidates"], key=lambda c: _clean_str(c.get("source_task_id"))):
            rows.append(_classify_candidate(board_name, entry, candidate, evaluated_at, budget, economics_gap))

    decision_type = "no_action"
    reason: str | None = None
    candidate_payload: dict | None = None
    winner_source_task_id: str | None = None

    if state == "RUNNING":
        reason = "fleet_busy_running"
    elif state == "READY_QUEUE":
        reason = "ready_work_exists"
    elif state == "IDLE_NO_GATES":
        # No revenue-critical triage/todo gate exists: there is no next bet to
        # pick and no gate to unblock, so no evidence step is actionable.
        reason = "no_actionable_revenue_gate"
    else:
        eligible = [
            row
            for row in rows
            if row["class"] == EXECUTABLE and row["execution_gate"] == "pass" and row["_raw_score"] is not None and row["_raw_score"] > 0
        ]
        # §5 rule 6: one mechanism = one candidate; keep the freshest OLDEST ref.
        by_mechanism: dict[str, dict] = {}
        for row in sorted(eligible, key=lambda r: (r["_oldest_age_days"], r["source_task_id"])):
            keeper = by_mechanism.setdefault(row["mechanism_id"], row)
            if keeper is not row:
                row["dedup"] = f"merged_into:{keeper['source_task_id']}"
        eligible = list(by_mechanism.values())
        # §4 full deterministic order: exactly one winner or none.
        eligible.sort(
            key=lambda r: (
                -r["_raw_score"],
                r["_total_cost_rub"],
                -r["_confidence"],
                r["_oldest_age_days"],
                r["source_task_id"],
            )
        )
        if eligible:
            winner = eligible[0]
            decision_type = "execute_bet"
            winner_source_task_id = winner["source_task_id"]
            source = next(
                cand
                for board_name in sorted(boards)
                for cand in boards[board_name]["candidates"]
                if _clean_str(cand.get("source_task_id")) == winner["source_task_id"]
            )
            squad_raw = source.get("squad")
            squad = (
                [_clean_str(item) for item in squad_raw if _clean_str(item)]
                if isinstance(squad_raw, list)
                else [part.strip() for part in str(squad_raw).split(",") if part.strip()]
            )
            kill = dict(source.get("kill_criterion") or {})
            expected_impact = _clean_str(source.get("expected_impact")) or (
                f"E_effective={winner['score_components']['E_effective']:g} RUB/30d, "
                f"A_effective={winner['score_components']['A_effective']:g} RUB/30d"
            )
            candidate_payload = {
                "source_task_id": winner["source_task_id"],
                "project": winner["project"],
                "board": winner["board"],
                "metric_id": _clean_str(source.get("metric_id")),
                "mechanism_id": winner["mechanism_id"],
                "owner": _clean_str(source.get("owner")),
                "squad": squad,
                "hypothesis": _clean_str(source.get("hypothesis")),
                "expected_impact": expected_impact,
                "kill_criterion": {
                    "metric": _clean_str(kill.get("metric")),
                    "window_days": kill.get("window_days"),
                    "adverse_threshold_relative": kill.get("adverse_threshold_relative"),
                },
                "rollback": _clean_str(source.get("rollback")),
                "evidence_refs": list(source.get("evidence_refs") or []),
                "score": winner["score_components"],
            }
        else:
            missing = _collect_missing_fields(clean, rows, evaluated_at)
            if missing:
                decision_type = "collect_evidence"
                collectors = clean["collectors"]
                candidate_payload = {
                    "priority_reason": (
                        f"no eligible EXECUTABLE candidate; one deterministic evidence step "
                        f"aggregates {len(missing)} missing field(s) across canonical boards"
                    ),
                    "missing_fields": missing,
                    "collector_owner": collectors["owner"],
                    "collector_squad": list(collectors["squad"]),
                    "freshness_target_days": collectors["freshness_target_days"],
                    "kill_criterion": (
                        f"if evidence collection cannot produce authoritative values within "
                        f"{collectors['freshness_target_days']} days, keep decision_type=collect_evidence "
                        "and escalate scope to company"
                    ),
                    "rollback": "No state change; shadow controller is read-only.",
                    "evidence_refs": list(CONTRACT_EVIDENCE_REFS),
                    # No invented RUB: an evidence recommendation carries no money figure.
                    "score": {"formula": None, "value": None},
                }
            elif not rows:
                reason = "no_candidates"
            else:
                reason = "no_eligible_candidate"

    hash_payload = {
        "v": CONTROLLER_VERSION,
        "formula": FORMULA_VERSION,
        "evaluated_at": clean["evaluated_at"],
        "boards": {
            board_name: {
                "tasks": sorted(entry["tasks"], key=lambda t: t["task_id"]),
                "candidates": sorted(entry["candidates"], key=lambda c: _clean_str(c.get("source_task_id"))),
                "metric": None if entry["metric"] is None else {
                    "value": entry["metric"]["value"],
                    "observed_at": entry["metric"]["observed_at"],
                    "evidence_gap": entry["metric"]["evidence_gap"],
                },
                "project": entry["project"],
                "primary_metric_id": entry["primary_metric_id"],
                "service": entry["service"],
            }
            for board_name, entry in boards.items()
        },
        "budget": budget,
        "economics_state": clean.get("economics_state"),
        "collectors": clean["collectors"],
    }
    inputs_hash = _canonical_hash(hash_payload)
    decision_id = DECISION_PREFIX + inputs_hash[:32]

    if decision_type == "collect_evidence" and candidate_payload is not None:
        candidate_payload = {"idempotency_key": decision_id, **candidate_payload}

    projects_in_budget = sorted(CANONICAL_PROJECTS | set(budget))
    default_month = evaluated_at.strftime("%Y-%m")
    budget_snapshot = {
        project: {
            "month": budget.get(project, {}).get("month") or default_month,
            "month_to_date_spend_rub": budget.get(project, {}).get("month_to_date_spend_rub", 0.0),
            "limits": {"per_op_rub": MAX_COST_PER_OP_RUB, "monthly_per_project_rub": MAX_MONTHLY_PER_PROJECT_RUB},
        }
        for project in projects_in_budget
    }

    metric_inputs = {}
    for board_name in sorted(boards):
        entry = boards[board_name]
        if entry["service"]:
            continue
        metric = entry["metric"]
        if metric["value"] is None:
            metric_inputs[board_name] = f"gap:{metric['evidence_gap']}"
        else:
            age = (evaluated_at - metric["observed_at_dt"]).total_seconds() / 86400.0
            metric_inputs[board_name] = "fresh" if age <= METRIC_FRESHNESS_DAYS else f"stale:{_round2(age)}d"

    decision: dict[str, Any] = {
        "controller_version": CONTROLLER_VERSION,
        "formula_version": FORMULA_VERSION,
        "mode": MODE,
        "success": False,
        "mutation_ops": [],
        "decision_id": decision_id,
        "idempotency_key": decision_id,
        "state": state,
        "decision_type": decision_type,
        "execution_eligible": decision_type == "execute_bet",
        "reason": reason,
        "counts": counts,
        "evaluated_at": clean["evaluated_at"],
        "inputs": {
            "metric": metric_inputs,
            "economics_state": "gap" if economics_gap else "ok",
            "candidates_total": len(rows),
        },
        "audit": {
            "formula_version": FORMULA_VERSION,
            "evaluated_at": clean["evaluated_at"],
            "boards": sorted(boards),
            "candidates": [_public_audit_row(row) for row in rows],
            "winner_source_task_id": winner_source_task_id,
            "budget_snapshot": budget_snapshot,
            "inputs_hash": inputs_hash,
        },
        "candidate": candidate_payload,
        "canonical_boards": sorted(CANONICAL_BOARDS),
    }
    if decision_type == "no_action" and rows:
        decision["candidate_reasons"] = [
            {"source_task_id": row["source_task_id"], "board": row["board"], "class": row["class"], "reason": row["reason"]}
            for row in rows
        ]
    decision["digest"] = _digest(state, decision_type, reason, decision)
    return decision


# --------------------------------------------------------------------------
# engine: append-only persistence over the existing events store
# --------------------------------------------------------------------------


class ControllerEngine:
    """Runs the reducer and records decisions idempotently in the store.

    The engine only ever INSERT OR IGNOREs one event row of kind
    ``controller_decision``; an identical repeat run writes zero new records
    and returns the stored decision. It never creates, promotes, unblocks,
    archives or deletes tasks, and never alters cron or config.
    """

    KIND = "controller_decision"

    def __init__(self, store: Any) -> None:
        self.store = store

    def _stored_payload(self, event_id: str) -> dict | None:
        with self.store.connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM events WHERE event_id=? AND kind=?",
                (event_id, self.KIND),
            ).fetchone()
        if row is None:
            return None
        try:
            payload = json.loads(row[0])
        except (json.JSONDecodeError, TypeError):
            return None
        return payload if isinstance(payload, dict) else None

    def run(self, snapshot: dict, now: str = "") -> dict:
        decision = reduce(snapshot)
        if now:
            decision["evaluated_at"] = str(now)
        event_id = f"controller-{decision['decision_id']}"
        inserted = self.store.record_event(
            event_id=event_id,
            correlation_id=event_id,
            task_id=None,
            kind=self.KIND,
            payload=decision,
            significant=False,
        )
        if inserted:
            return dict(decision, duplicate=False)
        stored = self._stored_payload(event_id)
        if stored is None:
            # The row exists but its payload is unreadable: still a repeat,
            # return the freshly reduced decision marked as duplicate.
            return dict(decision, duplicate=True)
        return dict(stored, duplicate=True)
