# PATTERNS-SOURCES-v2 — свод официальных паттернов коммуникации для моделей флота

Дата сборки: 2026-10-04
Источник пула: `profiles/company/scripts/model_router.py` (ROUTES + PATTERNS, head=0e41574d8e02f493e73313966b9b73572c046110)
Правило приёма: только официальные источники (вендорская документация, engineering-блог, cookbook); утверждение без URL не принимается. Пометка «источник: только флот-канон» используется, когда вендорного источника нет.
Версия: v2 (расширение v1: новая модель deepseek-v4-flash, меж-агентный слой, 5-слойная структура с каноническими настройками)

---

## Методология

Для каждой модели флота собрано 5 слоёв паттернов:

1. **Как брифовать** — структура промпта, роль, формат входа/выхода.
2. **Что требовать строго** — обязательные ограничения, валидация, запреты.
3. **Страховка-валидация** — как проверить результат перед применением.
4. **Анти-паттерны** — что не делать (по вендорному гайду или флот-канону).
5. **Канонические настройки** — официально подтверждённые параметры API (temperature, reasoning_effort, tool-форматы, контекст).

Пул моделей: kimi-k3, qwen3.8-max, glm-5.3, gpt-6.1-sol, gpt-6-astra, qwen-vl-max, gpt-6-luna, deepseek-v4-flash.

---

## 1. kimi-k3 (Moonshot AI)

### Канонические настройки
- `model`: `kimi-k3`
- `reasoning_effort`: `"low"` / `"high"` / `"max"` (default `"max"`) — top-level поле, не внутри `thinking`
- `thinking`: не передавать для k3 (reserved for k2.x); reasoning всегда включён, Preserved Thinking всегда включён
- `response_format`: `{"type": "json_object"}` для JSON Mode
- `temperature`: не документирован в официальном гайде; использовать default
- Контекст: 1M токенов; context caching доступен (cache-hit ~10% от cache-miss price)

### Как брифовать
- Точное ТЗ, один deliverable, без параллельных веток. Официально: «Write Clear Instructions — The model can't read your mind. The less the model has to guess about your needs, the more likely you are to get satisfactory results.»
- Использовать system prompt для роли: `{"role": "system", "content": "You are Kimi, an AI assistant..."}` — подтверждено гайдом «Requesting the Model to Assume a Role Can Yield More Accurate Output».
- Разделители (triple quotes, XML tags, section headings) для разных частей входа — официально подтверждено.
- Для JSON: дать конкретный пример вывода в промпте + `response_format={"type": "json_object"}`. Официально: «Define the output JSON format in the system or user prompt, including specific field names and field types; the best practice is to provide a concrete output example.»

### Что требовать строго
- Источники на каждый факт; числа только с URL; выдуманные данные запрещены. **Источник: только флот-канон** (вендорный гайд такого требования не содержит).
- При multi-turn: передавать полный `messages` list, включая `reasoning_content` и `tool_calls` из предыдущих ответов. Официально: «K3 requires the complete assistant message returned by the API to be passed back to messages as-is, including reasoning_content and tool_calls.»

### Страховка-валидация
- Деструктивные файловые операции только после diff/backup. **Источник: только флот-канон** (A/B 02.09 — kimi удаляет данные при конфликтных инструкциях).
- Для JSON: парсить `message.content` как JSON; если `response_format` не использован — проверять на malformed JSON (trailing commas, extra text).

### Анти-паттерны
- Конфликтные инструкции по формату — при конфликте удаляет данные (0/3, A/B 02.09). **Источник: только флот-канон.**
- Передавать `thinking.type` для k3 — ошибка; использовать только `reasoning_effort`.

### Официальные источники
- https://platform.kimi.ai/docs/guide/prompt-best-practice (доступ 2026-10-04)
- https://platform.kimi.ai/docs/guide/use-thinking-models.md (доступ 2026-10-04)
- https://platform.kimi.ai/docs/guide/use-reasoning-effort.md (доступ 2026-10-04)
- https://platform.kimi.ai/docs/guide/use-json-mode-feature-of-kimi-api.md (доступ 2026-10-04)
- https://platform.kimi.ai/docs/guide/engage-in-multi-turn-conversations-using-kimi-api.md (доступ 2026-10-04)
- https://platform.kimi.ai/docs/guide/context-caching.md (доступ 2026-10-04)

