# KANBAN_TENANT_DIAG_2909 — диагностика kanban после layer-apply 29.09.2026

Карта: t_787fab6a (fleet-ops, research). Исполнитель: профиль tech. Режим: read-only (без push/apply/рестартов).
Рантайм: `C:/Users/max/AppData/Local/hermes/hermes-agent` — official HEAD `31c5d57ec6` (FF от 29.09 04:17), layer v5 = working-tree diff (20 файлов); merge-коммит слоя `e5a6fbf82f` ("merge layer v5 (b80fdbbd01) onto official f81bb4c485", ветка company/autocompany-rebased-p0-v5-local).
Комментарии карты: 5055 (основные находки), 5056 (инкремент после re-scope).

---

## (a) Root cause поведения `kanban list` — layer vs official

**Слой v5 НЕ является причиной.** Layer-diff kanban-подсистемы не затрагивает роутинг board/tenant/list:
- `hermes_cli/kanban_parser.py` (12 строк): только новая команда `metrics` и help `block --kind policy_denied`; top-level `--board` (L475–483) и `--tenant` у `list` (L238) идентичны official base f81bb4c485.
- `hermes_cli/kanban.py` (117 строк): goal-judge fallback-review + `metrics`; board-override блок L155–178 — official, не изменён.
- `hermes_cli/kanban_db.py` (168 строк): `_board_path`, `kanban_db_path`, `scoped_current_board`, `get_current_board` слоем НЕ тронуты.
- `hermes_cli/kanban_db_connect.py` (+34): только тест-изоляция.

**Механизм (official), три факта:**
1. `--board` — TOP-LEVEL флаг парсера kanban: корректно `hermes kanban --board <slug> list ...`. Форма `hermes kanban list --board <slug>` → argparse usage error, exit≠0 (воспроизведено 29.09). У `list` есть только `--tenant` — ортогональная фича.
2. Env-пин `HERMES_KANBAN_DB` побеждает `--board`: `_board_path()` (`kanban_db.py` L496–510) проверяет `os.environ.get(env_var)` РАНЬШЕ slug/contextvar; `--board` действует через `scoped_current_board()` (L361), до которого при пине дело не доходит. Диспетчер инжектит `HERMES_KANBAN_DB`/`HERMES_KANBAN_BOARD`/`HERMES_KANBAN_WORKSPACES_ROOT` в env каждого воркера (`kanban_db_dispatch.py:2947`, official). Внутри agent/worker-сессии и всех её подпроцессов `kanban --board X list` молча читает запиненную доску при любом X.
3. Доски НЕ слиты, тенант-миграция ни при чём: `kanban/boards/{fleet-ops 13.7MB (29.09 23:07), rr-team 4.7MB, video 2.6MB (29.09 12:37), general, portfolio, seo-site, venture-lab, freelance, e2e-canary-3c9f}/kanban.db` — раздельные живые файлы; корневой `kanban.db` (default) 122KB с 16.09; `kanban/current` отсутствует. `list --tenant video → 0`: tenant — отдельная колонка, у всех задач fleet пустая (тенанты не использовались).

**Сведение к наблюдениям:** «`list --board video` → 121 задача» и «N копий каждой карты» (FIX P4 в fleet_rollup.py) = чтение одной запиненной БД (вероятно fleet-ops) из сессии воркера/company при любом `--board`. Формулировка «тенант-миграция ядра» — мисдиагноз.

**Коммит-виновник: НЕ в изменениях 29.09.** Reflog деплоя: 27.09 04:13 HEAD=f81bb4c485 → 28.09 FF 2ffa4977ba→952c941e74 → 29.09 04:02/04:17 FF 449fae030a→31c5d57ec6 → 05:00:03 reset-to-HEAD + layer working-tree apply. `_board_path` и env-инжект БАЙТ-ИДЕНТИЧНЫ в 952c941e74 (L496–510; dispatch L2882/2887) и da77a7e2e8 (deploy 25–26.09): механизм присутствует минимум с 25.09; ни слой v5, ни official-диапазон 952c941e74..31c5d57ec6 (662 коммита) его не вносили. «Потеря после layer-apply» — корреляция: 29.09 изменился контекст наблюдения (прогоны из запиненных worker-сессий). Точный upstream-коммит введения пина не определён (history-walk таймаутил 120/180s); владельцу: фоновый `git log -S "HERMES_KANBAN_DB" -- hermes_cli/kanban_db_dispatch.py`.

