# ADR-001: Capability and Human-Boundary Policy v2

- Status: Accepted
- Date: 2026-09-03
- Owner: tech
- Kanban: fleet-ops / t_e7e74526
- Decision evidence: `decision:company=go` (t_e7e74526 comment, 2026-09-03) and
  `decision:owner=approved` (owner confirmation in the active Hermes owner
  session, 2026-09-03, for the exact policy recorded here and its
  implementation/attested rollout after independent gates).

## Context

The fleet operates as an autonomous product company (`APPROVALS.md`,
`docs/FLEET_POLICY.md`). Experience showed two failure modes:

1. Over-escalation — routine actions with an active, owner-granted scoped
   capability (existing bot accounts, tokens, bot-controlled OTP channels,
   routine credential rotation) were treated as owner-waiting events.
2. Under-protection — the genuinely human/legal/financial/ultimate-ownership
   actions must stay fail-closed even when agents can otherwise act freely.

v1.2.5 already provides the enforcement substrate this ADR builds on and does
not re-decide:

- `approvals` table (`src/fleet_policy/storage.py`): columns
  `rule_key, task_id, action, target, args_hash, status, created_at,
  decided_at, consumed_at, decided_by, revoked_at, revoked_by`; unique binding
  index `(task_id, action, target, args_hash)`; statuses
  `pending/approved/rejected/revoked/consumed`; rows are immutable audit
  history (never deleted).
- Worker self-approval is refused at the storage layer when
  `HERMES_KANBAN_TASK` is set, and the CLI requires an interactive TTY plus
  the 8-character `rule_key` suffix (`src/fleet_policy/cli.py`).