---

## 2. qwen3.8-max (Alibaba / DashScope)

### Канонические настройки
- `model`: `qwen3.8-max`
- System message: optional but recommended — «Defining the model's role and behavioral constraints produces more consistent and predictable output»
- `temperature`, `top_p`, `top_k`: не документированы для qwen3.8-max в официальном гайде; использовать default
- Vision: поддерживает single и multiple image inputs (через `image_url` + `text` в user message)

### Как брифовать
- Жёсткий формат вывода (JSON/схема), поля перечислены по порядку. Официально: «Build clear and specific prompts… The clearer, and more specific your task description (prompt) is, the more likely the LLM's performance will meet your expectations.»
- System message для behavioural constraints — подтверждено официальным гайдом.

### Что требовать строго
- Запрет уничтожения данных — при конфликте сохранить значение в восстановимой форме. **Источник: только флот-канон** (A/B 02.09 — qwen сохраняет данные 3/3).
- Краткость, без прозы после JSON. **Источник: только флот-канон.**

### Страховка-валидация
- Readback/валидация вывода по схеме. **Источник: только флот-канон.**

### Анти-паттерны
- Факты без проверки цитированием (галлюцинации 40%). **Источник: только флот-канон** (число 40% из внутреннего канона, не из официального источника).
- «Творческие» задания без жёсткого формата. **Источник: только флот-канон.**

### Официальные источники
- https://www.alibabacloud.com/help/en/model-studio/text-generation (доступ 2026-10-04)
- https://www.alibabacloud.com/help/en/model-studio/prompt-engineering-guide (доступ 2026-10-04)

---

## 3. glm-5.3 (Z.ai / Zhipu)

### Канонические настройки
- `model`: `glm-5.3`
- Thinking: **принудительно включён, отключить нельзя**. Официально: «GLM-5.3 uses forced thinking and cannot be disabled.»
- Thinking effort: `low` / `high` / `max` (из блога GLM-5.3; не путать с API-полем — в документации GLM-5.3 поле `thinking.type` не поддерживает `disabled`)
- `clear_thinking`: `false` для Preserved Thinking (default on Coding Plan, off on standard API)
- Structured output: поддерживается JSON

### Как брифовать
- Ревью по пунктам с номерами, каждый пункт — критерий. **Источник: флот-канон** (вендорный гайд не содержит ревью-специфики).
- Учитывать принудительный thinking: не просить «не думать», а задавать effort под задачу. Официально: «GLM-5.3 supports three thinking effort levels: low, high, and max. Disabling thinking is no longer supported.»

### Что требовать строго
- Вердикт структурирован по пунктам PASS/FAIL с цитатами; FAIL → нумерованные дефекты, не чинить. **Источник: флот-канон.**
- Interleaved thinking: thinking blocks должны быть preserved и возвращены вместе с tool results. Официально: «When using interleaved thinking with tools, thinking blocks should be explicitly preserved and returned together with the tool results.»

### Страховка-валидация
- На main/deploy — второй независимый вердикт (dual verdict 03.09). **Источник: только флот-канон.**
- Проверять `reasoning_content` на полноту при multi-turn: «Do not reorder or edit these blocks; otherwise, performance may degrade and cache hit rates may be affected.»

### Анти-паттерны
- Размытое «всё выглядит хорошо» без пунктов и evidence. **Источник: флот-канон.**
- Попытка отключить thinking — API вернёт ошибку или проигнорирует. Официально подтверждено.

### Официальные источники
- https://docs.z.ai/guides/llm/glm-5.3 (доступ 2026-10-04)
- https://docs.z.ai/guides/capabilities/thinking-mode (доступ 2026-10-04)
- https://z.ai/blog/glm-5.3 (доступ 2026-10-04)

---

## 4. gpt-6.1-sol (OpenAI)

