# PATTERNS-SOURCES — сверка паттернов автороутера с официальными гайдами

Дата сверки: 2026-10-03
Источник пула: `profiles/company/scripts/model_router.py` (ROUTES + PATTERNS, head=0e41574d8e02f493e73313966b9b73572c046110)
Правило приёма: утверждение без официального URL не принимается; если официального гайда нет — честная пометка «источник: только флот-канон».

Пул моделей (из ROUTES/PATTERNS): kimi-k3, qwen3.8-max, glm-5.3, gpt-6.1-sol, gpt-6-astra, qwen-vl-max, gpt-6-luna.

---

## 1. kimi-k3 (Moonshot AI)

Официальный URL: https://platform.kimi.ai/docs/guide/prompt-best-practice (Kimi API Platform, «Best Practices for Prompts»; доступ 2026-10-03).

Что подтверждено официальным гайдом:
- «Write Clear Instructions» — модель не читает мысли; чем меньше догадок, тем точнее результат. Подтверждает строку PATTERNS «как брифовать: точное ТЗ, один deliverable».
- «Including More Details in Your Request Can Yield More Relevant Responses» — детали и контекст повышают релевантность. Подтверждает требование конкретики в брифе.
- «Requesting the Model to Assume a Role» — системная роль в messages. Согласуется с практикой точного ТЗ.
- «Using Delimiters… triple quotes/XML tags/section headings» — разделители для частей ввода. Не противоречит PATTERNS.

Расхождения с текущей строкой PATTERNS:
- «требовать строго: источники на каждый факт; числа только с URL; выдуманные данные запрещены» — в официальном гайде Kimi такого требования нет (это флот-канон против галлюцинаций, не вендорная рекомендация). Оставить, но пометить как флот-канон.
- «анти-паттерн: при конфликте удаляет данные (0/3, A/B 02.09)» — внутренний A/B, не вендорный источник. Оставить как флот-канон.
- «страховка: деструктивные файловые операции только после diff/backup» — флот-канон, не из гайда Kimi.

Предлагаемая правка: не требуется; добавить суффикс «(флот-канон)» к пунктам, не имеющим вендорного URL.

---

## 2. qwen3.8-max (Alibaba / DashScope)

Официальные URL:
- https://www.alibabacloud.com/help/en/model-studio/text-generation (Alibaba Cloud Model Studio, «Text generation»; доступ 2026-10-03).
- https://qwen.ai/blog?id=qwen3.8 (Qwen Team, «Qwen3.8-Max: A New Bar for Coding and Cowork», 2026-08-02; доступ 2026-10-03).

Что подтверждено официальным гайдом:
- «The system message is optional but recommended. Defining the model's role and behavioral constraints produces more consistent and predictable output» — подтверждает «как брифовать: жёсткий формат вывода (JSON/схема)» через явные behaviour constraints.
- Блог Qwen3.8-Max подчёркивает «end-to-end and dependable delivery of complex tasks», «self-evolves through feedback loops» — согласуется с использованием в классах data/code с readback/валидацией.

Расхождения с текущей строкой PATTERNS:
- «требовать строго: запрет уничтожения данных — при конфликте сохранить значение в восстановимой форме» — в официальных источниках Alibaba/Qwen такого правила нет (это флот-канон по A/B 02.09). Пометить как флот-канон.
- «анти-паттерн: факты без проверки цитированием (галлюцинации 40%)» — число 40% из внутреннего канона, не из официального источника. Пометить как флот-канон.

Предлагаемая правка: не требуется; суффикс «(флот-канон)» к невендорным пунктам.

---

## 3. glm-5.3 (Z.ai / Zhipu)

Официальные URL:
- https://docs.z.ai/guides/llm/glm-5.3 (Z.AI Developer Document, «GLM-5.3»; доступ 2026-10-03).
- https://docs.z.ai/guides/capabilities/thinking-mode (Z.AI, «Thinking Mode»; доступ 2026-10-03).
- https://z.ai/blog/glm-5.3 (Z.ai blog, «GLM-5.3: Frontier Coding with Emergent Cyber Capabilities», 2026-08-14; доступ 2026-10-03).

Что подтверждено официальным гайдом:
- «Offering multiple thinking modes for different scenarios»; «Thinking is activated by default in GLM-5.3 … GLM-5.3 uses forced thinking and cannot be disabled» — критично: у GLM-5.3 thinking принудительный, отключить нельзя. Это меняет паттерн брифа: не просить «не думать», а задавать effort (low/high/max — из блога).
- Блог: «GLM-5.3 supports three thinking effort levels: low, high, and max. Disabling thinking is no longer supported» — прямое подтверждение уровней effort.
- «Support for structured output formats like JSON, facilitating system integration» — подтверждает «вердикт структурирован по пунктам PASS/FAIL».
- «Interleaved thinking … supported since GLM-4.5, allowing GLM to think between tool calls» — согласуется с ревью-паттерном по пунктам.

