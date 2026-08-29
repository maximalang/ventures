# Venture Lab — Discovery 1: венчурные гипотезы (2026-09)

Task: t_a136511b · Дата исследования: 2026-08-29 · Владелец: research · Ревью: product
Метод: web-research открытых источников (официальные документы платформ/EC, community-треды, отраслевая пресса). Все ссылки посещены 2026-08-29.
Confidence: **High** = первоисточник или страница, извлечённая полностью; **Medium** = несколько независимых вторичных источников; **Low** = единичный вторичный/маркетинговый источник. Пометка «(snippet)» = утверждение взято из поискового сниппета, страница целиком не извлекалась.

Критерии shortlist: (1) качество evidence, (2) наличие свободного wedge при заметной конкуренции, (3) совпадение с компетенциями студии (data-first продукты, программатик-дистрибуция), (4) срочность «why now».

## Реестр гипотез (7)

### H1. Custom GPT Escape & Compliance (CEC)
**Гипотеза.** Инструмент/сервис для создателей Custom GPTs: запечатанный экспорт-снапшот GPT (инструкции + knowledge-файлы + starters) как переносимый актив, crosswalk-документ «где функциональность живёт теперь» (Workspace Agents / альтернативные платформы) и compliance-квитанция для бизнес-клиентов агентств.

**Проблема.** OpenAI закрыла создание и публикацию новых Custom GPTs на личных аккаунтах (Free, Go, Plus, Pro); существующие GPTs остаются доступны и редактируемы, создание сохранено только в Business/Enterprise/Edu воркспейсах.[1] По данным прессы, ограничение действует с 16 августа 2026, GPT Store закрыт для новых сабмишенов от индивидуальных аккаунтов, и OpenAI не объявляла, будет ли функция возвращена.[4] Официальный преемник — Workspace Agents (запуск 22.04.2026, кредитная модель с 06.05.2026); migration tooling анонсирован, но пока не доступен, реконструкция — ручной труд.[5] Сообщество реагирует остро: фрилансеры и консультанты называют потерю инструмента критичной для своей работы,[2] преподаватели и исследователи сообщают о разрушении публичных образовательных ресурсов и массово оценивают альтернативы (Poe, Gemini Gems, Claude).[3] Одновременно платформа уже показала паттерн разрыва непрерывности: ретайр моделей GPT-4o/4.1/GPT-5 Instant/Thinking из ChatGPT с 13.02.2026 зафиксирован на той же официальной странице.[1]

**Аудитория.** Создатели публичных GPTs (~159K публичных из >3M созданных[7][8]), фрилансеры/коучи, упаковывавшие GPTs в клиентские продукты,[6] малые агентства, агентства/образовательные проекты из [2][3].

**Why now.** Ограничение live с 16.08.2026 — волна «что мне делать со своими GPTs» происходит прямо сейчас;[4] официального migration tooling нет,[5] значит первые месяцы рынок закрывается контентом и утилитами, а не вендором.

**Существующие траты (спрос подтверждён деньгами).** Платящие подписки Plus/Pro у создателей, потерявших функцию;[2] B2B-консалтинг на internal GPTs по $5–20K за внедрение плюс $1–5K/мес поддержки;[7] агентства продают GPT-слои внутри клиентских услуг и ищут, куда перенести актив.[6]

**Конкуренция и wedge.** FormWise, Pickaxe, Qolaba и др. продают «пересобери как агента на нашей платформе» — migration-rebuild.[6] Не занят соседний угол: (а) запечатанный архив-снапшот GPT как актив/страховка (аналог экспорта перед deprecation), (б) crosswalk + compliance-документ для агентств перед бизнес-клиентами. Продукт лёгкий (парсер конфигурации GPT → артефакт), дистрибуция — перехват search/LLM-запросов «how to export/migrate custom GPT».

**Риски.** OpenAI может откатить решение или выпустить официальный экспорт (обесценит ядро); существующие GPTs редактируемы — срочность архивации у части аудитории умеренная; объём «хочу унести» vs «злюсь, но остаюсь» не измерен. Реверс решения = NO-GO сценарий, поэтому Discovery 2 обязана включить лендинг-тест спроса и интервью.

**Evidence-оценка: High.** Официальная документация (полная страница),[1] широкая первичная community-боль,[2][3] измеримая база пользователей.[7][8]

