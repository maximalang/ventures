---
name: rr-project
description: Shared operating guidance for Recruiter Radar tasks handled by the universal Hermes fleet.
---

# Recruiter Radar project guidance

Read `C:/Users/max/Desktop/all/recruiter-radar/AGENTS.md` and `CLAUDE.md` before work. Preflight the actual worktree, branch, HEAD, repository instructions, and relevant runtime evidence. Develop in `codex/*` and preserve user changes. Run repository-defined checks and independent review. After `gate:ci=pass`, `gate:review=pass`, and `gate:rollback=pass`, merge/push to main is autonomous; deploy additionally requires `gate:qa=pass` and `gate:backup=pass`. Report reproducible evidence.

This file adds only cross-project routing guidance; the Recruiter Radar repository rules remain authoritative and are not duplicated here.

Automatic application is bounded: the fleet-policy plugin injects this guidance when dispatcher metadata says `HERMES_KANBAN_BOARD=rr-team`, or when task project data maps to `recruiter-radar`. Hermes does not dynamically load arbitrary skill packages from task metadata. Explicit task creation with `--skill rr-project` remains preferred.

