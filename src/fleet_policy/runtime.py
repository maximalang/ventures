from __future__ import annotations

from datetime import datetime, timezone
import time
import re
from pathlib import Path
from typing import Any

from .config import load_config
from .models import PolicyDecision
from .policy import Classification, classify, infer_task_type
from .redaction import args_hash, redact, stable_id
from .storage import PolicyStore, utc_now


class FleetPolicyRuntime:
    EVIDENCE_GATED_CATEGORIES = {
        "release_to_protected_branch",
        "deploy_external_runtime",
        "public_product_action",
        "financial_action",
        "destructive_change",
    }

    def __init__(self, root: str | Path, *, config_path: str | Path | None = None,
                 db_path: str | Path | None = None):
        self.root = Path(root)
        self.config = load_config(config_path or self.root / "config" / "fleet-policy.yaml")
        self.store = PolicyStore(db_path or self.root / ".state" / "fleet-policy.db")
        self.store.migrate()

    def task_type(self, context: dict[str, Any]) -> tuple[str | None, str | None]:
        return infer_task_type(context.get("task_body"), context.get("comments"), context.get("skills"))

    @staticmethod
    def _run_key(context: dict[str, Any]) -> str:
        return str(context.get("current_run_id") or context.get("run_id") or "")

    GATE_AUTHORS = {
        "ci": {"tech", "qa"}, "review": {"qa"}, "qa": {"qa"},
        "rollback": {"tech", "operations"}, "backup": {"operations"},
        "finance": {"finance"}, "company_decision": {"company"},
        "scope": {"qa", "operations"},
    }

    def missing_gates(self, category: str, context: dict[str, Any]) -> list[str]:
        required = list(self.config.get("evidence_gates", {}).get(category, []))
        task_type, _ = self.task_type(context)
        if task_type == "review":
            required = [gate for gate in required if gate not in {"review", "qa"}]
        if not required:
            return []
        records = context.get("comment_records") or []
        missing: list[str] = []
        for gate in required:
            marker = "decision:company=go" if gate == "company_decision" else f"gate:{gate}=pass"
            allowed_authors = self.GATE_AUTHORS.get(gate, set())
            if not any(
                any(line.strip().lower() == marker for line in str(record.get("body") or "").splitlines())
                and (not allowed_authors or str(record.get("author") or "").lower() in allowed_authors)
                and not (gate in {"review", "qa"} and str(record.get("author") or "").lower() == str(context.get("assignee") or "").lower())
                for record in records
            ):
                missing.append(gate)
        return missing

    def gate_comment_allowed(self, text: str, context: dict[str, Any]) -> bool:
        lowered = text.lower()
        marker = re.search(r"gate:([a-z_]+)=pass", lowered)
        gate = marker.group(1) if marker else ("company_decision" if "decision:company=go" in lowered else "")
        if not gate:
            return True
        profile = str(context.get("profile") or "").lower()
        if profile not in self.GATE_AUTHORS.get(gate, set()):
            return False
        return not (gate in {"review", "qa"} and profile == str(context.get("assignee") or "").lower())

    @staticmethod
    def _amount_rub(arguments: dict[str, Any]) -> int | None:
        raw = arguments.get("amount_rub")
        if raw is None:
            match = re.search(r"(?i)amount_rub\s*[=:]\s*(\d+)", str(arguments))
            raw = match.group(1) if match else None
        try:
            return int(raw) if raw is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _capability_id(arguments: dict[str, Any]) -> str:
        raw = arguments.get("capability_id")
        if raw:
            return str(raw)
        match = re.search(r"(?i)capability_id\s*[=:]\s*([a-z0-9._-]+)", str(arguments))
        return match.group(1) if match else ""

    def budget_snapshot(self, context: dict[str, Any], task_type: str | None) -> dict[str, Any]:
        task_id = str(context.get("task_id") or "")
        now_epoch = int(datetime.now(timezone.utc).timestamp())
        run_key = self._run_key(context)
        if task_id and run_key:
            claimed_at = self.store.touch_run(task_id, run_key, now_epoch)
            used = self.store.budget_for_run(task_id, run_key)
            used["wall_clock_minutes"] = max(0, (now_epoch - claimed_at) // 60)
        else:
            used = self.store.budget(task_id) if task_id else {"tokens": 0, "tool_calls": 0, "retries": 0}
            started = context.get("started_at")
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
        else:
            result = classify(tool_name, arguments, self.config, worker=worker)
            if worker and context.get("task_status") == "blocked" and result.effect != "read":
                result = Classification("state_change", "task_already_blocked", "deny", "Kanban task is blocked")

        if worker:
            flat_args = str(arguments)
            if tool_name.lower() in {"terminal", "shell", "bash", "exec"} and re.search(r"(?i)hermes\s+kanban[^\n]*comment[^\n]*(?:gate:|decision:company=go)", flat_args):
                result = Classification("state_change", "gate_forgery", "deny", "role gates must be written through kanban_comment by the current profile")
            elif tool_name.lower() == "kanban_comment":
                text = str(arguments.get("text") or arguments.get("body") or arguments.get("comment") or "")
                if not self.gate_comment_allowed(text, context):
                    result = Classification("state_change", "gate_forgery", "deny", "current profile cannot attest this gate")

        # Evidence gates protect consequential transitions, not the ordinary
        # implementation/review work that produces their evidence. Applying
        # gates to every configured category creates a lifecycle deadlock: a
        # worker cannot edit or test before it has backup/scope/review output.
        missing = (
            self.missing_gates(result.category, context)
            if worker
            and result.decision == "allow"
            and result.category in self.EVIDENCE_GATED_CATEGORIES
            else []
        )
        deny_nonce: str | None = None
        if missing:
            result = Classification(
                result.effect, "evidence_gate_missing", "deny",
                "fleet must satisfy gates before execution: " + ", ".join(missing),
            )
            if worker and (self.task_type(context)[0] or "") == "review":
                # v1.2.10 item C — review-probe nonce lane. A review task
                # probing a gated transition is an expected QA probe, not a
                # worker failure: the refusal stays fail-closed but carries a
                # stable per-run nonce and records exactly one artifact per
                # run. It must not grow loop counters (post_tool_call skips
                # probe failures) and the plugin must not project/block the
                # card on it; the tool-call budget above still charges every
                # probe so runaway review runs keep their stop class.
                run_key = self._run_key(context) or "session"
                deny_nonce = stable_id(task_id, run_key, "review_probe_nonce")
                self.store.record_event(
                    stable_id(task_id, run_key, "review_probe_nonce", "artifact"),
                    run_key, task_id or None, "review_probe_nonce",
                    {"nonce": deny_nonce, "rule_id": result.category}, False,
                )

        spend: tuple[int, str, str] | None = None
        if result.category == "financial_action" and result.decision == "allow":
            amount = self._amount_rub(arguments)
            capability_id = self._capability_id(arguments)
            project = str(context.get("project") or "")
            if amount is None or amount <= 0:
                result = Classification(result.effect, "financial_metadata_missing", "deny", "financial action requires positive amount_rub")
            else:
                spend = (amount, capability_id, project)
                if not capability_id or not self.store.capability_active(capability_id, project):
                    result = Classification(result.effect, "new_paid_capability_or_payment_rail", "approval_required", "a scoped active payment capability is required")

        snapshot = self.budget_snapshot(context, task_type)
        exhausted = self._exhausted(snapshot, context) if worker else None
        blocked_read = context.get("task_status") == "blocked" and result.effect == "read"
        if exhausted and not blocked_read:
            result = Classification(result.effect, "budget_exhausted", "deny", f"hard budget exhausted: {exhausted}")
        elif worker and not blocked_read and self.store.count_signature(
            task_id, "call_signature", call_signature, self._run_key(context) or None
        ) >= int(self.config["anti_loop"]["max_identical_calls"]):
            result = Classification(result.effect, "identical_call_loop", "deny", "maximum identical calls reached")

        if worker and task_type:
            run_key = self._run_key(context) or None
            event_id = stable_id(task_id, tool_call_id, "tool_call")
            self.store.add_budget(task_id, "tool_calls", 1, event_id, run_key)
            self.store.add_budget(task_id, "tool_calls", 1, event_id)
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

        if decision == "allow" and spend and task_id:
            amount, capability_id, project = spend
            spend_id = stable_id(task_id, tool_call_id, "spend")
            if rule_id == "approved_once":
                self.store.reserve_spend(spend_id, task_id, project, amount, capability_id or "one-time-approval")
            else:
                mandate = self.config["financial_mandate"]
                status = self.store.authorize_and_reserve_spend(
                    spend_id, task_id, project, amount, capability_id,
                    int(mandate["max_transaction"]), int(mandate["max_monthly_per_project"]),
                )
                if status != "reserved":
                    rule_id = "new_paid_capability_or_payment_rail" if status == "capability_missing" else "financial_over_budget"
                    decision = "approval_required"
                    reason = f"financial mandate blocked action: {status}"
                    rule_key = stable_id(task_id, tool_name, target, hashed)
                    self.store.ensure_approval(rule_key, task_id, tool_name, target, hashed)
                    approval_card = self._approval_card(context, rule_id, target, hashed, rule_key)

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
            pattern_category=result.category,
            call_index=max(1, int(snapshot.get("used", {}).get("tool_calls", 0))),
            deny_nonce=deny_nonce,
        )
        notify = decision == "approval_required" or rule_id in {"secret_read_or_write", "worker_self_approval"}
        if decision == "allow" and result.effect == "read":
            rate = float(self.config["safe_defaults"].get("read_sampling_rate", 0.1))
            sampled = int(hashed[:8], 16) / 0xFFFFFFFF < rate
        else:
            sampled = True
        important = decision != "allow"
        payload = policy_decision.as_dict()
        payload["task_status"] = str(context.get("task_status") or "unknown")
        payload["board"] = str(context.get("board") or "")
        payload["run_key"] = self._run_key(context) or "session"
        if important or sampled:
            if decision == "deny":
                event_id = stable_id(task_id, rule_id, payload["task_status"], payload["run_key"], "policy")
            elif important:
                event_id = stable_id(task_id, tool_name, target, hashed, rule_id, "policy")
            else:
                event_id = stable_id(tool_call_id, "policy")
            self.store.record_event(
                event_id,
                str(context.get("run_id") or context.get("session_id") or event_id),
                task_id or None,
                "policy_decision",
                payload,
                notify,
            )
        return policy_decision

    @staticmethod
    def projection_event_id(payload: dict[str, Any]) -> str:
        return stable_id(
            payload.get("task_id"), payload.get("rule_id"),
            payload.get("task_status") or "unknown", payload.get("run_key") or "session", "projection",
        )

    def claim_projection(self, payload: dict[str, Any]) -> bool:
        event_id = self.projection_event_id(payload)
        return self.store.record_event(
            event_id, event_id, str(payload.get("task_id") or "") or None,
            "projection_claim", {"source_rule": payload.get("rule_id")}, False,
        )

    def release_projection(self, payload: dict[str, Any]) -> bool:
        return self.store.delete_event(self.projection_event_id(payload))

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
            if (self.task_type(context)[0] or "") == "review" and error_type == "review_probe_nonce":
                # v1.2.10 item C — the probe refusal is an expected artifact:
                # no call ledger row and no failure-signature accounting, so
                # reviewing gates can never escalate into same_failure_loop.
                # Budget was already charged at pre_tool_call.
                return None
        event_id = stable_id(task_id, context.get("tool_call_id"), call_signature, success, failure_signature)
        run_key = self._run_key(context) or None
        projection_run_key = run_key or "session"
        self.store.add_call(event_id, task_id, call_signature, failure_signature, success, run_key)
        tool_call_id = str(context.get("tool_call_id") or "")
        if tool_call_id:
            self.store.settle_spend(stable_id(task_id, tool_call_id, "spend"), success)
        if failure_signature and self.store.count_signature(
            task_id, "failure_signature", failure_signature, run_key
        ) >= int(self.config["anti_loop"]["max_same_failure"]):
            if self.store.has_expected_failure(task_id, failure_signature, run_key):
                # v1.2.10 item D — blast-radius override: this exact failure
                # signature was marked expected for this task/run by an
                # out-of-band operator decision (audited in failure_overrides
                # + a significant event), so the stop event must not fire.
                # The counter keeps being observed on later failures; the
                # override simply removes this signature from the stop class.
                return None
            payload = {
                "decision": "deny", "rule_id": "same_failure_loop",
                "reason": "same failure signature reached the stop threshold",
                "task_id": task_id, "project": context.get("project", ""), "profile": context.get("profile", ""),
                "action": tool_name, "target": self._target(tool_name, arguments), "args_hash": hashed,
                "timestamp": utc_now(), "budget_snapshot": self.budget_snapshot(context, self.task_type(context)[0]),
                "approval_card": None, "failure_signature": failure_signature,
                "task_status": str(context.get("task_status") or "unknown"),
                "board": str(context.get("board") or ""),
                "run_key": projection_run_key,
            }
            inserted = self.store.record_event(
                stable_id(task_id, projection_run_key, failure_signature, "same_failure_loop"),
                projection_run_key, task_id, "anti_loop_stop", payload, True,
            )
            return payload if inserted else None
        return None

    def post_api_request(self, context: dict[str, Any], usage: dict[str, Any] | None,
                         assistant_tool_call_count: int) -> dict[str, Any] | None:
        task_id = str(context.get("task_id") or "")
        if not task_id:
            return None
        request_id = str(
            context.get("api_request_id")
            or context.get("request_id")
            or stable_id(task_id, time.time_ns(), usage or {})
        )
        if usage:
            # Budget counts GENERATED tokens only. prompt_tokens is the full
            # re-sent context on every request (a healthy agent run exhausts a
            # prompt-inclusive budget in ~7 calls); completion tokens measure the
            # model's actual work for this task.
            generated = usage.get("completion_tokens")
            if generated is None:
                generated = usage.get("output_tokens")
            run_key = self._run_key(context) or None
            event_id = stable_id(task_id, request_id, "tokens")
            self.store.add_budget(task_id, "tokens", int(generated or 0), event_id, run_key)
            self.store.add_budget(task_id, "tokens", int(generated or 0), event_id)
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
        request_id = str(
            context.get("api_request_id")
            or context.get("request_id")
            or stable_id(task_id, time.time_ns(), "api_error")
        )
        error_type = str(error.get("type") or "unknown") if isinstance(error, dict) else type(error).__name__
        # Retry accounting is deliberately NOT plugin-owned: within one healthy
        # turn Hermes walks its fallback chain and fires this hook once per failed
        # provider (zai 429 -> codex 429 -> ...), so any API-error-derived retry
        # budget exhausts on infrastructure noise. Dispatcher-level task retries
        # remain the source of truth via kanban.failure_limit / task max_retries.
        self.store.record_event(
            stable_id(task_id, request_id, error_type, "api_error"),
            str(context.get("run_id") or task_id), task_id, "api_request_error",
            {"error": error_type}, False,
        )
        return None
