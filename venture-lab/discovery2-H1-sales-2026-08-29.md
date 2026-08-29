# Discovery 2 — H1 GPT Estate Manager: линза «рынки сбыта и источники спроса» (sales)

Дата: 2026-08-29. Карточка: t_d17fba46. Владелец линзы: sales (GLM).
Метод: web-поиск + чтение страниц/выдачи; каждая цифра — с URL и датой среза. Поле для
полевой верификации (посты, DM, Wordstat) помечено явно; на cette дату НЕ проводилось.
Confidence: HIGH = измеримо/официально; MED = репутационная вторичка; LOW = оценка/план.
Задача карточки (из body): (a) 3+ источника спроса, (b) SERP на целевые квери,
(c) каналы ≥3 на сегмент, (d) GTM-гипотезы + первым шагом канала — полевой тест.

---

## 1. Кому продаём: сегменты и как устроены (без выдуманных цифр)

Контекст из research-файла: v1 = GPT Estate Manager (скан портфеля GPT → инвентарь →
экспорт MD/SKILL.md/JSON → отчёт рисков миграции). Сегменты S1–S3 заданы оркестратором.

**S1. Solo-создатели с портфелем 5+ GPT (Pro-подписка).**
- Где собираются (размеры — на 2026-08-29):
  - r/ChatGPTPro — ~606K members (thehiveindex.com/communities/r-chatgptpro, sync 2026-08-25);
    +118K за год, +24.2%/год (gummysearch via thehiveindex, дата среза на странице).
  - r/OpenAI — ~2.82–2.84M members (reddit.com/r/OpenAI/about, снято 2026-08-29).
  - r/ChatGPT — ~11.6M (thehiveindex.com/topics/gpt/platform/reddit, upd 2026-06-03) — слишком широкая, целевой только тематический пост.
  - Нишевые: r/GPTStore (~0.5K, reddit.com/r/GPTStore/about, 2026-08-29),
    r/gptsbuilders (точный размер не подтверждён — глючный ответ; NEXT), r/ChatGPTStore,
    r/GPT_creators (размеры не подтверждены, лежат в gummysearch/hive — NEXT).
  - Доля Pro-подписчиков и доля владельцев 5+ GPT — НЕИЗВЕСТНА публично. Оценки не даю.
- Покупческий сигнал: RedditGrow (redditgrow.ai/hidden-subreddits/ai-tools, 2026):
  r/ChatGPTPro = "Paid ChatGPT users — proven willingness to pay for AI tools" (позиция #4
  в их списке) — вторичка, но прямая формулировка сегмента.

**S2. Агентства/консультанты (AAA-модель), продавшие GPT-ассеты клиентам.**
- AI Automation Agency Hub (Skool, Liam Ottley): 329,183 members
  (skoolmakers.com/communities/ai-automation-agency, обзор 2026; на skool.com/learn-ai/about — 333.1K
  на момент снятия 2026-08-29). Это крупнейшее открытое сообщество AAA-агентств.
- Правило сообщества r/GPTStore: ссылки на third-party запрещены, шэрить GPT можно только
  официальными ссылками OpenAI (reddit.com/r/GPTStore — Rules, снято 2026-08-29) →
  в reddit-каналах наш тул позиционируем через гайд/кейс, не через линк-дроп.
- S2-модель в цифрах вторички: «сетап $5–20K + maintenance $1–5K/мес»
  (digitalapplied.com, из research-файла F12b; в отчёты клиенту не идти).
- Цена ошибки S2: их клиенты уже слышали «GPT sunsetting» (см. §5) — агентству нужен
  артефакт-отчёт, чтобы показать клиенту управление рисками. Это продаваемая ценность.

**S3. Админы Business/SMB-воркспейсов (GPT заперты в воркспейсе).**
- Факт запирания: публичный шаринг запрещён, только «Anyone in this workspace»
  (community.openai.com/t/1391451, авг 2026; из research-файла F4).
- В Team-воркспейсах per-member экспорт обычно выключен админом, экспорт идёт через
  Workspace Settings, в ZIP попадает `shared-gpts/` с конфигами воркспейс-GPT;
  personal GPT членов команды в воркспейс-экспорт НЕ входят (whychose.com/seo/chatgpt-team-export-difference, 2026).
