# Recruiter Radar — SPEC: агрегатная AI-сводка всех лидов профиля и помощь рекрутёру

Версия: 2.0, 02.10.2026 (MSK). Scope correction по уточнению владельца, доставленному после первичного handoff.
Task: rr-team / t_18026ee9. task_type: research.
Product lead: product. Бизнес-решение: company. Независимые gates: qa / finance.
Статус: NEEDS-EVIDENCE для пользовательской ценности и LLM-реализации; готовый продуктовый brief, НЕ разрешение на строительство, merge, deploy или spend.

## 1. Решение и граница фазы

Обязательная граница: AI-сводка = АГРЕГАТ ПО ВСЕМ ЛИДАМ ПРОФИЛЯ рекрутёра, а не пересказ отдельного лида. Ядро — кросс-лидовая картина: что новое/изменилось с прошлого среза, приоритеты на сегодня, кластеры/паттерны, аномалии/риски и рекомендованные ручные действия. Per-lead элементы допустимы только как строки внутри агрегата (топ-N, изменения, evidence refs); отдельная AI-сводка компании НЕ является deliverable и не добавляется в карточку лида. Карточка уже содержит информацию о нём. Генерация сообщения не является ядром, отдельной стадией воронки или критерием готовности.

Источник scope: исходная директива в t_18026ee9 + company comment от 02.10 00:30 MSK с уточнением владельца (01.10 22:5x), дословно: «ai сводка должна быть по всем лидам профиля а не по одному, зачем делать по одному если в лиде уже есть вся инфа?» Уточнение переопределяет исходную формулировку «по каждому лиду» в opening body. Версии 1.0/1.1 и completion по 1.1 — superseded для актуального acceptance; их per-lead hypothesis, эксперимент на 60 решений и tech scope больше не основание для GO. Это явная коррекция, не молчаливый artifact drift.

Пользовательская единица результата — один агрегат выбранного профиля на указанное время среза, с сопоставимым предыдущим срезом, а не N сгенерированных lead summaries. Анализ охватывает весь разрешённый профиль, независимо от текущей страницы списка, viewport, локального UI-фильтра или ограничения показанных топ-N строк. Нельзя выдать анализ первых N лидов за сводку всего профиля. Условия полноты, сравнимости и безопасного partial-mode определены в §5.

Рекомендация product: сначала независимый review этого SPEC, затем company выбирает дешёвый тест потребности. Не открывать реализацию трёх условных tech briefs из §9 до отдельного GO. Полезность формата информации и полезность LLM — разные гипотезы. Сначала проверяется первая.

Фаза этой карты = переопределение scope и проверяемый план. Изменение accepted_evidence_backed_leads_28d, спрос, выручка и готовность AI в production этой картой НЕ доказаны. product остаётся lead гипотезы до фазовой рекомендации по наблюдениям; company владеет continue / iterate / kill и назначает следующий измеримый task. Передача документа не означает завершённый продуктовый outcome.

Не входит: изменение лендинга/демо/маркетинговой копи, новые источники, изменение scoring/ranking/gates, CRM-автоматизация, поиск персональных контактов, агент с доступом к инструментам, массовые обращения, новая доставка AI-текста, новая платная capability. Эта карта не открывает PR261 и не возвращает его в merge-lane.

## 2. Problem evidence и неизвестное

### 2.1 Проверенные основания

E1. Канон primary metric: C:/Users/max/Desktop/all/ventures/PORTFOLIO.md:17-20 — accepted_evidence_backed_leads_28d. Публичные признаки найма и факт действий пользователя важнее числа AI-запросов.

E2. Детерминированная по-лидовая сводка уже есть: apps/web/lib/leads/company-summary.ts:1-60, 65-128. buildCompanySummary возвращает identity, hiringMotion, agencyRelevance, strength, isThin; при слабых данных говорит меньше. Это существующая информация в карточке, не новый deliverable и не доказательство готового агрегата профиля. Вызывается из app/leads/[id]/page.tsx и app/api/leads/[id]/route.ts. Не добавлять рядом вторую AI-сводку того же лида; baseline эксперимента — вся нынешняя рабочая очередь и её карточки (§7), а не один buildCompanySummary.

E3. Рабочий brief уже есть: apps/web/lib/opportunities/opportunity-brief-builder.ts:5-50, 65-87. OpportunityBriefBuilder выдаёт whyNow, problemHypothesis, recommendedAction, agencyFitExplanation, limitations. Код прямо не подтверждает готовность компании работать с агентством или конкретного ЛПР.

E4. Evidence-first boundary: apps/web/lib/ai/boundary.ts:1-15, 26-66, 95-109. AI может пересказать/объяснить уже рассчитанное, но не менять score, confidenceGate, evidence, lawfulContactPath, suppression и не отправлять сообщения. Наличие AiAssistProvider hooks в assist-types.ts:188-193 само по себе не подтверждает доступную функцию.

E5. D3 status-handoff проверен отдельно: t_1db3c461; https://github.com/maximalang/recruiter-radar/pull/261 — CLOSED, mergedAt=null, head=6c6f615da8685148fad96903814d6c3dc633633f. Preserved checkout C:/tmp/rr-d3-draft имеет тот же HEAD. По handoff реальных LLM-вызовов не было. Пройденные mocked/unit/DB-проверки draft-lifecycle не являются доказательством новой сводки или спроса на неё.

E6. Существующее AI-enrichment не путать с новой функцией. apps/web/lib/ai/enrichment/enrichRunCandidates.ts и ai/providers/firecrawl.ts используют карьерную страницу как extraction-путь; это не доказательство работающего интерактивного summary-assistant. llm-config.ts:1-22, 41-82 — конфигурационный seam с operator override/env, не проверка доступности провайдера на production.

E7. Текущий dashboard считает accepted по feedback_status contacted/replied/meeting/won за 7 и 30 дней, на строках digest_candidates: apps/web/lib/dashboard-data.ts:93-129. Это не готовый 28-дневный, evidence-backed, deduplicated primary metric. Особенно нельзя брать COUNT кандидатов за фактическое число уникальных принятых компаний.

Код E2-E4/E6/E7 прочитан в checkout f3e87a13b9a2564f90698657954c0a0abda162ee. Scoped git diff относительно remote main a043fe8c20246b44becf2c80fb34695d0961ff36 не показал изменений в этих inspected модулях. Поэтому ссылки на код можно воспроизводить на main anchor a043fe8c. Юридические страницы отличаются между checkout и main; их нельзя переносить между HEAD без проверки (§6).

