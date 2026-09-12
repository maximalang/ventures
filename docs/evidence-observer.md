# Evidence observation: Batch 0.2

Base: `8fafc3713c44f7ab0046696cc45e81cca69cb597`, repository `maximalang/ventures`.
Normative source: Batch-0.2-Observe-Only-Spec.md and the scoped implementation request.

## Contract

The adapter calls the observer only after the original runtime post hook and
successful projection. Legacy exceptions are not intercepted. An independent
Exception boundary isolates observer failures. The observer has no permission,
budget, gate, lifecycle, execution, retry or receipt authority.

The existing runtime config dictionary accepts `evidence_observer_enabled: true`.
Only boolean true enables observation. Missing, false or string values leave it
disabled. No installed configuration is changed by this increment.

Only kanban_complete and kanban_request_review with submitted metadata.evidence_v1
are eligible. Missing evidence produces no event and no context lookup.

## Trust and coverage

Actor is hook profile_name, falling back to HERMES_PROFILE, never task assignee.
Target is invoked operation plus explicit task/board or dispatcher-pinned values.
Conflicting board/run locators are unavailable. A single read-only primary-key
lookup uses dispatcher-pinned HERMES_KANBAN_DB and run_id. Completed runs remain
resolvable without current_run_id. Unknown or mismatching runs are unavailable.
No sibling-board discovery or comment scans are performed.

CRITICAL COVERAGE GAP: the baseline has no independent full expectation issuer
for decision, subject, artifact and environment. Submitted run metadata and comment
author labels cannot supply it. Production resolution therefore reports
context_unavailable/null, including when actor/run identity matches. Validated
true/false tests inject separate trusted fixture snapshots; they do not demonstrate
that today's real flow can produce a full trusted expectation. No new issuer,
storage schema, authorization rule or public resolver API is introduced here.

## Diagnostics and bounds

Logger-only, schema hermes-evidence-observation/v1, version 0.2.0, mode
post_tool_metadata. Status is validated, context_unavailable or validator_error;
valid is respectively bool, null or null. No raw envelope, note, artifact path,
bytes, exception text or raw context is logged. Locators are restricted tokens.
Digest is recorded only from validator output, not as an authenticated claim.
Repeated observations are harmless log duplicates, not repeated tool executions.
Consumers must not count them as unique actions without invocation deduplication.

Snapshot traversal is capped at depth 16, 4096 nodes and a conservative 64 KiB
allocation budget. Bound violations yield validator_error/null, not policy deny.
SQLite uses mode=ro, zero lock wait and a 2000-VM-step interrupt. No network APIs,
artifact reads, file hashing, workers, cache, queue or PolicyStore writes are added.
The existing PolicyStore has a 10-second wait, so it is not used for diagnostics.
Only local dispatcher-pinned DB paths are supported; UNC paths are rejected.

Existing synchronous logging handlers and OS disk scheduling cannot offer a hard
wall-clock deadline. No handler is installed here. Before any future rollout,
verify that the real logging sink and DB are local and bounded. timing_ms measures
work before emission; adapter benchmark includes emission. The local fixture
benchmark is not a production latency guarantee.

## Verification and rollback

Run `uv run --frozen python -m pytest tests/test_evidence_observer.py -q -s`
and `uv run --frozen python -m pytest tests/ -q` in a full-history LF checkout.
Differential tests compare OFF/ON return/exception, arguments, runtime/project
calls, fixture store contents, budgets and gate results. Performance uses 300
samples; CPU samples amortize 100 observations for Windows clock granularity.
Adapter measurements stub legacy effects but include real SQLite lookup and logging.

Rollback: leave/remove the observer toggle or set boolean false. No data migration
or cleanup is needed. Source rollback reverts this increment, not Batch 0.1.
Independent QA, exact-head CI and merge evidence remain required. This increment
is not deployed, enabled in production or production-ready.