### Канонические настройки
- `model`: `gpt-6.1-sol`
- `reasoning.effort`: `low` / `medium` (default) / `high` / `xhigh` / `max`
- **`none` и `minimal` не поддерживаются** — официально: «The none and minimal reasoning efforts are not supported.»
- Async tool calling: `async: true` на function tool; mid-turn steering через WebSocket
- API: Responses API для tool calling; Chat Completions для простых запросов без tools

### Как брифовать
- Короткий ясный текст, только суть; финишная линия в каждой задаче. **Источник: флот-канон** (вендорный гайд рекомендует precise instructions, но не ограничивает длину).
- Официально: «GPT models like gpt-6-astra benefit from precise instructions that explicitly provide the logic and data required to complete the task in the prompt.» — аналогично для sol.

### Что требовать строго
- Решение + обоснование в 3–5 предложениях. **Источник: флот-канон.**
- Без «think hard» — глубина только через `reasoning_effort`. Официально подтверждено: none/minimal не поддерживаются.

### Страховка-валидация
- Сверять поле `model` в usage — флагованный ответ тихо даунгрейдит модель. **Источник: только флот-канон.**

### Анти-паттерны
- Длинные многоуровневые брифы. **Источник: флот-канон** (вендорный гайд не запрещает длинные брифы, но рекомендует precise instructions).
- Хаотичная смена правил mid-turn. **Уточнение v2:** API поддерживает mid-turn steering через WebSocket («Send additional user instructions while GPT-6 is working… preserves completed work») — использовать контролируемо, не как смену ТЗ.

### Официальные источники
- https://developers.openai.com/api/docs/guides/latest-model (доступ 2026-10-04)
- https://developers.openai.com/api/docs/guides/prompt-engineering (доступ 2026-10-04)
- https://developers.openai.com/api/docs/guides/reasoning-best-practices (доступ 2026-10-04)
- https://openai.com/index/introducing-gpt-6-sol-and-luna/ (доступ 2026-10-04)

---

## 5. gpt-6-astra (OpenAI)

### Канонические настройки
- `model`: `gpt-6-astra`
- `reasoning.effort`: `low` / `medium` (default) / `high` / `xhigh` / `max`
- Fast mode и Ultrafast mode: доступны для всех пользователей astra
- Async tool calling: `async: true`

### Как брифовать
- Только узкий пакет — один вопрос/одно решение. **Источник: флот-канон** (вендорный гайд: «precise instructions that explicitly provide the logic and data»).
- Официально: «GPT-6 Astra… Highest intelligence. For the most demanding reasoning, coding, and professional work.»

### Что требовать строго
- Ответ в формате пакета, без развернутых исследований. **Источник: флот-канон.**

### Страховка-валидация
- Нужно глубокое исследование — передать классу research (kimi-k3). **Источник: флот-канон** (роутинг-правило).
- При жёстком SLA рассмотреть Fast/Ultrafast режимы. **Добавлено в v2** — официально: «All GPT-6 Astra users also have access to Fast mode and the new Ultrafast mode for our fastest API speeds.»

### Анти-паттерны
- Портфельные исследования и длинный анализ. **Источник: флот-канон.**

### Официальные источники
- https://developers.openai.com/api/docs/guides/latest-model (доступ 2026-10-04)
- https://developers.openai.com/api/docs/guides/prompt-engineering (доступ 2026-10-04)
- https://openai.com/index/practical-guide-building-gpt-6/ (доступ 2026-10-04)

---

## 6. qwen-vl-max (Alibaba / DashScope, vision)

### Канонические настройки
- `model`: `qwen-vl-max`
- Input modality: Text + Image + Video
- Function Calling: **Unsupported** (официально)
- Structured Outputs: **Supported** (официально)
- Context: 129K input / 8K output / 131K total
- Max image size: не документировано в официальном гайде; использовать `image_url` с URL или base64

### Как брифовать
- Одно изображение на вопрос; вопрос конкретный (что прочитать/описать). **Источник: флот-канон.**
- Официально: «Visual understanding models can answer questions based on the images or videos that you provide. They support single or multiple image inputs.»

