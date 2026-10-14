# IMPLEMENTATION: gateway-restart hygiene (t_63a7d05c, fleet-ops)

task_type: ops. Owner profile: tech. Дата: 2026-10-14. Host: DESKTOP (Windows 11).
SPEC: docs/fleet-ops/gateway-restart-hygiene-20261013/SPEC.md (sha256 160e28c5fd16b80f2cc05f5b1b7045246a9a62ad151aecef51a9ef455d030395).

## Контекст

Рестарт Hermes desktop app спавнит НОВЫЙ default-мультиплексор
(`python -m hermes_cli.main gateway run`), но не терминирует гейтвеи прошлых
поколений. 13.10 stale company-gateway отдавал `[Errno 2]` на каждый in-place
model switch (5 фейлов 11:05-11:12) и терял pywin32. `hermes gateway restart` —
только service-mode, на Windows-хосте недоступен. Существующий
ram_orphan_cleanup.ps1 v3 считает `gateway run`-пайтоны LIVE ROOT и их не трогает.

## Решение

Sibling-скрипт в той же per-tick лейне (fleet_fast_watch -> company_cron_watchdog
-> check_ram), чтобы не менять QA-логику v3:

1. `profiles/company/scripts/gateway_orphan_reaper.ps1` (новый, ASCII+BOM,
   sha256 73b8b8892efa818e806850ad87e1cb3ff3e24a62be6c325e1f9c072f19d31844):
   - убивает ТОЛЬКО процессы python с cmdline `-m hermes_cli.main gateway run`,
     созданные РАНЬШЕ (старт app-инстанса − 300s grace);
   - app-инстанс = Hermes.exe из `apps\desktop\release` без `--type=` (CLI
     hermes.exe serve/kanban/chat отсечены по ExecutablePath: PowerShell -eq
     регистронезависен и ловил их как «инстансы»);
   - 0 или >1 app-инстансов = SKIP (fail-closed, пишется в лог);
   - whitelist (даже при матче паттерна): CDP/remote-debugging-port/9222,
     Fleet-Browser, kanban/chat-воркеры, pm/worker.py, HermesLimitsWidget,
     --service/--daemon;
   - PID-reuse guard: перед Stop-Process процесс перечитывается по PID и
     cmdline перепроверяется;
   - текущее поколение мультиплексора всегда старше app-инстанса быть не может
     (спавнится после) → бан «не убивать текущий мультиплексор» выполняется
     конструктивно;
   - лог `profiles/company/logs/gateway-orphan-reaper.log`: каждая KILL /
     KILLED / KILL-FAILED / KILL-ABORT / RUN-сводка (при наличии кандидатов) /
     SKIP-причина; последняя строка stdout `killed N` / `would_kill N` —
     контракт парсера watchdog (как у v3);
   - `-SelfTestIgnoreAge` форсит dry-run, отключает age-фильтр и файл-лог.
2. `profiles/company/scripts/company_cron_watchdog.py` — хук в `check_ram()`
   (сразу после вызова ram_orphan_cleanup.ps1): вызов reaper каждый тик,
   парсинг `killed N`, detail `, stale gateways N`, internal-alert при убийстве.
   Backup: company_cron_watchdog.py.bak-gwreaper-20261014.

hermes-agent НЕ тронут (ban). Убийства вне gateway-run паттерна невозможны
(ban): других классов жертв в скрипте нет.

## Риски / компромиссы

- R1: если после рестарта app новый мультиплексор НЕ поднялся, reaper убьёт
  старый → сервис без гейтвея до rescue (check_gateway_starts.ps1 +
  HermesCompanyRescue поднимают). Это поведение прямо предписано SPEC.
- R2: два одновременных app-инстанса = постоянный SKIP (fail-closed): сироты
  не чистятся, пока ambiguity не разрешится. Сознательный выбор против
  убийства гейтвея «чужого» инстанса.
- R3: gateway, переживший несколько рестартов app (напр. rescue-спавн после
  рестарта), younger app-инстанса → переживёт чистку; будет срезан после
  следующего рестарта app. Возраст — единственный признак поколения.
- R4: RUN-строка пишется каждый тик при наличии кандидата (~200 строк/день,
  ~25KB) — цена A3-аудита; hygiene-лейн файл не ротирует (только *.log.N).

## Проверки / evidence (2026-10-14, все exit 0)

- BOM+ASCII: bom_present=True, non_ascii_lines=0, anchors ok
  (ps1_bom_verify2.py, повторено после каждого патча).
- Dry-run (нормальный): `would_kill 0`; app_pid=11156 (01:30:26),
  candidates=1 (PID 16108, 11:26:48 — younger → не сирота).
- Dry-run selftest: `WOULD pid=16108 age_h=4.3 ... thr=2026-10-14T01:25:26` +
  `would_kill 1` — селекция/age/лог-формат доказаны без убийств.
- Real-run: `killed 0` + RUN-строка в логе; контракт парсера проверен.
- Fail-closed доказан до фикса фильтра: 2 SKIP-строки «ambiguous: 5/6 Hermes.exe
  main instances» в логе (15:39) — guard отработал, ничего не убито.
- Python-хук: изолированный юнит-тест (fake _company_home, capture _alert):
  killed-2 → detail+alert; killed-0 → молча; garbage stdout → не падает;
  отсутствие файла → skip. ALL_OK=True, exit 0.
- py_compile company_cron_watchdog.py: OK; кириллица не повреждена
  (grep «сирот» = 5).

## Acceptance-статус

- A1 (нет gateway старше app-инстанса после рестарта): механизм задеплоен;
  подтверждение наступит на ближайшем рестарте app (по baseline M2 ~4/день).
  Проверка: лог reaper (RUN/KILL) + таблица процессов с CreationDate.
- A2 (in-place model switch после рестарта, 0 ENOENT за 24h): окно открыто
  с 15:44 14.10; аудит логов гейтвея — QA-карта.
- A3 (0 убийств здоровых процессов за 24h): аудит
  profiles/company/logs/gateway-orphan-reaper.log — каждая KILL-строка
  обязана показывать cmd_tail с gateway-run и age > threshold.

## Изменённые файлы

- NEW profiles/company/scripts/gateway_orphan_reaper.ps1 (5561 B, sha256 выше)
- MOD profiles/company/scripts/company_cron_watchdog.py (+37/-2, check_ram hook)
- NEW profiles/company/logs/gateway-orphan-reaper.log (audit)
- BAK profiles/company/scripts/company_cron_watchdog.py.bak-gwreaper-20261014
- NEW docs/fleet-ops/gateway-restart-hygiene-20261013/IMPLEMENTATION-t_63a7d05c.md (этот файл)

Suggested commit message (ventures docs):
  docs(fleet-ops): gateway-restart hygiene implementation note (t_63a7d05c)

Откат: удалить gateway_orphan_reaper.ps1, вернуть
company_cron_watchdog.py.bak-gwreaper-20261014 -> company_cron_watchdog.py,
удалить лог. Reversible, hermes-agent не затронут.
