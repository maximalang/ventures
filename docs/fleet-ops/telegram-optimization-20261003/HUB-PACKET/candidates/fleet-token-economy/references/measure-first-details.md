# fleet-token-economy — measure-first depth

> Topic-focused reference — moved from this skill's SKILL.md by hub compaction (t_cef261ac, 2026-10-03, SOURCE-ONLY packet). Original text preserved verbatim.

## Measure first (never guess)

1. `hermes insights --days N` — raw input/output tokens, model/platform/tool/skill breakdowns. Note: "Total tokens" includes context re-transmission/cache and is far larger than raw input+output. Most fleet traffic is usually `subscription_included` (quota/latency, not invoice) — frame savings accordingly.
2. `hermes prompt-size --json` — fixed per-prompt budget: system prompt, skills index, memory, user profile, tool schemas. Every disabled skill shrinks EVERY future prompt.
3. Per-profile `state.db` (read-only `file:...?mode=ro` URI): `sessions`, `messages.tool_calls`, `session_model_usage` (input/output/cache_read per model+billing_mode). Recipes + tested SQL in `references/audit-recipes.md`. PITFALL daily-срезов: строки `session_model_usage` накопительные по (session, model, task), а не дневные — фильтр `last_seen >= day_start` даёт точные ВЫЗОВЫ за день, но токены carryover-сессий (first_seen < сегодня) включают прошлые дни; в отчёте разделяй new/carry и помечай токены как накопительные. Здоровье провайдеров за день — из логов: `grep '<дата>' profiles/*/logs/agent.log | grep 'API call failed'` с разбором `model=`/`error_type=`, а не из БД.
4. `hermes cron list` — check `deliver` targets and `last_delivery_error`; cron deliveries can run full agent turns. Classify by mode: `Mode: no-agent` script jobs cost zero tokens; agent-mode jobs run a FULL agent turn per fire — convert deterministic high-frequency agent jobs to no-agent scripts.
5. **Wasted-turn audit** — two state.db scans insights cannot show: repeat loops (same tool + same normalized args ≥6× inside one session) and error turns (tool results carrying error payloads, classified by distinct pattern per profile). Every loop iteration and error retry re-transmits the whole context. Recipes in `references/audit-recipes.md`.

