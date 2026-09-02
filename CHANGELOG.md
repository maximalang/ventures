# Changelog

## [1.2.7] - 2026-09-02

### Added

- Company OS deterministic next-bet controller v1, SHADOW mode only (`fleet_policy.controller`, `fleet-policy controller` CLI). Pure reducer over a board snapshot: fixed rule `running=0 && ready=0` with a revenue-critical `triage`/`todo` gate is `ACTIONABLE_IDLE`, never success. `decision_type` is `execute_bet` only when metric AND finance inputs are fresh/authoritative/non-gap and candidate effort is known; otherwise at most one `collect_evidence` recommendation for the single deterministic highest-priority missing-evidence step (`execution_eligible=false`, missing fields, collector owner/squad, freshness target, kill/rollback, evidence refs, no invented RUB). Ties (score or evidence priority), empty boards, blocked-only gates and busy/ready fleets resolve to `no_action` with a deterministic reason. Decisions are content-hashed (`decision_id` = idempotency key); the engine is append-only into the events store — an identical repeat run writes zero new records and returns the stored decision. Live input is read-only via the official `hermes kanban list --json` CLI (no direct kanban DB access); canonical boards restricted to `rr-team`, `seo-site`. Shadow mode never creates/promotes/unblocks/archives/deletes tasks or alters cron/config.
- Tests: acceptance fixture (portfolio+seo-site+rr-team mirror), determinism/order-independence, zero-new-record repeat, empty/blocked/duplicate/tie cases, fail-closed invalid input, marker parser and live adapter.

### Changed

- Controller reducer re-derived from the exact v3 contract artifacts (controller_version `next-bet-shadow/2.0`, formula `econ-score/v3`): `score_rub = (E + A) * confidence * freshness - total_cost_rub` with C NOT discounted; freshness `2^(-oldest_age/30)` computed over the OLDEST mandatory evidence ref with floor 0.125 at age >= 90 days and `requires_reverification` beyond 90 days; candidates classified EXECUTABLE / EVIDENCE_GAP / BLOCKED_BUDGET / REJECTED; winner by the full deterministic order (§4): max score_rub, min total_cost_rub, max confidence, min oldest-ref age, lexicographic min source_task_id — exactly one winner or `no_action`; budget guardrails 10 000 RUB/op and 30 000 RUB/month/project (§6); anti-gaming guards (§5): double-count zeroing (smaller component, A when equal), avoided-loss admissible only for gate_removal/risk work and capped at independently evidenced loss exposure x event probability over 30 days, one mechanism = one candidate, pre-filled `score_components` rejected; kill criterion requires metric + window + explicit NONZERO adverse threshold even for C=0 (§8); execute gate additionally requires a fresh (<= 30d) authoritative board metric snapshot and non-gap economics state; every decision carries a machine-readable audit block (all candidates, classes, reasons, score components, winner, budget snapshot, inputs_hash). Snapshot input is now the v3 collector schema: `evaluated_at` collector stamp, canonical board/project/metric pairs (project and board are separate fields; `rr-team`->`recruiter-radar`/`accepted_evidence_backed_leads_28d`, `seo-site`->`seo-site`/`successful_organic_calculations_28d`; `rr-*` and `search-utility` never accepted), 12-field-style metric records with the value/observed_at<->evidence_gap nullability invariant (demand contract v3 §2), RUB-only money.
- Tests: v1-era battery and fixture superseded by `tests/test_controller_v3.py` + `tests/fixtures/controller_shadow_v3.json` (v3 mirror of portfolio+seo-site+rr-team; old files retained as stubs — deletions are prohibited on this branch). 29 tests: fixture acceptance (ACTIONABLE_IDLE -> single collect_evidence, execution_eligible=false, no invented RUB), QA arithmetic pins (f(90d)=0.125 exactly, f(20d)=0.629961, RR example -5842.26 RUB, negative-EV -6400 RUB), execute gates (fresh metric + ok economics + complete owner/squad/hypothesis/kill/rollback), budget guardrails, anti-gaming, full-order tie-break, determinism/idempotency (zero new records on repeat), fail-closed validation, read-only canonical live adapter.
- Shadow guarantees unchanged: no create/promote/unblock/archive/delete, no cron/config writes, append-only events store, idempotent content-hashed decision_id (`nbc2-`), Telegram-only digest.
- Contract lineage: ECONOMICS_SCORING_CONTRACT_V3.md (t_a92701e0, sha256 ed5b0848...), DEMAND_METRIC_SOURCE_CONTRACT_V3.md (t_dbb4235b, sha256 7922ee61...), QA contract_review_v3=pass (t_7ee1d606). Supersedes the v1-era reducer semantics derived from econ-score/v1 (t_871c9c3b).

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
