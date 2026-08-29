# Discovery 2 — H1 Custom GPT Escape & Compliance: линза «пользовательская проблема» (product)

Дата: 2026-08-29. Карточка: t_af24b763. Владелец линзы: product (GLM).
Метод: web-поиск поведенческих свидетельств (community-треды, DIY-скрипты, vendor-гайды) + чтение первоисточников; citation ledger grounded-citations (18 источников, `ledger.json`).
Confidence: HIGH = официальные доки OpenAI / дословные цитаты из прочитанных тредов; MED = репутационная вторичка / фрагменты тредов; LOW = одиночные сигналы.

TL;DR: боль реальна, давняя (с января 2024) и подтверждена поведением (DIY-скрипты, повторяющиеся треды, паника после 16.08). Но она разнородна: «не потерять актив» — самый массовый и острый job, «перенести» и «показать аудитору» — производные и пока не оплаченные. Платящая готовность платить (WTP) не доказана ни одним свидетельством — это главный разрыв для вердикта.

## 1. Кто и когда чувствует боль (JTBD, поведенческие свидетельства)

Три наблюдаемых типа поведения вместо выдуманных персон:

- [P1][HIGH] **Проактивный backup-инстинкт у «серьёзных» билдеров.** У автора backup-скрипта «создано приличное количество кастомных GPT» и был триггер — «ChatGPT недоступен, что подчёркивает важность не полагаться на платформу без бэкапа». Портфель, а не один GPT: автор спрашивает про bulk-экспорт именно конфигураций. Тред от 2024-07-08, ответы-подхваты в 2024-09 и 2025-06 («Any solution for this pls?») — спрос живёт без решения 2+ года.[3]
- [P2][HIGH] **Постфактум-потеря + ручной workaround.** Автор треда от 2024-01-11: «Я только что потерял всё, что было в поле инструкций, — заменилось на что-то гораздо более короткое и нерелевантное» и запрос «нам нужен способ вернуться к предыдущим инструкциям, а в идеале — история инструкций». Опытный билдер mojave: «Я пишу все инструкции офлайн в текстовом редакторе, потом копирую в Configure. У меня есть backup-копии» — т.е. рабочих процессов экспорта в платформе нет, люди строят их сами. 2.7k просмотров, 27 лайков.[2]
- [P3][HIGH] **Консьюмерский страх потери после 16.08.** Контент-гайд для новичков (бес дат, MED): «люди строят сложные конфигурации, загружают десятки knowledge-файлов, настраивают инструкции неделями — и ни разу не задумываются, что будет, если GPT исчезнет. Ваши кастомные GPTs могут и исчезнут». Вендор закрывает эту боль туториалом — значит, аудитория покупает/ищет такой контент.[7]
- [P4][MED] **Паника создателей после закрытия 16.08.** Тред от 2026-08-18: «Люди вложили существенное время в библиотеки GPT, научные ресурсы, учебные инструменты, воркфлоу, документацию, ссылки и комьюнити вокруг продуктовой модели, которую OpenAI активно поощряла» + запрос «ясного долгосрочного роадмапа и пути миграции/экспорта ДО удаления возможностей». Прямо сформулирован job «не потерять актив», но нет признаков платящего поведения.[8] Второй тред от 2026-08-16 (плюс-подписчик): возмущение закрытием, без экспортной боли.[9] Сигнал: боль страха ( anticipatory) доминирует в разговоре; поведенческая (backup) — в тредах 2024–2025.
- [P5][MED] **Enterprise-админ с растущим портфелем.** Гипотетический кейс governance-вендора: «10 000 сотрудников, шесть месяцев спустя — 800 Custom GPTs в воркспейсе. Как управлять тем, что не видишь?» — аудитории Enterprise это откликается (вендор на этом строит продукт, см. §4). Дата 2026-03-08.[12]

Когда болит (моменты): апдейт GPT перезаписал инструкции (P2); аккаунт/платформа недоступна (P1); закрытие создания → «что теперь с моими N GPT» (P4); аудит/передача клиенту у агентств — evidenced only indirectly (см. §5).

## 2. Официальная платформа: что экспортируется, а что нет

Проверка противоречия из сноски задачи (research-файл F8 vs страница whychose [11]):

