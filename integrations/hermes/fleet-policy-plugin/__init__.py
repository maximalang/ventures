from __future__ import annotations

import os
import sys
import threading
import re
from pathlib import Path
from typing import Any

CODE_ROOT = Path(__file__).resolve().parents[3]
VENTURES_ROOT = Path("C:/Users/max/Desktop/all/ventures")
if not (CODE_ROOT / "src" / "fleet_policy").is_dir():
    CODE_ROOT = VENTURES_ROOT
SRC = CODE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fleet_policy.kanban_context import load_task_context  # noqa: E402
from fleet_policy.projector import HermesProjector  # noqa: E402
from fleet_policy.runtime import FleetPolicyRuntime  # noqa: E402

_RUNTIME: FleetPolicyRuntime | None = None
_PROJECTOR = HermesProjector()
_KANBAN_TASK_RE = re.compile(r"^t_[0-9a-f]{6,}$")


def runtime() -> FleetPolicyRuntime:
    global _RUNTIME
    if _RUNTIME is None:
        _RUNTIME = FleetPolicyRuntime(VENTURES_ROOT)
    return _RUNTIME


def _resolve_task_id(kwargs: dict[str, Any]) -> str | None:
    # The hook kwarg "task_id" is the Hermes session-scoped id, NOT the Kanban
    # task. The dispatcher pins the real board task in $HERMES_KANBAN_TASK.
    env_task = os.environ.get("HERMES_KANBAN_TASK") or ""
    if env_task:
        return env_task
    kwarg = str(kwargs.get("task_id") or "")
    return kwarg if _KANBAN_TASK_RE.match(kwarg) else None


def context(kwargs: dict[str, Any]) -> dict[str, Any]:
    base = {
        "task_id": _resolve_task_id(kwargs),
        "run_id": kwargs.get("run_id"),
        "session_id": kwargs.get("session_id"),
        "tool_call_id": kwargs.get("tool_call_id"),
        "turn_id": kwargs.get("turn_id"),
        "api_request_id": kwargs.get("api_request_id"),
        "board": kwargs.get("board"),
        "profile": kwargs.get("profile_name") or os.environ.get("HERMES_PROFILE"),
    }
    return load_task_context(base, runtime().config.get("projects", {}))


def _message(payload: dict[str, Any]) -> str:
    return (
        f"FLEET POLICY BLOCKED [{payload.get('rule_id')}]: {payload.get('reason')}\n"
        f"task={payload.get('task_id') or 'none'} args_hash={payload.get('args_hash')}"
    )


def _project(payload: dict[str, Any]) -> None:
    task_id = str(payload.get("task_id") or "")
    if not task_id or not runtime().claim_projection(payload):
        return
    board = str(os.environ.get("HERMES_KANBAN_BOARD") or payload.get("board") or "default")

    def _work() -> None:
        # Projecting policy evidence is a compensating control action, not the blocked user action.
        try:
            _PROJECTOR.comment_and_block(board, task_id, _message(payload), block=True)
        except Exception:
            pass
        # Company notifications are NOT drained here: _project fires on every
        # significant deny/approval, so auto-drain would retry the whole pending
        # outbox per blocked call and spam company's Bot Chat. Delivery is an
        # explicit operator action: `fleet-policy drain-notifications`.

    # pre_tool_call callbacks are bounded by plugins.hook_callback_timeout (30s).
    # Kanban block + Bot Chat projection are subprocess-bound and can exceed it,
    # so projection runs detached; the fail-closed block decision returns immediately.
    threading.Thread(target=_work, name="fleet-policy-projection", daemon=True).start()


def pre_tool_call(tool_name: str = "", args: Any = None, **kwargs: Any) -> dict[str, Any] | None:
    arguments = dict(args or {}) if isinstance(args, dict) else {}
    try:
        decision = runtime().pre_tool_call(tool_name or "unknown", arguments, context(kwargs))
    except Exception as exc:
        lowered = (tool_name or "").lower()
        if lowered.startswith(("read_", "search_", "list_", "get_", "show_", "view_")):
            return None
        return {"action": "block", "message": f"FLEET POLICY FAIL-CLOSED: {type(exc).__name__}"}
    payload = decision.as_dict()
    if decision.decision in {"deny", "approval_required"}:
        payload.setdefault("board", os.environ.get("HERMES_KANBAN_BOARD") or "")
        _project(payload)
        return {"action": "block", "message": _message(payload)}
    return None


def post_tool_call(tool_name: str = "", args: Any = None, status: str = "", error_type: str = "",
                   error_message: str = "", **kwargs: Any) -> None:
    arguments = dict(args or {}) if isinstance(args, dict) else {}
    payload = runtime().post_tool_call(
        tool_name or "unknown", arguments, context(kwargs),
        success=status != "error", error_type=error_type or "", error_message=error_message or "",
    )
    if payload:
        _project(payload)


def post_api_request(usage: Any = None, assistant_tool_call_count: int = 0, **kwargs: Any) -> None:
    payload = runtime().post_api_request(
        context(kwargs), usage if isinstance(usage, dict) else None, int(assistant_tool_call_count or 0)
    )
    if payload:
        _project(payload)


def api_request_error(error: Any = None, **kwargs: Any) -> None:
    payload = runtime().api_request_error(context(kwargs), error)
    if payload:
        _project(payload)


def kanban_task_claimed(task_id: str = "", board: str = "", assignee: str = "", run_id: Any = None,
                        **kwargs: Any) -> None:
    ctx = load_task_context(
        {"task_id": task_id, "board": board, "profile": assignee, "run_id": run_id},
        runtime().config.get("projects", {}),
    )
    task_type, error = runtime().task_type(ctx)
    if not error:
        return
    payload = {
        "decision": "deny", "rule_id": "missing_or_unknown_task_type", "reason": error,
        "task_id": task_id, "project": ctx.get("project", board), "profile": assignee,
        "board": board or "",
        "action": "worker_launch", "target": task_id, "args_hash": "not-applicable",
        "timestamp": "", "budget_snapshot": runtime().budget_snapshot(ctx, task_type), "approval_card": None,
    }
    runtime().store.record_event(
        f"claim-task-type:{board}:{task_id}:{error}", str(run_id or task_id), task_id,
        "invalid_task_type", payload, True,
    )
    _project(payload)


def fleet_guidance(_session_info: Any) -> str:
    return (
        "# Fleet policy gate\n"
        "Kanban is the task registry. Dispatcher tasks require an exact task_type marker: research, code, review, or ops. "
        "All risky state-changing calls are automatically checked before execution. A deny or approval_required result must not be bypassed. "
        "Approvals are exact, one-time bindings to task_id + action + target + args_hash. Record evidence in Kanban; do not spam allow events."
    )


def rr_guidance(_session_info: Any) -> str:
    if os.environ.get("HERMES_KANBAN_BOARD") != "rr-team":
        return ""
    path = VENTURES_ROOT / "skills" / "rr-project" / "SKILL.md"
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return "Recruiter Radar task: read the repository AGENTS.md and CLAUDE.md before work; use codex/* and never push or merge main."


def register(ctx) -> None:
    ctx.register_hook("pre_tool_call", pre_tool_call)
    ctx.register_hook("post_tool_call", post_tool_call)
    ctx.register_hook("post_api_request", post_api_request)
    ctx.register_hook("api_request_error", api_request_error)
    ctx.register_hook("kanban_task_claimed", kanban_task_claimed)
    ctx.register_system_prompt_section("fleet-policy", fleet_guidance, position="after_memory", max_chars=1200)
    ctx.register_system_prompt_section("rr-project", rr_guidance, position="after_memory", max_chars=2000)
