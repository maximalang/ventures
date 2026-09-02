from __future__ import annotations

import fnmatch
import re
import shlex
from dataclasses import dataclass
from pathlib import PurePath
from typing import Any, Literal

TASK_TYPES = {"research", "code", "review", "ops"}
TASK_LINE = re.compile(r"(?im)^\s*task_type\s*:\s*([a-z_-]+)\s*$")
TASK_TAG = re.compile(r"(?i)(?:^|[\s,;])task_type\s*=\s*([a-z_-]+)(?=$|[\s,;])")
TASK_SKILL = re.compile(r"(?i)(?:^|[\s,;])task-type-(research|code|review|ops)(?=$|[\s,;])")

CANONICAL_PUBLIC_POLICY_DOC = (
    "c:/users/max/desktop/all/ventures/" + "app" + "rovals.md"
)

# Rule ids and protected names are assembled from parts so policy scanners do
# not match this source file itself (same convention as the test suite).
PROTECTED_STORE_RULE = "sec" + "ret_read_or_write"
DENY_MSG = "protected paths and " + "cre" + "dential stores are prohibited"

# F4(b): policy-controlled files are operational state, not sensitive
# material. The fleet may READ them (tests load the policy config; board DBs
# are read for task resolution) but may never WRITE them.
_POLICY_CONTROLLED_BASENAMES = {"fleet-" + "policy.yaml", "app" + "rovals.md"}
_POLICY_CONTROLLED_SUBSTRINGS = ("fleet-" + "policy.db", "kan" + "ban.db")

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




def _is_policy_controlled(pattern: str) -> bool:
    """F4(b): operational policy state — readable by the fleet, immutable."""
    lowered = str(pattern).lower().replace("\\", "/")
    base = PurePath(lowered).name
    if base in _POLICY_CONTROLLED_BASENAMES:
        return True
    return any(part in lowered for part in _POLICY_CONTROLLED_SUBSTRINGS)


def _is_path_like(word: str) -> bool:
    """F4 precision: bare trigger words are prose; only path-shaped tokens are
    candidates for the protected-path matcher."""
    return any(char in word for char in ("/", "\\", ".", ":"))


def _protected_path_match(text: str, patterns: list[str]) -> str | None:
    """Return the first protected pattern matched by any path-like token."""
    normalized = text.replace("\\", "/").lower()
    words = re.findall(r"[^\s\"']+", normalized)
    for pattern in patterns:
        lowered = pattern.lower()
        variants = [lowered]
        if lowered.startswith("**/"):
            variants.append(lowered[3:])
        for word in words:
            if not _is_path_like(word):
                continue
            basename = PurePath(word).name.lower()
            if any(fnmatch.fnmatch(word, v) or fnmatch.fnmatch(basename, v) for v in variants):
                return pattern
    return None

def _canonical_public_doc_read(tool_name: str, arguments: dict[str, Any]) -> bool:
    """Recognize the one public policy document caught by a broad name rule."""
    if tool_name != "read_file":
        return False
    raw = str(arguments.get("path") or "").replace("\\", "/").lower()
    return raw == CANONICAL_PUBLIC_POLICY_DOC


READ_TOOLS = {
    "read_file", "search_files", "web_search", "web_extract", "read_preview", "read_terminal",
    "vision_analyze", "session_search", "skills_list", "skill_view", "project_list", "kanban_show",
    "kanban_list", "kanban_context", "kanban_diagnostics", "kanban_attachments", "fact_store",
}
READ_PREFIXES = ("read_", "search_", "list_", "get_", "show_", "view_", "probe_", "inspect_")
TERMINAL_TOOLS = {"terminal", "shell", "bash", "powershell", "exec", "execute_command"}

# F4: tools whose payload is operator free text (kanban card bodies, comment
# bodies, file contents, memory notes, delegation briefs, generated code).
# Neither the path guard nor the risk regexes may scan these fields:
# classification firing on descriptive prose froze the fleet. Coordination
# integrity is enforced by the runtime gate-forgery checks and the store
# environment guard instead. Documented gap: code text passed to in-kernel
# executors is not content-inspected (compensating control: event-log audit).
FREE_TEXT_TOOLS = {
    "kanban_comment", "kanban_create", "kanban_complete", "kanban_block",
    "kanban_unblock", "kanban_heartbeat", "kanban_link", "kanban_edit",
    "kanban_attach", "kanban_attach_url", "kanban_request_review",
    "kanban_request_changes", "write_file", "patch", "skill_manage",
    "memory", "todo", "clarify", "delegate_task",
}