- [E1][HIGH] Официальный help по экспорту данных описывает ZIP с «chat history и другими релевантными данными аккаунта»; про конфиги GPT — ни слова (help.openai.com/en/articles/7260999, обр. 2026-08-29). OpenAI НЕ документирует экспорт конфигураций GPT в общем экспорте.[14]
- [E2][HIGH] Официальный help по переносу между аккаунтами прямо перечисляет, чего перенос НЕ делает: «Не переносит кастомные инструкции, memories, **GPTs** или другие настройки аккаунта» (help.openai.com/en/articles/9106926, обр. 2026-08-29). Это самое сильное официальное подтверждение пробела — конфиги GPT не входят ни в экспорт, ни в перенос.[15]
- [E3][HIGH] Официальный help по созданию/редактированию GPT описывает version history и duplication, но НЕ экспорт конфигурации наружу (help.openai.com/en/articles/8554397, обр. 2026-08-29).[16]
- [E4][MED, противоречие] whychose.com (2026-05-30) описывает per-GPT экспорт «MyGPTs → GPT → Edit → ⋯ → Export» с системным промптом и action-схемами (без содержимого knowledge-файлов). Это НЕ подтверждено официальной документацией; противоречит официальным формулировкам E1–E3. Возможные объяснения: фича удалена после мая 2026, была неточной, или описывает A/B-поведение. **Статус: NEEDS-VERIFICATION** — это критический развилочный пункт: если нативный per-GPT export существует и работает, ценность продукта смещается с «экспорт» на «аудит/мульти-GPT/риски миграции».[11]
- [E5][HIGH] Enterprise: «There's no simple export workspace / archive all GPTs button in OpenAI Enterprise» — CTO Securonix строит DIY-архивацию через Compliance API (требующую support-активации ключа), ссылается на институциональные знания как на lock-in риск. 2026-02-17. Массовый нативный путь для S3 отсутствует.[13]

Вывод §2: research-факт F8 («экспорт не покрывает конфиги») подтверждается официальными доками E1–E2 на агрегатном уровне (все GPT сразу, перенос, Enterprise), но с одной незакрытой развилкой по per-GPT ручному экспорту (E4). Для v1-scope это означает: продавать «массовый аудит + отчёт рисков», не «единственный способ достать конфиг».

## 3. Какой job сильнее (по свидетельствам, не по интуиции)

- «**Не потерять актив**» — job с наибольшей частотой и интенсивностью: P1 (2024), P2 (2024, 2.7k views), P3 (undated), P4 (2026-08-18). Острейший триггер — недавно (16.08) ставший видимым риск + 30.11 дедлайн Agent Builder (research F5) как тикающие часы. Сегмент: S1 (соло-создатели с портфелем) и частично S3.
- «**Перенести в другую платформу**» — производный job, активность низкая: прямых тредов «как перенести мой GPT в Claude Skills» в выдаче не найдено; есть только инструмент (gpt2skill, research F11a) и migration-маркетинг Pickaxe/FormWise (research F11d). Перенос без решения «не потерять» малополезен — нельзя перенести то, что не сохранил. Сегмент: S1/S2, но пока молчит.
- «**Показать аудитору/клиенту инвентарь**» — job с наименьшим числом прямых свидетельств для S2: агентские handoff-чеклисты существуют (silvermine.ai — «exported assets where relevant, naming conventions», без дат/URL-цитат — LOW; picsart gen-ai-skills SKILL.md — handoff-манифест для gen-ai активов, не GPT — LOW), но ни одного найденного свидетельства «агентство продало GPT-ассеты и теперь не может их задокументировать/передать» — **нет**. Сегмент S2 — наименее evidenced. Слабое место: Customer Zero для интервью.[19][20]

Ранжирование job-ов: 1) «не потерять актив» (S1), 2) «перенести» (S1/S2, производный), 3) «показать аудитору» (S2, недоказан). Для S3 job другой: «инвентаризация + governance» (см. §4).

## 4. Сегменты: кто ближе к «платит за решение»

