# SPEC: заморозка baseline рельсов (фаза A, fast-lane, строго read-only)

Исполнитель: operations (custom/kimi-k3 max, дефолт профиля). Родитель программы:
`ventures/docs/fleet-ops/model-routing-20261003/PROGRAM.md` — прочитать первым.
Следующий владелец результата: company (пост-аудит контрольной суммой).

ВАЖНО: замер делается ДО любых изменений программы — это граница счётчиков, от неё
будут считаться дельты. Любая конфигурационная правка в этой карте = провал.

## Deliverable

1. `C:/Users/max/Desktop/all/ventures/docs/fleet-ops/model-routing-20261003/BASELINE-20261003.json`
2. `C:/Users/max/Desktop/all/ventures/docs/fleet-ops/model-routing-20261003/BASELINE.md`

## Метод

Профили (13): company, tech, ux, video-editor, qa, research, finance, operations,
product, design, sales, video-director, default.
state.db каждого: `C:/Users/max/AppData/Local/hermes/profiles/<profile>/state.db`,
python stdlib sqlite3, read-only URI `file:...?mode=ro&immutable=0`.

1. Граничный срез (главное): по каждому профилю SELECT из `session_model_usage`
   агрегаты SUM(input_tokens), SUM(output_tokens), SUM(cache_read_tokens),
   SUM(reasoning_tokens), COUNT(*) ГРУППИРОВКА по (model, billing-рельсе/провайдеру,
   cost_status если есть). Счётчики НАКОПИТЕЛЬНЫЕ — срез и есть цель, НЕ делить по дням.
2. `hermes insights --days 7` как обзор (timeout 600s, вывод в файл; если команда
   недоступна/падает — записать limitation и продолжать, срез п.1 самодостаточен).
   CLI: сначала `"$LOCALAPPDATA/hermes/bin/hermes.exe"`, при ошибке запуска —
   `C:/Users/max/AppData/Local/hermes/hermes-agent/venv/Scripts/hermes.exe`.
3. Качественная сторона (опционально, дёшево): через kanban CLI в ДОЧЕРНЕМ процессе
   БЕЗ унаследованных HERMES_KANBAN_DB/HERMES_KANBAN_BOARD и с явным `--board`
   (fleet-ops, portfolio): количество done/blocked карт за 7 суток. Прямой sqlite к
   kanban.db запрещён fleet-policy. Если извлечь дорого — в JSON пишется null с причиной.

JSON-схема: `{"captured_at": iso, "window_note": "cumulative boundary snapshot",
"per_profile": {"<profile>": {"<provider|rail>": {"<model>": {"input": N, "output": N,
"cache_read": N, "reasoning": N, "calls": N}}}}}, "kanban_7d": {...|null}, "limitations": [...]}`.

## Pitfalls (обязательны к соблюдению)

- reasoning_tokens может быть уже включён в output_tokens — поля рядом, НЕ суммировать.
- cost_status=included / 0 USD = подписка (квота), НЕ «бесплатно» — в MD квотные рельсы
  (openai-codex, zai) и платные ₽-рельсы (custom/DashScope, agentrouter) отдельными
  блоками; деньги не выдумывать: где цены нет — null.
- Ключи/секреты (.env, auth.json) не открывать; в JSON только агрегаты токенов.

## Acceptance (измеримое)

- JSON валиден (`python -m json.tool` exit 0), покрывает все 13 профилей, у каждой
  строки model+рельса+5 полей; captured_at присутствует.
- BASELINE.md: метод (точные команды), топ-5 моделей по сумме токенов, блоки
  квота/платные рельсы, limitations явные. Итоговые числа сходятся с JSON (пост-аудит
  company: пересчёт одного профиля на выборке).
- Ноль изменений конфигов/канбана/кронов; gateway не рестартить.

## Cost/kill/rollback

Cost: токены operations (DashScope, операционка). Kill: невозможность прочитать ≥3
профиля state.db → блок с точной ошибкой, не молчаливые дыры. Rollback: файлы
заменимы, влияния на живые системы ноль.
