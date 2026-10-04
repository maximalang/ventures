# PR266 primary QA recovery — source acceptance only

Company contract, 03.10.2026. Canonical card t_caf6e99f, board rr-team, owner qa. SAME-ID continuation of interrupted review run 1054; not a duplicate implementation or a waiver. Original implementation is delivered: do not edit it.

## Deliverable and exact anchor
One independent source-acceptance verdict with newly executed local checks and persisted evidence for https://github.com/maximalang/recruiter-radar/pull/266.
HEAD ec77dadf72ed9ada28f1bd092587ab731b3b22f0; BASE/main observed 1d7906ae45f9570d4c37d9f73fc6bd5100246f65; branch codex/npm-audit-baseline-green.
Known diff: 8 files (two manifests, root lockfile, pending-auth-action view, its tests, two auth e2e harnesses, landing verification script).
Primary reviewer qa uses its existing sanctioned routing. A second different-model verdict is still required before protected merge; this run does not supply both verdicts.

## Root cause and changed precondition
Run 1054 was stopped before its own local tests by a destructive shell cleanup of a clone directory that had not been created. Useful static/remote observations survive, but do not complete acceptance. The procedure now has NO cleanup: create a NEW unique clone directory, retain it, and delete nothing. Do not repeat the denied command or reproduce it through another tool. Any new deny => stop, retain evidence and report the exact failed call; no self-unblock.

## Acceptance with measurable evidence
1. Before review and before verdict, re-read PR266 and main: exact head/base must match the anchor. Identity drift => WITHHOLD with the observed identity, not review another artifact. In your own clone verify HEAD, base ancestry and clean status before running tests.
2. Cold-read every changed hunk and lockfile semantics. Check axios override 1.20.0; Nodemailer 10.0.13/Node>=20; Next 16.3.8 compatibility; fail-closed pending-auth replay; TLS certificate verification and negative controls. No waived tests or weakened assertions.
3. Independently run npm ci; npm audit --omit=dev at high and moderate levels; full npm audit. Require exit 0 and zero JSON vulnerability counts. Verify materialized package versions against lockfile.
4. Run npm run web:check, npm run web:build, the repository's actual DB-adapter parity script (read package.json for its exact command), full apps/web Jest, focused pending-auth StrictMode tests and a mail-transport smoke with NO outbound mail. Persist commands, exit codes, test/suite counts. Producer baseline is 453 passed suites/16 DB-dependent skipped; 3650 passed tests/90 skipped. Explain discrepancies. Local service exclusions require explicit exact-head CI coverage; never connect to production.
5. Re-read exact-head CI with programmatic pagination/count. Latest company readback: 38 SUCCESS, no pending/failure. All auth/e2e, tenancy, migration, audit/security, OAuth, commercial-contract, build and landing lanes must remain green. Historical green on another SHA is not evidence.
6. Before any positive verdict, attest actual serving/fallback/vision/aux/compression lineage against the author chain. Author session 20261002_233439_c1e57f, tech: 81 serving calls on custom/qwen3.8-max, no aux/compression rows. Persisted sanctioned evidence: C:/Users/max/Desktop/all/ventures/docs/rr-ai/PR266-ec77dadf-AUTHOR-LINEAGE.json. Use ONLY C:/Users/max/Desktop/all/ventures/scripts/lineage_readback.py with your real worker_session_id, --profile qa --hermes-home C:/Users/max/AppData/Local/hermes --json. Do not query raw state.db/kanban.db, private session stores or logs. Any intersecting model or missing lineage => WITHHOLD, name the missing attestation, no positive gate.
7. Persist report, raw logs/count JSON and own lineage JSON in a durable evidence directory or native task attachments. Record git status after checks and any generated deviations without cleaning. Native handoff includes exact head, evidence paths/hashes, executed checks/results, actual reviewer chain and one disposition: APPROVE FOR MERGE, concrete BLOCK or withheld acceptance with dependency.

## Workspace and prohibitions
Use a NEW path under the native task workspace: review-pr266-<real-run-id>-<unique-suffix>. Check non-existence before clone; collision means choose a new suffix. Do not reuse/touch C:/tmp/rr-audit-green or other workers' trees. Probes/logs stay outside the reviewed clone. NO file/directory deletion, reset --hard, worktree removal/prune, force-push, implementation edits, security/CI-policy changes, main push/merge, deploy, spend, outbound messages, new capabilities, or reads of .env*, auth/secrets/dumps. Preserve every producer artifact and telemetry/worktree.

## Handoff and unfinished release acceptance
This run closes ONLY source acceptance. Original 'four lanes green on main' acceptance is NOT yet achieved and must not be claimed. Carry it as disposition_ref=t_edc2b4b9 (existing merge-train consumer) after independent dual verdict and normal CI/review/rollback gates. Production is read-only. Do not issue main/deploy gates or company decisions. If a native terminal transition is refused, persist the verified verdict once via kanban_comment and hand it to company; no repeated completion or replacement.

## Value, cost and stop
Hypothesis: accepting the existing dependency/security increment removes baseline security-CI blockers in the P0 feature train. Confidence high for dependency relation, not a QA verdict. No purchase/new commitment/external paid capability is authorized. Kill: head/base drift, reproducible regression, nonzero audit, unknown/intersecting lineage or any new policy deny. Rollback of coordination = park this review; no product bytes changed.
Financial scope: RR watchdog + this source-QA recovery, 03.10.2026. confirmed_revenue=null, refunds=null (not measured); incremental_paid_costs_rub=0, new_commitments_rub=0 (no payment/contract operations); estimated_usage_cost_rub=null (no reconciled cost record). Sources: native coordination operations, live GitHub readback, sanctioned model-usage lineage. This is not a project finance report.
