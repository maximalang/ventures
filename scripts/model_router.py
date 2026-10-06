#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""model_router.py — автороутер флота «Рельсы v2.2» (SPEC v3 + дельты v4, ред. 03.10.2026).

Логика: задача → класс → упорядоченный список моделей → первый подходящий;
неудача/блок → шаг вправо (явный пер-картовый пин с причиной, лог — фаза C).
Только stdlib, 0 сети, 0 LLM, 0 pip. Единый источник правды: ROUTES/RULES/
PATTERNS/INVARIANTS внутри этого файла; внешних данных и фикстур нет.
Канон: ventures/docs/fleet-ops/model-routing-20261003/PROGRAM.md (v2.2),
SPEC-routing-matrix-router.md, SPEC-router-v4-hardening.md, fleet-doctrine SKILL.md (числа).
v4-дельты: D1 --status (пропуск недоступной рельсы ДО выбора; деградация безопасна),
D2 аудит-мета (router_version/rules_sha/input_echo), D3 selftest 11 кейсов, D5 правило R6 (кэш-дисциплина повтора). CLI: --card file.json [--status s.json] | --selftest | --print-rules
"""
import argparse
import hashlib
import json
import re
import sys

VERSION = "2.2.0"
ROUTER_VERSION = "v4"  # D2: версия самого роутера (SPEC v4 — дельта над SPEC v3, ядро не менялось)

if hasattr(sys.stdout, "reconfigure"):  # Windows: стабильный UTF-8 вывод
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# --- ROUTES: 7 классов; порядок списка = предпочтение; обоснование = число канона ---
ROUTES = {
    "code": {
        "models": ["custom/qwen3.8-max", "zai/glm-5.3", "custom/kimi-k3"],
        "why": "лестница 03.10: qwen3.8-max первый (reasoning max — канон, не даунгрейдить); glm-5.3 второй — провайдерное разнообразие (отказ custom не обнуляет класс, D1 пропускает рельсу до выбора); kimi-k3 третий (Terminal-Bench 2.1 88.3)",
    },
    "data": {
        "models": ["custom/qwen3.8-max", "custom/kimi-k3"],
        "why": "пайплайны/файлы/миграции: внутренний A/B 02.09 — qwen сохраняет данные 3/3, kimi удаляет 0/3 при конфликтных инструкциях; правило владельца: потеря данных хуже неопрятного формата",
    },
    "research": {
        "models": ["custom/kimi-k3", "custom/qwen3.8-max", "zai/glm-5.3"],
        "why": "kimi-k3 сильнее в глубоком поиске (BrowseComp 91.2, DeepSearchQA 95.0); галлюцинации 51% против 40% — паттерн строго требует источник/URL на каждое число (канон fleet-doctrine); glm-5.3 третий — провайдерный бэкап (лестница 03.10)",
    },
    "ops": {
        "models": ["custom/qwen3.8-max", "zai/glm-5.3", "custom/kimi-k3"],
        "why": "лестница 03.10: qwen3.8-max первый — доменная работа и строгий чистый вывод (канон Round-2 02.09, reasoning max); glm-5.3 второй — провайдерное разнообразие; kimi-k3 третий",
    },
    "review": {
        "models": ["zai/glm-5.3", "openai-codex/gpt-6.1-sol", "custom/qwen3.8-max"],
        "why": "glm-5.3 = qa-сит (решение владельца 23.09; dual verdict 03.09); sol второй — живой бэкап при стене zai (инцидент rate-limit 04.10); qwen3.8-max третий — независимый резерв; author_model исключается из списка (инвариант №2, R1)",
    },
    "strategic": {
        "models": ["openai-codex/gpt-6.1-sol", "openai-codex/gpt-6-astra"],
        "why": "owner-facing/портфель/protected: brain-рельса (канон fleet-doctrine Two-rail model) — sol решения, astra узкий пакет; дешёвая рельса не первой",
    },
    "vision": {
        "models": ["custom/qwen-vl-max", "openai-codex/gpt-6-luna"],
        "why": "qwen-vl-max — канон перцепции (PerceptionBench 63.5 против 58.5), без reasoning_effort (инвариант №3); luna (low) — массовые простые просмотры",
    },
}

# --- PATTERNS: на каждую модель «как брифовать / что требовать строго / страховка / анти-паттерн» ---
PATTERNS = {
    "kimi-k3": (
        "как брифовать: точное ТЗ, один deliverable, без параллельных веток.\n"
        "требовать строго: источники на каждый факт; числа только с URL; выдуманные данные запрещены.\n"
        "страховка: деструктивные файловые операции только после diff/backup.\n"
        "анти-паттерн: конфликтные инструкции по формату — при конфликте удаляет данные (0/3, A/B 02.09)."),
    "qwen3.8-max": (
        "как брифовать: жёсткий формат вывода (JSON/схема), поля перечислены по порядку.\n"
        "требовать строго: запрет уничтожения данных — при конфликте сохранить значение в восстановимой форме; краткость, без прозы после JSON.\n"
        "страховка: readback/валидация вывода по схеме.\n"
        "анти-паттерн: факты без проверки цитированием (галлюцинации 40%); «творческие» задания."),
    "glm-5.3": (
        "как брифовать: ревью по пунктам с номерами, каждый пункт — критерий.\n"
        "требовать строго: вердикт структурирован по пунктам PASS/FAIL с цитатами; FAIL → нумерованные дефекты, не чинить.\n"
        "страховка: на main/deploy — второй независимый вердикт (dual verdict 03.09).\n"
        "анти-паттерн: размытое «всё выглядит хорошо» без пунктов и evidence."),
    "gpt-6.1-sol": (
        "как брифовать: короткий ясный текст, только суть; финишная линия в каждой задаче.\n"
        "требовать строго: решение + обоснование в 3–5 предложениях; без «think hard» — глубина только через reasoning_effort.\n"
        "страховка: сверять поле model в usage — флагованный ответ тихо даунгрейдит модель.\n"
        "анти-паттерн: длинные многоуровневые брифы; смена правил mid-turn."),
    "gpt-6-astra": (
        "как брифовать: только узкий пакет — один вопрос/одно решение.\n"
        "требовать строго: ответ в формате пакета, без развернутых исследований.\n"
        "страховка: нужно глубокое исследование — передать классу research (kimi-k3).\n"
        "анти-паттерн: портфельные исследования и длинный анализ."),
    "qwen-vl-max": (
        "как брифовать: одно изображение на вопрос; вопрос конкретный (что прочитать/описать).\n"
        "требовать строго: без параметра reasoning_effort (инвариант №3); ответ в запрошенном формате.\n"
        "страховка: критичное распознавание — перепроверка второй моделью (gpt-6-luna).\n"
        "анти-паттерн: коллажи и несколько изображений в одном запросе; любая настройка effort."),
    "gpt-6-luna": (
        "как брифовать: массовые простые просмотры — пачка однотипных изображений, low effort.\n"
        "требовать строго: короткий единообразный ответ на каждый элемент.\n"
        "страховка: сложный/сомнительный кадр — эскалация на qwen-vl-max.\n"
        "анти-паттерн: детальный анализ одного изображения."),
}

RULES_SHA = hashlib.sha1(json.dumps({"ROUTES": ROUTES, "PATTERNS": PATTERNS}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:12]  # D2: отпечаток правил — sha1 канонического дампа, [:12]; детерминизм между прогонами

# --- Жёсткие правила: применяются до выбора; при коллизии побеждает старший номер (R3 > R2) ---
RULES = [
    ("R1", "task_type=review → author_model исключается из списка класса (инвариант №2: проверяющий на чужой модели)."),
    ("R2", "owner_facing=true или protected (main/deploy/publish в title/body) → класс strategic."),
    ("R3", "needs_vision=true → класс vision (способность выше тира: R3 перекрывает R2)."),
    ("R4", "prior_run_failed=true → следующий элемент списка (эскалация одним шагом вправо; на конце списка остаётся последний)."),
    ("R5", "спорный класс (нет маркеров) → устойчивый маппинг task_type→класс (research→research, ops→ops, review→review, code→code, code+файловые ключевые слова→data); неизвестный task_type → code."),
    ("R6", "кэш-дисциплина (инвариант №5, канон 8): повторная карта той же работы рекомендует ту же модель — роутер детерминирован; единственная причина смены — prior_run_failed (R4: шаг вправо с логом)."),
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
TASK_TYPE_CLASS = {"research": "research", "ops": "ops", "review": "review", "code": "code", "data": "data"}


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
    cls = TASK_TYPE_CLASS.get(tt)  # R5: устойчивый маппинг task_type→класс
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
            fired.append("W1"); notes.append("W1: все рельсы класса недоступны по --status — оставлен полный список (безопасная деградация)")
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
            "router_version": ROUTER_VERSION, "rules_sha": RULES_SHA, "input_echo": echo}  # D2: аудит-мета


CASES = [  # (имя, карта, ожидаемый класс, ожидаемая модель[, статус D1]) — по одному на правило + эскалация + спорный + три дельты v4
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
]


def selftest():
    print(f"model_router {VERSION} router {ROUTER_VERSION} — selftest: {len(CASES)} встроенных кейсов, 0 сети")
    ok = True
    all_models = {m.split("/")[-1] for r in ROUTES.values() for m in r["models"]}
    missing = sorted(all_models - set(PATTERNS))
    line = "PASS" if not missing else f"FAIL (нет паттерна: {missing})"
    print(f"{line}  структура: PATTERNS есть на каждую модель списков ROUTES")
    ok = ok and not missing
    for name, card, exp_cls, exp_model, *rest in CASES:
        r = classify(card, rest[0] if rest else None)
        good = r["class"] == exp_cls and r["model"] == exp_model and bool(r["pattern"])
        ok = ok and good
        tail = "" if good else f" (ожидалось {exp_cls}/{exp_model})"
        print(f"{'PASS' if good else 'FAIL'}  {name} → {r['class']}/{r['model']}{tail}")
    print(f"итог: {'ALL PASS' if ok else 'ЕСТЬ ПАДЕНИЯ'}")
    return 0 if ok else 1


def print_rules():
    print(f"rules_sha {RULES_SHA}")  # D2: отпечаток правил — первая строка вывода
    print(f"Политика автороутера «Рельсы v{VERSION}» — вывод --print-rules (источник правды: model_router.py)")
    print("\n== Классы и списки предпочтений (порядок = предпочтение; обоснование = число канона) ==")
    for name, r in ROUTES.items():
        print(f"- {name}: " + " → ".join(r["models"]))
        print(f"    обоснование: {r['why']}")
    print("\n== Жёсткие правила (применяются до выбора, по порядку) ==")
    for rid, text in RULES:
        print(f"- {rid}: {text}")
    print("\n== Эскалация ==")
    print("- Неудача/блок → шаг вправо по списку; на конце — остаётся последняя модель.")
    print("- Эскалация явная: пер-картовый пин с причиной + строка в ROUTING-LOG.md (фаза C); тихой подмены на ходу нет (инвариант №1).")
    print("\n== Паттерны общения на каждую модель (целиком — для вставки в спецификацию) ==")
    for m in sorted(PATTERNS):
        print(f"--- {m} ---")
        print(PATTERNS[m])
    print("\n== Инварианты (PROGRAM.md v2.2) ==")
    for inv in INVARIANTS:
        print(f"- {inv}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Автороутер «Рельсы v2.2»: задача → класс → модель → паттерн.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--card", metavar="FILE.JSON",
                   help="JSON карты: title, body, task_type, author_model, needs_vision, owner_facing, prior_run_failed")
    g.add_argument("--selftest", action="store_true", help="встроенные кейсы, таблица PASS/FAIL, exit 0/1")
    g.add_argument("--print-rules", action="store_true", help="человекочитаемая политика (те же данные); первая строка — rules_sha")
    ap.add_argument("--status", metavar="S.JSON", help="опционально с --card (D1): {\"<provider|модель>\": {\"available\": false}} — пропуск недоступной рельсы ДО выбора")
    args = ap.parse_args(argv)
    if args.status and not args.card: print("ошибка: --status используется только с --card", file=sys.stderr); return 2
    if args.selftest:
        return selftest()
    if args.print_rules:
        return print_rules()
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