- `notification_outbox` with bounded batched drain and atomic claims
  (`src/fleet_policy/storage.py`, notifier hardening PR #6) provides
  channel-resilient owner notification.
- `capabilities` and `financial_ledger` tables scope spend to owner-granted
  capabilities within the project mandate (≤10,000 RUB/transaction,
  ≤30,000 RUB/project/month, `APPROVALS.md`).

The company decision recorded here refines the classification boundary and the
owner-principal approval transport. This ADR is a decision record only: no
code, configuration, account, or live-system change is part of it.

## Decision

### 1. Policy matrix

Class A — autonomous (no owner involvement; evidence gates still apply where
`APPROVALS.md` names them):

| ID  | Action class | Condition for autonomy |
|-----|--------------|------------------------|
| A1  | Use of existing registered bot email/phone/service accounts, their tokens, and bot-controlled OTP channels | The capability scope is active (`capabilities` grant for the project, kind and scope match the call). |
| A2  | Creation of free accounts | No KYC, no payment obligation, no phone/domain/bank-owner obligation. |
| A3  | Routine login, OAuth flows, token rotation, least-privilege IAM changes | Owner break-glass/recovery material is untouched; change is reversible; no expansion beyond least privilege. |
| A4  | Ordinary product/UX/brand-risk changes | Non-blocking Telegram review notice with veto path is emitted; work continues during the veto window (section 4). |
| A5  | Spend inside the project mandate | Within ≤10,000 RUB/transaction and ≤30,000 RUB/project/month using an already granted scoped payment capability; `gate:finance=pass` + `decision:company=go` recorded. |

Class H — owner hard gate ONLY (exhaustive list; anything not listed here is
decided by the fleet):

| ID  | Hard-gated action class |
|-----|--------------------------|
| H1  | Spend above mandate, or any new paid obligation / payment instrument / payment rail. |
| H2  | Human-only OTP, KYC, or legal signature. |
| H3  | Transfer or removal of the ultimate owner, root access, break-glass or recovery material. |
| H4  | Mass unsolicited outreach. |
| H5  | Irreversible data loss. |
| H6  | Material security or privacy policy change. |
| H7  | Serious legal or reputational event. |

Class X — forbidden (never autonomous, never owner-approvable by the fleet):

| ID  | Prohibited action class |
|-----|--------------------------|
| X1  | Any fleet-agent invocation, inspection, planning, or dependency on the external Hermes auto-updater. |

Classification is fail-closed: an action that cannot be unambiguously placed
in A is treated as H (`approval_required`) by the policy classifier; an
unclassifiable call is denied (`src/fleet_policy/policy.py`).

Boundary pairs that decide close calls (test oracles for QA):

1. Existing scoped capability (A1) vs new paid/KYC/phone obligation (H1/H2):
   the trigger is the obligation, not the account. Reusing an active granted
   capability is A; any step that creates a new payment, KYC, phone, domain-
   owner or bank-owner obligation is H even for an otherwise registered
   account.
2. Bot-controlled OTP (A1) vs human-only OTP (H2): an OTP channel the bot
   already legitimately receives and consumes is A1; an OTP delivered only to
   the human owner's personal device/identity is H2.
3. Routine IAM (A3) vs removing the final owner/recovery (H3): rotation and
   least-privilege scoping of agent credentials is A3; any change that
   transfers, demotes, or locks out the ultimate owner, root, break-glass or
   recovery path is H3 — including changes framed as "cleanup".
4. Ordinary product risk (A4) vs serious legal/irreversible risk (H5–H7):
   reversible product/UX/brand choices are A4; legal commitment, regulated
   claims, material privacy/security change, irreversible loss, or material
   reputational exposure are H.
5. Within-budget spend (A5) vs over-limit spend (H1): the mandate limits are
   hard numeric thresholds per transaction and per project per calendar month;
   crossing either is H1 regardless of capability availability.

### 2. Owner principal

- Identity root: the existing configured Telegram owner user + direct-chat
  identity in the Hermes gateway configuration. Agents never create, modify,
  or re-point this mapping; changing it is itself an H3-class action.
- A nonce alone is not identity. Identity is established exclusively by the
  configured Telegram owner mapping; the nonce provides replay-safety only
  inside an already-authenticated principal channel.
- The owner principal is used ONLY for class H actions. Class A actions never
  request or wait for it (kill criterion: an active scoped capability must not
  trigger an owner request).
- Binding tuple for every hard-gated action:
  `(task_id, action, target, args_hash, amount_rub?, scope, nonce,
  expires_at)`. The approval card shows the exact action, amount, scope and
  expiry; approving binds exactly that tuple. Any change to action, target,
  amount or scope after approval invalidates the binding (`args_hash`
  mismatch) and a new hard-gate cycle is required.
- Replay-safety: one `pending` row per exact binding (unique index);
  consume-once transition `approved → consumed`; `expires_at` checked at
  consumption time (a granted but expired binding must be refused, surfaced as
  expired, and re-requested if still needed); `revoked` kills a granted or
  pending binding before consumption; concurrent decide races resolve to
  exactly one winner because decisions are a single conditional UPDATE from
  `pending`.
- Forged-input resistance: decisions enter only via the configured Telegram
  owner mapping or the interactive TTY CLI. Agent-produced text, LLM output,
  cron, pipes and non-TTY stdin cannot decide (storage-layer worker guard +
  CLI TTY + confirm suffix). Messages from any other user, any other chat, or
  any group context are not the principal and are refused.

### 3. State machine

Action lifecycle on every state-changing tool call:

```
request
  → classify (policy.py)
      ├─ A (autonomous)            → evidence gates OK? → execute → settle
      ├─ A4 (ordinary product risk)→ queue review notice (NON-blocking)
      │                               → execute → owner may veto later
      │                               → veto ⇒ compensating rollback task
      ├─ H (hard gate)             → ensure binding (pending)
      │                               → notify owner principal (Telegram)
      │                                   ├─ approve (exact binding, unexpired)
      │                                   │    → approved → execute ONCE → consumed
      │                                   ├─ reject  → rejected  (terminal)
      │                                   ├─ revoke  → revoked   (terminal)
      │                                   └─ expires → expired at consumption;
      │                                                re-request if still needed
      └─ unclassifiable            → deny (fail-closed)
```

Binding statuses: `pending → approved | rejected | revoked`;
`approved → consumed | revoked`; plus expiry enforced at consumption.
Terminal states (`rejected`, `consumed`, `revoked`, expired-and-refused) never
re-enter the lifecycle; every transition is an immutable audit row.

Failure/degradation semantics:

- Telegram outage blocks ONLY the specific hard-gated action whose approval is
  pending. Class A actions have no Telegram dependency and proceed; A4 review
  notices queue in `notification_outbox` and drain when the channel recovers
  (work continues, by definition non-blocking). Kill criterion: a Telegram
  outage must never halt unrelated work.
- Offline break-glass: the v1.2.5 interactive TTY CLI
  (`approve`/`reject`/`revoke`, `docs/OWNER_RUNBOOK_APPROVALS.md`) remains the
  fallback decision path while Telegram is unavailable. Owner break-glass and
  recovery always remain with the human owner (condition of A3).

### 4. Ordinary product/UX/brand risk path

Ordinary product, UX, or brand risk is NOT a hard gate. The fleet emits one
Telegram review notice (task, change summary, evidence, veto instruction),
continues work immediately, and records the notice event. If the owner vetoes
within the review window, the fleet opens a compensating rollback/revert task
with the same evidence-gate discipline as any reversible change. Absence of a
veto means the change stands. A review notice must never block execution
(kill criterion).

### 5. Audit fields

Existing row fields (kept): `rule_key, task_id, action, target, args_hash,
status, created_at, decided_at, consumed_at, decided_by, revoked_at,
revoked_by`.

v2 additions for hard-gate rows:

| Field | Content | Note |
|-------|---------|------|
| `nonce` | One-time random token of the binding | Replay-safety within the authenticated principal. |
| `expires_at` | Binding expiry timestamp | Enforced at consumption. |
| `principal_ref` | `sha256(owner_user_id \| direct_chat_id)` fingerprint | Identity proof without storing PII; the mapping itself lives only in the gateway configuration. |
| `channel` | `telegram` or `tty` | Which decision path was used. |
| `amount_rub` | Numeric amount or NULL | Never free text. |
| `scope` | Canonical scope digest (hash of the normalized scope string) | Binds approval to exact scope. |
| `notified_at` / outbox `event_id` | Notice linkage | Connects the approval card in `notification_outbox` to the binding. |

No secrets and no PII in audit rows: no tokens, passwords, usernames, or raw
contact identifiers; owner identity appears only as the fingerprint hash.

### 6. Auto-updater boundary (class X1)

Fleet agents never invoke, inspect, plan, or depend on the external Hermes
auto-updater. At ADR time this is verified by absence: no reference to the
updater exists under `src/`, `docs/`, `config/`, or `scripts/` of this
repository. Implementation must classify any updater-related call as
out-of-fleet-scope and deny it; appearance of any updater interaction is a
kill criterion for this policy version.

### 7. Alternatives considered

1. Keep v1.2.5 as-is (TTY-only approvals, coarse escalation list). Rejected:
   does not encode the autonomous classes A1–A3/A5 explicitly and leaves
   ordinary product risk undefined, reproducing over-escalation.
2. Human approval for every risk including ordinary product risk. Rejected:
   turns the owner into a routine dispatcher, violating the operating
   principle; veto-after-notice achieves the same protection non-blockingly
   for reversible choices.
3. A second, fleet-managed identity provider for approvals. Rejected: adds a
   new trust root the fleet could influence; the configured Telegram owner
   mapping plus TTY break-glass already form a minimal, owner-only identity
   surface.

## Evidence

- `src/fleet_policy/storage.py` @ fa39b66aa5ae789bbee19a95b36a4ea45691632b —
  approvals schema, unique binding index, worker self-approval guard,
  confirm-suffix check, consume-once and revoke transitions, immutable rows,
  notification outbox.
- `src/fleet_policy/cli.py` @ fa39b66 — TTY requirement for
  approve/reject/revoke.
- `src/fleet_policy/policy.py` @ fa39b66 — classification categories for the
  hard-gate classes and fail-closed default.
- `docs/FLEET_POLICY.md`, `docs/OWNER_RUNBOOK_APPROVALS.md`, `APPROVALS.md`
  @ fa39b66 — current mandate, gates, and owner runbook this ADR refines.
- `decision:company=go`, Kanban t_e7e74526 comment thread (2026-09-03).
- `decision:owner=approved`, owner confirmation in the active Hermes owner
  session (2026-09-03), scoped to this exact policy and its attested rollout
  after independent gates; explicitly NOT an approval for any future spend
  above mandate, paid obligation, KYC/signature, ultimate-ownership transfer,
  mass outreach, destructive action, or serious legal/security/privacy event.

## Consequences and rollback

Consequences:

- The implementation PR(s) must add the v2 route, the additional audit fields
  (nonce, expires_at, principal_ref, channel, amount_rub, scope, notice
  linkage), the A4 non-blocking notice path, and the X1 deny rule — then
  update `docs/FLEET_POLICY.md` and `APPROVALS.md` wording in the same PR so
  the canonical docs and the classifier cannot drift.
- Independent gates before rollout: `gate:review=pass` and
  `gate:security=pass` from QA threat-model task t_25908a44
  (classification boundaries and owner-principal attack suite), plus
  `gate:scope=pass` for this decision record.
- Kill criteria (any one reopens this decision): an agent can forge the owner
  principal; an ordinary product-risk review blocks execution; an active
  scoped capability unnecessarily requests the owner; a Telegram outage halts
  unrelated work; any updater interaction appears.

Rollback:

- This record is documentation-only; its rollback is a PR revert.
- For the future implementation: restore the prior attested policy/gateway
  payloads, disable the new approval route, and preserve existing capability
  records and immutable approval rows; the
  `scripts/fleet_migration.py rollback` path (validates `snapshot.sha256` and
  restores prior routing values) covers control-plane state. No account or
  product mutation is part of rollout, so nothing outside the policy payload
  needs reversal.
