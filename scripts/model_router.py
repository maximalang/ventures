#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""model_router.py — автороутер флота «Рельсы v3» (ROUTES v3, карта t_91e8ce45, ред. 05.10.2026).

Логика: задача → класс → упорядоченный список моделей → первый подходящий;
неудача/блок → шаг вправо (явный пер-картовый пин с причиной, лог — фаза C).
Только stdlib, 0 сети, 0 LLM, 0 pip. Единый источник правды: ROUTES/RULES/
PATTERNS/INVARIANTS внутри этого файла; внешних данных и фикстур нет.

Канон: ventures/docs/fleet-ops/model-routing-20261003/PROGRAM.md (v2.2),
SPEC-routing-matrix-router.md, SPEC-router-v4-hardening.md, fleet-doctrine SKILL.md (числа),
OPEN-QUESTIONS-20261004.md (директива владельца 04.10), LADDER-PROVIDERS.md (T1/T2/T3,
правила лестницы), PATTERNS-SOURCES-v2.md (PATTERNS v2 — 5 слоёв + источники на каждую модель, карта t_234de1e7; сверка 2026-10-04).

Дельты v3 (поверх v2.2 + engine v4):
- рельсы только T1-провайдеров (custom, zai, openai-codex); T2/T3 никогда не в ROUTES;
- разнообразие: соседние элементы — разные провайдеры, ≤2 моделей одного провайдера,
  первые две позиции не однопровайдерные (канон-исключение: strategic — ручная рельса);
- GPT-ярусность (директива владельца 04.10): luna/terra — экономичные ступени,
  sol/astra — по назначению (strategic/owner-facing топ-рельса, astra только ручной пин);
- terra-ступень — только после положительной каталог-верификации (t_4e47fef0,
  05.10.2026: terra=available, обе строки пула HTTP 200);
- новые классы brief/creative для творческих профилей (design/ux/video-*) —
  GPT-ярусность + DashScope-руки, входят в лестницу;
- R7 деградация: все рельсы класса недоступны → дефолт профиля + degrade-строка
  (LADDER правило 6);
