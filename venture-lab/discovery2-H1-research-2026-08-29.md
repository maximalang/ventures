# Discovery 2 — H1 Custom GPT Escape & Compliance: линза «рынок и источники» (research)

Дата: 2026-08-29. Карточка: t_f3573ec1. Владелец линзы: research (GLM).
Метод: web-поиск + чтение первоисточников; citation ledger grounded-citations (18 источников, см. `ledger.json`).
Confidence: HIGH = официальные доки/анонсы OpenAI; MED = репутационная вторичка; LOW = одиночные сигналы/слухи.

## 1. Статус платформы (перепроверено на дату работы)

- [F1][HIGH] По офиц. докам OpenAI (help.openai.com/en/articles/8554397 «Creating and editing GPTs», обр. 2026-08-29): с 16.08.2026 создание и публикация новых GPT недоступны на личных аккаунтах (Free, Go, Plus, Pro). Существующие GPT продолжают работать и редактируемы при соблюдении плана/прав. Создание — только Business/Enterprise/Edu-воркспейсы, по админ-настройкам.
- [F2][MED] GPT Store закрыт для новых сабмитов с личных аккаунтов; публикация в Store — только через админа воркспейса (sqmagazine.co.uk 2026-08-17, по тексту офиц. доки; сама докя подтверждает запрет создания/публикации на personal).
- [F3][HIGH] 22.04.2026 OpenAI представила Workspace Agents — «эволюция GPTs» (openai.com/index/introducing-workspace-agents-in-chatgpt). В анонсе прямо: «Soon, we'll make it easy to convert GPTs into workspace agents». GA для Business/Enterprise/Edu; кредитный прайсинг с 06.05.2026 (venturebeat.com — deprecating custom GPT standard для организаций, дата не названа).
- [F4][MED] Business-воркспейсы: публичный шаринг GPT запрещён — только «Anyone in this workspace» (community.openai.com/t/1391451, авг 2026). Созданные в Business GPT отрезаны от внешней аудитории.
- [F5][HIGH] 03.06.2026 OpenAI депрекейтила Agent Builder + Evals + reusable prompts; shutdown 30.11.2026 (developers.openai.com/api/docs/deprecations; openai.com/index/introducing-agentkit). Офиц..Community-совет: «экспортируй, пока дашборд жив» — публичный прецедент «export until it's gone».
- [F6][HIGH] 06.08.2026 Agent Plugins 1.0 — открытый vendor-neutral стандарт упаковки Agent Skills (SKILL.md) + MCP от OpenAI, Microsoft, AWS, GitHub, Cursor(Anysphere), Vercel; Google — мейнтейнер; 6 клиентов поддержали на старте (thenextweb.com; agenticskills.io).
- [F7][LOW-MED] 17.08.2026 Tibor Blaho (lead engineer AIPRM, надёжный leak-репортёр): OpenAI «появляется работа над конвертацией существующих GPTs в Skills» (x.com/btibor91/status/2089390083166404701; вторично sqmagazine.co.uk 2026-08-17). Официально не подтверждено. ГЛАВНЫЙ kill-фактор для конвертационного wedge, если шипнётся.

## 2. Экспорт-пробел (ядро боли)

- [F8][HIGH] Официальный экспорт ChatGPT (Settings → Data controls → Export) покрывает conversations-данные, НЕ конфиги GPT (help.openai.com/en/articles/7260999; подтверждают сторонние гиды).
- [F9][HIGH] Enterprise: «There's no simple export workspace / archive all GPTs button in OpenAI Enterprise» — CTO Securonix построил DIY-архивацию через Compliance API, требующую support-активации ключа (ctovswild.com, 2026-02-17). Конфиги GPT считаются institutional knowledge / vendor lock-in риском.
- [F10][MED] Комьюнити-практики: JS-console скрипты для копирования настроек (reddit r/ChatGPT 1ccihj7, 2024), советы «держи копии файлов и промптов вручную» (community.openai.com/t/990639, 2024; /t/605372, 2024). Спрос на обходной путь существует годами, нативного решения нет.

## 3. Конкуренция (на 2026-08-29)

