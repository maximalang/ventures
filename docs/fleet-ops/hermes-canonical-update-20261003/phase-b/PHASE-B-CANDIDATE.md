# Phase B — clean custom-branch candidate + native update_in_place fixture tests

Task: t_1dd91b18 (tech). Date: 2026-10-03. Status: STAGED ONLY — no live switch/config/scheduler install, no update/doctor run, no main commit, no state/kanban/policy DB touch.

## 1. Frozen source candidate (immutable SHA)

- Base (official HEAD, byte-verified at recon): `9aae3c23e2c4f39f77d8d54b5e72ba4b90f4ba8f` (v0.21.5, `rc.35-v0.21.5-328-g9aae3c23e2`)
- Candidate commit: `a35fd4b08741767f4b2367eb762560fe42e84999`
- Candidate tree: `b6b5f0ea44365ea259e89660745f9ea866b374bd`
- Branch name: `fleet/canonical-20261003` (exists ONLY in staging repo `C:/tmp/hermes-phaseb-t1dd91b18/cand` + bundle; NOT created in the live repo)
- Identity: scoped test identity `Hermes Fleet Staging <fleet-staging@noreply.local>` — repo-local to the staging repo only. Live repo has no local identity; global git config untouched (was empty, still empty). No owner identity fabricated.
- Assembly: fully offline git plumbing (read-tree of base + hash-object/update-index per overlay file + commit-tree). `GIT_NO_LAZY_FETCH=1` throughout — zero upstream pulls, zero conflict merges, zero live-repo writes (live HEAD/status re-verified unchanged after build).

### Delta manifest (CANDIDATE-DELTA-46.txt in this dir)
Exactly 46 paths = the current fleet overlay: 35 modified tracked files (M) + 11 new fleet test files (A). Diffstat `46 files changed, 3435 insertions(+), 117 deletions(-)`; the 35-file portion matches the live repo's own `git diff --stat HEAD` byte-for-byte (`1502 insertions(+), 117 deletions(-)`), the remaining 1933 insertions are the 11 new test files. No renormalization churn inside the delta.

### Byte-preservation verification (PASS)
For all 46 paths: candidate blob SHA == live-repo `git hash-object --path=<p> <live worktree file>` (computed independently in the LIVE repo context, i.e. exactly what `git add` there would store). Result: 46/46 equal, 0 mismatches.

Checkout proof: `git worktree add --detach` of the candidate materialized a full tree with `git status --porcelain` = 0 lines (clean, offline).

### Excluded from candidate, preserved in backup (per BRIEF)
Live-tree untracked, left in place untouched AND copied to `phase-b/excluded-backup/` with SHA256 in `phase-b/ARTIFACTS.sha256`:
- `e2e_canary_rebased.py` (throwaway canary) — `1a1e6d3a…9fd14`
- `hermes_cli/kanban_db_dispatch.py.bak-blockerauth-20261002T003321Z` — `af109606…fa04e`
- `tests/hermes_cli/test_kanban_db.py.bak-blockerauth-20261002T003321Z` — `c3e9daca…cf100`

### Known latent anomaly (documented, not "fixed")
A full-content re-hash of the live tree (foreign-index probe) surfaced 744 paths (e.g. `.envrc`, `.npmrc`, `.nvmrc`) whose worktree bytes (CRLF) differ from HEAD blobs while the live index stat-cache marks them clean — a classic hidden CRLF drift. They are NOT part of the overlay, NOT in the candidate, and are not rewritten by branch switch or by update_in_place merges (merge touches only files changed upstream). Deliberately left as-is: any renormalization would violate "preserve live fleet runtime bytes" and create a 744-file conflict surface for future merges.

### Delivery artifact
- Bundle: `phase-b/hermes-fleet-candidate-a35fd4b0.bundle` — SHA256 `fd1187483fbbb7477cf9099cd9cdb87edf82bd4b47495e15679eafb3688eea7e`, 59,842 bytes, `git bundle verify` OK (prerequisite: base commit `9aae3c23…`, present in the live repo → Phase D fetch works offline).

