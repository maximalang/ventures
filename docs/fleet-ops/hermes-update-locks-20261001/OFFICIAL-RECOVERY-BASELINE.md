# Official recovery baseline — Hermes Windows update

## Scope
Owner requested proper repair through official methods. Preserve application data, profiles, source stashes and all independently tracked fleet artifacts. No local updater patches, wrappers, forced integrity acceptance, direct tool-store edits, secret reads or broad process termination.

## Verified live evidence
- Probe time: 2026-10-01 01:51 +03:00.
- Installation: C:/Users/max/AppData/Local/hermes/hermes-agent; method git, branch main.
- Clean source HEAD: bda33b601d194fb8a43e5660c57542aad14aa372.
- `hermes --version`: v0.21.5+4955.gbda33b6; exit 0. Its 'Up to date' text is not an end-to-end installation-health verdict.
- Desktop attempted supported repo handoff at 2026-09-30 22:39 and 22:47 local; both failed with exit 1. Evidence: C:/Users/max/AppData/Local/hermes/logs/desktop.log, lines 23846–24210.
- Preparation failure paths point to locked retired/displaced Git bash.exe and Python libcrypto-3-x64.dll. Evidence: C:/Users/max/AppData/Local/hermes/logs/desktop-update-handoff.log, lines 2391–2571. WinError 5 does not by itself identify the holding process.
- `hermes pm doctor`: exit 1; exact finding `python: realized bytes do not match recorded digest`. Git, node, npm, uv, ripgrep, ffmpeg, Chromium, cua-driver and agent-browser installed checks pass. Optional packages shown 'not installed' are not presumed defects.
- `hermes pm status`: exit 0 returns a FAILED update receipt with exit_code=1. Source apply succeeded, completion did not. The successful command exit is a successful receipt read, not a repaired updater.
- Receipt records pre_update_backup disabled and local changes parked in stash 8ad914efc2c2a47820c41faedcfeb3dfae53efc9. Source stashes remain intact; no stash was applied or removed by this session.

## Supported command discovery
- `hermes pm repair --help`: rebuild the recorded dependency environment without changing its graph. This is not an application update or a blanket reinstall of tool binaries.
- `hermes pm install --help`: named packages; `--tools-only` stops before the dependency-environment sync. Do not use `--trust-recorded` as recovery from a demonstrated digest mismatch.

## Official sources
- https://hermes-agent.nousresearch.com/docs/getting-started/updating
- https://hermes-agent.nousresearch.com/docs/reference/package-management
- https://hermes-agent.nousresearch.com/docs/user-guide/desktop

## Existing work disposition
The isolated candidate on t_91dbfaf5 is not official upstream and has not been activated. t_0ab59219 is candidate-only QA; a scope comment explicitly prohibits treating it as an application repair. Audit t_8bcfc1fc does not prove end-to-end update success. No duplicate candidate implementation is needed for this request.

## Recovery progress (verified 2026-10-01)
- The first full-history archive attempt on D: failed before creation (WinError 5 at the drive-root destination). The owner rejected that enlarged scope; no full archive is to be recreated for this repair.
- A direct official SQLite backup preflight exposed the actual snapshot failure: `database or disk is full`. Company state.db was 5,332,467,712 bytes versus about 2 GB free on C:. This is not evidence of DB corruption.
- After supported gateway stop, `py -3.11 -m pm.cli install python` exited 0 and `pm doctor` exited 0. Do not substitute the earlier failed cleanup result for this successful follow-up.
- Canonical source update completed to clean SHA 12e4d3e2dd5281adf289f70e5d6c7f33427d6982. Receipt remains `partial`: Desktop rebuild was skipped while the application held its files; old serve restart initially failed and the app subsequently respawned a serve backend.
- Vendor scripts/desktop-update/windows.ps1 executed as PID 5972 at 03:17:50 +03:00 with exact Desktop PID 19528. It exited 4 after 30 seconds because the app did not exit. The result file is C:/Users/max/AppData/Local/hermes/.hermes-update-result.json (ok=false, exit_code=4). Graceful CloseMainWindow delivery is not an app-quit verdict.
- Host gateway was restored using the explicit default-profile canonical launcher: exit 0, PID 11600. Do not start a per-profile gateway to avoid the host binding.
- The Jev cron job was paused at 02:40:19 +03:00; verification confirmed enabled=false and no Jev checker / browser launcher / port 9222 process.
- Full Desktop replacement, cold runtime verification and independent QA remain unfinished; the owner-visible app must exit using its supported Quit/Update control. No local updater candidate was activated.

## Acceptance remaining
1. Supported app Quit/Update control actually exits the exact old Desktop process (do not repeat a handoff on a still-live PID).
2. Supported cold Desktop rebuild/replacement and vendor runtime verification succeed.
3. Running Desktop matches the resulting source/build and host gateway remains alive.
4. Independent readback confirms preserved profiles and the Jev check remains disabled before full completion is reported.

## Financial scope
Period: this maintenance request, 2026-10-01. Confirmed revenue/refunds: null (outside scope). Incremental external paid operations: 0 (none issued). New paid commitments: 0 (none issued). Estimated model usage cost: null (not measured). No spending authorized or requested.
