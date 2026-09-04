from __future__ import annotations

import os
import sys
import re
from pathlib import Path
from typing import Any

CODE_ROOT = Path(__file__).resolve().parents[3]
VENTURES_ROOT = Path(os.environ.get("HERMES_VENTURES_ROOT") or CODE_ROOT)
if not (CODE_ROOT / "src" / "fleet_policy").is_dir():
    CODE_ROOT = VENTURES_ROOT
SRC = CODE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fleet_policy.kanban_context import load_task_context  # noqa: E402
from fleet_policy.policy import classify  # noqa: E402
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
        f"FLEET POLICY BLOCKED [{payload.get('rule_id')}] "
        f"pattern={payload.get('pattern_category') or 'unknown'} "
        f"call_index={payload.get('call_index') or 0}"
    )


def _project(payload: dict[str, Any]) -> None:
    # This denial is emitted only after a primary projection already moved the
    # card to blocked. Re-projecting it produces comments without changing the
    # stop outcome and can amplify fallback chains into owner-visible noise.
    if payload.get("rule_id") == "task_already_blocked":
        return
    task_id = str(payload.get("task_id") or "")
    if not task_id or not runtime().claim_projection(payload):
        return
    board = str(payload.get("board") or os.environ.get("HERMES_KANBAN_BOARD") or "default")

    # Synchronous official CLI projection is deliberate: a daemon thread could be
    # killed with a short-lived worker before the block lands. `kanban block` also
    # appends the evidence comment and normally completes in <2s; the callback's
    # 30s Hermes timeout remains fail-closed if the CLI itself is unavailable.
    try:
        result = _PROJECTOR.comment_and_block(board, task_id, _message(payload), block=True)
    except Exception:
        runtime().release_projection(payload)
        raise
    if result.get("block") != 0:
        runtime().release_projection(payload)
    # Company notifications are NOT drained here: _project fires on every
    # significant deny/approval, so auto-drain would retry the whole pending
    # outbox per blocked call and spam company's Bot Chat. Delivery is explicit:
    # `fleet-policy drain-notifications`.


def pre_tool_call(tool_name: str = "", args: Any = None, **kwargs: Any) -> dict[str, Any] | None:
    arguments = dict(args or {}) if isinstance(args, dict) else {}
    try:
        ctx = context(kwargs)
        decision = runtime().pre_tool_call(tool_name or "unknown", arguments, ctx)
    except Exception as exc:
        # Preserve ordinary read availability during a policy-DB outage, but
        # never let the fallback bypass secret-bearing path classification.
        try:
            cfg = _RUNTIME.config if _RUNTIME is not None else runtime().config
            fallback = classify(
                tool_name or "unknown", arguments, cfg,
                worker=bool(os.environ.get("HERMES_KANBAN_TASK")),
            )
            if fallback.effect == "read" and fallback.category != "secret_read_or_write":
                return None
        except Exception:
            pass
        return {"action": "block", "message": f"FLEET POLICY FAIL-CLOSED: {type(exc).__name__}"}
    payload = decision.as_dict()
    if decision.decision in {"deny", "approval_required"}:
        payload["board"] = str(ctx.get("board") or os.environ.get("HERMES_KANBAN_BOARD") or "")
        payload["task_status"] = str(ctx.get("task_status") or "unknown")
        payload["run_key"] = str(ctx.get("current_run_id") or ctx.get("run_id") or "session")
        _project(payload)
        return {"action": "block", "message": _message(payload)}
    return None


def post_tool_call(tool_name: str = "", args: Any = None, status: str = "", error_type: str = "",
                   error_message: str = "", **kwargs: Any) -> None:
    arguments = dict(args or {}) if isinstance(args, dict) else {}
    payload = runtime().post_tool_call(
        tool_name or "unknown", arguments, context(kwargs),
        success=status in {"ok", "success"}, error_type=error_type or "", error_message=error_message or "",
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
        "task_status": str(ctx.get("task_status") or "unknown"),
        "run_key": str(ctx.get("current_run_id") or ctx.get("run_id") or "session"),
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
        "All state-changing calls pass fleet-policy. Routine main/deploy/publishing/spend are autonomous after independent evidence gates. "
        "Only serious legal, ownership/access, irreversible-data, mass-outreach, capability, or over-budget actions require owner approval. "
        "Approvals are exact one-time bindings; record decisions, profit hypothesis, kill criteria, gates and evidence in Kanban."
    )


def project_guidance(_session_info: Any) -> str:
    board = os.environ.get("HERMES_KANBAN_BOARD") or ""
    project = runtime().config.get("projects", {}).get(board, {})
    relative = project.get("guidance") if isinstance(project, dict) else None
    if not relative:
        return ""
    path = VENTURES_ROOT / str(relative)
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return f"Project board {board}: read the canonical repository AGENTS.md/CLAUDE.md and record evidence in Kanban."


# Backward-compatible test/import alias.
def rr_guidance(session_info: Any) -> str:
    return project_guidance(session_info)


def register(ctx) -> None:
    # Prewarm config + idempotent schema migration outside the hot tool path.
    runtime()
    ctx.register_hook("pre_tool_call", pre_tool_call)
    ctx.register_hook("post_tool_call", post_tool_call)
    ctx.register_hook("post_api_request", post_api_request)
    ctx.register_hook("api_request_error", api_request_error)
    ctx.register_hook("kanban_task_claimed", kanban_task_claimed)
    ctx.register_system_prompt_section("fleet-policy", fleet_guidance, position="after_memory", max_chars=1200)
    ctx.register_system_prompt_section("project-guidance", project_guidance, position="after_memory", max_chars=2000)
