# SPEC: Hermes desktop restart hygiene (Windows host, DESKTOP)

## Problem (verified 13.10.2026)
- Desktop app (re)start spawns a NEW default multiplexer (`python -m hermes_cli.main gateway run`,
  PID 6488 @ 13.10 11:59) but does NOT terminate previous-generation gateways:
  company gateway PID 14216 (started 12.10 09:50, parent dead) survived the restart.
- Stale gateways keep serving profiles on pre-update code/state. After the 13.10 ~07:07
  runtime tree rebuild, the stale company gateway threw
  `[Errno 2] No such file or directory` on EVERY in-place model switch (5 fails 11:05–11:12)
  and lost pywin32 (concurrent-log-handler fell back to stdlib rotation).
  Fresh processes switch fine (verified by harness).
- `hermes gateway restart` is service-mode only (systemd/launchd) — unavailable in
  Windows host mode. This leak is long-standing: every app restart leaves orphans.

## Deliverable (tech)
1. Extend the orphan watchdog (ram_orphan_cleanup.ps1 v3 or sibling script in the same
   scheduler lane): terminate `python ... -m hermes_cli.main gateway run` processes
   OLDER than the current Hermes desktop app instance start time (grace 300s).
   Log every kill: PID, cmdline tail, age, trigger time.
2. Safety whitelist (never touch): Fleet-Browser CDP 9222, dispatch/task worker pythons
   with live kanban runs, HermesLimitsWidget, service-mode gateways if
   `hermes gateway status` ever reports one.
3. Watchdog-side only. Do NOT patch hermes-agent source (nightly updates overwrite it).

## Acceptance (evidence)
- A1: after an app restart, within the watchdog period there is no `gateway run`
  process older than the new app instance (process table with CreationDate evidence).
- A2: after restart, an in-place model switch in the company desktop chat succeeds
  (log line "Model switched in-place"; zero "In-place model switch failed" ENOENT
  warnings over the following 24h).
- A3: zero kills of healthy processes over 24h (watchdog log audit).

## Anchor
Host: DESKTOP (owner machine, Windows 11). Watchdog lane: ram_orphan_cleanup v3 +
per-tick watchdog (канон ram-and-orphan-audits.md).

## Bans
- No hermes-agent code edits; no kills outside `gateway run` cmdline pattern.
- .ps1 must be ASCII+BOM (MSYS eats $_ in powershell -Command).
- Do not kill the default multiplexer of the CURRENT app generation.