### Что требовать строго
- Без параметра `reasoning_effort` (инвариант №3). **Источник: флот-канон** (документация не упоминает `reasoning_effort` для qwen-vl-max).
- Ответ в запрошенном формате.

### Страховка-валидация
- Критичное распознавание — перепроверка второй моделью (gpt-6-luna). **Источник: флот-канон.**

### Анти-паттерны
- Коллажи и несколько изображений в одном запросе без явной необходимости. **Смягчено в v2:** официально multi-image поддерживается; ограничение — флот-канон по качеству распознавания.
- Любая настройка effort. **Источник: флот-канон.**

### Официальные источники
- https://www.alibabacloud.com/help/en/model-studio/vision (доступ 2026-10-04)
- https://help.aliyun.com/en/model-studio/qwen-vl-max (доступ 2026-10-04)

---

## 7. gpt-6-luna (OpenAI, vision)

### Канонические настройки
- `model`: `gpt-6-luna`
- `reasoning.effort`: `none` / `low` / `medium` / `high` — **`none` поддерживается** (в отличие от astra/sol)
- Официально: «GPT-6 Sol and GPT-6 Luna do support the none reasoning effort.»

### Как брифовать
- Массовые простые просмотры — пачка однотипных изображений, low effort. **Источник: флот-канон** (вендорный гайд: «Fastest and most cost-effective. Strong performance for focused, high-volume tasks.»).

### Что требовать строго
- Короткий единообразный ответ на каждый элемент. **Источник: флот-канон.**

### Страховка-валидация
- Сложный/сомнительный кадр — эскалация на qwen-vl-max. **Источник: флот-канон** (роутинг-правило).
- Для массовых просмотров использовать `reasoning_effort: none`. **Добавлено в v2** — официально подтверждено.

### Анти-паттерны
- Детальный анализ одного изображения. **Источник: флот-канон.**

### Официальные источники
- https://developers.openai.com/api/docs/guides/latest-model (доступ 2026-10-04)
- https://openai.com/index/introducing-gpt-6-sol-and-luna/ (доступ 2026-10-04)

---

## 8. deepseek-v4-flash (DeepSeek) — NEW in v2

### Канонические настройки
- `model`: `deepseek-flash` (legacy `deepseek-v4-flash` accepted, served by DeepSeek-V4.1-Flash)
- `thinking`: `{"type": "enabled"}` / `{"type": "disabled"}` — thinking mode on/off
- `reasoning_effort`: `"high"` (only when thinking enabled; not supported in non-thinking mode)
- `temperature`, `top_p`, `presence_penalty`, `frequency_penalty`: **не поддерживаются** в thinking mode — «setting temperature, top_p, presence_penalty, frequency_penalty will not trigger an error but will also have no effect»
- `max_tokens`: default 32K, max 64K (включая CoT)
- Context: 1M tokens; max output 384K
- Context caching: enabled by default, disk-based; cache-hit price ~10% of cache-miss

### Как брифовать
- Чёткий system prompt + user prompt; для JSON — пример в промпте + `response_format={"type": "json_object"}`. Официально: «Include the word 'json' in the system or user prompt, and provide an example of the desired JSON format.»
- Для reasoning: включить thinking mode; для скорости — отключить.

### Что требовать строго
- При thinking mode: `reasoning_content` не передавать в следующий turn (только `content`). Официально: «In each turn of the conversation, the model outputs the CoT (reasoning_content) and the final answer (content). In the next turn… the CoT from previous turns is not concatenated into the context.»
- Для JSON: `max_tokens` достаточный, чтобы JSON не truncated.

### Страховка-валидация
- Проверять, что `content` не пустой (известная issue: «the API may occasionally return empty content»).
- Для FIM: использовать `base_url=https://api.deepseek.com/beta`.

### Анти-паттерны
- Использовать `logprobs`/`top_logprobs` в thinking mode — вызовет ошибку.
- Ожидать deterministic output при изменении `temperature` — параметр игнорируется в thinking mode.

