# Root-cause разбор: worker spawn crash `No module named 'hermes_cli'`

Инцидент: 25.09.2026, вторая волна крашей на 4 досках (7 карт авто-блокированы).
Дата разбора: 29.09.2026 (operations, t_05b9f4cc).

---

## 1. Цепочка причин (почему воркер падает)

### 1.1. Непосредственная причина
Диспатчер (`kanban_db_dispatch.py::_resolve_hermes_argv`, строки 2599-2632) резолвит argv воркера как:
```python
[sys.executable, "-m", "hermes_cli.main"]
```
где `sys.executable` — интерпретатор **самого диспатчера** (gateway).

### 1.2. Почему диспатчер выбирает tools-python
Gateway (мультиплексор `gateway run`) запускается под **tools-python 3.14** (`C:/Users/max/AppData/Local/hermes/tools/python-3.14.7+.../python.exe`) с **cwd = корень hermes-agent** (`C:/Users/max/AppData/Local/hermes/hermes-agent`).

В этом окружении `importlib.util.find_spec("hermes_cli")` **проходит**, потому что cwd содержит `hermes_cli/`. Диспатчер "видит" модуль и решает: "можно использовать текущий интерпретатор".

### 1.3. Почему воркер падает
Воркер стартует в **workspace задачи** (`~/.hermes/kanban/boards/<board>/workspaces/<task_id>/`). Из этого cwd `hermes_cli` **не импортируется** — tools-python не находит модуль → `ModuleNotFoundError` → crash → карта авто-блокируется после 2 крашей.

### 1.4. Почему .pth-фикс не держится
Файл `hermes_agent_source.pth` в site-packages tools-python **стирается при пересоздании каталога**. Evidence:
- `.displaced-1c191c78c2944fe3b83b43adc9564870/` (25.09 21:41) содержит `Lib/site-packages/hermes_agent_source.pth` — старый каталог сохранён
- Текущий `python-3.14.7+202****0901-win32-x64/` создан **26.09 04:02** — pristine, .pth отсутствует
- `README.txt` в site-packages: дата 01.01.2024 — стандартный python-build marker

**Триггер пересоздания**: не установлен окончательно. Кандидаты:
- воркер-бутстрап (cron no_agent, hourly)
- official-runtime self-heal (проверка целостности tools)
- Task Scheduler задача `HermesOfficialRuntimeInstall` (статус: Ready, disabled)

---

## 2. Постоянный слой (HERMES_BIN) — почему это workaround, не fix

Company внёс `HERMES_BIN=C:\Users\max\AppData\Local\hermes\hermes-agent\venv\Scripts\hermes.exe` в user env (HKCU\Environment). `_resolve_hermes_argv` проверяет его **первым** (строка 2614).

**Почему это не полный fix:**
1. HERMES_BIN — **user env**, не system env. Сервис/scheduled task под SYSTEM или другим user не видит его.
2. Если gateway запущен без наследования user env (чистый scheduled task), HERMES_BIN отсутствует → fallback на find_spec → снова tools-python.
3. `hermes.exe` в venv — wrapper script, не сам интерпретатор. При spawn он запускает `venv\Scripts\python.exe -m hermes_cli.main`, что корректно, но добавляет лишний hop.

---

## 3. Почему gateway запускается под tools-python

### 3.1. Текущий запуск
Процессы gateway сейчас не видны (нет активных gateway в tasklist). Но по коду:
- `hermes_cli/gateway.py` — фасад, использует `hermes_cli.gateway_windows` для Windows service
- `hermes_cli/_launchers.py::runtime_command` — резолвит команду запуска

### 3.2. Предполагаемый путь запуска (по evidence)
Вариант A: **Task Scheduler** → `gateway-service\HermesFleet_Gateway_<profile>.vbs` → `pythonw.exe -m hermes_cli.main gateway run`
- VBS-файлы найдены в `profiles/company/gateway-service/`
- Scheduled tasks `HermesFleet_Gateway_*` — статус Disabled (не активны сейчас)

Вариант B: **Desktop spawn** (пользовательский ярлык/автозагрузка)
- Не подтверждено — нет evidence в стандартных автозагрузках

Вариант C: **Hermes multiplex** — один процесс на все профили
- `gateway_multiplex_mode.py` — подтверждает существование режима
- При этом запуск может идти через официальный runtime installer, который использует tools-python

### 3.3. Кто выбирает интерпретатор
Если запуск идёт через `hermes.exe` (любой — venv или tools), то `hermes.exe` — это entry-point script, который вызывает `python -m hermes_cli.main`. Какой `python` — зависит от того, какой `hermes.exe` запущен и как он сконфигурирован.

**Проблема**: если gateway стартует из среды, где `hermes` в PATH указывает на tools-python (например, после обновления tools), то диспатчер унаследует tools-python.

---

## 4. Устойчивые альтернативы (рекомендации)

### 4.1. Системный env вместо user env
`HERMES_BIN` в **system environment** (HKLM\System\CurrentControlSet\Control\Session Manager\Environment) — тогда любой процесс, включая service/scheduled task, его видит.

**Риск**: требует admin, влияет на всех пользователей. Только если fleet single-user.

### 4.2. Патч диспатчера: проверять импортируемость в workspace, не в dispatcher
Вместо `find_spec` в текущем процессе — проверять, импортируется ли `hermes_cli` из **рабочей директории воркера**. Сложно: требует spawn probe-процесса перед реальным воркером.

### 4.3. Явный `--python` флаг в gateway run
`gateway run --python C:\...\venv\Scripts\python.exe` — зафиксировать интерпретатор при старте gateway, передавать в диспатчер.

### 4.4. Устранить tools-python из путей gateway
Запускать gateway строго из venv hermes-agent, не из tools. Требует пересмотра official-runtime installer.

---

## 5. Текущее состояние (29.09.2026 11:00)

| Компонент | Статус | Evidence |
|-----------|--------|----------|
| tools-python каталог | Pristine, создан 26.09 04:02 | `ls` + PowerShell timestamps |
| `.pth` в site-packages | **ОТСУТСТВУЕТ** | `ls` + `find` — нет файла |
| `.pth` в `.displaced` | Есть (25.09 21:41) | `find` подтвердил |
| HERMES_BIN в user env | Установлен | `reg query` — `C:\...\venv\Scripts\hermes.exe` |
| venv hermes.exe | Работает (v0.21.5) | `hermes.exe --version` exit 0 |
| Cron guard_worker_runtime | **НЕ СОЗДАН** (jobs.json пуст для guard) | `cronjob_manage list` — нет записи |
| Gateway процессы | Не активны (нет python/hermes в tasklist) | `tasklist` пуст |

**Риск рецидива**: средний. Пока HERMES_BIN в user env и gateway наследует его — воркеры стартуют через venv. Но при рестарте gateway из чистого окружения (scheduled task, service) — риск повторения.

---

## 6. Рекомендации для layer/владельца

1. **Немедленно**: восстановить `.pth` в текущем tools-python (скрипт guard_worker_runtime.py делает это, но cron не создан).
2. **Краткосрочно**: создать cron-задачу guard_worker_runtime (hourly, no_agent) для автоматического восстановления .pth.
3. **Среднесрочно**: перенести HERMES_BIN в system env или встроить в scheduled task definition для gateway.
4. **Долгосрочно**: патч диспатчера — не доверять `find_spec` в процессе gateway, использовать явный путь к venv hermes-agent.

---

*Разбор подготовлен operations (t_05b9f4cc), read-only. Запреты соблюдены: gateway не рестартовал, scheduled tasks не менял, dispatcher не патчил.*
