---
name: fleet-workflow-efficiency
description: "Use when designing or auditing autonomous fleet task routing, parallelism, policy resilience, and token efficiency. Apply one canonical dispatcher with bounded lanes and evidence-first handoffs."
version: 1.0.0
---

# Fleet workflow efficiency

## Canonical operating model

- Keep one dispatcher owner per board/database; never add a second control loop to compensate for a stuck queue.
- Separate deterministic dispatch ticks, strategic model decisions, recovery reconciliation and result delivery before calling polling a defect. Compare one native event-wake plus reconciliation path with the existing scheduler before adding a workflow engine.
- Check a repair's completion contract against its real repository/PR before dispatch. Reject literal documentation placeholders early; repair through a native compare-and-swap interface without downgrading CI or impersonating the worker. A missing native edit capability is an interface defect, not permission for CLI/SQL surgery.
- Treat `ready` as spawnable only when the assignee resolves to an installed profile and the task has a valid lifecycle contract.
- Keep one canonical task and one active run per deliverable. Dependencies, not chat messages, control ordering.
- Never bulk-complete/archive a baseline classification as if it were verified delivery. Closing or archiving a parent can immediately spawn obsolete deployment children, including downgrades. Before each native transition, refresh exact state, verify artifact and descendants, and establish canonical supersession/containment. Do not use force to displace a live claim or archive to bypass incomplete parents.
- Test staged maintenance packages adversarially before installation: a live lock must not be stolen on age alone; rollback must not treat newly-dirty tracked files as newly-created files; manifests/backups must exclude secret-bearing paths before opening them. Passing a toy supervisor simulation is not proof that the production scheduler has recovery wired.
- Prove worker-tree termination, not just launcher-PID exit. If a retired owned descendant survives a timeout or termination failed, preserve the claim/fence and do not spawn a successor beside it. Bind cleanup to native task/run, executable/argument identity, ancestry and creation-time fingerprint; back up nonsecret source/evidence before scoped operations containment. Cleanup is not scheduler prevention.
- Give board-fenced reviewers a provenance-labelled, owner-exported native read snapshot when cross-board evidence is required. An unknown-id result under a pinned board is not deletion evidence; never replace it with direct SQLite access or environment stripping.
- Run independent leaf tasks in parallel; run dependent work only after accepted completion. Reserve capacity for review/QA so implementation cannot starve verification.

## Policy-resilient routing

- Use the worker's actual tool schema as the source of truth; do not ask a worker to call a tool excluded from its profile.
- A policy denial is a terminal classification for that attempt, not a retry reason. Record the exact denied capability and route to an allowed equivalent or a scoped blocker.
- Do not widen worker permissions globally to cure a task-specific denial. Change the task contract or assign the task to the profile that legitimately owns the capability.
- Normalize assignees against the installed roster before creating or promoting tasks. Unknown names must fall back to a verified configured profile, never remain in `ready`.

## Parallelism and economics

- Bound three levels: host global in-progress, per-profile in-progress, and per-tick spawn budget. Use the smallest cap that preserves progress; memory pressure may reduce it further.
- Keep review/QA capacity reserved. Do not fan out subtasks that write the same file, repository head, or external record.
- Size source deadlines from observed successful natural model round-trip and test durations, not a convenient short constant. A 20-minute ceiling can terminate an honest multi-call implementation before checkpoint; budget calls and time together, reduce remaining scope from preserved evidence and never extend a live claim through a hidden writer. If timeout ownership is unsafe, quarantine only affected canonical cards and contain verified retired writers before resuming; do not fan out more implementation duplicates.
- When an expected flat artifact is missing, inspect native task attachments and the exact nested producer workspace before declaring evidence lost. Mirror proven ordinary reports and actual partial source to the durable acceptance paths with byte hashes; a copied backup manifest is not proof that every backup byte was also copied, and an ops DONE is not implementation/prevention QA.
- Prefer short leaf tasks with one artifact and one acceptance contract. Avoid broad exploratory prompts, repeated full-context retries, and status-only heartbeats.
- Retry only transient infrastructure or worker crashes, with an error fingerprint and a finite budget. Never retry owner, safety, policy, dependency, or quota blockers blindly.
- Contain a quota storm with native parking and durable partial evidence before adding an already-sanctioned per-card QA-backup evidence run. Keep one canonical acceptance intake, bind its backup as a real parent, preserve all negative controls and attribute each test to its actual issuer. Never change global pools/profile pins or treat a model override as proof of serving identity.
- When native dependency blocking has no incomplete parent it becomes a sticky needs-input hold. Establish the real dependency and verify TODO before leaving; if a running child cannot accept a new edge, park it natively as transient, add the parent, then unblock into parent-gated TODO. No owner answer is required for internal routing, and no status or native-kind readback may be assumed.
- Native CLI task DTOs can omit current_run_id. Use sorted actual run records and ended/outcome fields for active-run evidence; absent DTO fields do not mean no run. Preserve the declared-count invariant in collected snapshots.

## Completion evidence

- Keep a goal-mode card's measurable terminal phase explicit in its native title/body, not only in an external Spec path: the current completion judge reads title/body and can confuse source delivery with downstream QA/live acceptance. Do not hide failed/unknown gates to satisfy it. After one refusal preserve the original task and repair the legitimately missing authoring interface; no alternative CLI/DB completion or repeat phrasing.
- A worker terminal handoff contains terminal status, evidence/artifact references, and one next action.
- A heartbeat proves liveness only; it never proves completion.
- Treat advancing a delivery cursor as a claim, not a durable send acknowledgment. Verify crash-between-claim-and-send recovery, preserve pending cursor when moving a subscription, and bind platform receipt to the exact task/event/route. Read failures must be marked degraded, not silently converted to an empty inventory.
- Preserve reproducers and execution evidence outside disposable worker workspaces or attach them natively. A durable report with references to deleted scratch scripts is not a reproducible handoff.
- A dispatcher tick is successful only when it either advances work, records a durable terminal disposition, or emits a precise actionable blocker.
- Verify the exact artifact/run state before claiming success; distinguish local, CI, runtime, and production evidence.
- Inspect the native creation receipt and the allowlisted auto-subscription setting separately. `subscribed:false` with configured-off is not a context-loss or transport-loss incident; a correct existing route does not prove that a newly created task has a subscription. Never turn on mass subscriptions to compensate for a missing selected-task delivery primitive.
- Validate exact source head/base against the real native handoff and remote ref before writing an acceptance spec. Never expand a remembered SHA prefix or infer a worktree path; producer test counts remain claims until independent review.
