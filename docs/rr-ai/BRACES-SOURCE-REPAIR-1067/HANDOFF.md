# HANDOFF — t_f7a640af / run 1067 — BRACES PROD-GRAPH SOURCE REPAIR

Verdict: NO SAFE SOURCE REPAIR (this run). Not ready for source re-review. No commits; clone pristine at frozen head = rollback anchor.

## Identity / lineage
- run_id 1067, session 20261003_190033_67d885, profile tech, board rr-team, card t_f7a640af (child QA: t_66d48535; consumer t_edc2b4b9 stays blocked).
- Spec (immutable): C:/Users/max/Desktop/all/ventures/docs/rr-ai/BRACES-PROD-GRAPH-REPAIR-20261003.md
- Clone (durable, retained for QA): C:/Users/max/Desktop/all/ventures/.worktrees/rr-braces-source-1067-a7c3 — branch codex/braces-source-repair-1067, HEAD ec77dadf72ed9ada28f1bd092587ab731b3b22f0, git status 0 dirty at closeout. origin set to https://github.com/maximalang/recruiter-radar.git (no network ops beyond gh api readback + npm registry metadata).
- Evidence dir (durable): C:/Users/max/Desktop/all/ventures/docs/rr-ai/BRACES-SOURCE-REPAIR-1067 (hashes in evidence-sha256.txt).
- GitHub readbacks (gh api, read-only): PR266 OPEN head=ec77dadf72ed9ada28f1bd092587ab731b3b22f0 (authoritative head unchanged, matches GO anchor); branch main head=1d7906ae45f9570d4c37d9f73fc6bd5100246f65 == observed main; merge-base --is-ancestor main..head = true.

## Baseline reproduction (fresh, at frozen head, clone dir)
- npm audit --omit=dev --audit-level=high --json → exit 1; counts {high:29, total:29}; single advisory root: braces, range "*", GHSA-vfj7-8cjw-p6xm (source 1240992), "stack-exhaustion DoS via deeply nested patterns". 29 findings = 1 advisory root + 28 dependent nodes (effects chain) — NOT 29 distinct advisories.
- npm audit --audit-level=high --json (full) → exit 1; {high:30, total:30}.
- Files: baseline-audit-omit-dev.json, baseline-audit-full.json, baseline-audit-timestamp.txt (2026-10-03T16:06:20Z).
- Registry/upstream: no fixed release (receipt first_patched_version=null; latest=3.0.3 is itself vulnerable) → upstream-fix route impossible; only dependency-classification repair.

## Prod-graph analysis (prod-graph-analysis.json)
- One braces lock node: node_modules/braces@3.0.3, dev:false.
- Exactly 18 direct ROOT prod deps reach it: braces, micromatch (both direct prod deps themselves), babel-jest, create-jest, expect, jest-circus, jest-cli, jest-config, jest-environment-jsdom, jest-environment-node, jest-haste-map, jest-message-util, jest-resolve, jest-resolve-dependencies, jest-runner, jest-runtime, jest-snapshot, jest-watcher. 68 paths total; every path is root→(jest toolchain | micromatch)→…→braces.
- Declaration (where-declared.json): all 18 ONLY in root:dependencies (jest-environment-jsdom additionally apps/web:devDependencies; jest itself only apps/web:devDependencies). Root manifest: 299 dependencies vs 2 devDependencies — inverted classification.
- Eligible minimal move set = all 18 (each independently reaches braces in prod graph; leaving any one keeps braces prod-reachable).

## Runtime non-requirement evidence for all 18
- Grep across clone (ts/tsx/js/mjs/cjs, excluding node_modules and test/config files) for require/from/dynamic-import of any of the 18 (incl. expect): ZERO hits in shipped code (apps/web app/lib/src, packages/db/src, all scripts dirs).
- apps/web/Dockerfile runner stage explicit closure (lines 71–121): socks, ip-address, smart-buffer, undici, saxes, xmlchars, teleproto, big-integer, mime, node-localstorage, store2, write-file-atomic, slide, graceful-fs, imurmurhash, playwright, playwright-core + named sync/migrate/verify scripts — contains NONE of the 18. Builder runs full `npm ci` (dev included) → moving to devDependencies does not change builder behavior; runner gets standalone trace + explicit copies only.
- Provenance: git log -S shows braces and micromatch entered root dependencies in commit c0eb67c6 "feat: add career-pages smoke targets and test integration" — test-integration work, not a runtime requirement.

