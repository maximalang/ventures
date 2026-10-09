---
name: kanban-card-authoring
description: Use when authoring or recovering fleet Kanban tasks.
category: devops
---

# Kanban: executable contracts and bounded recovery

Kanban is task truth. One canonical executor and one testable deliverable per card. Project rules, the live tool schema and current Fleet Policy are authoritative. Historical recipes are diagnosis, never additional permissions. Keep routine skill loading small; use a focused reference only when the problem matches.

## 1. Authority and surfaces

- Lifecycle writes use the native tools actually exposed in this session. An unavailable native edit/archive/cancel/subscribe is a precise capability prerequisite, not permission for CLI, UI automation, imports, SQL or another session to perform it.
- Board is a hard worker boundary. Keep worker task/run/profile/board/storage pins intact; a delegated child is not an orchestrator. An assignee name or task/run CAS is not authenticated authority by itself.
- Company may perform bounded read-only CLI inventory in a child process with company-session board pins removed and an explicit board. Never remove pins inside a worker, use that route for writes, or change the global current-board selector.
- Read exact native task state before acting. CLI JSON normally wraps the row under `task` (show/list), but `create --json` returns a bare row with top-level `id` — parse each shape accordingly and assert its id/fields. DTOs may omit current_run_id, goal flag or overrides: absence is UNKNOWN, not proof that no run/flag/model exists. Use actual sorted runs, ended_at/outcome, authoritative events and natural-run evidence.
- Read-only CLI syntax traps: `--board` precedes the verb; list generally has no `--limit`; filter in code. Never infer deletion from a wrong-board unknown-id or a filtered session list. Discover allowed syntax instead of repeating failed arguments. Native show/list can return tens of KB and be stubbed out of context; for bounded field reads (status, parents/children, body marker line 1) prefer the read-only CLI `--json` parsed in a child process — on this host use `"$LOCALAPPDATA/hermes/bin/hermes.exe"` (the `hermes.cmd` launcher is broken); parents/children are top-level keys, the row is under `task`.
- Exact runtime source reads and task artifacts use read_file/search_files. Do not open real control-plane databases, auth/config secrets or dumps, even read-only. Use native show/list/export and approved metadata snapshots; secret values never belong in evidence.

## 2. Dispatch-ready contract

Classify BEFORE authoring (owner directive): if the work is simple, low-risk and company can execute and verify it in-session, do it directly — no card. A card exists only when the work genuinely needs an independent executor or gate (source/code changes, spend, publication, cross-profile rollout, multi-step verification). Routing trivial in-session work through cards and worker chains is the failure mode the owner explicitly rejected («ты можешь доделать всё сам, без канбан, карт»). Equally forbidden: answering a slowness complaint by editing instructions/skills instead of executing the task — meta-work is not progress; roll such an edit back.

Before dispatch company states: exact deliverable; measurable acceptance with SHA/counts/paths; explicit bans; anchor (exact base/head or target system and owner). If a material point cannot be retrieved, ask all independent owner questions in one form. Do not guess or create a card that cannot distinguish success from failure.

1. Check the relevant existing source, artifacts and live cards first; reuse verified work. Do not inventory the entire fleet for a narrow repair.
2. Body line 1 is one exact marker: research, code, review or ops. Pick the actual work type, never a cheaper envelope. Keep the body around 200 characters with a durable absolute Spec path.
3. Keep the terminal phase clear in the native title/body, especially for goal_mode: source delivery READY FOR RE-REVIEW is not independent QA or deployed acceptance. The current goal judge reads title/body and may not open the Spec file. Never hide truthful limits or write PASS merely to satisfy it.
4. The spec holds the full deliverable, immutable anchor, acceptance commands/evidence, constraints, permitted tools, executor, next owner, cost/kill/rollback. Every referenced file must really exist outside disposable scratch, or be an explicitly gated future producer artifact.
5. Size to one bounded worker run. Independent leaves may run in parallel in separate worktrees; never two writers of the same source/head/record. Preserve medium-batch evidence and source checkpoints, not a final-only handoff.
6. Use explicit board, real returned parent IDs and an idempotency key. Create QA with its producer parent from the start; prose 'wait for' does not gate dispatch. Attach required QA as a parent of its actual consumer.
7. A healthy parent is not replaced by a duplicate. A long-lived outcome tracker is not an executable prerequisite; use initiative linkage instead. A genuinely unmet owner/capability condition may start blocked, not ready followed by a race-prone park.
8. Set goal mode deliberately according to the real scope. Do not disable an existing judge to escape a refusal. Pin only installed target-profile skills; self-contained specs must not assume execute_code or other missing tools.
9. Read back the exact created body/marker, title, assignee, spec paths and parent graph. Inspect native auto-subscription separately; configured-off is intentional, not a transport incident.
10. An LLM coordinator spawn (`hermes chat --query-file … --format stream-json`) can exit 0 with an empty result and NO cards created — never trust the spawn exit code; verify creation with a board list/title search. Fallback that works: direct company-side CLI `hermes kanban create --body-file <path>` (a file body preserves newlines and flag-like lines through shell quoting; `--parent` gates a child to todo until the parent is done). Card body text is still lexically classified at creation: phrase bans with generalized words («защитные инфраструктурные литералы в аргументах команд запрещены») instead of enumerating the protected literals themselves, or the creation itself is falsely denied.

