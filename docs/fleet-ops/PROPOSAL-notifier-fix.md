# PROPOSAL: фикс kanban notifier (notify-режим) — t_a362a047

Дата: 2026-09-27. Автор: tech (worker, read-only диагностика).
Карта: t_a362a047 (fleet-ops). Evidence-карта: t_4342c06e.
Runtime: C:\Users\max\AppData\Local\hermes\hermes-agent (gateway исполняется из этого чекаута; текущий процесс с 27.09 12:24:38).

## 1. Резюме

Два независимых дефекта:

1. **Аудит-пробел (подтверждён кодом и логом).** Успешная notify-доставка (passive ping) логируется только на DEBUG; единственная INFO-строка нотифайера — "woke agent" (wake-leg). Все silent-skip пути claim-цепочки — DEBUG или ничего. Поэтому "в gateway.log ноль строк про карту" структурно неизбежно для notify-режима даже при успешной доставке, а инцидент невозможно диагностировать по логу.
2. **Claim-starvation подписок thread-131 (подтверждён данными, механизм статически не воспроизводится).** Подписки t_4342c06e и t_eff9b2e1 (telegram/-1004426332349, topic 131, profile=company, mode=notify) перестали клеймить терминальные события 26.09 между 12:38 (успешный blocked-пинг) и 13:40 (unblocked) и остались замороженными сквозь два рестарта gateway (27.09 10:21:51, 12:24:38), пока тот же процесс успешно клеймил другие подписки (DM wake 13:38/13:48/14:16, группа wake 17:27/17:39 27.09). Главный подозреваемый: **незакоммиченный dirty worktree рантайма** — изменены именно модули claim-стека (см. §5).

## 2. Ключевые факты (evidence)

### 2.1 Подписка t_4342c06e (hermes kanban notify-list --json, fleet-ops, 27.09 ~17:45)

```
task_id=t_4342c06e platform=telegram chat_id=-1004426332349 thread_id=131
chat_type=thread user_id=null notifier_profile=company delivery_mode=notify
delivery_metadata={parent_chat_id: -1004426332349}
created_at=1790412953 (26.09 11:55:53 +0300, через 141с после создания карты)
last_event_id=38955  last_ping_event_id=38955
```

- Карта completed_at=1790430188 = **26.09 16:43:08 +0300** (в тексте карты-задания "~27.09 15:35" — фактическая ошибка на сутки; epoch подтверждён `date -d @1790430188`).
- События карты (hermes kanban show --json): … blocked 26.09 12:38:15 (payload policy_denied), unblocked 13:40:14, promoted 16:28:07, heartbeats 16:28–16:42, attached, **completed 16:43:08**.
- `unblocked` входит в TERMINAL_KINDS: его claim сдвинул бы курсор **без всякой отправки**. Курсор стоит на 38955 ⇒ **ни одного успешного claim этой подписки с 26.09 ~12:38**, включая 5+ часов текущего процесса.

### 2.2 Идентификация события 38955 (арифметика глобального счётчика task_events)

Счётчик id глобальный на board DB (смежность подтверждена: t_0a4a374e completed 27.09 14:16:34 = 39030 — курсор его подписки; t_a362a047 created 27.09 17:30:46 = 39031 — курсор моей подписки при создании).

- t_c87f6555: sub ct=27.09 13:25:28, курсор 38981 ⇒ 38981 @ 27.09 ~13:25.
- 38955 < 38981 ⇒ событие 38955 записано до 27.09 13:25, т.е. 26.09.
- Интервал 38870 (t_eff9b2e1) → 38955 = 85 событий; гипотеза "38955 = completed @16:43" даёт 85 событий за ~4ч13м преимущественно **простой** доски (0.34/мин) — противоречие; гипотеза "38955 = blocked @12:38:15" даёт 85 событий за ~35мин при двух работающих воркерах с heartbeat/60c (~2.4/мин) — **единственная арифметически состоятельная**.
- Вывод: **38955 = blocked-событие 26.09 12:38:15**; completed ≈ 38970–38978 (< 38981 ✓) — **не заклеймлен**. last_ping=38955 ⇒ blocked-пинг "⏸ … FLEET POLICY BLOCKED" был **успешно отправлен** в topic 131 (record_notify_ping пишется только после успешного send) 26.09 ~12:38. Notify-leg тогда работал.

### 2.3 Вторая замороженная подписка — t_eff9b2e1