**Канон употребления для скриптов флота:**
- форма флага: `hermes kanban --board <slug> list|ls ...` (перед subcommand); `ls` — алиас `list`;
- `list --tenant` — НЕ board-фильтр (колонка пуста);
- из запиненного контекста (worker/agent): читать пер-борд явным `HERMES_KANBAN_DB=<root>/kanban/boards/<slug>/kanban.db` на subprocess ЛИБО сняв пины (pop `HERMES_KANBAN_DB`/`HERMES_KANBAN_BOARD`/`HERMES_KANBAN_WORKSPACES_ROOT`);
- из незапиненного cron/gateway форма `--board` работает; при отсутствии `kanban/current` default-доска почти пуста.

## (b) Сталл диспетчера 00:14→12:25, восстановление ~12:29

**Таймлайн (logs/gateway.log, локальное время; 522 строки за 29.09):**
- 00:00:58 `[video] spawned=5`; 00:07–00:30 серия `reaped zombie worker` + 00:08 `crashed=1` — ночной инцидент: воркеры падали сразу после спавна.
- 00:14:19 первый `dispatcher stuck: ready queue non-empty ... Last tick held back: blocker_auth=***` (в 00:24 также `rate_limit_cooldown=1`).
- Сталл пережил рестарты gateway 04:25:58 и 05:01:37 (layer-apply ~05:00) → начался на ~4ч45м РАНЬШЕ слоя; **слой не причина**; состояние в строках tasks, не в процессе.
- 126 stuck-тиков за 29.09 (несколько стриков; аналоги 23–24.09 — повторяющийся класс); финальный стрик: 31 consecutive tick, последний 12:25:16.
- 12:28:06 profile reconcile (config изменён, MCP +timeweb — владелец правил конфигурацию); 12:29:20 `spawned=2 [fleet-ops]` И `spawned=2 [rr-team]` одновременно; 12:30 `[video] spawned=1`; 12:31 t_8b3e6475 completed. 12:52:33 рестарт (prev life pid=31828, started 05:00:20 local, UNCLEAN exit, last heartbeat 12:38:47).

**Механизм (official source):** respawn-guard `_respawn_guard_reason` (`kanban_db_dispatch.py` L1525–1600): ready-задача удерживается с причиной `blocker_auth`, если `tasks.last_failure_error` матчит `_RESPAWN_BLOCKER_RE` (L63–71: `quota|rate limit|429|403|auth*|authoriz*|authz|unauthorized|forbidden|billing|subscription|access denied|permission denied|invalid api key`, IGNORECASE) и outcome последнего run ≠ `crashed`. В отличие от `rate_limit_cooldown` (300s, ретраи «forever») у `blocker_auth` НЕТ временного освобождения — парк до перезаписи ошибки новым run или смены outcome. Ночной provider/auth-инцидент проштамповал auth-текст → готовые карты висели 12 часов. Это НЕ claim-lock, НЕ tenant-несоответствие, НЕ DB-lock.

**Layer-diff диспетчера к сталлу отношения не имеет:** `kanban_watchers_dispatcher.py` (+37) — эскалация PermissionError-стриков в [FLEET ALERT]; `kanban_db_dispatch.py` — fail-closed проверка реестра профилей, protocol-violation streak, выбор интерпретатора в `_module_hermes_argv`. Ни один хунк не создаёт/снимает blocker_auth.

**`blocker_auth=***`** — артефакт secret-редакции логов: `describe_suppression` (L157–183) печатает честные `k=v`, но редактор («Secret redaction: ENABLED») маскирует значение после ключа, содержащего «auth» (соседний `rate_limit_cooldown=1` виден). Число held-карт в логе не читается.

**Точный триггер освобождения 12:29 НЕ подтверждён** (evidence gap): нужны task_runs/task_events fleet-ops и rr-team; прямой доступ воркера к kanban.db запрещён политикой. Кандидаты: (i) действия владельца ~12:28 (unblock/requeue с перезаписью last_failure_error); (ii) смена outcome последнего run. Одновременность двух досок указывает на общую причину (provider/вмешательство владельца), не на починку кода.

**Доп. симптом — zombie-reaps вечера 29.09 (20:59, 21:01, 21:07, 21:13, 21:15, 21:22, 22:29, 22:51, 23:03): benign.** Сэмплены t_4a5b52f1 (reap 23:03:29) и t_25858b18 (reap 21:22:51) — оба заканчиваются `[kanban-worker-exit] rc=0` (нормальные завершения, сессии 3 и 46 мин). Механика: на Windows нет `waitpid(-1)` — `_default_spawn` паркует Popen в `_live_worker_procs`, `reap_worker_zombies` поллит каждый тик и логирует «reaped N zombie worker(s)» для ЛЮБОГО завершившегося между тиками ребёнка; исход классифицируется по exit-trailer → `crashed=0` во всех вечерних тиках (доска [default]). Единственный настоящий crash за сутки — 00:08 [video] crashed=1.

