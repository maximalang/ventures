# P0 COLLECTION CONTRACT — moderated paired workflow test (SPEC 2.0 §7.2 L181-205)

Статус: выпущен company-решением по карте t_0a65e710 (02.10.2026). Владелец контракта: company.
Binding: canonical SPEC C:/Users/max/Desktop/all/ventures/docs/rr-ai/SPEC-ai-summary-assist.md,
sha256=65f28c45b4ce43aa5004613386ed2515aaf8db9a10a6267963df3d411e408067 (292 строки / 74965 байт) — НЕ изменять.
Decision record: C:/Users/max/Desktop/all/ventures/docs/rr-ai/COMPANY-DECISION-t_0a65e710-P0-GO.md
Потребитель: карта сбора (assignee research, task_type marker в её body). Вердикт-правила: SPEC L199-205 + F-1 resolution ниже.

## 0. Что это и чем не является
P0 = qualitative discovery-тест гипотезы H1 (агрегат по всему профилю сокращает время до корректного дневного плана ≥20% без потери grounding). НЕ A/B c power-claims, НЕ production trial, НЕ доказательство пользы LLM (H3), НЕ строительство. Treatment-агрегат строится исследователем детерминированно из тех же фактов; честная маркировка обязательна: «исследовательская агрегатная сводка; не LLM». Успех P0 ≠ GO на build/LLM.
Роли: research (эта карта) = owner сбора evidence; product = lead интерпретации (отдельная lane после QA-верификации); qa = независимая валидация fixtures до первого наблюдения и верификация собранных наблюдений (дочерняя карта); company = business verdict на analysis_at.

## 1. Timeline (pre-committed; без post-hoc сдвигов порогов)
- Phase A (подготовка): немедленно после диспатча; дедлайн 2026-10-05T18:00:00+03:00 — к дедлайну обязаны существовать: 5 подписанных согласий подходящих участников, QA-валидированные fixtures обоих кейсов, замороженные assignment/sequence/seed и case key, объявленный frozen start_at.
- Промежуточный статус-комментарий на карту: 2026-10-04T18:00:00+03:00 (recruitment/fixture прогресс, риски, блокеры) — даже если пусто.
- frozen start_at: planned 2026-10-06T10:00:00+03:00; объявляется комментарием на карту ДО первого наблюдения; если подготовка не готова к planned-значению, worker фиксирует одно новое start_at (не позднее 2026-10-09T10:00:00+03:00) тем же комментарием-фиксацией. Позднее 2026-10-09T10:00:00+03:00 старт не фиксируется — вместо этого завершение карты с честным verdict NEEDS-EVIDENCE (причина: recruitment/fixtures не готовы), без продлений.
- analysis_at = frozen start_at + ровно 7 календарных дней (planned 2026-10-13T10:00:00+03:00). Единственная фиксированная точка; не двигается (исключение: safety STOP → немедленная остановка, не перенос). Рабочий прогон сессий не обязан ждать analysis_at: сессии проводятся внутри окна (цель: все сессии ≤72ч от start_at), датасет морозится и карта завершается сразу после последней сессии; вердиктные lane (QA-верификация → product → company) чтят analysis_at как точку business verdict (досрочно — только safety STOP).
- Две попытки сбора без новых evidence/участников = уменьшить scope / сменить разрешённый тест / STOP. Не переносить next action бесконечно.

## 2. Phase A1 — recruitment (5 реальных участников)
Критерий «подходящий»: рекрутёр/BD небольшого агентства, который сам выбирает компании для работы (персона SPEC §3). Соискатели, candidate-sourcing по резюме и outbound-агенты — не подходят.
Разрешено: индивидуальные добровольные приглашения через собственные research-каналы флота; письменное информированное согласие (цель исследования, псевдонимизация, добровольность, отказ в любой момент, отсутствие влияния на продукт/feedback, хранение identity/consent в закрытом research-процессе ВНЕ публичного repo и вне kanban).
ЗАПРЕЩЕНО: mass outreach (рассылки/потоковые DM), личные аккаунты владельца, платные панели/инсайты, любое вознаграждение деньгами (cash cap 0 RUB), синтетические/выдуманные участники, принуждение.
Участники НЕ получают доступ к production-данным чужих workspace; кейсы = исследовательские профили (п.3), не live-профили участников.
Если к дедлайну Phase A каналов/согласий не хватает: kanban_block(kind=needs_input) с ТОЧНОЙ формулировкой одного вопроса владельцу (реферал 5 добровольных agency-рекрутёров: да/нет/контакты) — company маршрутизирует вопрос владельцу одним form; НЕ снижать планку до 4 участников, НЕ фабриковать.