### 2.2 Что НЕ установлено

Интервью/наблюдения по новой потребности: null — в этой карте не проводились. Частота трудности, время на план работы по всему профилю, число активных подходящих рекрутёров, готовность платить за AI: null. Baseline primary metric: null — DB/customer datasets не читались. Наличие полного profile-level inventory, доступных сопоставимых исторических срезов, устойчивых lead identities и готового cross-lead aggregator в production НЕ подтверждено. Не считать dashboard counters или per-lead summary реализацией нового scope. Стоимость LLM и доступный остаток project monthly budget: null — не проверялись. Это не нули и не повод выдумать uplift.

Owner direction — evidence приоритета и scope, но не доказательство потребительского спроса. Код доказывает доступные механизмы, а не то, что рекрутёр их понимает или принимает больше лидов. Дизайн/архитектура принадлежат ux/design/tech; этот SPEC задаёт пользовательский outcome и границы, не выбирает layout, DB schema или API.

CHARTER.md и STATE.md в RR root не найдены (direct reads + targeted file search). Доступный runtime-context документ — docs/CURRENT_STATE.md; task truth остаётся Kanban и точные SHA, а не перенос старого документа в текущий runtime. Канон ventures/README.md, AGENTS.md, OPERATING_SYSTEM.md и APPROVALS.md прочитан. Пробел не разрешает самостоятельно менять портфельную метрику.

## 3. Пользователь, JTBD, outcome и falsifiable hypotheses

Целевая персона — рекрутёр/BD небольшого агентства, который сам выбирает компании для работы, имеет настроенный market profile и просматривает evidence-backed leads. Это предлагаемая сегментация, а не подтверждённое описание всех клиентов. Исключены соискатели, подбор кандидатов по резюме и самостоятельный outbound-agent.

JTBD: «В начале рабочей сессии покажи картину по всем лидам моего выбранного профиля: что изменилось с прошлого среза, где сосредоточены подтверждённые поводы и риски и с чего начать сегодня, чтобы составить проверяемый ручной план работы, не открывая каждую карточку ради общей картины».

Текущая альтернатива: рабочая очередь целиком, существующие фильтры/порядок и детальные карточки с evidence + buildCompanySummary / OpportunityBriefBuilder. Предполагаемая проблема — ручная сборка кросс-лидовой картины и плана из отдельных карточек, НЕ отсутствие информации в одной карточке и НЕ отсутствие генератора письма. Owner direction устанавливает именно этот job; реальный bottleneck ещё нужно наблюдать.

H1 (самая рискованная). Агрегат по всему профилю уменьшает время составления корректного дневного плана минимум на 20% против нынешней очереди и карточек при том же составе исходных данных, без ухудшения independently audited grounding/качества плана. Если проблема в качестве/релевантности данных или текущих фильтров, а агрегат не помогает, гипотеза отклоняется; не лечить источник/fit генерацией.

H2. Не менее 4 из 5 подходящих участников в обоих treatment-кейсах без подсказки модератора верно отличают изменение от неизменного, находят supporting evidence и объясняют допустимое следующее ручное действие из агрегатного плана. Если участник принимает изменение состава профиля за рост найма, неподтверждённый кластер за рынок или top-N за полный охват — формат не принимается.

H3 (только после H1/H2). LLM даёт добавочную пользу поверх полезного детерминированного агрегата: тот же корректный profile-level план быстрее, при полном grounding, полном охвате профиля и ограниченной стоимости. Если выигрывает только структурирование данных, оставить deterministic implementation; LLM не обязателен. Успех P0 не доказывает H3.

Причинная цепочка к primary metric: меньше времени на сборку картины и плана по профилю → больше корректно выбранных и проверенных компаний за рабочую сессию → больше реальных evidence-backed компаний, взятых в работу. На данный момент все стрелки — гипотезы. Агрегат, его строки, показ top-N, AI-generation, copy-to-clipboard и субъективное «полезно» не равны primary outcome и не создают новый accepted lead.

## 4. Scope: ровно четыре кандидатные функции

Это четыре части одной профильной сводки/помощи, не четыре разных генератора по компании. Верхняя граница scope после GO, не активный backlog. P0 проверяет минимальное агрегатное представление F1 с уже вычисленными строками приоритетов, паттернов/рисков и ручных действий; оно не доказывает каждый F2-F4 отдельно или пользу LLM. Постоянную автоматическую генерацию/новую cadence не обещать.

### F1. Агрегат всех лидов профиля и изменения с прошлого среза

User story: как рекрутёр, начинающий день, я хочу увидеть полный срез моего профиля и отличия от последнего сопоставимого среза, чтобы понять, что действительно требует внимания, без последовательного пересказа каждой карточки.

Связь с primary metric: гипотеза — сокращение времени на сборку картины освобождает время для корректной ручной проверки и взятия evidence-backed компаний в работу. Leading measure — время до independently grounded profile-level плана; ни агрегат, ни его delta не увеличивают accepted_evidence_backed_leads_28d сами по себе.

Вход: весь server-authorized lead inventory выбранного workspace/profile на cutoff, версии evidence/статусов и сопоставимый предыдущий успешный срез (§5). Результат: один агрегат «Сводка профиля», current/previous as-of и coverage; сколько новых/изменённых/без изменения и сколько данных не подтверждено; приоритеты, кластеры, риски, действия из F2-F4. Детали отдельных лидов — только короткие строки изменений/топ-N со ссылками на уже существующие карточки, не отдельные summary-блоки или N LLM-запросов. Список всех contributing IDs доступен для проверки полноты без передачи private content.

AC:
- При полном разрешённом наборе обработаны все страницы/лиды профиля; changing viewport/UI filter/top-N не меняет aggregate denominator. Число строк на экране не число анализируемых лидов. Несколько профилей одного владельца не объединяются без нового scope-решения.
- Новый = появился в составе профиля после previous cutoff; изменённый = был в обоих срезах и имеет подтверждённую смену evidence/состояния/ограничений. Дубли одного факта и повторное сканирование не объявляются новым наймом; source published/observed times не заменяются временем генерации.
- Первый срез показывает «Нет предыдущего среза — изменения неизвестны», а не «всё новое»/«рост». Несопоставимые profile criteria/scope дают новый baseline и явную причину; удалённые/отозванные данные не выдаются из старого cache.
- Пустой полный профиль честно пуст; incomplete inventory/ошибка страницы/context overflow показываются как partial/unavailable с причиной. Без доказанной полноты запрещены «по всем лидам», глобальные top/cluster claims и выдуманные zero deltas. Без AI доступны исходная очередь и детерминированные данные.