**Оценка:** сталл = provider/auth-инцидент + official respawn-guard без TTL при очень широком regex (403/auth/forbidden/permission denied ловят безобидные тексты; код сам ссылается на #117097). Трактовать как provider-инцидент/классификацию, а не «умершие ключи».

## (c) Аудит потребителей `kanban list`

Расположение: `C:/Users/max/AppData/Local/hermes/profiles/company/scripts/`. Только номера строк, read-only.

**Исправлены company (не трогал):**
- `fleet_rollup.py` (mtime 29.09 22:31) — FIX P4 (L173–186 `_task_board`, L196–201 комментарий): два глобальных `kanban list --json`, атрибуция доске regex'ом по `workspace_path` (`boards/<slug>/workspaces`), недиспатченные → «флот». Caveat: «глобальный» list в запиненном контексте вернёт только запиненную доску — workaround корректен лишь незапиненным (cron/gateway).
- `owner_attention_watch.py` (22:52), `cap_tool_watch.py` (22:52; копия в `ventures/scripts/`) — исправлены company, детально не изучались.

**Сломаны (не исправлены) — ломаются только в запиненном worker-контексте:**
- `daily_pc_hygiene.py` (mtime 27.09, до инцидента): L195 (`kanban --board <b> list --archived --json`), L533 (`_board_tasks`: `env = dict(os.environ)` + `HERMES_HOME`, пины не снимаются), L833 (`--board <b> list --json` + `--archived`). Форма CLI корректная; env наследуется → каждый борд цикла читает одну запиненную БД (тихие неверные данные/дубли).
- `card_readiness.py` (mtime 25.09): L40–42 `kanban()` — `subprocess.run(["hermes","kanban"]+args)` БЕЗ env → полное наследование пинов; L241 `--board <b> list --status <st> --json`; L262 default `--board` из `HERMES_KANBAN_BOARD`. Та же хрупкость + зависимость от PATH-`hermes`.

**Починка (owner-задача):** в subprocess-env `pop` пинов `HERMES_KANBAN_DB`/`HERMES_KANBAN_BOARD`/`HERMES_KANBAN_WORKSPACES_ROOT` или явный пер-борд `HERMES_KANBAN_DB=boards/<b>/kanban.db`.

## (d) Evidence base

- git: `reflog --date=iso` (таймлайн деплоя 27–29.09); `merge-base HEAD f81bb4c485`; `status --short` (20 файлов слоя); `log e5a6fbf82f`; `branch --contains e5a6fbf82f`; `rev-list --count 952c941e74..31c5d57ec6` = 662; `git diff` по kanban_parser/kanban/kanban_db/kanban_db_connect/kanban_db_dispatch/kanban_watchers_dispatcher; `git show 952c941e74:hermes_cli/kanban_db.py` + `...kanban_db_dispatch.py`, `git show da77a7e2e8:hermes_cli/kanban_db.py` (идентичность `_board_path`/инжекта).
- source: `kanban.py:150–185`; `kanban_db.py:355–470,484–560`; `kanban_db_dispatch.py:63–80,141,157–215,1525–1600,2947`; `kanban_watchers.py:370–425`; `kanban_parser.py:225–250,460–505`.
- Живое воспроизведение (worker-сессия tech, пин fleet-ops): R1 `kanban list --board video --json` → usage error; R2–R4 → fence «delegate_task child contexts cannot mutate» (CLI из воркера заблокирован — «121» пересчитать не мог).
- `logs/gateway.log` (4664 строки, 21.08→29.09 22:59): таймлайны (b), zombie-reaps, lifecycle_ledger 12:51:08.
- worker-логи: `kanban/logs/t_4a5b52f1.log`, `t_25858b18.log` — tail, `[kanban-worker-exit] rc=0`.
- ФС: `ls -la kanban/boards/*/kanban.db kanban.db`; `read_file kanban/current` (not found); `reg query HKCU\Environment` (user-уровневых HERMES_KANBAN_* нет); env воркера (`HERMES_KANBAN_DB=...fleet-ops/kanban.db`).
- Consumer-скрипты: grep/sed по строкам, перечисленным в (c).
- Отклонено политикой (не повторялось): grep agent.log по credential-ключевикам → secret_read_or_write (call_index=32, автоблок рана, снят владельцем); write_file deliverable в блокировке (записан после unblock).

## (e) Выводы

**Факты:**
1. `--board` у `list` никогда не было (top-level флаг kanban); корректная форма глушится env-пином `HERMES_KANBAN_DB` (official-резолвинг: env > contextvar/аргумент), который диспетчер инжектит каждому воркеру. Слой v5 и official-диапазон 29.09 поведение не меняли — механизм идентичен базам 25.09 и 28.09.
2. Доски физически раздельны; tenant-модель не задействована (колонка пуста) — «тенант-миграция» в комментариях фиксов есть мисдиагноз.
3. Сталл 00:14→12:25 — official respawn-guard `blocker_auth` (regex по last_failure_error, без TTL) после ночного provider/auth-инцидента; layer-apply (05:00) и рестарты gateway его не снимали; восстановление 12:29:20 одновременно на fleet-ops и rr-team, через минуту после config-reconcile 12:28:06.
4. Вечерние zombie-reaps — benign: Windows-поллинг завершившихся детей, сэмпл rc=0; настоящий crash за сутки один (00:08 [video]).
5. Сломанные потребители: `daily_pc_hygiene.py` L195/533/833, `card_readiness.py` L40–42/241 — наследуют env-пины; исправленные company (fleet_rollup/owner_attention_watch/cap_tool_watch) не тронуты, workaround fleet_rollup корректен только незапиненным контекстом.

**Assumptions/пробелы:** «121» не пересчитана (CLI fenced); триггер освобождения 12:29 — кандидаты, не доказано (DB-доступ запрещён); upstream-коммит введения env-пина не определён (history-walk таймаутит); ночные worker-логи 00:07–00:30 по доскам не прочитаны (grep отклонён политикой).

**Рекомендации owner (отдельными картами):**
1. Починить `daily_pc_hygiene.py`/`card_readiness.py`: снимать/переопределять `HERMES_KANBAN_DB/BOARD/WORKSPACES_ROOT` в subprocess-env.
2. Апстрим-репорты NousResearch/hermes-agent: (i) `blocker_auth` без TTL паркует ready-карты на неопределённый срок при широком regex — нужен max-hold/сужение паттерна; (ii) `--board` молча игнорируется при env-пине — warning или приоритет флага; (iii) secret-редактор маскирует held-back-счётчик (`blocker_auth=***`) — переименовать причину или починить редакцию.
3. Термин «тенант-модель» в FIX P4 (fleet_rollup) заменить на «env-пин HERMES_KANBAN_DB глушит --board».
4. Cross-board скрипты запускать из незапиненного контекста (cron/gateway) либо читать пер-борд БД явным `HERMES_KANBAN_DB`.

---

## Аддендум run 1826 (независимая blob-level проверка, 29.09 23:2x)

Проверка в read-only чекауте `C:/Users/max/Documents/hermes-official-live-layer` (HEAD 2dd7c6c9c2; все три SHA резолвятся: `git cat-file -t` f81bb4c485 / 31c5d57ec6 / e5a6fbf82f = commit). Diff — по явным SHA, не по HEAD.

1. **Диапазон f81bb4c485..31c5d57ec6, kanban-подсистема** (`git diff --stat`): `kanban_parser.py` ОТСУТСТВУЕТ (не менялся); `kanban.py` −8 и `kanban_db.py` −85 = только удаление PLUGIN-COMPAT-блоков (revert-scheduled shim, COMPAT_MANIFEST.md); `kanban_db_dispatch.py` +53/−4 = i18n exit-summary маркер, per-task событие `skipped_nonspawnable` (#122422), `_propagate_module_import_root` (#122299/#122487/#122500). Ни один ханк не затрагивает board/list-роутинг, `_board_path` или respawn-guard. Подтверждает вывод (a): диапазон поведение не менял.
2. **`--board` top-level во всех трёх версиях** (grep по blob-ам `kanban_parser.py`): base f81bb4c485 L467/470 ≡ official HEAD 31c5d57ec6 L467/470; layer v5 e5a6fbf82f L475/478. Флаги subcommand `list` (official HEAD L234–248, alias `ls`): `--mine/--assignee/--status/--tenant/--session/--archived/--json/--sort/--workflow-template-id/--step-key` — `--board` нет и не было ни в одной из трёх версий. **«Коммита-виновника потери фильтра list --board» не существует: форма никогда не была валидной** (usage error), а наблюдавшиеся «121 задача» — env-пин (механизм (a), присутствует минимум с 25.09).
3. **Zombie-reaps вечера 29.09** (gateway.log 584796 байт на 23:18): 18 одиночных INFO-reaps 13:30→23:03; строки L4635 (21:22:51 pid 9708), L4658 (22:29:55 pid 31944), L4662 (22:51:20 pid 28376), L4665 (23:03:29 pid 24864) — по одному pid на reap, диспетчер продолжал спавнить. Согласуется с benign-классификацией раздела (b) (Windows-поллинг завершившихся детей, сэмпл rc=0).
4. **Статус пробелов:** upstream-коммит введения env-пина и точный триггер освобождения 12:29 остаются owner-пробелами (фоновый `git log -S` / task_runs+events fleet-ops и rr-team — воркеру DB-доступ запрещён). Остальное закрыто; реализация — отдельными owner-картами по рекомендациям (e).

