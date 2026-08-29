# Протокол G3: «consented GPT portfolio inventory scan» (field-спринт H1)

Карточка: t_9b0bda2c (родитель t_e56b725d, спринт-трекер; вердикт NEEDS-EVIDENCE — decisions/0001).
Статус: Accepted (2026-08-29, карточка t_9b0bda2c). Без external runtime-действий: протокол определяет только метод подсчёта и приёмки evidence; никакого продукта не строится, никакого сбора данных по протоколу не выполняется до user-approvals B1–B4.

## 1. Что это и зачем

G3 — полевая метрика спринта H1: «сколько портфелей GPT реально существует у людей и как они устроены». До этой карточки метрика была «WCMS-скан» с неопределённым методом (блокер B3); аббревиатура WCMS нигде не расшифрована. Это протокол вместо загадки: операционное определение «одного скана» и правила счёта.

Дизайн следует §3.3 агрегата: сбор согласие-based (consent-based), user-authorized, без автоматизированного извлечения из OpenAI — автоматизация запрещена (ToS: «Automatically or programmatically extract data or Output» [S21][HIGH], снапшот `evidence-discovery2-H1/e21_openai_terms_of_use_2026-08-29.txt`). Поскольку сбор не автоматизирован, «метод» = контролируемый человек-процесс с raw-регистром evidence.

## 2. Fixed decisions (не пересматриваются в этом протоколе)

- Именование: в спринт-доках метрика называется **«consented GPT portfolio inventory scan»**. Аббревиатура WCMS не расшифровывается; если первичный артефакт позже докажет её расшифровку, правка задним числом не делается — изменение имени через новый файл с Supersedes (правила decisions/README.md). WCMS упоминание в `discovery-2026-09.md` — исторический артефакт, не трогаем (не field-sprint doc).
- Гейт G3 остаётся ровно: **«≥50 completed distinct portfolio scans ИЛИ ≥30 landing registrations»**. Счётчики регистраций и сканов не комбинируются и не конвертируются друг в друга, никогда. Registration count = только строка `landing_registration` в signals CSV; scan count = только completed scans per §3.2.
- Валидные evidence-типы: user-authorized экспорт-файлы, screenshots, manual inventory. Валидные GPT/agent-ассеты: Custom GPTs (classic GPTs), Workspace Agents, Skills, Projects, любой другой GPT/agent-тип ассетов.
- Никаких credentials не запрашиваем и не храним; персональные данные — минимизируются (§5).
- Никаких автоматизированных extraction'ов из OpenAI UI/API — fail-closed (§7).

## 3. Определение completed scan

**Ровно один completed scan** засчитывается при одновременном выполнении C1–C7:

| ID | Критерий |
|---|---|
| C1 | Ровно один уникальный `workspace_id` (owner/account/agency workspace), впервые появившийся в raw-регистре; одна workspace сущность = один вклад в счётчик, сколько бы ассетов и повторных сканов у неё ни было. |
| C2 | Зафиксировано `consent_scope`, покрывающее этот скан: записанное согласие владельца/workspace на инвентаризацию и хранение указанных артефактов. Согласие — отдельное, scoped, отзываемое; молчание/участие в интервью согласием на скан не являются. |
| C3 | Evidence существует на диске (пути в raw-записи) и покрывает либо весь портфель workspace (экспорт/screenshots/manually enumerated inventory — достаточно одного из типов), либо его явное подмножество, заданное полем `portfolio_subset`. |
| C4 | Из evidence получен **перечень как минимум одного GPT/agent-ассета** (имя/ID/тип — достаточно идентифицируемого минимума). |
| C5 | Заведён **timestamped summary** (`summary` в raw-записи + `scanned_at` ISO-8601): сколько ассетов, какие типы, ссылки на evidence. |
| C6 | Отсутствует статус ошибки/незавершённости: любой из статусов `failed`/`incomplete`/`invalid` обнуляет вклад (fail-closed). |
| C7 | Способ получения evidence — не automated extraction: ни скрейпинг UI, ни неофициальные API, ни массовый сбор через интерфейс от имени сервиса. |

### 3.1 Метод (человеческий процесс, $0)

1. Подтверждение согласия (C2) — recorded consent от владельца/workspace (email/письмо/форма; фиксируется `consent_scope` + дата).
2. Приёмка evidence (C3): участник по своему выбору присылает user-authorized экспорт-файлы, скриншоты или заполняет ручную инвентаризацию (что видно в его workspace: список GPT/агентов/скиллов). Хранение — только указанные в согласии артефакты.
3. Инвентаризация (C4): человек переносит из evidence перечень ассетов (имя, тип, наличие instructions/knowledge/actions — если видно) в timestamped summary.
4. Регистрация (C5): одна строка в `sprint-H1-scans-2026-08-29.csv` + файлы в `evidence-sprint-H1/scans/` (создаётся при первом скане).

### 3.2 Правила подсчёта

- Счётчик G3 = количество строк raw-регистра со статусом `completed`, уникальных по `workspace_id` (dedupe C1).
- `completed_at` проставляется при первом `completed` записи workspace. Повторные сканы/рефреш-данные той же workspace — `superseded`/`repeat`, счётчик не увеличивают (обновляются evidence/summary той же записи).
- Ретрай после `failed`/`incomplete` — это **та же запись** workspace (тот же `workspace_id`), счётчик двигает только переход в `completed`.
- Пересчёт всегда из raw-регистра сканов; счётчик нигде не хранится отдельно.

## 4. Формат raw-регистра evidence

