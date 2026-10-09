Phase A pre-disable state snapshot
Task: t_fa5b7e6e
Operator: operations
Timestamp (UTC): 2026-10-03T08:10:39Z
Host: LAPTOP

Goal: reversibly contain the four unsafe nightly mutators ONLY.
Spec: docs/fleet-ops/hermes-canonical-update-20261003/BRIEF.md (Phase A).

Tasks present (verified via schtasks /query /tn <name> /v /fo LIST):
  1. HermesLayerRebase      State: Ready  Next: 04.10.2026 03:40:00  Cmd: powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\max\AppData\Local\hermes\deploy\our-layer\rebase_layer.ps1
  2. HermesOurLayerPark     State: Ready  Next: 04.10.2026 03:55:00  Cmd: powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\max\AppData\Local\hermes\deploy\our-layer\park_our_layer.ps1
  3. HermesNightlyUpdate    State: Ready  Next: 04.10.2026 04:00:00  Cmd: "C:\Users\max\AppData\Local\hermes\scripts\nightly_update.cmd"
  4. HermesOurLayerApply    State: Ready  Next: 04.10.2026 05:00:00  Cmd: powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\max\AppData\Local\hermes\deploy\our-layer\apply_our_layer.ps1

HermesSoakCollect: read-only, out of containment scope (per BRIEF).

Action plan (reversible):
  - XML exports written to ./phase-a-tasks/<TaskName>.xml
  - sha256 manifest: ./phase-a-tasks/manifest.sha256
  - disable via schtasks /change /tn <name> /disable (no delete, no stop of running apps)
  - readback via schtasks /query /tn <name> /v /fo LIST to confirm Disabled for all four
  - confirm fresh company Telegram writer on current gateway PID 24928 + runtime receipt

## Post-disable readback (verified 2026-10-03T08:11:5xZ)
  1. HermesLayerRebase      Next Run Time: N/A    Status: Disabled
  2. HermesOurLayerPark     Next Run Time: N/A    Status: Disabled
  3. HermesNightlyUpdate    Next Run Time: N/A    Status: Disabled
  4. HermesOurLayerApply    Next Run Time: N/A    Status: Disabled

HermesSoakCollect: untouched (read-only, out of scope).

## Fresh company Telegram writer on current gateway
Source: C:/Users/max/AppData/Local/hermes/gateway_state.json (live)
- gateway PID 24928, gateway_state=running, code_sha=9aae3c23e2c4f39f77d8d54b5e72ba4b90f4ba8f, code_version=0.21.5
- platforms."company:telegram": state=connected, writer_pid=24928, writer_start_time=179099280601, updated_at=2026-10-03T08:09:57.542901+00:00 (fresh, ~2 min before readback)
- served_profiles includes company + 11 others; single multiplex gateway, multiplex_standalone_reason=null

## Official runtime receipt
- Install root C:/Users/max/AppData/Local/hermes/hermes-agent, git HEAD=9aae3c23e2c4f39f77d8d54b5e72ba4b90f4ba8f (matches brief §6 baseline)
- Dirty fleet overlay intact (M agent/auxiliary_client.py, M agent/credential_pool.py, M agent/delegation_context.py, M agent/retry_utils.py, M gateway/kanban_watchers.py, ...), NOT reset
- gateway.lifecycle.json: phase=running, pid=24928, started_at=2026-10-03T02:00:39Z, prior_unclean_exit=true (documented in brief §10)

## Boundaries honoured
- No restart, no update invocation, no force, no stop of running apps/agents
- No task deletion; tasks remain in Task Scheduler with Disabled state
- No changes to live tree, configs, policies, creds, models, pools, state, sessions
- No park/apply/update scripts executed
- Jev paused state preserved; no port 9222 operation

## Rollback
Per task: schtasks /create /tn <name> /xml ./phase-a-tasks/<name>.xml (no force). Or: schtasks /change /tn <name> /enable. No force flags used or needed.

## Next owner
Phase B: tech (t_1dd91b18) — offline clean custom-branch candidate, native update/schedule tests, immutable SHA. No live activation.