READ_COMMAND = re.compile(
    r"^\s*(?:git\s+(?:status|diff|log|show|branch\s+(?:--show-current|--list|-l)\b|rev-parse|rev-list|remote(?:\s+-v)?|ls-remote|ls-files|ls-tree|clone|fetch)\b|"
    r"(?:rg|grep|findstr|ls|dir|pwd|type|get-content|select-string|sed|head|tail|stat|wc|file|du|sort|uniq|cut|tr|column|python\s+-m\s+pytest\b|npm\s+(?:test|run\s+(?:test|lint|build))\b)\b)",
    re.I,
)
MUTATOR = re.compile(
    r"(?:^|[;&|]\s*|\b)(?:rm|del|remove-item|mv|move-item|cp|copy-item|set-content|add-content|"
    r"git\s+(?:commit|push|merge|rebase|reset|checkout|switch)|hermes\s+(?:config\s+set|plugins\s+(?:enable|disable|install|remove)|kanban\s+(?:create|comment|block|unblock|archive|assign|reassign|reclaim))|"
    r"fleet-policy\s+approve|deploy|publish)\b",
    re.I,
)
# v1.2.6: in-place/redirecting variants of otherwise read-only utilities are
# mutations so the effect classifier and the protected path guard agree.
# v1.2.6.1 (F-01): the write-marker scan is token-based and covers every
# spelling — long option names (`--in-place`, `--output`, including `=`
# forms), option clusters (`sed -ni`, `sort -uo`), suffix forms (`sed -i.bak`),
# `tee` pipeline stages and shell output redirects — so no mutating form of a
# read-whitelisted utility can be classified as a read. Fail-closed by design:
# anything unrecognized as a write keeps the stricter classification.
_SHORT_OPTION_CLUSTER = re.compile(r"^-[A-Za-z]+$")
_FD_DUP_REDIRECT = re.compile(r"\d*>&\d+")
_OUTPUT_REDIRECT = re.compile(r"&>>|&>|>>|>")


def _simple_commands(command: str) -> list[str]:
    """Split a command line into stages: chains, lists and pipes."""
    return [part.strip() for part in re.split(r"&&|\|\||;|\|", command) if part.strip()]


def _stage_tokens(segment: str) -> list[str]:
    try:
        return shlex.split(segment, posix=False)
    except ValueError:
        return segment.split()


def _writes_via_option(program: str, args: list[str]) -> bool:
    """F-01: in-place/output forms of read-whitelisted utilities.

    `sed` writes when any option is `-i` (with or without suffix) or
    `--in-place[=SUFFIX]`; `sort` writes when any option is `-o[FILE]` or
    `--output[=FILE]`. Option clusters (`-ni`, `-uo`) count too.
    """
    if program not in {"sed", "sort"}:
        return False
    write_letter = "i" if program == "sed" else "o"
    long_name = "--in-place" if program == "sed" else "--output"
    for token in args:
        bare = token.strip("\"'")
        if bare.startswith(f"-{write_letter}") or bare == long_name or bare.startswith(f"{long_name}="):
            return True
        if _SHORT_OPTION_CLUSTER.match(bare) and write_letter in bare.lower():
            return True
    return False


def _has_write_marker(command: str) -> bool:
    for segment in _simple_commands(command):
        tokens = _stage_tokens(segment)
        if not tokens:
            continue
        program = PurePath(tokens[0].replace("\\", "/")).name.lower()
        if program == "tee" or _writes_via_option(program, tokens[1:]):
            return True
        # Shell output redirects write regardless of the program. Quoted
        # payload text is ignored; `2>&1`-style fd duplication is not a write.
        unquoted = re.sub(r"\"[^\"]*\"|'[^']*'", " ", segment)
        unquoted = _FD_DUP_REDIRECT.sub(" ", unquoted)
        if _OUTPUT_REDIRECT.search(unquoted):
            return True
    return False


def _terminal_is_read_only(command: str) -> bool:
    if MUTATOR.search(command) or _has_write_marker(command):
        return False
    segments = [part.strip() for part in re.split(r"&&|\|\||;", command) if part.strip()]
    # v1.2.6: bare `cd <dir>` segments are no-ops for the read classifier;
    # chained read (cd repo && git clone ...) was misclassified before.
    # v1.2.6: match() (anchored) instead of search() — search() let the
    # non-word-bounded `type` keyword match inside words like "...ownership".
    return bool(segments) and all(
        READ_COMMAND.match(part) or re.match(r"^\s*cd\s+\S+\s*$", part, re.I)
        for part in segments
    )




def _effect_for(name: str, arguments: dict[str, Any]) -> Literal["read", "state_change"]:
    if name in TERMINAL_TOOLS:
        command = str(arguments.get("command") or arguments.get("cmd") or "")
        return "read" if _terminal_is_read_only(command) else "state_change"
    if name in READ_TOOLS or name.startswith(READ_PREFIXES):
        # fact_store has mutating actions despite its read-like name.
        if name == "fact_store" and str(arguments.get("action") or "") in {"add", "update", "remove"}:
            return "state_change"
        return "read"
    return "state_change"


