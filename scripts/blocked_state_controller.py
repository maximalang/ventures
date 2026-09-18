#!/usr/bin/env python3
"""Durable all-board blocked-state recovery controller.

Default mode is read-only. ``--apply`` performs only bounded, supported
Hermes Kanban CLI actions. It never opens or writes a board database.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import tempfile
from typing import Any, Callable, Iterable

BOARD_ROOT = pathlib.Path(
    os.environ.get(
        "HERMES_KANBAN_BOARDS",
        r"C:\Users\max\AppData\Local\hermes\kanban\boards",
    )
)
STATE_PATH = pathlib.Path(
    os.environ.get(
        "HERMES_BLOCKED_CONTROLLER_STATE",
        r"C:\Users\max\AppData\Local\hermes\profiles\company\scripts\blocked_state_controller.state.json",
    )
)
CLI = os.environ.get("HERMES_CLI", "hermes")
ACTION_LIMIT = 5
RETRY_COOLDOWN_SECONDS = 6 * 3600
SPAWN_RETRIES = 3
SPAWN_FLAKE_RCS = {3221225794}
STALE_BLOCK_DAYS = 7.0
HEARTBEAT_STALL_SECONDS = 2 * 3600
DELEGATION_ENV_KEYS = (
    "HERMES_DELEGATED_CHILD_CONTEXT",
    "HERMES_KANBAN_DB",
    "HERMES_KANBAN_BOARD",
)


def _scrubbed_env(base: dict[str, str] | None = None) -> dict[str, str]:
    """Worker-runnable CLI environment: drop delegation/board pinning vars."""
    env = dict(os.environ if base is None else base)
    for key in DELEGATION_ENV_KEYS:
        env.pop(key, None)
    return env

SAFETY_RULES = {
    "secret_read_or_write",
    "worker_self_approval",
    "gate_forgery",
    "irreversible_data_loss",
    "financial_over_budget",
}
LOOP_RULES = {"same_failure_loop", "identical_call_loop"}
OWNER_TERMS = {
    "phone",
    "sms",
    "kyc",
    "bank-owner",
    "domain-owner",
    "ownership transfer",
    "root/admin",
    "payment instrument",
    "телефон",
    "смс",
    "верификац",
    "владение",
    "владелец домена",
    "банков",
    "платёжный инструмент",
}
COMPLETION_TERMS = {
    "verified",
    "pass",
    "published",
    "работа завершена",
    "доставлен",
    "exact head",
}


@dataclasses.dataclass(frozen=True)
class Decision:
    classification: str
    owner: str
    action: str
    reason: str
    safe_to_apply: bool = False


@dataclasses.dataclass
class Candidate:
    board: str
    task: dict[str, Any]
    show: dict[str, Any]
    decision: Decision
    age_seconds: int

    @property
    def task_id(self) -> str:
        return str(self.task.get("id") or "")


def _now_epoch() -> int:
    return int(dt.datetime.now(dt.timezone.utc).timestamp())


def atomic_json_write(path: pathlib.Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, sort_keys=True, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    finally:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass


def load_state(path: pathlib.Path = STATE_PATH) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def run_cli(board: str, args: list[str], timeout: int = 45) -> Any:
    cmd = [CLI, "kanban", "--board", board, *args]
    expects_json = bool(args and args[0] in {"list", "show", "create", "promote"})
    if expects_json:
        cmd.append("--json")
    proc = None
    last_error: Exception | None = None
    for attempt in range(SPAWN_RETRIES):
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                stdin=subprocess.DEVNULL,
                env=_scrubbed_env(),
            )
            break
        except OSError as exc:
            last_error = exc
            rc = getattr(exc, "winerror", None)
            if rc is None:
                rc = getattr(exc, "errno", None)
            if rc in SPAWN_FLAKE_RCS and attempt + 1 < SPAWN_RETRIES:
                continue
            raise RuntimeError(f"CLI spawn failed rc={rc}: {exc}") from exc
    if proc is None:
        raise RuntimeError(f"CLI spawn failed after {SPAWN_RETRIES} attempts: {last_error}")
    if proc.returncode != 0:
        raise RuntimeError(f"CLI rc={proc.returncode}: {' '.join(cmd)}\n{proc.stderr[-1200:]}")
    text = proc.stdout.strip()
    if not expects_json:
        return {"ok": True, "stdout": text}
    if not text:
        return None
    start_candidates = [i for i in (text.find("["), text.find("{")) if i >= 0]
    if not start_candidates:
        raise RuntimeError(f"CLI returned non-JSON output: {text[-1200:]}")
    return json.loads(text[min(start_candidates):])


def discover_boards(root: pathlib.Path = BOARD_ROOT) -> list[str]:
    if not root.is_dir():
        return []
    return sorted(
        child.name
        for child in root.iterdir()
        if child.is_dir() and (child / "kanban.db").is_file()
    )


def _payload(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("payload")
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else {"raw": raw}
    except (TypeError, ValueError):
        return {"raw": str(raw)}


def latest_block_reason(show: dict[str, Any]) -> tuple[str, str, int]:
    for event in reversed(show.get("events") or []):
        if event.get("kind") not in {"blocked", "block_loop_detected"}:
            continue
        payload = _payload(event)
        reason = str(payload.get("reason") or payload.get("raw") or "")
        rule = ""
        for known in SAFETY_RULES | LOOP_RULES | {
            "policy_control_plane_mutation",
            "evidence_gate_missing",
            "budget_exhausted",
            "missing_or_unknown_task_type",
            "worker_code_execution",
        }:
            if known in reason:
                rule = known
                break
        return rule, reason, int(event.get("created_at") or 0)
    return "", "", 0


def _all_text(task: dict[str, Any], show: dict[str, Any]) -> str:
    chunks = [
        str(task.get("title") or ""),
        str(task.get("body") or ""),
        str(task.get("result") or ""),
        str(show.get("latest_summary") or ""),
    ]
    chunks.extend(str(comment.get("body") or "") for comment in show.get("comments") or [])
    return "\n".join(chunks).lower()


def _company_resume(show: dict[str, Any]) -> bool:
    for comment in reversed(show.get("comments") or []):
        body = str(comment.get("body") or "").lower()
        author = str(comment.get("author") or "").lower()
        if author in {"company", "worker"} and any(
            token in body for token in ("decision:company=go", "resume:", "correction:")
        ):
            return True
    return False


def is_recovery_card(task: dict[str, Any]) -> bool:
    title = str(task.get("title") or "").strip().lower()
    return title.startswith("recover ")


def detect_heartbeat_stall(
    task: dict[str, Any],
    show: dict[str, Any],
    *,
    now: int | None = None,
    stall_seconds: int = HEARTBEAT_STALL_SECONDS,
) -> bool:
    """True iff a non-running card's most recent heartbeat is stale by ``stall_seconds``."""
    if str(task.get("status") or "") == "running":
        return False
    stamps = [
        int(event.get("created_at") or 0)
        for event in (show.get("events") or [])
        if str(event.get("kind") or "") == "heartbeat"
    ]
    if not stamps:
        return False
    current = now if now is not None else _now_epoch()
    return (current - max(stamps)) > stall_seconds


