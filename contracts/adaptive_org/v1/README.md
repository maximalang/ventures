# Adaptive organization contracts v1

These Draft 2020-12 JSON Schemas describe product, agent, bet, and agent-change declarations. They do not authorize an action, create a Hermes profile, schedule work, or replace Projects/Kanban. Authorization and attestations stay in the existing fleet-policy and canonical evidence lane.

## Contract invariants

- IDs are stable and machine-safe; `agent_id` is `<product-slug>--<role>--<purpose>` and must start with the exact `product_id`.
- Timestamps are UTC ISO 8601 with `Z`.
- Monetary values are `{ "minor_units": <integer>, "currency": "<ISO-421 3-letter code>" }`; `unit` is `minor_units`.
- An unknown metric is `value: null`, `unit: null`, a non-empty `unknown_reason`, and `evidence_ref: null`. Unknown is never zero.
- Source/evidence fields are references into existing canonical records, not embedded attestations.
- Agent manifests cannot contain secrets or authorize recursive spawning. `can_spawn_agents` is optional only because its sole valid/default value is `false`.
- `requested_transition.dry_run` defaults to `true`; consumers must treat omission as true. Schema defaults annotate and do not mutate an instance.
- One active bet per product, revision freshness, idempotency conflicts, and unknown-outcome reconciliation are collection/state invariants enforced by `validator.py`.

## Executable check

```bash
uv run --frozen pytest tests/test_adaptive_org_contracts.py
```

`validator.py` uses `jsonschema.Draft202012Validator` plus semantic checks that JSON Schema cannot express across documents or against current state.
