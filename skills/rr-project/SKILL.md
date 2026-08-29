---
name: rr-project
description: Shared operating guidance for Recruiter Radar tasks handled by the universal Hermes fleet.
---

# Recruiter Radar project guidance

Read `C:/Users/max/Desktop/all/recruiter-radar/AGENTS.md` and `CLAUDE.md` before work. Preflight the actual worktree, branch, HEAD, repository instructions, and relevant runtime evidence. Work only on `codex/*`; preserve user changes. Run the repository-defined checks, perform review, and report reproducible evidence. After a completed RR task, commit and push its scoped change to `codex/*`. Never push or merge `main`.

This file adds only cross-project routing guidance; the Recruiter Radar repository rules remain authoritative and are not duplicated here.

Automatic application is bounded: the fleet-policy plugin injects this guidance when dispatcher metadata says `HERMES_KANBAN_BOARD=rr-team`, or when task project data maps to `recruiter-radar`. Hermes does not dynamically load arbitrary skill packages from task metadata. Explicit task creation with `--skill rr-project` remains preferred.

