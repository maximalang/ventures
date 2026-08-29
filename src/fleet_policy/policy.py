from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from pathlib import PurePath
from typing import Any, Literal

TASK_TYPES = {"research", "code", "review", "ops"}
TASK_LINE = re.compile(r"(?im)^\s*task_type\s*:\s*([a-z_-]+)\s*$")
TASK_TAG = re.compile(r"(?i)(?:^|[\s,;])task_type\s*=\s*([a-z_-]+)(?=$|[\s,;])")
TASK_SKILL = re.compile(r"(?i)(?:^|[\s,;])task-type-(research|code|review|ops)(?=$|[\s,;])")


@dataclass(frozen=True, slots=True)
class Classification:
    effect: Literal["read", "state_change"]
    category: str
    decision: Literal["allow", "deny", "approval_required"]
    reason: str


def infer_task_type(*values: Any) -> tuple[str | None, str | None]:
    found: list[str] = []
    for value in values:
        if isinstance(value, (list, tuple, set)):
            items = value
        else:
            items = [value]
        for item in items:
            text = str(item or "")
            found.extend(TASK_LINE.findall(text))
            found.extend(TASK_TAG.findall(text))
            found.extend(TASK_SKILL.findall(text))
    normalized = {item.lower() for item in found}
    if not normalized:
        return None, "missing task_type marker"
    if len(normalized) != 1:
        return None, "conflicting task_type markers"
    task_type = next(iter(normalized))
    if task_type not in TASK_TYPES:
        return None, f"unknown task_type: {task_type}"
    return task_type, None


