# SPEC v3: автороутер — просто и логично (фаза B)

Ревизия 03.10 (вторая коррекция владельца: «более логично и профессионально, главное —
просто и оптимизировано»). Версии v1 (статичная матрица) и v2 (паспорта+скоринг)
ОТМЕНЕНЫ как избыточные; действительна только эта.

Логика одной строкой: **задача → класс → упорядоченный список моделей → первый
подходящий; неудача/блок → шаг вправо по списку** (явный пер-картовый пин с причиной).
Производственный стандарт ordered preference lists: объяснимо, детерминировано,
0 токенов на решение.

Исполнитель: tech (дефолт профиля, пин не нужен). QA: карта-потомок, §QA ниже.
Родитель: `ventures/docs/fleet-ops/model-routing-20261003/PROGRAM.md` (v2.2) —
прочитать первым.

## Deliverable 1: profiles/company/scripts/model_router.py

ОДИН файл, stdlib, 0 сети, 0 LLM, 0 pip, ≤250 строк. Единый источник правды — словарь
ROUTES внутри скрипта. Внешних файлов данных и фикстур НЕТ (кейсы selftest встроены).

Классы и списки (порядок = предпочтение; каждое обоснование — число канона):
- code (чистый кодинг): [custom/kimi-k3 (Terminal-Bench 88.3), custom/qwen3.8-max (86.6)]
- data (пайплайны/файлы/миграции): [custom/qwen3.8-max (data-preservation 3/3), custom/kimi-k3 (0/3)]
- research: [custom/kimi-k3, custom/qwen3.8-max] (галлюцинации 51%/40% → паттерн требует источников)
- ops: [custom/kimi-k3, custom/qwen3.8-max]
- review: [zai/glm-5.3, openai-codex/gpt-6.1-sol]
- strategic (owner-facing, портфель, protected): [openai-codex/gpt-6.1-sol, openai-codex/gpt-6-astra]
- vision: [custom/qwen-vl-max, openai-codex/gpt-6-luna (low)]

Жёсткие правила (немного, поверх списков, применяются до выбора):
1. task_type=review → из списка исключается author_model.
2. owner_facing=true или protected (main/deploy/publish в title/body) → класс strategic.
3. needs_vision=true → класс vision.
4. prior_run_failed=true → выбрать СЛЕДУЮЩИЙ элемент списка (эскалация одним шагом).
5. Спорный класс (нет маркеров) → устойчивый маппинг task_type→класс (research→research, ops→ops, code→code/data по ключевым словам файлов, review→review).

PATTERNS-словарь: на каждую модель 3–5 строк — «как брифить / что потребовать строго /
страховка / анти-паттерн» (kimi: источники обязательны, числа только с URL; qwen:
жёсткий формат, запрет уничтожения данных, краткость; glm: структура вердикта по
пунктам; sol: короткий ясный текст, только суть; astra: только узкий пакет, без
развернутых исследований; qwen-vl-max: без reasoning_effort, вопросы по одному
изображению; luna: массовые простые просмотры). Паттерн выдаётся в выводе ЦЕЛИКОМ —
готовый блок для вставки в спецификацию.

CLI: `--card file.json` (поля: title, body, task_type, author_model, needs_vision,
owner_facing, prior_run_failed) → JSON {class, model, provider, reasoning, pattern,
reason, rules_fired}; `--selftest` — 6–8 встроенных кейсов (по одному на правило +
эскалация + спорный класс), таблица pass/fail, exit 0/1; `--print-rules` — печать
человекочитаемой политики (те же данные, без дублирования текста в коде).

## Deliverable 2: ROUTING.md (≤120 строк)

Путь: `ventures/docs/fleet-ops/model-routing-20261003/ROUTING.md`. Человекочитаемая
политика: таблица классов со списками и обоснованием «число+источник»; жёсткие
правила; эскалация (шаг вправо, пин + лог); 5 инвариантов PROGRAM.md v2.2; сжатая
таблица паттернов. Содержание согласовано с `--print-rules` (одни и те же данные).

## Acceptance (измеримое)

- `python model_router.py --selftest` exit 0 (без сети, из любого cwd).
- `wc -l model_router.py` ≤ 250; `grep -iE "requests|urllib|httpx|socket"` — пусто.
- ROUTING.md ≤ 120 строк; каждый порядок в списках имеет обоснование числом канона.
- `--print-rules` вывод согласуется с ROUTING.md.

## Запрещено

- НЕ менять card_readiness.py, dispatcher, конфиги, кроны, доктрину; никаких новых
  рельс/моделей вне списков; никаких live inference; .env*/auth.json не открывать.
- Не выдумывать числа: обоснования только из PROGRAM.md/канона/RESEARCH.md (если
  досье уже готово — свериться).

## §QA (карта-потомок, исполнитель qa — zai/glm-5.3 max)

1. Fresh `--selftest` exit 0, все pass.
2. Правила: review-кейс реально исключает author_model; owner_facing/protected →
   strategic; prior_run_failed → следующий элемент (проверить и самодельным входом,
   файлы не менять); strategic не выбирает дешёвую рельсу первым; data не начинается
   с kimi.
3. Паттерны: есть на каждую модель списков, утверждения обоснованы (выборочно 4).
4. ROUTING.md ↔ --print-rules согласованы; ≤120 строк.
Выход: `VERDICT-MATRIX.md` (PASS/FAIL по пунктам, цитаты; FAIL → нумерованные дефекты,
не чинить). Cost: токены qa (операционка). Kill: невоспроизводимый selftest или
нарушение правила 1/2 → FAIL.
