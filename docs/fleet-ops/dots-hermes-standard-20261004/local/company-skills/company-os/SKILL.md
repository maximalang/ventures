---
name: company-os
description: "Use for portfolio, fleet-ops, and autonomous company work."
---

# Autonomous Company Operating Skill

Read the canonical `AGENTS.md`, `PORTFOLIO.md`, `OPERATING_SYSTEM.md`, and `APPROVALS.md` under `C:/Users/max/Desktop/all/ventures`.

## Org model (owner directive 16.09.2026)

Canonical file: `C:/Users/max/Desktop/all/ventures/ORG_MODEL.md`. Two board types only: functional DEPARTMENTS (one agent collective serving ALL products — `video`, `freelance`) and PRODUCT boards (`recruiter-radar`/`rr-team`, `seo-site`). Routing rule: a task goes to the board of WHO does the work, not which product it is for (all video work for every product → `video`; marketplace orders → `freelance`). Cross-cutting task: execution on the department board, product acceptance as a linked card on the product board — never duplicate execution. Departments staff SPECIALIST profiles, not generalists: video = `video-director` (gpt-5.6-sol, playbook video-direction) → `video-editor` (glm-5.3-flash, playbook video-editing-craft) → independent `qa` gate; freelance = tech/qa/research until a specialist trigger fires. New agents and new departments are created BY THE FLEET ON DEMAND (triggers/procedure/rollback in ORG_MODEL.md §«Протокол создания агентов и отделов»): steady defect/workflow/new-project/overload trigger → evidence card → profile create --clone-from → SOUL.md → skills → roster update → trial run; role that fails to beat the generalist in 2 cycles gets deleted. Never pre-create idle profiles/boards. WIP limit: ≤5 parallel workers, one active bet per department/product. Owner directive: everything must stay quality and simple — no org sprawl, no third board type without owner decision.

## Decision protocol

1. Orient from the board, project metric, latest evidence, and budget.
2. `company` names one accountable owner and the smallest 2–5 role squad.
3. For material decisions record: hypothesis, expected profit/metric effect, confidence, cost, kill criterion, rollback.
4. Gather independent evidence: `research` for demand, `finance` for economics, `qa` for verification, `tech/operations` for delivery risk.
5. `company` decides and posts `decision:company=go` or a reasoned NO-GO. Routine decisions do not go to the user.
6. Execute autonomously, including main merge, deploy, publishing, and paid experiments after the required role gates.
7. Escalate only the serious classes in `APPROVALS.md`.

## Board taxonomy

- `portfolio`: cross-project strategy, capital allocation, GO/NO-GO, incubation.
- one board per registered product/venture with repo + owner + metric.
- `fleet-ops`: shared accounts, capabilities, models, credentials, fleet infrastructure.
- `general`: one-off work not belonging to a registered project.

## Simple result loop

Use the compact Outcome, money and handoff templates in `references/outcome-loop.md`; Kanban remains the source of truth and no parallel bet schema is introduced.

Use one closed loop per active product:

1. Observe the registered primary metric and current evidence.
2. Select exactly one smallest reversible bet with expected impact and kill criterion.
3. Execute with one accountable owner; add specialists only for material demand, economics, delivery-risk, or QA evidence.
4. Independently verify the exact artifact/head.
5. Ship after the required boundary gates; do not gate ordinary reads or analysis.
6. Observe the metric over the declared horizon.
7. Company records continue/kill/iterate and creates exactly one next measurable action.

Daily completion is one verified ACTION, bounded WAIT or justified BLOCKED state — not a status-only report.

Keep portfolio WIP at no more than five workers and one active bet per product. Machine state belongs in structured task metadata and dependency edges, never inferred from prose comments. Do not add a permanent subsystem until a live failure proves it is needed.

The fleet may claim end-to-end autonomy only after: a clean seven-day shadow soak, one live research-to-QA-to-company chain, external restart/recovery proof, and one real outcome loop completed without owner intervention outside serious escalation classes. Stop and repair the control plane if policy/tool failures consume over 30% of task attempts or if three consecutive decisions contradict later evidence.

## Adaptive product organization

For organizational design, portfolio expansion, dedicated product agents or external operational pipelines, read `references/adaptive-product-organization.md`. The target is profitable multi-product operation with an adaptable roster, not a permanently fixed fleet. Start with one proven product loop; add persistent agents when recurring responsibility, isolation or economics justify them. Owner availability does not replace routine autonomous execution.

## Owner communication

Routine work stays in Kanban. Send one short daily digest: metric movement, shipped outcomes, spend/remaining budget, blockers, next bets. Interrupt immediately only for critical incidents or serious escalation classes.

