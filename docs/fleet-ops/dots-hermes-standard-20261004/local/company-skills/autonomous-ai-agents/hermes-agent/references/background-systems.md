# Durable & Background Systems

Four systems run alongside the main conversation loop. Quick reference
here; full developer notes live in `AGENTS.md`, user-facing docs under
`website/docs/user-guide/features/`.

### Delegation (`delegate_task`)

Spawn a subagent with an isolated context + terminal session.

- **Single or batch:** use the CURRENT tool schema, normally `delegate_task(tasks=[{goal, context, ...}])`. Batch concurrency is bounded by `delegation.max_concurrent_children`.
- **Background:** top-level delegation already returns immediately; do not pass the legacy `background=true` flag. Grouping controls result delivery, not execution order. Use `action=list|steer|stop` for live control.
- **Depth:** capability is depth-derived and bounded by `delegation.max_spawn_depth`; do not rely on legacy per-call `role` to grant delegation.
- **Not durable.** A backgrounded child is still process-local — if the
  parent process exits, the child is lost. For work that must outlive
  the process, use `cronjob` or
  `terminal(background=True, notify_on_complete=True)`.

Config: `delegation.*` in `config.yaml`.

### Cron (scheduled jobs)

Durable scheduler — `cron/jobs.py` + `cron/scheduler.py`. Drive it via
the `cronjob` tool, the `hermes cron` CLI (`list`, `add`, `edit`,
`pause`, `resume`, `run`, `remove`), or the `/cron` slash command.

- **Schedules:** duration (`"30m"`, `"2h"`), "every" phrase
  (`"every monday 9am"`), 5-field cron (`"0 9 * * *"`), or ISO timestamp.
- **Per-job knobs:** `skills`, `script` (pre-run collection; `no_agent=True` makes the script the whole job), `context_from`, `workdir`, and delivery. Distinguish scheduler capability from agent-tool authority: current official cron docs reserve per-job model/provider/reasoning pins to user-owned configuration; the agent-facing cron tool cannot change them. Check the current tool schema before promising autonomous model routing. Do not bypass that boundary via direct file edits or another surface.
- **Invariants:** 3-minute hard interrupt per run, `.tick.lock` file
  prevents duplicate ticks across processes, cron sessions pass
  `skip_memory=True` by default, and cron deliveries are framed with a
  header/footer instead of being mirrored into the target gateway
  session (keeps role alternation intact).

User docs: https://hermes-agent.nousresearch.com/docs/user-guide/features/cron

### Curator (skill lifecycle)

Background maintenance for agent-created skills. Tracks usage, marks
idle skills stale, archives stale ones, keeps a pre-run tar.gz backup
so nothing is lost.

- **CLI:** `hermes curator <verb>` — `status`, `usage`, `run`, `pause`,
  `resume`, `pin`, `unpin`, `archive`, `restore`, `list-archived`, `prune`,
  `backup`, `rollback`.
- **Slash:** `/curator <subcommand>` mirrors the CLI.
- **Scope:** only touches skills with `created_by: "agent"` provenance.
  Current docs default `curator.prune_builtins=true`: unused bundled skills may also be archived; hub-installed skills remain exempt. Verify the installed config/source before assuming agent-only scope. Auto-transitions archive rather than delete. Pinned skills and cron-referenced skills are protected; archive-TTL purge is a separate mechanism.
- **Cost:** the deterministic inactivity/prune sweep runs for free. The
  aux-model "consolidate overlapping skills into umbrellas" pass is
  **off by default** — opt in with `curator.consolidate: true` or
  `hermes curator run --consolidate`. Routine background curation costs
  zero tokens.
- **Telemetry:** sidecar at `~/.hermes/skills/.usage.json` holds
  per-skill `use_count`, `view_count`, `patch_count`,
  `last_activity_at`, `state`, `pinned`.

Config: `curator.*` (`enabled`, `interval_hours`, `min_idle_hours`,
`stale_after_days`, `archive_after_days`, `backup.*`).
User docs: https://hermes-agent.nousresearch.com/docs/user-guide/features/curator

### Kanban (multi-agent work queue)

Durable SQLite board for multi-profile / multi-worker collaboration.
Users drive it via `hermes kanban <verb>`; dispatcher-spawned workers
see a focused `kanban_*` toolset gated by `HERMES_KANBAN_TASK`, and
orchestrator profiles can opt into the broader `kanban` toolset. Normal
sessions still have zero `kanban_*` schema footprint unless configured.

- **CLI verbs (common):** `init`, `create`, `list` (alias `ls`),
  `show`, `assign`, `link`, `unlink`, `comment`, `complete`, `block`,
  `unblock`, `archive`, `tail`. Less common: `watch`, `stats`, `runs`,
  `log`, `dispatch`, `daemon`, `gc`.
- **Worker/orchestrator toolset:** `kanban_show`, `kanban_complete`,
  `kanban_block`, `kanban_heartbeat`, `kanban_comment`, `kanban_create`,
  `kanban_link`; profiles that explicitly enable the `kanban` toolset
  outside a dispatcher-spawned task also get `kanban_list` and
  `kanban_unblock` for board routing.
- **Dispatcher** runs inside the gateway by default
  (`kanban.dispatch_in_gateway: true`) — reclaims stale claims,
  promotes ready tasks, atomically claims, spawns assigned profiles.
  Auto-blocks a task after `failure_limit` consecutive spawn failures
  (default 2; configurable via `kanban.failure_limit` or per-task
  `max_retries`).
- **Isolation:** board is the hard boundary (workers get
  `HERMES_KANBAN_BOARD` pinned in env); tenant is a soft namespace
  within a board for workspace-path + memory-key isolation.

User docs: https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban

#### Trust-boundary discovery

When reviewing evidence issuance, pin the integration repository and native Hermes core separately; a plugin merge does not establish the installed core identity. Inspect every writer (tools, dashboard, CLI) before treating comment authors or run metadata as authority. Run assignment is scheduler intent; a content digest proves integrity, not the issuer. Reproduce questionable writers only in an isolated database/source-function harness and label that scope explicitly — it is not a live HTTP authentication test. Inspect existing terminal-transaction event/CAS patterns before proposing new storage.

For principal-bound write proofs, trace dispatcher spawn, live agent invocation and the native DB transaction separately. Do not confuse runtime `effective_task_id` (tool-resource isolation) with the Kanban target, or provider tool-call IDs with runtime-issued credentials. Check delegated child context before reading inherited worker environment, and preserve the child's own session identity without inventing a Kanban run. Test successful task/run CAS as consistency, not authentication; separately inject event INSERT failure to prove business/run/event rollback using the actual transaction helper. A source-function fixture is never a positive authenticated-launch proof. Internal-only context protects public API provenance only within an explicit trusted host/storage boundary; private parameters cannot authenticate arbitrary same-process Python or raw SQL writers.

For read-only source audits, avoid invoking the Hermes launcher merely to discover profiles when an interrupted update is possible: even `hermes profile list` may trigger startup recovery. Prefer scoped filesystem/profile discovery; do not repair or update runtime as an audit side effect.
