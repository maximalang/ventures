# Rules for agents working under ventures

- Read `README.md`, `PORTFOLIO.md`, `OPERATING_SYSTEM.md`, and `APPROVALS.md` before portfolio work.
- For a registered project, its own `AGENTS.md`/`CLAUDE.md`, `CHARTER.md`, `STATE.md`, and decisions override generic workflow details.
- Never read `.env*`, secrets, dumps, or credential stores. Never expose client/private data.
- Evidence first: no completed claim without command exit code, URL, SHA, file path, or reproducible observation.
- Develop in a scoped task branch. Main/protected merge and deploy are autonomous after the role/evidence gates in `APPROVALS.md`; keep one task to one deliverable.
- Kanban is task truth. Update `STATE.md` only on milestone/gate/state change.
- Respect `APPROVALS.md`; routine decisions stay autonomous, serious escalation tasks remain blocked until the owner decides.