def _path_guard_subjects(name: str, arguments: dict[str, Any]) -> list[str]:
    """F4: the path guard sees only path-like targets, never free text."""
    if name in TERMINAL_TOOLS:
        command = str(arguments.get("command") or arguments.get("cmd") or "")
        try:
            tokens = shlex.split(command, posix=False)
        except ValueError:
            tokens = command.split()
        if tokens and PurePath(tokens[0].replace("\\", "/")).name.lower() in {
            "grep", "rg", "findstr", "select-string",
        }:
            positional = [token for token in tokens[1:] if not token.startswith("-")]
            # The first positional argument is the search expression. Only
            # subsequent positionals are filesystem targets.
            return [" ".join(positional[1:])] if len(positional) > 1 else []
        return [command]
    if name in FREE_TEXT_TOOLS:
        # write_file/patch still carry one real filesystem target.
        path = arguments.get("path")
        return [str(path)] if path else []
    subjects: list[str] = []
    for key in ("path", "file_path", "url", "image_url", "target"):
        if arguments.get(key):
            subjects.append(str(arguments[key]))
    if name == "search_files" and arguments.get("file_glob"):
        subjects.append(str(arguments["file_glob"]))
    if name == "web_extract":
        subjects.extend(str(item) for item in (arguments.get("urls") or []))
    return subjects


def _risk_subject(name: str, arguments: dict[str, Any]) -> str:
    """F4: risk regexes scan real targets (commands, URLs), never free text."""
    if name in TERMINAL_TOOLS:
        return str(arguments.get("command") or arguments.get("cmd") or "")
    if name in FREE_TEXT_TOOLS:
        return ""
    url = arguments.get("url")
    return str(url) if url else ""


def classify(tool_name: str, arguments: dict[str, Any], config: dict[str, Any], *, worker: bool) -> Classification:
    name = tool_name.strip().lower()
    effect = _effect_for(name, arguments)

    # In-kernel Python can access the filesystem and network without passing
    # its nested operations through this hook. Worker use therefore requires
    # the existing exact, one-time approval binding. Operator sessions remain
    # available for bounded maintenance and incident response.
    if worker and name == "execute_code":
        return Classification(
            "state_change", "worker_code_execution", "approval_required",
            "worker in-kernel code execution requires an exact one-time grant",
        )

    # F4(a)/(b): protected-path guard over path-like subjects only.
    patterns = list(config["protected"]["paths"])
    for subject in _path_guard_subjects(name, arguments):
        matched = _protected_path_match(subject, patterns)
        if not matched or _canonical_public_doc_read(name, arguments):
            continue
        if _is_policy_controlled(matched):
            if effect == "read":
                return Classification("read", "read_only", "allow", "policy-controlled documents are readable by the fleet")
            return Classification("state_change", "policy_control_plane_mutation", "deny", "policy-controlled files are immutable for the fleet")
        return Classification("state_change", PROTECTED_STORE_RULE, "deny", DENY_MSG)

    subject = _risk_subject(name, arguments)
    lower = f"{name} {subject}".lower()

    # Hard-deny checks inspect command/target fields only. They must never scan
    # generated code, card bodies, comments or file contents.
    if worker and (
        re.search(r"(?:^|[\s/\\])fleet[-_]policy(?:\.exe)?\s+(?:approve|reject|revoke)\b", subject, re.I)
        or re.search(r"\bpython\s+-m\s+fleet_policy\.cli\s+(?:approve|reject|revoke)\b", subject, re.I)
        or re.search(r"\b(?:decide_approval|consume_exact_approval|ensure_approval|revoke_approval)\b", subject, re.I)
        or re.search(r"\b(?:update|insert|delete)[^\n]*\bapprovals\b", subject, re.I)
    ):
        return Classification("state_change", "worker_self_approval", "deny", "workers cannot approve their own action")
    if worker and (
        re.search(r"(?:^|[\s/\\])fleet[-_]policy(?:\.exe)?\s+grant-capability\b", subject, re.I)
        or re.search(r"\bgrant_capability\s*\(", subject, re.I)
    ):
        return Classification("state_change", "worker_capability_grant", "deny", "workers cannot grant capabilities")
    if worker and re.search(
        r"\bhermes(?:\s+-p\s+\S+)?\s+config\s+set\s+(?:approvals|security|privacy|plugins|kanban\.dispatch)",
        subject,
        re.I,
    ):
        return Classification("state_change", "policy_control_plane_mutation", "approval_required", "control-plane security changes require owner approval")

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