- [F11a][HIGH] gpt2skill.com — БЕСПЛАТНЫЙ copy-paste конвертер GPT→Claude Skill (Name/Description/Instructions/Starters + knowledge files → ZIP со SKILL.md). Уже индексируется, есть гайды (thejoai.com). Limitation: capabilities (web search, code interpreter, actions) не переносятся.
- [F11b][MED] Agensi — converter-скилл «Custom GPT → SKILL.md» для маркетплейсов (agensi.io). MD2SKILL и подобные — open-source подходы.
- [F11c][HIGH] aimemory.pro — контент-гайд «How to export ChatGPT custom GPTs» (2026) — контентный угол занят.
- [F11d][HIGH] Pickaxe и FormWise — migration-маркетинг «уходи с GPT к нам»: Pickaxe $29–478/мес (pickaxe.co/post/openai-custom-gpts-august-2026-shutdown-migrate-to-pickaxe; /pricing), FormWise (formwise.ai/blog/openai-deprecating-custom-gpts-migration-path, 2026-05-12). Оба продают white-label платформы, не аудит/экспорт.

## 4. Деньги в экосистеме

- [F12a][MED] Масштаб: ~3–5M GPTs Q2 2026, большинство не монетизированы; revenue-share — ограниченный rollout (presenc.ai/research/ai-tool-marketplace-economics-2026).
- [F12b][LOW-MED, secondary] Store-выплаты ~$0.03/диалог при пороге 25 диалогов/нед; медиана $47/мес; у большинства потолок $100–500/мес; топ-1% забирает ~78% выплат (uandai.ai; digitalapplied.com). Реальные деньги — B2B: агентства/консультанты, сетап $5–20K + maintenance $1–5K/мес (digitalapplied.com). Все цифры — вторичные, для планирования, не для отчётов клиентам.

## 5. Слухи vs факты

- [F13][проверено] Слух «OpenAI sunsetting Custom GPTs в августе 2026» — НЕ подтверждён: Pickaxe сам пишет «no actual official evidence» (ссылка на r/OpenAI тред). Август прошёл — закрылось только СОЗДАНИЕ (F1). Как факт не использовать; как рыночный сигнал (страх миграции уже в продажах агентств) — можно с пометкой.

## 6. Вывод линзы research

1. Момент подтверждён и УСИЛИЛСЯ относительно Discovery 1: 16.08.2026 закрытие создания (F1), 30.11.2026 публичный дедлайн Agent Builder (F5), открытый стандарт Skills (F6). «Why now» — доказуемо первоисточниками.
2. Wedge «просто конвертация GPT→SKILL.md» обесценен: существует бесплатный gpt2skill (F11a) и вероятна нативная конвертация от OpenAI (F7).
3. Устойчивый угол v1 — «GPT Estate Manager»: аудит/инвентарь портфеля GPT (что построено, где знания, какие actions/ключи), экспорт в переносимые форматы (MD/SKILL.md/JSON), отчёт «что потеряешь при миграции» (capabilities не переносятся — F11a), для владельцев 5+ GPT и агентств. Бесплатный тул = floor цены на конвертацию; платить могут за автоматизацию, аудит и multi-GPT масштаб.
4. Не подтверждено (гэпы): размер платящего сегмента; готовность платить за аудит; вероятность/сроки нативной GPT→Skills (F7); число GPT именно на personal-аккаунтах (нет публичных данных). Нет данных об оттоке/даунгрейдах создателей после 16.08.

## 7. Решения оркестратора (фиксируются в дочерних карточках)

- Рабочее название v1: **GPT Estate Manager** (не финальный бренд).
- v1 scope: скан портфеля GPT → инвентарь (инструкции, знания, actions, версии) → экспорт (Markdown + SKILL.md + JSON) → отчёт рисков миграции. Без хостинга ассетов, без запуска GPT.
- Сегменты: S1 solo-создатели с портфелем 5+ GPT (Pro); S2 агентства/консультанты, продавшие GPT-ассеты клиентам; S3 админы Business/SMB-воркспейсов (для них актуален F4 — их GPT заперты внутри воркспейса).
- Прайс-гипотезы для проверки finance: $29–49 one-time solo; $99–199/год agency; free-скан 1 GPT как лид-магнит.

## Пробелы и следующий шаг

- Гэпы: платящий размер сегментов S1–S3; готовность платить; тайминг F7.
- Следующий шаг: fan-out 4 линз (product/critic/finance/sales) карточками на доске venture-lab; агрегация и вердикт GO/NO-GO/NEEDS-EVIDENCE — отдельной карточкой research после их завершения.
