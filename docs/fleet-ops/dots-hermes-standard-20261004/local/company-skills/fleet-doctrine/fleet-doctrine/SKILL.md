---
name: fleet-doctrine
description: "Use when choosing models or briefing GPT fleet tasks."
---

# Fleet Doctrine — Model Routing
> Extended triggers: Model routing strategy for a multi-model AI fleet. Use when spawning sub-agents, choosing models for scheduled jobs, delegating coding tasks, or deciding which model should handle a task.
Send each task to the model class that fits it; do not silently substitute a weaker or non-independent model to complete a gate. Verify live profile pins before routing.

## Current owner routing (29.09.2026 — overrides dated sections below)
- GPT = brain: `product`/`design`/`sales` use `openai-codex/gpt-6-sol` at max; `video-director` default is `openai-codex/gpt-6-sol` at max (owner decision after an Astra token audit: Astra is consumption-heavy and no public benchmark establishes better short-form hooks/story or retention). Astra max goes per-card pointwise only, for a semantic dead-end / flagship hook decision, with independent verification. `company` interactive/owner-facing brain = `openai-codex/gpt-6.1-sol` (owner decision 02.10 after repeated complaints that Qwen produced overly long, unclear owner-facing text; Sol 6→6.1 migration was owner-sanctioned 29.09). Routine bulk subagents and delegation from company stay `custom/qwen3.8-max`. If plus-pool quota pressure from company interactive use starts starving the QA backup lane, company reports the tradeoff to the owner before any revert. GPT profiles' subagents default to `custom/qwen3.8-max` at max ONLY on an explicit `delegate_task`; direct GPT tool calls do not magically move to DashScope.
- DashScope = hands: `tech`, `ux`, `video-editor` use Qwen for code/data/visual execution; `operations`/`research`/`finance` use Kimi for domain work. Keep hands on DashScope even where a GPT coding benchmark is stronger; the owner explicitly requires the brain/hands split. Do not pin Sol to new tech executor cards.
- `qa` primary remains direct `zai/glm-5.3` max. A single owner-approved main fallback is `openai-codex/gpt-6-sol` max after GLM transport/rate-limit failure; no Kimi automatic main fallback. QA's delegate hands = `custom/kimi-k3` max. For a positive gate, establish the ACTUAL reviewer model and author model from permitted run/evidence; if both are Sol or either unknown, park for another independent model. Protected-main/deploy still require a second independent model on the exact head. Never force inference to trigger fallback on owner accounts.
- Quality-pointwise substitution inside the GPT brain tier (owner directive: Terra where it RAISES quality, Luna where it can REPLACE Sol without quality loss, Astra separately — route by the deliverable's quality, never by price or quota-filling): **Terra 5.6 max** is a candidate over Sol 6 max for financial-disclosure brain-analysis and US legal/tax research (Vals AI head-to-head: Finance Agent v2 54.44 vs 49.05; Legal Research 41.35 vs 28.85; Tax Agent 65.20 vs 53.05). This is NOT evidence over Kimi-finance (Finance Agent parity 54.44 vs 54.36; Kimi ahead on US legal/tax) and does NOT transfer to Russian law/economics — independent `finance` verification still required. **Luna 6 max** may replace Sol only on a narrow, checkable task with a published comparable result showing no degradation (Finance Agent v2 49.87±0.23 vs 49.05±0.58), cross-checked against Terra and the incumbent before assignment; benchmark parity never generalizes to product/creative/code decisions (AA Briefcase 1299 vs Sol 1483). **Astra 6 max** = pointwise adversarial second-eye on high-risk ambiguous decisions and long-horizon agentic tasks (AA-Briefcase 1569>1483, AutomationBench-AA 68%>62% vs Sol) — not a universal video/creative rail. Astra is token-expensive (owner directive: точечно и на реальное качество): give it a short bounded packet — trimmed sources, 2–3 candidates, one concrete deliverable question (e.g. the hook/story delta) — never a long production loop; accept its artifact only with independent QA plus an owner/retention verdict. `video-director` default is Sol max; Astra there is a per-card decision on a semantic dead-end, not a standing pin. Speed/cost are not quality; do not infer a short-form-video winner from a general Intelligence Index.
- Activating any pointwise substitution: per-card override ONLY, on a REAL live card carrying the full contract (deliverable, measurable acceptance, bans, anchor); never bypass the DashScope-hands split. Pin through the session's authorized lifecycle surface — native kanban tools first; the CLI form (`hermes kanban --board <slug> set-model <task_id> <model> --provider openai-codex`, model `none` clears) only where it is the authorized surface, never as a substitute for missing native tools and never from inside a task worker. When every board reads back as one identical db_path or `show` misses a known live id, suspect your own session's ambient `HERMES_KANBAN_DB`/`HERMES_KANBAN_BOARD` pin BEFORE declaring the board broken: a read-only lookup in a child process with exactly those vars stripped and explicit `--board` restores distinct stores and finds the card. Global profile defaults change only by explicit owner decision (config backup + semantic diff + `config check` + readback), never to exercise a model. If no suitable live card exists even after correct readback, record the routing decision + evidence in the dossier and claim ZERO live effect — never manufacture a synthetic card just to exercise a model. After the run verify the card's model/provider override fields AND the actual `session_model_usage` of the natural run, not the profile default. If brain/author and QA-fallback resolve to the same Sol model, a positive QA stamp is forbidden until an independent reviewer on a different model.
- TG chat surface = Qwen (owner directive 30.09): every owner-facing Telegram session runs on the config default `custom/qwen3.8-max`; Sol 6.1 works ONLY under the hood (GPT-profile boards, per-card pins, explicit `delegate_task`, `auxiliary.vision`). A `/model` session override outranks config.yaml AND survives gateway restarts (gateway.log `Rehydrated persisted /model override`), so after any migration verification in a TG chat return the pin with `/model qwen3.8-max` in that same chat — only a user of that chat can run `/model`; an agent cannot inject into another live session, and direct session-store edits are policy-blocked. The config `moa` block is one-shot `/moa` sugar, never a standing chat surface.
- Live change/evidence/rollback record: `C:/Users/max/Desktop/all/tools/workspace/fleet-model-routing/ROLLOUT-20260929.md`. Fallback config readback proves configuration only, not a successful switch; monitor natural QA runs. Older tables and no-QA-fallback rules below are historical where they conflict.
- New major model releases: never attribute the previous version's results or quality claims to the new version, and never auto-re-pin roles on an announcement. Protocol: (1) zero-token catalog-coverage check across all active pool accounts — a stale local models cache is NOT negative evidence of entitlement; (2) a scoped decision on the real task type; (3) verification of the ACTUAL model from `session_model_usage` on natural runs, not the profile default. No paid synthetic probes without separate owner authorization.

## Priority
1. **Opus-class** — judgement, security, high-stakes calls, reviewing others
2. **Coding agent** (Claude Code or Codex) — implementation
3. **Sonnet-class** — routine / scheduled / templated work
4. **Fast generalist** (current GPT or Grok) — speed, second opinions
5. **Dedicated image/video model** — stills and video
6. **Long-context / multimodal** (Gemini-class) — huge docs, mixed media

## Aliases
Treat these as classes, not frozen IDs:

- `opus` → current Opus-class reasoning model
- `sonnet` → current Sonnet-class workhorse
- `codex` → current Codex / coding-agent model
- `gpt` → current GPT-class generalist
- `grok` → current Grok generalist
- `imagine` → current Grok Imagine image/video model
- `gemini` → current Gemini-class long-context / multimodal model

Do not publish or hardcode a dated model ID unless you need a reproducible run.

## Routing

### Opus-class — commander
Main-session judgement, orchestration, security decisions, ambiguous calls,
and review of other models' output. Do not spend it on scheduled jobs,
lookups, or templates.

### Coding agent — implementer
Refactors, features, repo work, PR review, debugging, technical drafting.
Claude Code is a strong default; Codex is the second engine or parallel pair.
Do not use a coding agent for non-coding work.

### Sonnet-class — workhorse
Scheduled jobs, briefings, routine admin, drafts, form letters, anything
repetitive. Default for crons unless the job needs real reasoning.

### Fast generalist — backup
GPT-class or Grok when the first two are busy or you want a cheap second
look: sanity-checks, lightweight review, fast research, drafts.

### Image / video — dedicated model
Use a dedicated image/video model (Grok Imagine is a strong default).
Do not send stills or video to a general chat model, including Gemini,
unless that is all you have.

### Gemini-class — long context
Very long documents and multimodal analysis. Not the default for image
generation.

## Decision flow
1. Routine / scheduled / templated? → **Sonnet-class**
2. Image or video? → **dedicated image/video model**
3. Huge document or mixed media? → **Gemini-class**
4. Coding / repo work? → **coding agent** (second engine if you want a pair)
5. High-stakes, security, or unclear? → **Opus-class**
6. Need a fast extra opinion? → **GPT or Grok**

## Fallback
If a class is missing on your instance, use the closest thing you have.
A finished job on a worse-fit model beats a failed job on the "right" one.

## Historical company-fleet routing (20.09 baseline; 29.09 override above takes precedence)

### Stable defaults

| Profiles | Provider / model | Effective reasoning |
|---|---|---|
| `company`, `tech`, `ux`, `video-editor` | `custom/qwen3.8-max` (DashScope) | max |
| `qa`, `research`, `finance`, `operations` | `custom/kimi-k3` (DashScope) | max |
| `product`, `design`, `sales` | `openai-codex/gpt-5.6-sol` | high |
| `video-director` | `openai-codex/gpt-6-astra` | high |
| `default` | `openai-codex/gpt-5.6-sol` | high |

Hands = DashScope AT MAXIMUM (owner: «можно не экономить, ставить везде max»). Brains = Codex GPT (Sol workhorse; **Astra pinpoint**: video-director primary + alias `astra` (model.aliases.astra) on GPT profiles — use `/model astra` for hero video / flagship product quality moments).

### Benchmark-confirmed qwen/kimi split (CANON 2026-09-24, company decision on public benchmarks — defaults UNCHANGED)

External evidence (Artificial Analysis Index v4.1.1: K3 57 vs Qwen 56, $0.86 vs $1.14/task; LMArena overall 15.09: K3 #8 vs Qwen #17; llm-stats: K3 wins 8 of 11 shared benches) + internal live A/B (02.09: kimi deletes data under conflicting instructions 0/3, qwen preserves 3/3):

- **kimi-k3 strengths**: coding/agentic (Terminal-Bench 2.1 88.3 vs 86.6, DeepSWE, FrontierSWE, SWE Marathon 42.0, coding index 42.3 vs 38.8, Math 40.9 vs 33.4), science reasoning (GPQA Diamond 93.5 vs 92.6, HLE), deep search (BrowseComp 91.2, DeepSearchQA 95.0). **Weaknesses**: hallucination rate 51% (vs 40%), output ~2.5x дороже, data-loss under conflicting format rules (internal).
- **qwen3.8-max strengths**: real occupational tasks (GDPval-AA Elo 1739 vs 1685), desktop/computer-use (OSWorld-Verified 86.1 vs 84.8), perception/vision (PerceptionBench 63.5 vs 58.5, CharXiv-RQ, vision/multimodal indexes), native video input, hallucination 40%, ~2.3x дешевле за токен, data preservation under conflicts.

Routing refinement (profile defaults stay as in the canon table above):

1. **tech**: pure-coding cards (implementation, refactor, debugging, long-horizon repo work — защищены git+CI+QA от data-loss) → pointwise pin `--provider custom --model kimi-k3` (max) при создании карты. Карты с data pipelines/extraction/transforms или риском конфликтных форматов → остаются qwen3.8-max. Правило применяет company при dispatch.
2. **research**: остаётся kimi-k3; каждое факт-утверждение через grounded-citations / пометку «не подтверждено» (51% hallucination rate — внешний верификатор обязателен).
3. **company / ux / video-editor**: остаются qwen3.8-max (judgement=GDPval, визуальная оценка=perception, видео=native multimodal, data preservation в оркестрации).
4. **finance / operations**: остаются kimi-k3 (strict-clean output, tool use, AutomationBench).
5. **delegation/subagents и все aux-слоты**: остаются qwen3.8-max — data preservation важнее 1-пунктной разницы агрегатов; judge-слоты совпадают с GDPval-лидерством qwen.
6. **qa gate**: без изменений — glm-5.3 max primary; kimi-k3 второй независимый verdict на main/deploy (dual verdict 03.09).

Evidence hygiene: независимыми якорями считать ТОЛЬКО Artificial Analysis и LMArena; вендорские таблицы имеют расходящиеся якоря (FrontierSWE, Agents' Last Exam, DeepSWE у Moonshot и Alibaba несопоставимы по шкалам) — на их основе дефолты не переключать.

### GPT-6 family measured vs qwen3.8-max (AA v4.3.2, снято 24.09 с artificialanalysis.ai, max reasoning)

Линейка GPT-6 = Luna/Sol/Astra (Terra в GPT-6 НЕТ — это тир 5.6). Все три в пуле openai-codex (+900k варианты).
- Intelligence Index: Astra 52.7 > Sol 47.5 > Qwen3.8-Max 45.4 > Kimi-K3 43.6 > Luna 37.3 (все на одной шкале v4.3.2; ВАЖНО — старые цифры v4.1.1 «K3 57 vs Qwen 56» НЕ сопоставимы, шкала пересобрана). AA-Briefcase Elo: Qwen 1640 > Astra 1569 > Kimi 1505 > Luna 1299. Omniscience (анти-галлюцинации): Astra 43.4 > Kimi 19.7 > Luna 0.65 (qwen/sol не в выборке).
- GDPval-AA v2.1 Elo (реальные рабочие задачи): Qwen 1668 > Sol 1487 > Luna 1367. AA-Briefcase Elo (агентская knowledge-работа): Qwen 1640 > Astra 1569; для Sol/Luna данных AA нет.
- Coding Agent Index (AA, 22.09): Sol 57, Luna 41; qwen ~39 / kimi ~42 измерены на более ранней версии шкалы — прямое сравнение невалидно, направление: Sol6 заметно впереди в агентском кодинге.
- Cost per II task (API list): Luna $0.07 < Sol $1.06 < Astra $3.26 < Qwen $5.41. Output speed: Luna 132, Sol 104, Astra 52, Qwen 39 tok/s.
- Routing-вывод (company, 24.09, дефолты БЕЗ изменений): company/ux остаются qwen (лидерство в GDPval+Briefcase = проксиметрики оркестрации + data preservation); Sol6 — кандидат для точечного пина на тяжёлые кодинг/tech-карты (сильнее kimi по Coding Agent Index); Luna6 — только дешёвый массовый объём, где качество не критично (индекс НИЖЕ qwen); Astra — уже запинен video-director. Ограничение: GPT-пул = подписочные креды (5 сторов), при объёме риск 429-блэкаута (инцидент 21.09); DashScope-рельса такого капа не имеет.

### Fallback — REMOVED on DashScope profiles (owner decision 2026-09-21)

- **No cross-model fallbacks at all** on the 8 DashScope profiles (company, tech, ux, video-editor, qa, research, finance, operations): `fallback_providers` deleted, aux `fallback_chain` (vision→nemotron free, compression→sol-900k) deleted. Rationale: a silent skip to a weaker/other model is worse than a paused task.
- **Failure behaviour instead**: retries of the SAME model (`agent.api_max_retries`, `auxiliary.transient_retries: 2`), then task pause; notify owner only on prolonged outage. Credential-pool rotation within the same model (openai-codex 5 creds round_robin etc.) is KEPT — key rotation is access resilience, not executor substitution.
- GPT profiles (product/design/sales/video-director) and root default: OUT OF SCOPE per owner — their fallbacks remain untouched.
- If a model is unavailable and the task cannot wait: block/park the card with the exact reason; NEVER treat unavailability as a task defect and NEVER auto-substitute another model mid-task.
- Backup of pre-change configs: `%LOCALAPPDATA%/hermes/config-backups/fallback-removal-20260921-220557/` (8 files). Edit method: text-level block removal → `.tmp` → yaml validation (residual-key walk + invariant snapshot: main/delegation/aux/pool strategies/retries unchanged) → `os.replace`.

### Aux offloads paid rails (owner directive 20.09)

All aux slots except vision/compression = `custom/qwen3.8-max` @ DashScope, reasoning **max**: skills_hub, mcp, triage_specifier, title_generation, curator, review, goal_judge, background_review, approval, kanban_decomposer, tts_audio_tags, monitor, profile_describer, memory_query_rewrite. vision = `openai-codex/gpt-6-luna` low (owner directive 02.10: дешёвый GPT-тир вместо Sol; цель — gpt-free пул free-аккаунтов по spec free-gpt-pool-20260925, t_f9b89160/t_fefc9453; gpt-6-luna vision подтверждён живыми тестами 02.10 на free- и plus-аккаунтах), NO fallback chain on DashScope-8 since 21.09 (silent degradation worse than explicit missing result). DashScope VL model ТЕПЕРЬ ЕСТЬ — `qwen-vl-max` (live-протестирован 02.10; qa vision = custom/qwen-vl-max с 01.10 для независимости) — но в fallback-цепи DashScope-8 НЕ ставится (доктрина 21.09). NEMOTRON/openrouter-free НА VISION ЗАПРЕЩЁН ВЛАДЕЛЬЦЕМ (повторно 02.10) — никогда не добавлять. GPT-профили (design/product/sales/video-director) + root: vision fallback_chain = custom/qwen-vl-max (вне scope правила 21.09). compression = `custom/qwen3.8-max` max, NO fallback chain since 21.09 (on failure: preserve original context, pause rather than continue with a corrupted summary). Delegation: provider=custom everywhere, model=qwen3.8-max (qa→kimi-k3, gate independence preserved), reasoning max. MoA disabled (company preset). deepseek remains removed from chains.

### Position provider — DELETED 20.09 (owner)

No `providers.1` blocks anywhere, position-* pool creds removed from company. AgentRouter stays for the nightly review lane only.

### Nightly review lane (cron abafeb3de109 `nightly-fleet-review-opus`)

Schedule **0 6 * * *** (was 02:15), model agentrouter/claude-opus-5 reasoning max. Mode «found — fix now»: BLOCKER/MAJOR with a clear safe fix → fix cards assigned tech/operations/qa (task_type marker in body line 1, evidence gates, acceptance criteria, ≤3/night); MINOR/unclear → «Аудит:» cards to company (≤5/night). Morning check cron 53a32ddc1649 at 09:30 verifies run status + AgentRouter usage + card list.

### Change control (20.09)

- Backups: `%LOCALAPPDATA%/hermes/config-backups/20260920-111743/` (13 configs).
- Bulk edit method: ruamel (python from hermes venv), write to `.tmp` then `os.replace`. NEVER `hermes config set model '<json-dict>'` — the CLI redirects a bare `model` key to `model.default` and the dict lands as a string.
- Verified by readback: 13/13 configs (mains, aux, delegation, fallbacks); cron schedule/prompt updated rc=0.

### GPT-6: рабочий подход к задачам

При подготовке GPT-брифа, контекста или восстановлении незавершённого run загружай `references/gpt6-operating-playbook.md`: чёткое задание и acceptance, дозированный контекст, границы автономности, проверяемое завершение и независимые ветви. В карты передавай только релевантный развёрнутый бриф; модели/effort/пулы/гейты не меняй по статье.
Материал `references/gpt6-sol-opus55-prompting.md` — исторический снимок; его API-рецепты не являются подтверждёнными возможностями текущего Hermes.

## Historical: company-fleet routing (live-verified 2026-08-31, superseded by canon 20.09)

### Stable defaults

| Profiles | Provider / model | Effective reasoning |
|---|---|---|
| `company`, `product`, `sales`, `default` | `openai-codex/gpt-5.6-sol` | max |
| `qa` (quality gate) | direct `zai/glm-5.3` | max |
| `finance`, `operations`, `research` | `custom/kimi-k3` (DashScope) | max |
| `tech`, `design`, `ux` | `custom/qwen3.8-max` (DashScope) | high |

Two-rail model (owner decisions 2026-09-02): **Brain rail** = `gpt-5.6-sol` + `glm-5.3-flash` (direct zai) for orchestration, decisions, review and critical cards (pin via `kanban set-model`). **Hands rail** = DashScope `custom`: `qwen3.8-max` default executor, `kimi-k3` domain workers + first fallback.

**Qwen vs Kimi verdict — Round 2 (4 tasks × 3 reps each, live-verified via session_model_usage, 02.09)**: on conflicting instructions kimi STABLY DELETES the value (0/3 on D3, text:null/empty) while qwen STABLY PRESERVES data in recoverable form (3/3, translit + conflict field) — at the cost of chattiness (1/3 added prose after strict JSON). Owner rule: data loss is worse than sloppy formatting. Therefore: **qwen for data pipelines/extraction/transforms** (tech/design/ux default), **kimi for strict-clean output and domain work** (finance/operations/research); plain extraction is parity (both 6/6 invoices, 5/5 facts, zero fabrications). Round-1 ranking (GLM > kimi > qwen > deepseek on format discipline) is superseded for data-handling roles; GLM remains top overall and holds the qa seat.

**GLM's seat**: glm-5.3-flash is the smartest available model (owner verdict: "GLM очень умный"). It holds a primary role, not just a fallback: default of `qa` (quality/review gate) plus first fallback of the brain profiles.

**glm-5.3 non-flash upgrade (owner-approved 23.09, package A+B+C)**: probe `glm-5.3` via coding-global PASSed (session 20260923_181655_6b677a, billing_provider=zai, 1-token ping). `qa` profile default = `zai/glm-5.3` (reasoning MAX — owner directive 23.09, overrides in qa+company configs); brain fallback and ROOT alias `glm53` unchanged. Quota hygiene: PC-health cron 757bb1078776 moved zai→custom/qwen3.8-max (it was the main weekly-quota burner: 429-storms code 1310 every week); ROOT `openrouter z-ai/glm-5.2:free` zombie removed from fallback (:free models banned by owner). Owner directive 23.09 (second): NO rollback/downgrade to kimi-k3 — qa stays on glm-5.3 max; on quota/limit failure the lane fails loud (retries + pause, no cross-model fallback), recovery = quota reset or owner action. NOTE 21.09 canon table row 125 superseded: qa seat is glm-5.3 (non-flash, max), NOT glm-5.3-flash.

**deepseek-v4-pro-0813**: REMOVED from the fleet entirely (owner directive 03.09, poor probe results). No automatic chains, no pointwise pins — the pointwise pin palette is qwen3.8-max / kimi-k3 / glm-5.3-flash / gpt-5.6-sol only. Deepseek was scrubbed from all 10 profile configs (picker lists + agent.reasoning_overrides).

Compression must stay Hermes STANDARD (`auxiliary.compression.provider: auto` = main model then its fallback) — owner correction 02.09; never pin it to a cheap model by default. Pointwise routing via per-card `--model/--provider` pins (`kanban create --model … --provider custom`, `kanban set-model`), never with new providers.

**Delegation (owner directive 02.09): ALL 10 profiles pin `delegation.provider: custom` + `delegation.model: qwen3.8-max`.** Subagents are executor-hands with a precise spec, and qwen preserves data under conflicting rules — so every subagent runs on qwen regardless of the parent profile. Reasoning-heavy research subagents are pinned pointwise via kanban cards to kimi/glm, never by loosening the global delegation pin.

### Main fallback by provider class

- GPT profile (company/product/sales/default): `zai/glm-5.3-flash` → `custom/kimi-k3`.
- `qa` profile (glm-5.3-flash): `custom/qwen3.8-max` → `custom/kimi-k3`.
- DashScope worker profiles (tech/design/ux): `custom/kimi-k3` (single step; deepseek removed — same endpoint, no redundancy).
- DashScope domain profiles (finance/operations/research): `custom/qwen3.8-max`.
- GPT never sits in worker fallback chains — rail purity (owner-approved 2026-09-02): executor failures must not burn the brain quota. Rollback: `config.yaml.bak-*` per profile.
- No free endpoint or same-provider duplicate belongs in the automatic chain.

### Subagents

- GPT profiles pin `delegation` to `custom/kimi-k3`, reasoning max.
- Direct-GLM and DashScope profiles pin `delegation` to `custom/qwen3.8-max`, reasoning max.
- WHEN to spawn subagents (allowed work, hard limits, forbidden gates) — skill `subagent-economy` (owner decision 03.09; ≤5 per batch, depth 1, material gates never via subagents).
- Explicit provider pins deliberately fail loud and do not inherit the parent fallback chain.
- `deepseek-v4-pro-0813` is max-reasoning task override only for exact code/logic work where its SWE evidence raises quality; never a general default.

### DashScope inventory and provider hygiene

- Canonical route is named `custom` at the DashScope endpoint; original `alibaba` / `alibaba-coding-plan` providers are suppressed, as are zero-balance Novita aliases, across all 10 profiles.
- Live-verified DashScope models include `qwen3.8-max`, `qwen3.8-flash`, `kimi-k3`, `kimi-k2.7-code`, `deepseek-v4-pro`, `deepseek-v4-pro-0813`, `deepseek-v4-flash-0731`, `MiniMax-M2.5`, and `glm-5.2-fast-preview`.
- `glm-5.2` currently returns insufficient-quota; `glm-5.3-flash` is not available on this DashScope endpoint. Direct Z.AI remains the GLM-5.3-Flash rail.
Kilo/OpenCode free models remain specialists for explicit public/sanitize tasks, never global fallbacks. Their catalogs drift and may train on prompts, so verify live availability per task. UPDATE 04.10 (provider registry cleanup, docs: ventures/docs/fleet-ops/provider-cleanup-20261004/PROVIDER-CLEANUP.md): OpenRouter REMOVED — `hermes auth remove` cleared OPENROUTER_API_KEY from runtime .env; RU billing closed since 11.05; free-tier (nemotron) last worked 01.10. Restore = owner re-issues key. OpenCode zen endpoint ALIVE again (catalog 200 on 04.10; was dead 30.08). alibaba*/dashscope-cn/novita* auth shells auto-reseed as logged-out placeholders after `auth remove` (built-in self-heal) — inert, unselectable, suppression markers set; do not fight the healer. Dead openrouter config refs (image_gen recraft, MoA deepseek/claude-opus refs, pool strategy, aux knob) surgically removed from root+12 profiles; root MoA aggregator repointed to openai-codex/gpt-6.1-sol. No working image_gen rail remains. Live-but-unused root providers (catalog 200): groq, mistral, cloudflare.

### Critical-gate dual verdict (owner decision 03.09)

For `release_to_protected_branch` (merge to main) and `deploy_external_runtime` gates, ONE qa verdict is not enough: require a **second independent verdict from a different model** on the same artifact (qa seat = glm; the second reviewer = `kimi-k3` pinned pointwise on the review card). Both must pass before the gate counts. Routine QA (non-main/deploy) stays single-verdict.

`qa` profile delegation is pinned to `custom/kimi-k3` (reasoning max) — NOT qwen — so qa's own subagents never share the executor model the implementers use (owner decision 03.09: gate independence).

### Change control

- Backups: each profile has `config.yaml.bak-model-routing-20260831-230607`.
- Verified: 10/10 functional config audits passed; all gateways running; config mtime+size stable for 60 seconds.
- Compression, curator, MCP and other auxiliary routing remain a separate layer and must not be inferred from this main/delegation map.

### Routing evidence rule

Exit code 0 and a plausible answer do not prove the requested provider answered: automatic fallback can hide provider failure. Verify `session_model_usage` (model + billing_provider) and inspect the exact session-id log entry on mismatch. In the 2026-08-31 audit, several Ollama, Copilot, Kilo, OpenCode, and Z.AI probes returned successful answers actually produced by the custom Qwen fallback.

## Anti-patterns
- Downgrading reasoning_effort anywhere on DashScope profiles/slots — owner invariant (20.09, re-confirmed 22.09): DashScope = max во ВСЕХ слотах, включая тривиальные aux; token-экономия на effort здесь запрещена
- Opus-class on summaries or crons
- Sonnet-class on hard multi-step reasoning
- Coding agent on non-coding work
- Chat model for image/video when a dedicated model exists
- Spawning several models on one task unless you deliberately want a second opinion
- Putting every registered provider into one linear fallback chain
- Treating a credential in `auth list` as proof that the provider is live
- Sending private context to free endpoints whose terms allow prompt training
