"""body_guard.py — v1.2.40: pre-claim валидация тела канбан-карты (t_f0599145).

Стража вызывается плагином fleet-policy из ``kanban_task_claimed`` — той же
официальной pre-claim точки, что пре-диспатч проверка task_type и router_hook
(v1.2.36) — ONLY за конфиг-флагом ``body_guard.enabled``.

Правила (директива владельца 04.10 «корректные, нативные, полноценные карты»;
семантика и regex — порт profiles/company/scripts/card_readiness.py rails v3,
t_20d62426 — механизм переиспользуется, а не изобретается; live-скрипт не
трогается, дрейф сверяет QA-сэмплинг):

  1. Первая строка body — точный маркер ``task_type: <research|code|review|ops>``
     (BOM-терпимо, регистронезависимо). Маркер глубже первой строки карту НЕ
     спасает. Дефекты: missing_task_type_marker / invalid_task_type_value
     (BLOCK, точная причина цитирует первую строку).
  2. Секции DELIVERABLE / ACCEPTANCE / BANS / ANCHOR (EN+RU синонимы,
     markdown-заголовки, скобочные квалификаторы — FP-регрессия t_22153d76).
     Для карт, созданных агентами (created_by != owner; created_by неизвестен/
     пуст = агент, fail-closed), отсутствие секций → BLOCK
     body_sections_missing; для owner-карт (created_by ∈ owner_created_by) →
     WARN (advisory, не блокирует).

Режимы (конфиг ``body_guard.mode``):
  enforce — BLOCK → deny card_structurally_broken (плагин пишет комментарий и
            блокирует карту штатным claim-deny механизмом; deny_triage_bot
            структурно сломанные карты не авто-ресумит), WARN → advisory-
            комментарий без блока;
  warn    — все дефекты advisory (полный откат поведения без передеплоя);
  off     — стража не вызывается (как enabled: false).
Неизвестное/мусорное значение mode → warn (fail-safe: не ужесточать на мусоре,
конвенция card_readiness v3). Поставочный режим — enforce (решение company:
эта карта — активация strict-секций для agent-карт).

Контракт best-effort (канон 7): валидация НИКОГДА не блокирует сам claim —
решение возвращает плагину, проекцию (комментарий/блок) делает плагин; любое
исключение деградирует молча. stdlib only, 0 сети.

CLI (QA/отладка, read-only):
  python body_guard.py --selftest                       # ≥6 кейсов, любой cwd, exit 0
  python body_guard.py --body-file b.txt --created-by tech --mode enforce --json
Exit code: 0 = pass, 1 = найдены дефекты, 2 = usage-ошибка.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

GUARD_VERSION = "1.2.40"
TASK_TYPES = ("research", "code", "review", "ops")
MODES = ("off", "warn", "enforce")
DEFAULT_OWNER_CREATED_BY = ("user",)
TEMPLATE_DOC = "docs/CARD_BODY_TEMPLATE.md"

# Первая строка body: точный маркер 'task_type: <type>' (BOM-терпимость +
# IGNORECASE + значение \S+ — семантика card_readiness.first_line_marker
# rails v3; неканоническое значение → invalid_task_type_value).
FIRST_LINE_RX = re.compile(r"^\uFEFF?\s*task_type\s*:\s*(\S+)\s*$", re.IGNORECASE)


def _section_rx(alts):
    """Секция = имя в начале строки (допуская markdown-префикс #/>/*/+/-), далее
    опционально составное имя через '/' («Эскалация/якорь:»), опциональный
    квалификатор в скобках («Acceptance criteria (v2):», «ANCHOR (проверен …):» —
    реальный FP t_22153d76), далее разделитель [:=—–-] с любым содержимым, включая
    пустое («BANS:»), ИЛИ чистая heading-строка ('## NAME').

    Порт 1:1 из card_readiness.py rails v3 (t_20d62426) — единая семантика
    шаблона тела во флоте; не расходиться с live-скриптом."""
    return re.compile(
        r"(?im)^\s*(?:[#>*+\-]+\s*)?(?:" + alts + r")"
        r"(?:\s*/\s*(?:" + alts + r"))*"
        r"(?:\s*\([^()\n]*\))?"
        r"\s*(?:[:=—–-].*|\s*$)")


BODY_SECTION_PATTERNS = {
    "deliverable": _section_rx(r"deliverables?|артефакт(?:ы)?|поставка|результат"),
    "acceptance": _section_rx(
        r"acceptance(?:\s+criteria)?|критерии\s+при[её]мки|при[её]мка"
        r"|definition\s+of\s+done|done[-\s]критерии"),
    "bans": _section_rx(r"bans?|запреты?|запрещено|guardrails?"),
    "anchor": _section_rx(r"anchor|якорь|эскалация"),
}
SECTION_HINTS = {
    "deliverable": "DELIVERABLE: <конкретный артефакт, расположение, sha256/receipt>",
    "acceptance": "ACCEPTANCE: <проверяемые критерии готовности: тесты/проверки>",
    "bans": "BANS: <что запрещено; минимум: policy-denial -> partial+stop>",
    "anchor": "ANCHOR: <кто и где проверяет результат (QA-якорь/эскалация)>",
}


# --- конфиг -------------------------------------------------------------

def guard_config(config):
    bg = (config or {}).get("body_guard")
    return bg if isinstance(bg, dict) else {}


def guard_enabled(config):
    """Мастер-флаг интеграции: только явный true (отсутствие/мусор → off,
    конвенция router_bridge.router_enabled)."""
    return guard_config(config).get("enabled") is True


def resolve_mode(mode=None):
    """off|warn|enforce; неизвестное значение → warn (fail-safe: не ужесточать
    без решения, конвенция card_readiness.resolve_body_template_mode)."""
    m = str(mode or "").strip().lower()
    return m if m in MODES else "warn"


def owner_set(config=None):
    """Множество created_by, считающихся владельцем (owner-карты → advisory).
    Список/строка из конфига; мусор/пусто → дефолт ('user',)."""
    raw = guard_config(config).get("owner_created_by")
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, (list, tuple)) or not raw:
        raw = DEFAULT_OWNER_CREATED_BY
    owners = {str(x).strip().lower() for x in raw if str(x).strip()}
    return owners or set(DEFAULT_OWNER_CREATED_BY)


def is_owner(created_by, owners=None):
    """created_by неизвестен/пуст → НЕ owner (fail-closed: строгая проверка)."""
    if owners is None:
        owners = DEFAULT_OWNER_CREATED_BY
    owners = {str(o).strip().lower() for o in owners}
    cb = str(created_by or "").strip().lower()
    return bool(cb) and cb in owners


# --- валидация ------------------------------------------------------------

def check_first_line(body):
    """Правило 1: маркер task_type строго в первой строке body."""
    lines = str(body or "").splitlines()
    first = lines[0].strip() if lines else ""
    match = FIRST_LINE_RX.match(first)
    if match:
        value = match.group(1).lower()
        if value in TASK_TYPES:
            return []
        return [("BLOCK", "invalid_task_type_value",
                 f"первая строка body 'task_type: {match.group(1)}': значение "
                 f"'{value}' вне множества {list(TASK_TYPES)} — исправь на "
                 f"каноническое (первая строка, точный маркер)")]
    if not first:
        return [("BLOCK", "missing_task_type_marker",
                 "body пустое: первая строка должна быть ровно маркером "
                 "'task_type: <research|code|review|ops>'")]
    quoted = first[:120] + ("…" if len(first) > 120 else "")
    return [("BLOCK", "missing_task_type_marker",
             f"первая строка body '{quoted}' не является маркером task_type — "
             f"первая строка должна быть ровно 'task_type: "
             f"<research|code|review|ops>' (маркер глубже первой строки не "
             f"считается)")]


def check_sections(body, owner=False, mode="enforce"):
    """Правило 2: секции deliverable/acceptance/bans/anchor. agent-карты —
    BLOCK в enforce; owner-карты — всегда WARN (advisory)."""
    missing = [name for name, rx in BODY_SECTION_PATTERNS.items()
               if not rx.search(str(body or ""))]
    if not missing:
        return []
    names = ", ".join(m.upper() for m in missing)
    hints = " | ".join(SECTION_HINTS[m] for m in missing)
    sev = "BLOCK" if (mode == "enforce" and not owner) else "WARN"
    detail = (f"в теле нет секций: {names}. Добавь строки (считаются и "
              f"эквивалентные заголовки/синонимы): {hints}")
    if owner:
        detail += " (owner-карта: advisory — не блокирует)"
    return [(sev, "body_sections_missing", detail)]


def validate(body, created_by=None, owners=None, mode=None):
    """Карта → решение стража. Не бросает исключений на валидных типах.

    Возвращает dict: {guard_version, mode, decision: deny|warn|pass, defects,
    codes, owner_card, reason, remediation}."""
    resolved = resolve_mode(mode)
    owner = is_owner(created_by, owners)
    defects = []
    if resolved != "off":
        defects.extend(check_first_line(body))
        defects.extend(check_sections(body, owner=owner, mode=resolved))
        if resolved == "warn":
            # Полный откат строгости: любой дефект — advisory.
            defects = [("WARN", code, detail) for (_sev, code, detail) in defects]
    codes = sorted({code for (_sev, code, _d) in defects})
    if any(sev == "BLOCK" for sev, _c, _d in defects):
        decision = "deny"
    elif defects:
        decision = "warn"
    else:
        decision = "pass"
    reason = "; ".join(f"{code}: {detail}" for _sev, code, detail in defects)
    remediation = {}
    if decision != "pass":
        remediation = {
            "how": ("исправь тело карты по шаблону " + TEMPLATE_DOC +
                    ": первая строка 'task_type: <research|code|review|ops>'"
                    " + секции DELIVERABLE/ACCEPTANCE/BANS/ANCHOR; затем"
                    " unblock (структурный дефект не авто-ресумится)"),
            "who": "company",
        }
    return {
        "guard_version": GUARD_VERSION, "mode": resolved, "decision": decision,
        "defects": [list(d) for d in defects], "codes": codes,
        "owner_card": owner, "reason": reason, "remediation": remediation,
    }


# --- pre-claim шаг плагина --------------------------------------------------

def read_created_by(ctx, board, task_id):
    """created_by карты: read-only запрос канбан-БД (штатный паттерн
    router_bridge.card_payload). Нет факта → None (fail-closed: agent-карта)."""
    db = str((ctx or {}).get("kanban_db") or "")
    if not db and board:
        try:
            from .kanban_context import board_db

            db = str(board_db(str(board)) or "")
        except Exception:
            db = ""
    if not db or not Path(db).is_file():
        return None
    try:
        conn = sqlite3.connect(f"file:{Path(db).as_posix()}?mode=ro", uri=True,
                               timeout=2)
        try:
            row = conn.execute("SELECT created_by FROM tasks WHERE id = ?",
                               (task_id,)).fetchone()
        finally:
            conn.close()
    except sqlite3.Error:
        return None
    if row and row[0] is not None:
        return str(row[0])
    return None


def guard_step(ctx, task_id, board, run_id, config, store=None):
    """Один шаг pre-claim валидации. None = флаг выключен/mode off (стража не
    вызывается). Исключения не глотает только вызывающий плагин (канон 7:
    claim не блокируется); сам шаг best-effort на всех внутренних путях."""
    if not guard_enabled(config):
        return None
    gc = guard_config(config)
    mode = resolve_mode(gc.get("mode"))
    if mode == "off":
        return {"guard_version": GUARD_VERSION, "mode": "off",
                "decision": "pass", "defects": [], "codes": [],
                "owner_card": False, "reason": "", "remediation": {}}
    ctx = ctx if isinstance(ctx, dict) else {}
    created_by = ctx.get("created_by")
    if created_by is None:
        created_by = read_created_by(ctx, board, task_id)
    result = validate(str(ctx.get("task_body") or ""), created_by=created_by,
                      owners=owner_set(gc), mode=mode)
    result["created_by"] = created_by
    if store is not None:
        try:
            store.record_event(
                f"body-guard:{task_id}:{run_id or 'claim'}",
                str(run_id or task_id), task_id, "body_guard",
                {"board": str(board or ""), "mode": result["mode"],
                 "decision": result["decision"], "codes": result["codes"],
                 "owner_card": result["owner_card"],
                 "guard_version": GUARD_VERSION},
                False,
            )
        except Exception:
            pass  # наблюдаемость не должна ломать диспатч
    return result


# --- selftest (≥6 кейсов, temp-каталоги не нужны — валидация чистая) --------

GOOD_AGENT_BODY = "\n".join([
    "task_type: code",
    "Сделать парсер логов.",
    "DELIVERABLE: модуль + тесты, PR в trunk",
    "ACCEPTANCE: suite green, selftest ≥6",
    "BANS: не трогать live; policy-denial -> partial+stop",
    "ANCHOR: QA-потомок после merge",
])

SELFTEST_CASES = [
    # (имя, body, created_by, mode, ожидаемое decision, ожидаемые codes)
    ("good-agent-card-passes", GOOD_AGENT_BODY, "tech", "enforce", "pass", set()),
    ("marker-deep-in-body-denied", "Задача\n\ntask_type: code\nDELIVERABLE: x\n"
     "ACCEPTANCE: y\nBANS: z\nANCHOR: w",
     "tech", "enforce", "deny", {"missing_task_type_marker"}),
    ("invalid-marker-value-denied", "task_type: build\nDELIVERABLE: x\n"
     "ACCEPTANCE: y\nBANS: z\nANCHOR: w",
     "tech", "enforce", "deny", {"invalid_task_type_value"}),
    ("bom-and-case-tolerated", "\ufeffTASK_TYPE: CODE\nрезультат: x\nприёмка: y\n"
     "запреты: z\nякорь: w", "tech", "enforce", "pass", set()),
    ("agent-missing-sections-denied", "task_type: ops\nDELIVERABLE: x\nACCEPTANCE: y",
     "company", "enforce", "deny", {"body_sections_missing"}),
    ("owner-missing-sections-warned", "task_type: research\nчто-то свободное",
     "user", "enforce", "warn", {"body_sections_missing"}),
    ("unknown-created-by-is-strict", "task_type: review\nDELIVERABLE: x\nACCEPTANCE: y\n"
     "BANS: z", None, "enforce", "deny", {"body_sections_missing"}),
    ("ru-synonyms-and-md-headings-pass", "task_type: code\n## Поставка\nмодуль\n"
     "- Критерии приёмки: тесты\n> ЗАПРЕТЫ: нет\n### Эскалация/якорь:",
     "qa", "enforce", "pass", set()),
    ("paren-qualifier-fp-regression", "task_type: code\nDELIVERABLE: отчёт\n"
     "Acceptance criteria (v2): suite\nBANS:\nANCHOR (проверен company readback 22:0x):",
     "tech", "enforce", "pass", set()),
    ("warn-mode-downgrades-marker-block", "свободный текст без маркера",
     "tech", "warn", "warn", {"missing_task_type_marker", "body_sections_missing"}),
    ("off-mode-is-silent", "что угодно", "tech", "off", "pass", set()),
    ("garbage-mode-fails-safe-to-warn", "task_type: code\nDELIVERABLE: x",
     "tech", "ENFORCE!", "warn", {"body_sections_missing"}),
    ("empty-body-denied", "", "worker", "enforce", "deny",
     {"missing_task_type_marker", "body_sections_missing"}),
]


def selftest():
    """Прогон SELFTEST_CASES; PASS-строка на кейс + итог ALL PASS. exit 0."""
    failures = 0
    for index, (name, body, created_by, mode, want_decision, want_codes) in enumerate(
            SELFTEST_CASES, start=1):
        result = validate(body, created_by=created_by, mode=mode)
        got_codes = set(result["codes"])
        ok = result["decision"] == want_decision and got_codes == want_codes
        if ok:
            print(f"PASS {index} {name}")
        else:
            failures += 1
            print(f"FAIL {index} {name}: decision={result['decision']} "
                  f"codes={sorted(got_codes)} want={want_decision}/{sorted(want_codes)}")
    if failures:
        print(f"SELFTEST FAILED: {failures} case(s)")
        return 1
    print(f"ALL PASS ({len(SELFTEST_CASES)} cases)")
    return 0


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows UTF-8
    ap = argparse.ArgumentParser(description="fleet-policy body guard (v1.2.40)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--body-file", help="файл с телом карты (read-only проверка)")
    ap.add_argument("--created-by", default=None)
    ap.add_argument("--mode", default=None, help="off|warn|enforce (default: warn fail-safe)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    if not args.body_file:
        ap.error("--selftest или --body-file обязательны")
        return 2
    try:
        body = Path(args.body_file).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"cannot read body file: {exc}", file=sys.stderr)
        return 2
    result = validate(body, created_by=args.created_by, mode=args.mode)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"decision={result['decision']} mode={result['mode']} "
              f"codes={','.join(result['codes']) or '-'}")
        for sev, code, detail in result["defects"]:
            print(f"  [{sev}] {code}: {detail}")
    return 0 if result["decision"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