- **S1 solo-создатели 5+ GPT.** Боль evidenced (P1–P4), массовость — портфельная база создаётся годами: 3M+ кастомных GPT создано за ~2 месяца после запуска (OpenAI via seo.ai), в Store ~159k публичных; остальное — приватные портфели типа «shelf of GPTs» у предпринимателей (jonathanmast.com, 2026-08-18: «если вы как большинство предпринимателей, вы не один GPT построили, а полку»). Готовность платить НЕ evidenced — релевантный факт: revenue-share в Store платит медиана ~$47/мес (research F12b, LOW-MED) → аудитория S1 привыкла не платить. Риск: free-тул разрушает WTP.[17][10]
- **S2 агентства.** Прямых свидетельств боли не найдено (см. §3) — only adjacent: агентские AI-хэндофф-чеклисты (silvermine.ai, undated — LOW), picsart-скилл (LOW). Интервью — единственный путь проверки. Не строить на S2 до интервью.[19][20]
- **S3 админы Business/SMB.** Косвенное подтверждение бюджета: два вендора уже продают governance/inventory enterprise-клиентам через Compliance API — AgentsOrg (2026-03-08: «автоматизированный, непрерывный discovery каждого Custom GPT через Compliance API») и Securonix CTO (2026-02-17). Значит, в Enterprise/большом Business сегменте есть B2B-бюджет на «инвентаризация GPT-портфеля». Но: (а) это Enterprise-класс, не SMB-класс из оркестраторского S3; (б) Compliance API требует Enterprise-воркспейса — у SMB-админа его нет; (в) конкуренты уже там.[12][13]
- **S3 lock-in усилится:** Business-воркспейсы больше не могут публиковать GPT наружу (community.openai.com/t/1391451, 2026-08-18: «GPTs can no longer be shared publicly», только workspace-only). Ассеты ещё более запёрты — до Gemini-класса наружу их не вытащить. Усиление гипотезы «S3 audit» из research F4.[9]

## 5. v1-выводы для GPT Estate Manager (product lens)

Что MUST войти в v1, чтобы отличаться от gpt2skill (free converter, research F11a) и будущей нативной конвертации (research F7):
1. **Мульти-GPT скан → инвентарь** (не single-GPT конвертация): что построено, инструкции, knowledge-файлы, actions/ключи, sharing/версии. Ничего из этого gpt2skill не делает.
2. **Отчёт рисков миграции** («что ты потеряешь»): capabilities, действия, знание-файлы, права. Это job «не потерять актив» в формате, который понимает владелец портфеля (P4)[8][15][16].
3. **Портативные экспорт-форматы** (MD / SKILL.md / JSON) — must-have, но гигиенический, не платный слой: бесплатный конвертер задал floor цены на конвертацию.

Что НЕ должно войти (из продукта): хостинг ассетов, запуск GPT, «конвертация» как headline-фича, Governance-платформа уровня AgentsOrg (Enterprise compliance API) — иначе конкуренция не по адресу.

Ценообразование: гипотезы research ($29–49 solo one-time; $99–199/год agency; free-скан 1 GPT) согласуются с секцией 4 — main bet на S1 (one-time lower bound) и S3-SMB (годовой аудит), но НЕ валидированы ни одним свидетельством WTP. Сильнейший риск: нативная конвертация GPT→Skills от OpenAI (research F7) съест и «перенос», и частично «аудит» — mitigация: позиционирование в «estate/risk», не «convert».

## 6. План проблемных интервью (5–7 вопросов, не питч)

Кого звать (n=8–12): (a) авторы тредов backup/DIY-экспорта (P1, P2 — треды[3][2], публичные профили/DM); (b) недавние паникующие создатели из тредов 16.08+ (P4[8]); (c) S2 — агентства, продающие GPT-клиентам (искать: r/ChatGPTPro, X-треды «sold my client a custom GPT», indie-hacker-комьюнити); (d) S3-SMB админы Business-воркспейсов (community.openai.com, r/ChatGPTPro); (e) практикующие AI-консультанты (LinkedIn «AI agency GPT builder»). Где искать: community.openai.com, r/ChatGPT/r/ChatGPTPro, X-треды про 16.08, indie hackers Slack, дискуссии под gpt2skill-гайдами (thejoai.com).

1. Расскажите про ваш портфель: сколько GPT, какие, кто пользуется? (контекст, не питч)
2. Когда вы в последний раз думали о backup/экспорте ваших GPT — что случилось? (триггер: 16.08? потеря? апдейт?)
3. Что вы попробовали сделать? Покажите/опишите шаги. (проверка: дошли ли до ручного копирования как mojave P2[2])
4. Что из этого было самым болезненным/долгим? Почему? (позиционирование боли в процессе)
5. Что для вас значит «успешно решить» эту проблему — что изменилось бы в вашей работе? (desired outcome, not solution)
6. Если бы существовал инструмент, который сканирует все ваши GPT и показывает, что и где хранится + риски миграции, — что бы вы ожидали от него и чего боялись бы? (собирать возражения, не продавать)
7. Кто ещё в вашей команде/у клиентов отвечает за эти ассеты? (выйти на S2/S3 респондентов)

