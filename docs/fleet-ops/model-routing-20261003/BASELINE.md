# BASELINE-20261003 — заморозка стоимости рельсов (фаза A, рельсы v2.2)

**Captured at:** 2026-10-03T19:31:10Z (UTC) = 2026-10-03 22:31:10 RTZ
**Spec:** `SPEC-baseline-freeze.md` (тот же каталог)
**Window:** cumulative boundary snapshot — все счётчики накопительные, граница «ДО» любых изменений программы «Рельсы v2.2».

## Метод (точные команды)

Read-only срез `session_model_usage` в 13 профилях Hermes.

Скрипт: `snapshot_baseline.py` (сохранён в workspace kanban-карты t_370d8c6a; копия логики приведена ниже).

1. Список профилей: company, tech, ux, video-editor, qa, research, finance, operations, product, design, sales, video-director, default.
2. Путь state.db: `C:/Users/max/AppData/Local/hermes/profiles/<profile>/state.db`, для default — `C:/Users/max/AppData/Local/hermes/state.db`.
3. Открытие строго read-only через URI:
   `sqlite3.connect(f"file:{path}?mode=ro&immutable=0", uri=True)`
4. SQL (по каждому профилю):
   ```sql
   SELECT model, billing_provider, billing_mode, cost_status,
          COALESCE(SUM(input_tokens),0),
          COALESCE(SUM(output_tokens),0),
          COALESCE(SUM(cache_read_tokens),0),
          COALESCE(SUM(reasoning_tokens),0),
          COALESCE(SUM(estimated_cost_usd),0),
          COALESCE(SUM(actual_cost_usd),0),
          COUNT(*)
   FROM session_model_usage
   GROUP BY model, billing_provider, billing_mode, cost_status
   ```
5. Обзор за 7 суток: `hermes insights --days 7` (rc=0, вывод 89 строк, сохранён в workspace). Insights агрегирует только профиль вызывающего (operations) — используется как sanity-check, не как источник fleet-wide цифр.
6. Kanban 7d (fleet-ops, portfolio): `hermes kanban --board <b> list --status done|blocked --archived --json` в дочернем процессе без унаследованных `HERMES_KANBAN_DB/HERMES_KANBAN_BOARD/HERMES_KANBAN_TASK/HERMES_KANBAN_WORKSPACE/HERMES_DELEGATED_CHILD_CONTEXT`. Прямой sqlite к kanban.db запрещён fleet-policy.

## Итоговые числа (совпадают с BASELINE-20261003.json)

| Метрика | Значение |
|---|---|
| Профилей покрыто | **13 / 13** (errors = 0) |
| Суммарный input | **1,076,113,466** токенов |
| Суммарный output | **194,085,521** токенов |
| Суммарный calls | **5,594** |
| captured_at | 2026-10-03T19:31:10Z |

### Per-profile totals

| Profile | Input | Output | Calls |
|---|---:|---:|---:|
| company        | 528,615,416 | 87,622,944 | 1,591 |
| tech           | 170,385,725 | 53,267,393 |   968 |
| default        | 128,474,587 |  8,553,867 |   343 |
| qa             | 125,506,015 | 22,912,776 | 1,506 |
| operations     |  54,737,728 | 10,100,844 |   678 |
| research       |  28,973,841 |  2,973,792 |   228 |
| video-editor   |  12,071,076 |  5,810,560 |    61 |
| product        |  10,716,046 |    897,969 |    75 |
| video-director |   7,831,241 |    543,808 |    40 |
| finance        |   4,464,786 |    648,803 |    49 |
| design         |   2,687,881 |    461,379 |    30 |
| ux             |   1,320,493 |    264,506 |    16 |
| sales          |     328,631 |     26,880 |     9 |

### Топ-5 моделей (по сумме input+output)

| Модель | Input | Output | Calls | Рельсы |
|---|---:|---:|---:|---|
| qwen3.8-max      | 461,914,183 | 137,010,063 | 2,080 | custom, unknown |
| glm-5.3-flash    | 166,240,210 |  24,727,268 | 1,176 | zai, unknown |
| gpt-5.6-sol      | 131,296,113 |   6,053,012 |   298 | openai-codex, unknown |
| stealth/ox-alpha |  80,713,816 |   4,500,783 |    82 | openrouter, unknown |
| kimi-k3          |  60,706,149 |   4,739,886 |   570 | custom, unknown |

## Блок 1. Подписочные (квотные) рельсы — `included` / `subscription_included`

Это **НЕ «бесплатно»** — это предоплаченная квота, реальный расход.

| Rail | Input | Output | Calls |
|---|---:|---:|---:|
| openai-codex \| subscription_included \| included | 243,345,076 | 12,178,015 | 638 |
| custom \| subscription_included \| unknown         |  18,859,566 |  2,602,252 |  44 |
| openrouter \| subscription_included \| unknown     |   3,624,818 |    177,301 |   8 |
| zai \| subscription_included \| unknown            |   2,363,380 |    213,969 |  12 |
| openrouter \| subscription_included \| estimated   |     189,545 |     17,025 |   2 |
| opencode-zen \| subscription_included \| unknown   |     185,562 |      2,487 |   2 |
| kilocode \| subscription_included \| unknown       |      85,621 |      2,440 |   1 |
| **Итого квота** | **268,653,568** | **15,204,529** | **707** |

## Блок 2. Платные ₽/$-рельсы и прочие (без `included`)

Цены на момент среза в JSON — `estimated_cost_usd` / `actual_cost_usd` (где провайдер их отдал). Где цены нет — null / 0.0000 (не выдумываем).