def _has_completed_evidence(task: dict[str, Any], show: dict[str, Any]) -> bool:
    text = _all_text(task, show)
    return any(term in text for term in COMPLETION_TERMS)


def infer_marker(task: dict[str, Any]) -> str:
    assignee = str(task.get("assignee") or "company")
    if assignee == "research":
        return "research"
    if assignee == "qa" or "review" in str(task.get("title") or "").lower():
        return "review"
    if assignee in {"operations", "company"}:
        return "ops"
    return "code"


def classify(
    task: dict[str, Any],
    show: dict[str, Any],
    parent_status: Callable[[str], str | None] | None = None,
    *,
    now: int | None = None,
    stale_after_days: float | None = None,
) -> Decision:
    parent_status = parent_status or (lambda _task_id: None)
    rule, reason, blocked_at = latest_block_reason(show)
    text = _all_text(task, show)
    block_kind = str(task.get("block_kind") or "")
    if stale_after_days is None:
        stale_after_days = 0.0
    if stale_after_days < 0:
        stale_after_days = 0.0

    open_parents = [
        parent for parent in (show.get("parents") or [])
        if parent_status(str(parent)) not in {"done", "archived"}
    ]
    if open_parents:
        return Decision("dependency", "dependency-owner", "wait", f"open parents: {','.join(open_parents)}")

    if rule in SAFETY_RULES:
        return Decision("safety", "company", "hold", rule)

    if any(term in text for term in OWNER_TERMS) and block_kind not in {"transient", "dependency"}:
        return Decision("owner_only", "owner", "escalate", "human-bound capability or ownership boundary")

    if is_recovery_card(task) and not _company_resume(show):
        return Decision("nested_recovery", "company", "hold", "recovery card must not trigger further recovery")

    if rule == "missing_or_unknown_task_type":
        return Decision("malformed_card", "company", "route_repair", "required first-line work marker missing")

    if _has_completed_evidence(task, show):
        return Decision("completed_artifact", "company", "route_review", "completion evidence exists on blocked card")

    if block_kind == "transient":
        return Decision("transient", str(task.get("assignee") or "company"), "unblock", "typed transient block", True)

    if _company_resume(show) and rule not in SAFETY_RULES:
        if str(task.get("status") or "") == "triage":
            return Decision("triage_resume", "company", "route_review", "triage requires specification/review, not unblock")
        return Decision("approved_resume", str(task.get("assignee") or "company"), "unblock", "company resume decision present", True)

    if detect_heartbeat_stall(task, show, now=now):
        return Decision("heartbeat_stall", str(task.get("assignee") or "company"), "unblock", "worker heartbeat stalled, bounded requeue", True)

    if rule != "" and stale_after_days > 0:
        current = now if now is not None else _now_epoch()
        if (current - blocked_at) > int(stale_after_days * 86400):
            return Decision("stale_archive_review", "company", "route_archive_review", "typed block is stale; archive review instead of recovery")

    if rule == "policy_control_plane_mutation":
        read_only = any(token in reason.lower() for token in ("read_file", "search_files", "web_search", "list"))
        if read_only:
            return Decision("proven_false_positive", str(task.get("assignee") or "company"), "unblock", "read-only call misclassified", True)
        return Decision("policy_review", "company", "route_review", "control-plane deny needs scoped review")

    if rule in LOOP_RULES:
        return Decision("method_loop", "company", "route_repair", "same method must not be retried")

    if rule == "budget_exhausted":
        return Decision("budget_continuation", "company", "route_repair", "fresh bounded continuation required")

    if rule == "evidence_gate_missing":
        return Decision("evidence_gap", "qa", "route_evidence", "specific independent evidence required")

    if rule == "worker_code_execution":
        return Decision("capability_mismatch", "company", "route_repair", "task must be reshaped for available tools")

    if task.get("status") == "triage":
        return Decision("triage_review", "company", "route_review", "stale triage requires disposition")

    return Decision("unclassified", "company", "route_review", reason or "no typed recovery class")


