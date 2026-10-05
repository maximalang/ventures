---
name: fleet-token-economy
description: "Use when measuring/cutting fleet token usage."
---
# Fleet Token Economy

Class: diagnose where fleet tokens go and cut consumption without breaking quality gates. Owner prioritizes token economy. Measure first, propose levers with evidence, apply only approved ones, verify after.

## Measure first (never guess)

Never guess — measure. Full commands, caveats and tested SQL for every item: `references/measure-first-details.md` (+ `references/audit-recipes.md`).

1. `hermes insights --days N` — raw input/output tokens, model/platform/tool/skill breakdowns; "Total tokens" includes context re-transmission/cache; frame `subscription_included` as quota/latency, not invoice.
2. `hermes prompt-size --json` — fixed per-prompt budget (system, skills index, memory, profile, tool schemas); every disabled skill shrinks EVERY future prompt.
3. Per-profile `state.db` read-only (`file:...?mode=ro`): `sessions`, `messages.tool_calls`, `session_model_usage` — daily-slice PITFALL (cumulative rows, new/carry split, provider health from logs) in `references/measure-first-details.md`.
4. `hermes cron list` — `deliver` targets, `last_delivery_error`; `Mode: no-agent` jobs cost zero tokens, agent-mode jobs run a FULL agent turn per fire.
5. **Wasted-turn audit** — repeat loops + error turns via state.db scans: recipes in `references/measure-first-details.md` and `references/audit-recipes.md`.

## Levers (typical impact order)

1. **Session hygiene** — biggest free lever for interactive chats: `/new` after big tasks; archive/delete/prune dead sessions; cron/kanban always start fresh sessions. Per-key pitfalls — incl. UPDATED session_reset / reset-policy-plugin facts and the owner ban on reset-as-economy — in `references/levers-playbook.md`.
2. **MoA fan-out** — each user turn pays reference models + aggregator; real switch is preset-level: `hermes config set moa.presets.default.enabled false` (pitfalls in `references/levers-playbook.md`).
3. **Compression** — `hermes config set compression.protect_last_n / target_ratio / protect_first_n`.
4. **Reasoning effort — ЗАПРЕЩЁННЫЙ рычаг на DashScope-профилях.** Директива владельца (20.09, подтверждена жёстко 22.09): все DashScope-модели (qwen3.8-max, kimi-k3) во всех слотах (main, delegation, ВСЕ auxiliary) = reasoning **max**, «можно не экономить». Никаких max→high/low даунгрейдов на DashScope, включая тривиальные aux (title_generation, memory_query_rewrite и т.п.) — даже когда замеры показывают перерасход. Перед любым предложением по effort — сверить fleet-doctrine «Aux offloads paid rails». Effort-правки допустимы только на GPT-профилях и только с явного одобрения владельца.
5. **Skills index** — disable never-loaded skills via `skills.disabled` (reversible, per-profile scope); measured numbers, quarantine variant and tiering in `references/levers-playbook.md` + `references/mechanics-pitfalls.md`.
6. **Cron delivery targets** — `bot-chat:<profile>` resumes that profile's Bot Chat session and runs a FULL agent turn every fire; drop it when the real channel is Telegram.

Full lever text with every measured number and pitfall: `references/levers-playbook.md`.

## Mechanics & pitfalls — always-on safety subset (full list: `references/mechanics-pitfalls.md`)

- **Config writes:** `patch`/`write_file` on a profile config.yaml is refused by the agent guard — always use `hermes config set key value` via terminal. Take a timestamped backup copy first; verify each value with `hermes config get`.
- **Unknown-key warning matters:** if `hermes config set` says a key is "not recognized", the intended consumer may not read that path — verify in installed source/plugins before claiming the change works.
- **fleet-policy:** direct sqlite reads of kanban.db and the sessions dir are blocked — use `kanban_*` tools and `hermes sessions ...` CLI. Read-only `mode=ro` queries on `state.db` pass.
- **Skill body size is a per-load cost:** keep only always-on rules in SKILL.md, depth in on-demand `references/`; rank skills by weekly injection = loads × chars/4.

## Deep lanes (load the reference on demand)

- **Routing/provider audit safeguards** (catalog vs primary/fallback slots, configured vs effective reasoning, `cost_status` semantics, usage scopes, Windows `where.exe hermes` discovery) → `references/routing-audit-safeguards.md`.
- **From audit to program** (freeze baseline + boundary snapshot of cumulative counters BEFORE levers deploy; per-lever revertible kanban cards; per-profile LOADED readback; weekly no-agent delta cron; money stays `null` without pricing; window-compression procedure) → `references/audit-to-program.md`.
- **Prompt-audit лейн** (канон 25.09: `profiles/company/scripts/prompt_audit.py`, daily no-agent cron `d341b0d4a136`, рубрики P1/P2/P3/P5, anti-noise quantization, P4 false-premise lesson, 25.09 cleaning evidence, consumer cron `9bf1839bf40f`) → `references/prompt-audit-lane.md`.

## Support files

- `references/measure-first-details.md` — full "Measure first" depth: commands, state.db daily-slice PITFALL, wasted-turn audit.
- `references/levers-playbook.md` — full levers depth: session hygiene incl. UPDATED reset-policy facts, MoA, compression, skills-index measurements, cron targets.
- `references/mechanics-pitfalls.md` — full mechanics & pitfalls list incl. UPDATED verify-after-changes rule.
- `references/routing-audit-safeguards.md` — routing/provider audit safeguards.
- `references/audit-to-program.md` — baseline/boundary/program procedure.
- `references/prompt-audit-lane.md` — prompt-audit lane canon (25.09–30.09).
- `references/audit-recipes.md` — exact commands, tested state.db SQL, savings math.
- `references/harness-efficiency.md` — Cursor-style harness-lever mapping with probe/control results (reasoning echo scoping, tool deferral, cache layout, cold-start facts).
- `scripts/skill_usage_audit.py` — cross-profile real skill_view usage audit driving the disable list.
