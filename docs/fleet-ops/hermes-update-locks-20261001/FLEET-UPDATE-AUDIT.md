# FLEET-UPDATE-AUDIT — native update × preserved fleet layer

Run: t_8bcfc1fc, run_id 1893, profile operations, read-only, 2026-10-01 00:45–01:05 UTC+3.
Card spec: `C:/Users/max/Desktop/all/ventures/docs/fleet-ops/hermes-update-locks-20261001/FLEET-AUDIT.md`.
Company binding: comment 5166 (decision:company=go, head=bda33b60).

## Anchors (re-verified this run)

| anchor | expected | observed | verdict |
|---|---|---|---|
| Live source HEAD | bda33b601d194fb8a43e5660c57542aad14aa372 | bda33b601d194fb8a43e5660c57542aad14aa372 (`git rev-parse HEAD`, exit 0) | match |
| Live tree dirty files | 0 | 0 (`git status --porcelain | wc -l` → 0) | match |
| Layer branch ref | refs/heads/company/autocompany-rebased-p0-v5-local = e5a6fbf82f95185529d51a946976f101520db8c2 | e5a6fbf82f95185529d51a946976f101520db8c2 | match |
| Layer base | f81bb4c4851db72c66593f595a577a4fef008efc | f81bb4c4851db72c66593f595a577a4fef008efc (merge-base bda33b60 f81bb4c4 = f81bb4c4) | match |
| `deploy/our-layer/apply_our_layer.ps1` | sha256 33230f26…eccbaab | 33230f2652f23ddd6c64ee158fb4ac3e42e0e2d6f4b25db7af1e85599eccbaab | match |
| `deploy/our-layer/park_our_layer.ps1` | sha256 f4f4946e…c91269 | f4f4946e5a1f5c5047bbba3145f4b7bb16ccb1aefc9900408567588132c91269 | match |
| `scripts/desktop-update/windows.ps1` | sha256 b63951c8…28418b | b63951c8551df1c44ed3ec15a88322b39316306835ffdf4b4fed2f4f1d28418b | match — note: spec writes path as `source scripts/desktop-update/windows.ps1` (with a space); on-disk the real file is `hermes-agent/scripts/desktop-update/windows.ps1`. Spec path is a typo; the canonical file matches by hash. |

All anchored bytes are unchanged — prior review conclusions still attach to them.

## 1. Layer base→tip enumeration (f81bb4c4..e5a6fbf8)

`git diff --name-status f81bb4c4..e5a6fbf8` → 43 entries: 7 added (A), 36 modified (M), 0 deleted. Aggregate 3229 insertions / 109 deletions.

Programmatic classification against HEAD bda33b60 (`git diff --stat bda33b60 e5a6fbf8 -- <path>` per file):