## 2. Native update_in_place fixture tests (real official tests, temp fixtures only)

Run from the candidate worktree (`C:/tmp/hermes-phaseb-t1dd91b18/src`, HEAD=a35fd4b0) with the live venv interpreter; hermes home isolated via LOCALAPPDATA/USERPROFILE/HERMES_HOME → `C:/tmp/hermes-phaseb-t1dd91b18/fixture-*` (live home never targeted). Tests build REAL git origin+clone fixtures under pytest tmp_path; nothing ran against the live install.

One environment neutralizer was required and is disclosed: `retarget_to_owning_install()` (hermes_cli/update_owning_install.py) redirects `hermes update` back to the install that owns the running interpreter — it fires only because tests ran on the LIVE in-tree venv, and it would re-exec the live CLI (observed once before neutralization: child died harmlessly on pytest argv parsing; live repo state re-verified unchanged afterwards). Official CI interpreters are not in-tree venvs, where `owning_install_root()` returns None by design. The plugin (`C:/tmp/hermes-phaseb-t1dd91b18/plugin/neutralize_owning_install.py`) pins exactly that CI outcome. No test file or update machinery was modified.

Results (candidate code):
- `tests/hermes_cli/test_update_parked_branch_guard.py` — 18 passed (45.8s). Covers: in_place merge when `parked_branch_strategy=update_in_place` (checkout never moves, origin/main code arrives, local commit survives); DIRTY parked branch → loud warn + exit 1 + code update SKIPPED + no autostash created, branch/HEAD untouched; untracked-file block; `--switch-branch` one-run override leaves branch tip byte-identical; clean fully-merged auto-switch; stopped rebase / git-am refusal without moving HEAD.
- `tests/hermes_cli/test_update_diverged_rescue_ref.py` — 3 passed (9.4s): rescue-ref backup before diverged reset, index-lock reported without false divergence, operational ff-failure preserved without reset.
- `tests/hermes_cli/test_update_autostash.py` — 36 passed, 1 skipped (84.2s), incl. conflicted-restore parks the patch and records it in the receipt.
- `tests/hermes_cli/test_update_interrupted_pull.py` — 2 passed, 1 failed (35.8s). Failure: `test_killed_pull_is_restored_on_next_launch_and_update_reruns` — early recovery DID restore the checkout, but the rerun's `merge --ff-only` hit "local changes to other.py would be overwritten" and the code took the safe refusal path (`✗ Fast-forward failed; refusing to reset…no reset was attempted`, SystemExit 1 at update_cmd.py:952). DISCRIMINATOR: the identical test fails identically on a pristine official BASE worktree (`C:/tmp/hermes-phaseb-t1dd91b18/base`, 9aae3c23, zero overlay) ⇒ environmental (Windows), NOT a fleet-overlay regression. Failure mode is non-destructive by design.

### Conflict-path coverage — honest limitation
No official test asserts the custom-branch in-place merge CONFLICT branch itself (`_reconcile_diverged_checkout`: `git merge --abort` + "Merge conflict…update stopped, nothing was changed" + exit 1). Code path was read and confirmed (update_cmd.py ~781-800); adjacent official coverage passed: merge-conflict marker semantics (interrupted_pull), dirty-tree refusal (guard), diverged rescue refs. QA follow-up recommended before activation: one fixture run forcing an in-place merge conflict.

## 3. Native scheduling — alignment (per SIMPLE-NATIVE-SCHEDULE.md; research NOT expanded)

