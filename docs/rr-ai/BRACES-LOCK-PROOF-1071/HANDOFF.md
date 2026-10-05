# HANDOFF — RR PR266 residual lockfile proof, run 1071 (t_8323638f)

## VERIFIED LOCKFILE BLOCKER

Cold native experiment disproves the residual hypothesis: an honest cold `npm install --ignore-scripts` (repaired manifest with the proven 18 declaration moves + original lock) preserves inventory/versions perfectly (584→584 nodes, 0 version changes) but recomputes dev flags for only 3 nodes. `braces@3.0.3` stays production-classified; `npm audit --omit=dev --audit-level=high` exits 1 with 28 findings (identical to producer r1067 warm result). No candidate was committed; nothing was pushed.

## Causal proof (package-manager export, exit 0)

`npm ls braces --omit=dev --all`:

recruiter-radar@1.0.0 → ts-jest@29.4.11 → @jest/transform@29.7.0 → micromatch@4.0.8 → braces@3.0.3

Root still declares ts-jest and 15 other jest-ecosystem packages as PRODUCTION dependencies (jest-util, jest-mock, jest-diff, jest-validate, jest-worker, jest-changed-files, babel-preset-jest, ...). They are outside the authorized 18-move scope. While any of them remains a root production declaration, micromatch/braces are production-reachable and no lock-only, version-preserving repair can make prod audits exit zero. The 3 flips npm did compute (jest-environment-jsdom + @types/jsdom + @types/tough-cookie) confirm npm's honesty: jest-environment-jsdom is the only moved package also declared in apps/web devDependencies, i.e. genuinely dev-only.

## Why experiments 2/3 were not run as separate installs

- Exp2 (as-of regeneration candidate): saved r1067 evidence already disproves the class — full regeneration = 89 version changes/156 nodes added; hand-recomputed flags = 15 unexpected prod flips. Both violate binding criteria; re-execution cannot pass.
- Exp3 (Arborist/real-tree ground truth): subsumed — exports taken from the real cold-installed tree (exp1-npm-ls-braces.txt, exp1-npm-ls-braces-omit-dev.txt, exp1-braces-prod-paths.json).

## Evidence index (this directory)

- receipt.json — machine receipt, all exits/counts/SHAs
- baseline-sha256.txt, baseline-package.json, baseline-package-lock.json — frozen ec77dadf LF bytes (lock sha 8d9db68b… == producer lock-before.json)
- normalization-note.txt — CRLF worktree artifact of `.gitattributes * text=auto`; raw-blob normalization in owned clone only
- surgical-move-1071.mjs, manifest-move-result.json — parameterized producer move script; 18 moves, diff 18+/18-
- exp1-install.log — cold install, exit 0, 54s
- exp1-lock-comparison.json, exp1-comparison-summary.txt — inventory/version/edge/flag comparison (compare-locks.mjs)
- exp1-lock.diff, exp1-manifest.diff — exact 21+/18- lock delta (root mirror + 3 flag lines) and manifest delta
- exp1-audit-omit-dev-high.json (exit 1, 28), exp1-audit-omit-dev-moderate.json (exit 1), exp1-audit-full-high.json (exit 1, 30)
- exp1-npm-ls-braces.txt, exp1-npm-ls-braces-omit-dev.txt (exit 0), exp1-braces-prod-paths.json (BFS script flawed, 0 paths — do not cite; npm ls is authoritative)
- deny-call17-payload.json — policy denial record (see receipt.policy_denials)
- clone-metadata.json — clone provenance, node v24.15.0, npm 11.17.0

## State / lineage

- Owned clone retained dirty (uncommitted moves + flag-updated lock, node_modules present): C:/Users/max/Desktop/all/ventures/.worktrees/rr-braces-lock-1071-e1, HEAD ec77dadf (no commits).
- Owner checkout (dirty, f3e87a13) untouched; pristine producer clone untouched; PR266 untouched (open, head ec77dadf); no push, no publication, no waiver, no spend, no secret/env access.
- scripts/lineage_readback.py absent in frozen and owner checkouts (verified) — this handoff + receipt + evidence-sha256.txt are the lineage record.
- For QA (t_8ac8ae5e): no new candidate SHA exists to freeze; validate this blocker evidence independently (baseline SHAs, comparison JSON, audit exits, npm ls export). Original negative findings remain binding; consumers stay blocked.

## Follow-up beyond this bounded phase (owner decision required, NOT performed)

Moving ts-jest/jest-util/jest-mock/jest-diff/jest-validate/jest-worker/jest-changed-files/babel-*-jest etc. out of root production dependencies (or to devDependencies where no shipped import needs them) would be a NEW declaration-scope decision beyond the authorized 18; it needs shipped-import analysis for that wider set before any lock repair can succeed.