Post-dispatch material scope corrections go in the durable spec and a native comment too: an already-spawned worker may have an older body. Explicitly separate already verified/do-not-redo work from remaining acceptance. Scope changes preserve real controls and old negative artifacts.

## 3. Safety: no lexical evasion

A first policy denial ends that attempt: durable partial evidence plus the exact missing prerequisite, then stop. Do not retry the same meaning via a different spelling, quotation, path, environment variable, split command, generated script, string fragments, copied target, SHA alias or path-free Git plumbing. A script is a normal authoring mechanism, never an exemption from a denied action. Do not execute adversarial test strings; feed them only as fixture data to a pure evaluator.

Differentiate removing a genuinely unnecessary effect from hiding an unchanged effect. Classifier false positives are repaired against their exact recurrence corpus in a separate authorised source increment with true-positive/no-weakening tests and independent QA. No global worker permission widening. Marker, financial, protected-path and credential handling restrictions retain their gates.

References containing force completion, direct database lookup, wrapped policy CLI decisions, profile spoofing, path hiding, live config repins, polling aliases or mass unblocks are obsolete and must not be executed. Preserve the exact denial; don't sanitize away the diagnosis.

## 4. Recovery decision tree

- Refresh exact native task/runs/events/comments and preserved source/artifacts. Heartbeat is liveness, not progress. Notification text is a timestamped snapshot, not live state. Read source index/HEAD and durable receipts before deciding work was lost.
- Healthy progressing worker: do not duplicate, kill or restart it. A dependent TODO lane is not failed dispatch. Diagnose the blocked root, capacity and quota separately; never force the children ready.
- Transient timeout with partial work: re-scope the SAME card to known remaining tests/delivery using a material changed precondition and a finite budget. No reset-by-comment or blind repeated full battery. Verify writer ownership before resuming.
- Worker timeout/stale/terminal cleanup: direct launcher exit does not establish descendant termination. Bind host/task/run, ancestry/group and creation-time fingerprints; backup nonsecret dirty source outside canonical workspace too. If an owned descendant may live, retain the native fence and forbid a replacement. A one-off containment operation is not prevention; prevention must be wired into production spawn/reclaim and independently tested.
- Interrupted review setup: a destructive clone-directory cleanup denied before local checks is not an accepted review. Preserve partial evidence; recover the SAME card only after a persisted contract removes cleanup entirely and uses a unique non-existing clone path, with no deletion/reset/worktree removal. Bind GO to the exact head and existing body type. Native unblock may restore `review`, not `ready`; read back the lane and actual claim/spawn. Require newly executed checks and full reviewer/author lineage before any positive stamp; dispatch recovery is not QA success.
- Policy/owner/dependency holds: sticky until the real fact/capability changes. An unchanged denial cannot be repaired by transient/unblock to clear its lexical field. For a dependency hold establish the real parent, then verify gated TODO through an available native operation; do not invent an owner question for internal routing.
- Malformed body marker is an authoring defect, not a policy incident. No native body-edit exists, so never repair the marker through CLI/SQL or a re-scope comment: create the replacement card with the exact first-line marker, re-link the real parent graph under a fresh idempotency key, post the GO anchor on the NEW card (an anchor does not travel with a successor's title), and stand the old card down with a comment whose first line names the successor — comments ride in any spawned worker_context, so a stand-down note without a first-line marker still reads to a worker as live work.
- A repeated missing-gate-evidence denial on one card means the GO anchor binding is wrong or absent: no `head=<full SHA>` + type pair, a bare marker line without its binding, or the anchor posted on the producer instead of the consuming card. Repair the binding with a correctly formed anchor comment; re-unblocking or re-dispatching only replays the same denial.
- Quota: count real rate_limited outcomes, not heartbeats. Park a storm natively with durable partial evidence; no infinite cooldown respawn or invented reset time. A canonical per-card backup may be used only with verified failure and existing scoped routing authority, and only after a zero-token liveness check of the backup rail plus its fallback chain — a backup pinned onto another walled rail merely converts one quota wait into another (`fleet-model-probing` → multi-rail wall cascade). Preserve the canonical intake, bind backup evidence as a real parent and attribute every test to its actual issuer. Global pools/model/profile changes require their own explicit scope.
- Already delivered: verify the immutable artifact and exact phase acceptance, then ONE permitted native finalization, with no live-claim takeover. Source-only closure does not issue QA/live gates. On reachable judge refusal preserve the original card/evidence and its gated children; don't repeat phrasing, use --force, archive as success or move through another surface. Missing editor/phase contract is an interface defect, routed as source + independent QA.
- Triage/budget/anti-loop terminal: no automatic promotion, forced supersession or repeated denied action. Native specify is only for a legitimately re-scoped triage card, preserving the marker; omitted fields must survive. Read back before dispatch. A native operation not exposed is a blocker, not a reason to use an LLM CLI specifier.
- Judge transport failure: inspect current disposition and any canonical review fallback; behavior is version-dependent. No transport failure, orphan verifier or archived parent counts as acceptance. A cancellation/supersession is different from a successful deliverable.
- Before any permitted archive/supersession, salvage durable artifacts and inspect every descendant: terminal parents can release stale deployment children. Bind canonical replacement prerequisites first and verify exact native readback. No bulk complete/archive/unblock.
- Complete enforces parent-first ordering: a leaf-first supersede cascade is refused (`unsatisfied parent dependencies`), and completing a parent promotes its todo children toward ready. Retire a dead line by posting RETIRED/stand-down comments on EVERY card first (they ride in any spawned worker_context), then completing top-down. A blocked goal_mode root cannot be admin-completed — the goal judge rejects a SUPERSEDED summary as goal-not-achieved; do not fight or rephrase it. A line frozen behind a blocked root cannot dispatch, so the comments carry the retirement.

## 5. Independent acceptance and gates

Evidence means actual results against acceptance, not a path/hash or author's statement. Separate local, CI, immutable source and live/deployed head. A done card may carry BLOCK or WITHHELD; consumers must inspect typed verdicts, not only status.

- Acceptance artifacts not yet copied to the durable program path sit in the card's workspace dir (`%LOCALAPPDATA%/hermes/kanban/workspaces/<task_id>/`, e.g. `VERDICT-*.md`): grep there before declaring a deliverable missing — a `done` QA card whose verdict exists only in its workspace is a location fact, not an absent gate.

- The author cannot accept own material work. CI: tech/qa; review and QA: qa; rollback: tech/operations; backup: operations; scope: qa/operations; finance: finance. Company owns the go/no-go decision, not specialists' gates.
- Exact serving lineage is natural-run evidence, not configured model/profile names. Use ordinary session-bound API stamps/approved native usage snapshots, including actually executed fallback/auxiliary/vision/compression (recipe: `fleet-model-probing` → serving-lineage attestation — run metadata `worker_session_id` → profile agent.log stamp lines → durable file + SHA commented on the reviewer's card). When a reviewer withholds for missing lineage, company supplies that attestation; do not re-dispatch the reviewer without it. Missing fields are UNKNOWN, not zeros. Compare full author/brain and reviewer chains symmetrically; an overlap is correlated, not independent. Do not read raw state stores or modify another profile/config to obtain a positive result.
- QA self-markers do not arm its own review/QA gate. QA's own card returns a word-form source verdict and evidence. Binding markers are issued by authorised specialists on the SAME BOARD's consumer card (assignee not that reviewer), not copied or impersonated by company.
- Each marker is standalone: exact marker line, then `head=<full SHA> task_type: <consumer type>`. Evidence prose is separate. The company GO anchor uses that exact head/type on the consuming card. An unbound marker is not evidence; colon versus equals matters. Never change marker order/author/spelling to evade a deny.
- Main/merge requires CI/review/rollback; deploy adds QA/backup; publication review/QA; destructive cleanup backup/scope; spend finance/company/scoped payment capability and budget. No GO until actual exact-head evidence exists. Changed head invalidates prior bindings; only the independent reviewer can qualify unchanged prior evidence.
- Preserve all old negative verdicts and genuine controls. Baseline/harness failures are attributed by identical environment and programmatic nodeid set comparison, not deleted. A toy helper simulation doesn't prove runtime wiring.
- Source changes remain in their own branch/patch until sanctioned integration, final exact-head layer QA and rollout gates. Do not run updater/doctor/restart or change installed overlay during diagnosis.

## 6. Results and handoff

Attach genuine files durably before scratch cleanup. After external writes read back exact target/parent graph/comments/attachments/receipt before claiming success. Do not repeatedly verify an internal edit already confirmed by the write tool; hash only where evidence requires it.

Selected task delivery is explicit; auto-subscription may intentionally be off. Do not bulk-subscribe or add a second wake controller. Verify exact board/topic and platform receipt; advancing a cursor is a claim, not send ACK. Read failure is degraded, not empty. Ambiguous delivery must not replay blindly. Owner summary route follows fleet-notification-ops, not old incident topic numbers. Pending journal entry is not delivered.

Handoff: actual terminal phase/verdict, immutable evidence/artifact refs, important limits, next owner/action and condition/check_at. Owner chat is short and human-readable; internal IDs/JSON/gate mechanics stay in Kanban. Every financial statement has scope/period/source: confirmed revenue, refunds, incremental paid costs, commitments and estimated usage separately; unknown is null with a reason, not 0.

## Focused references

Load only when matching; they may contain historical recipes that do not override the safety/authority rules above:
- references/backlog-triage.md
- references/policy-block-retry-contracts.md
- references/policy-deny-diagnosis.md
- references/policy-recovery-recipes.md
- references/program-orchestration.md
- references/policy-package-delivery.md
- references/fleet-policy-deploy-ops.md