class Controller:
    def __init__(
        self,
        *,
        apply: bool = False,
        state_path: pathlib.Path = STATE_PATH,
        action_limit: int = ACTION_LIMIT,
        cli: Callable[[str, list[str], int], Any] = run_cli,
    ) -> None:
        self.apply = apply
        self.state_path = state_path
        self.action_limit = action_limit
        self.cli = cli
        self.state = load_state(state_path)
        self.now = _now_epoch()
        self.actions = 0

    def _list(self, board: str, status: str) -> list[dict[str, Any]]:
        value = self.cli(board, ["list", "--status", status], 60)
        return value if isinstance(value, list) else []

    def _show(self, board: str, task_id: str) -> dict[str, Any]:
        value = self.cli(board, ["show", task_id], 45)
        return value if isinstance(value, dict) else {}

    def _task_status(self, board: str, task_id: str) -> str | None:
        try:
            return str((self._show(board, task_id).get("task") or {}).get("status") or "") or None
        except RuntimeError:
            return None

    def scan(self, boards: Iterable[str]) -> list[Candidate]:
        found: list[Candidate] = []
        for board in boards:
            parent_cache: dict[str, str | None] = {}
            for status in ("blocked", "triage"):
                for task in self._list(board, status):
                    task_id = str(task.get("id") or "")
                    if not task_id:
                        continue
                    show = self._show(board, task_id)
                    task_full = show.get("task") or task
                    def parent_status(parent_id: str) -> str | None:
                        if parent_id not in parent_cache:
                            parent_cache[parent_id] = self._task_status(board, parent_id)
                        return parent_cache[parent_id]
                    decision = classify(task_full, show, parent_status)
                    _, _, blocked_at = latest_block_reason(show)
                    created_at = int(task_full.get("created_at") or self.now)
                    age = max(0, self.now - (blocked_at or created_at))
                    found.append(Candidate(board, task_full, show, decision, age))
        return found

    def _acted_recently(self, candidate: Candidate) -> bool:
        key = f"{candidate.board}:{candidate.task_id}:{candidate.decision.classification}"
        at = int((self.state.get("acted") or {}).get(key) or 0)
        return self.now - at < RETRY_COOLDOWN_SECONDS

    def _remember(self, candidate: Candidate) -> None:
        key = f"{candidate.board}:{candidate.task_id}:{candidate.decision.classification}"
        self.state.setdefault("acted", {})[key] = self.now

    def _route_task(self, candidate: Candidate) -> dict[str, Any]:
        d = candidate.decision
        title = f"Recover {candidate.task_id}: {str(candidate.task.get('title') or '')[:80]}"
        marker = "review" if d.owner in {"company", "qa"} else infer_marker(candidate.task)
        body = (
            f"task_type: {marker}\n"
            f"Recover {candidate.board}/{candidate.task_id}. Class={d.classification}. "
            f"Resolve cause, preserve safety, and read back the original card."
        )
        args = [
            "create",
            title,
            "--body", body,
            "--assignee", d.owner,
            "--priority", str(int(candidate.task.get("priority") or 0) + 1),
            "--idempotency-key", f"blocked-recovery:{candidate.board}:{candidate.task_id}:{d.classification}",
        ]
        return self.cli(candidate.board, args, 60)

    def apply_candidate(self, candidate: Candidate) -> dict[str, Any]:
        d = candidate.decision
        if not self.apply:
            return {"outcome": "dry_run", "proposed": d.action}
        if self.actions >= self.action_limit:
            return {"outcome": "deferred", "reason": "action_limit"}
        if self._acted_recently(candidate):
            return {"outcome": "deferred", "reason": "cooldown"}

        if d.action == "unblock" and d.safe_to_apply:
            before = str(candidate.task.get("status") or "")
            self.cli(candidate.board, ["unblock", candidate.task_id, "--reason", f"controller:{d.classification}"], 45)
            after = self._task_status(candidate.board, candidate.task_id)
            if before not in {"blocked", "triage"} or after not in {"ready", "todo"}:
                raise RuntimeError(f"readback failed for {candidate.board}/{candidate.task_id}: {before}->{after}")
            result = {"outcome": "unblocked", "before": before, "after": after}
        elif d.action.startswith("route_"):
            if not d.safe_to_apply:
                return {"outcome": "dry_run", "proposed": d.action}
            created = self._route_task(candidate)
            result = {"outcome": "routed", "created": created}
        else:
            return {"outcome": "held", "reason": d.action}

        self.actions += 1
        self._remember(candidate)
        return result

    def run(self, boards: Iterable[str]) -> dict[str, Any]:
        candidates = self.scan(boards)
        rows = []
        metrics: dict[str, int] = {}
        for candidate in sorted(candidates, key=lambda c: c.age_seconds, reverse=True):
            result = self.apply_candidate(candidate)
            key = candidate.decision.classification
            metrics[key] = metrics.get(key, 0) + 1
            rows.append({
                "board": candidate.board,
                "task_id": candidate.task_id,
                "status": candidate.task.get("status"),
                "age_seconds": candidate.age_seconds,
                "classification": key,
                "owner": candidate.decision.owner,
                "action": candidate.decision.action,
                "result": result,
            })
        if self.apply:
            self.state["last_run_at"] = self.now
            self.state["last_metrics"] = metrics
            atomic_json_write(self.state_path, self.state)
        return {
            "mode": "apply" if self.apply else "dry_run",
            "boards": list(boards),
            "counts": metrics,
            "actions_applied": self.actions,
            "items": rows,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--board", action="append", default=[])
    parser.add_argument("--action-limit", type=int, default=ACTION_LIMIT)
    parser.add_argument("--state", type=pathlib.Path, default=STATE_PATH)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    boards = args.board or discover_boards()
    if not boards:
        print(json.dumps({"error": "no boards discovered"}))
        return 2
    controller = Controller(apply=args.apply, state_path=args.state, action_limit=max(0, args.action_limit))
    try:
        report = controller.run(boards)
    except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
