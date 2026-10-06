# CARD_BODY_TEMPLATE.md — шаблон тела канбан-карты для авторов (v1.2.40, t_f0599145)

Директива владельца 04.10: карты должны быть «корректными, нативными, полноценными».
С v1.2.40 тело карты валидируется стражей fleet-policy **до спавна воркера**
(pre-claim точка `kanban_task_claimed`, модуль `src/fleet_policy/body_guard.py`).
Семантика правил едина с живым валидатором `card_readiness.py` rails v3 (t_20d62426).

## Обязательный шаблон тела

Первая строка — **точный маркер task_type** (канон: `research|code|review|ops`;
регистр и BOM прощаются, маркер глубже первой строки НЕ считается):

```
task_type: <research|code|review|ops>

<суть задачи: контекст, что и зачем>

DELIVERABLE: <конкретный артефакт, расположение, sha256/receipt>
ACCEPTANCE: <проверяемые критерии готовности: тесты/проверки>
BANS: <что запрещено; минимум: policy-denial -> partial+stop>
ANCHOR: <кто и где проверяет результат (QA-якорь/эскалация)>
```

Синонимы и формы секций, которые принимает стража (EN+RU, markdown):

| Секция | Принимаемые формы (примеры) |
|---|---|
| DELIVERABLE | `DELIVERABLE:`, `## Deliverables`, `Поставка:`, `Артефакты:`, `Результат:` |
| ACCEPTANCE | `ACCEPTANCE:`, `Acceptance criteria (v2):`, `## Критерии приёмки`, `Приемка:`, `Definition of done:`, `Done-критерии:` |
| BANS | `BANS:`, `## Запреты`, `Запрещено:`, `Guardrails:` |
| ANCHOR | `ANCHOR:`, `## Якорь`, `Эскалация:`, `Эскалация/якорь:`, `ANCHOR (проверен …):` |

Разделитель после имени — любой из `: = — – -`; содержимое может быть пустым
(`BANS:` валидно), допустимы markdown-префиксы `# > * + -`, скобочный
квалификатор и составное имя через `/`.

## Строгость по автору карты (created_by)

| Автор | Отсутствие секций | Отсутствие/мусорный маркер в 1-й строке |
|---|---|---|
| agent (`created_by != owner`; неизвестен/пуст = agent, fail-closed) | **BLOCK** → deny `card_structurally_broken`: комментарий + блок карты до исправления | **BLOCK** → deny (штатный claim-deny; для маркера — правило `missing_or_unknown_task_type`/`card_structurally_broken` с точной причиной) |
| owner (`created_by ∈ body_guard.owner_created_by`, поставочно `user`) | **advisory**: WARN-комментарий без блока | BLOCK (маркер обязателен для всех) |

Структурно сломанная карта **не авто-ресумится** deny-triage стражей: исправление
тела и unblock — маршрут автор/owner (`next_step` в комментарии блока).

## Пример нативного kanban_create (agent-карта)

```python
kanban_create(
    title="Fix parser crash on empty input",
    assignee="tech",                      # живой профиль (hermes profile list)
    parents=["t_a0f026dd"],               # зависимости: ready после done родителей
    workspace_kind="worktree",            # для кода — worktree/dir, НЕ scratch
    body=(
        "task_type: code\n"               # ← ПЕРВАЯ строка, точный маркер
        "\n"
        "Парсер падает на пустом вводе (traceback в комментарии родительской карты).\n"
        "\n"
        "DELIVERABLE: PR в trunk: фикс + tests/test_parser_empty.py; ветка fix/<task-id>.\n"
        "ACCEPTANCE: pytest tests/ -q зелёный; selftest фиксера ≥6 кейсов; CI clean.\n"
        "BANS: не трогать live deploy-пути; первый policy-denial -> partial+stop.\n"
        "ANCHOR: QA-потомок (независимая проверка после merge, форма owner)."
    ),
)
```

Эквивалент CLI: `hermes kanban create --title … --assignee … --body "$(cat body.txt)"`
— body.txt начинается со строки маркера.

## Чек-лист автора перед созданием карты

1. Первая строка body — ровно `task_type: research|code|review|ops`.
2. Все четыре секции присутствуют (для agent-карт — обязательно).
3. DELIVERABLE конкретен (артефакт + расположение), ACCEPTANCE проверяем.
4. BANS содержит минимум `policy-denial -> partial+stop`.
5. ANCHOR называет независимого проверяющего и момент проверки.
6. Решения, от которых зависит карта, вписаны в её body (воркеры не видят
   соседние карты); assignee — существующий профиль; workspace — не scratch
   для правок существующего worktree.

## Режимы стражи (конфиг `body_guard`, откат без передеплоя)

```yaml
body_guard:
  enabled: true          # мастер-флаг вызова (false = стража не вызывается)
  mode: enforce          # off|warn|enforce; мусорное значение → warn (fail-safe)
  owner_created_by: ["user"]
```

- `enforce` (поставочный): BLOCK → deny `card_structurally_broken` (блок карты с
  точной причиной), WARN → advisory-комментарий;
- `warn`: все дефекты advisory (поведение диспатча как до v1.2.40);
- `off` / `enabled: false`: стража не вызывается.

Проверка тела вручную (read-only): `python src/fleet_policy/body_guard.py
--body-file body.txt --created-by tech --mode enforce --json` (exit 0 = pass,
1 = дефекты) и `--selftest` (≥6 кейсов). Наблюдаемость: событие policy-store
`kind="body_guard"` на каждый claim при включённой страже; deny —
`kind="card_structurally_broken"`, advisory — `kind="body_guard_advisory"`.