Расхождения с текущей строкой PATTERNS:
- «страховка: на main/deploy — второй независимый вердикт (dual verdict 03.09)» — флот-канон, не из гайда Z.ai. Пометить как флот-канон.
- Отсутствует в PATTERNS: у GLM-5.3 thinking принудителен и имеет три уровня (low/high/max). Это вендорный факт, который стоит отразить в брифе.

Предлагаемая правка текста паттерна (добавить строку):
- «как брифовать: …; thinking у GLM-5.3 принудителен (off недоступен) — выбирать effort low/high/max под задачу (Z.ai, thinking-mode).»

---

## 4. gpt-6.1-sol (OpenAI)

Официальные URL:
- https://developers.openai.com/api/docs/guides/latest-model (OpenAI, «Using GPT-6»; доступ 2026-10-03).
- https://developers.openai.com/api/docs/guides/prompt-engineering (OpenAI, «Prompt engineering»; доступ 2026-10-03).
- https://openai.com/index/introducing-gpt-6-sol-and-luna/ (OpenAI, «Introducing GPT-6 Sol and Luna», обновлено 2026-09-29; доступ 2026-10-03).

Что подтверждено официальным гайдом:
- «Set reasoning.effort to low, medium (default), high, xhigh, or max … The none and minimal reasoning efforts are not supported» — прямое подтверждение, что глубина только через reasoning_effort; «none/minimal» недоступны. Подтверждает «без "think hard" — глубина только через reasoning_effort».
- «GPT-6.1 Sol … Balanced speed, cost, and intelligence. Near-Astra performance for complex work at a lower cost» — подтверждает позиционирование sol как strategic-дефолта.
- Prompt engineering guide: «GPT models like gpt-6-astra benefit from precise instructions that explicitly provide the logic and data required to complete the task in the prompt» — согласуется с «короткий ясный текст, только суть».

Расхождения с текущей строкой PATTERNS:
- «страховка: сверять поле model в usage — флагованный ответ тихо даунгрейдит модель» — флот-канон (наблюдение), не из официального гайда. Пометить как флот-канон.
- «анти-паттерн: длинные многоуровневые брифы; смена правил mid-turn» — флот-канон. OpenAI гайд упоминает «Mid-turn steering: Send additional user instructions while GPT-6 is working … preserves completed work» — то есть mid-turn steering поддерживается API, но как контролируемая фича, а не хаотичная смена правил. Не противоречие, но стоит уточнить.

Предлагаемая правка текста паттерна (уточнить анти-паттерн):
- «анти-паттерн: длинные многоуровневые брифы; хаотичная смена правил mid-turn (API поддерживает mid-turn steering через WebSocket — использовать контролируемо, не как смену ТЗ).»

---

## 5. gpt-6-astra (OpenAI)

Официальные URL:
- https://developers.openai.com/api/docs/guides/latest-model (OpenAI, «Using GPT-6»; доступ 2026-10-03).
- https://developers.openai.com/api/docs/guides/prompt-engineering (OpenAI, «Prompt engineering»; доступ 2026-10-03).

Что подтверждено официальным гайдом:
- «GPT-6 Astra … Highest intelligence. For the most demanding reasoning, coding, and professional work» — подтверждает использование astra как запасного/высшего ранга в классе strategic.
- «All GPT-6 Astra users also have access to Fast mode and the new Ultrafast mode for our fastest API speeds» — вендорная фича, в PATTERNS не отражена.
- Prompt engineering guide: precise instructions, explicit logic and data — согласуется с «только узкий пакет — один вопрос/одно решение».

Расхождения с текущей строкой PATTERNS:
- «страховка: нужно глубокое исследование — передать классу research (kimi-k3)» — флот-канон (роутинг-правило), не вендорный гайд. Пометить как флот-канон.
- Отсутствует в PATTERNS: Fast/Ultrafast режимы astra. Это вендорный факт, который может быть полезен для strategic-задач с жёстким SLA.

Предлагаемая правка текста паттерна (добавить строку):
- «как брифовать: …; при жёстком SLA рассмотреть Fast/Ultrafast режимы (OpenAI, latest-model).»

---

## 6. qwen-vl-max (Alibaba / DashScope, vision)

Официальный URL: https://www.alibabacloud.com/help/en/model-studio/vision (Alibaba Cloud Model Studio, «Image and video understanding»; доступ 2026-10-03).