Канонический регистр: `sprint-H1-scans-2026-08-29.csv` (одна строка = одна попытка скана workspace).

| Поле | Тип | Описание |
|---|---|---|
| `scan_id` | string | уникальный ID попытки (`scan-0001`, ...) — идентифицирует попытку, не участника |
| `workspace_id` | string | псевдоним участника (`ws-...`); ключ дедупликации. Никаких email/имён/URL профилей |
| `segment` | enum | `S1` (solo 5+ GPT) / `S2` (agency) / `S3` (Business/SMB admin) |
| `consent_scope` | string | что разрешено: `portfolio-inventory + evidence retention (email/письмо, дата)` |
| `consent_date` | date | дата фиксации согласия (ISO-8601) |
| `evidence_type` | enum | `export_file` / `screenshots` / `manual_inventory` |
| `evidence_paths` | string | пути к артефактам в `evidence-sprint-H1/scans/` (можно несколько через `;`) |
| `asset_count` | int | ≥1 для completed; 0 допустим только в failed/incomplete |
| `asset_types` | string | перечисление типов (`custom_gpt`, `workspace_agent`, `skill`, `project`) |
| `portfolio_subset` | string | `full` или описание непокрытой части; обязателен, если evidence не весь портфель |
| `status` | enum | `completed` / `failed` / `incomplete` / `invalid` / `superseded` / `repeat` / `duplicate` |
| `scanned_at` | datetime | timestamp summary (ISO-8601, момент завершения скана) |
| `completed_at` | date | дата первого `completed` этой workspace (dedupe-якорь) или пусто |
| `method` | string | свободное описание (напр. `manual-inventory-form`, `screenshots+form`) |
| `summary` | string | timestamped summary: перечень ассетов/типов, ссылка на evidence-файл |
| `notes` | string | причина статуса, ссылки на consent-артефакт |

Правила хранения: никаких credentials никогда; персональные данные — минимум (псевдоним workspace, без email/имён/URL в регистре; контакт для связи — вне регистра, в consent-канале). Evidence-файлы могут содержать PII из workspace участника — доступ ограничен, хранение в согласованном scope, удаление по отзыву согласия.

## 5. Примеры подсчёта (replicability-набор; синхронизирован с seed-строками CSV)

Ожидаемый счётчик G3 в каждом случае (после применения §3.2 к нижеприведённым записям, `P = ` значение счётчика):

| # | Сценарий | Записи в регистре | P = | Почему |
|---|---|---|---|---|
| EX1 | Валидный скан | `scan-0001`: `ws-alfa`, evidence = ручной реестр, 7 custom GPT, status `completed` | **1** | C1–C7 все выполнены |
| EX2 | Дубликат workspace | `scan-0002`: `ws-alfa`, new evidence, status `duplicate` | **1** | C1: та же workspace уже посчитана; повторный вклад не увеличивает счётчик |
| EX3 | Ретрай после провала | `scan-0003`: `ws-beta`, status `failed` (прислал пустую форму), затем `scan-0004`: `ws-beta`, status `completed`, 2 GPT | **2** | Ретрай = та же запись workspace, счётчик двигает только `completed` |
| EX4 | Незавершённый скан | `scan-0005`: `ws-gamma`, `manual_inventory` без перечня ассетов (asset_count=0), status `incomplete` | **2** | C6 fail-closed: incomplete не считается, несмотря на согласие и evidence |
| EX5 | Неподдерживаемый способ extraction | `scan-0006`: `ws-delta`, evidence собран авто-парсером UI ChatGPT (script), status `invalid` | **2** | C7: automated extraction запрещён (S21 ToS) — fail-closed даже при живом согласии |

Пять обязательных кейсов приёмки: EX1 valid → count; EX2 duplicate → no count; EX3 retry → счёт только `completed` ретрая; EX4 incomplete → no count; EX5 unsupported extraction → no count.

## 6. Пограничные случаи (fail-closed по умолчанию)

- Согласие получено, но evidence не доставлен в течение 14 дней → `failed`, счётчик не двигается; ретрай по §3.2.
- Evidence покрывает только часть портфеля → валидно (C3) при непустом `portfolio_subset`; полный охват НЕ требуется.
- Скриншоты без читаемого перечня ассетов → C4 не выполняется → `incomplete`.
- Согласие отозвано участником → строка помечается notes; evidence удаляется; счётчик уменьшается на 1, если workspace была `completed`.
- Участник присылает новые данные позже → `superseded`/`repeat` запись, счётчик на месте.
- Два скана от одной workspace в один день → первый по `scanned_at` — кандидат, второй — `duplicate`.
- Сомнительный кейс, не покрытый правилами → статус `invalid` (fail-closed), эскалация в комментарии карточки спринта.
- Автоматизированный сбор данных по протоколу до user-approvals B1–B4 → весь batch `invalid` (недопустимая фаза).

## 7. Границы протокола

- Не автоматизируем extraction из OpenAI (UI/API/скрейпинг) — до появления официального поддерживаемого и ToS-совместимого пути, подтверждённого первичным артефактом [S21][HIGH]. Если такой путь появится — это отдельное решение (новый ADR/Supersedes) и правка протокола, не молчаливое расширение.
- Не собираем credentials; не запрашиваем логины/токены/доступ к аккаунту.
- Не строим продукт: этот протокол — метод подсчёта полевой метрики, не MVP. Продвижение скана (упоминание в письмах/лендинге/постах) требует approval по B1–B4 — вне этой карточки.
- Минимизация PII: контактные данные участников живут только в consent-канале; в регистре — псевдонимы.