## 3. Phase A2 — fixtures (2 matched profile-level кейса)
Каждый кейс = ВЕСЬ исследовательский профиль + пара сопоставимых срезов (previous/current):
- только реально проверенные публичные company-level facts с reproducible URLs и зафиксированными as-of (published/observed time); НИ live DB dump, НИ выдуманные leads/deltas/previous-срезы;
- ≥10 различных компаний на кейс; доказанная history (реальные опубликованные даты, позволяющие честный previous/current срез); ≥1 проверяемый cross-lead pattern/quality risk;
- исследовательский профиль честно обозначен как исследовательский (не выдаётся за production-профиль участника); все lead records присутствуют; профиль не урезается ради top-N;
- кейсы matched по: числу компаний/изменений/рисков, сложности, сегменту, качеству evidence; у одного участника профиль/компании не повторяются между arms;
- control = полная очередь/карточки того же разрешённого набора фактов с существующим deterministic rank/brief-стилем (без нового агрегата); treatment = те же данные + один детерминированный исследовательский агрегат профиля: coverage/as-of, delta (новые/изменённые/без изменений/неподтверждённые), top-строки текущего приоритета (≤5), описательные группы/риски с denominators, существующие manual actions. Никакого нового scoring/action engine/нового evidence; treatment не получает более свежие/богатые данные, чем control;
- первый срез без previous честно помечается «изменения неизвестны», не «всё новое/рост».
Артефакты: fixture bundle (файлы кейсов + source refs + as-of таблица + case key + assignment/sequence/seed) в durable path C:/tmp/rr-p0-evidence/fixtures/ + sha256 каждого файла; копия natively attached к карте.

## 4. Phase A3 — freeze
До первого наблюдения заморозить (комментарием на карту + файлами в bundle): case key, assignment/sequence/seed (ABBA/BAAB counterbalance насколько позволяет N=5; пары и порядок не меняются после freeze), frozen start_at, тайминговую схему сессий, измерительные поля (п.6). Рабочий профиль/timeline/контрольная сложность фиксируются, не выбираются по результату.

## 5. Phase A4 — независимая QA-валидация fixtures (ДО первого наблюдения)
Механика (точная): kanban_create одной qa-карты (assignee qa, marker review-типа первой строкой body) c deliverable: проверить полный inventory каждого кейса, сопоставимость previous/current, case key, честность маркировки, matched-критерии, отсутствие фабрикации (spot-check ≥5 source URL на кейс + as-of), sha256 bundle; verdict PASS/FAIL словом + хэши. Затем kanban_link(parent_id=<qa-карта>, child_id=<эта карта>) и kanban_block(kind=dependency) — авто-резюм после завершения qa-карты. НЕ опрашивать статус qa-карты циклом (identical_call_loop).
QA FAIL → исправить fixtures, ОДНА повторная валидация; второй FAIL → завершить карту verdict NEEDS-EVIDENCE (причина: fixtures не прошли независимую валидацию). Третья попытка — только с новым evidence и через company.

## 6. Phase B — сессии и measurement (внутри 7-днeвного окна от frozen start_at)
Задача участника (обе arms, по каждому кейсу): по всему профилю назвать главное изменение/unknown; выбрать до трёх первых ручных проверок и их evidence; отметить один подтверждённый cluster/risk и следующий безопасный шаг. Это study plan, НЕ реальные contacted/accepted outcomes.
Поля измерения на наблюдение: псевдоним участника, case/arm/spec/snapshot/criteria version, coverage/unique-company counts, start/end, plan_seconds (включая source/coverage/delta-проверку, не только чтение заголовка), выбранные plan/evidence refs, материал для independent grounding verdict, can_explain_delta / can_explain_next_step (без подсказки модератора), missing/censored flags, manual prep time.
Timeout одного полного profile-case = 480s → запись censored at480 с отдельным timeout/failure status; НЕ successful fast plan и НЕ удалённое наблюдение. Недостающие строки не выдумывать и не удалять.
ЗАПРЕЩЕНО во время сессий: любые записи feedback в продукт за участника (feedback_status неприкосновенен); live LLM-вызовы; изменения core/лендинга; раскрытие чужих/private данных. Немедленный STOP при: раскрытии чужих/private данных, изменении core, неразрешённом обращении/spend, материальном unsupported fact — отчёт включает инцидент, исключённый от показа output и rollback; карта завершается с инцидент-отчётом.