- PATTERNS v2 (карта t_234de1e7): 5 слоёв + канонические настройки + источники
  на каждую модель СТРОГО по PATTERNS-SOURCES-v2.md (сверка 2026-10-04);
  gpt-5.6-terra — маркер «только флот-канон» (§12 вопрос #1); deepseek-v4-flash —
  паттерн есть, в ROUTES не входит (дешёвые ступени — без class-quality evidence).
CLI: --card file.json [--status s.json] | --selftest | --print-rules | --patterns [MODEL]
"""
import argparse
import hashlib
import json
import re
import sys

VERSION = "3.1.0"  # v3.1: PATTERNS v2 (карта t_234de1e7); ROUTES/engine без изменений
ROUTES_VERSION = "v3"  # версия таблицы ROUTES (карта t_91e8ce45, директива владельца 04.10)
ROUTER_VERSION = "v4"  # версия движка (SPEC v4: --status, аудит-мета, selftest, R6) — ядро не менялось

if hasattr(sys.stdout, "reconfigure"):  # Windows: стабильный UTF-8 вывод
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# --- Константы лестницы (LADDER-PROVIDERS.md 03.10.2026 + директива владельца 04.10) ---
T1_PROVIDERS = ("custom", "zai", "openai-codex")  # T1 — стабильное ядро; T2 (agentrouter/TypeSafe/OpenRouter) и T3 в ROUTES никогда
# terra-ступень (scope b карты t_91e8ce45): только при положительной каталог-верификации.
# Верификация t_4e47fef0 (operations, done 05.10.2026): проба 2026-10-05T18:30:50Z,
# GET chatgpt.com/backend-api/codex/models?client_version=99.0.0 — HTTP 200 на обеих
# строках пула (a2662b, 8a052d), точная id-строка "gpt-5.6-terra" присутствует в каталоге.
# Телеметрия 30д: 0 вызовов → качество для классов НЕ доказано → terra экономичная ступень
# не выше середины списка (LADDER правило 1); повышение — только по shadow-данным.
TERRA_CATALOG_VERIFIED = True
TERRA_ALLOWED_CLASSES = ("brief", "creative")
DIVERSITY_EXEMPT = ("strategic",)  # канон: brain-рельса owner-facing, только ручной пин (sol+astra — оба openai-codex)
DEGRADE_MODEL = "PROFILE_DEFAULT"  # R7: все рельсы класса недоступны → дефолт профиля (LADDER правило 6)
DEGRADE_PROVIDER = "profile-default"

# --- ROUTES v3: 9 классов; порядок списка = предпочтение; обоснование = число/источник канона ---
ROUTES = {
    "code": {
        "models": ["custom/qwen3.8-max", "zai/glm-5.3", "custom/kimi-k3"],
        "why": "лестница 03.10: qwen3.8-max первый (reasoning max — канон, не даунгрейдить); glm-5.3 второй — провайдерное разнообразие (отказ custom не обнуляет класс, D1 пропускает рельсу до выбора); kimi-k3 третий (Terminal-Bench 2.1 88.3). v3: без изменений",
    },
    "data": {
        "models": ["custom/qwen3.8-max", "zai/glm-5.3", "custom/kimi-k3"],
        "why": "пайплайны/файлы/миграции: внутренний A/B 02.09 — qwen сохраняет данные 3/3, kimi удаляет 0/3 при конфликтных инструкциях (правило владельца: потеря данных хуже неопрятного формата) → qwen первый, kimi последний; v3: glm-5.3 второй — соседний провайдер (LADDER правило 2: отказ custom не обнуляет класс)",
    },
    "research": {
        "models": ["custom/kimi-k3", "zai/glm-5.3", "custom/qwen3.8-max"],
        "why": "kimi-k3 первый — сильнее в глубоком поиске (BrowseComp 91.2, DeepSearchQA 95.0); галлюцинации 51% против 40% — паттерн строго требует источник/URL на каждое число (канон fleet-doctrine); v3: glm-5.3 второй — LADDER правило 2 (соседние элементы — разные провайдеры; черновик списка LADDER нарушал собственное правило 2 — исправлено, см. ROUTES-V3-CHANGELOG)",
    },
    "ops": {
        "models": ["custom/qwen3.8-max", "zai/glm-5.3", "custom/kimi-k3"],
        "why": "лестница 03.10: qwen3.8-max первый — доменная работа и строгий чистый вывод (канон Round-2 02.09, reasoning max); glm-5.3 второй — провайдерное разнообразие; kimi-k3 третий. v3: без изменений",
    },
    "review": {
        "models": ["zai/glm-5.3", "openai-codex/gpt-6.1-sol", "custom/qwen3.8-max"],
        "why": "glm-5.3 = qa-сит (решение владельца 23.09; dual verdict 03.09); sol второй — живой бэкап при стене zai (инцидент rate-limit 04.10); qwen3.8-max третий — независимый резерв; author_model исключается из списка (инвариант №2, R1). v3: без изменений; terra не входит — качество для класса не доказано (LADDER правило 1)",
    },
    "strategic": {
        "models": ["openai-codex/gpt-6.1-sol", "openai-codex/gpt-6-astra"],
        "why": "owner-facing/портфель/protected: brain-рельса (канон fleet-doctrine Two-rail model) — sol решения, astra узкий пакет (только ручной пин); дешёвая рельса не первой. v3: канон-исключение LADDER правила 2 — класс ручной (стратегия остаётся ручной), отказ провайдера = решение владельца, не автолестница",
    },
    "vision": {
        "models": ["custom/qwen-vl-max", "openai-codex/gpt-6-luna"],
        "why": "qwen-vl-max — канон перцепции (PerceptionBench 63.5 против 58.5), без reasoning_effort (инвариант №3); luna (low/none effort) — массовые простые просмотры, качество доказано (телеметрия 30д: 125 вызовов). v3: без изменений",
    },
    "brief": {
        "models": ["openai-codex/gpt-6-luna", "custom/qwen3.8-max", "openai-codex/gpt-5.6-terra", "custom/kimi-k3"],
        "why": "v3-класс (директива владельца 04.10, OPEN-QUESTIONS-20261004 §1-2): брифы/копирайт/ТЗ творческих профилей — GPT-ярусность + DashScope-руки. luna первый — качество доказано (телеметрия 30д: 125 вызовов; none/low effort — developers.openai.com); qwen3.8-max второй — жёсткий формат вывода (A/B 02.09: данные 3/3); terra третий — каталог-верификация t_4e47fef0 05.10.2026 (HTTP 200 обе строки пула), качество для класса не доказано (0 вызовов 30д) → не выше середины; kimi-k3 четвёртый — цитатная дисциплина (platform.kimi.ai)",
    },
    "creative": {
        "models": ["custom/qwen3.8-max", "openai-codex/gpt-6-luna", "custom/kimi-k3", "openai-codex/gpt-5.6-terra"],
        "why": "v3-класс (директива владельца 04.10): design/ux/video-продакшн — DashScope-руки первые (qwen3.8-max: визуальный вход + строгий формат — alibabacloud.com model-studio); luna второй — экономичная GPT-ступень, качество доказано (125 вызовов 30д); kimi-k3 третий (визуальный вход, platform.kimi.ai); terra четвёртый — каталог-верификация t_4e47fef0, качество для класса в ожидании (0 вызовов 30д)",
    },
}

# --- PATTERNS v2 (карта t_234de1e7): 5 слоёв на каждую модель — как брифовать /
# требовать строго / страховка / анти-паттерн / канонические настройки + строка
# «источники» (traceability к цитате; сверка 2026-10-04). Источник правды слоя:
# docs/fleet-ops/model-routing-20261003/PATTERNS-SOURCES-v2.md
# (sha256 76e68e7c3cd536d5129746491bd209f8f3d6d6dd4591522fbb65e93d0206ab33).
# Формат строки совместим с hook v1.2.36+ (decision["pattern"] — строка целиком).
PATTERNS_VERSION = "v2"
PATTERNS_SOURCE_DOC = "PATTERNS-SOURCES-v2.md (сверка 2026-10-04, sha256 76e68e7c…)"
PATTERNS_V2_LAYERS = ("как брифовать:", "требовать строго:", "страховка:",
                      "анти-паттерн", "канонические настройки:", "источники:")
PATTERNS = {
    "kimi-k3": (
        "как брифовать: точное ТЗ, один deliverable, без параллельных веток («Write Clear Instructions — the less the model has to guess» — platform.kimi.ai); роль — system prompt; разделители (тройные кавычки/XML-теги/заголовки); JSON — конкретный пример вывода в промпте + response_format json_object.\n"
        "требовать строго: источники на каждый факт; числа только с URL; выдуманные данные запрещены (флот-канон). multi-turn: полный messages list as-is, включая reasoning_content и tool_calls (platform.kimi.ai).\n"
        "страховка: деструктивные файловые операции только после diff/backup (флот-канон); JSON без response_format — проверка на malformed (trailing commas, лишний текст).\n"
        "анти-паттерн: конфликтные инструкции по формату — при конфликте удаляет данные (0/3, A/B 02.09, флот-канон); thinking.type для k3 — ошибка (reserved for k2.x), только reasoning_effort.\n"
        "канонические настройки: reasoning_effort low/high/max (default max, top-level); thinking не передавать; response_format json_object; контекст 1M; cache-hit ~10% от цены cache-miss.\n"
        "источники: platform.kimi.ai/docs/guide/prompt-best-practice; use-thinking-models.md; use-reasoning-effort.md; use-json-mode-feature-of-kimi-api.md; engage-in-multi-turn-conversations-using-kimi-api.md; context-caching.md (сверка 2026-10-04)."),
    "qwen3.8-max": (
        "как брифовать: жёсткий формат вывода (JSON/схема), поля перечислены по порядку («the more specific your task description… the more likely the LLM's performance will meet your expectations» — alibabacloud.com); system message для роли и ограничений.\n"
        "требовать строго: запрет уничтожения данных — при конфликте сохранить значение в восстановимой форме (флот-канон, A/B 02.09: qwen сохраняет 3/3); краткость, без прозы после JSON (флот-канон).\n"
        "страховка: readback/валидация вывода по схеме (флот-канон).\n"
        "анти-паттерн: факты без проверки цитированием (галлюцинации 40%, флот-канон); «творческие» задания без жёсткого формата (флот-канон).\n"
        "канонические настройки: system message optional but recommended; temperature/top_p/top_k для 3.8-max не документированы → default; vision: single/multiple image_url + text.\n"
        "источники: alibabacloud.com/help/en/model-studio/text-generation; prompt-engineering-guide (сверка 2026-10-04)."),
    "glm-5.3": (
        "как брифовать: ревью по пунктам с номерами, каждый пункт — критерий (флот-канон); thinking принудителен — не просить «не думать», а задавать effort под задачу («Disabling thinking is no longer supported» — docs.z.ai).\n"
        "требовать строго: вердикт структурирован по пунктам PASS/FAIL с цитатами; FAIL → нумерованные дефекты, не чинить (флот-канон); interleaved thinking: thinking-блоки preserved и возвращаются вместе с tool results (docs.z.ai).\n"
        "страховка: на main/deploy — второй независимый вердикт (dual verdict 03.09, флот-канон); reasoning_content не переупорядочивать/не редактировать — деградация качества и кэш-хитов (docs.z.ai).\n"
        "анти-паттерн: размытое «всё выглядит хорошо» без пунктов и evidence (флот-канон); попытка отключить thinking — API вернёт ошибку или проигнорирует (docs.z.ai).\n"
        "канонические настройки: thinking forced (нельзя отключить); effort low/high/max; clear_thinking:false = Preserved Thinking (default Coding Plan); structured output JSON поддерживается.\n"
        "источники: docs.z.ai/guides/llm/glm-5.3; docs.z.ai/guides/capabilities/thinking-mode; z.ai/blog/glm-5.3 (сверка 2026-10-04)."),
    "gpt-6.1-sol": (
        "как брифовать: короткий ясный текст, только суть; финишная линия в каждой задаче (флот-канон); «precise instructions that explicitly provide the logic and data required to complete the task» (developers.openai.com).\n"
        "требовать строго: решение + обоснование в 3–5 предложениях (флот-канон); без «think hard» — глубина только через reasoning_effort; none/minimal не поддерживаются (developers.openai.com).\n"
        "страховка: сверять поле model в usage — флагованный ответ тихо даунгрейдит модель (флот-канон).\n"
        "анти-паттерн: длинные многоуровневые брифы (флот-канон); хаотичная смена правил mid-turn — API поддерживает контролируемый steering через WebSocket, но это не смена ТЗ (уточнение v2, developers.openai.com).\n"
        "канонические настройки: reasoning.effort low/medium(default)/high/xhigh/max; none и minimal NOT supported; async tool calling (async:true); Responses API для tools, Chat Completions для простых запросов.\n"
        "источники: developers.openai.com/api/docs/guides/latest-model; prompt-engineering; reasoning-best-practices; openai.com/index/introducing-gpt-6-sol-and-luna (сверка 2026-10-04)."),
    "gpt-6-astra": (
        "как брифовать: только узкий пакет — один вопрос/одно решение (флот-канон); «precise instructions that explicitly provide the logic and data» (developers.openai.com).\n"
        "требовать строго: ответ в формате пакета, без развернутых исследований (флот-канон).\n"
        "страховка: нужно глубокое исследование — передать классу research (kimi-k3, флот-канон); при жёстком SLA — Fast/Ultrafast режимы («All GPT-6 Astra users also have access to Fast mode and the new Ultrafast mode» — openai.com, добавлено в v2).\n"
        "анти-паттерн: портфельные исследования и длинный анализ (флот-канон).\n"
        "канонические настройки: reasoning.effort low/medium(default)/high/xhigh/max; Fast и Ultrafast mode доступны всем пользователям astra; async tool calling.\n"
        "источники: developers.openai.com/api/docs/guides/latest-model; prompt-engineering; openai.com/index/practical-guide-building-gpt-6 (сверка 2026-10-04)."),
    "qwen-vl-max": (
        "как брифовать: одно изображение на вопрос; вопрос конкретный — что прочитать/описать (флот-канон); официально поддержаны single и multiple image inputs (alibabacloud.com).\n"
        "требовать строго: без параметра reasoning_effort (инвариант №3, флот-канон); ответ в запрошенном формате; Function Calling не поддерживается, Structured Outputs поддерживается (alibabacloud.com).\n"
        "страховка: критичное распознавание — перепроверка второй моделью (gpt-6-luna, флот-канон).\n"
        "анти-паттерн: любая настройка effort (флот-канон); коллажи/несколько изображений — официально multi-image поддерживается, ограничение флот-канона по качеству распознавания (смягчено в v2).\n"
        "канонические настройки: input text+image+video; Function Calling Unsupported; Structured Outputs Supported; контекст 129K input / 8K output / 131K total.\n"
        "источники: alibabacloud.com/help/en/model-studio/vision; help.aliyun.com/en/model-studio/qwen-vl-max (сверка 2026-10-04)."),
    "gpt-6-luna": (
        "как брифовать: массовые простые просмотры — пачка однотипных изображений, low/none effort («Fastest and most cost-effective. Strong performance for focused, high-volume tasks» — developers.openai.com); творческие брифы — короткий ясный пакет (флот-канон).\n"
        "требовать строго: короткий единообразный ответ на каждый элемент (флот-канон).\n"
        "страховка: сложный/сомнительный кадр — эскалация на qwen-vl-max (флот-канон); для массовых просмотров reasoning_effort:none — «GPT-6 Sol and GPT-6 Luna do support the none reasoning effort» (developers.openai.com, добавлено в v2).\n"
        "анти-паттерн: детальный анализ одного изображения; портфельные исследования (флот-канон).\n"
        "канонические настройки: reasoning.effort none/low/medium/high — none поддерживается (в отличие от sol/astra).\n"
        "источники: developers.openai.com/api/docs/guides/latest-model; openai.com/index/introducing-gpt-6-sol-and-luna (сверка 2026-10-04)."),
    "gpt-5.6-terra": (
        "как брифовать: короткий ясный текст, только суть, один deliverable — экономичная ступень (GPT-семейство: precise instructions — developers.openai.com/api/docs/guides/prompt-engineering).\n"
        "требовать строго: результат + краткое обоснование; глубина только через reasoning_effort; сверять поле model в usage (тихий даунгрейд — флот-канон).\n"
        "страховка: качество для класса не доказано (телеметрия 30д: 0 вызовов; каталог-верификация t_4e47fef0 05.10.2026 — HTTP 200 обе строки пула) → результат критичного класса через независимую QA.\n"
        "анти-паттерн: постановка на первые две позиции класса; портфельные исследования и длинный анализ. Источник: только флот-канон (в вендорном корпусе PATTERNS-SOURCES-v2 terra отсутствует — §12 вопрос #1) + гайды GPT-семейства.\n"
        "канонические настройки: вендорных настроек для terra нет (§12 вопрос #1); по гайдам GPT-семейства глубиной управляет reasoning_effort (developers.openai.com).\n"
        "источники: только флот-канон + developers.openai.com/api/docs/guides/prompt-engineering (GPT-семейство); каталог-верификация t_4e47fef0 05.10.2026 (сверка 2026-10-04)."),
    "deepseek-v4-flash": (
        "как брифовать: чёткий system + user prompt; для JSON — слово «json» в промпте + пример формата + response_format json_object («Include the word 'json'… and provide an example of the desired JSON format» — api-docs.deepseek.com); reasoning → thinking enabled, скорость → disabled.\n"
        "требовать строго: в thinking mode reasoning_content не передавать в следующий turn — только content (api-docs.deepseek.com); max_tokens достаточный, чтобы JSON не truncated.\n"
        "страховка: проверять content на пустоту (известная issue: «the API may occasionally return empty content»); для FIM — base_url=https://api.deepseek.com/beta.\n"
        "анти-паттерн: logprobs/top_logprobs в thinking mode — ошибка; ожидать детерминизма от temperature — в thinking mode параметры игнорируются (api-docs.deepseek.com).\n"
        "канонические настройки: model deepseek-flash (legacy deepseek-v4-flash); thinking enabled/disabled; reasoning_effort high только при thinking; temperature/top_p/presence_penalty/frequency_penalty в thinking mode игнорируются; max_tokens 32K default / 64K max; контекст 1M, output 384K; кэш по умолчанию, хит ~10%.\n"
        "источники: api-docs.deepseek.com/guides/thinking_mode; json_mode; function_calling; kv_cache; chat_prefix_completion; fim_completion; quick_start/pricing (сверка 2026-10-04)."),
}

RULES_SHA = hashlib.sha1(json.dumps({"ROUTES": ROUTES, "PATTERNS": PATTERNS}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:12]  # D2: отпечаток правил — sha1 канонического дампа, [:12]; детерминизм между прогонами

# --- Жёсткие правила: применяются до выбора; при коллизии побеждает старший номер (R3 > R2) ---
RULES = [
    ("R1", "task_type=review → author_model исключается из списка класса (инвариант №2: проверяющий на чужой модели)."),
    ("R2", "owner_facing=true или protected (main/deploy/publish в title/body) → класс strategic."),
    ("R3", "needs_vision=true → класс vision (способность выше тира: R3 перекрывает R2)."),
    ("R4", "prior_run_failed=true → следующий элемент списка (эскалация одним шагом вправо; на конце списка остаётся последний)."),
    ("R5", "спорный класс (нет маркеров) → устойчивый маппинг task_type→класс (research→research, ops→ops, review→review, code→code, brief→brief, creative→creative, code+файловые ключевые слова→data); неизвестный task_type → code."),
    ("R6", "кэш-дисциплина (инвариант №5, канон 8): повторная карта той же работы рекомендует ту же модель — роутер детерминирован; единственная причина смены — prior_run_failed (R4: шаг вправо с логом)."),
    ("R7", "деградация v3 (LADDER правило 6): все рельсы класса недоступны по --status → дефолт профиля (model=PROFILE_DEFAULT) + degrade-строка в reason; деградация явная (инвариант №1), решение выдаётся всегда."),
]

INVARIANTS = [  # PROGRAM.md v2.2, раздел «Инварианты (5)»
    "1. Выбор модели — только ДО старта задачи; тихой подмены на ходу нет.",
    "2. Проверяющий всегда на чужой модели (review исключает author_model).",
    "3. DashScope-модели — reasoning max (конфиг-уровень); qwen-vl-max — без effort.",
    "4. TG = qwen3.8-max и дефолты профилей — только словом владельца.",
    "5. Внутри живой сессии модель не переключаем (prompt cache).",
]

PROTECTED_RE = re.compile(r"\b(main|deploy(?:ment|s|ing)?|publish(?:ing|ed|es)?)\b", re.I)
DATA_RE = re.compile(
    r"\b(migrat\w*|pipeline\w*|etl|csv|tsv|parquet|dump\w*|ingest\w*|lockfile|"
    r"database|backup\w*|миграц\w*|пайплайн\w*|выгрузк\w*)\b", re.I)
TASK_TYPE_CLASS = {"research": "research", "ops": "ops", "review": "review", "code": "code",
                   "data": "data", "brief": "brief", "creative": "creative"}  # v3: + brief/creative (R5)

DEGRADE_PATTERN = (  # R7: паттерн деградации — дефолт профиля, явная строка
    "как брифовать: дефолт профиля — карта идёт на модель профиля без override (R7 деградация).\n"
    "требовать строго: обычный контракт профиля; причина деградации зафиксирована в reason и ROUTING-LOG.md.\n"
    "страховка: после восстановления рельс — повторный диспатч через роутер; вынужденная смена модели логируется (R6 не применяется).\n"
    "анти-паттерн: тихая подмена на ходу (инвариант №1) — деградация всегда явная, с degrade-строкой.")


def load_status(path):  # D1: --status JSON → (dict|None, warn|None); нет файла/битый/пустой → (None, warn)
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        data = None
    if isinstance(data, dict) and data:
        return data, None
    return None, "W1: --status не прочитан (нет файла/битый JSON/пустой) — все рельсы считаются доступными (безопасная деградация)"


def _rail_down(status, full):  # D1: рельса "provider/model" недоступна по --status (ключ: точный id, короткое имя модели, provider)
    prov, _, mod = full.partition("/")
    marks = [status.get(k) for k in (full, mod, prov)]
    return any(v is False or (isinstance(v, dict) and v.get("available") is False) for v in marks)


def classify(card, status=None, status_warn=None):
    """Карта (dict) + опциональный статус доступности (D1) → рекомендация: поля v3 + аудит-мета D2."""
    text = " ".join(str(card.get(k) or "") for k in ("title", "body"))
    tt = str(card.get("task_type") or "").strip().lower()
    author = str(card.get("author_model") or "").strip().lower()
    echo = {k: card[k] for k in ("title", "body", "task_type", "author_model", "needs_vision", "owner_facing", "prior_run_failed") if k in card}  # D2: использованные поля входа
    fired, notes = [], []
    cls = TASK_TYPE_CLASS.get(tt)  # R5: устойчивый маппинг task_type→класс (v3: + brief/creative)
    if cls is None:
        cls, cls_reason = "code", "R5: неизвестный/пустой task_type → дефолт code"
    elif cls == "code" and DATA_RE.search(text):
        cls, cls_reason = "data", "R5: code→data по файловым ключевым словам (миграции/пайплайны/дампы)"
    else:
        cls_reason = f"R5: устойчивый маппинг task_type→{cls}"
    fired.append("R5")
    if card.get("owner_facing") or PROTECTED_RE.search(text):
        cls, cls_reason = "strategic", "R2: owner_facing/protected (main/deploy/publish) → strategic"
        fired.append("R2")
    if card.get("needs_vision"):
        cls, cls_reason = "vision", "R3: needs_vision → vision (способность выше тира)"
        fired.append("R3")
    models = list(ROUTES[cls]["models"])
    if status_warn:  # D1: предупреждение — в rules_fired; решение выдаётся в любом случае
        fired.append("W1"); notes.append(status_warn)
    elif status:
        avail = [m for m in models if not _rail_down(status, m)]
        if avail and len(avail) < len(models):
            fired.append("S1"); dropped = [m for m in models if m not in avail]; models = avail
            notes.append("S1: --status пропустил недоступные рельсы ДО выбора: " + ", ".join(dropped))
        elif not avail:
            # R7 (v3, LADDER правило 6): все рельсы класса недоступны → дефолт профиля + degrade-строка
            fired.append("W1"); fired.append("R7")
            return {"class": cls, "model": DEGRADE_MODEL, "provider": DEGRADE_PROVIDER,
                    "reasoning": ROUTES[cls]["why"], "pattern": DEGRADE_PATTERN,
                    "reason": cls_reason + f"; R7 degrade: все рельсы класса {cls} недоступны по --status → дефолт профиля (LADDER правило 6)",
                    "rules_fired": fired, "router_version": ROUTER_VERSION,
                    "routes_version": ROUTES_VERSION, "rules_sha": RULES_SHA, "input_echo": echo}
    if cls == "review" and author:
        kept = [m for m in models if m.split("/")[-1] != author.split("/")[-1]]
        if kept and len(kept) < len(models):
            models = kept
            fired.append("R1")
            notes.append("R1: author_model исключён из списка review")
        elif not kept:
            notes.append("R1: исключение опустошило бы список — оставлен полный")
    idx = 0
    if card.get("prior_run_failed"):
        idx = min(1, len(models) - 1)
        fired.append("R4")
        notes.append("R4: эскалация одним шагом вправо" + ("" if idx else " — на конце списка, оставлен последний"))
    if not notes:
        notes.append("первый подходящий в списке предпочтений")
    provider, model = models[idx].split("/", 1)
    return {"class": cls, "model": model, "provider": provider,
            "reasoning": ROUTES[cls]["why"], "pattern": PATTERNS[model],
            "reason": cls_reason + "; " + "; ".join(notes), "rules_fired": fired,
            "router_version": ROUTER_VERSION, "routes_version": ROUTES_VERSION,
            "rules_sha": RULES_SHA, "input_echo": echo}  # D2: аудит-мета; v3: + routes_version


def _structural_checks():
    """v3: проверки данных ROUTES на правила LADDER-PROVIDERS.md и scope карты t_91e8ce45."""
    ok, lines = True, []

    def add(good, text):
        nonlocal ok
        ok = ok and good
        lines.append(f"{'PASS' if good else 'FAIL'}  {text}")

    all_models = {m.split("/")[-1] for r in ROUTES.values() for m in r["models"]}
    missing = sorted(all_models - set(PATTERNS))
    add(not missing, "структура: PATTERNS есть на каждую модель списков ROUTES" + ("" if not missing else f" (нет: {missing})"))
    old7 = {"code", "data", "research", "ops", "review", "strategic", "vision"}
    add(old7 <= set(ROUTES), "структура: старые 7 классов сохранены (v3 добавляет brief/creative)")
    provs = {m.split("/")[0] for r in ROUTES.values() for m in r["models"]}
    add(provs <= set(T1_PROVIDERS), f"структура: рельсы только T1-провайдеров {list(T1_PROVIDERS)}, найдено: {sorted(provs)}")
    bad = []
    for cls, r in ROUTES.items():
        if cls in DIVERSITY_EXEMPT:
            continue
        ps = [m.split("/")[0] for m in r["models"]]
        if any(a == b for a, b in zip(ps, ps[1:])):
            bad.append(f"{cls}: соседние элементы одного провайдера")
        if len(ps) >= 2 and ps[0] == ps[1]:
            bad.append(f"{cls}: первые две позиции одного провайдера")
        cnt = {}
        for p in ps:
            cnt[p] = cnt.get(p, 0) + 1
        if max(cnt.values()) > 2:
            bad.append(f"{cls}: >2 моделей одного провайдера")
    add(not bad, "структура: разнообразие — соседние разные провайдеры, ≤2 на провайдера, первые две не однопровайдерные (исключение: strategic — ручной класс)" + ("" if not bad else "; " + "; ".join(bad)))
    terra = "openai-codex/gpt-5.6-terra"
    t_cls = [c for c, r in ROUTES.items() if terra in r["models"]]
    if TERRA_CATALOG_VERIFIED:
        t_ok = all(c in TERRA_ALLOWED_CLASSES for c in t_cls) and all(ROUTES[c]["models"].index(terra) >= 2 for c in t_cls)
    else:
        t_ok = not t_cls  # без положительной верификации terra-ступени нет вовсе
    add(t_ok, f"структура: terra — catalog-verified={TERRA_CATALOG_VERIFIED} (t_4e47fef0), классы={t_cls or '—'}, не на первых двух позициях (качество для класса не доказано)")
    astra = [c for c, r in ROUTES.items() if any(m.endswith("/gpt-6-astra") for m in r["models"])]
    sol = [c for c, r in ROUTES.items() if any(m.endswith("/gpt-6.1-sol") for m in r["models"])]
    add(set(astra) <= {"strategic"} and set(sol) <= {"strategic", "review"},
        f"структура: sol/astra по назначению (astra⊆strategic — только ручной пин; sol⊆strategic+review): astra={astra}, sol={sol}")
    add("флот-канон" in PATTERNS.get("gpt-5.6-terra", ""),
        "структура: паттерн terra содержит маркер источника (сверка PATTERNS-SOURCES-v2: в вендорном корпусе отсутствует → только флот-канон)")
    bad_v2 = sorted(m for m, p in PATTERNS.items() if not all(l in p for l in PATTERNS_V2_LAYERS))
    add(not bad_v2, f"структура v2: каждая запись PATTERNS несёт 5 слоёв + строку источники ({len(PATTERNS)} записей, PATTERNS {PATTERNS_VERSION})"
        + ("" if not bad_v2 else f"; слои не найдены: {bad_v2}"))
    add("deepseek-v4-flash" in PATTERNS and "api-docs.deepseek.com" in PATTERNS["deepseek-v4-flash"],
        "структура v2: deepseek-v4-flash — паттерн по §8 PATTERNS-SOURCES-v2 (в ROUTES не входит: дешёвые ступени без class-quality evidence, LADDER правило 1)")
    return ok, lines


CASES = [  # (имя, карта, ожидаемый класс, ожидаемая модель[, статус D1]) — v4-ядро + входы v3 (карта t_91e8ce45)
    ("code: первый подходящий", {"title": "Реализовать парсер логов", "body": "модуль и тесты", "task_type": "code"}, "code", "qwen3.8-max"),
    ("R1: review исключает author_model", {"title": "Ревью диффа задачи 42", "body": "проверить тесты", "task_type": "review", "author_model": "zai/glm-5.3"}, "review", "gpt-6.1-sol"),
    ("R2: owner_facing → strategic", {"title": "Бриф владельцу по портфелю", "body": "сводка", "task_type": "ops", "owner_facing": True}, "strategic", "gpt-6.1-sol"),
    ("R2: protected deploy → strategic", {"title": "deploy релиза на прод", "body": "чек-лист", "task_type": "code"}, "strategic", "gpt-6.1-sol"),
    ("R3: needs_vision → vision", {"title": "Прочитать текст со скриншота", "body": "одно изображение", "task_type": "research", "needs_vision": True}, "vision", "qwen-vl-max"),
    ("R4: prior_run_failed → шаг вправо", {"title": "Реализовать парсер логов", "body": "прошлый прогон упал", "task_type": "code", "prior_run_failed": True}, "code", "glm-5.3"),
    ("R5: code+миграция → data", {"title": "db migration", "body": "схема и lockfile", "task_type": "code"}, "data", "qwen3.8-max"),
    ("R5: спорный класс → дефолт code", {"title": "Непонятная задача", "body": "", "task_type": "misc"}, "code", "qwen3.8-max"),
    ("D1: --status провайдер zai недоступен → следующий элемент", {"title": "Ревью диффа задачи 42", "body": "проверить тесты", "task_type": "review"}, "review", "gpt-6.1-sol", {"zai": {"available": False}}),
    ("D3: вход без единого маркера → устойчивый маппинг", {"title": "", "body": "", "task_type": "ops"}, "ops", "qwen3.8-max"),
    ("D3: protected main в title → strategic", {"title": "Слияние в main", "body": "чек-лист", "task_type": "code"}, "strategic", "gpt-6.1-sol"),
    # --- входы v3: новые классы, правила лестницы, деградация (acceptance карты t_91e8ce45) ---
    ("v3 research: kimi первый, соседний провайдер zai второй", {"title": "Глубокий поиск рынка", "body": "обзор источников", "task_type": "research"}, "research", "kimi-k3"),
    ("v3 brief: GPT-ступень luna первая", {"title": "Бриф для дизайнера", "body": "текст и структура", "task_type": "brief"}, "brief", "gpt-6-luna"),
    ("v3 creative: DashScope-руки первые", {"title": "Концепт визуала лендинга", "body": "макет и палитра", "task_type": "creative"}, "creative", "qwen3.8-max"),
    ("v3 R4: creative + prior_run_failed → шаг вправо", {"title": "Концепт визуала лендинга", "body": "прошлый прогон упал", "task_type": "creative", "prior_run_failed": True}, "creative", "gpt-6-luna"),
    ("v3 R4: data + prior_run_failed → соседний провайдер zai", {"title": "db migration", "body": "выгрузка", "task_type": "code", "prior_run_failed": True}, "data", "glm-5.3"),
    ("v3 brief: terra не в первых двух (шаг вправо → qwen3.8-max)", {"title": "Копирайт для продукта", "body": "оффер", "task_type": "brief", "prior_run_failed": True}, "brief", "qwen3.8-max"),
    ("v3 R7 деградация: все рельсы класса недоступны → дефолт профиля", {"title": "Рутинная ops задача", "body": "чек-лист", "task_type": "ops"}, "ops", "PROFILE_DEFAULT", {"custom": False, "zai": False, "openai-codex": False}),
]


PATTERN_CASES = [  # v2-формат (карта t_234de1e7): паттерн модели несёт заявленные слои/маркеры
    ("v2 kimi-k3: multi-turn as-is + platform.kimi.ai", "kimi-k3",
     ["reasoning_content", "platform.kimi.ai", "канонические настройки:"]),
    ("v2 glm-5.3: forced thinking + docs.z.ai", "glm-5.3",
     ["Disabling thinking is no longer supported", "docs.z.ai", "источники:"]),
    ("v2 gpt-6-luna: effort none поддержан + developers.openai.com", "gpt-6-luna",
     ["do support the none reasoning effort", "developers.openai.com"]),
    ("v2 deepseek-v4-flash: thinking mode + api-docs.deepseek.com", "deepseek-v4-flash",
     ["thinking", "api-docs.deepseek.com", "reasoning_content"]),
    ("v2 gpt-5.6-terra: маркер «только флот-канон» + каталог-верификация", "gpt-5.6-terra",
     ["флот-канон", "t_4e47fef0"]),
]


def selftest():
    print(f"model_router {VERSION} routes {ROUTES_VERSION} engine {ROUTER_VERSION} patterns {PATTERNS_VERSION} — selftest: {len(CASES)} кейсов + {len(PATTERN_CASES)} v2-паттерн-кейсов + структурные проверки, 0 сети")
    ok = True
    s_ok, s_lines = _structural_checks()
    ok = ok and s_ok
    for line in s_lines:
        print(line)
    for name, card, exp_cls, exp_model, *rest in CASES:
        r = classify(card, rest[0] if rest else None)
        good = r["class"] == exp_cls and r["model"] == exp_model and bool(r["pattern"])
        ok = ok and good
        tail = "" if good else f" (ожидалось {exp_cls}/{exp_model})"
        print(f"{'PASS' if good else 'FAIL'}  {name} → {r['class']}/{r['model']}{tail}")
    for name, model, subs in PATTERN_CASES:  # v2: traceability слоёв паттерна
        p = PATTERNS.get(model, "")
        good = bool(p) and all(s in p for s in subs)
        ok = ok and good
        miss = [s for s in subs if s not in p]
        print(f"{'PASS' if good else 'FAIL'}  {name}" + ("" if good else f" (нет: {miss})"))
    print(f"итог: {'ALL PASS' if ok else 'ЕСТЬ ПАДЕНИЯ'}")
    return 0 if ok else 1


def print_patterns(model=None):
    """--patterns [MODEL]: JSON паттернов v2 — машинный контракт для delegation/
    brain-brief/hands-deliverable шаблонов и субагентов (карта t_234de1e7).
    Выход: {patterns_version, source, rules_sha, models, patterns}; exit 2 при
    неизвестной модели. Детерминирован: sort_keys, 0 сети."""
    if model is not None and model not in PATTERNS:
        print(f"ошибка: модель {model!r} не найдена в PATTERNS; доступные: {', '.join(sorted(PATTERNS))}", file=sys.stderr)
        return 2
    sel = {model: PATTERNS[model]} if model is not None else dict(PATTERNS)
    out = {"patterns_version": PATTERNS_VERSION, "source": PATTERNS_SOURCE_DOC,
           "rules_sha": RULES_SHA, "models": sorted(sel), "patterns": sel}
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def print_rules():
    print(f"rules_sha {RULES_SHA}")  # D2: отпечаток правил — первая строка вывода
    print(f"Политика автороутера «Рельсы v{VERSION}» (ROUTES {ROUTES_VERSION}, engine {ROUTER_VERSION}) — вывод --print-rules (источник правды: model_router.py)")
    print("\n== Классы и списки предпочтений (порядок = предпочтение; обоснование = число/источник канона) ==")
    for name, r in ROUTES.items():
        print(f"- {name}: " + " → ".join(r["models"]))
        print(f"    обоснование: {r['why']}")
    print("\n== Жёсткие правила (применяются до выбора, по порядку) ==")
    for rid, text in RULES:
        print(f"- {rid}: {text}")
    print("\n== Эскалация и деградация ==")
    print("- Неудача/блок → шаг вправо по списку; на конце — остаётся последняя модель.")
    print("- Эскалация явная: пер-картовый пин с причиной + строка в ROUTING-LOG.md (фаза C); тихой подмены на ходу нет (инвариант №1).")
    print(f"- R7 деградация (v3): все рельсы класса недоступны по --status → дефолт профиля (model={DEGRADE_MODEL}) + degrade-строка в reason (LADDER правило 6).")
    print("\n== Лестница провайдеров (LADDER-PROVIDERS.md; v3) ==")
    print(f"- Рельсы только T1-провайдеров: {', '.join(T1_PROVIDERS)}; T2 (agentrouter/TypeSafe/OpenRouter) и T3 в ROUTES никогда.")
    print("- Разнообразие: соседние элементы — разные провайдеры, ≤2 моделей одного провайдера в списке, первые две позиции не однопровайдерные; исключение: strategic (ручной класс).")
    print("- GPT-ярусность (директива владельца 04.10): sol/astra — по назначению (strategic — топ-рельса, astra только ручной пин; sol — живой бэкап review); luna/terra — экономичные ступени (brief/creative; luna — также vision).")
    print(f"- terra: catalog-verified={TERRA_CATALOG_VERIFIED} (t_4e47fef0, 05.10.2026); разрешённые классы: {', '.join(TERRA_ALLOWED_CLASSES)}; не на первых двух позициях — качество для класса не доказано (телеметрия 30д: 0 вызовов); повышение — только по shadow-данным.")
    print(f"\n== Паттерны общения на каждую модель (PATTERNS {PATTERNS_VERSION}: 5 слоёв + источники; целиком — для вставки в спецификацию) ==")
    for m in sorted(PATTERNS):
        print(f"--- {m} ---")
        print(PATTERNS[m])
    print("\n== Инварианты (PROGRAM.md v2.2) ==")
    for inv in INVARIANTS:
        print(f"- {inv}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Автороутер «Рельсы v3»: задача → класс → модель → паттерн.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--card", metavar="FILE.JSON",
                   help="JSON карты: title, body, task_type, author_model, needs_vision, owner_facing, prior_run_failed")
    g.add_argument("--selftest", action="store_true", help="встроенные кейсы + структурные проверки, таблица PASS/FAIL, exit 0/1")
    g.add_argument("--print-rules", action="store_true", help="человекочитаемая политика (те же данные); первая строка — rules_sha")
    g.add_argument("--patterns", nargs="?", const="__all__", metavar="MODEL",
                   help="JSON паттернов v2 (машинный контракт delegation/brain-brief): без аргумента — все модели, с аргументом — одна; поля: patterns_version, source, rules_sha, models, patterns")
    ap.add_argument("--status", metavar="S.JSON", help="опционально с --card (D1): {\"<provider|модель>\": {\"available\": false}} — пропуск недоступной рельсы ДО выбора; все недоступны → R7 дефолт профиля")
    args = ap.parse_args(argv)
    if args.status and not args.card: print("ошибка: --status используется только с --card", file=sys.stderr); return 2
    if args.selftest:
        return selftest()
    if args.print_rules:
        return print_rules()
    if args.patterns:
        return print_patterns(None if args.patterns == "__all__" else args.patterns)
    try:
        with open(args.card, encoding="utf-8") as fh:
            card = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"ошибка: не прочитан --card {args.card}: {exc}", file=sys.stderr)
        return 2
    if not isinstance(card, dict):
        print("ошибка: карта должна быть JSON-объектом", file=sys.stderr)
        return 2
    status, status_warn = load_status(args.status) if args.status else (None, None)  # D1: деградация безопасна
    print(json.dumps(classify(card, status, status_warn), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