## What was applied and what blocked
1. Working-tree CRLF→LF normalization of package.json (blob is LF; clone inherited autocrlf=true — known trap). Local clone config set core.autocrlf=false.
2. Surgical manifest move (surgical-move.mjs): 18 deps→devDependencies, exact minimal diff 18+/18−, LF-clean, JSON-valid. VERIFIED minimal.
3. BLOCKER — lockfile regeneration semantics:
   - `npm install --package-lock-only --ignore-scripts` against the existing lock: versions preserved (lock diff 21+/18−) but dev flags NOT recomputed (only 3 nodes flipped) → audit --omit=dev still exit 1, 28 high (29→28 only because the direct braces root-dep entry disappeared; node flags stale). Evidence: repaired-audit-*.json, repaired-audit-timestamp.txt, npm-partial-repair-lock.json.
   - Full regeneration (lock moved aside to EV, fresh resolve): npm re-resolved to latest — 89 version changes, 156 nodes added (jest 30.x family, @babel bumps, @mendable/firecrawl-js 4.30.1→4.42.4, @noble 2.3.0→2.4.0, @peculiar 2.8.0→2.10.0…), 2 removed → REJECTED: violates no-version-change/minimal-repair and would invalidate QA-validated PR266 state. Evidence: lock-drift.json, lock-moved-aside-for-regen.json, lock-before.json (original bytes).
   - Own reachability model (recompute-dev-flags.mjs, prod edges deps+optional+peer): aborted safely on 15 unexpected dev→prod flips (workspace link nodes apps/web, packages/db and nested duplicates under jest tooling still declared in root deps, e.g. under jest-diff/jest-matcher-utils) → npm dev-flag semantics ≠ naive reachability; refused to hand-write flags. No lock written by this path.
4. Closeout: git checkout -- package.json package-lock.json → clone pristine (status 0). NO commit created; patch_file=null. Rollback anchor = frozen head ec77dadf (nothing to revert).

## Not performed (bounded budget 2700s exhausted by analysis + lock-regeneration blocker)
- Cold full npm ci and production install/materialization in separate clones: NOT RUN.
- web:check, apps/web full jest, web:build/standalone trace: NOT RUN.
- DB adapter parity: NOT RUN (no local disposable fixture available; would bind to exact-head CI lanes Tests/db-parity, Tests/source-live-db, Tests/query-planner-v2-db — unperformed here, stated honestly).
- Full audit residual enumeration on repaired graph: NOT RUN (repair not completed).
- scripts/lineage_readback.py: ABSENT in frozen checkout (ls exit 2) → lineage readback not executed via repo script; this handoff + receipt.json + evidence-sha256.txt are the lineage record.
- git bundle: NOT created (budget); durable clone + evidence dir retained instead; repair candidate preserved as scripts+diffs in EV (no commit existed).

## Resume recipe (minimal residual preconditions)
1. On pristine clone re-run: node $EV/surgical-move.mjs (idempotent; expects LF working tree — normalize package.json bytes CRLF→LF first if autocrlf re-smudged; set local core.autocrlf=false).
2. Version-preserving lock recomputation — candidates, each MUST be verified zero version drift vs $EV/lock-before.json before acceptance:
   a. `npm install --package-lock-only --ignore-scripts --before=2026-10-02T05:05:40Z` (original lock timestamp) — as-of resolution should reproduce original versions with recomputed dev flags.
   b. Cold `npm install --ignore-scripts` (reify, not lock-only) in a scratch clone from repaired manifest + original lock bytes, then copy produced lock back; reify recomputes flags from the actual tree.
   c. Empirical ground truth: after cold install, `npm ls --all --omit=dev --json` → set dev:=true exactly on lock nodes absent from that prod set (never touch versions/integrity).
3. Accept only if: npm audit --omit=dev --audit-level=high exit 0 count 0 AND --audit-level=moderate exit 0 count 0 AND lock diff vs original = classification/dev-flags only (zero resolved-version changes) AND manifest diff = 18+/18−.
4. Then run spec step 5 battery fresh in two unique clones (full cold: npm ci → web:check → apps/web jest → web:build + standalone node_modules absence proof for the 18; production: repo materialization path per Dockerfile builder+runner semantics), full audit residual report, commit exactly two files, format-patch + sha256, bundle, receipt, re-handoff.
5. Residual risk to verify in step 4: root dependencies still contain other jest tooling (jest-diff, jest-each, jest-matcher-utils, jest-get-type, jest-mock, jest-leak-detector, jest-docblock, jest-changed-files, jest-pnp-resolver, jest-regex-util, babel-plugin-jest-hoist, babel-preset-jest etc.) that do NOT reach braces — out of minimal scope, but a follow-up classification cleanup candidate (separate decision, not this card).

## Boundary compliance
No push/PR266/main mutation, no merge/deploy, no audit waiver, no spend, no network beyond gh api readbacks + npm registry metadata. No secret/credential/.env read or write (frozen checkout contains no env files). Drifted regenerated lock rejected, not delivered.