| Path | Status | Update/dispatch-related? | Disposition vs HEAD bda33b60 |
|---|---|---|---|
| agent/credential_pool.py | M | NO (model pool) | unrelated — diverged upstream; do not reinstall |
| agent/delegation_context.py | M | NO (delegation ctx) | unrelated — diverged upstream; do not reinstall |
| agent/retry_utils.py | M | NO (model pool retry) | unrelated — diverged upstream; do not reinstall |
| e2e_canary_rebased.py | A | NO (canary harness for the layer itself) | layer-owned tooling, not a runtime patch |
| gateway/kanban_watchers.py | M | YES (dispatch path) | update-related, still required |
| gateway/kanban_watchers_dispatcher.py | M | YES (dispatch path) | update-related, still required — PermissionError streak alert (#t_baed78d9 fix) |
| hermes_cli/commands.py | M | partial (kanban wiring) | still required (kanban command routing) |
| hermes_cli/gateway.py | M | YES (PM env on Windows fix, orphan venv labels) | still required |
| hermes_cli/kanban.py | M | YES (kanban CLI surface) | still required |
| hermes_cli/kanban_db.py | M | YES (kanban persistence) | still required |
| hermes_cli/kanban_db_connect.py | M | YES | still required |
| hermes_cli/kanban_db_dispatch.py | M | YES | still required |
| hermes_cli/kanban_decompose.py | M | YES | still required |
| hermes_cli/kanban_parser.py | M | YES | still required |
| hermes_cli/kanban_specify.py | M | YES | still required |
| plugins/platforms/telegram/adapter.py | M | NO (outbound HTML lane) | unrelated to update; still required for fleet comms |
| tests/agent/test_credential_pool_sole_cooldown.py | M | NO | unrelated |
| tests/agent/test_retry_delay_parsers_shared.py | M | NO | unrelated |
| tests/agent/test_zai_pool_rotation.py | A | NO | unrelated |
| tests/conftest.py | M | partial (test infra) | test-only |
| tests/gateway/test_dispatcher_permission_storm_fleet_alert.py | A | YES | covers kanban_watchers_dispatcher PermissionError alert |
| tests/gateway/test_pm_gateway_legacy_venv.py | A | YES | covers hermes_cli/gateway.py PM env on Windows |
| tests/gateway/test_telegram_html_payload.py | A | NO | telegram adapter coverage |
| tests/hermes_cli/test_kanban_decompose.py | M | YES | still required |
| tests/hermes_cli/test_kanban_dispatch_isolation.py | A | YES | still required |
| tests/hermes_cli/test_kanban_lifecycle_metrics.py | A | YES | still required |
| tests/hermes_cli/test_kanban_policy_denied.py | A | YES | still required |
| tests/hermes_cli/test_kanban_review_lifecycle_complete.py | M | YES | still required |
| tests/hermes_cli/test_kanban_review_surfaces.py | M | YES | still required |
| tests/hermes_cli/test_kanban_specify.py | M | YES | still required |
| tests/hermes_cli/test_kanban_unknown_profile_dispatch.py | A | YES | still required |
| tests/hermes_cli/test_kanban_write_guard.py | M | YES | still required |
| tests/home_io_guard.py | M | partial (test guard refinement) | still required |
| tests/tools/test_goal_judge_transport_failure.py | A | YES | review/goal-judge transport path |
| tests/tools/test_kanban_specify_tool.py | A | YES | still required |
| tests/tools/test_kanban_tools.py | M | YES | still required |
| tools/kanban_tools.py | M | YES | still required |
| tools/kanban_tools_schemas.py | M | YES | still required |
| tools/send_message_senders.py | M | NO (telegram send) | unrelated |
| toolsets.py | M | partial (toolset exposure) | still required (kanban toolset exposure) |
| website/docs/reference/tools-reference.md | M | NO (docs) | docs only |
| website/docs/reference/toolsets-reference.md | M | NO (docs) | docs only |
| website/docs/user-guide/features/kanban.md | M | NO (docs) | docs only |

Update/dispatch-related subset (the one this audit must verify survives a native update):
- gateway/kanban_watchers.py
- gateway/kanban_watchers_dispatcher.py
- hermes_cli/commands.py
- hermes_cli/gateway.py
- hermes_cli/kanban.py
- hermes_cli/kanban_db.py
- hermes_cli/kanban_db_connect.py
- hermes_cli/kanban_db_dispatch.py
- hermes_cli/kanban_decompose.py
- hermes_cli/kanban_parser.py
- hermes_cli/kanban_specify.py
- tests/gateway/test_dispatcher_permission_storm_fleet_alert.py
- tests/gateway/test_pm_gateway_legacy_venv.py
- tests/hermes_cli/test_kanban_* (8 files)
- tests/tools/test_goal_judge_transport_failure.py, tests/tools/test_kanban_specify_tool.py, tests/tools/test_kanban_tools.py
- tools/kanban_tools.py, tools/kanban_tools_schemas.py, toolsets.py

Out of scope and explicitly NOT to be reinstalled by this work (unrelated model/pool/auth): agent/credential_pool.py, agent/delegation_context.py, agent/retry_utils.py, plugins/platforms/telegram/adapter.py (HTML lane), tools/send_message_senders.py, tests/agent/*, tests/gateway/test_telegram_html_payload.py, docs/*.

## 2. Stock update handoff → source swap → completion → live fleet resume

Source trail (live `C:/Users/max/AppData/Local/hermes/hermes-agent` @ bda33b60, clean):

1. `hermes_cli/update_cmd.py:899 _update_via_git_with_autostash` — orchestrates ff/detach + `_reconcile_diverged_checkout`.
2. `hermes_cli/update_cmd.py:773 _reconcile_diverged_checkout` — custom branch ⇒ `git merge --no-edit origin/<branch>`; same branch and proven non-ancestor ⇒ `git update-ref refs/hermes-update-backups/<kind>-<branch>-<ts>-<pre12>` then `git reset --hard`. The rescue ref prefix `refs/hermes-update-backups/…` is a durable pre-reset backup.
3. `hermes_cli/update_cmd_stash.py:82 _stash_local_changes_if_needed` — unconditional `git stash push --include-untracked -m <AUTOSTASH_PREFIX><ts>` whenever `git status --porcelain -z` is non-empty. Layer files are tracked-modified, so they land in this stash.
4. `hermes_cli/update_cmd.py:974–990` — on success the autostash is restored by `_restore_stashed_changes` (default), parked on `--keep-stash`, discarded only on `updates.non_interactive_local_changes=discard`.
5. `hermes_cli/update_cmd_stash.py:432 _restore_stashed_changes` — re-applies the stash and validates the restored Python files (`_validate_python_files_syntax`, `_critical_module_import_failures` before/after); refuses and re-parks on mismatch (`_reject_unsafe_stash_restore`).
6. `hermes_cli/update_completion.py:38 run_completion` — "imported before the swap, executed by path from the selected tree afterward"; spawns a fresh `python -I -S -u` against `<new tree>/hermes_cli/update_completion.py`. PM is initialised from the new tree (`_prepare` at line 135 imports `pm`, `hermes_cli.venv_sync`, `hermes_cli.source_completion`, `hermes_cli.update_cmd`, `hermes_cli.update_cmd_config` — all from the new checkout).
7. `hermes_cli/update_completion.py:172 _complete_selected` — calls `complete_source_checkout(...)`; on success `record_stage("build", "success")` and `clear_completion(root)`.
8. Gateway resume: `hermes update` pauses gateways via socket ACK (observed in nightly log 30.09: "1 gateway(s) ACKed socket pause; waiting up to 10s for graceful exit; Force-stopped 1 gateway process(es)") and restarts them itself; our `nightly_update.sh` then re-verifies health via `nightly_update_gateway.ps1`.

Dirty/stashed layer survival across a fresh post-swap interpreter:
- The 43 layer paths are TRACKED files in the official tree. None of the paths the layer modifies are touched by `update_cmd.py`, `update_completion.py`, `update_cmd_stash.py`, `update_cmd_windows.py`, `update_cmd_fleet*.py` (`git diff f81bb4c4..e5a6fbf8 -- 'hermes_cli/update*'` returns empty). So the update pipeline itself is stock.
- A native `hermes update` against the layer-applied working tree hits step 3 → 4 → 5 unconditionally: layer ends up in the autostash, gets re-applied on the new HEAD, syntax/import-validated, and the stash is dropped on success. The fresh post-swap interpreter (step 6/7) only sees the new tree AFTER the stash restore has already run on the parent side (stash restore is in `_update_via_git_with_autostash`, which executes in the pre-swap interpreter before `run_completion` is spawned). PM and `complete_source_checkout` import from the new tree but do not consult layer files unless those files are physically present — which the just-restored autostash guarantees.
- Conclusion: a dirty/stashed layer DOES survive a fresh post-swap interpreter through the native autostash path, PROVIDED the restore validates clean. If `_restore_stashed_changes` rejects (syntax, import failure, untracked-collision), the stash is parked with an explicit `⚠ Local changes preserved in stash` notice and the update ends partial / non-zero (`_unrestored_autostash_notice`, update_cmd.py:739). This is the correct failure mode.
- Acceptance 2 evidence gate: PM-side tests alone cannot prove persistence — the conclusion above is anchored in stock source functions (file:line above), not in test runs.

## 3. Verify update-related fleet patches vs current official source (isolated)

Isolated worktrees created (no live edits):
- `C:/Users/max/AppData/Local/hermes/profiles/operations/cache/scratch/audit-layer-tip` @ e5a6fbf8 (detached)
- `C:/Users/max/AppData/Local/hermes/profiles/operations/cache/scratch/audit-official` @ bda33b60 (detached)

Required bounded tests per spec (test_update_completion_process.py, test_update_completion_routing.py, test_update_fleet_completion.py, test_update_launch_completion.py), pytest interpreter `C:/Users/max/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe` (3.11.16):

| Tree | HERMES_HOME | Result | Evidence |
|---|---|---|---|
| audit-layer-tip (e5a6fbf8) | unset (inherited scratch) | 17 failed / 43 passed / 3 skipped — every failure is `tests/home_io_guard.py:123 AssertionError: TEST BUG: file I/O against the REAL hermes home: C:\\…\\cache\\scratch\\manifest.json` | scratch/layer-tip-pytest.log |
| audit-layer-tip (e5a6fbf8) | isolated `audit-hermes-home` | 17 failed / 43 passed / 3 skipped — same guard fires on the *interpreter* path `…/hermes-agent/.hermes-runtime/python/generation-…/cpython-3.11-…/Lib/…` | scratch/layer-tip-pytest2.log |
| audit-official (bda33b60) | unset / isolated / layer-tip PYTHONPATH | identical guard aborts at session setup; teardown raises `KeyError: <_pytest.stash.StashKey …>` because the first failure interrupted fixture setup | scratch/official-pytest.log, official-pytest3.log |

Root cause of the failures is the test-side home_io_guard (older copy at official, refined copy at layer-tip adds `sys.base_prefix` lexical/resolved to `_INTERPRETER_PREFIXES`, lines 14–21) tripping on the host's runtime layout: the venv interpreter resolves stdlib paths inside `C:/Users/max/AppData/Local/hermes/hermes-agent/.hermes-runtime/python/…`, which IS under the real Hermes home, so every `pathlib.stat` / `linecache` call inside pytest's own traceback formatting refuses. Operator guidance (mid-run note): these baseline failures are test-home-guard noise, not app defects; do not treat as evidence against the layer. No further probing of this guard was done, per the steer.

Per-file patch applicability vs official HEAD bda33b60 (git diff bda33b60 e5a6fbf8 -- <file>):
- gateway/kanban_watchers_dispatcher.py — required, +36/−1 vs official (PermissionError streak alert, #t_baed78d9).
- gateway/kanban_watchers.py — required, +122/−0 vs official (watcher-side escalation surfacing).
- hermes_cli/gateway.py — required, substantial divergence (333 lines changed vs official: PM env on Windows fix + orphan venv labels + subsequent upstream moves). Needs rebase-on-current-HEAD review before re-application; not a clean apply.
- hermes_cli/kanban_db_dispatch.py — required, +104/−… vs official (substantial drift; rebase-needed).
- tools/kanban_tools*.py, hermes_cli/kanban*.py, toolsets.py — required, all diverged vs official HEAD (official has moved on these files since f81bb4c4).
- update_cmd.py, update_completion.py, update_cmd_stash.py, update_cmd_windows.py, update_cmd_fleet*.py — untouched by the layer: nothing to reapply, no obsolete update-side patches.

Aggregate drift signal: `git diff --stat bda33b60 e5a6fbf8` → 2831 files changed, 61818 insertions, 233294 deletions. That is dominated by upstream movement (official advanced from f81bb4c4 → bda33b60); layer-only content is the 43-file set enumerated above.

## 4. Scheduled update/layer tasks (read-only inventory)

Live Task Scheduler state (schtasks /query, no edits, no invocations):

| Task | Schedule | Command | Last run | Last result | Next run |
|---|---|---|---|---|---|
| HermesNightlyUpdate | daily 04:00 (since 18.09.2026) | `"C:\\Users\\max\\AppData\\Local\\hermes\\scripts\\nightly_update.cmd"` | 30.09.2026 04:00:01 | 1 | 01.10.2026 04:00:00 |
| HermesOurLayerPark | daily 03:55 (since 19.09.2026) | `powershell -File C:\\…\\deploy\\our-layer\\park_our_layer.ps1` | 30.09.2026 03:55:01 | 0 | 01.10.2026 03:55:00 |
| HermesOurLayerApply | daily 05:00 (since 19.09.2026) | `powershell -File C:\\…\\deploy\\our-layer\\apply_our_layer.ps1` | 30.09.2026 05:00:01 | 0 | 01.10.2026 05:00:00 |
| HermesFleetPatchApply | daily 04:20 (since 19.09.2026) — DISABLED (⪫祭) | `bash -c "…/fleet-patch-layer/postupdate-apply.sh"` | 22.09.2026 04:20:01 | 0 | N/A (disabled) |
| HermesLayerApplyNow | one-shot 25.09 16:17 (disabled) | same apply_our_layer.ps1 | n/a | n/a | N/A |
| HermesOfficialBaseActivation | one-shot 13.09 22:57 (disabled) | `…/activate-official-b927.ps1` | n/a | n/a | N/A |
| HermesOfficialRuntimeInstall | one-shot 13.09 23:00 (disabled) | `…/install-official-runtime.ps1` | n/a | n/a | N/A |
| HermesUICacheResetOnce | one-shot 30.08 23:59 (disabled) | `venv\\Scripts\\python.exe …\\Temp\\hermes-ui-cache-reset.py` | n/a | n/a | N/A |
| HermesPoolSyncIslands | one-shot 20.09 17:37 (disabled) | `venv\\Scripts\\python.exe …\\pool_sync_islands_20260919.py` | n/a | n/a | N/A |
| HermesSoakCollect | daily 06:00 (since 19.09.2026) | `powershell -File …\\deploy\\our-layer\\collect_soak_day.ps1` | n/a | n/a | 01.10.2026 06:00:00 |

No competing updater: HermesFleetPatchApply (the older `fleet-patch-layer/postupdate-apply.sh` line) is DISABLED — its log ends 22.09.2026 ("DONE: layer applied, gateway restarted") and was superseded by the our-layer line. The active loop is exactly NightlyUpdate(04:00) → OurLayerApply(05:00) → SoakCollect(06:00), with OurLayerPark(03:55) parking the layer before the nightly.

Ownership/lock correlation:
- park-result.log 30.09 03:55:03 — `parked OK: stash 9870b6d60132…; tree pristine; HEAD unchanged 31c5d57ec6…` (`deploy/our-layer/park-result.log`).
- apply log 30.09 05:00 (`logs/layer-apply-result.log`): `official HEAD 02e4118110…`, `our branch tip e5a6fbf8…`, `our layer base f81bb4c485…`, `isolated patch preflight PASS`, `taskkill gateway pid 13432`, `our layer applied over official HEAD (dirty tree; main untouched)`, `readback OK (drift 1745 official commits): all 43 patch files applied`, `plugin already at 4908dd4d1d01…`, `gateway relaunched via VBS … Hermes_Gateway.vbs`, `imports OK (lifecycle_metrics + remediation_for)`, `kanban metrics CLI live`, `canary interpreter: PM committed …\\installs\\…\\venv\\Scripts\\python.exe`, `live E2E canary PASS`, `consumed stash dropped: stash@{0} (9870b6d6…)`, `=== layer apply complete ===`. Order: park → official update (04:00) → apply → gateway relaunch → canary → stash cleanup. Matches the documented contract.
- Failure-path return-to-service: apply_our_layer.ps1 §7 — on official-behind / failure it restores the PARKED layer from `park-result.json` so the fleet is not left bare, and exits fail-loud.
- Env/profile pin isolation: apply runs outside any Hermes process (Task Scheduler, powershell -NoProfile -File), so the live-checkout write guard refuses in-process rewrites by design. apply_our_layer.ps1 §"Must run OUTSIDE any Hermes process".
- Stash/backup: park creates a timestamped stash per day; apply drops the consumed stash on success; native update_cmd creates `refs/hermes-update-backups/<kind>-…-<pre12>` rescue refs before any reset --hard (update_cmd.py:815) plus 9 leftover autostash entries from earlier updates remain in the live repo (nightly log 30.09 lists stash@{10}..stash@{19}) — see Finding F5.
- Account/session material was not inspected. None of the tasks were invoked.

## 5. Built-in preservation mechanisms — recommendation

Option A — native custom-branch preservation (update_cmd.py:773 `_reconcile_diverged_checkout`). Source proof (local): when HEAD is on a custom branch that is not an ancestor of the update target, the function takes the `merge --no-edit origin/<branch>` path (line 790) and aborts cleanly on conflict (lines 791–795) — local commits survive. On the same branch with proven non-ancestor it parks the old HEAD under `refs/hermes-update-backups/diverged-<branch>-<ts>-<pre12>` before `reset --hard` (lines 801–831). This is exactly the durability primitive the fleet layer needs, and it is stock, maintained upstream, and already wired into both git-pull and zip fallbacks.

Option B — upstream inclusion of the kanban/telegram lane. Correct long-term, but the diff is 3.2k insertions across 18 source files plus 12 test files; upstreaming cadence is slower than the fleet's needs. Keep as the strategic direction, not the mechanism.

Option C — plugin extension path. The fleet-policy plugin already loads this way; the layer's runtime patches are NOT pluginshaped (they edit hermes_cli/gateway/kanban files), so the plugin lane cannot carry them.

Rejected per spec: new updater wrappers, startup monkey-patches, periodic patch injection, swallowing genuine errors. The current park/apply line is explicitly a wrapper around `git diff | apply -3way` and duplicates a stock capability.

RECOMMENDATION: migrate the layer from "park/apply via scheduler" to "managed custom branch + `_reconcile_diverged_checkout`". Concretely: commit the 43-file layer onto a named branch (`company/autocompany-rebased-p0-v5-local` already exists at e5a6fbf8), keep HEAD on that branch, let `hermes update` hit the custom-branch merge path. Rollback: the rescue ref `refs/hermes-update-backups/diverged-…-<pre12>` is created by stock code before any reset. Local fixture/source proof: update_cmd.py:773–838 inspected at bda33b60 (quoted above); not an assertion that an unexecuted real update is stable.

## 6. Host recovery evidence

- Pre-recovery stale PID 18828: absent from `tasklist /FI "PID eq 18828"` ("ᥬ, ⢥騥  , " — no tasks match). Port 8644 refused by anything other than the live gateway: `netstat -ano | grep 8644` shows a single listener `TCP 127.0.0.1:8644 … LISTENING 10928`.
- Live gateway: PID 10928, started 01.10.2026 00:17:54 (Win32_Process CreationDate), parent PID 27384 (already exited — detached VBS launcher, matches `Hermes_Gateway.vbs` relaunch), command line `…\\tools\\python-3.14.7+202****0901-win32-x64\\python.exe -m hermes_cli.main gateway run`. Port 8644 LISTENING owned by 10928.
- `hermes -p default gateway status` exit 0 — "✓ Gateway process running (PID: 10928)" plus per-profile webhook URLs for default/company/design/finance/operations/product/qa/research/sales/tech/ux/video-director/video-editor.
- Fresh source SHA: `gateway_state.json` reports `"code_sha":"bda33b601d194fb8a43e5660c57542aad14aa372"`, `"code_version":"0.21.5"`, `"gateway_state":"running"`, `"served_profiles":[13 profiles]`, `"company:telegram":{"state":"connected","writer_pid":10928,"updated_at":"2026-09-30T21:19:43Z"}`.
- Connected company Telegram: as above (state connected, writer_pid 10928 == gateway pid, fresh updated_at).
- Spawned producer task: this card t_8bcfc1fc was claimed by lock `laptop:10928` at run_id 1893 (kanban_events 'claimed' payload), and `spawned` event pid 27000 recorded — dispatch through the recovered gateway is proven by the producer's own event trail, not by a PID alone.
- Existing infra-kill requeue work t_1b5e3e56 is a separate tracked fix; not duplicated, not claimed released here.

## 7. Remediation and kill criteria for the next code/activation card

Defects (numbered, concrete):

F1. NightlyUpdate gateway-health check false-negatives. `nightly_update_gateway.ps1:24` invokes `hermes --profile default gateway start` and pipes stderr through PowerShell 5.1's `$ErrorActionPreference='Stop'`; benign Python warnings (`Config ref '${env:...KEN}'`) become NativeCommandError, the script throws, and the nightly records `update rc=1` on 28/29/30.09 even though the gateway recovers (gateway_state.json shows running + telegram connected by 21:19 same day). Three consecutive false-failure nights. Fix: in nightly_update_gateway.ps1 either set `$ErrorActionPreference='Continue'` around the `& $hermes …` call, or detect health purely via `gateway_state.json` (`pid` alive + `gateway_state -eq 'running'` + `platforms.'company:telegram'.state -eq 'connected'`) without invoking `gateway start` when the pid is already alive.

F2. HermesNightlyUpdate task `Last Result = 1` persists into 30.09. Direct consequence of F1 (script exits 1 on the false-negative). Resolves once F1 lands.

F3. HermesFleetPatchApply (postupdate-apply.sh, 04:20) is disabled but still registered. The our-layer line superseded it on 22.09; leaving the disabled task in place invites an accidental re-enable that would double-apply patches on top of apply_our_layer.ps1 (postupdate-apply.sh:30 calls `hermes.exe gateway restart` itself — two gateway restarts inside one window). Kill: unregister the task (state-changing → separate card), or convert it to a no-op guard that exits 0 when `apply_our_layer.ps1`'s marker exists. Not done here (read-only card).

F4. Layer branch base is 1,745+ official commits behind HEAD (apply log 30.09: `drift 1745 official commits`). Each nightly apply re-3ways the 43-file patch set onto a moving target; conflicts will eventually land (already happened once: postupdate-apply.log 22.09 "Applied patch to 'cli.py' with conflicts"). Mitigation: scheduled rebase of `company/autocompany-rebased-p0-v5-local` onto current official main (e.g. weekly, or wired into the park step), OR move to the custom-branch preservation path in §5 Option A which merges upstream into the layer branch instead of re-applying a diff.

F5. 9 orphaned update autostash entries older than 7 days in the live repo (nightly log 30.09 lists stash@{10}..stash@{19}, `hermes-update-autostash-20260829…20260912`). They hold real pre-update local changes; never restored, never dropped. Native `_warn_orphaned_update_autostashes` is doing its job (the warning prints every nightly). Remediation: inventory each entry (`git stash show -p <entry>`), decide restore-or-drop per entry, then `git stash drop`. State-changing → separate card.

F6. Update pipeline test suite is unrunnable from the venv interpreter on this host (tests/home_io_guard.py trips on `…/hermes-agent/.hermes-runtime/python/…/Lib/…` stdlib paths, which sit under the real Hermes home). This blocks base-attribution for any future update-side regression. NOT a defect of the layer — reproduced on a clean official checkout. Remediation options (for the next code card): extend `_INTERPRETER_PREFIXES` to include the resolved `sys.base_prefix` chain on Windows (the layer-tip copy of home_io_guard already does exactly this at lines 14–21 — promote that hunk upstream), or run the bounded update tests from an interpreter whose stdlib is outside the Hermes home.

Kill criteria for the migration in §5 (Option A):
- A custom-branch update against a controlled upstream bump leaves the layer commits present on the branch (verified by `git log origin/main..HEAD` non-empty post-update) AND `run_completion` exits 0 AND the live E2E canary passes on the post-update tree.
- If the custom-branch merge conflicts on any of the 43 layer paths, the update must abort with the stock "Resolve manually" message (update_cmd.py:792–795) and leave the tree untouched — verified by `git status --porcelain` empty and HEAD unchanged.
- If `_reconcile_diverged_checkout` ever takes the reset --hard path while the layer branch is checked out, that is a defect — kill the migration, restore from `refs/hermes-update-backups/diverged-…-<pre12>`, return to park/apply.

Persistence of the PM fix t_91dbfaf5 across the next native source replacement: the fix lives outside the 43-file layer set, so under both the current park/apply contract and the Option A custom-branch contract it rides the same path as the rest of the layer (stash → restore → validate, or branch merge). Its survival is gated by F4 (rebase discipline) and verified by the same `imports OK (lifecycle_metrics + remediation_for)` + `kanban metrics CLI live` + live E2E canary chain the apply step already runs; do not add a separate mechanism for it.

End-to-end acceptance for the migration remains NOT VERIFIED until independent integration tests AND an actual permitted release window demonstrate it. This card was read-only: no backup was taken, no release was activated, no gateway/desktop/scheduler state was changed.

## INVENTORY.json

See `INVENTORY.json` next to this report for the machine-readable enumeration.

## Log evidence

- scratch/layer-tip-pytest.log, scratch/layer-tip-pytest2.log — pytest runs against e5a6fbf8 (home_io_guard aborts; not app defects per operator steer)
- scratch/official-pytest.log, scratch/official-pytest3.log — pytest runs against bda33b60 (same guard abort)
- Live log excerpts quoted inline from `logs/nightly-update.log` (28–30.09), `logs/layer-apply-result.log` (29–30.09), `deploy/our-layer/park-result.log` (23–30.09), `fleet-patch-layer/postupdate-apply.log` (terminal entry 22.09).