### F2. Приоритеты на сегодня внутри агрегата

User story: как рекрутёр, я хочу видеть, с каких компаний моего полного профиля начать сегодня и почему, чтобы выбрать первые ручные проверки с учётом изменений, свежести и рисков, а не читать ещё один пересказ каждой компании.

Связь с primary metric: гипотеза — быстрее выбираются подтверждённые пригодные компании и меньше времени тратится на неподтверждённые/устаревшие. Leading measures — время до первых обоснованных действий и доля grounded планов; показ приоритета не accepted outcome.

Вход: полный inventory F1 + текущие deterministic rank/order, policy/suppression/entitlement и уже рассчитанные причины. Результат: до пяти actionable строк в агрегате — company/lead ref, подтверждённый повод внимания, дата, ограничение, следующий ручной шаг. Top-N — только ограничение представления, не отбора input. Порядок следует существующему допустимому ranking; фильтр актуальности/доступности объясняется, не превращается в AI-score. «Сегодня» — время плана и freshness cutoff, не обещание ежедневного ingest.

AC:
- Просроченные/недоказанные и suppressed записи не становятся actionable; если нет пригодных строк — сказать это и показать причины/unknowns, не заполнить пять мест выдумкой.
- Повторные leads одной компании не создают несколько top-строк; число лидов и уникальных компаний различается явно. Ссылки ведут в существующие разрешённые карточки, не в новую F1-per-lead страницу.
- AI не пишет score/priority/профиль/scan plan, не меняет core order/gates, не добавляет кандидатов, не увеличивает лимиты и не засчитывает план как действие. Неполный профиль не объявлять глобальным топом.

### F3. Кросс-лидовые кластеры, паттерны, аномалии и риски

User story: как рекрутёр, я хочу видеть группы похожих подтверждённых сигналов и проблемы по всему профилю, чтобы отличить концентрированный повод для работы от дублей, устаревших данных или нехватки evidence.

Связь с primary metric: гипотеза — меньше ложных принятия/повторной проверки и лучше распределение ручной работы по пригодным компаниям. Leading measures — grounded обнаружение паттерна/риска и качество дневного плана; размер кластера и предотвращённое ложное принятие не положительный accepted outcome.

Вход: полный F1 и только уже подтверждённые company/role/segment/signal/freshness признаки; недоступный признак = unknown. Результат: кластеры по известным признакам с количеством лидов и уникальных компаний, долей/denominator и supporting members/refs; риски — дубль/source-family concentration, expired/тонкий/conflicting evidence, перекос покрытия. Изменение кластера возможно только по сопоставимым срезам. Конкретный алгоритм выбирает tech; definition/rule и ограничения показываются и проверяются, не придумываются моделью.

AC:
- Кросс-компанейный паттерн требует минимум двух различных компаний с supporting facts; одинаковый факт в десяти карточках/синдицированных источниках не десять независимых сигналов. Overlapping groups и unknown-признаки не скрываются ради красивой доли.
- Нет extrapolation «растёт рынок/бюджет/готовность агентству»: наблюдения ограничены данным профилем, выборкой и интервалом. Нет статистической «аномалии» без определённого baseline/rule; первый срез даёт описательные группы/риски, тренд unknown.
- Каждое число воспроизводимо из contributing set; вывод ссылается на агрегатное правило и supporting evidence. Unsupported pattern/citation отбрасывается. Risk flags не меняют source facts, score, eligibility или suppression.

### F4. Рекомендуемые ручные действия и bounded помощь по контексту профиля

User story: когда общая картина ясна не полностью, я хочу получить объяснимый следующий план и ответ на ограниченный вопрос по изменениям/кластерам/рискам моего профиля, чтобы самостоятельно решить, что проверить, взять в работу или отложить.

Связь с primary metric: гипотеза — fewer зависших проверок и больше реально выполненных разрешённых действий по evidence-backed компаниям. Leading measures — объяснимость плана, supporting evidence и допустимость шагов. Только реальные manual outcomes по утверждённому контракту участвуют в accepted_evidence_backed_leads_28d; вопросы/ответы/план/клики не accepted.

Вход: тот же агрегат и разрешённый профильный context; выбранная тема — «что изменилось», «почему эта группа/приоритет», «какие данные требуют проверки», «что сделать следующим». Результат: ограниченный план проверки источников/fit/отложения/ручной проверки существующего corporate path со ссылками на строки агрегата и факты. Ответ не открывает отдельную сводку лида; точный lead/evidence ref допустим как обоснование строки общего плана. Вне набора — честное «неизвестно».

AC:
- Не универсальный чат, не свободный web-research и не agent. Нет browsing/tool execution, загрузок резюме, многопользовательской памяти, новых компаний/контактов и raw free-text forwarding провайдеру.
- Не восстанавливает неизвестного ЛПР/личный контакт и не советует обходить no_personal/corporate_only. Corporate path не разрешение на массовую рассылку. Действия выполняет только человек; никаких send/CRM write/auto-accept/suppression write/автоизменения профиля.
- При устаревшем/несопоставимом/чужом context — refusal/fallback. Никаких инструкций из исходной вакансии/страницы вместо bounded темы пользователя. Каждый next step отделён от фактов/unknowns и имеет проверяемое основание.

Опциональный черновик сообщения — возможный поздний helper внутри помощи, default off. Только по явному запросу рекрутёра, без фоновой/автоматической генерации; текст редактируется человеком, подтверждение не отправляет сообщение. Не входит в первый эксперимент, current AC или F1-F4. Возможное включение требует отдельного evidence/решения company; сохранённый PR261 сам по себе не разрешение. Детерминированный opener, если уже есть в продукте, не объявлять новым AI-доказательством и не ломать.

## 5. Данные, grounding и human control