def _flatten(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(f"{key} {_flatten(item)}" for key, item in value.items())
    if isinstance(value, (list, tuple, set)):
        return " ".join(_flatten(item) for item in value)
    return str(value or "")


def _protected_path(text: str, patterns: list[str]) -> bool:
    normalized = text.replace("\\", "/").lower()
    words = re.findall(r"[^\s\"']+", normalized)
    variants: list[str] = []
    for pattern in patterns:
        lowered = pattern.lower()
        variants.append(lowered)
        if lowered.startswith("**/"):
            variants.append(lowered[3:])
    for word in words:
        basename = PurePath(word).name.lower()
        if any(fnmatch.fnmatch(word, v) or fnmatch.fnmatch(basename, v) for v in variants):
            return True
    return False


READ_TOOLS = {
    "read_file", "search_files", "web_search", "web_extract", "read_preview", "read_terminal",
    "vision_analyze", "session_search", "skills_list", "skill_view", "project_list", "kanban_show",
    "kanban_list", "kanban_context", "kanban_diagnostics", "kanban_attachments", "fact_store",
}
READ_PREFIXES = ("read_", "search_", "list_", "get_", "show_", "view_", "probe_", "inspect_")
TERMINAL_TOOLS = {"terminal", "shell", "bash", "powershell", "exec", "execute_command"}
READ_COMMAND = re.compile(
    r"^\s*(?:git\s+(?:status|diff|log|show|branch\s+--show-current|rev-parse|remote\s+-v)|"
    r"(?:rg|grep|findstr|ls|dir|pwd|type|get-content|select-string|python\s+-m\s+pytest\b|npm\s+(?:test|run\s+(?:test|lint|build))\b))",
    re.I,
)
MUTATOR = re.compile(
    r"(?:^|[;&|]\s*|\b)(?:rm|del|remove-item|mv|move-item|cp|copy-item|set-content|add-content|"
    r"git\s+(?:commit|push|merge|rebase|reset|checkout|switch)|hermes\s+(?:config\s+set|plugins\s+(?:enable|disable|install|remove)|kanban\s+(?:create|comment|block|unblock|archive|assign|reassign|reclaim))|"
    r"fleet-policy\s+approve|deploy|publish)\b",
    re.I,
)


def _terminal_is_read_only(command: str) -> bool:
    if MUTATOR.search(command):
        return False
    segments = [part.strip() for part in re.split(r"&&|\|\||;", command) if part.strip()]
    return bool(segments) and all(READ_COMMAND.search(part) for part in segments)


def classify(tool_name: str, arguments: dict[str, Any], config: dict[str, Any], *, worker: bool) -> Classification:
    name = tool_name.strip().lower()
    flat = f"{name} {_flatten(arguments)}"
    lower = flat.lower()
    if _protected_path(flat, list(config["protected"]["paths"])):
        return Classification("state_change", "secret_read_or_write", "deny", "secret-bearing paths and credential stores are prohibited")
    if worker and re.search(
        r"(?:\bfleet[-_]policy(?:[-\w.\\/]*)?\s+(?:approve|reject)\b|"
        r"\b(?:decide_approval|consume_exact_approval|ensure_approval|grant_capability)\b|"
        r"\b(?:update|insert|delete)[^\n]*\bapprovals\b)", lower,
    ):
        return Classification("state_change", "worker_self_approval", "deny", "workers cannot approve their own action")
    if worker and re.search(r"\bfleet[-_]policy(?:[-\w.\\/]*)?\s+grant-capability\b", lower):
        return Classification("state_change", "worker_capability_grant", "deny", "workers cannot grant capabilities")
    if worker and re.search(r"\bhermes(?:\s+-p\s+\S+)?\s+config\s+set\s+(?:approvals|security|privacy|plugins|kanban\.dispatch)", lower):
        return Classification("state_change", "policy_control_plane_mutation", "approval_required", "control-plane security changes require owner approval")

    if name in TERMINAL_TOOLS:
        command = str(arguments.get("command") or arguments.get("cmd") or "")
        effect: Literal["read", "state_change"] = "read" if _terminal_is_read_only(command) else "state_change"
    elif name in READ_TOOLS or name.startswith(READ_PREFIXES):
        # fact_store has mutating actions despite its read-like name.
        if name == "fact_store" and str(arguments.get("action") or "") in {"add", "update", "remove"}:
            effect = "state_change"
        else:
            effect = "read"
    else:
        effect = "state_change"

    if effect == "read":
        return Classification(effect, "read_only", "allow", "read-only action")

    branches = "|".join(re.escape(branch) for branch in config["protected"]["branches"])
    rules = [
        # Serious-only escalation classes.
        (r"\b(?:mass outreach|bulk (?:message|email|dm)|unsolicited campaign|scrape and send|spam)\b", "mass_outreach_or_bulk_messaging", "approval_required"),
        (r"\b(?:new paid capability|payment instrument|payment rail|open paid account)\b", "new_paid_capability_or_payment_rail", "approval_required"),
        (r"\b(?:kyc|phone verification|domain owner|bank owner|domain or bank ownership)\b", "phone_kyc_domain_or_bank_owner_action", "approval_required"),
        (r"\b(?:sign contract|legal commitment|regulated claim|material reputation|defamation|guaranteed return)\b", "legal_or_material_reputation_risk", "approval_required"),
        (r"\b(?:transfer ownership|root access|admin access expansion|recovery key|change owner)\b", "ownership_or_root_access_change", "approval_required"),
        (r"(?:\b(?:irreversible|unrecoverable|without backup|force[- ]?push|push\s+(?:-f|--force)|reset\s+--hard|filter-branch|drop\s+table|truncate)\b|(?:^|\s)rm\s+-rf\b)", "irreversible_data_loss", "approval_required"),
        (r"\b(?:material security policy|material privacy policy|disable encryption|disable audit)\b", "material_security_or_privacy_policy_change", "approval_required"),
        # Autonomous actions that require role/evidence gates in runtime.
        (rf"(?:\b(?:push|merge)[^\n]*(?:\b(?:{branches})\b|refs/heads/(?:{branches}))|\bgh\s+pr\s+merge\b)", "release_to_protected_branch", "allow"),
        (r"\b(?:deploy|release to production|release to staging|production deploy|staging deploy)\b", "deploy_external_runtime", "allow"),
        (r"\b(?:publish|publication|public post|product launch|content update|advertis|campaign)\b", "public_product_action", "allow"),
        (r"\b(?:pay|payment|purchase|ad spend|experiment spend|transfer funds|charge|stripe|yookassa|/charges)\b", "financial_action", "allow"),
        (r"(?:\b(?:delete|remove|cleanup|purge|git\s+clean|branch\s+-[dD]|tag\s+-d|stash\s+(?:drop|clear)|checkout\s+--\s+\.)\b|(?:^|\s)rm\s)", "destructive_change", "allow"),
        (r"\b(?:create|open|register)[^\n]*(?:free service account|free account|trial account)\b", "free_service_account", "allow"),
    ]
    for pattern, category, decision in rules:
        if re.search(pattern, lower, re.I):
            reason = f"{category} requires serious-risk approval" if decision == "approval_required" else f"{category} is autonomous after evidence gates"
            return Classification(effect, category, decision, reason)

    if re.search(r"\bgit\s+(?:commit|push|merge)\b", lower):
        return Classification(effect, "repository_change", "allow", "repository changes are autonomous within project rules")
    return Classification(effect, "scoped_state_change", "allow", "scoped state change is autonomous")


def effective_retries(policy_max: int, kanban_max: int | None, failure_limit: int | None) -> int:
    values = [policy_max]
    values.extend(value for value in (kanban_max, failure_limit) if isinstance(value, int) and value > 0)
    return min(values)