### H2. Agent Cost Guard — бюджетные лимиты и kill-switch для AI-агентов (SMB/агентства)
**Гипотеза.** Не-dev инструмент: прокси/конфигурация бюджетных лимитов, velocity-алертов и kill-switch для агентов на no-code стеках (n8n/Make/Zapier) + еженедельный ROI-отчёт для клиента агентства.

**Проблема.** Практики сообщают о «тихих» детонациях расходов: агент ретраил неудачный вызов всю ночь и сжёг £220, «тратит ваши деньги, пока вы спите».[10] Треды r/AI_Agents о том, как измерять ROI агентов «прежде чем API-билл съест прибыль», — регулярная тема.[9][20][21] Критический провайдерский гэп: месячные бюджеты OpenAI по независимым отчётам — уведомление, а не отсечка (единственный проверенный hard stop — prepaid credits); параллельно агенты получили платёжные слои (x402, Visa/Mastercard agent tokens), не разделяющие общий бюджет; OWASP LLM06:2026 «Unbounded Consumption» закрепил uncapped spend как security-риск.[13]

**Аудитория.** Малые команды и агентства, запускающие агентов клиентам; SMB-операторы no-code автоматизаций.

**Why now.** Расходы на agent-софт по прогнозу Gartner удваиваются $86B (2025) → $206B (2026), и >40% agentic-проектов будет отменено к 2027 из-за расходов и неясного ROI — по пересказу вторичного источника.[10] Платёжная инфраструктура агентов только разворачивается.[13]

**Существующие траты.** API-биллы существуют по определению; дев-observability бюджетирован (Braintrust встраивает caps/kill-switch в платформу[12]), open-source governance-тулкиты доступны.

**Конкуренция и wedge.** Dev-observability (Braintrust и аналоги[12]) и open-source (MS Agent Governance Toolkit) целят инженерные команды. Мало занят слой «не-разработчик»: агентство на n8n/Make, которому нужен 10-минутный guardrail + белый-label ROI-отчёт клиенту.

**Риски.** Distribution в dev-инструменты дорог и конкурентен; вендоры могут встроить hard caps нативно и убить категорию; SMB-продуктовая форма размыта (конфиг? дашборд? сервис?). Сегмент-вариант «ROI-отчётность агентств» выделен отдельно как H7.

**Evidence-оценка: Medium.** Яркая повторяющаяся community-боль и верифицируемый провайдерский гэп,[9][10][13] но перегретый dev-tool ландшафт и неотличимый wedge снижают уверенность в позиции.

### H3. AI Act Article 50 Transparency Scanner
**Гипотеза.** Сканер «Art.50-готовности» сайта/продукта: чат-бот дисклеймер, маркировка AI-контента (C2PA), deepfake-лейблы → отчёт с гэпами и чек-листом исправлений. Лид-магнит для compliance-услуг/воркспейса.

**Проблема.** Обязательства прозрачности AI Act (ст. 50: раскрытие чат-ботов, машинно-читаемая маркировка AI-контента) применяются с 02.08.2026 — то есть уже действуют; для систем, вышедших на рынок до 02.08.2026, watermarking-подобов обязателен с 02.12.2026; Digital Omnibus в силе с 27.07.2026 перенёс high-risk (Annex III) на 02.12.2027.[14][15] Штрафные потолки до €15M или 3% оборота.[14][16]

**Аудитория.** SMB SaaS и агентства на рынке ЕС, публикующие AI-контент и чат-ботов; консультанты, обслуживающие ЕС-клиентов.

**Why now.** Обязательства уже enforceable — компании несоответственны сегодня; под-дедлайн watermarking 02.12.2026 — принуждающее событие через ~3 месяца.[14]

**Существующие траты.** Категория монетизируется: ActReady продаёт классификатор+документы от €29/мес;[17] Complair строит compliance-воркспейс для SMB.[16] Прямых community-жалоб SMB на Art.50 не собрано — спрос выводится из монетизации конкурентов (gap, см. Пробелы).

**Конкуренция и wedge.** Конкуренты продают «воркспейс документов».[16][17] Свободный программатик-wedge: автоматический аудит живого сайта (краулер → отчёт), data-first, совпадает с SEO/AEO-компетенцией студии; перехват запросов «AI Act checklist for website/chatbot».

**Риски.** Enforcement в странах-членах может быть медленным → платёжеспособный спрос может материализоваться только к волне Dec 2027; правки Omnibus продолжаются; юридическая чувствительность формулировок («не юрконсультация»).

**Evidence-оценка: Medium-High на регуляторные факты** (официальная страница EC[15]), **Medium на готовность SMB платить** (косвенная).

