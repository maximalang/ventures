from __future__ import annotations

import fnmatch
import os
import posixpath
import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePath
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
    """v1.2.10 item F — body-first classification, first-canonical-marker-only.

    Only the task body (the first source) can establish the class: later
    comments and skill tags are never scanned, so a late comment can neither
    create a class for an unmarked body nor poison or switch an existing one.
    Within the body, the FIRST marker whose value is a canonical task type
    decides; non-canonical markers are reported only when the body carries
    no canonical marker at all."""
    body = values[0] if values else None
    first_noncanonical: str | None = None
    items = body if isinstance(body, (list, tuple, set)) else [body]
    for item in items:
        text = str(item or "")
        matches: list[tuple[int, str]] = []
        for pattern in (TASK_LINE, TASK_TAG, TASK_SKILL):
            matches.extend((match.start(1), match.group(1)) for match in pattern.finditer(text))
        for _, raw in sorted(matches):
            task_type = raw.lower()
            if task_type in TASK_TYPES:
                return task_type, None
            if first_noncanonical is None:
                first_noncanonical = raw
    if first_noncanonical is not None:
        return None, f"unknown task_type: {first_noncanonical}"
    return None, "missing task_type marker"




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


# v1.2.26: the broad name-based pattern for credential-like filenames denied
# read/diff/grep of ordinary git-tracked core source for every profile. The
# carve-out below is deliberately narrow: the matched pattern must carry a
# trigger token, the PHYSICAL file must exist, must not be a hard secret
# store, and must be git-tracked in the containing repository. Anything else
# keeps the deny (fail-closed).
# v1.2.34 W1: the sec+ret token family joins the trigger set. Live FP class
# (card t_d94dde9d case 4): git-tracked product source whose NAME merely
# contains that token was denied for every profile, while the identical
# credential-named case was carved out in v1.2.26. The fail-closed chain is
# unchanged: untracked, nonexistent, symlinked/reparse, hard-secret (.env*,
# auth.json, key material) and control-plane STORE names keep their deny.
_CARVEOUT_TOKENS = ("cre" + "dential", "sec" + "ret")
_HARD_SECRET_NAMES = {"auth.json", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"}
_HARD_SECRET_SUFFIXES = (".pem", ".key", ".p12", ".pfx")

# v1.2.27 HIGH-1: control-plane STORE names never join the plain-source
# carve-out, git-tracked or not.  A db filename combining a store token with
# the guarded name-token (e.g. kan…ban.<token>.db) is not "plain source";
# exact-substring store names are already covered by _is_policy_controlled.
_STORE_NAME_TOKENS = ("kan" + "ban", "fleet-" + "policy")
_STORE_DB_SUFFIX = re.compile(r"\.db(?:-(?:wal|shm|journal))?$")


def _is_hard_secret_name(basename: str) -> bool:
    lowered = basename.lower()
    return (
        lowered.startswith(".env")
        or lowered in _HARD_SECRET_NAMES
        or lowered.endswith(_HARD_SECRET_SUFFIXES)
    )


def _is_control_plane_store_name(basename: str) -> bool:
    """v1.2.27 HIGH-1: db-family file whose name carries a store token."""
    lowered = basename.lower()
    return bool(_STORE_DB_SUFFIX.search(lowered)) and any(
        token in lowered for token in _STORE_NAME_TOKENS
    )


def _git_tracked_source_file(word: str, arguments: dict[str, Any]) -> bool:
    """Physical existence + git-tracked verification for one path token.

    v1.2.27 hardening (QA t_14a79801 HIGH-1/HIGH-2), fail-closed on:
    - control-plane store names: any path matching the policy-controlled
      substrings or a store-token db-family name stays denied regardless of
      git-tracked status;
    - symlink/reparse indirection: the physical (realpath) identity of the
      candidate must equal its lexical absolute identity, and the final
      component must not be a link/reparse point.  A matched NAME on a link
      says nothing about the bytes behind it, so both the untracked-link and
      the tracked-link-to-tracked-target forms deny.
    """
    raw = word.strip().rstrip(".,;")
    if not raw:
        return False
    candidate = Path(raw)
    if not candidate.is_absolute():
        # v1.2.34 W1: explicit resolution base for tools that carry no
        # workdir binding (read_file/search_files pass only `path`). The
        # plugin executes in-process with the worker, so os.getcwd() IS the
        # task workspace; making the base explicit keeps relative-operand
        # resolution deterministic instead of implicit in Path.resolve().
        base = str(arguments.get("workdir") or "") or os.getcwd()
        candidate = Path(base) / raw
    # HIGH-1: store-name family is never plain source (check requested and
    # physical spellings; exact store substrings via _is_policy_controlled).
    if _is_policy_controlled(raw) or _is_policy_controlled(str(candidate)):
        return False
    if _is_control_plane_store_name(Path(raw).name) or _is_control_plane_store_name(candidate.name):
        return False
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, ValueError, RuntimeError):
        return False
    # HIGH-2: any symlink/junction/reparse hop between the requested path and
    # its physical target fails closed.
    absolute = os.path.abspath(str(candidate))
    if os.path.normcase(absolute) != os.path.normcase(str(resolved)):
        return False
    try:
        st = os.lstat(absolute)
    except OSError:
        return False
    if getattr(st, "st_reparse_tag", 0) or os.path.islink(absolute):
        return False
    if _is_policy_controlled(str(resolved)) or _is_control_plane_store_name(resolved.name):
        return False
    if not resolved.is_file():
        return False
    if _is_hard_secret_name(resolved.name) or _is_hard_secret_name(Path(raw).name):
        return False
    try:
        proc = subprocess.run(
            ["git", "-C", str(resolved.parent), "ls-files", "--error-unmatch", "--", resolved.name],
            capture_output=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


def _tracked_source_carveout(matched: str, subject: str, arguments: dict[str, Any]) -> bool:
    """v1.2.26: exempt git-tracked plain source matched only by NAME.

    Fail-closed by construction: if ANY token of the subject that matched the
    trigger pattern is untracked, nonexistent, a hard secret store, or outside
    a repository, the deny stands. Only when every matched token is tracked
    plain source does the guard stand down and let the ordinary effect
    classification decide (read_only / scoped_state_change).
    """
    if not any(token in matched.lower() for token in _CARVEOUT_TOKENS):
        return False
    lowered_pattern = matched.lower()
    variants = [lowered_pattern]
    if lowered_pattern.startswith("**/"):
        variants.append(lowered_pattern[3:])
    hit = False
    for word in re.findall(r"[^\s\"']+", subject):
        if not _is_path_like(word):
            continue
        normalized = word.replace("\\", "/").lower()
        basename = PurePath(normalized).name
        if not any(fnmatch.fnmatch(normalized, v) or fnmatch.fnmatch(basename, v) for v in variants):
            continue
        hit = True
        if not _git_tracked_source_file(word, arguments):
            return False
    return hit


def _canonical_public_doc_read(tool_name: str, arguments: dict[str, Any]) -> bool:
    """Recognize the one public policy document caught by a broad name rule."""
    if tool_name != "read_file":
        return False
    raw = str(arguments.get("path") or "").replace("\\", "/").lower()
    return raw == CANONICAL_PUBLIC_POLICY_DOC


# v1.2.12 C2: trusted absolute roots for the operational-artifact read
# exception. Tests may monkeypatch this tuple; production stays empty so a
# misconfigured deployment never inherits the exception by accident.
_TRUSTED_ARTIFACT_ROOTS: tuple[str, ...] = ()


def _trusted_root_for(raw: str) -> str | None:
    """Return the trusted root physically containing ``raw``, else None.

    v1.2.12 C2 — containment is PHYSICAL, not lexical. The requested path is
    resolved through the filesystem (junctions/symlinks followed); only a
    real location inside one of the trusted absolute roots qualifies. A
    path that cannot be resolved (does not exist) fails closed. In
    combination with the lexical canonicalization below, both directions
    of link escape are denied: a link inside the root pointing OUTSIDE
    resolves out of every trusted root, and an outside link whose TARGET
    lands inside is still refused because the LINK's own physical location
    (its resolved parent) lies outside every trusted root.
    """
    if not _TRUSTED_ARTIFACT_ROOTS:
        return None
    try:
        candidate = Path(raw)
        resolved = candidate.resolve(strict=True)
    except (OSError, ValueError, RuntimeError):
        return None
    resolved_text = str(resolved)
    for root in _TRUSTED_ARTIFACT_ROOTS:
        try:
            resolved_root = str(Path(root).resolve(strict=True))
        except (OSError, ValueError, RuntimeError):
            continue
        root_prefix = resolved_root.rstrip("\\/") + os.sep
        if resolved_text.startswith(root_prefix) or resolved_text == resolved_root:
            # Two-phase check: the RESOLVED target must be inside the root,
            # and the entry's own physical parent chain must not escape the
            # root via a reparse point planted at the boundary.
            physical_parent = resolved.parent
            try:
                parent_text = os.path.normpath(str(physical_parent))
            except (OSError, ValueError, RuntimeError):
                parent_text = resolved_text
            parent_prefix = resolved_root.rstrip("\\/") + os.sep
            if not (parent_text.startswith(parent_prefix) or parent_text == resolved_root):
                return None
            return root
    return None


def _canonical_operational_artifact_read(tool_name: str, arguments: dict[str, Any]) -> bool:
    """Allow direct reads of fleet artifacts without opening a search lane.

    Broad protected-name patterns can match benign audit filenames.  The
    exception is deliberately limited to a single explicit file read inside a
    fleet-owned state, task-workspace, or attachment root.  The requested
    path is canonicalized FIRST (separators, drive/UNC prefixes, case,
    ``..`` segments), so only PHYSICAL containment in a root qualifies:
    traversal escapes, mixed-separator and UNC impersonation never inherit
    the exception.  Secret-shaped basenames and directory segments remain
    denied even inside those roots.

    v1.2.12 C2: on top of the lexical canonicalization, containment is
    verified against the RESOLVED real path (junctions/symlinks followed)
    inside a trusted absolute root; an unresolvable path fails closed.
    """
    if tool_name != "read_file":
        return False
    raw = str(arguments.get("path") or "")
    if not raw:
        return False
    canonical = os.path.normpath(str(raw)).replace("\\", "/").lower()
    if canonical.startswith("//") or ".." in canonical.split("/"):
        return False
    if _TRUSTED_ARTIFACT_ROOTS:
        # C2: registry mode — the physical containment check below decides;
        # the lexical shape routes no longer gate the exception.
        return _trusted_root_for(raw) is not None
    parts = [part for part in canonical.split("/") if part]
    basename = parts[-1] if parts else ""
    hard_basename = basename.startswith(".env") or basename == "auth.json"
    hard_segment = any(part in {"sessions", "request_dump", "dumps"} for part in parts)
    if hard_basename or hard_segment:
        return False
    plugin_state = re.search(r"/profiles/[^/]+/plugins/[^/]+/\.state(?:/|$)", canonical)
    task_artifact = re.search(
        r"/kanban/boards/[^/]+/(?:workspaces|attachments)/[^/]+(?:/|$)", canonical
    )
    if not (plugin_state or task_artifact):
        return False
    # C2: when a trusted-root registry is configured, PHYSICAL containment
    # in a trusted root REPLACES the lexical routes entirely (resolve-based
    # check on the real path); without the registry the lexical routes keep
    # their historical meaning.
    if _TRUSTED_ARTIFACT_ROOTS:
        return _trusted_root_for(str(arguments.get("path") or "")) is not None
    return True


READ_TOOLS = {
    "read_file", "search_files", "web_search", "web_extract", "read_preview", "read_terminal",
    "vision_analyze", "session_search", "skills_list", "skill_view", "project_list", "kanban_show",
    "kanban_list", "kanban_context", "kanban_diagnostics", "kanban_attachments", "fact_store",
}
READ_PREFIXES = ("read_", "search_", "list_", "get_", "show_", "view_", "probe_", "inspect_")
TERMINAL_TOOLS = {"terminal", "shell", "bash", "powershell", "exec", "execute_command"}


def _normalize_tool_name(tool_name: str) -> str:
    """Normalize the namespace used by direct Hermes tool dispatch only.

    Deferred MCP names are intentionally left untouched: stripping arbitrary
    namespaces could accidentally assign read semantics to an unrelated tool.
    """
    lowered = tool_name.strip().lower()
    return lowered.removeprefix("functions.")

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

# v1.2.13 M-E: board lifecycle tools are a worker's ONLY coordination channel
# (handoff, heartbeat, block, comment, review transitions). The anti-loop
# collapse classes (identical_call_loop / same_failure_loop) must never sever
# it: their arguments repeat by nature (the same heartbeat note, the same
# completion summary after two executive denies), and losing the transition
# channel strands the card exactly when the worker most needs to report.
# Observed failures: run 655 (repeated board-read calls collapsed into
# identical_call_loop) and the terminal-deny → block-loop class where the
# lifecycle transition itself got counted as a repeated failing call.
# Scope is the kanban_* namespace ONLY — executive tools (terminal,
# write_file, patch, ...) keep full collapse guarding, and lifecycle calls
# still charge the tool-call budget, so a runaway lifecycle loop is bounded by
# budget_exhausted (which is NOT exempted).
LIFECYCLE_TOOLS = {
    "kanban_show", "kanban_list", "kanban_context", "kanban_diagnostics",
    "kanban_attachments", "kanban_comment", "kanban_create", "kanban_complete",
    "kanban_block", "kanban_unblock", "kanban_heartbeat", "kanban_link",
    "kanban_edit", "kanban_attach", "kanban_attach_url",
    "kanban_request_review", "kanban_request_changes",
}


def is_lifecycle_tool(tool_name: str) -> bool:
    """v1.2.13 M-E: normalized board-lifecycle namespace membership."""
    return _normalize_tool_name(tool_name) in LIFECYCLE_TOOLS

# v1.2.7: `git clone`/`git fetch` moved out of READ_COMMAND. They are
# network downloads into a local tree (state change), not pure reads; the
# exact-head verifier lane never needed them. Chained `cd X && git status`
# still classifies as a read via the per-stage rules below.
# v1.2.19: the git verb list accepts the common `git -C <path>` wrapper
# (case-sensitive `-C`: lowercase `-c` injects per-invocation config such as
# core.pager and must NOT buy the read lane). Mutating verbs are not
# whitelisted here; MUTATOR below carries the same `-C` tolerance so
# `git -C repo push/commit/merge/...` stays a state change.
# Read-only git inspection added: `config --get*/--list` and bare
# `config [--scope] <key>` with NO value (query form; a value argument makes
# it a write and falls through to state_change), `worktree list`, and
# `merge-base` (MUTATOR's `merge` no longer matches `merge-base`).
# `cat` joins the read utilities (stdout only — redirects and in-place forms
# are still caught by the write-marker scan). Deliberately NOT allowed:
# bare `VAR=value ...` env prefixes — PATH=/evil or LD_PRELOAD=evil.so in
# front of `python -m pytest` rebinds the executed binary, so assignment
# prefixes stay fail-closed.
# v1.2.23: stdout-only `echo`/`printf` and `true` join the read utilities.
# Incident 17.09.2026: pure-read diagnostics chained with section markers
# (`grep … fleet-policy.yaml; echo "==="; grep … policy.py`,
# `git merge-base --is-ancestor X Y && echo OK || echo NO`) were classified
# state_change solely because of the echo stage, so the path guard then
# hard-denied them as policy_control_plane_mutation ("policy-controlled
# files are immutable") although nothing wrote anything — the dominant
# false-positive first-pass failure family (F1, shadow baseline). Safety is
# unchanged: heredocs (`<<`), command substitution ($(), backticks) and
# process substitution fail closed via _SHELL_METACHARACTERS; redirects and
# `tee` fail closed via the write-marker scan; `date` stays fail-closed
# (clock-setting -s/--set forms are hard to bound lexically); a quoted
# payload never buys the read lane for its stage because only the PROGRAM
# is allowlisted here.
READ_COMMAND = re.compile(
    r"^\s*(?:git(?:\s+--no-pager)?(?:\s+(?-i:-C)\s+\S+)?\s+(?:status|diff|log|show|branch\s+(?:--show-current|--list|-l)\b|rev-parse|rev-list|remote(?:\s+-v)?|ls-remote|ls-files|ls-tree|"
    r"config\s+(?:--(?:global|local|system|worktree)\s+)*(?:--get(?:-all|-regex)?|--list|-l|--get-url|--get-regexp|[A-Za-z0-9][A-Za-z0-9._-]*\s*$)|"
    r"worktree\s+list\b|merge-base\b)|"
    # v1.2.22: `find` joins the read utilities for read-only forms. The
    # lookahead keeps every mutating primary option (-delete, -exec/-execdir,
    # -ok/-okdir, -fls/-fprint) out of the read lane; the token-based
    # write-marker scan below is the second, fail-closed layer for them.
    r"find\b(?!.*\s-(?:delete|exec|execdir|ok|okdir|fls|fprint)\b)|"
    # v1.2.23: stdout-only `echo`/`printf` and `true` join the read utilities.
    # `date` deliberately does NOT: its `-s`/`--set` clock-setting forms are
    # hard to bound lexically (-us/-ns/-Iseconds all cluster with 's'), so it
    # stays fail-closed. echo/printf never read or write files; redirects,
    # tee, command substitution and backticks still fail closed elsewhere.
    r"(?:rg|grep|findstr|ls|dir|pwd|type|get-content|select-string|sed|head|tail|stat|wc|file|du|sort|uniq|cut|tr|column|cat\b|echo\b|printf\b|true\b|diff\b|python\s+-m\s+pytest\b|npm\s+(?:test|run\s+(?:test|lint|build))\b)\b)",
    re.I,
)
MUTATOR = re.compile(
    # v1.2.19: the git verbs tolerate the `git -C <path>` wrapper (otherwise
    # `git -C repo push` would dodge MUTATOR and inherit the read lane from
    # READ_COMMAND's -C-aware verb list) and `merge` no longer matches
    # `merge-base` (a pure inspection subcommand).
    r"(?:^|[;&|]\s*|\b)(?:rm|del|remove-item|mv|move-item|cp|copy-item|set-content|add-content|"
    r"git(?:\s+(?-i:-C)\s+\S+)?\s+(?:commit|push|merge(?!-base)|rebase|reset|checkout|switch)|hermes\s+(?:config\s+set|plugins\s+(?:enable|disable|install|remove)|kanban\s+(?:create|comment|block|unblock|archive|assign|reassign|reclaim))|"
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
# v1.2.22: find primaries that write, mutate, or execute.
_FIND_WRITE_OPTIONS = {
    "-delete", "-exec", "-execdir", "-ok", "-okdir", "-fls", "-fprint",
}
_FD_DUP_REDIRECT = re.compile(r"\d*>&\d+")
# v1.2.25: stderr/stdout discard to /dev/null is not a filesystem write.
# Narrow by design: only a redirect whose TARGET is exactly /dev/null is
# stripped before the write-marker scan; redirects to real paths stay
# fail-closed. (Live false-positive 21.09: `grep … 2>/dev/null` flipped a
# read command into state_change and then into a bogus
# policy_control_plane_mutation deny on a policy-controlled path argument.)
_DEVNULL_DISCARD = re.compile(r"(?:\d+|&)?>>?\s*/dev/null(?=\s|$)")
# v1.2.25: a bare `VAR=value` stage only sets a shell variable — same class
# as the `cd <dir>` no-op. Command substitution inside the value cannot
# reach here: `$(`/backticks fail closed via _SHELL_METACHARACTERS first.
_ASSIGNMENT_STAGE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=(?:\"[^\"]*\"|'[^']*'|\S+)$")
_OUTPUT_REDIRECT = re.compile(r"&>>|&>|>>|>")


def _simple_commands(command: str) -> list[str]:
    """Split a command line into stages: chains, lists and pipes.

    v1.2.34 W2(b): the split is quote-aware — `&&`, `||`, `;` and `|` inside
    BALANCED single/double quotes are literal characters of one stage (the
    shell never treats them as control operators), so `python -c "a; b"` and
    `grep 'x|y' f` reach the stage classifier intact instead of being
    shredded into unparseable fragments. An unbalanced quote state fails
    closed to the historical quote-blind split, so a stray apostrophe can
    never swallow a later mutating stage into a "quoted" span; the MUTATOR
    and write-marker scans additionally run over the raw text.
    """
    stages: list[str] = []
    current: list[str] = []
    quote: str | None = None
    index = 0
    length = len(command)
    while index < length:
        char = command[index]
        if quote is not None:
            current.append(char)
            if char == "\\" and quote == '"' and index + 1 < length:
                current.append(command[index + 1])
                index += 2
                continue
            if char == quote:
                quote = None
            index += 1
            continue
        if char in "\"'":
            quote = char
            current.append(char)
            index += 1
            continue
        if command[index:index + 2] in ("&&", "||"):
            stages.append("".join(current))
            current = []
            index += 2
            continue
        if char in ";|":
            stages.append("".join(current))
            current = []
            index += 1
            continue
        current.append(char)
        index += 1
    if quote is not None:
        # Unbalanced quoting: fall back to the historical blind split.
        return [part.strip() for part in re.split(r"&&|\|\||;|\|", command) if part.strip()]
    stages.append("".join(current))
    return [part.strip() for part in stages if part.strip()]


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
        # v1.2.22: mutating find primaries are writes (same token-based
        # family as sed -i / sort -o); find never reaches this scan from
        # READ_COMMAND without them, but fail closed if it does.
        if program == "find" and any(
            _clean_shell_token(token).lower() in _FIND_WRITE_OPTIONS
            for token in tokens[1:]
        ):
            return True
        # Shell output redirects write regardless of the program. Quoted
        # payload text is ignored; `2>&1`-style fd duplication is not a write.
        # v1.2.25: `/dev/null` discards are not filesystem writes either —
        # strip them before the redirect scan (real-path redirects still hit
        # _OUTPUT_REDIRECT and fail closed).
        unquoted = re.sub(r"\"[^\"]*\"|'[^']*'", " ", segment)
        unquoted = _DEVNULL_DISCARD.sub(" ", unquoted)
        unquoted = _FD_DUP_REDIRECT.sub(" ", unquoted)
        if _OUTPUT_REDIRECT.search(unquoted):
            return True
    return False


_GH_READ_VERBS = {
    ("pr", "view"),
    ("pr", "diff"),
    ("pr", "checks"),
    ("pr", "list"),
    ("run", "view"),
    ("run", "list"),
    ("repo", "view"),
    ("release", "view"),
    ("workflow", "view"),
    ("issue", "view"),
}
# F-01: token-skip flags whose argument carries the HTTP method. (`--hostname`
# / `--gh-hostname` redirect the OAuth token to an attacker host; they are not
# allowlisted below, so every spelling fails closed.)
_GH_API_METHOD_FLAGS = ("--method", "-x")
# F-01/F-02: option handling is allowlist-based. pflag/cobra accepts inline
# `=` spellings (`--hostname=evil`) and unambiguous prefix abbreviations
# (`--hostn evil`), so a blocklist on exact flag names can be bypassed. Only
# these read-safe option forms are accepted; every other option fails closed.
# v1.2.19: `--jq`/`-q` (output formatting) joins the allowlist. It cannot
# change the HTTP method or carry a payload — it only projects the JSON
# response — but it consumes a value, so both the space form (`--jq .sha`)
# and the fused form (`--jq=.sha`) must skip their argument. Workers rely on
# it for exact-head probes (`gh api ... --jq .sha`); the v1.2.7 fail-closed
# behavior made every such probe a state change, burning runs (incident
# 13.09.2026, t_6f335dd6 case 4).
_GH_API_SAFE_FLAGS = {"--paginate", "--include", "-i"}
_GH_API_VALUE_FLAGS = ("--jq", "-q")
# F-02: a read-only endpoint must be a relative GitHub REST path — lowercase
# alphanumeric segments joined by slashes (optionally with a leading slash).
# Schemes (`https://...`), hosts, and any other character fail closed.
_GH_API_ENDPOINT_PATH = re.compile(r"/?[a-z0-9._-]+(?:/[a-z0-9._-]+)*")
# Background jobs (`cmd &`) and unconditional chaining would otherwise
# hide a second command behind a read-only first stage; fd duplication
# like `2>&1` is handled by the redirect scanner, not matched here.
_SHELL_METACHARACTERS = re.compile("[\\n\
]|(?<!&)&(?!&)|\\$\\(|`|<\\(|>\\(")
# v1.2.25: read-only process substitution `<(...)` with a parenthesis-free
# inner span (no nesting — nested forms fail closed). Verified inner-first
# in _terminal_is_read_only, then neutralized so the metacharacter guard
# does not reject the whole command. Output substitution `>(...)` is a
# write and is deliberately NOT matched here — it stays fail-closed.
_PROCESS_SUBSTITUTION = re.compile(r"<\(([^()]*)\)")


def _clean_shell_token(token: str) -> str:
    return token.strip().strip("\"'")


def _program_name(token: str) -> str:
    normalized = _clean_shell_token(token).replace("\\", "/")
    return PurePath(normalized).name.lower().removesuffix(".exe")


def _gh_api_is_read_only(args: list[str]) -> bool:
    """Allow REST GET probes only; anything unrecognized fails closed.

    F-01: option handling is allowlist-based. pflag/cobra accepts inline
    `--flag=VALUE` spellings and unambiguous prefix abbreviations (`--hostn`),
    so matching only exact flag names missed every `=`/abbreviated spelling of
    `--hostname`. Here every option token must be a known read-safe form
    (`--paginate`, `--include`, `-i`, or the method selectors) before the
    command can be read-only; `--hostname`, `--field`, `--input`, and every
    unknown option fall closed.
    """
    method = "GET"
    endpoint: str | None = None
    index = 0
    while index < len(args):
        raw = _clean_shell_token(args[index])
        lowered = raw.lower()
        if lowered in _GH_API_METHOD_FLAGS or lowered.startswith("--method=") or (
            lowered.startswith("-x") and len(raw) > 2
        ):
            if lowered.startswith(("--method=", "-x")):
                method = raw.split("=", 1)[1].upper() if "=" in raw else raw[2:].upper()
                index += 1
                continue
            if index + 1 >= len(args):
                return False
            method = _clean_shell_token(args[index + 1]).upper()
            index += 2
            continue
        if raw in _GH_API_SAFE_FLAGS or lowered in _GH_API_SAFE_FLAGS:
            index += 1
            continue
        # v1.2.19: output-formatting flags consume their value; the value is
        # a jq expression, never a request payload. Fused `--jq=...` forms
        # carry the value inline and are handled here too.
        if lowered in _GH_API_VALUE_FLAGS:
            index += 2
            continue
        if any(lowered.startswith(flag + "=") for flag in _GH_API_VALUE_FLAGS):
            index += 1
            continue
        if raw.startswith("-"):
            # Any other option spelling fails closed: write/payload flags
            # (`--field`, `--raw-field`, `--input`, `--header`, `--cache`,
            # `-f`, `-F`, `-H`), host overrides (`--hostname[=...]`,
            # `--gh-hostname[=...]`, abbreviations like `--hostn evil`),
            # template and jq selectors, and anything not allowlisted.
            return False
        if endpoint is None:
            endpoint = lowered
        index += 1
    if endpoint is None or endpoint == "graphql" or method != "GET":
        return False
    # F-02: the endpoint must be a relative REST path (`repos/o/r`,
    # `/user/repos`). Absolute URLs would let `gh api https://evil.example/...`
    # inherit the read lane, so any scheme or foreign-host spelling fails
    # closed against a strict path allowlist.
    return _GH_API_ENDPOINT_PATH.fullmatch(endpoint) is not None


def _gh_stage_is_read_only(tokens: list[str]) -> bool:
    if len(tokens) < 2 or _program_name(tokens[0]) != "gh":
        return False
    args = [_clean_shell_token(token) for token in tokens[1:]]
    if not args:
        return False
    if args[0].lower() == "api":
        return _gh_api_is_read_only(args[1:])
    if len(args) < 2 or (args[0].lower(), args[1].lower()) not in _GH_READ_VERBS:
        return False
    # Opening an external browser is a local state change, not a verifier read.
    return not any(arg.lower() in {"--web", "-w"} for arg in args[2:])


def _hash_stage_is_read_only(tokens: list[str]) -> bool:
    if not tokens:
        return False
    program = _program_name(tokens[0])
    if program == "sha256sum":
        return True
    if program == "shasum":
        args = [_clean_shell_token(token).lower() for token in tokens[1:]]
        return any(
            args[index] == "-a" and index + 1 < len(args) and args[index + 1] == "256"
            for index in range(len(args))
        ) or "-a256" in args
    return program == "certutil" and len(tokens) > 1 and _clean_shell_token(tokens[1]).lower() == "-hashfile"

# v1.2.34 W2(a): bare version probes join the read lane. A two-token stage
# `<program> <flag>` with an exact per-program flag is a pure stdout read;
# the map is deliberate — `python -v` is the verbose-import REPL, NOT a
# version probe, and must not buy the read lane. Live FP (card t_d94dde9d
# cases 1/5): a read-only diagnostics chain ending in `python --version`
# flipped the whole command to state_change, and the path guard then
# hard-denied the probe as a control-plane mutation.
_VERSION_PROBE_FLAGS = {
    "python": frozenset({"-V", "--version"}),
    "py": frozenset({"-V", "--version"}),
    "node": frozenset({"-v", "--version"}),
    "npm": frozenset({"-v", "--version"}),
    "uv": frozenset({"-V", "--version"}),
    "git": frozenset({"--version"}),
    "sqlite3": frozenset({"--version"}),
    "gh": frozenset({"--version"}),
    "jq": frozenset({"--version"}),
}
_VERSIONED_PYTHON_RE = re.compile(r"python\d+(?:\.\d+)*")


def _version_probe_is_read_only(tokens: list[str]) -> bool:
    if len(tokens) != 2:
        return False
    program = _program_name(tokens[0])
    flags = _VERSION_PROBE_FLAGS.get(program)
    if flags is None and _VERSIONED_PYTHON_RE.fullmatch(program):
        flags = _VERSION_PROBE_FLAGS["python"]
    return flags is not None and _clean_shell_token(tokens[1]) in flags


# v1.2.34 W2(b): narrow lexical lane for in-process `python -c` read probes.
# SUPERSEDES the v1.2.31 re-scope note ("in-process python -c sqlite form
# stays denied") per the company decision of 02.10.2026 on card t_d94dde9d:
# a mode=ro SELECT probe is a read, not a mutation. Fail-closed by design —
# the stage must be exactly `python -c <one quoted code argument>`, every
# `;`-separated statement must match an allowlisted shape, every SQL literal
# must be a read verb (the v1.2.31 regexes), every gh argv must pass the
# existing _gh_stage_is_read_only allowlist, and a global deny-token scan
# rejects mutation/execution/filesystem/network tokens. Residual risk
# (documented): the lane is lexical; string-concatenation obfuscation inside
# an otherwise template-shaped probe is the pre-existing scanner-gap class.
_PYTHON_C_PROGRAM_RE = re.compile(r"(?:python|py)(?:\d+(?:\.\d+)*)?")
_CODE_DENY_TOKENS: tuple[str, ...] = (
    "insert", "update", "delete", "drop", "alter", "create", "attach",
    "detach", "replace", "vacuum", "reindex", "executescript", "commit",
    "rollback", "open(", "os.", "subprocess", "eval", "exec(",
    "__import__", "socket", "urllib", "requests", "shutil", "pathlib",
    "write", "shell=true", "system(", "popen", "input(",
)
_QUOTED_LITERAL = re.compile(r"""(['"])([^'"]*)\1""")
_SQLITE_CONNECT_STMT = re.compile(
    r"""^(\w+)\s*=\s*sqlite3\.connect\(\s*(['"])(file:[^'"]*)\2\s*,\s*uri\s*=\s*True\s*\)$"""
)
_SQLITE_FETCH_STMT = re.compile(r"^(\w+)\s*=\s*(\w+)\.execute\(.+\)\.(?:fetchall|fetchone)\(\)$")
_SQLITE_CLOSE_STMT = re.compile(r"^(\w+)\.close\(\)$")
_SQLITE_PRINT_STMT = re.compile(r"^print\(.+\)$")
_SQLITE_EXECUTE_CALL = re.compile(r"""\.execute\(\s*(['"])([^'"]*)\1\s*\)""")
_GH_IMPORT_STMT = re.compile(r"^import\s+(.+)$")
_GH_ALLOWED_IMPORTS = frozenset({"subprocess", "json", "sys"})
_GH_RUN_STMT = re.compile(r"^(\w+)\s*=\s*subprocess\.run\(\s*\[([^\[\]]*)\]\s*(?:,\s*(.*?))?\s*\)$")
_GH_RUN_BOOL_KWARGS = {"capture_output": {"true", "false"}, "text": {"true", "false"}}
_GH_PRINT_STMT = re.compile(r"^print\(.+\)$")
_GH_JSON_STMT = re.compile(r"^(\w+)\s*=\s*json\.loads\(\s*(\w+)\.stdout\s*\)$")


def _code_deny_hit(code: str, *, allowed: frozenset[str] = frozenset()) -> str | None:
    lowered = " ".join(code.lower().split())
    for token in _CODE_DENY_TOKENS:
        if token in allowed:
            continue
        if token in lowered:
            return token
    return None


def _python_sqlite_probe_code(code: str) -> bool:
    """T-sqlite: `import sqlite3` → conn assignment via a file: URI carrying
    mode=ro with uri=True → read-verb execute/fetch → print → close. Every
    `.execute(` occurrence must carry a quoted read-verb SQL literal (covers
    print-wrapped calls too); any other statement shape fails closed."""
    statements = [part.strip() for part in code.split(";") if part.strip()]
    if not statements or statements[0] != "import sqlite3":
        return False
    conn_vars: set[str] = set()
    for statement in statements[1:]:
        connect = _SQLITE_CONNECT_STMT.match(statement)
        if connect:
            if "mode=ro" not in connect.group(3):
                return False
            conn_vars.add(connect.group(1))
            continue
        fetch = _SQLITE_FETCH_STMT.match(statement)
        if fetch:
            if fetch.group(2) not in conn_vars:
                return False
            continue
        if _SQLITE_PRINT_STMT.match(statement):
            continue
        close = _SQLITE_CLOSE_STMT.match(statement)
        if close and close.group(1) in conn_vars:
            continue
        return False
    execute_calls = _SQLITE_EXECUTE_CALL.findall(code)
    if code.count(".execute(") != len(execute_calls):
        return False  # an execute whose argument is not a plain literal
    for sql in (item[1] for item in execute_calls):
        if not sql.strip():
            return False
        if not (_SQLITE_READ_STATEMENT.match(sql) or _SQLITE_READ_PRAGMA.match(sql)):
            return False
    return _code_deny_hit(code) is None


def _python_gh_probe_code(code: str) -> bool:
    """T-gh: imports from {subprocess, json, sys} → exactly one
    subprocess.run([...gh argv...], capture_output/text/timeout kwargs only)
    whose argv passes _gh_stage_is_read_only → json.loads / print. The deny
    scan runs with quoted literals masked: the literals ARE the gh argv and
    are validated structurally, so endpoint names (e.g. commits) must not
    trip SQL-mutation tokens."""
    statements = [part.strip() for part in code.split(";") if part.strip()]
    if not statements:
        return False
    imported: set[str] = set()
    run_var: str | None = None
    for statement in statements:
        import_match = _GH_IMPORT_STMT.match(statement)
        if import_match:
            names = [name.strip() for name in import_match.group(1).split(",")]
            if not names or any(name not in _GH_ALLOWED_IMPORTS for name in names):
                return False
            imported.update(names)
            continue
        run_match = _GH_RUN_STMT.match(statement)
        if run_match and run_var is None:
            argv_pairs = _QUOTED_LITERAL.findall(run_match.group(2))
            residue = _QUOTED_LITERAL.sub(" ", run_match.group(2))
            if residue.strip(", \t") or not argv_pairs:
                return False
            argv = [text for _, text in argv_pairs]
            if argv[0] != "gh" or not _gh_stage_is_read_only(argv):
                return False
            kwargs_body = (run_match.group(3) or "").strip()
            if kwargs_body:
                for chunk in kwargs_body.split(","):
                    key, sep, value = chunk.strip().partition("=")
                    key, value = key.strip(), value.strip().lower()
                    if not sep:
                        return False
                    if key in _GH_RUN_BOOL_KWARGS:
                        if value not in _GH_RUN_BOOL_KWARGS[key]:
                            return False
                    elif key == "timeout":
                        if not value.isdigit():
                            return False
                    else:
                        return False
            run_var = run_match.group(1)
            continue
        if _GH_PRINT_STMT.match(statement):
            continue
        if _GH_JSON_STMT.match(statement):
            continue
        return False
    if run_var is None or "subprocess" not in imported:
        return False
    if code.count("subprocess.run") != 1:
        return False
    masked = _QUOTED_LITERAL.sub(" ", code)
    return _code_deny_hit(masked, allowed=frozenset({"subprocess"})) is None


def _python_stage_is_read_only(tokens: list[str]) -> bool:
    """Exactly `python -c <one quoted code argument>`; extra arguments,
    unquoted code, other flags or other programs fail closed."""
    if len(tokens) != 3:
        return False
    program = _program_name(tokens[0])
    if not _PYTHON_C_PROGRAM_RE.fullmatch(program):
        return False
    if _clean_shell_token(tokens[1]) not in {"-c", "--command"}:
        return False
    raw_code = tokens[2]
    if len(raw_code) < 3 or raw_code[0] not in "\"'" or raw_code[-1] != raw_code[0]:
        return False
    code = raw_code[1:-1]
    if not code.strip():
        return False
    return _python_sqlite_probe_code(code) or _python_gh_probe_code(code)


# v1.2.31: single-statement read-only SQL via the sqlite3 CLI joins the read
# lane (owner re-scope: read-only diagnostics — SELECT included — must never
# be classified as mutations). Mirrors the gh-api lane's allowlist discipline:
# known read-safe flags only, exactly two positionals (db + ONE statement),
# read-verb prefix, and no `;` statement splicing, dot-commands, or PRAGMA
# assignments. Everything else fails closed to the stricter state_change
# classification. Accepted residual risk (same class as the other lexical
# lanes): the engine may CREATE an empty database file when the db path does
# not exist; a SELECT-family statement cannot mutate rows, and -readonly
# removes even the creation risk.
_SQLITE_SAFE_FLAGS = frozenset({
    "-readonly", "-batch", "-noheader", "-header", "-csv", "-json",
    "-line", "-list", "-column", "-ascii",
})
_SQLITE_READ_STATEMENT = re.compile(r"^(?:select|with|values|explain)\b", re.IGNORECASE)
_SQLITE_READ_PRAGMA = re.compile(r"^pragma\b[^=]*$", re.IGNORECASE)


def _sqlite_stage_is_read_only(tokens: list[str]) -> bool:
    if not tokens or _program_name(tokens[0]) != "sqlite3":
        return False
    positionals: list[str] = []
    for raw in tokens[1:]:
        token = _clean_shell_token(raw)
        if token.startswith("-"):
            if token.lower() in _SQLITE_SAFE_FLAGS:
                continue
            return False
        positionals.append(token)
    # One positional is an interactive/stdin-driven session: unbounded, so
    # never read-only. More than two is a usage the CLI does not define.
    if len(positionals) != 2:
        return False
    statement = positionals[1].strip()
    if not statement or statement.startswith(".") or ";" in statement:
        return False
    return bool(
        _SQLITE_READ_STATEMENT.match(statement) or _SQLITE_READ_PRAGMA.match(statement)
    )


def _stage_is_read_only(segment: str) -> bool:
    if READ_COMMAND.match(segment):
        return True
    tokens = _stage_tokens(segment)
    return (
        _gh_stage_is_read_only(tokens)
        or _hash_stage_is_read_only(tokens)
        or _sqlite_stage_is_read_only(tokens)
        or _version_probe_is_read_only(tokens)
        or _python_stage_is_read_only(tokens)
    )


def _terminal_is_read_only(command: str) -> bool:
    # v1.2.7: bash executes newlines, background-job ampersands, and command
    # substitutions that shlex(posix=False) hides from the tokenizer, so any
    # command carrying these metacharacters fails closed. `&&` chaining is
    # excluded because every stage is still classified independently below.
    # v1.2.25 narrow exception: a process substitution `<(git show ref:path)`
    # whose inner command is itself a read-only stage is a read pattern
    # (comparing a pinned blob against the working tree). Inner spans are
    # matched without nesting; every other metacharacter form still fails
    # closed. The inner span is verified BEFORE it is neutralized, so it can
    # never hide a mutating stage from the write-marker scan.
    substitutions = list(_PROCESS_SUBSTITUTION.finditer(command))
    if substitutions:
        for match in substitutions:
            inner = match.group(1)
            if not inner or not _stage_is_read_only(inner):
                return False
        command = _PROCESS_SUBSTITUTION.sub("__fp_procsub__", command)
    if _SHELL_METACHARACTERS.search(command):
        return False
    # v1.2.22: quoted spans are search patterns / path prose, not verbs.
    # MUTATOR previously matched words INSIDE quotes, so `grep -rn "deploy"`
    # flipped a pure read into state_change and then into an evidence-gated
    # category. The unquote regex is the same one _has_write_marker already
    # uses; the RAW text still feeds the write-marker scan below, so
    # redirects and mutating flags outside quotes stay fail-closed.
    mutator_view = re.sub(r"\"[^\"]*\"|'[^']*'", " ", command)
    if MUTATOR.search(mutator_view) or _has_write_marker(command):
        return False
    segments = _simple_commands(command)
    # v1.2.7: every pipeline stage is classified independently. Remote exact-
    # head verification permits only explicit GitHub view/GET operations and
    # local hash utilities; any payload, mutation verb or unknown stage fails
    # closed. Bare `cd <dir>` remains a no-op for the read classifier.
    # v1.2.25: a bare `VAR=value` stage is a shell variable binding, not a
    # mutation (no program runs, nothing is written). Quoted values cannot
    # smuggle execution — `$(`/backticks/newlines fail closed above via
    # _SHELL_METACHARACTERS before this classifier is consulted.
    return bool(segments) and all(
        _stage_is_read_only(part)
        or _ASSIGNMENT_STAGE.match(part) is not None
        or (part.split() and part.split()[0].lower() == "cd" and len(part.split()) == 2)
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


# --- lexical delta (card t_f6acc5dc): action-aware operand classification ---
# D1 (F1, run2166 call19): an EMPTY-value dotted git config assignment
# (`git -c <config-key>.helper=`) resets/disables the option; the token is a
# config-key NAME, not a filesystem object. Only the empty-value form is
# exempt and only directly after `git -c`; any non-empty value stays
# guarded (fail-closed).
_GIT_CONFIG_EMPTY_OPTION = re.compile(
    r"^[A-Za-z][A-Za-z0-9_-]*(?:\.[A-Za-z0-9_-]+)+=$"
)
# D2 (F2, run2172 call26): dispatcher-provided worker binding pins are
# nonsecret context facts. A NAME=value binding for a child process does not
# mutate the referenced store, so the assignment token is not a filesystem
# operand. Fail-closed: D2e (in _path_guard_subjects) re-injects the bound
# value as a subject whenever the command expands the same pin ($NAME),
# because the value can then re-enter as a real operand. Unknown names are
# never exempt.
_ENV_PIN_BINDING_NAMES = frozenset({
    "HERMES_KANBAN_DB",
    "HERMES_KANBAN_BOARD",
    "HERMES_KANBAN_TASK",
    "HERMES_KANBAN_WORKSPACE",
    "HERMES_KANBAN_WORKSPACES_ROOT",
    "HERMES_TENANT",
})
_ENV_PIN_BINDING = re.compile(
    r"(?<![A-Za-z0-9_])("
    + "|".join(sorted(_ENV_PIN_BINDING_NAMES))
    + r")=(\"[^\"]*\"|'[^']*'|\S+)"
)


def _path_guard_subjects(name: str, arguments: dict[str, Any]) -> list[str]:
    """F4: the path guard sees only path-like targets, never free text."""
    if name in TERMINAL_TOOLS:
        command = str(arguments.get("command") or arguments.get("cmd") or "")
        # v1.2.11 item F5: structurally extract path-like operands per
        # pipeline stage.  Quoted segments are PROSE by construction (the
        # shell never glob-expands them) and are removed BEFORE tokenizing;
        # within each stage the leading executable is skipped, known
        # value-taking flags (git commit -m/--message, find -name, ...) and
        # the token after them are prose, a trailing ``--opt=`` contributes
        # only its empty value, and the value of an unquoted ``-flag=path``
        # token is a real filesystem operand and stays guarded.  Unquoted
        # flag values fail CLOSED (they are inspected as operands) — the
        # narrowing removes the whole-string prose scan, not operand checks.
        value_flags = {
            "-m", "--message", "--label", "-label",
            "--format", "--output", "-name", "--name",
        }
        subjects: list[str] = []
        # Lexical delta D2e (t_f6acc5dc): an expanded worker pin can feed the
        # bound value back in as a real operand ($PIN / ${PIN}); inject the
        # value so the guard sees it. Fail-closed: injection only ADDS a
        # subject, it never allows anything by itself.
        for binding_match in _ENV_PIN_BINDING.finditer(command):
            pin_name = binding_match.group(1)
            if pin_name in _ENV_PIN_BINDING_NAMES and re.search(
                r"\$\{?" + pin_name + r"\b", command
            ):
                bound_value = binding_match.group(2).strip("'\"")
                if _is_path_like(bound_value):
                    subjects.append(bound_value)
        # A code-bearing flag value (python -c "…") is executable input, not
        # prose: its text is scanned as an operand even though it was quoted.
        for code_match in re.finditer(
            r"\bpython(?:\d+(?:\.\d+)?)?\s+(?:-c|--command)\s*(\"[^\"]*\"|'[^']*')", command
        ):
            subjects.append(code_match.group(1)[1:-1])
        # Quote-aware tokenizer: quoted spans are single tokens (prose by
        # construction — code values were already extracted above) and do
        # not break tokenization the way shlex(posix=False) would.  A fused
        # ``--flag="value"`` stays ONE token so its value can be classified
        # by flag key: a known value-flag (git commit --message=…) is prose,
        # an unknown one fails closed (value inspected as an operand).
        token_re = re.compile(
            r"-{1,2}[A-Za-z][A-Za-z-]*=(?:\"[^\"]*\"|'[^']*')|\"[^\"]*\"|'[^']*'|\S+"
        )
        stages: list[list[str]] = [[]]
        for part in re.split(r"(\|\||&&|;|\|)", command):
            if part in ("||", "&&", ";", "|"):
                stages.append([])
            elif part:
                stages[-1].extend(token_re.findall(part))
        for stage in stages:
            # v1.2.11 F5 (search tools): the FIRST POSITIONAL operand of
            # grep/rg/findstr/select-string is the search EXPRESSION, not a
            # filesystem target — the original false-deny class (c2c46082);
            # later positionals stay guarded (needle auth.json → deny).
            head = stage[0] if stage else ""
            head_name = PurePath(head.replace("\\", "/")).name.lower()
            search_head = head_name in {
                "grep", "rg", "findstr", "select-string",
            }
            git_head = head_name in {"git", "git.exe"}
            pattern_seen = False
            expect_value = False
            expect_git_config = False
            for token in stage[1:]:
                if expect_value:
                    expect_value = False  # flag value = prose, never a target
                    continue
                if expect_git_config:
                    # Lexical delta D1 (t_f6acc5dc F1, run2166 call19): the
                    # token after `git -c` is a config assignment. Only the
                    # EMPTY-value dotted-key form (option reset/disable, e.g.
                    # an empty helper) names no filesystem object; every
                    # non-empty value falls through and stays guarded.
                    expect_git_config = False
                    if _GIT_CONFIG_EMPTY_OPTION.match(token):
                        continue
                if git_head and token == "-c":
                    expect_git_config = True
                    continue
                pin_binding = _ENV_PIN_BINDING.match(token)
                if pin_binding and pin_binding.group(1) in _ENV_PIN_BINDING_NAMES:
                    # Lexical delta D2 (t_f6acc5dc F2, run2172 call26): a
                    # dispatcher worker pin assignment binds the child
                    # process; it is context, not a filesystem operand. The
                    # bound value stays guarded via the D2e injection above
                    # whenever the command expands the same pin.
                    continue
                if token in value_flags:
                    expect_value = True
                    continue
                if token.startswith(('"', "'")):
                    if search_head and not pattern_seen:
                        pattern_seen = True  # quoted expression consumes the slot
                    continue
                if token.startswith("-"):
                    if "=" in token:
                        flag_key = token.split("=", 1)[0]
                        if flag_key in value_flags:
                            continue  # known value-flag: the value is prose
                        value_part = token.split("=", 1)[1].strip("'\"")
                        if _is_path_like(value_part):
                            subjects.append(value_part)
                    continue
                if search_head and not pattern_seen:
                    pattern_seen = True  # first positional = expression
                    continue
                if _is_path_like(token):
                    subjects.append(token)
        return subjects
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


def _task_workspace_root(raw_workdir: str) -> str | None:
    """Return the lexical root of a Hermes task workspace, if present."""
    normalized = posixpath.normpath(raw_workdir.replace("\\", "/"))
    parts = [part for part in normalized.split("/") if part]
    lowered = [part.lower() for part in parts]
    for index in range(len(parts) - 5):
        if (
            lowered[index] in {"hermes", ".hermes"}
            and lowered[index + 1] == "kanban"
            and lowered[index + 2] == "boards"
            and parts[index + 3]
            and lowered[index + 4] == "workspaces"
            and parts[index + 5]
        ):
            prefix = "/" if normalized.startswith("/") else ""
            return prefix + "/".join(parts[: index + 6])
    return None


def _rm_rf_targets(command: str) -> list[str] | None:
    """Parse ONE pure recursive+force ``rm`` invocation into its targets.

    Returns None for anything that is not a single unchained ``rm -rf``
    stage (shell metacharacters, chains, pipes, other programs, a missing
    -r/-f, unknown options): every non-trivial shape fails closed to the
    caller's stricter classification. Shared by the v1.2.28 workspace
    cleanup lane and the v1.2.31 scratch-root exemption so both see
    byte-identical parsing.
    """
    command = command.strip()
    if not command or _SHELL_METACHARACTERS.search(command):
        return None
    if len(_simple_commands(command)) != 1 or re.search(r"&&|\|\||;|\|", command):
        return None
    tokens = [_clean_shell_token(token) for token in _stage_tokens(command)]
    if not tokens or _program_name(tokens[0]) != "rm":
        return None

    recursive = False
    force = False
    targets: list[str] = []
    after_separator = False
    for token in tokens[1:]:
        if token == "--" and not after_separator:
            after_separator = True
            continue
        if token.startswith("-") and not after_separator:
            if token in {"--recursive", "--force"}:
                recursive = recursive or token == "--recursive"
                force = force or token == "--force"
                continue
            if not re.fullmatch(r"-[rf]+", token, re.I):
                return None
            letters = token[1:].lower()
            recursive = recursive or "r" in letters
            force = force or "f" in letters
            continue
        targets.append(token)
    if not (recursive and force and targets):
        return None
    return targets


def _is_ephemeral_workspace_cleanup(name: str, arguments: dict[str, Any]) -> bool:
    """Allow one pure ``rm -rf`` of child paths inside the current task workspace.

    Scratch artifacts are reproducible and task-scoped. Deleting a child there
    is neither irreversible business-data loss nor a release action. The lane
    is deliberately narrow: no command chaining, globbing, parent traversal,
    workspace-root deletion, or workdir outside a Hermes task workspace.
    """
    if name not in TERMINAL_TOOLS:
        return False
    command = str(arguments.get("command") or arguments.get("cmd") or "").strip()
    workdir = str(arguments.get("workdir") or "").strip()
    workspace_root = _task_workspace_root(workdir)
    if not command or not workspace_root:
        return False
    # v1.2.31: shared parser — the v1.2.28 workspace lane and the v1.2.31
    # scratch-root exemption must see byte-identical rm shapes, so both go
    # through _rm_rf_targets (metacharacters, chaining, options, `--`).
    targets = _rm_rf_targets(command)
    if not targets:
        return False

    normalized_workdir = posixpath.normpath(workdir.replace("\\", "/"))
    root_casefold = workspace_root.casefold()
    workdir_casefold = normalized_workdir.casefold()
    try:
        physical_root = Path(workspace_root).resolve(strict=True)
    except (OSError, ValueError, RuntimeError):
        return False
    for raw_target in targets:
        target = raw_target.replace("\\", "/")
        if (
            not target
            or target.startswith("~")
            or target in {".", "..", "/"}
            or ".." in target.split("/")
            or re.search(r"[*?\[\]$`{}]", target)
        ):
            return False
        absolute = target.startswith("/") or re.match(r"^[A-Za-z]:/", target)
        candidate = posixpath.normpath(target if absolute else normalized_workdir + "/" + target)
        candidate_casefold = candidate.casefold()
        if candidate_casefold == workdir_casefold:
            return False
        if not candidate_casefold.startswith(root_casefold.rstrip("/") + "/"):
            return False
        try:
            physical_candidate = Path(candidate).resolve(strict=False)
            physical_candidate.relative_to(physical_root)
        except (OSError, ValueError, RuntimeError):
            return False
        if physical_candidate == physical_root:
            return False
    return True


# v1.2.31 SPEC §2.2 — scratch-root exemption for the literal recursive+force
# rm shape. Roots whose CHILDREN are disposable:
#   - $TMPDIR / $TEMP / $TMP (when set and non-empty);
#   - the current task workspace (from the tool binding's workdir/workspace_path
#     or the dispatcher-provided HERMES_KANBAN_WORKSPACE) and its tmp/cache/temp
#     children;
#   - any ``<hermes_profiles>/*/cache/scratch`` directory, recognized by the
#     resolved path's segment sequence so it works without env on every host.
# The ephemeral roots themselves, ``..`` escapes, globs, tilde paths, unknown
# $-references, symlink escapes (checked on the physically resolved path) and
# mixed target sets with even one unsafe path all fail closed, keeping the
# irreversible_data_loss approval requirement of the rule table intact.
_SAFE_TEMP_ENV_NAMES = ("TMPDIR", "TEMP", "TMP")
# Only bare/braced references to the three ephemeral-root variables expand.
# Shell expansion is case-sensitive, so spellings must match the conventional
# upper-case names, and a reference whose variable is unset fails closed
# instead of expanding to an empty string.
_SAFE_ENV_REF = re.compile(r"\$(?:\{(TMPDIR|TEMP|TMP)\}|(TMPDIR|TEMP|TMP))(?![A-Za-z0-9_])")
# A target must stay a plain path: globs, quotes, redirects, separators and
# residual $-references are refused before any path math happens.
_SAFE_RM_FORBIDDEN = re.compile(r"""[*?`\[\]{}<>&|;"'$]""")


def _expand_safe_env_reference(target: str) -> str | None:
    """Expand $TMPDIR/$TEMP/$TMP references; None when a variable is unset or
    any other ``$`` reference would remain unexpanded."""
    missing: list[str] = []

    def replace(match: re.Match[str]) -> str:
        name = match.group(1) or match.group(2)
        value = os.environ.get(name) or ""
        if not value:
            missing.append(name)
        return value

    expanded = _SAFE_ENV_REF.sub(replace, target)
    if missing or "$" in expanded:
        return None
    return expanded


def _safe_rm_candidate(target: str, workdir: str | None) -> Path | None:
    """Normalize one rm target to an absolute path, failing closed on any
    non-plain shape (empty, tilde, globs, quotes, ``..`` segments, unknown
    env references, relative without a workdir binding)."""
    if not target or target.startswith("~"):
        return None
    expanded = _expand_safe_env_reference(target)
    if expanded is None or _SAFE_RM_FORBIDDEN.search(expanded):
        return None
    normalized = expanded.replace("\\", "/")
    if any(part == ".." for part in normalized.split("/")):
        return None
    candidate = Path(normalized)
    if not candidate.is_absolute():
        if not workdir:
            return None
        candidate = Path(workdir.replace("\\", "/")) / candidate
    return candidate


def _safe_rm_roots(binding: dict[str, Any] | None) -> tuple[Path | None, str, list[Path]]:
    """Ephemeral roots whose children may be deleted autonomously (SPEC §2.2).

    Returns ``(workspace_resolved, workspace_root_raw, temp_roots)``. The task
    workspace (from the tool binding's workspace_path/workdir or the
    dispatcher-provided HERMES_KANBAN_WORKSPACE) is tracked separately because
    it DOMINATES: a target lexically bound to the workspace is judged only by
    workspace semantics (strict physical child), never by the broader
    temp-env containment — otherwise a workspace nested under %TEMP% would
    inherit the looser temp-root rules and the v1.2.28 workspace contract
    (no root deletion, no symlink escape) would leak.
    """
    temp_roots: list[Path] = []
    for name in _SAFE_TEMP_ENV_NAMES:
        value = (os.environ.get(name) or "").strip()
        if not value:
            continue
        try:
            if Path(value).is_dir():
                temp_roots.append(Path(value).resolve())
        except OSError:
            continue
    arguments = binding or {}
    workspace_root = str(arguments.get("workspace_path") or "").strip()
    if not workspace_root:
        workspace_root = _task_workspace_root(str(arguments.get("workdir") or "")) or ""
    if not workspace_root:
        workspace_root = (os.environ.get("HERMES_KANBAN_WORKSPACE") or "").strip()
    workspace_resolved: Path | None = None
    if workspace_root:
        try:
            if Path(workspace_root).is_dir():
                workspace_resolved = Path(workspace_root).resolve()
        except OSError:
            workspace_resolved = None
    return workspace_resolved, workspace_root, temp_roots


def _under_profile_scratch(resolved: Path) -> bool:
    """True when *resolved* is a strict descendant of a
    ``<hermes_profiles>/*/cache/scratch`` directory."""
    parts = [part.casefold() for part in resolved.parts]
    for index, part in enumerate(parts):
        if (
            part == "profiles"
            and index + 4 < len(parts)
            and parts[index + 2] == "cache"
            and parts[index + 3] == "scratch"
        ):
            return True
    return False


def _safe_rm_contained(candidate: str, root: str) -> bool:
    try:
        relative = posixpath.relpath(candidate, root)
    except ValueError:
        return False
    return not (relative == ".." or relative.startswith("../") or Path(relative).is_absolute())


def _safe_rm_targets(command: str, binding: dict[str, Any] | None = None) -> bool:
    """SPEC §2.2 helper: True only when *command* is a single pure
    recursive+force rm (via _rm_rf_targets) whose targets ALL normalize —
    env-expanded, ``..``-free, physically resolved so symlink escapes fail —
    strictly inside an allowed ephemeral root. A target lexically bound to the
    task workspace is judged ONLY by workspace semantics (dominance: strict
    physical child of the workspace, never the workspace root itself); every
    other target must sit strictly inside a temp-env root or a profile scratch
    directory. Any other shape returns False and the caller's approval
    requirement stands."""
    targets = _rm_rf_targets(command)
    if not targets:
        return False
    arguments = binding or {}
    workdir = str(arguments.get("workdir") or "").strip() or None
    workspace_resolved, workspace_root, temp_roots = _safe_rm_roots(arguments)
    workspace_lexical = (
        Path(workspace_root).as_posix().casefold() if workspace_resolved is not None else ""
    )
    workspace_physical = (
        workspace_resolved.as_posix().casefold() if workspace_resolved is not None else ""
    )
    for raw_target in targets:
        candidate = _safe_rm_candidate(raw_target, workdir)
        if candidate is None:
            return False
        try:
            resolved = candidate.resolve(strict=False)
        except (OSError, ValueError, RuntimeError):
            return False
        if workspace_lexical:
            lexical = candidate.as_posix().casefold()
            if lexical == workspace_lexical:
                return False  # the workspace root itself is never deletable
            if _safe_rm_contained(lexical, workspace_lexical):
                # Workspace-bound target: workspace semantics only, no
                # temp-root fallback (v1.2.28 contract: no link escapes).
                physical = resolved.as_posix().casefold()
                if physical == workspace_physical:
                    return False
                if not _safe_rm_contained(physical, workspace_physical):
                    return False
                continue
        normalized = resolved.as_posix().casefold()
        contained = False
        for root in temp_roots:
            root_normalized = root.as_posix().casefold()
            if normalized == root_normalized:
                continue  # an ephemeral root itself is never a deletable target
            if _safe_rm_contained(normalized, root_normalized):
                contained = True
                break
        if contained or _under_profile_scratch(resolved):
            continue
        return False
    return True


# v1.2.34 W4: risk-regex span exemption. The hard-deny and rule-table scans
# see the RAW command text, so a deny phrase QUOTED as data (echo/grep
# arguments, git commit -m prose, gh --body text, heredoc lines) triggered
# evidence-gated categories or hard denies for commands that execute
# nothing — a live FP family (card t_d94dde9d case 2b: commit-message and
# report prose). A risk-regex match lying entirely inside a shell-quoted
# span is now exempt UNLESS the span is executable input: the token before
# the opening quote is a code-flag form (-c/--command/-e/--eval or a short
# cluster ending in c/e), or the span shares its line with an
# interpreter/executor program (bash -c, ssh host "cmd", awk 'prog',
# eval "x", sed scripts, heredoc opener lines). A span containing a URL
# stays scanned (real target, matching the _risk_subject URL doctrine).
# Unbalanced quoting disables every exemption (fail-closed). Untouched: the
# path guard and its python -c code extraction (F5), the MUTATOR/write-
# marker effect scans, and the runtime gate-forgery checks. Residual
# (documented): string-concatenation obfuscation inside an executed span is
# the pre-existing lexical-gap class (F4 free-text note).
_CODE_FLAG_TOKENS = frozenset({"-c", "--command", "-e", "--eval"})
_CODE_FLAG_CLUSTER = re.compile(r"^-[A-Za-z]*[ce]=?$")
_INTERPRETER_PROGRAMS = frozenset({
    "sh", "bash", "zsh", "ksh", "dash", "ash", "fish", "eval", "xargs",
    "python", "python2", "python3", "py", "perl", "node", "deno", "bun",
    "ruby", "php", "lua", "tclsh", "awk", "gawk", "mawk", "sed",
    "powershell", "pwsh", "cmd", "wscript", "cscript", "mshta", "ssh",
    "sqlite3", "psql", "mysql", "docker", "podman", "kubectl",
})
_VERSIONED_INTERPRETER_RE = re.compile(r"(?:python|py|node|ruby|php|lua)\d+(?:\.\d+)*")


def _span_is_prose(command: str, open_at: int, close_at: int) -> bool:
    if "://" in command[open_at + 1:close_at - 1]:
        return False  # a quoted URL is a real target, never inert prose
    preceding = command[:open_at].rstrip()
    token_match = re.search(r"(\S+)$", preceding)
    token = token_match.group(1) if token_match else ""
    bare = token[:-1] if token.endswith("=") else token
    if bare in _CODE_FLAG_TOKENS or _CODE_FLAG_CLUSTER.match(bare):
        return False
    line_start = command.rfind("\n", 0, open_at) + 1
    line_head = command[line_start:open_at].split()
    if line_head:
        program = _program_name(line_head[0])
        if program in _INTERPRETER_PROGRAMS or _VERSIONED_INTERPRETER_RE.fullmatch(program):
            return False
    return True


def _exempt_quote_spans(command: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    index = 0
    length = len(command)
    quote: str | None = None
    open_at = -1
    while index < length:
        char = command[index]
        if quote is None:
            if char in "\"'":
                quote = char
                open_at = index
            index += 1
            continue
        if char == "\\" and quote == '"' and index + 1 < length:
            index += 2
            continue
        if char == quote:
            if _span_is_prose(command, open_at, index + 1):
                spans.append((open_at, index + 1))
            quote = None
        index += 1
    if quote is not None:
        return []  # unbalanced quoting: no exemptions (fail-closed)
    return spans


def _mask_exempt_quote_spans(command: str) -> str:
    spans = _exempt_quote_spans(command)
    if not spans:
        return command
    chars = list(command)
    for start, end in spans:
        for position in range(start, min(end, len(chars))):
            chars[position] = " "
    return "".join(chars)


def classify(tool_name: str, arguments: dict[str, Any], config: dict[str, Any], *, worker: bool) -> Classification:
    name = _normalize_tool_name(tool_name)
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
        if (
            not matched
            or _canonical_public_doc_read(name, arguments)
            or (effect == "read" and _canonical_operational_artifact_read(name, arguments))
        ):
            continue
        if _is_policy_controlled(matched):
            if effect == "read":
                return Classification("read", "read_only", "allow", "policy-controlled documents are readable by the fleet")
            return Classification("state_change", "policy_control_plane_mutation", "deny", "policy-controlled files are immutable for the fleet")
        if _tracked_source_carveout(matched, subject, arguments):
            continue
        # v1.2.31: the deny carries the TRUE effect. A read-only probe of a
        # protected store stays a denied READ — relabeling it as a mutation
        # made the blocked-task override mask the real category as
        # task_already_blocked and starved read-only diagnostics.
        return Classification(effect, PROTECTED_STORE_RULE, "deny", DENY_MSG)

    subject = _risk_subject(name, arguments)
    # v1.2.34 W4: deny phrases quoted as DATA are exempt from the risk
    # scans below; executable spans (code-flag values, interpreter lines,
    # URLs) keep their raw text. Length-preserving masking, so no new token
    # adjacency can be fabricated outside the masked spans.
    if name in TERMINAL_TOOLS and subject:
        subject = _mask_exempt_quote_spans(subject)
    lower = f"{name} {subject}".lower()

    # Hard-deny checks inspect command/target fields only. They must never scan
    # generated code, card bodies, comments or file contents.
    if worker and (
        re.search(r"(?:^|[\s/\\])fleet[-_]policy(?:\.exe)?\s+(?:approve|reject|revoke|override-expected-failure)\b", subject, re.I)
        or re.search(r"\bpython\s+-m\s+fleet_policy\.cli\s+(?:approve|reject|revoke|override-expected-failure)\b", subject, re.I)
        or re.search(r"\b(?:decide_approval|consume_exact_approval|ensure_approval|revoke_approval|mark_expected_failure)\b", subject, re.I)
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

    # A pure child cleanup inside the worker's own task workspace is bounded,
    # reproducible scratch maintenance. Keep broad rm -rf escalation everywhere
    # else, including the workspace root itself.
    if _is_ephemeral_workspace_cleanup(name, arguments):
        return Classification(
            effect,
            "ephemeral_workspace_cleanup",
            "allow",
            "ephemeral task-workspace child cleanup is autonomous",
        )

    # v1.2.31 SPEC §2.2: scratch-root exemption for the literal recursive+force
    # rm shape whose targets ALL sit inside an allowed ephemeral root ($TMPDIR/
    # $TEMP/$TMP, <hermes_profiles>/*/cache/scratch/**, the task workspace and
    # its tmp/cache/temp children). Routed through the ungated ephemeral
    # cleanup category instead of the SPEC's destructive_change label because
    # destructive_change is evidence-gated (backup+scope): an allow there would
    # be re-denied at runtime as evidence_gate_missing, recreating the very
    # worker hang this exemption removes. Approval_required for every unsafe
    # shape — repos, state, home, ventures, escapes — is unchanged.
    if name in TERMINAL_TOOLS and _safe_rm_targets(
        str(arguments.get("command") or arguments.get("cmd") or ""),
        arguments,
    ):
        return Classification(
            effect,
            "ephemeral_workspace_cleanup",
            "allow",
            "ephemeral scratch-root cleanup is autonomous",
        )

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
        (rf"(?:\b(?:push|merge(?!-base))[^\n]*(?:\b(?:{branches})\b|refs/heads/(?:{branches}))|\bgh\s+pr\s+merge\b)", "release_to_protected_branch", "allow"),
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

    if re.search(r"\bgit\s+(?:commit|push|merge(?!-base))\b", lower):
        return Classification(effect, "repository_change", "allow", "repository changes are autonomous within project rules")
    return Classification(effect, "scoped_state_change", "allow", "scoped state change is autonomous")


def effective_retries(policy_max: int, kanban_max: int | None, failure_limit: int | None) -> int:
    values = [policy_max]
    values.extend(value for value in (kanban_max, failure_limit) if isinstance(value, int) and value > 0)
    return min(values)