Обязательный контракт результата (смысловые поля, конкретную schema/API выбирает tech): привязка workspace/profile/criteria version; current и previous snapshot/cutoff, сравнимость и причина отсутствия previous; полный contributing lead set и отдельно уникальные компании; coverage total/accounted/withheld/missing с определением denominator; delta/group/top/action facts и supporting refs; отдельно hypotheses/recommendations/unknowns; source published/observed time и freshness; attribution deterministic / investigator / AI; provider/model/prompt version, trace id; complete/partial/unavailable и fallback reason. org/lead ref — внутри строк, не единица новой summary generation. Не использовать ai_opener_draft как хранилище сводки.

### 5.1 Полный профиль, snapshot и сравнимость

- «Все лиды профиля» = полный server-authorized inventory выбранного profile_id на фиксированный cutoff по действующему membership/read contract. Это не последние N digest_candidates, не только текущая страница, не только top-N и не все профили workspace. Сохраняется учёт исходных lead identities; duplicate company/evidence помечается и не раздувает count компаний/независимых сигналов. Нет доступа — нет фактов/IDs из чужого scope.
- Все разрешённые записи учитываются; уже обработанные/архивные/expired/suppressed не становятся новыми actionable leads. Ограниченные policy-записи допустимы только в разрешённых status/quality counts, без раскрытия запрещённого содержимого/refs и без передачи их текста модели. Если сам count недоступен — unknown, не утечка скрытого количества.
- complete требует доказанного total и полного accounted inventory с объяснимыми категориями included/withheld; missing=0. Withheld по действующей политике не скрытый пропуск: причина и scope описаны. Незавершённая пагинация/ошибка/неизвестный total/context limit = partial/unavailable, не 100% coverage. Текст может быть коротким, но анализ не обрезается молча.
- current и previous — успешные сопоставимые срезы того же профиля/criteria/read scope; время генерации и source freshness разные поля. Нельзя сравнить current page с прошлым whole-profile набором. Опоздавший ingest отличать от нового опубликованного сигнала. Membership/state change не объявлять новым фактом найма.
- Смена критериев/прав/нормализации identity требует явной маркировки несопоставимости/нового baseline. Первая генерация не доказывает delta; отсутствие history = unknown. Last successful snapshot не продвигается после failed/partial generation. Подготовленный snapshot не подтверждает, что пользователь видел предыдущий; «с прошлого среза» не «с последнего визита».
- При revoked/delete/suppression change права проверяются повторно перед выдачей агрегата и каждой ссылки. Старые cached/historical факты с потерянным доступом не показываются. Не хранить приватные удалённые данные ради сравнения; точные retention/storage/API решения принадлежат tech/privacy owner.

### 5.2 Grounding агрегата и human control

AI — необязательный presentation/assist слой над core. Все source IDs/URLs в ответе разрешаются сервером по исходному разрешённому bundle; модель не создаёт ссылки. Валидный id недостаточен: исходный факт должен семантически поддерживать весь тезис. Числа, даты, сравнения и вывод о найме проверяются по фактам, не «confidence» модели. Коммерческая готовность — unknown, пока нет отдельного evidence.

Требования:
- read-only protected core; assertNoOverride — дополнительная защита, а не единственная гарантия;
- supplier text = данные, не инструкции; bounded input, allowlisted fields, prompt-injection tests, output validation до показа;
- новый/изменённый/expired evidence, изменённый profile scope и revocation доступа инвалидируют старый результат; нельзя продолжать показывать cache после потери доступа;
- минимум company-level public facts; одинаковые public facts не дают права читать результат другого workspace;
- неизвестное отсутствует/null с причиной, не превращается в 0, новый факт или «надёжного клиента»;
- counts/deltas/groups/denominators воспроизводятся из полного permitted contributing set и сопоставимых срезов; top-N display не data sampling и не новый evidence. Кластер не source, несколько leads не независимые подтверждения одного факта;
- hard input/output/time limits не разрешают silent truncation профиля: если безопасный полный агрегат невозможно построить — partial/unavailable и существующая очередь. Разбиение/предагрегацию решает tech, не подменяя acceptance «весь профиль»;
- при unsupported fact/schema/citation mismatch AI-результат не показывается; baseline и reason сохраняются;
- без провайдера, при timeout/429/ошибке/quota/budget отказе рабочая карточка остаётся доступной; нет бесконечных retry.

Пользовательское принятие лида — только существующее ручное feedback-действие. AI не нажимает его, не пишет outcome и не инициирует сообщения компаниям. Existing consented delivery пользователю — отдельный D4 pipeline; отправка компании и доставка дайджеста пользователю не одно и то же. В первой версии новая сводка остаётся в кабинете: payload и cadence каналов не расширяются.

## 6. Privacy, стоимость и ограничение риска

Privacy baseline main anchor: C:/tmp/rr-d3-draft/apps/web/app/privacy/page.tsx:92-95, 113-132 (D3 checkout наследует main по этому файлу): company-first/minimization, ограничение получателей, RF localization и отсутствие внешней аналитики в аккаунте/onboarding. Не трактовать страницу как юридическое одобрение нового LLM-процессора. Документы docs/legal/data-map.md и processor-register.md, прочитанные в основном checkout, отличаются от main; старые заявления о channels/processors не переносить в launch claims. Проверка актуальных processor/retention условий — до реального LLM-пилота.

Не уходят в LLM: имена/личные контакты сотрудников и пользователей, resumes, billing/auth identifiers, chat IDs, private agency/client notes, raw HTML/full dumps, полные arbitrary профили, токены, подписанные URL/query parameters, свободные пользовательские инструкции. Допустимый кандидатный payload — публичные company facts + обезличенные заранее вычисленные fit-пояснения. Если нельзя гарантировать минимизацию/разрешённость — deterministic only.

В аналитике/логах нет prompt/response, текстов вопросов, профилей или контактов. Нужны только внутренние scoped IDs, вариант/версия, времена, status/fallback code, количества, provider/model/trace, токены и денежный scope. Клиентская аналитика не должна обходить opt-in/закрытые списки /api/landing-events. Не добавлять Яндекс Метрику в кабинет. Исследовательские материалы — псевдонимы участников и минимальные observations; identity/consent остаётся в разрешённом закрытом research-процессе, не в публичном repo.

Cash cap данной карты и первого non-LLM теста: 0 RUB. Фактический spend этой карты: 0 RUB; реальных LLM calls: 0. Внутренний труд не объявляется бесплатной экономикой: время записывается, его денежная оценка пока null.

