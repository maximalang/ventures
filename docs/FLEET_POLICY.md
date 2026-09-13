# Fleet Policy Control Plane

## Purpose

The fleet is an autonomous product company. `company` is the primary user-facing CEO/orchestrator; `default` is a technical Hermes profile. The user allocates capital and grants capabilities, not routine task approvals.

The control plane is a standard Hermes plugin using official `pre_tool_call`, observer hooks, system-prompt sections, Kanban CLI/SQLite and profile/gateway APIs. Hermes core is not patched.

## Autonomous mandate

Autonomous after role/evidence gates:

- protected/main merge and push;
- staging/production deploy;
- product/content publishing and advertising experiments;
- reversible cleanup/migration;
- paid experiments within a project mandate;
- free service-account creation without KYC or payment commitment.

Serious-only escalation:

- mass unsolicited outreach;
- spend over 10,000 RUB/transaction or 30,000 RUB/project/month;
- a new paid capability/payment rail;
- phone/KYC/domain/bank-owner action;
- legal/material reputation risk;
- ownership/root-access changes;
- irreversible data loss;
- material security/privacy policy changes.

## Evidence gates

Exact Kanban comments from independent roles unlock routine actions:

- protected branch: `gate:ci=pass` (tech/qa), `gate:review=pass` (qa), `gate:rollback=pass` (tech/operations);
- deploy: CI + `gate:qa=pass` + `gate:backup=pass` + rollback;
- publish: review + QA;
- reversible destructive change: `gate:backup=pass` + `gate:scope=pass`;
- spend: `gate:finance=pass` + `decision:company=go`.

Missing gates block the task with actionable diagnostics; they do not create a user approval request.

## Owner principal, hard-gate bindings and boundary classes (ADR-001 v2)

Serious-class approvals are exact one-time bindings owned by an authenticated owner principal. Since v1.2.18:

- binding tuple: every pending approval row carries `nonce` (issued at approve), `expires_at` (24h TTL, enforced at consumption; an expired grant is refused and re-armed as a fresh pending cycle), `principal_ref` (sha256 fingerprint of owner user/direct-chat ids — never the raw ids), decision `channel`, `amount_rub` and `scope` digest. Legacy rows keep v1 semantics (`NULL` expiry = never expires);
- decision-namespace forge guard: worker board writes (card bodies, comments, reasons) cannot mint company or owner authority markers — such a write is denied at the classifier (`decision_namespace_forgery`). Repo docs/ADRs may still quote the markers;
- class X1: any invocation, inspection, planning or dependency on the external auto-updater is denied before any other classification (`updater_dependency`). Detection is word-bounded over tool names, terminal commands/workdirs and path/URL arguments, so prose describing the boundary stays writable;
- A4 ordinary product/UX/brand risk is non-blocking: the call queues exactly one `a4_review_notice` event and proceeds; the owner may veto within the review window. A4 review never blocks execution.

`APPROVALS.md` remains the protected canonical escalation list; this section mirrors its wording for the classifier and cannot drift without a doc-sync PR.

## Finance and capabilities

A financial tool call must provide `amount_rub` and `capability_id`. Capabilities are one-time owner grants:

```bash
fleet-policy grant-capability <id> --project <slug> --kind <kind> --scope <scope> --by user
fleet-policy spend-status --project <slug>
```

Workers cannot grant capabilities or approve themselves, including through direct Python storage APIs. Spend is reserved before execution and settled/released from `post_tool_call`. Monetary API cost remains `unavailable` when the provider does not report it.

## Task budgets and progress guard

Task-type budgets cover generated tokens only, wall clock and tool calls. Prompt tokens are not repeatedly charged as work. Retry enforcement belongs to Hermes Kanban (`failure_limit` / per-task `max_retries`), because provider fallback errors are not task retries. Identical-call, same-failure and idle-turn guards use the shared SQLite state.

## Boards and project context

- `portfolio`: cross-project strategy, capital allocation, venture incubation;
- one dedicated board per registered product/venture with repo + owner + primary metric;
- `fleet-ops`: shared accounts, capabilities, providers and infrastructure;
- `general`: one-off work outside registered projects.

Each registered product gets a thin project skill that points to canonical repo rules and declares metric/gates. `scripts/register_project.py` scaffolds the board and skill. The plugin loads board-specific guidance from `config/fleet-policy.yaml`.

## Notifications

Routine work stays in Kanban. `company-daily-ops` sends one short daily owner digest. Serious approval/critical events enter the outbox; a no-agent five-minute notifier drains them to `company` Bot Chat. Denies caused by missing routine gates do not notify the user.

## Coverage and honest limits

Covered: normal Hermes tools routed through the built-in executor, including Tool Search unwrapping. `pre_tool_call` is fail-closed for state-changing paths and secret-bearing reads.

Known limits:

- this is a workflow policy boundary, not an OS sandbox; all local profiles run as the same Windows user;
- processes launched outside Hermes are not intercepted;
- `kanban_task_claimed` is observer-only, so invalid task metadata is stopped at the first tool call;
- existing sessions require restart after plugin updates;
- intentionally hostile obfuscated arbitrary code needs OS-account/container isolation.

## Release attestation

Release decisions are bound to a signed evidence artifact. `RELEASE-ATTESTATION.json` (schema `hermes-fleet-release-attestation/v1`) is built offline from an explicit evidence object — gates are copied verbatim and never inferred or defaulted — and re-checked fail-closed at verify time.

```bash
uv run --frozen fleet-policy build-release-attestation --input <evidence.json> --output <path>
uv run --frozen fleet-policy verify-release-attestation --input <path>
```

Canonical encoding: UTF-8 JSON, sorted keys, compact separators, exactly one trailing newline. `attestation_sha256` is the SHA-256 of the canonical object with that field omitted. Invariants: 40-hex commit/tree SHAs, 64-hex digests, `t_`+8-hex task IDs, UTC RFC3339-Z timestamps, `ci.head_sha == source.head_sha`, `ci.conclusion == success`, gates `ci`/`review`/`qa`/`rollback` all `status: pass` with unique identities and review/QA profiles independent of `company` and the implementation profile, `decision = company/go`, `deployment.expected_payload_sha256 == bundle.payload_sha256`, and `target_profiles` exactly the ten canonical profiles once each. Any violation, unknown field, or digest mismatch fails the build/verify with a non-zero exit and machine JSON. The output file is written atomically; nothing is written on failure. Both commands run without network or policy database access.

## Rollback

```bash
uv run python scripts/fleet_migration.py rollback --dry-run
uv run python scripts/fleet_migration.py rollback
```

Rollback verifies `snapshot.sha256`, restores owners/blocked states and the exact prior Kanban routing values, including nullable `max_in_progress`. Old cron jobs are never automatically re-enabled.
