# LINEAGE READBACK — контракт evidence-канала для QA-карт

Статус: введён картой fleet-ops `t_c7b83504` (LINEAGE-CHANNEL), decision:company=go.
Инструмент: `scripts/lineage_readback.py` (read-only, stdlib-only, Python 3.10+).

## Зачем

QA acceptance вида «докажи, какими моделями обслуживалась сессия (serving/aux/compression)»
раньше было НЕЧЕМ доказать разрешёнными каналами:

| Канал | Почему не годится |
|---|---|
| `hermes usage` | только account-лимиты провайдера; для zai/custom — exit 1 «No account usage available» |
| `profiles/*/sessions/**` (дампы транскриптов) | перманентный deny fleet-policy `secret_read_or_write` — и правильно |
| `session_model_usage` | таблица существовала, но CLI/profiles её не обнажали |

`lineage_readback.py` читает РОДНОЙ billing-ledger гейтвея — таблицы `session_model_usage`
и `sessions` внутри `profiles/<p>/state.db` — строго read-only (`sqlite URI mode=ro` +
`PRAGMA query_only=ON`). Ни один защищённый путь не затрагивается.

## Команда (контракт)

```
python scripts/lineage_readback.py <worker_session_id> [--profile <name>] [--json] [--hermes-home <dir>]
```

* `worker_session_id` — например `20260930_120907_35d3ab` (берётся из run-метаданных
  диспетчера/баннера воркера, как и раньше — инструмент лишь ОТВЕЧАЕТ по нему).
* `--json` — машиночитаемый документ `lineage_readback/v1` (рекомендуется для QA-evidence).
* `--profile` — сузить скан до одного профиля (быстрее, детерминированнее).
* `--hermes-home` — явный hermes-home; по умолчанию авто-детект
  (понимает worker-форму `HERMES_HOME=<home>/profiles/<profile>`).

Exit-коды: `0` — сессия найдена, lineage выдан; `2` — сессия не найдена ни в одном
просканированном `state.db`; `3` зарезервирован (нечитаемый state.db отмечается в
`scan_notes`, скан продолжается).

## Интерпретация классов

Класс строится из колонки `task` ledger-а (forward-compatible):

| `task` в ledger | класс | смысл |
|---|---|---|
| `''` (пусто) | `serving` | основной conversation loop воркера |
| `compression` | `compression` | compact/сжатие контекста |
| всё остальное (`title_generation`, `goal_judge`, `vision`, `background_review`, …) | `aux` | вспомогательные вызовы; `task` сохраняется в выводе как subkind |

Поля строки lineage: `model`, `billing_provider`, `billing_base_url`, `billing_mode`,
`api_call_count`, token-итоги (input/output/cache_read/cache_write/reasoning),
`first_seen_iso`/`last_seen_iso` (UTC). `summary` даёт списки моделей по классам —
это и есть ответ на acceptance «линейка моделей serving/aux/compression».

## Как QA-карте доказать item через этот канал

1. Взять `worker_session_id` проверяемого рана.
2. Выполнить команду с `--json`, приложить stdout (или файл) как evidence артефакт.
3. Процитировать в handoff: `summary.serving`, `summary.aux`, `summary.compression`
   и строки lineage с `api_call_count`/таймстемпами.
4. `found=false` (exit 2) — НЕ фальсифицировать: сессия могла быть архивирована/стёрта
   retention-политикой гейтвея; зафиксировать «lineage недоступен по retention», а не
   «моделей не было».

## Гарантии безопасности

* только `mode=ro` SELECT-ы; никаких `-wal`/`-journal` артефактов не создаётся (тест);
* `profiles/*/sessions/**` не читается и не пишется — в тестах canary-файл под этим
  путём остаётся нетронутым;
* колонки с CONTENT сообщений/системных промптов не выбираются — только метаданные;
* auth/секреты не задействованы; вывод — только stdout.

## Проверки

```
python tests/test_lineage_readback.py                                        # из корня репо, stdlib
python -m unittest discover -s tests -p "test_lineage_readback.py" -v        # альтернативная форма
python -m pytest tests/test_lineage_readback.py -v                           # в venv репо, если pytest установлен
```

12 тестов: маппинг классов, ISO-конверсия, found/JSON/human-рендер, metadata сессии,
summary, exit 2 при отсутствии, legacy-схема (без `session_model_usage`), фильтр
профиля, canary `sessions/` не тронут, отсутствие write-артефактов.

## Референс demo (реальные сессии флота, 30.09.2026)

* `20260930_120907_35d3ab` (qa, kanban-ран): serving `glm-5.3/zai` (35 вызовов),
  aux `goal_judge qwen3.8-max/custom` (2), compression — none recorded. exit 0.
* `20260830_020016_9e70c3` (tech, cli): serving `gpt-5.6-terra/openai-codex` +
  `qwen3.8-max/custom`, aux `background_review qwen3.8-max`, compression
  `qwen3.8-max/custom` (15). exit 0.
