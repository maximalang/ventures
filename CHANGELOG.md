# Changelog

## [1.2.6] - 2026-09-02

### Fixed
- Read-effect classifier false denies eliminated. `READ_COMMAND` was missing `sed`, `head`, `tail`, `stat`, `wc`, `file`, `du`, `sort`, `uniq`, `cut`, `tr`, `column` and several git subcommands (`clone`, `fetch`, `ls-remote`, `ls-files`, `ls-tree`, `rev-list`, bare `branch --list/-l`), so reading a policy-controlled file (e.g. `sed -n '49,75p' config/fleet-policy.yaml`) was classified as `state_change` and hard-denied as `policy_control_plane_mutation` instead of allowed as `read_only`.
- Chained terminal commands with a leading `cd <dir>` segment (`cd repo && git clone ...`) were misclassified as `state_change` because the `cd` segment never matched the read whitelist. Bare `cd` segments are now read no-ops.
- Effect matching switched from `READ_COMMAND.search()` to anchored `READ_COMMAND.match()` per segment, and all read keywords are word-bounded. Previously non-word-bounded keywords (`tr`, `type`) matched mid-word inside adversarial commands ("transfer ownership...", "...type..."), misclassifying approval-required serious-risk commands as read-only.
- In-place/redirecting variants of otherwise read-only utilities (`sed -i`, `sort -o`) are explicitly classified as mutations via `WRITE_FLAG`, so the effect classifier and the protected-path guard agree.

### Added
- Regression tests: `test_v126_read_classifier_no_false_control_plane_denies` (10 read cases against policy-controlled paths, chained cd+clone, ls-remote) and `test_v126_write_and_destructive_variants_are_not_read` (sed -i/sort -o/git branch -D/-d/clean/tag -d stay non-read).

## [1.2.5] - 2026-09-01

### Security
- Owner-principal enforcement: `approve`/`reject`/`revoke` decisions are no longer accepted on a free-text `--by` claim alone. Every decision must present `--confirm <last 8 chars of the binding>` and runs only in an interactive owner terminal (TTY); non-TTY invocations fail closed with an explicit reason. Dispatcher workers remain blocked by the environment guard even with a valid confirmation code.
- New `fleet-policy revoke` subcommand and `revoke_approval` store method: granted (`approved`) or still-`pending` bindings can be revoked (`status='revoked'`, `revoked_at`, `revoked_by`). A revoked row never matches the consumption filter, so the granted action can no longer execute; the row is preserved as immutable audit history. Revoke of an already-consumed/rejected/revoked row fails closed.
- Worker self-approval denial now also covers `revoke` (CLI + `python -m fleet_policy.cli revoke` + direct `revoke_approval` calls).
- Schema v4 migration adds `revoked_at`/`revoked_by` columns to `approvals` idempotently; historical rows (including the incident audit row) are preserved untouched. `schema_migrations` carries markers 1-4.

### Fixed
- Notifier drain delivery timeout raised from a hardcoded 15s to `DELIVERY_TIMEOUT_SECONDS = 90`: measured bot-turn latency (~19s session resume + one turn) made nearly every batch expire, releasing rows into an endless retry cycle. Regression test pins the constant >= 60s and asserts the delivery call receives it.

## [1.2.4] - 2026-08-31

### Fixed
- Anti-loop stops are keyed and projected by dispatch run: the same failure stops once per run, a genuinely new run receives a fresh stop, and post-tool payloads retain their board/status/run binding.
- A `task_already_blocked` fallback denial no longer creates another Kanban projection, preventing comment/notification amplification after the primary block.

## [1.2.3] - 2026-08-31

### Fixed
- Notifier hardening: `drain_company` delivers the whole pending batch in ONE bounded bot turn (`--max-turns 1`, 15s timeout) instead of one 120s turn per row; `TimeoutExpired` no longer leaks rows — the batch claim is released and rows stay pending. Concurrent drains cannot duplicate a batch (atomic `claim_token` on `notification_outbox`; stale `dispatching` claims older than 5 minutes are reclaimed). Stores missing the new outbox columns are healed idempotently on `migrate()`.
- Notifier transport hardening: any expected transport failure (`TimeoutExpired`, `OSError`/`FileNotFoundError`, `subprocess.SubprocessError`) or non-zero child exit during the bot turn releases the claim immediately, keeps rows `pending`, and the CLI exits cleanly; malformed or unbound rows are released without blocking the rest of the batch. Delivery-time readback via the official board-bound Kanban CLI (`hermes kanban --board <board> show <task_id> --json`) suppresses task-bound alerts whose task is `done`/`archived`/`superseded` as `suppressed` with auditable `suppression_reason`/`resolved_at` (no owner notification, immutable events untouched); unknown or unresolvable lookups fail safe — rows stay pending and nothing is delivered as an active alert. Active serious task-bound alerts still deliver in the single bounded turn; the live-status cache bounds duplicate logical events to one read per exact board/task binding.

### Added
- `fleet_policy.alerting.is_owner_alertable`: owner alerts require a task binding and only serious rules (financial, rollback, destructive, security, approval-required); diagnostic no-task denies no longer alert.

## [1.2.2] - 2026-08-31

### Fixed
- `PolicyStore.migrate()` self-heals half-migrated stores: при наличии маркера версии 3, но отсутствии таблиц `run_budget` / `run_state` / `run_call_history` они создаются идемпотентно на месте (без потери строк). Регрессия: post-release canary C6 2026-08-31 — живой общий store был полумигрирован, из-за чего run-scoped бюджеты (фича 1.2) были неработоспособны, и релиз 1.2.1 (head 3e24a986) был откатан на пин 186d8302.

## [1.2.1] - 2026-08-30

### Security
- Worker `execute_code` теперь требует exact one-time approval binding; operator sessions остаются доступны для bounded incident response.
- Release-bundle verifier требует все канонические пути с ожидаемым типом и отклоняет symbolic links до проверки manifest inventory.

### Added
- Канонический release bundle с детерминированным inventory и SHA-256 verification.
- `fleet-policy --version`, `build-bundle` и `verify-bundle`.

### Fixed
- Package/plugin/CLI version синхронизирована на `1.2.1`.
- Free-text Kanban reports не интерпретируются как выполнение описанных privileged actions.
