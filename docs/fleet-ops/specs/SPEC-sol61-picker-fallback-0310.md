# SPEC: gpt-6.1-sol исчезает из пикера моделей после nightly (fallback-синтез без патча)

Дата: 03.10.2026. Автор: company. Board: fleet-ops. Тип: ops (инфраструктура nightly-лейна).

## Симптом (наблюдение владельца)
Модель gpt-6.1-sol (Sol 6.1, канон fleet-doctrine, релиз 29.09) пропала из выбора моделей
в desktop-пикере company-профиля 03.10 вечером.

## Подтверждённая причинная цепь (evidence 03.10, всё read-only)
1. Nightly update 04:00 меняет checkout: `hermes_cli/models.py` mtime 03.10 04:01:17.
   Некommиченный fleet-патч `hermes_cli/codex_models.py` (gpt-6.1-sol в DEFAULT_CODEX_MODELS,
   строка 25, и forward-compat mapping строка 49, «fleet patch 01.10.2026») при этом стирается.
2. Gateway company (PID 25536, `hermes.exe --profile company serve`) стартовал 03.10 04:26:37 —
   импортировал НЕпатченный `codex_models` в память.
3. Nightly apply 05:00 восстановил патч на диске: mtime `hermes_cli/codex_models.py` = 03.10 05:00:05.
   Работающий процесс модуль не перечитывает («source patches only reach the running gateway after restart»).
4. Триггер симптома: оба ключа пула openai-codex в usage-лимите —
   `auth list openai-codex` (20:58): #1 id=8a052d priority=0 rate-limited usage_limit_reached (429, ~1h53m left),
   #2 id=a2662b priority=1 rate-limited usage_limit_reached (429, ~2h6m left).
   Live-каталог недоступен → rebuild пикер-кэша идёт fallback-путём.
5. Fallback-синтез (in-memory DEFAULT без 6.1 + древний CLI-кэш `~/.codex/models_cache.json` от 21.09)
   перезаписал `profiles/company/provider_models_cache.json` с `fallback=True` и хвостом БЕЗ gpt-6.1-sol
   (rebuild 20:56, затем 21:01). Ручная правка кэша от 01.10 была смыта SWR-rebuild — ровно как
   предупреждает урок fleet-model-probing.
6. Company применил экстренную правку 21:10:04 (проверенный рецепт 01.10): slug gpt-6.1-sol вставлен
   первым, fp сохранён, at=now; readback: n=16, first=gpt-6.1-sol, fp_ok=True. Окно свежести 1ч;
   после ~23:00 (снятие 429) live-каталог должен вернуть 6.1 сам.

## Структурный дефект (что чинить)
Порядок nightly-цикла: update(04:00) стирает патч → рестарт gateway(~04:26) с непатченной памятью →
apply(05:00) возвращает патч только на диск. В любом будущем окне 429/недоступности live-каталога
fallback-хвост пикера снова теряет gpt-6.1-sol. Само не рассосётся.

## Deliverable
Механизм (выбор исполнителя в рамках запретов) гарантирующий, что ПОСЛЕ каждого nightly-цикла
fallback-путь пикера company (и в идеале остальных профилей с openai-codex) содержит gpt-6.1-sol.
Варианты-кандидаты (не исчерпывающе): (a) шаг в apply-лейне, после восстановления патча атомарно
правящий provider_models_cache.json (рецепт 01.10: fp сохранить, slug вставить, at=now);
(b) пост-apply reload/рестарт gateway строго в nightly-окно; (c) изменение порядка update/apply.
Правки файлов — только staged: запись в .tmp → полная валидация → os.replace.

## Acceptance (измеримо)
1. Dry-runTonight: локальная проверка механизма на текущих файлах — вывод «до/после»
   (slug-список, at, fallback, fp) без повреждения структуры JSON.
2. После следующего nightly-цикла (04.10, check_at 04.10 06:00): 
   - `git -C C:/Users/max/AppData/Local/hermes/hermes-agent status --short hermes_cli/codex_models.py` → `M` (патч жив), grep показывает строки gpt-6.1-sol (25, 49);
   - если пул в этот момент под 429: свежий rebuild кэша содержит gpt-6.1-sol (показать slug-список + at + fallback flag);
   - если 429 нет: live-каталог содержит gpt-6.1-sol (readback кэша).
3. Таймстемпы: apply-шаг завершён до момента, когда in-memory модуль считается актуальным
   (порядок виден из логов лейна/процессов).
4. Все артефакты — файлы/логи в durable-пути (не scratch), пути в handoff.

## Запреты
- Не запускать `hermes update` вручную (owner boundary v2, human-boundary).
- Не читать/менять auth.json, токены, .env, любые секреты; статус пула — только `auth list` (без значений).
- Никаких платных inference-проб; каталог — только read-only surfaces.
- Не менять состав пулов, маршрутизацию моделей, профили, Fleet Policy.
- Не рестартовать gateway company вне nightly-окна (днём живые сессии владельца).
- Не удалять и не ослаблять существующий патч codex_models.py; не коммитить в upstream без отдельной санкции.
- Не перезаписывать бандлом живой plugin.yaml (рантайм-ключи).

## Anchor
- Checkout: C:/Users/max/AppData/Local/hermes/hermes-agent, HEAD 9aae3c23e2 (02.10 17:08).
- Файл патча: hermes_cli/codex_models.py (uncommitted, mtime 03.10 05:00:05).
- Кэш пикера: C:/Users/max/AppData/Local/hermes/profiles/company/provider_models_cache.json.
- Лейн: скилл hermes-nightly-update-pipeline (rebase 03:40 / park 03:55 / update 04:00 / apply 05:00, v5 02.10).
- Урок-первоисточник: скилл fleet-model-probing, «TG /model picker chain (openai-codex, lesson of 01.10.2026)».

## Owner / next
- Исполнитель: operations. Независимая приёмка: qa (дочерняя карта, parent = ops-карта).
- Решение о механизме и GO: company. Откат: удалить добавленный apply-шаг / вернуть кэш из backup-копии (делать копию перед правкой).
- Бюджет: 0 ₽ (никаких платных вызовов). Kill-criterion: если механизм требует изменения updater-ядра вне fleet-контроля — стоп и эскалация company.