### H4. AI-приём звонков / missed-call recovery для SMB
**Факт спроса:** платформы живут с подписок $29–300/мес, категория коммерчески доказана.[18][19] **Против входа:** 7+ устоявшихся платформ, включая вертикальные и гибридные (AI+люди);[19] ключевые «статы потерь» ($126K/год, 85% voicemail) — vendor-маркетинг без первоисточника;[18] барьеры входа — voice-инфраструктура, телеком-интеграции, языки. **Вердикт:** спрос реален, но без уникального угла для студии — кандидат на NO-GO; в shortlist не входит.

### H5. RU-поисковые утилиты (конвертер ЦБ, калькулятор госпошлин, проверка КБМ)
Зарегистрированный внутренний shortlist (content-seo-strategy, references/niche-shortlist-2026-08.md): официальные источники проверены (cbr.ru XML_daily отвечает; ст. 333.21 НК РФ; autoins.ru HTTP 200). Заблокировано: снимок спроса Wordstat требует OAuth-токена (залогиненный UI); монетизация RPM-медленная (6–12 мес индексации нового домена). По правилам скилла расходы до выбора ниши пользователем запрещены. **Статус: отложена; в короткий лист не входит из-за слабого внешнего evidence и long-time-to-money.**

### H6. Аудит AI-подписок для SMB («subscription leak»)
Тренд зафиксирован: в r/AiForSmallBusiness и r/Entrepreneur обсуждают дублирующиеся AI-подписки и «утечку» бюджетов;[11] использование AI бизнесами 17–20% (Census Bureau, по пересказу[11]). Продуктовая форма слабая (аудит-сервис/контент, не тиражируемый продукт). **Совместимость: контент-воронка для H2, самостоятельная ценность низкая.**

### H7. Agent-ROI отчётность для агентств
Сегмент-вариант H2: агентства, продающие построение агентов, не могут доказать клиентам возврат — «нет ни одного кейса с определённым возвратом».[20][9] Отдельная карточка реестра для полноты; ранжируется внутри H2 (тот же evidence-база, тот же покупатель). **В shortlist отдельно не входит.**

## Shortlist (≤3, по качеству evidence)

| # | Гипотеза | Evidence | Wedge | Why now | Итог |
|---|---|---|---|---|---|
| 1 | H1 CEC — экспорт/compliance-снапшоты Custom GPTs | High: официальный доки[1] + массовая community-боль[2][3] + база 3M/159K[7][8] + платящие подписки и $5–20K B2B-контракты[2][7] | Архив+crosswalk угол не занят (конкуренты только rebuild[6]) | Ограничение live с 16.08.2026, официального tooling нет[4][5] | **#1 — на Discovery 2** |
| 2 | H2 Agent Cost Guard (вкл. H7) | Medium: боль повторяется[9][10][20][21], провайдерский гэп верифицируем[13], рост рынка[10] | Не-dev слой агентств свободен; dev-слой переполнен[12] | Рост расходов + платёжные слои агентов разворачиваются[13] | #2 — параллельный трек, готов как fallback |
| 3 | H3 Art.50 Transparency Scanner | Medium-High регуляторика (EC[15]); Medium WTP (косвенно[16][17]) | Сканер-лидмагнит против воркспейсов конкурентов | Обязательства действуют, watermarking-дедлайн 02.12.2026[14] | #3 — сезонное окно, сильная дистрибуция |

Отклонены от shortlist: H4 (рынок доказан, но перенасыщен и без wedge — см. карточку), H5 (блокер Wordstat, слабый внешний evidence), H6 (нет продуктовой формы), H7 (внутри H2).

## Рекомендация
Несовпадение с фильтром Discovery 2: **H1** — рынок и источники (research), пользовательская проблема через интервью (product), pre-mortem (critic), экономика (finance), канал (sales/marketing) → GO / NO-GO / NEEDS-EVIDENCE. Критическая проверка для pre-mortem: вероятность отката решения OpenAI и появления официального экспорта.

## Пробелы и ограничения
- Дата 16.08.2026 подтверждена одним вторичным источником[4]; официальная страница[1] дату не называет. Оценка: Medium.
- Цифры 3M созданных/159K публичных GPTs — вторичные (гайд 01.2026[7]; анализ 04.2024[8]); первичного подтверждения OpenAI нет.
- Gartner-цифры ($86B→$206B, >40% отмен к 2027) процитированы по пересказу блога,[10] не по первичному отчёту.
- Reddit-треды недоступны напрямую из сети (блокировка) — цитируются через вторичные обзоры [10][11]; формулировки pain сохранены как в источниках.
- $126K/85% статы H4 — vendor-маркетинг,[18] исключены из обоснований.
- Прямой спрос на H3 (жалобы/поисковые объёмы SMB) не измерен — только монетизация конкурентов.

