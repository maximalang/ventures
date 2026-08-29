# Fleet Policy Control Plane

## Supported architecture

The control plane is a standard Hermes plugin installed per universal profile. It uses the official `pre_tool_call` directive hook as the enforcement chokepoint, observer hooks for accounting, and the existing Kanban SQLite/CLI for task context and projections. Hermes core is not patched.

Runtime configuration lives in `config/fleet-policy.yaml`; shared state lives in ignored `.state/fleet-policy.db`.

## Enforcement flow

1. Resolve `HERMES_KANBAN_TASK`, board, run, assignee, task body/comments/skills.
2. Require exact `task_type: research|code|review|ops` for worker state-changing calls.
3. Canonicalize and redact arguments; compute SHA-256 `args_hash`.
4. Check hard budgets and anti-loop history.
5. Classify `allow`, `deny`, or `approval_required`.
6. For approval, persist an exact binding `(task_id, action, target, args_hash)` and block the call.
7. A non-worker operator may approve with `fleet-policy approve <rule_key> --by <name>`; the next exact call consumes the grant atomically before execution. Changed payloads never match and grants cannot be reused.
8. Significant events project to the task as a Kanban comment/block. Company Bot Chat delivery is explicit (`fleet-policy drain-notifications`) and never auto-drained from the pre-tool path, so repeated blocks cannot spam `company`. `fleet-policy fail-notifications --all-pending` retires stale outbox rows.

## Budget and anti-loop interaction

Budget limits are per task type. Token counters use provider/runtime `post_api_request.usage` when present and count GENERATED tokens only (`completion_tokens`); `prompt_tokens` is the full re-sent context on every request and would exhaust any healthy worker in a handful of calls. Missing usage is not guessed. Monetary cost remains `unavailable` because GPT/Z.AI subscription runtimes do not provide authoritative per-request currency cost.

Retry enforcement is dispatcher-owned: `kanban.failure_limit` and per-task `max_retries` govern task-level retries. The plugin deliberately does NOT derive a retry budget from `api_request_error` volume, because Hermes fires that hook once per failed provider inside a single healthy turn while walking its fallback chain — counting it would block every worker on infrastructure noise. The pure `effective_retries = min(policy retries, per-task max_retries, kanban.failure_limit)` helper remains covered as the documented reconciliation rule, but executable retry state stays in the dispatcher. Identical-call and same-failure thresholds are counted in the shared DB. Wall-clock uses task `started_at`; tool-call count uses pre-tool decisions.

## RR context

Hermes has no generic metadata-driven arbitrary skill loader for an already-created task. Supported controls are combined:

- new RR tasks use `--skill rr-project`;
- the plugin registers a bounded cache-safe `rr-project` system-prompt section when `HERMES_KANBAN_BOARD=rr-team`;
- the guidance points workers to the canonical RR `AGENTS.md` and `CLAUDE.md` rather than duplicating them.

## Coverage

Covered: every normal Hermes tool routed through the built-in tool executor, including underlying tools invoked through Tool Search. `pre_tool_call` is fail-closed on plugin exception/timeout for state-changing paths.

Known gaps:

- shell commands or external programs launched outside a Hermes agent process are not intercepted;
- the plugin is a workflow policy boundary, not an OS security sandbox: all local profiles run as the same Windows user, so deliberately obfuscated arbitrary code could bypass textual terminal classification or write files directly. Defense-in-depth denies known approval APIs/DB paths and worker-context decisions; hostile-code isolation would require a separate OS account/container;
- direct human edits to Kanban/profile files are outside the hook;
- already-running sessions do not pick up newly installed plugins until restarted;
- `kanban_task_claimed` is observer-only, so missing task type is enforced at the first state-changing tool call and by task-creation/cutover conventions, not by vetoing the dispatcher claim itself;
- company Bot Chat delivery is explicit (`fleet-policy drain-notifications`) and never auto-fired from a pre-tool callback, avoiding spam and nested agent loops.

Compensating controls: official CLI-only config changes, immutable plugin install SHA, SOUL rule, task creator conventions, dispatcher default owner/company, snapshots, rollback script, and post-cutover smoke tests.

Rollback is the repository-side operator command `uv run python scripts/fleet_migration.py rollback [--dry-run]`; the `fleet-policy` CLI intentionally handles policy state only and does not duplicate migration orchestration.
