# Verified source-Desktop scheduling constraint (addendum to BRIEF)

Anchor: installed official HEAD 9aae3c23e2c4f39f77d8d54b5e72ba4b90f4ba8f. Date/source: 03 October 2026, independent read-only fact collection + company source spot verification + official docs. No updater execution. This is NOT QA or release approval.

## Supported mechanism vs missing automatic Apply
The installed Desktop's passive update poller only runs checkUpdates/checkBackendUpdates: apps/desktop/src/store/updates.ts:1197-1249. Apply uses renderer IPC/control, not that timer. Windows source replacement follows apps/desktop/electron/updater/checkout.ts:354-393: Desktop itself starts official handoff, marks quitting-for-handoff and calls quit. scripts/desktop-update/windows.ps1:1604-1622 waits for the exact Desktop PID, exits 4 if still alive, changes nothing; 1624-1625 explicitly states PM creates a new dependency generation and old Python readers do not block that mechanism. Do NOT reuse legacy venv-holder help text to conclude managed PM always needs process killing.

No unattended/idle Desktop Apply setting/entrypoint was found in the inspected official version. CLI --yes skips prompts; it is not a supported command to make an active Desktop perform its own handoff. Official updating docs distinguish managed-source CLI/update handoff and bundled/MSIX/Store ownership. Do not replace the missing control with direct IPC, simulated GUI clicks, CloseMainWindow, force quit, custom restart wrapper or an updater task racing Desktop.

## Native preservation of intentional custom source
update_cmd.py:1037-1052 honors updates.parked_branch_strategy:update_in_place; 1055-1071 keeps main-target branch policy distinct from release tags. Desktop official handoff targets main/channel main and does not use --switch-branch; windows.ps1:1642-1650 appends --keep-stash (which parks uncommitted edits). Therefore a CLEAN COMMITTED custom branch can be preserved by native handoff. Dirty overlay on main is not the recommended final arrangement. Verified live official docs: https://hermes-agent.nousresearch.com/docs/getting-started/updating (intentional custom branch paragraph).

## Adjusted delivery disposition
Proceed with offline clean immutable custom-branch preservation and native conflict/dirty regression tests. Deliver a minimal supported source-Desktop Check/Apply arrangement and explicit remaining limitation: fully automatic installation while Desktop is left running is NOT demonstrated/supported by the inspected version. No need to author an invented scheduler action. Existing four unsafe schedule jobs stay Disabled. This limitation is not solved by model routing or native task registration and must not be hidden as PASS for the owner's full automatic-update requirement.

Independent QA may accept source-preservation/official-handoff readiness as a scoped increment, but must withhold full unattended auto-update acceptance. Company must decide scoped readiness separately from full request completion and explain the limitation to owner; do not block-loop workers trying to discover a nonexistent command. Switching to Windows packaged distribution is outside the current approved scope and may break custom fleet code, so no MSIX/Store migration without a separate exact compatibility decision.

Facts artifact: C:/Users/max/AppData/Local/hermes/profiles/company/cache/scratch/facts-desktop-update-unattended-apply.md. Critical anchors re-read by company: updates.ts:1193-1237; checkout.ts:354-403; windows.ps1:1600-1651; update_cmd.py:1032-1079. Raw read-only fact summary is not a material evidence gate.

Economics: maintenance-only, this request period, docs/source tools. External paid operations/commitments 0; confirmed revenue/refunds null (out of scope), estimated inference cost null (no metered readback).