## Sources

[1] https://help.openai.com/en/articles/8554397-creating-and-editing-gpts — OpenAI Help Center — Creating and editing GPTs (personal accounts cannot create/publish new GPTs)
[2] https://community.openai.com/t/removing-custom-gpt-creation-from-plus-and-pro-is-a-bad-decision/1390741 — OpenAI Community — Removing Custom GPT creation from Plus/Pro is a bad decision
[3] https://community.openai.com/t/removing-public-custom-gpt-creation-breaks-real-educational-and-research-infrastructure/1391052 — OpenAI Community — Removing public Custom GPT creation breaks educational/research infrastructure
[4] https://sqmagazine.co.uk/openai-blocks-personal-accounts-new-gpts — SQ Magazine — OpenAI Blocks Personal Accounts From Building New GPTs (Aug 16, 2026)
[5] https://scottarmbruster.com/articles/custom-gpts-dead-workspace-agents-replace-them — Scott Armbruster — Custom GPTs Are Dead. Workspace Agents replace them (Apr 22, 2026; credit pricing May 6)
[6] https://formwise.ai/blog/openai-deprecating-custom-gpts-migration-path — FormWise — OpenAI is deprecating Custom GPTs: migration path (agency/coach resale story)
[7] https://www.digitalapplied.com/blog/gpt-store-custom-gpts-business-guide-2026 — Digital Applied — GPT Store Business Guide 2026: 3M+ GPTs created, ~159K public, payouts $100-500/mo ceiling
[8] https://seo.ai/blog/gpt-store-statistics-facts — seo.ai — GPT Store statistics: 3M created, 159K public
[9] https://www.reddit.com/r/AI_Agents/comments/1r5kqdo/how_are_you_guys_actually_measuring_roi_on — r/AI_Agents — How are you measuring ROI on autonomous agents before the API bill eats the profit
[10] https://ivconsulting.in/blogs/what-reddit-really-thinks-ai-agent-spending-boom — IV Consulting — 5 Reddit threads on AI agent spending: silent retry burn £220 overnight, Gartner 40% cancellations by 2027
[11] https://theusefuldaily.com/article/small-businesses-are-starting-to-treat-ai-like-a-subscription-leak — The Useful Daily — Small businesses treat AI like a subscription leak (Aug 22, 2026)
[12] https://www.braintrust.dev/articles/how-to-track-llm-costs-2026 — Braintrust — How to track LLM costs 2026: caps, kill switches (cost observability = dev tool)
[13] https://changegamer.ai/resources/agent-spend-controls — ChangeGamer — Agent Spend Controls guide (updated 2026-08-15): OpenAI budget is notification-not-cutoff
[14] https://wpseoai.com/blog/ai-act-digital-omnibus-explained-what-actually-changed — WPSEO AI — AI Act Digital Omnibus: in force July 27, 2026; Art.50 transparency live Aug 2, 2026; Annex III moved to Dec 2027; Dec 2, 2026 watermarking deadline
[15] https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai — European Commission — AI Act regulatory framework (official timeline)
[16] https://complair.eu/blog/eu-ai-act-deadline-august-2026 — Complair — EU AI Act deadline Aug 2, 2026: SMB SaaS 90-day checklist (compliance workspace positioning)
[17] https://getactready.com/eu-ai-act-compliance-tool — ActReady — EU AI Act compliance tool: free classifier, €29/mo plans (existing competitor)
[18] https://callacy.com/blog/best-ai-receptionist-small-business-in-2026 — Callacy — 8 best AI receptionists 2026: SMBs lose ~$126,000/yr to missed calls; 85% voicemail skip rate
[19] https://ainora.lt/blog/best-ai-for-missed-calls-small-business-2026 — Ainora — Best AI for missed calls 2026: 7+ platforms ranked (crowded market)
[20] https://www.reddit.com/r/AI_Agents/comments/1qs9trz/the_reality_of_ai_roi_is_settling_in — r/AI_Agents — The reality of AI ROI is settling in
[21] https://www.reddit.com/r/artificial/comments/1svqm2m/are_ai_agents_actually_giving_people_roi_yet_or — r/artificial — Are AI agents actually giving people ROI yet