- Enterprise-путь: Compliance API (/v1/compliance/exports), доступ только по
  workspace-scoped Admin key, выдается workspace owner'ом (help.openai.com/en/articles/9261474, upd. свежее).
- Вывод: у S3 экспорт-механика другая (workspace-флоу), не «клик-клик-скачать». Тул v1
  должен либо читать shared-gpts из их ZIP, либо не обещать S3 в лендинге.
- Смежный вход: whitepaper Altimetrik «Governing Custom GPTs» (altimetrik.com/storage/2026/02/…Governing-Custom-GPTs-Whitepaper.pdf)
  — в enterprise-дискурсе уже есть запрос на реестр/инвентарь GPT. Это поддержка тезиса
  «аудит как продукт», но не метрика спроса.

---

## 2. Sources of demand — 7 источников (кто уже ищет/обсуждает боль)

| # | Источник | Тип | Сила | Ссылка/срез |
|---|---|---|---|---|
| D1 | Skool AAA Hub 329–333K — агентства, у которых GPT-ассеты у клиентов | сообщество | MED | skool.com/learn-ai/about, 2026-08-29 |
| D2 | r/ChatGPTPro 606K — платящие Pro-юзеры, тул-хантинг | сообщество | MED | thehiveindex.com/communities/r-chatgptpro, sync 2026-08-25 |
| D3 | Комьюнити-практики «как забэкапить GPT» (JS-скрипты, «держи копии вручную») | UGC-боль | HIGH (старая боль) | research-файл F10; community.openai.com/t/990639, /t/605372 |
| D4 | Гайды «migrate GPT → Claude Skill» (skiln.co, claudeskillsforge, sheriseadkins, aiforcontentmarketing, automato.substack) | контент-спрос | HIGH | skiln.co/blog/migrate-chatgpt-gpts-to-claude-skills-2026; серп 2026-08-29 |
| D5 | SEO-конкуренты в SERP: gpt2skill.com, aimemory.pro, agensi.io — уже ранжируются под «export/convert GPT» | конкуренция = спрос | HIGH | серп 2026-08-29 (§3) |
| D6 | Пик миграционного маркетинга: Pickaxe $29–478/мес и FormWise продают «уходи с GPT» | конкурентный маркетинг | HIGH | research-файл F11d |
| D7 | CTO Securonix DIY-архивация через Compliance API; Altimetrik whitepaper про реестр GPT | B2B-боль | MED | ctovswild.com 2026-02-17; altimetrik.com 2026-02 |

Замечание: источники D4–D6 — про миграцию, не про аудит. Это важно: спрос ВИДЕН в миграционной
рамке; рамку «аудит/инвентарь» надо продавать ПОВЕРХ неё (все равно проверяют «что я потеряю»).

## 3. SERP-снимок на 2026-08-29 (что занято, какие окна)

**Кверя 1: «how to export custom GPT / backup GPT»** (серп по searches §батч1 + research F8–F10)
- Занято: aimemory.pro (гайд), community-треды, whychose.com (team-export, свежак 2026), CTO-кейс.
- Окно: нет инструмента «сделай инвентарь всего портфеля»; гайды отвечают «как вручную».
- Формат интента: how-to + tool. Страница-инструмент + отчёт рисков — отстройка от гайдов.

**Кверя 2: «migrate GPT to Claude skill / converter»**
- Занято: gpt2skill.com (позиция 1 в поиск. выдаче по данным поиска 2026-08-29), skiln.co
  (гайд+директория), claudeskillsforge.com, claudskills.com/skills/skill-migrate,
  aiforcontentmarketing.ai, sheriseadkins.com.au, automato.substack.
- Плотность: высокая. Формат интента: tool + how-to. Free-конвертер уже задал floor цены.
- Окно для нас: «конвертер не переносит capabilities» — подтверждено в самих конвертерах
  (thejoai.com: web search/code interpreter/DALL-E/actions не переносятся; skiln.co: то же + «no
  automated migration tool», «требует human judgment»). Это наш угол «отчёт что потеряешь».

**Кверя 3: «GPT creator community»**
- Занято: r/GPTStore (модерация жёсткая), r/gptsbuilders, r/ChatGPTStore, r/GPT_creators,
  OpenAI community forum (GPT builders category), OpenAI Discord, Skool AAA Hub.
