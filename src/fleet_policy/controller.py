"""Company OS deterministic next-bet controller — SHADOW mode v1.

Scope (task t_8f2f6d0d, company design decision on the card 2026-09-02,
verdict artifact t_3594091b section 5.3/7):

- pure, order-free reducer over a board snapshot
  (``{"boards": {board: [task, ...]}, "metric": {...}, "finance": {...}}``);
- fixed rule: ``running == 0`` and ``ready == 0`` while a revenue-critical
  ``triage``/``todo`` gate exists is ``ACTIONABLE_IDLE`` and is never
  reported as success (``success`` is a constant ``False`` in v1);
- ``decision_type=execute_bet`` only when BOTH metric and finance inputs are
  fresh/authoritative/non-gap AND the candidate effort is known
  (``effort_known`` true) AND the proposal carries owner/squad/kill/rollback;
- otherwise at most ONE ``collect_evidence`` recommendation for the single
  deterministic highest-priority missing-evidence step marked by the input
  (``execution_eligible=false``, missing fields, collector owner/squad,
  freshness target, kill/rollback, evidence refs, no invented RUB);
- ties (equal bet score or equal best evidence priority) resolve to
  ``no_action`` with a deterministic reason; superseded/blocked/duplicate
  lanes are never candidates and stay untouched;
- output is a Telegram-only digest payload; no task/cron/config mutation;
- decisions are content-hashed: ``decision_id`` equals the idempotency key;
  the engine is append-only into the existing events store — an identical
  repeat run writes zero new records and returns the stored decision;
- live input is read-only via the official ``hermes kanban list --json``
  CLI (no direct kanban database access); canonical boards are restricted
  to ``rr-team`` and ``seo-site`` (never ``rr-*`` or ``search-utility``).

Money values are never invented: ``cost_rub`` on a bet candidate is the
declared figure from the input scores, and an evidence recommendation
carries no money figure at all. Unknown effort keeps
``execution_eligible=false`` (cost means cash plus evidence-backed
opportunity cost, so unknown effort is not executable).
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Callable

CONTROLLER_VERSION = "next-bet-shadow/1.0"
MODE = "shadow"
CANONICAL_BOARDS = frozenset({"rr-team", "seo-site"})
# Statuses queried by the live adapter (read-only ``hermes kanban list``).
LIVE_STATUSES = ("todo", "triage", "running", "ready", "blocked")
ACTIONABLE_STATUSES = frozenset({"todo", "triage"})
FRESH_INPUT_STATUS = "fresh"
BET_SCORE_KEYS = ("metric_impact", "gate_removal", "confidence", "cost_rub")

Runner = Callable[[list[str]], str]


class ControllerInputError(ValueError):
    """Fail-closed validation error for snapshot or live input."""


# --------------------------------------------------------------------------
# input normalization
# --------------------------------------------------------------------------


def _is_num(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _clean_str(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def task_from_row(board: str, row: dict) -> dict:
    """Normalize one ``kanban list --json`` row into a task dict.

    Task bodies carry the controller markers::

        revenue_gate: seo-site
        effort_known: false
        bet_score: metric_impact=0 gate_removal=0 confidence=0 cost_rub=0
        evidence_gap: <field> | priority=<int> | owner=<p> | squad=a,b | freshness=<ts>
        bet_hypothesis: ... / bet_impact: ... / bet_kill: ... / bet_rollback: ...
    """
    if not isinstance(row, dict):
        raise ControllerInputError("task row must be an object")
    task_id = _clean_str(row.get("id") or row.get("task_id"))
    if not task_id:
        raise ControllerInputError("task_id missing")
    body = str(row.get("body") or "")
    revenue_project = ""
    effort_known = True
    scores: dict[str, float] = {}
    gaps: list[dict] = []
    proposal: dict[str, str] = {}

    for raw_line in body.splitlines():
        line = raw_line.strip()
        match = re.match(r"^revenue_gate:\s*(.+)$", line)
        if match:
            revenue_project = match.group(1).strip()
            continue
        match = re.match(r"^effort_known:\s*(true|false)$", line, re.IGNORECASE)
        if match:
            effort_known = match.group(1).lower() == "true"
            continue
        match = re.match(r"^bet_score:\s*(.+)$", line)
        if match:
            for part in match.group(1).split():
                key, _, raw = part.partition("=")
                if key not in BET_SCORE_KEYS or not raw:
                    raise ControllerInputError(f"bad bet_score token: {part!r}")
                try:
                    scores[key] = float(raw)
                except ValueError as exc:
                    raise ControllerInputError(f"bad bet_score number: {part!r}") from exc
            continue
        match = re.match(r"^evidence_gap:\s*(.+)$", line)
        if match:
            gap: dict[str, Any] = {
                "field": "",
                "priority": 0,
                "owner": "",
                "squad": [],
                "freshness_target": "",
                "evidence_refs": [],
                "missing_fields": [],
            }
            parts = [p.strip() for p in match.group(1).split("|")]
            gap["field"] = parts[0] if parts else ""
            for part in parts[1:]:
                key, _, value = part.partition("=")
                key, value = key.strip(), value.strip()
                if key == "priority":
                    try:
                        gap["priority"] = int(value)
                    except ValueError as exc:
                        raise ControllerInputError(f"bad evidence_gap priority: {part!r}") from exc
                elif key == "owner":
                    gap["owner"] = value
                elif key == "squad":
                    gap["squad"] = [s.strip() for s in value.split(",") if s.strip()]
                elif key == "freshness":
                    gap["freshness_target"] = value
            if not gap["field"]:
                raise ControllerInputError("evidence_gap field missing")
            gap["missing_fields"] = [gap["field"]]
            gaps.append(gap)
            continue
        for marker, key in (
            ("bet_hypothesis:", "hypothesis"),
            ("bet_impact:", "expected_impact"),
            ("bet_kill:", "kill_criterion"),
            ("bet_rollback:", "rollback"),
        ):
            if line.startswith(marker):
                proposal[key] = line[len(marker):].strip()
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
        "effort_known": effort_known,
        "scores": scores,
        "evidence_gaps": gaps,
        "proposal": proposal,
    }


def _validate_task(board: str, task: Any) -> dict:
    if not isinstance(task, dict):
        raise ControllerInputError(f"task on board {board} must be an object")
    task_id = _clean_str(task.get("task_id"))
    if not task_id:
        raise ControllerInputError(f"task_id missing on board {board}")
    status = _clean_str(task.get("status"))
    if not status:
        raise ControllerInputError(f"status missing for {task_id}")
    scores = task.get("scores") or {}
    if not isinstance(scores, dict):
        raise ControllerInputError(f"scores must be an object for {task_id}")
    for key, value in scores.items():
        if key not in BET_SCORE_KEYS or not _is_num(value):
            raise ControllerInputError(f"invalid score {key}={value!r} for {task_id}")
    gaps = task.get("evidence_gaps") or []
    if not isinstance(gaps, list):
        raise ControllerInputError(f"evidence_gaps must be a list for {task_id}")
    for gap in gaps:
        if not isinstance(gap, dict) or not _clean_str(gap.get("field")):
            raise ControllerInputError(f"evidence_gap field missing for {task_id}")
        if not _is_num(gap.get("priority", 0)):
            raise ControllerInputError(f"evidence_gap priority invalid for {task_id}")
    proposal = task.get("proposal") or {}
    if not isinstance(proposal, dict):
        raise ControllerInputError(f"proposal must be an object for {task_id}")
    normalized = dict(task)
    normalized.update(
        task_id=task_id,
        board=_clean_str(task.get("board")) or board,
        status=status.lower(),
        revenue_critical=bool(task.get("revenue_critical")),
        effort_known=bool(task.get("effort_known", True)),
        scores={k: float(v) for k, v in scores.items()},
        evidence_gaps=[dict(gap) for gap in gaps],
        proposal=dict(proposal),
    )
    return normalized


def _validate_snapshot(snapshot: Any) -> dict:
    if not isinstance(snapshot, dict):
        raise ControllerInputError("snapshot must be an object")
    boards = snapshot.get("boards", {})
    if not isinstance(boards, dict):
        raise ControllerInputError("boards must be an object")
    normalized_boards: dict[str, list[dict]] = {}
    for board, tasks in boards.items():
        if not isinstance(tasks, list):
            raise ControllerInputError(f"board {board} must map to a list")
        normalized_boards[str(board)] = [_validate_task(str(board), task) for task in tasks]
    for key in ("metric", "finance"):
        section = snapshot.get(key)
        if section is not None and not isinstance(section, dict):
            raise ControllerInputError(f"{key} must be an object")
    return {
        "boards": normalized_boards,
        "metric": snapshot.get("metric") or {"status": "gap"},
        "finance": snapshot.get("finance") or {"status": "gap"},
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


def load_live_snapshot(boards: list[str], runner: Runner | None = None) -> dict:
    """Build the snapshot read-only from the official kanban CLI."""
    run = runner or _default_runner
    unknown = [board for board in boards if board not in CANONICAL_BOARDS]
    if not boards or unknown:
        raise ControllerInputError(f"boards must be a non-empty subset of {sorted(CANONICAL_BOARDS)}")
    collected: dict[str, list[dict]] = {board: [] for board in boards}
    for board in boards:
        for status in LIVE_STATUSES:
            argv = ["kanban", "--board", board, "list", "--status", status, "--json"]
            stdout = run(argv)
            try:
                rows = json.loads(stdout)
            except json.JSONDecodeError as exc:
                raise ControllerInputError(f"non-JSON kanban output for {board}/{status}") from exc
            if not isinstance(rows, list):
                raise ControllerInputError(f"kanban output must be a list for {board}/{status}")
            collected[board].extend(task_from_row(board, row) for row in rows)
    return {
        "boards": collected,
        "metric": {"status": "gap", "note": "live adapter is read-only; no metric source attached"},
        "finance": {"status": "gap", "note": "live adapter is read-only; no finance source attached"},
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
# pure reducer
# --------------------------------------------------------------------------


def _input_fresh(section: dict | None) -> bool:
    return bool(section) and _clean_str(section.get("status")).lower() == FRESH_INPUT_STATUS


def _bet_score(task: dict) -> float:
    scores = task.get("scores") or {}
    metric_impact = float(scores.get("metric_impact", 0))
    gate_removal = float(scores.get("gate_removal", 0))
    confidence = float(scores.get("confidence", 0))
    cost = float(scores.get("cost_rub", 0))
    return (metric_impact + gate_removal) * confidence - cost


def _proposal_complete(task: dict) -> bool:
    proposal = task.get("proposal") or {}
    needed = ("owner", "squad", "hypothesis", "kill_criterion", "rollback")
    if any(not _clean_str(proposal.get(key)) for key in needed):
        return False
    squad = proposal.get("squad")
    return isinstance(squad, str) and bool(squad.strip())


def _parse_squad(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(item) for item in raw if str(item).strip()]
    return [part.strip() for part in str(raw or "").split(",") if part.strip()]


def _digest(state: str, decision_type: str, reason: str | None, candidate: dict | None) -> dict:
    parts = [f"[shadow mode] state={state} decision={decision_type}"]
    if candidate is not None and decision_type == "collect_evidence":
        task = candidate["task"]
        parts += [
            f"gate={task['task_id']} board={task['board']}",
            f"collector={candidate['owner']} squad={','.join(candidate['squad'])}",
            f"missing={','.join(candidate['missing_fields'])}",
            f"freshness_target={candidate['freshness_target']}",
            "execution_eligible=false",
            f"hypothesis={candidate.get('hypothesis', '')}",
        ]
    elif candidate is not None and decision_type == "execute_bet":
        parts += [
            f"bet={candidate['task']['task_id']} board={candidate['task']['board']}",
            f"owner={candidate['owner']} squad={','.join(candidate['squad'])}",
            f"score={candidate['score']['value']:g}",
            f"cost_rub={candidate['score']['cost_rub']:g} (declared)",
            f"hypothesis={candidate.get('hypothesis', '')}",
            f"kill={candidate.get('kill_criterion', '')}",
            f"rollback={candidate.get('rollback', '')}",
        ]
    elif reason:
        parts.append(f"reason={reason}")
    return {"channel": "telegram", "text": "\n".join(parts)}


def _canonical_hash(snapshot: dict) -> str:
    boards = {board: sorted(tasks, key=lambda t: t["task_id"]) for board, tasks in snapshot["boards"].items()}
    payload = {"v": CONTROLLER_VERSION, "boards": boards, "metric": snapshot["metric"], "finance": snapshot["finance"]}
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def reduce(snapshot: dict) -> dict:
    """Pure reducer: board snapshot -> shadow decision dict."""
    clean = _validate_snapshot(snapshot)
    boards = clean["boards"]
    all_tasks = [task for tasks in boards.values() for task in tasks]
    running = sum(1 for task in all_tasks if task["status"] == "running")
    ready = sum(1 for task in all_tasks if task["status"] == "ready")
    actionable = sorted(
        (
            task
            for tasks in boards.values()
            for task in tasks
            if task["revenue_critical"] and task["status"] in ACTIONABLE_STATUSES
        ),
        key=lambda task: task["task_id"],
    )
    blocked_gates = sum(
        1
        for tasks in boards.values()
        for task in tasks
        if task["revenue_critical"] and task["status"] == "blocked"
    )
    counts = {
        "running": running,
        "ready": ready,
        "actionable_revenue_gates": len(actionable),
        "blocked_revenue_gates": blocked_gates,
    }
    metric_fresh = _input_fresh(clean["metric"])
    finance_fresh = _input_fresh(clean["finance"])

    if running:
        state, decision_type, reason, candidate = "RUNNING", "no_action", "fleet_busy_running", None
    elif ready:
        state, decision_type, reason, candidate = "READY_QUEUE", "no_action", "ready_work_exists", None
    elif not actionable:
        state, decision_type, reason, candidate = "IDLE_NO_GATES", "no_action", "no_actionable_revenue_gate", None
    else:
        state = "ACTIONABLE_IDLE"
        decision_type, reason, candidate = "no_action", None, None
        executable: list[tuple[float, dict, dict]] = []
        if metric_fresh and finance_fresh:
            for task in actionable:
                if task["effort_known"] and task["scores"] and _proposal_complete(task):
                    executable.append((_bet_score(task), task, task["proposal"]))
        executable.sort(key=lambda entry: (-entry[0], entry[1]["task_id"]))
        if executable:
            if len(executable) > 1 and executable[0][0] == executable[1][0]:
                decision_type, reason = "no_action", "score_tie"
            else:
                score, task, proposal = executable[0]
                decision_type, candidate = "execute_bet", {
                    "task": task,
                    "owner": _clean_str(proposal.get("owner")) or task["assignee"],
                    "squad": _parse_squad(proposal.get("squad")) or ([task["assignee"]] if task["assignee"] else []),
                    "hypothesis": _clean_str(proposal.get("hypothesis")),
                    "expected_impact": _clean_str(proposal.get("expected_impact")),
                    "kill_criterion": _clean_str(proposal.get("kill_criterion")),
                    "rollback": _clean_str(proposal.get("rollback")),
                    "score": {
                        "formula": "(metric_impact + gate_removal) * confidence - cost_rub",
                        "value": round(score, 6),
                        "cost_rub": float(task["scores"].get("cost_rub", 0)),
                    },
                }
        else:
            gaps = sorted(
                (
                    (int(gap.get("priority", 0)), task["task_id"], _clean_str(gap.get("field")), gap, task)
                    for task in actionable
                    for gap in task.get("evidence_gaps") or []
                ),
                key=lambda entry: (entry[0], entry[1], entry[2]),
            )
            if not gaps:
                decision_type, reason = "no_action", "no_executable_candidate_and_no_evidence_path"
            elif len(gaps) > 1 and gaps[0][0] == gaps[1][0]:
                decision_type, reason = "no_action", "evidence_priority_tie"
            else:
                _priority, _task_id, _field, gap, task = gaps[0]
                decision_type = "collect_evidence"
                candidate = {
                    "task": task,
                    "missing_fields": [str(field) for field in gap.get("missing_fields") or [gap.get("field")]],
                    "freshness_target": _clean_str(gap.get("freshness_target")),
                    "owner": _clean_str(gap.get("owner")) or task["assignee"],
                    "squad": _parse_squad(gap.get("squad")) or ([task["assignee"]] if task["assignee"] else []),
                    "evidence_refs": [str(ref) for ref in gap.get("evidence_refs") or []],
                    "hypothesis": _clean_str((task.get("proposal") or {}).get("hypothesis")),
                    "kill_criterion": _clean_str((task.get("proposal") or {}).get("kill_criterion")),
                    "rollback": _clean_str((task.get("proposal") or {}).get("rollback")),
                    # No invented RUB: evidence recommendations carry no money
                    # figure; the declared cost stays in the task scores.
                    "score": {"formula": None, "value": None, "cost_rub": float(task["scores"].get("cost_rub", 0))},
                }

    decision_id = "nbc1-" + _canonical_hash(clean)[:32]
    decision: dict[str, Any] = {
        "controller_version": CONTROLLER_VERSION,
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
        "inputs": {
            "metric_status": _clean_str(clean["metric"].get("status")).lower() or "gap",
            "finance_status": _clean_str(clean["finance"].get("status")).lower() or "gap",
        },
        "candidate": candidate,
        "canonical_boards": sorted(CANONICAL_BOARDS),
    }
    decision["digest"] = _digest(state, decision_type, reason, candidate)
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