Before reporting a card as «ждёт решения/ввода владельца», verify the ask is fresh by reading the BODY and latest comments — titles go stale for weeks (verified 27.09, t_0955f6c9: title «активация после получения кредов от владельца» while the creds had been delivered into repo secrets since 08.09 and the card was actionable fleet work; reporting the title sent the owner a ghost decision item). A stale owner-wait card gets rescoped (honest title, GO anchor if gated, specify, dispatch) — never escalated as an owner ask.

## Event-driven activation canon (owner directive 22.09)

Never burn turns on `sleep`-polling loops to watch worker cards. Native mechanisms, in priority order:
1. **DAG gating** — `kanban_create parents=[...]` / `kanban_link`: children auto-promote to ready when parents reach done. This IS the action graph; no external orchestrator.
2. **Selected native delivery** — use `fleet-notification-ops` and the actual exposed schema; configured-off auto-subscription is intentional. Owner summaries go to canonical topic 281, never retired topic 2 or DM; independently verify board outcome topics and exact platform receipt. Do not bulk-subscribe, invoke direct send/flush, or enable a second controller. Use LLM notify+wake selectively only when company reasoning is actually needed. A cursor claim is not delivery; UNKNOWN sends must not replay blindly.
3. **cron watchdog** (`--no-agent --script`, empty stdout = silent) for board-level anomalies only (e.g. ready-age > N h, blocked-without-guidance), not per-card tracking.
4. `terminal background=true notify_on_complete=true` for in-session shell waits only.
Wake turns cost tokens — subscribe selectively (chain gates, not every card). block_loop_detected is a wake kind: loops surface automatically.

## PR hygiene traps (proven 22.09)

- GitHub merge-keyword engine: a MERGED PR body containing "close #N"/"fixes #N" AUTO-CLOSES PR #N even when the prose says "do not close". Never reference other PR numbers with closing keywords in release-PR bodies; after any integration merge, immediately re-verify states of sibling PRs the release touched and reopen wrongly-closed ones (reopen = reversible, allowed for company).
- Legit deny classes for workers: opening live kanban.db/policy-db via sqlite3.connect (control-plane, even mode=ro) and diffing/showing config/ controlled paths — both fail closed; route reads through native `hermes kanban` CLI or kanban_* tools and ROOT plugin.yaml only.

## Dispatcher + finalization truths (proven 22.09)

- The kanban dispatcher runs embedded in the DEFAULT-profile gateway process (`C:/Users/max/AppData/Local/hermes/logs/gateway.log`, look for `kanban dispatcher [<board>]:` tick lines), NOT in company's gateway log. Worker profiles carry `kanban.dispatch_in_gateway=false` by design. Do not misdiagnose a dead dispatcher from `profiles/company/logs/gateway.log`; `hermes kanban daemon` is deprecated (embedded is canonical). Manual `kanban dispatch` is a safe nudge but normally unnecessary — ticks run every 60s.
- Delivered source and finalization are separate. Verify immutable artifact plus native task/run/descendant state, then one exposed native transition without force. Source delivery does not issue QA/live acceptance. A reachable judge refusal ends that attempt: do not rephrase away limits or switch to CLI/backend/SQL. Missing native authoring interfaces are scoped source prerequisites with independent QA; preserve the original card and real downstream gates.
- goal_mode judges can reject a valid negative verdict (e.g. QA NO-GO on a card that says "recommend rollout OR rollback"): rescope the card body to the achievable terminal outcome (deliver verdict + evidence), keep the marker, then complete. The judge rules against the card text, not against reality.
- A lexical blocker is diagnosis, not release authority. Record the exact error/denied action and distinguish quota, auth, capacity, dependency and policy. Do not clear a stale field through transient/unblock merely to pass the guard. Correct the exact classifier or materially remove an unnecessary effect through a legitimate native re-scope; verify the changed precondition before a fresh run.
- Compound terminal commands are a deny magnet for workers: any stage touching a policy-controlled basename (`config/fleet-policy.yaml`, live `kanban.db`, `.git/**/index.lock`) or starting with rm denies the WHOLE line. Worker rule: one action per terminal call, git-lock removal never by rm (ask company), and never read control-plane config — test via synthetic fixtures + `load_config()`.
- Multiple QA-passed branches ≠ one activation SHA. Before any rollout decision, verify `git merge-base --is-ancestor` between ALL component heads; divergent branches need an integration merge + independent re-QA of the merged bytes at the new exact SHA (prior per-branch verdicts do not cover it). Bind the decision to that single SHA.

## Windows operator notes (fleet-ops control plane, proven 05.09)