- Native installation EXISTS and is the design: official source path (`hermes update`, Desktop handoff/windows.ps1 runtime verification + relaunch). What was previously not found is only an autonomous in-app idle-triggered Apply — that absence is NOT a blocker for the scheduled native action and no GUI auto-Apply feature is authorized.
- Staged candidate task `COMPANY-NATIVE-NIGHTLY-STAGED.xml` re-verified in workspace: SHA256 `8f39b633a5543b54c6a4d14fa1dc699b97f2819a8a6dddaf8e06fe653b3c3d58` == company receipt. One DIRECT canonical action, no wrapper: `C:\Users\max\AppData\Local\hermes\hermes-agent\.hermes\bin\hermes.exe` `-p default update --yes`; `<Enabled>false</Enabled>` (Disabled staged artifact; schema validated via Microsoft TASK_VALIDATE_ONLY=1 exit 0 — validation of schema ONLY, NOT deploy evidence; live task unchanged).
- Phase B fixture tests substantiate exactly the git-level contract that action relies on: with a CLEAN committed fleet branch + `parked_branch_strategy=update_in_place` (already in live config per baseline receipt), `update --yes` merges origin/main into the branch in place, preserves local commits, never moves the checkout; dirty tree → safe skip; divergence → rescue ref; failures → non-destructive refusal. The clean candidate branch of §1 is the precondition that turns today's dirty-tree SKIP into a working in-place merge.
- NOT validated here (QA scope before any activation, per company): full Desktop relaunch/supervision lifecycle, gateway/serve ownership reconciliation (`update --plan` shows default gateway manual / default serve desktop-owned), active-owner-work protection at the idle boundary, update receipt + fresh stable Telegram. PM comment 1624 noted: old Python readers do not block new dependency generation; legacy CLI help text is not permission to kill holders. If the direct native CLI does not satisfy full Desktop relaunch semantics → mark the XML BLOCK and report the precise contract gap; no wrappers, no force-close/relaunch compensation, no new scheduler subsystem.

## 4. Phase D activation recipe (staged instructions only — NOT executed)

1. `cd C:/Users/max/AppData/Local/hermes/hermes-agent`
2. `git fetch <workspace>/phase-b/hermes-fleet-candidate-a35fd4b0.bundle fleet/canonical-20261003:refs/heads/fleet/canonical-20261003` (offline; prerequisite = current HEAD)
3. `git switch fleet/canonical-20261003` — expected clean switch: the 46 dirty/new worktree paths are byte-identical to target blobs (verified §1), so git carries them over and `git status` becomes clean; the 3 excluded untracked files stay in place (untracked files are untouched by switch/merge). VERIFY `git status --porcelain` == only the 3 excluded paths before proceeding; abort to rollback on any surprise.
4. No config change needed (`updates.parked_branch_strategy: update_in_place` already live). The staged native task then maintains the branch; conflicts abort safely and require the documented manual `git merge origin/main` resolution.

Rollback: `git switch main` (returns to official HEAD; overlay preserved on the candidate branch + bundle); updater-written anchors: `pre-update-<ts>` tags before in-place merges, `refs/hermes-update-backups/*` rescue refs on diverged resets. Immutable off-box copies: bundle + excluded-backup + this manifest (SHA256 in ARTIFACTS.sha256).

## 5. Source preservation readiness — verdict

READY (staged): exact frozen candidate (immutable SHA, byte-exact overlay, offline-assembled, exclusions backed up), native in_place contract proven by real official fixture tests on the candidate code, staged Disabled native task schema-verified. Gating for activation: QA lifecycle validation (§3) + Phase C exact-source decision (bundle vs official source) + owner boundary. One environmental official-test failure and one untested conflict branch are disclosed above — both non-destructive failure modes.

Evidence paths: staging repo `C:/tmp/hermes-phaseb-t1dd91b18/cand` (branch), worktrees `src` (candidate) / `base` (baseline discriminator), logs `guard.log`, `test_update_*.log`, `base_interrupted.log`, build scripts `build.sh` (v1, superseded — GIT_INDEX_FILE leak produced a 790-path phantom delta; v2 authoritative), `build2.sh`.
