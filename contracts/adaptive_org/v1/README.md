# Adaptive organization contracts v1

These Draft 2020-12 JSON Schemas describe product, agent, bet, and agent-change declarations. They do not authorize an action, create a Hermes profile, schedule work, or replace Projects/Kanban. Authorization and attestations stay in the existing fleet-policy and canonical evidence lane.

## Contract invariants

- IDs are stable and machine-safe; `agent_id` is `<product-slug>--<role>--<purpose>` and must start with the exact `product_id`.
- Timestamps are UTC ISO 8601 with `Z`.
- Monetary values are `{ "minor_units": <integer>, "currency": "<ISO-421 3-letter code>" }`; `unit` is `minor_units`. Decision on sign (v1): negative `minor_units` are ALLOWED — they encode deltas/refunds; a cost cap or spend total must be non-negative, and finance (AO-02) owns that per-field rule in kill rules/reviews. Note: JSON Schema 2020-12 `"type": "integer"` also accepts zero-fraction numbers (e.g. `10.0`); consumers must normalize to `int` before arithmetic.
- An unknown metric is `value: null`, `unit: null`, a non-empty `unknown_reason`, and `evidence_ref: null`. Unknown is never zero.
- Source/evidence fields are references into existing canonical records, not embedded attestations.
- Agent manifests cannot contain secrets or authorize recursive spawning. `can_spawn_agents` is optional only because its sole valid/default value is `false`.
- `requested_transition.dry_run` defaults to `true`; consumers must treat omission as true. Schema defaults annotate and do not mutate an instance.
- One active bet per product, revision freshness, idempotency conflicts, and unknown-outcome reconciliation are collection/state invariants enforced by `validator.py`. Precedence in `validate_agent_change` (fail-closed): changed payload under a reused key → `idempotency_conflict`; `prior_outcome == "unknown"` → `reconcile_required` even for a byte-identical retry; `"replay"` is returned only for an identical payload with a known prior outcome.

## Executable check

```bash
uv run --frozen pytest tests/test_adaptive_org_contracts.py
```

`validator.py` uses `jsonschema.Draft202012Validator` with a `referencing.Registry` (the supported replacement for the deprecated `jsonschema.RefResolver`) plus semantic checks that JSON Schema cannot express across documents or against current state.
