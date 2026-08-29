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
        r"\b(?:decide_approval|consume_exact_approval|ensure_approval)\b|"
        r"\b(?:update|insert|delete)[^\n]*\bapprovals\b)", lower,
    ):
        return Classification("state_change", "worker_self_approval", "deny", "workers cannot approve their own action")

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
        (r"\b(?:deploy|release|production deploy|staging deploy)\b", "deploy_external_runtime"),
        (r"\b(?:publish|publication|outreach|advertis|campaign|newsletter|send[_ -]?(?:message|email)|public post)\b", "public_outreach_or_publication"),
        (r"\b(?:pay|payment|purchase|subscription|billing|change budget)\b", "payments_subscriptions_or_budget"),
        (r"(?:\b(?:delete|remove|cleanup|purge|drop\s+table|truncate|irreversible|destructive migration)\b|(?:^|\s)rm\s)", "destructive_delete_cleanup_or_migration"),
        (r"\b(?:git\s+clean|branch\s+-[dD]|filter-branch|tag\s+-d|stash\s+(?:drop|clear)|checkout\s+--\s+\.)\b", "destructive_delete_cleanup_or_migration"),
        (r"\b(?:force[- ]?push|push\s+(?:-f|--force)|reset\s+--hard|rewrite history)\b", "rewrite_history"),
        (rf"\b(?:push|merge)[^\n]*(?:\b(?:{branches})\b|refs/heads/(?:{branches}))", "protected_branch_push_or_merge"),
        (r"\b(?:new credential|grant(?:\s+new)?(?:\s+api\s+key)?\s+permission|access grant|create api key|rotate token)\b", "new_credentials_or_permissions"),
        (r"\b(?:change|modify|disable|enable)[^\n]*(?:security|privacy|acl|firewall|approval mode)\b", "security_or_privacy_change"),
        (r"\b(?:private\s*(?:to|->)\s*public|visibility\s+(?:=\s*)?public)\b", "private_to_public"),
    ]
    for pattern, category in rules:
        if re.search(pattern, lower, re.I):
            return Classification(effect, category, "approval_required", f"{category} requires user approval")

    if re.search(r"\bgit\s+(?:commit|push)\b", lower):
        if re.search(r"\bcodex/[a-z0-9._/-]+", lower):
            return Classification(effect, "commit_push_codex_branch", "allow", "commit/push to codex/* is autonomous")
        if "push" in lower:
            return Classification(effect, "unscoped_git_push", "approval_required", "push is allowed autonomously only when codex/* is explicit")
    return Classification(effect, "scoped_state_change", "allow", "scoped state change is autonomous")


def effective_retries(policy_max: int, kanban_max: int | None, failure_limit: int | None) -> int:
    values = [policy_max]
    values.extend(value for value in (kanban_max, failure_limit) if isinstance(value, int) and value > 0)
    return min(values)