```
thread_id=131, company, notify, ct=1790412949 (26.09 11:55:49, на 4с раньше)
last_event_id=38870  last_ping_event_id=38870
```
Карта HF-VET: status=done, completed_at=1790415005 = **26.09 12:30:05**. По той же арифметике 38870 ≈ её blocked-пинг ~12:0x; completed (id > 38870) не заклеймлен. Симптом идентичен: **последний успешный пинг — blocked, далее вечная тишина**.

### 2.4 Работающие подписки (тот же процесс, тот же board, тот же профиль)

- t_c87f6555 (DM 1256122537, wake, ct 27.09 13:25): `2026-09-27 13:38:17 INFO gateway.run: kanban notifier: woke agent for t_c87f6555 on telegram/1256122537 profile=company events={'completed'}`.
- t_0a4a374e (DM, wake): woke 13:48:01 {blocked}, 14:16:34 {completed}; курсор 39030 = id completed — **claim+CAS персистнулись корректно**.
- t_0955f6c9 (группа -1004426332349, wake): woke 17:27:02 {block_loop_detected}, 17:39:13 {completed}; подписка затем удалена (unsub по archived — штатно).

### 2.5 Лог gateway (C:\Users\max\AppData\Local\hermes\logs\gateway.log, непрерывен с 21.08, 46 рестартов)

- `grep -c t_4342c06e` = **0**; `t_eff9b2e1` = 0; в desktop.log/agent.log/errors.log/gateway-stdio.log тоже 0.
- Все 104 notifier-строки за период — "woke agent" (INFO). По дням: 22.09=24, 23.09=43, 24.09=28, 25.09=4, 26.09=**0**, 27.09=5(+2 поздних).
- **Ноль** WARNING нотифайера за весь период: ни "send failed", ни "tick failed", ни "unroutable sub", ни "anchorless thread sub" ⇒ ни один failure-путь с логированием не выполнялся; подписки просто не доходят до claim/delivery либо скипаются молча.

### 2.6 Почему "by design" молчат t_eee1848b / t_00c7f2bf

Обе thread-131 notify+wake подписки созданы 26.09 04:09 **после** завершения своих карт (24.09 10:22 и 12:17). `add_notify_sub` стартует курсор caught-up (`last_event_id = MAX(task_events.id WHERE task_id=?)`, "never replays history") ⇒ новых событий нет, доставка не предусмотрена. Не бага; UX-пробел — subscribe не предупреждает, что карта уже терминальна (см. P2).

## 3. Обход silent-путей в коде (почему статика не объясняет starvation)

Путь claim: `gateway/kanban_watchers.py:95 _kanban_notifier_watcher` (tick 5s, sequential deliveries, один catch-all на тик → WARNING "tick failed" — в логе нет) → `gateway/kanban_watchers_notifier.py _Collector.collect_board` → `_claim_for_sub` (строки ~288–311) → `hermes_cli/kanban_db_notify.py claim_unseen_events_for_sub` (CAS внутри BEGIN IMMEDIATE).