## 7. Датасет и завершение карты
- Целевой датасет: 20 полных uncensored планов (5 чел × 2 arms × 2 кейса; 10 на arm, 4 на человека). N=5 людей, НЕ 20 независимых пользователей; три top-строки ≠ три independent users/accepted leads.
- Дurable path: C:/tmp/rr-p0-evidence/dataset/ (raw observations + session logs + recomputation-скрипт) + sha256 манифест; sensitive identity/consent — отдельно в закрытом research-хранилище (путь в handoff, доступ ограничен; ВНЕ repo/kanban/артефактов).
- Завершение карты: сразу после freeze датасета (до analysis_at). Handoff metadata: sha256 датасета, counts (n_plans/censored/missing), recruitment outcome, frozen start_at/analysis_at, consent complete (да/нет), safety violations (0/…), финансовые поля: cash spend 0 RUB (факт), labor time записан, labor cost estimate null (не оценивался). next_owner: qa (дочерняя верификационная карта стартует автоматически); business verdict — company на analysis_at.
- Если полный uncensored датасет 20 планов не собран: честный verdict NEEDS-EVIDENCE с точными missing-причинами (участники/inventory/history/контроль/наблюдения); НЕ синтетический успех, НЕ продление окна.

## 8. Вердиктные правила (применяют QA-верификация/product/company, НЕ сборщик)
Pre-committed, SPEC L199-205 на hash 65f28c45… + company F-1 resolution (t_0a65e710):
- ITERATE-кандидат (минимальный bounded aggregate slice; НЕ automatic build/LLM GO): 5/5 участников с четырьмя полными uncensored наблюдениями (20); median r_i ≤ 0.80 где r_i = median plan_seconds treatment / median plan_seconds control внутри участника; ≥4/5 в обоих treatment-кейсах без помощи верно объясняют delta/unknown, evidence и next step; доля independently useful plans у treatment НЕ НИЖЕ control ни pooled, ни внутри каждого участника (правило «3 п.п.» из LABEL NOTE t_a5071b8b 00:57 ОТМЕНЕНО — anchor = текст SPEC на hash); safety violations = 0.
- Useful plan = faithful delta/unknown + grounded приоритетные строки + корректный cluster/risk + допустимый next step; неподтверждённый материальный факт не компенсируется быстрым временем.
- NO-GO для AI-строительства: полные данные не проходят правило; если проблема оказалась source/fit — вернуть владельцу D1/D2, не лечить генерацией.
- NEEDS-EVIDENCE: нет 5 согласившихся подходящих участников / полного inventory-history-проверок / сопоставимого контроля / полного uncensored датасета 20 планов.
- Timeout может выявить usability-проблему, но не выдаётся за уверенную causal победу/поражение. Даже успех P0 доказывает максимум полезность исследовательского агрегатного формата на prepared cases — НЕ production coverage/history, daily-use, willingness-to-pay, F2-F4 по отдельности или преимущество LLM.

## 9. Границы, бюджеты, инструменты
Cash cap 0 RUB; бюджет null; без live LLM, без новых провайдеров, без платных API/панелей/подписок; никаких платежей. Внутренний труд записывается, денежная оценка null.
Без mass outreach и личных аккаунтов владельца; research-суждения НЕ влияют на продуктовый feedback contacted/accepted.
Инструменты: execute_code у воркеров запрещён политикой — обработка данных через write_file-скрипт + terminal python; длинное ожидание — background+notify, не polling; heartbeat при долгих операциях; в тексте terminal-команд избегать денежных токенов и литералов gate-маркеров; секреты/env-файлы не читать; live-DB мутации запрещены; артефакты держать в durable path (scratch затирается).
