# Guard: recurrence prevention — worker spawn crash `No module named 'hermes_cli'`

## Контекст (инцидент 25.09.2026, устранён company)
Мультиплексор `gateway run` работает под tools-python 3.14 с cwd = корень hermes-agent. Диспатчер резолвит argv воркера как `[sys.executable, -m, hermes_cli.main]`, потому что `find_spec('hermes_cli')` в самом диспатчере проходит за счёт cwd; воркеры же стартуют в workspace задачи → ModuleNotFoundError → crash → карты авто-блокируются после 2 крашей. Временное лечение (уже внесено и проверено): файл `hermes_agent_source.pth` (одна строка = `C:\Users\max\AppData\Local\hermes\hermes-agent`) в `C:/Users/max/AppData/Local/hermes/tools/python-3.14*/Lib/site-packages/`. **Подтверждено 25.09 21:41: каталог tools-python был пересоздан pristine (pip+README) через ~6 мин после записи .pth — стирание РЕАЛЬНО, триггер не установлен (кандидаты: воркер-бутстрап, official-runtime self-heal); после стирания прошла вторая волна крашей спавна на 4 досках (7 карт, все разблокированы company).** Постоянный слой (внесён company): user env `HERMES_BIN=C:\Users\max\AppData\Local\hermes\hermes-agent\venv\Scripts\hermes.exe` (setx, HKCU\Environment) — `_resolve_hermes_argv` проверяет его ПЕРВЫМ, спавн воркеров уходит на venv-рантайм и не зависит от tools-python; вступает в силу после ближайшего рестарта гейтвея (ночные задачи 04:00/05:00 рестартуют гейтвей).

## Deliverable
1. Скрипт-сторож `guard_worker_runtime.py` (каталог скриптов флота, где лежат аналоги вроде board_topic_router.py):
   - glob находит tools-python (`C:/Users/max/AppData/Local/hermes/tools/python-3.14*/python.exe`) и его site-packages;
   - проверяет наличие и содержимое `hermes_agent_source.pth`; при отсутствии/порче — перезаписывает (атомарно: tmp → os.replace);
   - проверяет `HERMES_BIN` в HKCU\Environment (reg query): при отсутствии — восстанавливает setx на venv `Scripts\hermes.exe` (постоянный слой, переживает стирания tools-python);
   - верификация: из НЕЙТРАЛЬНОГО cwd `<tools-python> -c "import hermes_cli"` exit 0;
   - при неуспехе после самолечения — алерт строго через owner_inbox (маршрут треда 281); успех — только лог.
2. Cron-лейн (no_agent, hourly, deliver local) на этот скрипт — по канону cron-lane-operations.
3. Read-only разбор первопричины: почему мультиплексор стартует под tools-python с cwd=корень (Task Scheduler XML / gateway-service VBS / desktop spawn); есть ли устойчивая альтернатива (HERMES_BIN в окружении сервиса). Выводы — файлом `C:/Users/max/Desktop/all/ventures/docs/fleet-ops/worker-runtime-rootcause-2509.md` (НЕ менять запуск гейтвея, НЕ патчить диспатчер — только документирование рекомендаций для layer/владельца).

## Acceptance (evidence комментарием)
1. Путь скрипта + cron id в комментарии.
2. Синтетический тест самолечения: ПЕРЕД тестом убедиться, что ни на одной доске нет карт в статусе running (`hermes kanban --board <b> list --status running` по всем доскам — пусто); затем временно переименовать .pth → дождаться цикла (или запустить скрипт вручную) → .pth восстановлен, import из нейтрального cwd exit 0. Окно теста — минуты, сразу вернуть в норму.
3. Файл root-cause-разбора существует: путь + краткие выводы в комментарии.

## Запреты
- Не рестартовать гейтвей/мультиплексор (убивает живые сессии; рестарт — только владелец/Task Scheduler).
- Не менять scheduled tasks, gateway-service, исходники диспатчера (`kanban_db_dispatch.py`) — только read-only анализ и рекомендации.
- Не читать .env*/секреты; алерты — только owner_inbox.
- Синтетический тест — только при отсутствии running-карт (иначе воркер в полёте упадёт).

## Инструменты
read_file, search_files, write_file, patch, terminal. execute_code может отсутствовать — вся логика через terminal. Commit-first для скриптов в репо флота; артефакты вне git — точными путями. Файлы, прочитанные при разборе, повторно не перечитывать.