Для возможного LLM-пилота: отдельные decision:company и независимый gate:finance с существующим provider capability, price source/currency/period, daily/workspace/project cap, allowlisted routing, bill/usage readback. Бюджет до этого = 0; real calls запрещены. Existing CodeXoid/OpenAI config в коде не доказывает credentials, prepaid/free quota или юридически допустимый fallback. Не покупать/регистрировать новый платный провайдер и не обходить закрытый route автоматически другим поставщиком.

Product ограничения для tech/finance: не более одного provider attempt на согласованную профильную aggregate generation/version; нет автоматических N per-lead calls. Reuse/cache при неизменном полном bundle/scope/snapshot; hard input/output/time limits без молчаливого усечения профиля; независимые per-profile/per-workspace и project money caps; concurrent reservation до запроса. Cost scope включает весь агрегат, а не только показанные top-N строки. При unavailable shared limiter или неизвестном допустимом cap — real generation fail-closed, baseline продолжает работать. D3 memory fallback НЕ доказывает распределённый budget limit. Точные лимиты/хранилище/предагрегацию выбирает tech после company/finance review; multi-call aggregate plan потребует отдельного рассмотрения cap, а не обхода лимита по лидам.

Cost_per_verified_accepted_lead = подтверждённый incremental AI cost за явно указанный период / соответствующие уникальные evidence-backed accepted leads. При неизвестных cost или denominator результат null с причиной; при нулевом denominator метрика undefined, не «0 ₽ за лид». Неизвестное usage.total_tokens не приравнивается к нулю. Любой real overspend/утечка/access violation прекращает генерацию и требует incident/gate review.

## 7. Primary metric и дешёвый эксперимент

### 7.1 Не подменять primary metric

accepted_evidence_backed_leads_28d остаётся primary metric проекта. Existing dashboard accepted statuses — только исходный vocabulary для предлагаемого контракта, не готовая реализация метрики.

Предложение на утверждение company до любой instrumentation: за последние 28 дней считать первый реальный ручной transition в contacted/replied/meeting/won по уникальной (workspace_id, org_id), когда acceptance-time snapshot содержит source ref, проверенное непросроченное evidence, provenance и выполненный текущий deterministic gate/contact policy. Повторные кандидаты/профили/переходы не создают новый outcome одной компании в том же окне. Окно привязывается к timestamp действия, не только к created_at кандидата; replay должен воспроизводить evidence as-of acceptance. Если действующий канон использует другую единицу accepted lead — company явно разрешает конфликт ДО изменений, а не молча вводит эту формулу.

Запреты счётчика: test/synthetic/internal/bot accounts, mock feedback, auto-accepted, отсутствующий/просроченный evidence, summary view, AI call, draft copy. Missing наблюдение = null, не 0. Нужен независимый query/replay test повторов, 28-дневных границ, tenancy, expiry и first-accept timestamp. Canon metric definition не меняется решением product в этой карте.

### 7.2 P0: проверить агрегатный workflow по профилю, без строительства AI

Riskiest assumption = H1: главный bottleneck — ручная сборка межлидовой картины и плана, а не бедный source/fit. После exact-version review + разрешения company провести moderated paired workflow test за 7 календарных дней от зафиксированного start_at. Это qualitative discovery, не powered A/B/production trial. Owner сбора evidence — research/ux по назначению company; product — lead интерпретации; qa независимо проверяет grounding/планы. Никакого mass outreach, платной панели или использования персонального аккаунта владельца; только добровольно согласившиеся подходящие участники.

План: 5 реальных agency recruiters; каждому 2 контрольных и 2 других matched profile-level кейса, всего 20 планов (5 × 2 arms × 2 кейса). Единица кейса — ВЕСЬ заданный исследовательский профиль и пара его сопоставимых срезов, не один lead; N=5 людей, не 20 независимых пользователей. Прежний план на 60 per-lead решений отменён. Fixtures/consent/snapshot history пока отсутствуют; это предложенный план, не проведённое исследование.

Контроль = полная нынешняя очередь/карточки со всем тем же разрешённым набором facts/sources, существующим deterministic rank/brief и доступным history (без нового агрегата). Вариант = те же данные + один исследовательский/детерминированный агрегат профиля: coverage/as-of, delta, top-строки текущего priority, описательные группы/риски, существующие manual actions. Нет нового scoring/action engine или нового evidence; source доступен в обоих arms. Честная маркировка «исследовательская агрегатная сводка; не LLM». Сравнивается пакет представления общего плана, не отдельный эффект каждого F1-F4 и не польза AI.

Подготовка кейсов: реально проверенные публичные company-level facts с reproducible URLs и зафиксированными as-of; ни live DB dump, ни выдуманные leads/deltas/предыдущие срезы. Исследовательский профиль честно обозначен, не выдается за production-профиль участника. Все его lead records присутствуют; test profile не урезается ради top-N. В каждом кейсе — не менее 10 различных компаний, доказанная history и хотя бы один проверяемый cross-lead pattern/quality risk; это критерии fixture для проверки job, не наблюдаемая customer evidence. Заранее независимый QA validates complete inventory/previous-current и case key. Если нельзя достоверно построить history/control/набор — NEEDS-EVIDENCE, не synthetic success.

Кейсы matched по числу компаний/изменений/рисков, сложности, сегменту и качеству evidence. У одного участника профиль/компании не повторяются между arms; пары и sequence/seed frozen до первого observation, ABBA/BAAB counterbalance насколько позволяет N=5. Нельзя дать treatment свежее/богаче данные или заранее готовый коммерческий ответ, отсутствующий в контрольных исходных фактах. Рабочий профиль, timeline и контрольная сложность фиксируются, не выбираются по результату.

Задача: по всему профилю назвать главное изменение/unknown, выбрать до трёх первых ручных проверок и их evidence, отметить один подтверждённый cluster/risk и следующий безопасный шаг. Это study plan, НЕ реальные contacted/accepted outcomes; никаких записей feedback в продукт за участника. Не считать три top-строки тремя independent users или тремя принятыми лидами.

