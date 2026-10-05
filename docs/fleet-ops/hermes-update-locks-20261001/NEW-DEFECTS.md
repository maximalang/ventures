# NEW-DEFECTS — Desktop update handoff branch-pinning risk

Run: t_8bcfc1fc, run_id 1893, profile operations, read-only, 2026-10-01 UTC+3.
Parent report: FLEET-UPDATE-AUDIT.md (same directory). Company binding: comment 5166 (decision:company=go, head=bda33b60).
Scope of this file: defects newly discovered in this run beyond F1–F6 already recorded in FLEET-UPDATE-AUDIT.md §7, plus one anchor-typo correction recorded as a spec defect.

---

## N1. Desktop "Update" button silently unpins the fleet layer branch on a parked tree

Severity: HIGH for the planned §5-Option-A migration (managed custom branch); latent today.

Chain (every link verified in live source at bda33b60):

1. Desktop handoff target branch comes from `readDesktopUpdateConfig()` —
   `apps/desktop/electron/main.ts:3462-3470`: reads `DESKTOP_UPDATE_CONFIG_PATH`
   (= `path.join(app.getPath('userData'), 'updates.json')`, main.ts:1171), falls back
   to `DEFAULT_UPDATE_BRANCH = 'main'` (main.ts:1188) when the file is absent or the
   branch field is blank.
2. Live host state: `C:/Users/max/AppData/Roaming/Hermes/updates.json` contains
   `{"branch": "main"}` (read this run). So the Desktop Update button ALWAYS hands off
   with `-Branch main`.
3. Handoff construction: `apps/desktop/electron/updater/checkout.ts:139-141`
   `const branch: string = status.branch ?? deps.defaultUpdateBranch`
   `const targetArgs = status.channel ? ['--channel', ...] : ['--branch', branch]`
   and checkout.ts:280 passes `'-Branch', branch` into windows.ps1;
   `scripts/desktop-update/windows.ps1:63` forwards it as
   `@("--branch", $Branch)` into `hermes update`.
4. CLI normalization: `hermes_cli/main_install_repair.py:327-329`
   `_resolve_update_branch` — default 'main', and `hermes_cli/update_cmd.py:608-610`
   `_source_update_channel`: "Explicit branches win" — an explicit `--branch main`
   short-circuits the install-record / channel resolution that could otherwise
   preserve a non-main line.
5. In `_pull_updates` (update_cmd.py:898+), with `branch="main"` and no release
   target, `merge_ref = origin/main`; ff-only fails on a diverged custom branch, and
   `_reconcile_diverged_checkout` (update_cmd.py:773+) is called with
   `branch="main"`. The custom-branch merge path DOES fire (current branch
   `company/autocompany-rebased-p0-v5-local` != `main`, so it merges `origin/main`
   into the layer branch — local commits survive), **but** the reconciliation target
   is hard-pinned to `origin/main` even if the operator intended the layer branch to
   track a different upstream line. There is no Desktop-side or CLI-side mechanism to
   say "update this checkout along its own branch"; `--branch` is always emitted,
   always `main`.

Concrete failure mode under the Option A migration (FLEET-UPDATE-AUDIT.md §5):
after a successful `HermesOurLayerPark` (03:55) the tree is pristine on
`company/autocompany-rebased-p0-v5-local`. If a user (or a recovery hand-off,
main.ts:4711-4716 — same `readDesktopUpdateConfig` fallback) triggers the Desktop
Update button in that window, the hand-off runs `hermes update --branch main`.
The update then (a) fetches origin/main, (b) merges origin/main into the layer
branch via the custom-branch path — unreviewed, outside the nightly window, with
no park/apply preflight, no isolated patch check, and no soak collection — or
(c) on any conflict aborts mid-window leaving the tree parked-but-unapplied until
05:00 apply. Either outcome bypasses every control the park/apply line exists for.

Contrast with the manual command card, which IS branch-aware:
`apps/desktop/electron/updater/checkout.ts:63-66` `buildManualUpdateCommand` emits
`hermes update --branch <currentBranch>` for non-main checkouts — the code knows how
to pin the current branch, but the apply path (checkout.ts:139) ignores the live
checkout branch and uses only the probe/config value.

Not a defect of the layer; not caused by F1–F6. Reproduced by source inspection
only — no update was executed (read-only card).

Remediation options (for the follow-up code card, NOT this card):
- R1: extend `check()` in checkout.ts to prefer the live checkout branch
  (`git branch --show-current`, already available via the source probe's
  `status.branch`) and pass it through `apply()` exactly as
  `buildManualUpdateCommand` already does; treat `updates.json` as an override,
  not the default source of truth.
- R2: in `_source_update_channel` / `_resolve_update_branch`, when the checkout is
  on a custom branch and `--branch` was NOT explicitly typed by a human on a CLI
  (i.e. came from a hand-off), resolve to the current checkout branch instead of
  'main'. Requires plumbing hand-off provenance — heavier than R1.
- R3 (interim, ops-side): set `updates.json` branch to
  `company/autocompany-rebased-p0-v5-local` at the same time the Option A migration
  lands, so the pinned branch IS the layer branch. Zero code change, but fragile:
  any Desktop reset of that config silently re-opens the hole. State-changing →
  belongs to the migration card, not here.

Kill criterion for any fix: a Desktop-initiated update on a parked
`company/autocompany-rebased-p0-v5-local` checkout must either target the layer
branch or refuse with a visible message; it must never target `origin/main` by
default.

---

## N2. Spec anchor typo: `source scripts/desktop-update/windows.ps1`

FLEET-AUDIT.md line 8 anchors "`source scripts/desktop-update/windows.ps1` sha256
b63951c8…28418b". No such path exists; the real file is
`hermes-agent/scripts/desktop-update/windows.ps1` and its sha256 matches
(b63951c8551df1c44ed3ec15a88322b39316306835ffdf4b4fed2f4f1d28418b, re-verified this
run). Recorded here as a card-spec defect so downstream cards quote the canonical
path. No action taken on the file itself.

---

## Relationship to existing findings

- N1 is a precondition-risk for the Option A migration recommended in
  FLEET-UPDATE-AUDIT.md §5: the migration's kill criteria there cover git-level
  misbehaviour (reset --hard on the layer branch); N1 covers the human/recovery
  trigger path that would invoke an off-window `hermes update --branch main`
  against that branch. Both must be closed before Option A is safe.
- N1 does not affect the current park/apply line while nobody clicks Update
  between 03:55 and 05:00; the nightly CLI path (`nightly_update.cmd` →
  `hermes update` without `--branch`) resolves via the install record and is not
  subject to this defect.

End-to-end acceptance remains NOT VERIFIED, unchanged from the parent report. This
card was read-only: no backup, no release activation, no gateway/desktop/scheduler
state changed; `updates.json` was read, not written.