- Repo clones that contain policy-controlled sources (e.g. ventures/fleet-policy) reject ALL writes inside the clone tree (policy_control_plane_mutation). Working pattern: pristine clone read-only + full copy to %LOCALAPPDATA%/Temp for mutation + sha256 manifest before/after as no-drift evidence.
- Protected-path/branch false positives require an exact scoped classifier fix and independent true-positive controls, not hiding via a renamed path, copied target, SHA alias, environment variable, split command or script wrapper. First denial partial+stop; fixtures may inspect denied text as data, never execute it.
- The same classifier denies plain-powerShell read probes in some inline forms; safest ops pattern: write ASCII .ps1 via write_file, run once via `powershell -NoProfile -ExecutionPolicy Bypass -File <path>`, cap tool budget, first repeat deny = block with exact command (protocol v3).
- Never make a gate/marker-delivery card a child of the blocked card it is unblocking: children do not dispatch until the parent is done, which recreates the deadlock (proven 05.09, t_4ca8337d/t_22257b53). Marker deliveries must be standalone cards with an idempotency key; superseded duplicates get a SUPERSEDED comment so workers do not double-run them.
- Before creating a recovery lane, list existing todo/blocked cards for the same scope (AO-00A/B/C existed before the bootstrap); post an explicit scope-split comment on the older lane instead of silently duplicating it.
- When a missing recovery operation blocks its own repair task, split out only the prerequisite native operation into an independently tested bootstrap lane; preserve the original repair ID, artifacts and downstream gates. Do not clone the entire failed task or treat ordinary unfinished tooling as an owner-only capability. Escalate only a genuine access/authority wall; never use alternate paths to bypass a denial.
- Preserve task identity during recovery. Use available native unblock for blocked tasks; for triage, first discover supported specify/promote semantics and authorization. An unavailable tool or one failed attempt does not make the card permanently unrecoverable. Replacement is a last resort for genuinely superseded/unrecoverable scope, not a default escape from triage. Missing native tools under a CLI prohibition are a capability gap to repair through reviewed tooling, never by hidden DB writes.
- Marker-sync merges are not gated merges (17.09, PR4 mvp-peni-site): a PR whose head ref merely echoes the deploy card's marker head prefix can land in main with green mergeability while the deploy card is already done and no QA/review child exists on the graph — markers bookkeep, they do not verify. After any merge, cross-check `gh pr view <n>` (state/mergeCommit/headRefOid) against the card's markers and children; a done card without an authorized independent verdict gets a standalone post-factum QA attestation card (exact head SHA contract, idempotency key, verdict marker as a separate 2-line comment by the authorized poster), linked to the audit card — never as a child of the done deploy card.
- Distinguish graph links from scheduler predicates. In inspected Hermes source, archived parents retain links but satisfy the terminal-parent predicate; retained edges alone do not prove blocking. Verify deployed behavior before surgery. For material dependencies, neither done nor archived by itself proves a positive exact-artifact verdict; require the evidence outcome. Never archive merely to bypass a negative quality gate.
- Validate backup member counts by parsing manifest hash records and hashing the referenced files; line count includes headers and is not a file count. Matching recorded members does not by itself prove complete scope coverage.
- Diagnose a blocked composite command before adding gate-delivery cards. If its optional destructive side effect is unnecessary, company may explicitly abandon that effect, retain the target unchanged and resume only the same task's non-destructive scope through native recovery. Never replay the denied effect via another command/path, infer scope from an args hash, or treat canceling one action as approval for it.
- Treat worker assertions of overlapping or surviving processes as hypotheses until correlated with run-specific OS identity and timestamps. A terminal DB state or a later comment alone proves neither process death nor overlap; withdraw unsupported incident claims immediately in task contracts and owner reports. Require a reproducible isolated failure before scheduling a fix.
- Treat comment closure, author-written gate strings and green GitHub mergeability as claims, not lifecycle or independent verdicts. Verify native task status and latest authorized exact-artifact evidence; correct historical bypass advice explicitly so resumed workers do not inherit it.
- Verify live-writer fences inside the canonical transaction, not only handler preflight; require real registry positive/negative tests. Keep source SHA, installed bundle and loaded process identity distinct, especially when a restart warning is present.

## Dots-style responsibility method

For a long-lived responsibility, bounded delegation, continuation/stop, or cross-channel handoff, load [references/dots-operating-method.md](references/dots-operating-method.md). Apply only the parts relevant to your profile and exact task. This is a methodological adaptation, not OpenAI Dots access, a permission grant, a new scheduler, or a model/config change; existing fleet canon and Fleet Policy take precedence.
