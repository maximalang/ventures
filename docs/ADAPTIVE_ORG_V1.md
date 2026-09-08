# Adaptive Organization v1 — scope and evidence matrix

Status: proposed contract/docs change only. Kanban and registered Hermes Projects remain operational truth; these JSON declarations are not a scheduler, approval, attestation, or capability grant.

| Concern | Accountable owner | v1 output | Independent evidence / stop rule |
|---|---|---|---|
| Product/job/outcome | `product` | `product_manifest/v1`, one falsifiable `bet/v1` | `research` supplies cited demand/problem evidence. Mark `NEEDS-EVIDENCE` when source refs are absent or stale. |
| Contract implementation | `product` | Schemas, fixtures, semantic validator, canon proposal | `qa` reruns positive/negative fixtures at exact SHA and adversarially checks unknowns, identities, transitions, revision and idempotency behavior. Author does not accept own work. |
| Economics and budget | `finance` | Reviewed `financial_metrics`, `budget_ref`, `cost_cap_ref` | `finance` verifies integer minor units + ISO currency, cost assumptions, spend ledger and mandate. Missing economics is unknown, not zero; no spending follows from JSON. |
| Agent capability and delivery | `tech` | Feasibility review of manifest/tool/eval/model references | Stop if a manifest implies unsupported behavior, recursive spawning, a second scheduler, or bypass of fleet-policy. |
| Operational state change | `operations` | Later plan/apply/verify/pause/retire runbook | Existing backup, rollback, scope and policy gates remain mandatory. Dry-run is the default; unknown outcome requires reconcile before retry. |
| Portfolio/capital decision | `company` | GO/NO-GO decision reference and accountable lead | One active bet per product. Stop or revert on kill criterion, unresolved safety defect, stale authority, or budget/scope failure. |

## Product experiment contract

Hypothesis: explicit product and agent boundaries reduce duplicated setup and wrong-product work. Confidence: medium.

Test: independently validate these fixtures, then use one declaration set in a sandbox-only product loop. Do not create live profiles in this task.

Metric: validation/recovery/setup defects attributable to missing or ambiguous product/agent context. Baseline is `unknown` until measured with a cited observation. Secondary metric: elapsed onboarding work for a later second product, also `unknown` until observed.

Stop rule: any required expanded privilege, competing authorization/evidence store, second scheduler, unresolved safety defect, or scope/budget failure. Rollback: discard/revert this scoped branch; no live state exists to unwind.

## Provenance rule

Every state or metric claim carries `source_refs`/`evidence_ref` and an UTC `observed_at`; `next_review_at` bounds staleness. A missing observation is encoded as `null` plus `unknown_reason`, never as zero or an invented estimate. `STATE.md` is a human-readable projection; Kanban, repo decisions, and cited measurement records remain its provenance.