- Активность реальная в OpenAI Dev Forum (community.openai.com/c/gpts-builders) — треды живые.
- Окно: ценность — не «где сидят» (известно), а «что им говорить». См. §5.

**Кверя 4: «OpenAI native GPT→Skill converter»**
- Сент. 2025: tibor blaho leak (F7 в research-файле). Дек. 2025: dataconomy повторяет.
- На 2026-08-29: help.openai.com/en/articles/20001066 «Skills in ChatGPT» — Skills GA
  (Business/Enterprise/Healthcare/Edu; Enterprise-дефолт с 23.07.2026). Конвертер GPT→Skill
  в офиц. доке НЕ упомянут. Слух всё ещё не шипнулся, но стал правдоподобнее
  (Skills уже в продукте; прошлый leak уже сбылся частично).
- Risk score: см. §5.

---

## 4. Каналы по сегментам (≥3 на сегмент) + GTM-гипотезы

**S1 (solo-создатели 5+ GPT):**
- C1: Reddit r/ChatGPTPro + r/OpenAI (606K / 2.8M). Формат: разбор «я экспортировал
  портфель из N GPT — вот что теряется» + тула. Не линк-дроп (правила, D3-форматы).
- C2: OpenAI Dev Forum (community.openai.com/c/gpts-builders) — живые треды по билдам,
  можно отвечать по теме экспорта/бэкапа.
- C3: SEO: «export GPT instructions», «GPT inventory tool», «what happens to my GPTs».
  Стартовая позиция слабая (домен новый), но окно свежее — whychose.com показал, что
  свежая дом-специфичная страница может ранжироваться (их team-export-страница в серпе 2026).
- C4: YouTube-комменты/коллабы с каналами туториалов (TheAIGRID 236K views на одном видео
  о создании GPT; WesGPT, Corbin AI и др. — gptshed.com/resource/wesgpt). GTM-канал, не core.

**S2 (AAA-агентства):**
- C5: Skool AAA Hub (329–333K, бесплатный вход) — пост/кейс «как я упаковал GPT-ассеты
  клиента перед миграцией» в формате value-first, не рекламы.
- C6: LinkedIn-аутрич (draft/assist) к AAA-агентствам — оффер «аудит GPT-портфеля клиента
  перед migration-дедлайном 30.11» — отстройка от Pickaxe/FormWise, которые продают
  re-platforming, а не аудит.
- C7: Партнёрка с migration-платформами (Pickaxe, FormWise) — наоборот, ИМ нужен входящий
  поток людей, уходящих с GPT; аудит-отчёт — их pre-sales артефакт. Гипотеза, не проверено.
- C8: YouTube-агентства (Corbin AI, Webcafe AI — gptshed.com/resource/wesgpt список).

**S3 (Business/SMB-админы):**
- C9: SEO/контент про «workspace export», «shared-gpts», «GPT governance» — whychose.com
  показал, что здесь есть пробел и окно ранжирования.
- C10: LinkedIn к IT-директорам SMB + комьюнити типа r/ChatGPTPro business-треды.
- C11: Партнёрка с compliance-аудиторами (гипотеза).
- ВНИМАНИЕ: C10/C11 — гипотезы, полевая проверка обязательна (см. §5), не тратить бюджет
  до проверки C9.

**GTM-гипотезы (проверяемые, не обещания):**
- H-S1: «Solo-создатель с 5+ GPT кликнет free-скан и оставит email, если увидит
  «what you lose»-отчёт» → метрика: конверсия лендинга ≥5% visitor→email на 200 визитов.
- H-S2: «AAA-агентство возьмёт аудит как pre-sales артефакт за $99–199/год, если покажеть
  кейс "клиент спросил что с его GPT"» → метрика: 3 из 10 cold-LinkedIn replies.
- H-S3: «Админ Business-воркспейса хочет инвентарь shared GPT» → метрика: 5 интервью или
  1 пилот. Слабая уверенность, приоритет низкий до S1/S2.

## 5. Риски и kill-факторы (обновлено против research-линзы)

- R1 (HIGH, усилел): нативный GPT→Skill конвертер OpenAI. Skills уже GA в ChatGPT
  (help.openai.com/en/articles/20001066, снято 2026-08-29; Enterprise-дефолт 23.07.2026);
  Codex имеет skills.md с дек. 2025 (simonwillison.net/2025/dec/12/openai-skills). Сам
  конвертер в офиц. доке не анонсирован — но теперь это вопрос «когда», не «если».
  Тул должен быть готов переупаковаться в «аудит/инвентарь» быстро (в «мы делаем
  inventory, а не конвертацию»), лендинг не строить вокруг слова «конвертер».