Что подтверждено официальным гайдом:
- «Visual understanding models can answer questions based on the images or videos that you provide. They support single or multiple image inputs» — официально поддерживаются single и multiple image inputs. Это расходится с текущим анти-паттерном «коллажи и несколько изображений в одном запросе».
- Пример вызова использует `image_url` + `text` в одном user message — подтверждает формат ввода.
- Документация не упоминает `reasoning_effort` для qwen-vl-max — согласуется с инвариантом №3 «без reasoning_effort».

Расхождения с текущей строкой PATTERNS:
- «анти-паттерн: коллажи и несколько изображений в одном запросе» — официальный гайд прямо говорит «support single or multiple image inputs». Текущий анти-паттерн слишком строг. Возможно, он отражает внутренний опыт качества распознавания, но не вендорное ограничение.
- «страховка: критичное распознавание — перепроверка второй моделью (gpt-6-luna)» — флот-канон, не из гайда Alibaba. Пометить как флот-канон.

Предлагаемая правка текста паттерна:
- «анти-паттерн: коллажи и несколько изображений в одном запросе без явной необходимости (официально multi-image поддерживается; ограничение — флот-канон по качеству распознавания).»
- Или смягчить: «анти-паттерн: коллажи; несколько изображений — только если задача явно требует сравнения/серии.»

---

## 7. gpt-6-luna (OpenAI, vision)

Официальные URL:
- https://developers.openai.com/api/docs/guides/latest-model (OpenAI, «Using GPT-6»; доступ 2026-10-03).
- https://openai.com/index/introducing-gpt-6-sol-and-luna/ (OpenAI, «Introducing GPT-6 Sol and Luna», обновлено 2026-09-29; доступ 2026-10-03).

Что подтверждено официальным гайдом:
- «GPT-6 Luna … Fastest and most cost-effective. Strong performance for focused, high-volume tasks» — прямое подтверждение «массовые простые просмотры».
- «GPT-6 Sol and GPT-6 Luna do [support the none reasoning effort]» — важно: luna поддерживает `reasoning_effort: none` (в отличие от astra/sol). Это вендорный факт, который стоит отразить для массовых просмотров.

Расхождения с текущей строкой PATTERNS:
- «страховка: сложный/сомнительный кадр — эскалация на qwen-vl-max» — флот-канон (роутинг-правило), не вендорный гайд. Пометить как флот-канон.
- Отсутствует в PATTERNS: luna поддерживает `reasoning_effort: none` для максимальной скорости/минимальной цены. Это вендорный факт.

Предлагаемая правка текста паттерна (добавить строку):
- «как брифовать: …; для массовых просмотров использовать reasoning_effort: none (поддерживается luna, в отличие от astra/sol).»

---

## Сводная таблица

| Модель | Официальный URL | Ключевое подтверждение | Расхождение / правка |
|---|---|---|---|
| kimi-k3 | https://platform.kimi.ai/docs/guide/prompt-best-practice | Точное ТЗ, роль, разделители | Пункты про источники/данные — флот-канон |
| qwen3.8-max | https://www.alibabacloud.com/help/en/model-studio/text-generation | System message для consistent output | Запрет уничтожения данных — флот-канон |
| glm-5.3 | https://docs.z.ai/guides/llm/glm-5.3 + thinking-mode | Thinking принудителен; effort low/high/max; JSON output | Добавить про принудительный thinking и уровни effort |
| gpt-6.1-sol | https://developers.openai.com/api/docs/guides/latest-model | reasoning_effort low/medium/high/xhigh/max; none/minimal не поддерживаются | Уточнить mid-turn steering как контролируемую фичу |
| gpt-6-astra | https://developers.openai.com/api/docs/guides/latest-model | Highest intelligence; Fast/Ultrafast режимы | Добавить про Fast/Ultrafast при SLA |
| qwen-vl-max | https://www.alibabacloud.com/help/en/model-studio/vision | Single и multiple image inputs | Смягчить анти-паттерн про несколько изображений |
| gpt-6-luna | https://developers.openai.com/api/docs/guides/latest-model | Fastest, high-volume; поддерживает reasoning_effort: none | Добавить про effort: none |

## Общие выводы

1. Все 7 моделей пула имеют официальные вендорные гайды/документацию — kill-критерий не сработал.
2. Три модели требуют правок текста PATTERNS по вендорным фактам: glm-5.3 (принудительный thinking + уровни), gpt-6-astra (Fast/Ultrafast), gpt-6-luna (effort: none), qwen-vl-max (смягчить multi-image).
3. Часть пунктов PATTERNS — флот-канон (A/B, dual verdict, инварианты), а не вендорные рекомендации. Рекомендуется пометить их суффиксом «(флот-канон)» для прозрачности.