Measurement: псевдоним участника, case/arm/spec/snapshot/criteria version, coverage/unique-company counts, start/end, план/выбранные evidence refs, independent grounding verdict, can_explain_delta/next_step, missing/censored flags и manual prep time. QA по заранее frozen case key, blind к arm для итогового плана насколько возможно, оценивает корректность данных/unknowns/refs/допустимость действий, не единственный коммерчески «правильный» top. Useful plan = faithful delta/unknown + grounded приоритетные строки + корректный cluster/risk + допустимый next step; неподтверждённый материальный факт не компенсируется быстрым временем. Недостающие строки не выдумывать и не удалять.

Ключевая pilot метрика: r_i = median plan_seconds treatment / median plan_seconds control внутри участника; итог = median r_i по участникам. Время включает source/coverage/delta-проверку, не только чтение заголовка. Предлагаемый timeout одного полного profile-case = 480 s: запись censored at480 с отдельным timeout/failure status, не successful fast plan и не удалённое наблюдение. Ratio — описательный learning indicator, не survival estimate и не proof эффективности LLM; timeout/missing не допускают positive rule.

Pre-committed rule:
- ITERATE → только кандидат минимального bounded aggregate slice: 5/5 участников с четырьмя полными uncensored observations, median r_i ≤ 0.80, не менее 4/5 в обоих treatment-кейсах без помощи верно объясняют delta/unknown, evidence и next step; доля independently useful plans treatment не ниже control ни pooled, ни внутри каждого участника; safety violations=0. Это не automatic build/LLM GO;
- NO-GO для AI-строительства, если полные данные не проходят правило; если проблема оказалась source/fit, вернуть её владельцу D1/D2, не лечить генерацией;
- NEEDS-EVIDENCE, если нет 5 согласившихся подходящих участников, полного inventory/history/проверок, сопоставимого контроля или полного uncensored датасета 20 планов. Не продлевать и не менять пороги post-hoc; company выбирает отдельный новый тест либо остановку. Timeout может выявить usability-проблему, но не выдаётся за уверенную causal победу/проигрыш;
- немедленный STOP при раскрытии чужих/private данных, изменении core, неразрешённом обращении/spend или материальном unsupported fact. Отчёт включает инцидент, исключённый от показа output и rollback.

N=5 независимых людей, а не 20 независимых пользователей: тест discovery, без p-value/статистически доказанного uplift. Не выбирать после результата удобный сектор, не объявлять «GO потому что тренд». Даже успех P0 доказывает максимум полезность исследовательского агрегатного формата на prepared cases; не подтверждает production coverage/history, реальный daily-use, willingness-to-pay, каждый F2-F4 отдельно или преимущество LLM (H3). Один фиксированный analysis_at на start+7 дней; досрочное завершение только для safety STOP, не для красивого выигрыша.

### 7.3 Если P0 полезен

company может дать отдельный GO на минимальный profile-aggregate deterministic-first slice, не на per-lead summary. До него tech подтверждает полный inventory и возможность безопасных сопоставимых срезов на реальном контракте, ux — понятность coverage/delta/top/unknown. Затем H3: на том же full-profile grounding контракте сравнить AI vs deterministic aggregate, включая качество, fallback, фактическую стоимость всего агрегата и время. Без finance/capability/privacy evidence реальный LLM test остаётся NEEDS-EVIDENCE; mocks показывают только software contract.

Scale/production outcome проверяется отдельно: workspace-level assignment (не смешивать arms внутри агентства), baseline и power/MDE заранее с реальным числом рабочих пространств/variance, полный 28-дневный outcome window после последнего включения, accepted_evidence_backed_leads_28d и полезные решения на eligible workspace/time. Guardrails: no unsupported facts/leaks/core mutation, полезность accepted outcomes не хуже, budget cap соблюдён, fallback не блокирует работу. Сейчас baseline, variance, traffic и power = null; численный scale threshold и обещание uplift не назначены. Нет данных для powered experiment — нет scale GO.

## 8. Что переиспользовать из D3 и D1/D2/D4

D3 @6c6f615da8685148fad96903814d6c3dc633633f:
- openerDraftProvider.ts:26-38, 193-260 — resolved configuration, injectable transport, one request, timeout, availability/error pattern, trace/model/token metadata. Переиспользовать seam/test pattern; draftOpener(), prompt opener-draft-v1, 450-char limit и свободный plain-text output не контракт сводки. Нужны новая capability/prompt/output validation и grounding.
- opener-actions.ts:40-100 — permission/session + entitlement + owner/workspace/profile-scoped loading до provider. Это pattern, НЕ готовая загрузка всех лидов профиля/срезов: прежний one-lead input не переиспользуется как aggregate. Для read-only summary подобрать существующее read permission с tech/security review; не копировать leads:write просто по привычке. Любая cache/store выдача повторно проверяет profile scope и каждый contributing ref.
- openerDraftRateLimit.ts:89-134, 146-165 — atomic consume/logging pattern; глобальный org-only ключ и in-memory fallback не переносить в tenant budget contract (§6). Failed provider attempt тоже имеет cost/trace.
- openerDraftStore и live-db/migration tests — pattern attribution/defensive parse/round-trip лишь после отдельного техрешения; не применять migration ai_opener_draft, lifecycle edit/confirm/send не нужен.
- opener-draft-block.tsx и draft-focused UI/copy не переносить. Не cherry-pick весь PR261: его финальный QA/CI не равен acceptance новой функции, merge не разрешён.

D1: t_96e4e1b3 / parent t_6f920d4f. Baseline main registry = 27, independently recounted на PR242@49d8daae; карточка D1 сообщает expansion WIP, это не production coverage. Использовать source refs, normalization, provenance, freshness/verification и независимость source family, а не число зарегистрированных entries. Unverified/reachable/429/TLS-blocked sources не превращать в подтверждённые facts. Не добавлять источники ради AI; source integration остаётся у D1 owner.

D2: t_3ef42b89, https://github.com/maximalang/recruiter-radar/pull/260 @a3011cb7ff4ce7e833ebed760446cc69e4809694 — OPEN на момент readback, не merged. Registry/resolver и editable criteria могут стать input после integration review. До этого сводка использует уже сохранённые разрешённые profile fields; не утверждает существование shipped preset. User edits побеждают preset; AI не переписывает профиль/scan plan.

