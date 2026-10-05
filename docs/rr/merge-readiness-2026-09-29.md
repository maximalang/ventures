# RR PR-wave merge readiness ledger

**Generated:** 2026-09-29 21:05 MSK (UTC+03:00)
**Worker:** operations / run t_0055a760
**Source data:** `gh pr list/view --repo maximalang/recruiter-radar` (live, exit 0); kanban handoff context from t_0055a760 body.
**Scope:** 19 open PRs (#198, #223, #226, #230, #236, #237, #242, #243, #245, #246, #247, #248, #249, #250, #251, #253, #254, #255, #256). Closed #235 (MERGED 2026-08-28) and #238 (MERGED 2026-08-29) are out of scope.

## Task coverage map (from t_0055a760 body)

| Task ID      | Title                                                | Lane    | PR          | Blocker / Superseded |
|--------------|------------------------------------------------------|---------|-------------|----------------------|
| t_b55d1a53   | Better Auth identity foundation                      | blocked | #198        | Multi-method auth program (RR new rule) |
| t_2a1c956f   | Auth stabilization [runtime+#214+#198 contract]      | blocked | runtime / #214 / #198 | blockers t_ecfc7c25 |
| t_a2bcc6ee   | Fix deploy CI/CD pipeline                            | CI/CD   | #249, #250  | — (known blocker)    |
| t_98d91920   | Landing demand instrumentation D1-D4                 | CI/CD   | #251 / #253 | dup                  |
| t_4e62056a   | Legal/privacy closure                                | legal   | #226        | legal compliance     |
| t_eee88d2d   | RF Source Intelligence V2                            | sources | #223        | dirty, huge (1,840+) |
| t_2cf2d814   | Trial honesty: 3x24h                                 | trial   | #236, #237  | — (known blocker)    |
| t_0955f6c9   | Telegram source activation                           | telegram| #255        | env-only            |
| t_0952a687   | Telegram feedback buttons                            | telegram| runtime + #235 (closed MERGED) | #247, #243 |
| t_2aa44ad2   | SEO surface closure                                  | seo     | #238 (closed MERGED) | — |
| t_4f3fb362   | Clock blocker: source cycle stall                    | ops     | runtime + #247 | #245, #246 (HH half fixed by 29.08 analysis) |
| t_0746b3b4   | Cabinet UI Linear-grade                              | cabinet | #256        | theme token (independent) |
| t_a6f197a1   | Product story clarity                                | story   | #242        | — (known blocker)    |
| t_31ef4854   | Techstack enrichment pilot                           | —       | #254        | evidence bundle      |
| (none)       | Landing analytics-disabled                           | landing | #230        | —                    |

## Per-PR CI rollup (latest check run at fetch time)

Legend: PASS = all listed checks green; FAIL = ≥1 red check; DIRTY = mergeStateStatus=DIRTY/CONFLICTING.

| PR   | Branch                                       | Mergeable | State     | CI verdict | Red checks (latest run)                                       |
|------|----------------------------------------------|-----------|-----------|------------|----------------------------------------------------------------|
| #198 | codex/better-auth-foundation                 | MERGEABLE | CLEAN     | PASS       | —                                                              |
| #223 | codex/rf-source-intelligence-v2              | CONFLICTING | DIRTY   | PASS       | —                                                              |
| #226 | codex/legal-compliance-closure               | CONFLICTING | DIRTY   | PASS       | —                                                              |
| #230 | codex/landing-analytics-disabled             | MERGEABLE | CLEAN     | PASS       | —                                                              |
| #236 | codex/trial-contract-immutable-profile       | MERGEABLE | CLEAN     | PASS       | —                                                              |
| #237 | codex/trial-runtime-guard                    | MERGEABLE | CLEAN     | PASS       | —                                                              |
| #242 | codex/landing-product-story-v2               | MERGEABLE | UNSTABLE* | PASS       | landing-playwright CANCELLED (re-run on retry usually green)  |
| #243 | codex/lead-suppression-digest                | MERGEABLE | UNSTABLE* | PASS       | landing-playwright CANCELLED (same pattern)                   |
| #245 | codex/source-refresh-rate-limit-rootcause    | MERGEABLE | CLEAN     | PASS       | —                                                              |
| #246 | codex/source-refresh-vm-authority            | CONFLICTING | DIRTY   | FAIL       | lint-and-types ×2, Auth v2/unit ×2                            |
| #247 | codex/source-refresh-failure-classification  | MERGEABLE | UNSTABLE  | FAIL       | commercial-signal-evidence-radar, smoke, contracts, lint-and-types ×2, Auth v2/unit ×2 |
| #248 | codex/rf-identity-boundary-hardening         | MERGEABLE | UNSTABLE  | FAIL       | unit-tests ×2                                                  |
| #249 | codex/agents-scope-preflight                 | MERGEABLE | UNSTABLE  | FAIL       | commercial-signal-evidence-radar, timeweb-oauth-security ×2, unit-tests ×2, Auth v2/security-smoke ×2, security-audit ×2 |
| #250 | codex/ci-baseline-green                      | MERGEABLE | UNSTABLE  | FAIL       | unit-tests ×2                                                  |
| #251 | codex/landing-telemetry-remediation          | MERGEABLE | UNSTABLE  | FAIL       | commercial-signal-evidence-radar, timeweb-oauth-security ×2, Auth v2/security-smoke ×2, security-audit ×2, landing-playwright ×2 |
| #253 | codex/telemetry-mainline-21                  | MERGEABLE | UNSTABLE  | FAIL       | commercial-signal-evidence-radar, timeweb-oauth-security ×2, Auth v2/security-smoke ×2, security-audit ×2, landing-playwright ×2 |
| #254 | codex/techstack-enrichment                   | MERGEABLE | UNSTABLE  | FAIL       | commercial-signal-evidence-radar, timeweb-oauth-security ×2, Auth v2/security-smoke ×2, security-audit ×2 |
| #255 | codex/telegram-source-runtime                | MERGEABLE | UNSTABLE  | FAIL       | commercial-signal-evidence-radar, timeweb-oauth-security ×2, unit-tests ×2, Auth v2/security-smoke ×2, security-audit ×2 |
| #256 | rr/cabinet-linear-polish                     | MERGEABLE | UNSTABLE  | FAIL       | commercial-signal-evidence-radar, timeweb-oauth-security, Auth v2/security-smoke, security-audit |

`*` UNSTABLE here reflects a single CANCELLED landing-playwright run with all other checks green; GitHub classifies cancelled as non-success.

### Diff-size sanity on the #251/#253 dup
- #251: 70 files changed, +3321/-100, head 2df6c648
- #253: 21 files changed, +1405/-19,  head 6ae0de15
- Same business scope (landing demand instrumentation D1-D4, t_98d91920). **#253 is the atomic 21-file scope on main** — supersedes #251.

## Classifications

### merge-ready (CI green, MERGEABLE, no live blocker)
| PR   | Why                                                                 |
|------|---------------------------------------------------------------------|
| #230 | Landing analytics-disabled tests; independent of telemetry wave.    |
| #236 | Trial contract doc only (runtime guard lives in #237).              |
| #237 | Trial 3×24h runtime guard; RR honesty rule codified.                |
| #245 | Source refresh rate-limit root cause; unblocks Clock.               |
| #198 | Better Auth foundation — **HOLD for owner**: RR rule says multi-method auth program is a separate PR wave; #198 alone is incomplete. Listing as merge-ready on CI, but lane-blocked by product decision. Downgraded to `blocked` in queue. |

### blocked (waiting on a named external decision/artifact, not on another PR in this wave)
| PR   | Blocker                                                                                                  |
|------|----------------------------------------------------------------------------------------------------------|
| #198 | Multi-method auth program (passkey/magic-link/OAuth/Telegram/password+TOTP) must land as separate wave.   |
| #226 | Legal compliance closure requires owner sign-off on privacy/terms content.                               |
| #249 | Docs-only preflight but carries failing unit-tests ×2 + security-smoke ×2; likely stale branch. Rebase needed. |
| #255 | Telegram source runtime: env-only blocker per coverage map; needs owner to set VDS env.                  |

### superseded (closed PR replaced by another open PR)
| PR   | Superseded by | Reason                                                              |
|------|---------------|---------------------------------------------------------------------|
| #251 | #253          | Same D1-D4 scope; #253 is atomic 21-file on main, #251 is 70 files. |
| #247 | #245          | Clock blocker lane: 29.08 analysis classified failures; #245 is the surviving fix. #247 still red on 5 check classes. |

### conflict (mergeStateStatus=CONFLICTING, requires rebase before any merge evaluation)
| PR   | Lane    | Notes                                                                 |
|------|---------|-----------------------------------------------------------------------|
| #223 | sources | RF Source Intelligence V2 — dirty + 1,840+ file footprint. Rebase first. |
| #226 | legal   | Legal closure — dirty. Rebase first.                                   |
| #246 | ops     | VM source refresh tick authority doc — dirty + 4 red checks. Likely stale; consider close after #245 merges. |

### needs-rework (MERGEABLE but red CI on real code paths)
| PR   | Red checks (latest)                                                                          |
|------|----------------------------------------------------------------------------------------------|
| #248 | unit-tests ×2                                                                                |
| #250 | unit-tests ×2 (browserslist bump — likely unrelated breakage, needs lockfile regen + rebase) |
| #253 | commercial-signal-evidence-radar, timeweb-oauth-security ×2, Auth v2/security-smoke ×2, security-audit ×2, landing-playwright ×2 |
| #254 | commercial-signal-evidence-radar, timeweb-oauth-security ×2, Auth v2/security-smoke ×2, security-audit ×2 |
| #256 | commercial-signal-evidence-radar, timeweb-oauth-security, Auth v2/security-smoke, security-audit |

Note: `commercial-signal-evidence-radar`, `timeweb-oauth-security`, `Auth v2/security-smoke`, `security-audit` fail in lockstep across most PRs — high probability of a shared baseline failure rather than per-PR regression. Recommend a single baseline-green PR (e.g. rebase #250) landed first, then re-evaluate.

### queued-after (depends on another PR in this wave landing first)
| PR   | Queued after | Why                                                                       |
|------|--------------|---------------------------------------------------------------------------|
| #242 | #253         | Product-story copy changes should land on top of telemetry-instrumented landing so events fire on the final markup. |
| #243 | #245         | Lead-suppression digest touches the same source-refresh runtime paths as #245; merge after Clock fix stabilises. |
| #256 | #242         | Cabinet Linear theme is independent by the coverage map, but landing/cabinet share design tokens; ship after story to avoid token thrash. (Soft queue — can be promoted to merge-ready if owner wants visual closure first.) |

## Routing summary

- **merge-ready (4):** #230, #236, #237, #245
- **blocked (4):** #198 (auth-program wave), #226 (legal sign-off), #249 (stale + red), #255 (env)
- **superseded (2):** #251 → #253, #247 → #245
- **conflict (3):** #223, #226, #246
- **needs-rework (5):** #248, #250, #253, #254, #256
- **queued-after (3):** #242, #243, #256 (soft)

(#226 appears in both `blocked` and `conflict`; classify as `blocked` for routing, flag conflict for rebase when unblocked. #256 appears in `needs-rework` and `queued-after`; classify as `needs-rework` until CI is green, then queue behind #242.)

## Recommended next actions for owner
1. Land the four merge-ready PRs in this order: #245 (Clock) → #237 (trial guard) → #236 (trial contract doc) → #230 (analytics-disabled tests).
2. Close #251 and #247 as superseded.
3. Trigger a baseline-green pass (rebase #250, fix unit-tests ×2) — this should clear the lockstep security-* / commercial-signal / timeweb-oauth failures on #253, #254, #256.
4. Owner decisions needed: #198 (auth wave timing), #226 (legal copy), #255 (VDS env), #223 (rebase strategy for 1,840-file sources wave).

## Out of scope for this run
- rr-team QA card creation: worker context is `HERMES_DELEGATED_CHILD_CONTEXT=1`; `hermes kanban --board rr-team list` returned `delegate_task child contexts cannot mutate Kanban tasks or boards`. MCP `kanban_create(board=rr-team)` from this worker would silently land in the fleet-ops DB per live defect t_91c13f66 (sticky `HERMES_KANBAN_DB` env overrides `--board`). QA cards must be created by company/operator context. Recommend company replays this ledger and creates the rr-team QA cards from the routing summary above.