Проверенные и **исключённые** тихие скипы для данной подписки:
- Profile-фильтр листа: notifier_profile=company; company-подписки DM/группа тем же процессом листаются и доставляются ⇒ company ∈ notifier_profiles, board листается.
- Platform gate: telegram активен (те же тики).
- Route gate `_adapter_for_subscription`: `multiplex_profiles: true` (config.yaml:598), но **profile_routes отсутствуют** во всех конфигах (default + profiles/*) ⇒ route-цикл пуст; при пустых routes результат функции зависит только от (platform, owner_profile) и **не может различать thread-131 и DM подписки одного профиля**. Trap "second matches() с user_id-дефолтом → silent None" (строки 196–199) недостижим без routes.
- Anchorless-warning: не применим (parent_chat_id в metadata есть) — потому и молчит.
- Send-failure/rewind: всегда WARNING с task_id + rewind CAS — ноль в логе, курсор не двигался.
- present_notification (gateway/warning_notifications.py): глушит только **diagnostic** пинги при suppress_warning_notifications; completed — не diagnostic, gate не применим. К тому же подавление не объясняет не-claim немого unblocked.
- Конкурирующий процесс/DB-сплит: исключён — строки подписок t_c87f6555/t_0a4a374e (созданы 27.09 gateway-процессом) и продвинутый курсор 39030 видны в той же реальной DB, которую читал CLI.
- GC/purge (30 дней), unsub-по-архиву, MAX_SEND_FAILURES(12): не срабатывали (строки на месте, WARNING-ов нет).

Вывод: по **чистому** коду (`kanban_watchers_notifier.py`, `kanban_db_notify.py` — оба clean в git status) подписка обязана клеймиться каждый тик. Наблюдаемое противоположно ⇒ расхождение между читаемым кодом и фактическим поведением лежит в **изменённых зависимостях или ненаблюдаемом состоянии**.

## 4. Dirty worktree рантайма (главный подозреваемый)

`git status --porcelain` в C:\Users\max\AppData\Local\hermes\hermes-agent (HEAD f81bb4c485):

```
M  gateway/kanban_watchers.py            <- watcher-цикл нотифайера
M  gateway/kanban_watchers_dispatcher.py
M  gateway/run.py
M  hermes_cli/kanban_db.py               <- connect/Event/write_txn/boards — ядро claim-пути
M  hermes_cli/kanban_db_connect.py       <- резолвинг board DB
M  hermes_cli/kanban_db_dispatch.py
M  hermes_cli/kanban.py / commands.py / gateway.py / kanban_parser.py / kanban_decompose.py / kanban_specify.py
M  plugins/platforms/telegram/adapter.py <- send-путь Telegram (thread metadata)
A  tests/gateway/test_telegram_html_payload.py и др.
```

`kanban_watchers_notifier.py` и `kanban_db_notify.py` в списке нет (чистые). Gateway после рестартов 27.09 10:21/12:24 исполняет **незакоммиченный worktree** (вероятно, lane "notifier-lane-B", каталог Desktop/all/notifier-lane-B существует). Диффы НЕ просмотрены (read-only мандат + git log/gc завис на 180s) — это первое действие фикс-лейна.

Хронологическая натяжка, которую фикс-лейн должен объяснить: в 26.09 процессе (старт 05:02, код в памяти с 05:02) starvation начался ~12:38–13:40 без рестарта. Кандидаты: (а) редактирование файлов 26.09 днём не влияет на уже импортированные модули — значит либо состояние (adapter/session), либо (б) ленивые импорты внутри функций (`_kanban_sub_op` импортирует `kanban_db_connect`/`kanban_db_notify` **на каждый вызов** — но модульный кэш процесса всё равно фиксирует версию с 05:02), либо (в) событие в Telegram-адаптере/роутах компании вокруг 12:38–13:40 (в логе: idle-TTL evict сессий company-топиков 129/131/132/281/3284 в 12:07–14:09 — перестройка multiplex-состояния). Требует live-пробы с DEBUG.

## 5. Побочная находка: hosted_room_worker (оценка влияния)

- Факт: `2026-09-25 17:02:18 ERROR gateway.run: Supervised task hosted_room_worker died 5 times in rapid succession — giving up restarts`. Причина: `import tui_gateway.server` → contracts → `from pydantic import Field` → `ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'` (hermes-agent\venv, Python 3.14.7 из C:\Users\max\AppData\Local\hermes\tools\python-3.14.7+…) — нативное расширение pydantic_core отсутствует/не по ABI венва.
- Влияние на notifier: **нулевое**. Notifier живёт в самом gateway-процессе (`_kanban_notifier_watcher`), не импортирует tui_gateway; эмпирически wake-доставки работали и после отказа (25.09 08:42→27.09 17:39, 9 строк). Влияние ограничено hosted Group Chat rooms (dashboard/tui_gateway).
- Фикс (отдельный leyн, ops): переустановка pydantic+pydantic_core в hermes-agent\venv под cp314 (`pip install --force-reinstall pydantic pydantic-core` или пересборка венва), затем рестарт gateway; проверка — отсутствие ERROR в gateway.log и `_start_hosted_room_worker_sync` без исключений.

## 6. Предложения (по приоритету)

### P0 — Аудит notify-leg (устраняет "не логируются"; мало, обратимо)
1. INFO-строка на успешный пинг (паритет с wake): `kanban notifier: pinged <kind> for <task> on <platform>/<chat>[:<thread>] profile=<p> event=<id>` — одна строка на событие, flood-risk минимальный (терминальные события редки).
2. INFO-строка на settle курсора wake-only подписок (advances без пинга сейчас невидимы).
3. Rate-limited WARNING в `_claim_for_sub` на каждый тихий скип с причиной и task_id: adapter=None (расширить `_warn_anchorless_thread_sub_once` на **anchored** thread-подписки — сейчас warning-помощник молча пропускает их), platform не активен.
4. **Stall-watchdog**: раз в N минут (например 10) сверять курсор подписки с MAX(id) её TERMINAL_KINDS-событий; при отставании — WARNING `kanban notifier: subscription stalled: task=<id> chat=<…> thread=<…> pending=<count> oldest=<age>`. Именно эта строка подняла бы тревогу 26.09 ~13:50 вместо тишины на сутки.

### P1 — Устранение starvation (сначала диагностика, потом патч)
1. **Зафиксировать runtime**: закоммитить/откатить dirty worktree hermes-agent (владелец решает судьбу lane-B); gateway должен исполнять коммиченный код. До этого любые патчи notifier бессысленны — поведение непрозрачно.
2. Review диффов `hermes_cli/kanban_db.py`, `kanban_db_connect.py`, `gateway/kanban_watchers.py`, `plugins/platforms/telegram/adapter.py` против HEAD — искать изменения в connect(board=…)/write_txn/Event/claim-обвязке и обработке thread metadata.
3. Live-проба с DEBUG: разовый прогон notifier-тика с logging.DEBUG (или временный DEBUG-флаг kanban.notify_debug) на реальном board — лог покажет точную точку скипа для t_4342c06e (перечислены в §3 кандидаты: list → platform → adapter → claim-empty).
4. Регресс-тест (pytest, изолированный tmp-DB): notify-only thread-подписка (thread_id+parent_chat_id, user_id=null) → blocked(пинг) → unblocked → completed; assert: курсор дошёл до completed, пинг отправлен, после "рестарта" (новый collector) поведение то же. Существующие тесты (test_kanban_notifier*.py) покрывают wake-ordering/api-server/zero-sub, но не notify-only thread-sub через несколько терминальных событий.
5. После фикса: курсоры t_4342c06e/t_eff9b2e1 догонят completed (at-least-once) — поздние "✔ done" пинги в topic 131 ожидаемы и допустимы; либо владелец явно отписывает эти две подписки (`hermes kanban notify-unsubscribe`).

### P2 — Дизайн-пробелы, вскрытые инцидентом
1. `notify-subscribe` на карту с уже имеющимся терминальным событием должен предупреждать: "subscription starts caught-up at event <id>; past terminal events will NOT be delivered" (кейс t_eee1848b/t_00c7f2bf — владелец ждал доставку, которой by design нет).
2. Аномалия t_c87f6555 (требует отдельной проверки): wake залогирован 13:38:17, но курсор 38981 выглядит не продвинутым до completed-id (ср. t_0a4a374e: 39030 = completed ✓). Возможно, мой id-реконструкшен неточен для этой карты, либо wake-settle теряет CAS — проверить в P1.3 пробе; повторяющихся wake в логе нет (13:38:17 единственный), что странно при не-продвинутом курсоре (re-claim каждые 5s → wake-шторм). Кандидат: dedup по session-state на wake-стороне.
3. `present_notification` глушит diagnostic-пинги при suppress_warning_notifications полностью бесследно — добавить счётчик подавленных (DEBUG→INFO в daily-сводке или метрика).

### P3 — hosted_room_worker
См. §5: пересборка pydantic в hermes-agent\venv под cp314; отдельная ops-карта; к notifier отношения не имеет.

## 7. Проверка (как владелец подтвердит фикс)

1. **Живой зонд уже armed**: эта карта (t_a362a047) имеет собственную подписку thread 131, notify+wake, company, курсор 39031 (= её created-событие). После моего complete: (а) если в topic 131 придёт пинг/wake и курсор сдвинется — notify-leg для НОВЫХ thread-подписок жив, starvation специфичен для подписок эпохи 26.09; (б) если тишина и курсор=39031 — голодание воспроизведено на текущем билде вживую, P1.3 проба обязательна. (`hermes kanban notify-list t_a362a047 --json` через минуту после complete.)
2. После P0: в gateway.log появляются INFO "pinged …" на каждый notify-пинг; инцидент класса 26.09 диагностируется за минуты.
3. После P1: курсоры замороженных подписок догоняют терминальные события; stall-watchdog молчит.

## 8. Ограничения и допущения

- Мандат read-only соблюдён: код/конфиги/состояния не изменялись; чтение config.yaml — только наличие ключей multiplex/profile_routes (значения секретов не читались и не приводятся).
- Прямой доступ к kanban.db не выполнялся (policy); состояние подписок получено официальным CLI `hermes kanban notify-list` (read-only).
- Идентификация "38955 = blocked" — арифметическая реконструкция по смежности глобальных id (39030/39031) и темпу событий; точные id событий недоступны read-only средствами. Альтернатива (38955 = completed) отвергнута арифметикой (§2.2), но живая проба (§7.1) закроет вопрос окончательно.
- `git log` по файлам notifier не выполнен (auto-gc репозитория превысил 180s таймаут) — история изменений lane-B не восстановлена; это задача P1.1–P1.2.