### Официальные источники
- https://api-docs.deepseek.com/ (доступ 2026-10-04)
- https://api-docs.deepseek.com/quick_start/pricing (доступ 2026-10-04)
- https://api-docs.deepseek.com/guides/thinking_mode (доступ 2026-10-04)
- https://api-docs.deepseek.com/guides/json_mode (доступ 2026-10-04)
- https://api-docs.deepseek.com/guides/function_calling (доступ 2026-10-04)
- https://api-docs.deepseek.com/guides/kv_cache (доступ 2026-10-04)
- https://api-docs.deepseek.com/guides/chat_prefix_completion (доступ 2026-10-04)
- https://api-docs.deepseek.com/guides/fim_completion (доступ 2026-10-04)

---

## 9. Меж-агентный слой: handoff и reviewer-паттерны

### 9.1 Anthropic «Building Effective Agents» (2024-12-19)

**Официальный URL:** https://www.anthropic.com/engineering/building-effective-agents (доступ 2026-10-04)

**Workflow patterns (5 штук):**

| Pattern | Когда использовать | Пример |
|---------|-------------------|--------|
| **Prompt chaining** | Задача cleanly decomposes into fixed subtasks; trade latency for accuracy | Generate marketing copy → translate |
| **Routing** | Distinct categories better handled separately; classification accurate | Customer service: general/refund/technical → different prompts/tools |
| **Parallelization** | Subtasks parallelizable for speed, or multiple perspectives needed | Sectioning: guardrails + core response; Voting: multiple code reviews |
| **Orchestrator-workers** | Can't predict subtasks needed; dynamic delegation | Coding: number of files depends on task |
| **Evaluator-optimizer** | Clear evaluation criteria; iterative refinement valuable | Literary translation; complex search with multiple rounds |

**Agents (autonomous):**
- «Agents begin their work with either a command from, or interactive discussion with, the human user. Once the task is clear, agents plan and operate independently, potentially returning to the human for further information or judgement.»
- «During execution, it's crucial for the agents to gain 'ground truth' from the environment at each step (such as tool call results or code execution) to assess its progress.»
- «Agents can then pause for human feedback at checkpoints or when encountering blockers.»

**Tool design (Appendix 2):**
- «Give the model enough tokens to 'think' before it writes itself into a corner.»
- «Keep the format close to what the model has seen naturally occurring in text on the internet.»
- «Make sure there's no formatting 'overhead' such as having to keep an accurate count of thousands of lines of code, or string-escaping any code it writes.»
- «Poka-yoke your tools. Change the arguments so that it is harder to make mistakes.» (Example: absolute filepaths instead of relative after SWE-bench agent moved out of root directory.)

### 9.2 OpenAI «A Practical Guide to Building Agents» (PDF, 34 pages)

**Официальный URL:** https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf (доступ 2026-10-04)

**Agent foundations (3 components):**
1. Model — LLM powering reasoning and decision-making
2. Tools — external functions/APIs (Data, Action, Orchestration)
3. Instructions — explicit guidelines and guardrails

**Model selection principles:**
- «Set up evals to establish a performance baseline»
- «Focus on meeting your accuracy target with the best models available»
- «Optimize for cost and latency by replacing larger models with smaller ones where possible»

**When to split into multiple agents:**
- «Complex logic: When prompts contain many conditional statements (multiple if-then-else branches), and prompt templates get difficult to scale»
- «Tool overload: The issue isn't solely the number of tools, but their similarity or overlap. Some implementations successfully manage more than 15 well-defined, distinct tools while others struggle with fewer than 10 overlapping tools.»

**Orchestration patterns:**

| Pattern | Description | When to use |
|---------|-------------|-------------|
| **Single-agent** | One model with tools in a loop until exit condition | Most tasks; maximize single agent first |
| **Manager (agents as tools)** | Central manager coordinates specialized agents via tool calls | One agent controls workflow + user access |
| **Decentralized (handoffs)** | Agents hand off execution to peers; one-way transfer | No central control needed; specialized agents take over |

**Guardrails (layered defense):**
- Relevance classifier, Safety classifier, PII filter, Moderation, Tool safeguards, Rules-based protections, Output validation
- «Focus on data privacy and content safety; Add new guardrails based on real-world edge cases; Optimize for both security and user experience»

