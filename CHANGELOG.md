# Changelog

## [1.2.14] - 2026-09-08

### Fixed
- Phantom approval counter: pending approval bindings now carry the board they were created on (`approvals.board`, idempotent v4-heal on legacy stores), and the `drain-notifications` tick first sweeps pending bindings through the live board (`HermesProjector.expire_closed_approvals`): a binding whose card is provably closed (done/archived/superseded) is written off as `expired` with an auditable reason — never approved/rejected (that stays the owner's decision), never deleted, and never re-grantable (`consume_exact_approval` still requires `status='approved'`). Unresolvable or board-less legacy rows stay pending (no expiry without live evidence). On 2026-09-07, 43 of 47 pending approvals belonged to closed cards.
- Eternal pending outbox rows: `post_api_request` budget/loop-stop payloads now include the run-context `board`/`task_status`/`run_key`, so `notification_binding()` resolves them and the drain can suppress closed-task rows instead of cycling claim→release→pending forever (39 of 83 pending outbox events on 2026-09-07 were budget denies without a board).
- Alert readability: `drain_company` non-approval sections are compact Russian HTML cards (`event_text`) instead of raw `json.dumps(indent=2)`; `approval_text` is an HTML card with emoji icons (🔴👁🚫🟠📊). Every dynamic value is HTML-escaped because the TG adapter delivers with ParseMode.HTML.

### Added
- `tests/test_v1214_noise_fix.py`: 13 contract tests — expiry sweep (closed→expired, open/unresolvable→pending, no worker-context expiry), board-bound budget-stop payloads drain and suppress, HTML escaping of `<`, `>`, `&` in every dynamic field, no raw JSON dumps in delivered text. Full suite: `uv run --frozen python -m pytest tests/ -q` → 349 passed (was 336 at 1.2.13).

### Known issues (recorded by company directive; deny semantics NOT weakened in this release)
- `worker_self_approval` is a fail-closed textual classifier: it also denies read-only commands whose arguments merely contain binding/decision literals (4 confirmed false-positive cases on 2026-09-07/08, including shell pattern-greps during this release run). Source exploration must use file read/search tools instead of shell greps carrying those literals. Classifier refinement is deferred to a scoped follow-up card.
- Item E (12 confirmed cases): lifecycle board calls (e.g. `kanban_heartbeat`) were still denied through the failure-loop collapse in live worker runs despite the v1.2.13 M-E exemption; root cause (deployed bundle vs. code path) is not yet verified. Lifecycle calls must be immune to failure-loop collapse so workers spend budget on work, not on deny loops — tracked for the next patch release.

## [1.2.13] - 2026-09-07

### Security
- Attestation identity validators anchor at end-of-string (`\Z` instead of `$`): sha40/sha64/task-id/timestamp fields reject trailing-newline padding instead of silently accepting `"<hex>\n"`; new bounded validators cover run ids (1-12 digits) and base refs (ref-name charset, max 89 chars), so attestation evidence cannot smuggle newline-padded payloads through any identity field (M1).
- Anti-loop collapse never severs the coordination channel: the `kanban_*` lifecycle namespace (show/list/context/diagnostics/attachments/comment/create/complete/block/unblock/heartbeat/link/edit/attach/attach_url/request_review/request_changes) is exempt from `identical_call_loop` and `same_failure_loop`. Executive tools (terminal, write_file, patch, read_file, ...) keep full collapse guarding; lifecycle calls still write call/failure ledger rows and still charge the tool-call budget, so runaway lifecycle loops remain bounded by `budget_exhausted` (M-E).

### Fixed
- Pristine-manifest determinism: `manifest-pristine-v1211.txt` recorded sha256 of Windows CRLF checkout bytes (57/57 CRLF-hashed, 0/57 canonical), so the same tree verified 0/57 on Linux CI (autocrlf=false) — non-deterministic attestation evidence. All 57 entries are regenerated as sha256 of the canonical git-blob (LF) bytes at the pinned pristine ref; a deterministic oracle test recomputes every hash from `git cat-file` (autocrlf/platform-independent), treats a CRLF blob as a hard failure, and CI checks out full history (`fetch-depth: 0`) so the pinned ref is present on ubuntu runners (M2).

### Added
- `tests/test_v1213_lifecycle_exempt.py`: 7 contract tests — namespace membership with normalization, lifecycle read/failure no-collapse replays, executive collapse controls, transition-stays-allow after two terminal-denies, budget charging and exhaustion still deny lifecycle calls.
- `tests/test_v1213_pristine_manifest.py`: deterministic LF-blob oracle over all 57 manifest entries at the pinned pristine ref (explicit skip when git/ref unavailable; full history in CI).
- M1 validator tests: 14 fail-closed cases (validator-level + evidence-build level). Full suite: `python -m pytest tests/ -q` → 336 passed (328 after M1, 314 at the 1.2.12 merge base).

## [1.2.12] - 2026-09-07

### Security
- Gate PASS markers are fail-closed and fully bound: a PASS arms a gate only when the same record binds the verdict to the expected head (`context["head"]`, 7-40 hex prefix match) and the card class it was issued under; an `artifact=` reference must physically exist on disk or the gate stays unarmed. PASS without head binding, on a foreign head, under a switched task class, or against a missing artifact never arms; a record carrying no head context is an unproven verdict.
- Company no-go is last-wins: a later authorized company no-go record revokes all earlier PASS evidence for every gate in the category; a later authorized go re-arms. The last authorized record still decides per gate, and record order is significant.
- Artifact-read containment is physical: the requested path is resolved (`Path.resolve(strict=True)`) inside trusted absolute roots with a two-phase parent check; unresolvable paths fail closed. Junction/symlink escapes are denied in both directions (a link inside the root pointing out, and a link outside the root targeting in). A configured trusted-root registry replaces the lexical shape routes; without a registry the historical lexical behavior is preserved. The lexical protections (normpath+lower, UNC refusal, residual `..` denial, secret basenames/segments) remain in force.
- Review-waiver removal: the card class sets the process but never waives a real side-effect gate — the `review` class no longer drops required `review`/`qa` gates, and review/qa records authored by the card's own assignee are ignored entirely (self-approval can neither attest nor revoke).
- Override authority for expected-failure overrides is two-factor: non-worker context AND the exact confirmation code derived from the binding identity (`task:sig:run`, last 8 chars, mirror of decide/revoke). The CLI `override-expected-failure` command gains `--confirm`; without the code the store refuses even on a non-worker host (rc=2). Tests derive the code from the binding itself, never manufacture authority by env removal.

### Added
- `tests/test_v1212_gate_binding.py`: 15 contract tests incl. foreign-head, unbound-PASS, post-PASS revoke, task_type switch, junction negatives, wrong confirm code, worker-context-with-code; gate fixtures and legacy contracts updated to carry the head/class binding. Full suite: `python -m pytest tests/ -q` → 178 passed (was 163).

## [1.2.11] - 2026-09-07

### Security
- Artifact-read containment: the `read_file` exception canonicalizes the requested path BEFORE any root matching (separators, drive/UNC prefixes, case, `..` collapse), refuses UNC impersonation (`//host/...`) outright, and fails closed on any residual `..` segment — traversal escapes, mixed-separator and case games never inherit the exception. Secret-shaped basenames (starting with `.env`, and `auth.json`) and segments (`sessions`, `request_dump`, `dumps`) stay denied inside trusted roots.
- Override authority: a dispatcher worker context can never record an expected-failure override — the authority is structural, matching decide/revoke, so a stripped shell variable cannot manufacture operator privilege. The second factor (exact confirm code, CLI `--confirm`) completes in 1.2.12.
- Path-guard structured operands: the path guard tokenizes per pipeline stage with quote awareness — quoted spans are prose by construction and removed before matching; the leading executable, known value-taking flags (`-m`, `--message`, `--format`, `-name`, ...) and the token after them are prose; a trailing `--opt=` contributes only its empty value; the value of an unquoted `-flag=path` token is a real filesystem operand and stays guarded; unquoted flag values fail CLOSED (inspected as operands). Code-bearing flag values (`python -c "…"`) are still scanned as operands. The narrowing removes the whole-string prose scan, not operand checks.
- Dead-guard removal: `consume_exact_approval` drops its no-op environment check; the approval lookup binds the effective path (`effect_path`) instead of the raw `target` argument.

### Added
- Gate evaluation is order-sensitive: for every required gate the LAST authorized record decides — a later fail/revocation from the gate's author cancels an earlier pass, a later pass re-arms; records from authors outside the gate's role set are ignored. Task-type classification is body-first: only the task body can establish the class, later comments and skill tags are never scanned, so a late comment can neither create a class for an unmarked body nor poison or switch an existing one. Regression coverage: `tests/test_v1211_gate_resolver.py`.

## [1.2.7] - 2026-09-03

### Security
- Added a narrow, fail-closed self-verification lane for exact-head QA: only explicit GitHub CLI view/list/check operations, REST `gh api` GET requests without payload/header fields, and local digest utilities are classified as read-only. GitHub REST POST/PUT/PATCH/DELETE, GraphQL, field/input/header flags, browser-opening flags, redirects, unknown executables and every non-read pipeline stage remain state changes.
- Terminal pipelines are now classified stage by stage instead of inheriting read semantics from the first command; an unknown or write-capable downstream stage cannot hide behind a read-only GitHub/hash probe.
- Direct Hermes namespaced calls (`functions.<tool>`) normalize to their canonical tool name without broad MCP namespace stripping.

### Added
- Regression coverage for exact-head PR/check/API/hash reads over policy-controlled paths, all GitHub API mutation spellings, pipeline smuggling, executable identity and namespaced direct tools.

### Release identity
- `1.2.7` is assigned to this prerequisite security fix. The draft controller lane that previously reserved the number must rebase after this release and advance its version before merge.

## [1.2.6] - 2026-09-02

### Security
- F-01 (High, QA finding t_e4351498): the write-marker scan of the read-effect classifier is now token-based and catches every mutating spelling of read-whitelisted utilities — long-form `sed --in-place[=SUFFIX]` and `sort --output[=FILE]`, suffix form `sed -i.bak`, option clusters (`sed -ni`, `sort -uo`), `tee` pipeline stages and shell output redirects (`>`, `>>`, `&>`). The previous `WRITE_FLAG` regex matched only the short forms `sed -i` / `sort -o`, so `sed --in-place ... <policy-controlled-path>` and `sort --output=... <policy-controlled-path>` were classified `read_only`/allow and could bypass the protected-path guard. Shell fd duplication (`2>&1`) and quoted payload text are not treated as writes. Fail-closed direction: unrecognized write forms keep the stricter classification.
- Regression tests: `test_f01_longform_write_variants_never_read` (nine mutating spellings on policy-controlled paths must be hard `policy_control_plane_mutation` denies), `test_f01_safe_read_variants_stay_read` (stdout-only sed/sort forms remain reads), `test_path_guard_inspects_target_not_replacement_text` (protected-path matching inspects the targeted filesystem path, never arbitrary replacement text — incident t_f2257124).

### Fixed
- Read-effect classifier false denies eliminated. `READ_COMMAND` was missing `sed`, `head`, `tail`, `stat`, `wc`, `file`, `du`, `sort`, `uniq`, `cut`, `tr`, `column` and several git subcommands (`clone`, `fetch`, `ls-remote`, `ls-files`, `ls-tree`, `rev-list`, bare `branch --list/-l`), so reading a policy-controlled file (e.g. `sed -n '49,75p' config/fleet-policy.yaml`) was classified as `state_change` and hard-denied as `policy_control_plane_mutation` instead of allowed as `read_only`.
- Chained terminal commands with a leading `cd <dir>` segment (`cd repo && git clone ...`) were misclassified as `state_change` because the `cd` segment never matched the read whitelist. Bare `cd` segments are now read no-ops.
- Effect matching switched from `READ_COMMAND.search()` to anchored `READ_COMMAND.match()` per segment, and all read keywords are word-bounded. Previously non-word-bounded keywords (`tr`, `type`) matched mid-word inside adversarial commands ("transfer ownership...", "...type..."), misclassifying approval-required serious-risk commands as read-only.
- In-place/redirecting variants of otherwise read-only utilities (`sed -i`/`--in-place`, `sort -o`/`--output`) are explicitly classified as mutations, so the effect classifier and the protected-path guard agree.

### Added
- Regression tests: `test_v126_read_classifier_no_false_control_plane_denies` (10 read cases against policy-controlled paths, chained cd+clone, ls-remote) and `test_v126_write_and_destructive_variants_are_not_read` (sed -i/sort -o/git branch -D/-d/clean/tag -d stay non-read).

### Note
- Version stays at `1.2.6`: `1.2.7` is occupied by the controller lane (`f3ba8bb`, `origin/wt/t_8f2f6d0d`), so the fix ships under the same unreleased version per the retry contract.
- Known gap (tracked separately, not in this stack): `config/fleet-policy.yaml` `protected.branches` lists only `main/master/production/release`, while the actual default branch is `codex/company-os`; GitHub branch protection currently compensates. Changing the policy config is itself a control-plane change and is out of scope for this stack.

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