Стоп-правило для интервью: ≥3 из 8 респондентов S1 независимо описывают недавний (≤90 дней) инцидент потери/страха потери и предпринятые действия — гипотеза «не потерять актив» подтверждена как первичная; иначе — переранжировать job-ы.

## 7. Гэпы evidence и следующий шаг

- Не подтверждено: WTP в любом сегменте (ни одного платящего сигнала); существование/полнота per-GPT native export (E4 NEEDS-VERIFICATION — решается 10-минутной проверкой в реальном ChatGPT аккаунте); реальность боли S2 (0 найденных свидетельств); доля S1 с портфелем 5+.
- Слабое место: Customer Zero для интервью — S2. Не строить ценовую гипотезу на S2 до интервью.
- Рекомендация агрегатору: вердикт по H1 — **NEEDS-EVIDENCE** (не GO): JTBD и платформенный момент подтверждены, но (а) WTP=0 свидетельств, (б) per-GPT export развилка E4 меняет scope v1, (в) риск нативной конвертации OpenAI (F7) не разрешён. Дешёвый test: 8–12 проблемных интервью (§6) + 10-минутная ручная проверка E4 → потом GO/NO-GO на v1.

## Sources

[2] https://community.openai.com/t/updating-an-existing-custom-gpt-will-randomly-overwrite-your-instructions/582479 — OpenAI Community: Updating an existing custom GPT will randomly overwrite your instructions
[3] https://community.openai.com/t/any-way-to-export-your-custom-gpts-in-bulk/858737 — OpenAI Community: Any way to export your custom GPTs in bulk?
[7] https://dredyson.com/fix-this-gpt-is-inaccessible-or-not-found-a-beginners-step-by-step-guide-to-avoiding-the-5-critical-mistakes-everyone-makes-with-custom-gpt-errors-builder-profile-failures-and-complete-data — dredyson.com: Fix This GPT is Inaccessible - beginner guide to custom GPT data loss
[8] https://community.openai.com/t/removing-custom-gpt-creation-from-plus-and-pro-is-a-bad-decision/1390741 — OpenAI Community: Removing Custom GPT Creation from Plus and Pro Is a Bad Decision
[9] https://community.openai.com/t/unable-to-publicly-share-custom-gpts-from-a-chatgpt-business-workspace/1391451 — OpenAI Community: Unable to publicly share Custom GPTs from a ChatGPT Business workspace
[10] https://jonathanmast.com/what-happens-to-your-custom-gpts-now-that-openai-has-closed-new-gpt-creation-on-personal-accounts — jonathanmast.com: What Happens To Your Custom GPTs Now
[11] https://whychose.com/seo/chatgpt-custom-gpts-export — whychose.com: How to Export Your ChatGPT Custom GPTs (2026)
[12] https://agentsorg.ai/blog/enterprise-custom-gpt-governance-guide — AgentsOrg: The Enterprise Custom GPT Governance Guide
[13] https://ctovswild.com/2026/02/17/there-is-no-simple-export-workspace-archive-all-gpts-button-in-openai-enterprise — CTO vs Wild: no simple export/archive-all-GPTs button in OpenAI Enterprise
[14] https://help.openai.com/en/articles/7260999-how-do-i-export-my-chatgpt-history-and-data — OpenAI Help: Exporting your ChatGPT history and data
[15] https://help.openai.com/en/articles/9106926-transfer-exported-conversations-between-chatgpt-accounts — OpenAI Help: Transfer exported conversations between ChatGPT accounts
[16] https://help.openai.com/en/articles/8554397-creating-and-editing-gpts — OpenAI Help: Creating and editing GPTs
[17] https://seo.ai/blog/gpt-store-statistics-facts — seo.ai: GPT Store Statistics - 3M created, 159k public
[19] https://www.silvermine.ai/newsletter/ai-agency-asset-ownership-and-handoff-checklist-for-service-businesses — Silvermine: AI Agency Asset Ownership and Handoff Checklist
[20] https://github.com/PicsArt/gen-ai-skills/blob/HEAD/skills/agency-client-handoff/SKILL.md — GitHub PicsArt gen-ai-skills: agency-client-handoff SKILL.md