- R2 (HIGH): free-конвертер gpt2skill.com уже на #1 в серпе по миграционному интенту.
  Не конкурировать в этой квери вообще. Целься в «inventory/audit/what-you-lose»-кластер.
- R3 (MED): правила r/GPTStore запрещают third-party ссылки — промо в Reddit только
  через гайды/кейсы, иначе бан и репутационный минус.
- R4 (MED): в S3 (Team) пер-юзер экспорт выключен админом, personal GPT не попадают в
  workspace export (whychose.com) → тул v1 может не работать для S3 as-is. Не обещать
  S3 в лендинге до ручной проверки workspace-флоу.
- R5 (LOW): дом-руморы «GPT sunsetting» — фейк, но рынок их уже слышал (Pickaxe сам
  пишет «no actual official evidence»). В копирайте: строго факты (16.08 закрытие
  создания, 30.11 Agent Builder shutdown), без нагнетания. Иначе минус доверие в S2/S3.

## 6. Ответ на вопрос карточки: строим первый канал «сам» или с партнёром?

**Ответ: первый канал (2–4 недели) — строить самому, руками, без партнёров.**

Почему:
1. Бесплатные органические каналы (Reddit + OpenAI forum + Skool) дают сигнал без бюджета.
   Партнёрства (Pickaxe/FormWise) на этом этапе — отвлечение на переговоры при нулевой
   базе пользователей.
2. SEO-окно есть, но домен новый: ранжирование 3–12 мес (не обещаем), поэтому SEO —
   параллельно, не первый канал.
3. Партнёрская гипотеза (Pickaxe/FormWise) откладывается до момента, когда есть
   артефакт (отчёт «что потеряешь»), который можно показать партнёру — после первых
   50–100 реальных сканов.

Первый шаг (полевой тест, 2 недели, бюджет $0):
1. Кейсы в Reddit (r/ChatGPTPro, r/OpenAI) + OpenAI Dev Forum: формат «я экспортировал
   портфель из N GPT вручную — вот чеклист и что теряется» + free-тул. Цель: 5–10
   органических ответов + первые 30–50 сканов.
2. Skool AAA Hub: кейс-пост «упаковка GPT-ассетов клиента перед миграцией» + опрос в
   треде. Цель: 10+ ответов агентств (валидация H-S2 качественно).
3. Параллельно: лендинг с free-скан лид-магнитом и email-захват. Метрики воронки:
   visitor→scan ≥ 20%, scan→email ≥ 25% (это целевые значения, не прогноз).
   Claim: до полевого теста НЕ используем в материалах.

## 7. Ограничения этого отчёта (честно)

- Полевых интервью/постов — 0 на дату отчёта. Все «где сидит спрос» — вторичка.
- Wordstat/поисковые объёмы — не снимались (русскоязычный интент тут вторичен, ниша EN).
- Размер r/gptsbuilders, r/ChatGPTStore, r/GPT_creators — не подтверждён; sабреддиты
  маленькие, но живые (GPT Store-специфика).
- Доля владельцев 5+ GPT среди Pro-подписчиков — неизвестна. Целевая метрика S1
  (TAM в людях) не выводится из открытых данных. Проверяем behavior'ом (free-скан),
  не досчитыванием.
- Целевые конверсии в §6 — целевые значения для проверки, не прогноз и не обещание.

## 8. Рекомендация линзы sales

1. GO на полевой тест S1+S2 (2 недели, $0): Reddit + OpenAI forum кейсы, Skool AAA пост,
   лендинг с free-скан. KPI: 30–50 сканов + 10 ответов агентств.
2. S3 отложить до ручной проверки workspace-флоу (R4).
3. Позиционирование: НЕ «конвертер» (R1+R2), а «inventory + what-you-lose отчёт».
4. Партнёрства — после первых 50–100 сканов (см. §6).
5. Для finance-линзы: price-гипотезы research-файла ($29–49 solo, $99–199/год agency)
   можно тестировать как есть; готовность платить проверяется полем, не анализом.
