# Outcome loop

Use this reference for one active product bet. Kanban remains the source of truth; this template does not create a second tracker or a new schema.

## Minimal Outcome block

```text
hypothesis: <falsifiable claim>
user_segment: <who>
value: <measurable user/business value>
experiment: <smallest lawful test>
success_condition: <threshold + source>
stop_condition: <threshold/fence>
observation_window: <start/end or duration>
baseline:
  value: <value|null>
  source_ref: <path/URL/task>
  observed_at: <UTC ISO8601|null>
actual:
  value: <value|null>
  source_ref: <path/URL/task>
  observed_at: <UTC ISO8601|null>
financial_scope:
  currency: RUB
  period: <start/end>
  confirmed_revenue_minor: <integer|null + reason>
  refunds_minor: <integer|null + reason>
  incremental_paid_costs_minor: <integer|null + reason>
  new_commitments_minor: <integer|null + reason>
  estimated_usage_cost_minor: <integer|null + reason>
  source_ref: <receipt/ledger/task|null + reason>
decision: <GO|NO-GO|NEEDS_EVIDENCE|ITERATE>
next_task:
  board: <board>
  id: <task id>
  owner: <profile>
  check_at: <UTC ISO8601>
```

Money uses integer minor units plus currency. Keep confirmed revenue, refunds, incremental paid costs, new commitments and estimated usage cost separate. Unknown is `null` with a reason, never `0`; forecast is never summed with fact. No new commitments does not mean the work was free.

## Native phase handoff

Complete a phase with the native lifecycle tool and compact metadata:

```json
{
  "outcome_ref": {"board": "<board>", "task_id": "<initiative task>"},
  "phase_result": "<verified result>",
  "evidence_refs": ["<URL/SHA/path/task>"],
  "observation_status": "<observed|waiting|blocked|unknown>",
  "next_action": "<one measurable action>",
  "next_owner": "<profile>",
  "check_at": "<UTC ISO8601>"
}
```

During work, use one compact comment with the same facts. Comments and JSON do not control scheduling: dependencies must be native parent edges. If independent QA fails, route the exact defect back to the original phase owner; do not advance, self-accept, or create a duplicate lane.

## Cadence decisions

Daily output must be exactly one of:
- **ACTION** — one permitted action executed and its exact target read back;
- **WAIT** — only with a future `check_at` and wake condition;
- **BLOCKED** — exact cause, evidence and owner for removal.

For a native company-cycle BLOCKED receipt, preserve the complete native `blocked_reason` or `last_failure_error` verbatim inside `blocked.reason`. The native consumer requires the entire actual cause to occur in the receipt, not merely a matching excerpt or a paraphrase. Keep the readable diagnosis separate; do not expose raw bootstrap/config warnings in the owner digest, and do not mistake them for a request for credentials or spending. If both current native cause fields are null, a historical blocked-event payload is not a substitute accepted by this consumer: keep an honest HOLD rather than inventing a cause or changing task lifecycle to manufacture acceptance.

When verifying an owner-inbox push, compare the blank-line-normalized payload with `full_lines` when present, otherwise `lines`, and verify its `sig`. The existing inbox may cap only the render version while retaining the full report; a mismatch against capped `lines` alone is not a failed push. Journal ACK never attests Telegram delivery.

Do not touch a healthy running task. Expired `check_at` triggers reassessment, not repetition. After two consecutive cycles without new evidence or movement, reduce scope, change to another permitted method, stop, or assign one concrete cause-removal task. Never bypass a deny.

Weekly: compare forecast with actual; separate product outcome, money, learning and task movement; choose continue/iterate/kill; record exactly one next measurable task and verify owner, status and prerequisites. `NO-GO` is valid learning, not revenue. Unknown demand is not absence of demand.

## Dependency safety

The author completes the phase deliverable and releases any pre-created review child. Do not keep implementation open until revenue. Do not make an executable next-step card a child of an unfinished outcome/initiative card: that deadlocks the scheduler. Link it to the initiative through `outcome_ref`; use parent edges only for real prerequisites.