**Human intervention triggers:**
- Exceeding failure thresholds (retries)
- High-risk actions (sensitive, irreversible, high stakes)

### 9.3 Применение к флоту

| Флот-паттерн | Anthropic pattern | OpenAI pattern | Каноническая настройка |
|--------------|-------------------|----------------|------------------------|
| author → reviewer | Evaluator-optimizer | Single-agent + guardrails | Reviewer = отдельная модель (инвариант №2) |
| kanban dispatcher → worker | Routing / Orchestrator-workers | Manager / Decentralized | ROUTES по классам; R5 task_type mapping |
| research → synthesis | Prompt chaining | Single-agent with tools | kimi-k3 для research, synthesis вручную |
| code → test → fix | Evaluator-optimizer | Single-agent loop | qwen3.8-max / glm-5.3 |
| vision batch | Parallelization (sectioning) | Single-agent | qwen-vl-max / gpt-6-luna |

**Ключевое отличие флота от вендорских гайдов:** флот использует **фиксированный пул моделей** с жёстким роутингом (ROUTES), а не dynamic model selection. Это соответствует OpenAI принципу «build prototype with most capable model, then swap in smaller models» — но на уровне всего флота, а не одного агента.

---

## 10. Сводная таблица по моделям

| Модель | reasoning_effort | thinking | JSON mode | Tool calling | Vision | Context | Канонический источник |
|--------|-----------------|----------|-----------|--------------|--------|---------|----------------------|
| kimi-k3 | low/high/max (default max) | always on, preserved | ✓ | ✓ | ✓ | 1M | platform.kimi.ai |
| qwen3.8-max | — | — | ✓ | ✓ | ✓ | 128K | alibabacloud.com |
| glm-5.3 | low/high/max (forced) | forced, cannot disable | ✓ | ✓ | — | 128K | docs.z.ai |
| gpt-6.1-sol | low/medium/high/xhigh/max | — | ✓ | ✓ | — | — | developers.openai.com |
| gpt-6-astra | low/medium/high/xhigh/max | — | ✓ | ✓ | — | — | developers.openai.com |
| qwen-vl-max | — | — | ✓ | ✗ | ✓ | 131K | alibabacloud.com |
| gpt-6-luna | none/low/medium/high | — | ✓ | ✓ | ✓ | — | developers.openai.com |
| deepseek-v4-flash | high (thinking only) | enabled/disabled | ✓ | ✓ | ✗ | 1M | api-docs.deepseek.com |

---

## 11. Изменения v1 → v2

| Что | v1 | v2 |
|-----|----|----|
| Моделей | 7 | 8 (+deepseek-v4-flash) |
| Структура | 4 слоя | 5 слоёв (+канонические настройки) |
| Меж-агентный слой | нет | Anthropic 5 patterns + OpenAI orchestration |
| qwen-vl-max multi-image | анти-паттерн | смягчено (официально поддерживается) |
| gpt-6-astra Fast/Ultrafast | не отражено | добавлено |
| gpt-6-luna effort:none | не отражено | добавлено |
| glm-5.3 thinking | принудителен | + уровни low/high/max |
| mid-turn steering | анти-паттерн | уточнено (API поддерживает контролируемо) |

---

## 12. Открытые вопросы

1. **terra** — упомянута в ROUTES v3 (t_698a054c), но не найдена в официальных источниках. Возможно, внутреннее название или новая модель. Требуется уточнение.
2. **Kimi K3 tool calling best practices** — llms.txt ссылается на `kimi-k3-api-tool-calling-best-practices.md`, но URL возвращает Quickstart (404/redirect). Требуется ручная проверка.
3. **Qwen3.8-max temperature/top_p** — не документированы для этой конкретной модели; общие рекомендации Qwen3: temperature=0.7, top_p=0.8, top_k=20 (для Instruct-2507). Применимость к 3.8-max не подтверждена.
4. **GLM-5.3 API endpoint** — не найден в публичной документации; предположительно через Z.ai Coding Plan.

---

*Конец PATTERNS-SOURCES-v2.md*