| Rail | Input | Output | Calls | Σ cost_usd |
|---|---:|---:|---:|---:|
| custom \| unknown \| unknown                       | 455,622,075 | 125,269,141 | 2,542 | 0.0000 |
| zai \| unknown \| unknown                          | 176,953,989 |  30,624,737 | 1,764 | 0.0000 |
| openrouter \| unknown \| unknown                   |  68,300,257 |   3,613,793 |    63 | 0.0401 |
| custom \| chat_completions \| unknown              |  43,910,354 |  11,815,259 |    74 | 0.0000 |
| zai \| chat_completions \| unknown                 |  24,322,511 |   2,334,748 |    41 | 0.0000 |
| custom \| codex_responses \| unknown               |  10,940,753 |   2,196,479 |    15 | 0.0000 |
| openrouter \| chat_completions \| unknown          |   7,572,706 |     484,541 |     7 | 0.0000 |
| openai-codex \| unknown \| unknown                 |   5,962,016 |   1,320,220 |   189 | 0.0000 |
| openrouter \| unknown \| estimated                 |   5,742,248 |     461,087 |    28 | 0.2136 |
| opencode-zen \| unknown \| unknown                 |   1,116,771 |      11,860 |    13 | 0.0000 |
| zai \| codex_responses \| unknown                  |     701,552 |      49,077 |     3 | 0.0000 |
| kilocode (3 подрельсы)                             |     437,994 |       7,702 |    14 | 0.0000 |
| moa \| unknown \| unknown                          |      26,727 |       2,300 |     1 | 0.0019 |
| groq \| unknown \| unknown                         |       4,345 |         194 |    15 | 0.0005 |
| cloudflare, ollama-cloud, opencode-free, copilot, mistral, alibaba, 1, unknown, fallback_chain | <1M combined | — | — | ~0.0000 |
| **Итого платные** | **807,459,898** | **178,880,992** | **4,887** | **≈ 0.2561** |

Большая часть платных рельсов идёт с `cost_usd = 0` — это не «бесплатно», а «провайдер не прислал цену в usage-ответе». Реальные ₽-счета за DashScope / Z.AI / OpenRouter видны только на биллинге провайдера, в БД Hermes их нет.

## Kanban 7d (fleet-ops, portfolio)

| Board | done за 7d | blocked created за 7d | blocked сейчас |
|---|---:|---:|---:|
| fleet-ops | 44 | 33 | 44 |
| portfolio | 0 | 1 | 4 |

Окно: 2026-09-26T22:32Z — 2026-10-03T22:32Z. Метод: `hermes kanban list --status done|blocked --archived --json` (CLI, без прямого sqlite). Limitation: у list API нет `updated_at`, для blocked использован `created_at` как прокси; «blocked сейчас» — моментальный снимок независимо от даты создания.

## Limitations (явные)

1. **reasoning_tokens может уже входить в output_tokens** — поля лежат рядом, **не суммировать**. В JSON приведены отдельно.
2. **`cost_status=included` / 0 USD = подписка (квота), не «бесплатно»**. Реальный расход есть, просто он не в ₽-счете.
3. **insights --days 7** агрегирует только профиль вызывающего (operations); fleet-wide baseline — только `per_profile` в JSON.
4. **kanban_7d blocked** использует `created_at` как прокси (в list API нет `updated_at`); `blocked_currently` — текущий снимок, не окно.
5. **insights cost section**: 1 сессия `included`, 114 `unknown` (нет pricing data) — для рублёвой оценки недостаточно.
6. **Схема БД**: использованы фактические поля `session_model_usage`: `model, billing_provider, billing_mode, cost_status, input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, reasoning_tokens, estimated_cost_usd, actual_cost_usd, first_seen, last_seen, session_id, task, api_call_count, cost_source`.
7. **default** профиль — это `C:/Users/max/AppData/Local/hermes/state.db` (без подкаталога profiles/default).
8. **Live-разрыв при пост-аудите**: срез граничный, флот продолжает писать в state.db после captured_at. При пост-аудите operations показал raw in=54,991,011 vs JSON 54,737,728 (Δ = +253,283 input, +125,975 output, +255 calls) — это ровно сессия kanban-карты t_370d8c6a. Для точной сверки используйте `captured_at` как границу: `WHERE first_seen < captured_at` или сравнивайте снапшоты, снятые в одну секунду.

## Acceptance status

- [x] JSON валиден (`python -m json.tool` exit 0).
- [x] Покрывает все 13 профилей (errors = 0).
- [x] У каждой строки model + рельс (provider|billing_mode|cost_status) + 5 полей (input/output/cache_read/reasoning/calls) + 2 поля стоимости (estimated_cost_usd, actual_cost_usd).
- [x] captured_at присутствует.
- [x] BASELINE.md содержит метод (точные команды), топ-5 моделей, отдельные блоки квота/платные, явные limitations.
- [x] Ноль изменений конфигов / канбана / кронов; gateway не рестартовался; ни одной записи в state.db (только `mode=ro`).

## Rollback

Не требуется — чистое чтение. Файлы `BASELINE-20261003.json` / `BASELINE.md` заменимы, на живые системы влияния ноль.

## Post-audit (для company)

Пересчёт одного профиля на выборке:
```
sqlite3 "file:C:/Users/max/AppData/Local/hermes/profiles/operations/state.db?mode=ro&immutable=0" \
  "SELECT model, billing_provider, billing_mode, cost_status, SUM(input_tokens), SUM(output_tokens), COUNT(*) FROM session_model_usage GROUP BY 1,2,3,4"
```
Сравнить с `per_profile.operations` в JSON — суммы должны сойтись.