D4: t_04c5e801, https://github.com/maximalang/recruiter-radar/pull/262 @2b8fd4e61f113b5ca813971e012fc3c83f52aa84 — OPEN на момент readback. В main уже есть VK/Webhook UI: app/profile/notification-channels.tsx:110,141,234-249 + page.tsx:142; dispatch: notification-dispatch.ts:588,601; push sender webPush.ts:196+. Конкретные connect/SW/verification gaps устраняет D4. Наличие модуля не означает end-to-end/live PASS. Первая версия summary не добавляет dispatch/new payload; при будущей доставке переиспользовать consent, entitlements, retries/idempotency и independent proof, не менять D4 самостоятельно.

Scope drift: t_f8701369 до сих пор требует «все 4 PR merged», callable draftOpener и старый frozen landing head9eaa919b. Product оставил comment1833: before activation company должен согласовать новую audit/release границу с owner direction. Done status-handoff D3 нельзя засчитать как shipped AI. В task t_18026ee9 нет разрешения менять landing claim под этот SPEC.

## 9. Условная декомпозиция: до трёх tech-карт после GO

Ниже design briefs для оценки/маршрутизации, не активный feature backlog. Спавнить только выбранный минимальный slice после company decision с evidence P0; новые follow-ups назначать живым профилям. tech/ux — исполнительские владельцы, product не пишет фичи. Проверен roster hermes profile list: tech и ux на qwen3.8-max; qa и finance существуют и остаются независимыми. API/storage/provider details определяет tech, interaction/layout — ux/design; один вопрос не решают параллельно два автора.

### T1. Полный profile inventory, сопоставимые срезы и evidence-bound aggregate seam

Предполагаемые assignee=tech, task_type: code; parent = company GO + принятый privacy/cost contract, а не старая D3 done.
Scope: доказать полный scoped inventory всех лидов профиля, фиксированный cutoff и membership/criteria versions; deterministic aggregate с coverage, delta и supporting refs; тонкий validated presentation seam, fallback/выключатель. Не строить новую company summary и не использовать current page/top-N как input. LLM adapter — только при отдельном H3/finance разрешении; архитектуру snapshot/storage/pagination выбирает tech.
AC: QA fixtures на многостраничный профиль с изменением вне первой страницы, дубли компаний/фактов, archived/suppressed/expired, пустой профиль, unknown total/failed page/overflow, first snapshot, no change, late ingest, criteria/read-scope change, revoked/deleted refs/cache. Complete только с proven coverage; delta/count/group claim воспроизводим; отсутствие previous = unknown; failed/partial не становится новым успешным baseline. Score/gate/ranking/evidence/contact/suppression unchanged; нет новых contacts/URLs/tool calls/private text logs; missing provider/timeout/429/budget/shared limiter → safe baseline, не per-lead retries. Exact diff/SHA и reproducible test output.
Independent review: qa; economics/route: finance до real calls. Endpoint/migration shape и feature-flag implementation не предрешены.

### T2. Агрегатная выдача и scoped recruiter work assist (F2-F4)

Предполагаемые assignee=tech, task_type: code; parent=T1 pass + ux interaction acceptance + отдельный company GO на этот slice.
Scope: одна профильная выдача current/previous/coverage + изменения, до пяти строк текущих приоритетов, проверяемые cross-lead groups/risks и bounded manual plan/context topics. Не переделывать dashboard/lead UI целиком; отдельные AI-summary карточки/страницы лида не deliverable. Сначала ux определяет понятные состояния/attribution/источники, затем tech реализует; layout не предрешён product.
AC: отличие полного профиля от top-N/partial видно; first/no-comparable snapshot не «рост»; scope switching/revocation инвалидирует result. Supporting group refs и counts replayable, source navigation в existing карточки; current core order/suppression preserved, no duplicate company top-row/AI accept/send. Keyboard/accessibility, honest unknown/empty/unavailable и human action required. Нет новых channels/cadence/profiles/contacts/core drafts/landing diff; old per-lead summary test не acceptance этого агрегата.
Independent review: qa; hotspot координация с существующим dashboard-visual-refresh WIP, не править общий файл одновременно вслепую.

### T3. Evidence measurement и ограниченный pilot proof

Предполагаемые assignee=tech, task_type: code; parent=T1 accepted contract + company-approved primary definition/instrumentation; не ждёт полного T2, если тесту достаточно F1.
Scope: серверные минимальные scoped events/counters, replayable measurement, generation cost/fallback diagnostics, выключатель/rollback proof. Не использовать внешнюю аналитику в кабинете и не заносить study acceptance в реальные outcomes.
AC: dedupe/first acceptance/28d cutoff/evidence as-of/tenancy тесты; anonymous study exports с profile/snapshot/criteria/spec versions, coverage, assignment, plan_seconds, grounding, missing/censored/timeout flags (20 study plans != accepted leads). Total generation cost относится ко всему aggregate, не одной top-строке; feature kill-switch прекращает вызовы без потери core leads; measured provider vs mock evidence явно разделены; usage/cost неизвестное=null; reproducer+sanitized output. Repository checks на точном HEAD: repo-defined check/tsc, npm test в apps/web с реальными suite/test counts, build и CI. DB-тесты только isolated disposable с разрешённым ACK, migrations/replay/backup/rollback по repo gates. Green mocks не закрывают actual LLM или production proof.

Merge/deploy — только отдельный release lane: independent CI/review/QA/rollback, backup перед deploy; по APPROVALS.md и актуальным repository rules. Ни один T1-T3 здесь не имеет implicit spend/publishing/merge grant.

## 10. Review, stop rule и следующий owner

Product verdict сегодня: NEEDS-EVIDENCE, не фиктивный GO. Получен конкретный scope и план проверки; спрос/метрика/LLM usability/экономика неизвестны.

Следующий переход: независимый qa review SPEC2.0 на точном hash → company disposition на тот же artifact. QA проверяет latest owner direction: АГРЕГАТ ВСЕГО ПРОФИЛЯ (не per-lead text), полноту/срезы/deltas/top-N/groups/risks/actions, grounding источников/HEAD, primary metric без подмены, profile-level experiment/control/denominators, adversarial privacy/budget failures, условность T1-T3, границы D3 и stale audit t_f8701369. Это review нового SPEC, не дублирование старого functional-truth audit. Предыдущие QA anchors 1.0/1.1 отозваны comments1841/1842; verdict на них не переносится на2.0. Если QA успел закончить старую версию, company организует explicit re-review, не implicit PASS.

