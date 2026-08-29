from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import load_config
from .models import PolicyDecision
from .policy import Classification, classify, infer_task_type
from .redaction import args_hash, redact, stable_id
from .storage import PolicyStore, utc_now


class FleetPolicyRuntime:
    def __init__(self, root: str | Path, *, config_path: str | Path | None = None,
                 db_path: str | Path | None = None):
        self.root = Path(root)
        self.config = load_config(config_path or self.root / "config" / "fleet-policy.yaml")
        self.store = PolicyStore(db_path or self.root / ".state" / "fleet-policy.db")
        self.store.migrate()

    def task_type(self, context: dict[str, Any]) -> tuple[str | None, str | None]:
        return infer_task_type(context.get("task_body"), context.get("comments"), context.get("skills"))

    def budget_snapshot(self, context: dict[str, Any], task_type: str | None) -> dict[str, Any]:
        task_id = str(context.get("task_id") or "")
        used = self.store.budget(task_id) if task_id else {"tokens": 0, "tool_calls": 0, "retries": 0}
        started = context.get("started_at")
        now_epoch = int(datetime.now(timezone.utc).timestamp())
        used["wall_clock_minutes"] = max(0, (now_epoch - int(started)) // 60) if started else 0
        limits = dict(self.config["budgets"].get(task_type, {})) if task_type else {}
        return {
            "task_type": task_type,
            "used": used,
            "limits": limits,
            "monetary_cost": {"status": "unavailable", "amount": None, "currency": None},
        }

    def _exhausted(self, snapshot: dict[str, Any], context: dict[str, Any]) -> str | None:
        used, limits = snapshot["used"], snapshot["limits"]
        if not limits:
            return None
        checks = {
            "tokens": int(limits["tokens"]),
            "wall_clock_minutes": int(limits["wall_clock_minutes"]),
            "tool_calls": int(limits["tool_calls"]),
            # retries is dispatcher-owned (kanban.failure_limit / task
            # max_retries) and is not enforced from API-error volume.
        }
        for metric, limit in checks.items():
            if int(used.get(metric, 0)) >= limit:
                return metric
        return None

    @staticmethod
    def _target(tool_name: str, arguments: dict[str, Any]) -> str:
        raw = arguments.get("path") or arguments.get("url") or arguments.get("target") or arguments.get("command") or tool_name
        return str(redact(raw))[:500]

    @staticmethod
    def _approval_card(context: dict[str, Any], category: str, target: str, hashed: str, rule_key: str) -> dict[str, Any]:
        return {
            "project_task": f"{context.get('board', 'unknown')} + {context.get('task_id', 'unknown')} + {context.get('task_title', 'untitled')}",
            "action": f"{category}: {target}",
            "why": "portfolio approval policy",
            "evidence": f"args_hash:{hashed}",
            "risk": "external, privileged, destructive, or irreversible effect",
            "rollback": "not executed; unblock only after the exact binding is approved",
            "choice": "APPROVE | REJECT | CHANGE <condition>",
            "rule_key": rule_key,
        }

    def pre_tool_call(self, tool_name: str, arguments: dict[str, Any], context: dict[str, Any]) -> PolicyDecision:
        task_id = str(context.get("task_id") or "")
        task_type, task_error = self.task_type(context)
        worker = bool(context.get("worker") or task_id)
        hashed = args_hash(arguments)
        target = self._target(tool_name, arguments)
        call_signature = stable_id(tool_name, hashed, target)
        tool_call_id = str(context.get("tool_call_id") or stable_id(task_id, call_signature, context.get("turn_id")))

        if worker and context.get("task_context_error"):
            result = Classification("state_change", "task_context_unavailable", "deny", str(context["task_context_error"]))
        elif worker and task_error:
            result = Classification("state_change", "missing_or_unknown_task_type", "deny", task_error)
        elif worker and context.get("task_status") == "blocked":
            result = Classification("state_change", "task_already_blocked", "deny", "Kanban task is blocked")
        else:
            result = classify(tool_name, arguments, self.config, worker=worker)

        snapshot = self.budget_snapshot(context, task_type)
        exhausted = self._exhausted(snapshot, context) if worker else None
        if exhausted:
            result = Classification(result.effect, "budget_exhausted", "deny", f"hard budget exhausted: {exhausted}")
        elif worker and self.store.count_signature(task_id, "call_signature", call_signature) >= int(self.config["anti_loop"]["max_identical_calls"]):
            result = Classification(result.effect, "identical_call_loop", "deny", "maximum identical calls reached")

        if worker and task_type:
            self.store.add_budget(task_id, "tool_calls", 1, stable_id(task_id, tool_call_id, "tool_call"))
            snapshot = self.budget_snapshot(context, task_type)

        approval_card = None
        decision = result.decision
        reason = result.reason
        rule_id = result.category
        if decision == "approval_required":
            if not task_id:
                decision, rule_id, reason = "deny", "approval_binding_missing", "risky action requires a Kanban task binding"
            elif self.store.consume_exact_approval(task_id, tool_name, target, hashed):
                decision, rule_id, reason = "allow", "approved_once", "exact one-time approval consumed"
            else:
                rule_key = stable_id(task_id, tool_name, target, hashed)
                self.store.ensure_approval(rule_key, task_id, tool_name, target, hashed)
                approval_card = self._approval_card(context, result.category, target, hashed, rule_key)

        policy_decision = PolicyDecision(
            decision=decision,
            rule_id=rule_id,
            reason=reason,
            task_id=task_id,
            project=str(context.get("project") or ""),
            profile=str(context.get("profile") or ""),
            action=tool_name,
            target=target,
            args_hash=hashed,
            timestamp=utc_now(),
            budget_snapshot=snapshot,
            approval_card=approval_card,
        )
        significant = decision != "allow"
        if decision == "allow" and result.effect == "read":
            rate = float(self.config["safe_defaults"].get("read_sampling_rate", 0.1))
            sampled = int(hashed[:8], 16) / 0xFFFFFFFF < rate
        else:
            sampled = True
        if significant or sampled:
            event_id = stable_id(task_id, tool_name, target, hashed, rule_id, "policy") if significant else stable_id(tool_call_id, "policy")
            self.store.record_event(
                event_id,
                str(context.get("run_id") or context.get("session_id") or event_id),
                task_id or None,
                "policy_decision",
                policy_decision.as_dict(),
                significant,
            )
        return policy_decision

    def claim_projection(self, payload: dict[str, Any]) -> bool:
        event_id = stable_id(
            payload.get("task_id"), payload.get("action"), payload.get("target"),
            payload.get("args_hash"), payload.get("rule_id"), "projection",
        )
        return self.store.record_event(
            event_id, event_id, str(payload.get("task_id") or "") or None,
            "projection_claim", {"source_rule": payload.get("rule_id")}, False,
        )

    def post_tool_call(self, tool_name: str, arguments: dict[str, Any], context: dict[str, Any], *,
                       success: bool, error_type: str = "", error_message: str = "") -> dict[str, Any] | None:
        task_id = str(context.get("task_id") or "")
        if not task_id:
            return None
        hashed = args_hash(arguments)
        call_signature = stable_id(tool_name, hashed, self._target(tool_name, arguments))
        failure_signature = None
        if not success:
            normalized_error = " ".join(str(error_message or "").lower().split())[:300]
            failure_signature = stable_id(tool_name, error_type, normalized_error)
        event_id = stable_id(task_id, context.get("tool_call_id"), call_signature, success, failure_signature)
        self.store.add_call(event_id, task_id, call_signature, failure_signature, success)
        if failure_signature and self.store.count_signature(task_id, "failure_signature", failure_signature) >= int(self.config["anti_loop"]["max_same_failure"]):
            payload = {
                "decision": "deny", "rule_id": "same_failure_loop",
                "reason": "same failure signature reached the stop threshold",
                "task_id": task_id, "project": context.get("project", ""), "profile": context.get("profile", ""),
                "action": tool_name, "target": self._target(tool_name, arguments), "args_hash": hashed,
                "timestamp": utc_now(), "budget_snapshot": self.budget_snapshot(context, self.task_type(context)[0]),
                "approval_card": None, "failure_signature": failure_signature,
            }
            inserted = self.store.record_event(
                stable_id(task_id, failure_signature, "same_failure_loop"), str(context.get("run_id") or task_id),
                task_id, "anti_loop_stop", payload, True,
            )
            return payload if inserted else None
        return None

    def post_api_request(self, context: dict[str, Any], usage: dict[str, Any] | None,
                         assistant_tool_call_count: int) -> dict[str, Any] | None:
        task_id = str(context.get("task_id") or "")
        if not task_id:
            return None
        request_id = str(context.get("api_request_id") or context.get("request_id") or "")
        if usage:
            # Budget counts GENERATED tokens only. prompt_tokens is the full
            # re-sent context on every request (a healthy agent run exhausts a
            # prompt-inclusive budget in ~7 calls); completion tokens measure the
            # model's actual work for this task.
            generated = usage.get("completion_tokens")
            if generated is None:
                generated = usage.get("output_tokens")
            self.store.add_budget(task_id, "tokens", int(generated or 0), stable_id(task_id, request_id, "tokens"))
        # A successful API request breaks the failure streak: fallback-chain errors
        # that resolved within the same turn must not accumulate as retries.
        with self.store.connect() as connection:
            connection.execute(
                "DELETE FROM budget_ledger WHERE task_id=? AND metric='retries'", (task_id,)
            )
        idle = self.store.set_idle_turns(task_id, increment=int(assistant_tool_call_count or 0) == 0)
        task_type, _ = self.task_type(context)
        snapshot = self.budget_snapshot(context, task_type)
        exhausted = self._exhausted(snapshot, context)
        rule = None
        reason = None
        if idle >= int(self.config["anti_loop"]["max_idle_turns"]):
            rule, reason = "idle_turn_loop", f"idle turn threshold reached: {idle}"
        elif exhausted:
            rule, reason = "budget_exhausted", f"hard budget exhausted: {exhausted}"
        if not rule:
            return None
        payload = {
            "decision": "deny", "rule_id": rule, "reason": reason, "task_id": task_id,
            "project": context.get("project", ""), "profile": context.get("profile", ""),
            "action": "llm_request", "target": request_id, "args_hash": stable_id(request_id),
            "timestamp": utc_now(), "budget_snapshot": snapshot, "approval_card": None,
        }
        inserted = self.store.record_event(
            stable_id(task_id, rule, exhausted or idle), str(context.get("run_id") or task_id),
            task_id, "budget_or_loop_stop", payload, True,
        )
        return payload if inserted else None

    def api_request_error(self, context: dict[str, Any], error: Any) -> dict[str, Any] | None:
        task_id = str(context.get("task_id") or "")
        if not task_id:
            return None
        request_id = str(context.get("api_request_id") or context.get("request_id") or "")
        # Retry accounting is deliberately NOT plugin-owned: within one healthy
        # turn Hermes walks its fallback chain and fires this hook once per failed
        # provider (zai 429 -> codex 429 -> ...), so any API-error-derived retry
        # budget exhausts on infrastructure noise. Dispatcher-level task retries
        # remain the source of truth via kanban.failure_limit / task max_retries,
        # reconciled by effective_retries for reporting.
        self.store.record_event(
            stable_id(task_id, request_id, type(error).__name__, "api_error"),
            str(context.get("run_id") or task_id), task_id, "api_request_error",
            {"error": type(error).__name__}, False,
        )
        task_type, _ = self.task_type(context)
        snapshot = self.budget_snapshot(context, task_type)
        exhausted = self._exhausted(snapshot, context)
        return None