company после QA: одна проверяемая decision (GO только на P0 или NEEDS-EVIDENCE/NO-GO с reason), owner/check_at, disposition на открытые карточки фазы. Предлагаемый decision checkpoint 2026-10-02T18:00:00+03:00; это checkpoint, не обещание результата теста. При QA FAIL — конкретная коррекция/новая owner-карта, не обход review. Финансовый verdict product/qa не имитируют.

Если P0 назначен: один pilot task, start_at/analysis_at/assignment frozen, observation artifact, independent QA, рекомендация product по фактам, затем business verdict company. Две попытки без нового evidence/участников — уменьшить scope, сменить разрешённый тест или STOP, не бесконечно переносить next action. Если никакой capability/consent/бюджет не доступен, NEEDS-EVIDENCE с owner и wake condition; не строить пустого агента.

## 11. Воспроизведение evidence и честность отчёта

Read-only команды этой карты (в workspace, Windows native paths; exit 0):
- date -Is; git -C C:/Users/max/Desktop/all/recruiter-radar status --short --branch; git rev-parse HEAD / origin/main;
- gh api repos/maximalang/recruiter-radar/commits/main --jq .sha → a043fe8c20246b44becf2c80fb34695d0961ff36;
- gh pr view 261 --repo maximalang/recruiter-radar --json url,state,mergedAt,headRefOid → CLOSED / null / 6c6f615da8685148fad96903814d6c3dc633633f;
- gh pr list --repo maximalang/recruiter-radar --state all --limit 25 --json number,title,headRefName,headRefOid,state → #260/#262 OPEN, #261 CLOSED;
- gh pr view 242 --repo maximalang/recruiter-radar --json headRefOid → 49d8daae40b405f9a46a2de6ad574e8fa2a6406f (historical frozen9eaa919bb661ebfcbc998542e0316b13c0a893cd — другой anchor, не исправлялся мной);
- gh contents на apps/web/lib/sources/source-registry.ts?ref=49d8daae40b405f9a46a2de6ad574e8fa2a6406f, base64 decode, подсчёт реальных строк id в SOURCE_REGISTRY → registered_count=27, unique_count=27. Repro count command:

```bash
gh api 'repos/maximalang/recruiter-radar/contents/apps/web/lib/sources/source-registry.ts?ref=49d8daae40b405f9a46a2de6ad574e8fa2a6406f' --jq .content | python -c 'import sys,base64,re,json; t=base64.b64decode(sys.stdin.read()).decode("utf-8"); ids=re.findall(r"^    id: .([a-z0-9-]+).[, ]",t,re.M); print(json.dumps({"registered_count":len(ids),"unique_count":len(set(ids)),"source_ids":ids},ensure_ascii=False))'
```

Count доказывает registry, не live coverage. Старый remediation SPEC с 25 и отсутствием D3/D4 на другом anchor не использовать как текущую runtime truth. Нынешний PR242 всё ещё содержит draft-focused copy; эта карта НЕ меняла его и не даёт разрешения публиковать будущую AI-сводку как доступную.

Read-only source refs доступны также по https://github.com/maximalang/recruiter-radar/blob/a043fe8c20246b44becf2c80fb34695d0961ff36/ + указанный repo-relative путь + #L<line>; preserved D3 по https://github.com/maximalang/recruiter-radar/blob/6c6f615da8685148fad96903814d6c3dc633633f/ + путь из §8.

Основной RR checkout грязный на codex/dashboard-visual-refresh; ventures — грязный на fix/deny-remediation-routes. Чужие WIP, policies, runtime, STATE и refs не менялись. Deliverable — только этот SPEC по явно заданному пути; не общий коммит грязного checkout. Build/tsc/Jest/deploy/production HTTP/real LLM calls в этой research-карте не запускались. Родительские test counts принадлежат их runs, не являются моей новой верификацией. Suggested future isolated docs commit: docs(rr-ai): specify whole-profile aggregate and recruiter workflow experiment.

## 12. Correction history и handoff

- 1.0/1.1: предварительный ошибочный per-lead scope; SHA2561.1=c080455a98dcd4607f8f221e33001e1a9a1eac414732d9059633c1c1c049c3f8. Structural21/21 не доказал соответствие уточнённой директиве. Первичный completion родителя произошёл до обработки mid-run доставки уточнения; его summary/metadata — исторический, не действующий acceptance anchor.
- 2.0: correction по прямому уточнению владельца — один full-profile aggregate, cross-lead delta/priorities/patterns/risks/manual actions; переписаны раздел1, job/hypotheses, F1-F4, full-coverage/snapshot contract, P0 на20 profile-level планов и T1-T3. Per-lead facts сохраняются только внутри aggregate rows/refs. Drafts/helper не ядро и не включены в P0/AC.
- 2.0, residual self-check t_b898ec69 (02.10.2026): найден stale next-owner после company disposition t_bf239163; ниже обновлён только маршрут независимого re-review. Scope, F1-F4, контракт данных и P0/пороги не менялись; это handoff correction, не новая версия и не product GO. Начальный readback SHA256=17bfccb22acd222bd0c9b62dc6aaedf5525f5185d4f68462f312695590f4d775 заменяется итоговым exact hash в native handoff t_b898ec69.
- Next owner: qa, существующая карта t_a5071b8b (parent=t_b898ec69); затем company t_0a65e710 (parent=t_a5071b8b). Старые t_b64d86b6 / t_bf239163 завершены: PASS на 1.1 не принят для 2.0, business disposition — NEEDS-EVIDENCE. Эти карты не дублировать и не переносить их verdict на новый artifact. Итоговый exact hash и полный авторский self-check/readback публикуются в обеих действующих review/disposition threads; completion t_b898ec69 освобождает QA, не заменяет его независимый verdict или business decision company.
- Problem evidence: latest owner scope + reproducible code/PR refs выше; customer observation, primary baseline/change, real-profile coverage/history, LLM advantage/cost = unknown. Гипотеза/тест/метрика: H1, P0 profile-level workflow, accepted_evidence_backed_leads_28d без изменения канона. Риски: incomplete aggregation, ложная delta/кластеры, leakage исторического scope, cost scaling и неподтверждённая потребность. Статус остаётся NEEDS-EVIDENCE, spend0 RUB и реальные RR LLM calls0; никакой реализации/релиза не разрешено.
