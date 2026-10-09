#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""router_hook.py — нативный hook автороутинга для пути диспатча (SPEC v5, v1.2.36).

Место — profiles/company/scripts/, рядом с model_router.py (единый источник правил).
Вызывается из плагина fleet-policy в pre-claim точке (kanban_task_claimed) ONLY за
флагом router_hook.enabled; company — вручную через --card. stdlib, 0 сети.
Режимы — ROUTER_ACTIVE.json рядом (нет файла/битый → off, канон 7):
  {"mode": "off|shadow|enforce", "classes": ["ops"], "status_file": null, "log_file": null}
  off — выход пустой, действий нет (откат = одна эта строка); shadow — строка в
  ROUTING-LOG.md, модель НЕ ставит; enforce — model+provider+pattern (action=override)
  только для классов из "classes", класс вне списка — как shadow.
Деградация (канон 7): task_type вне {research,code,review,ops} → рекомендация
«default: профильный дефолт» + строка лога degrade; override невозможен.
Доступность (канон 7): status_file {"<provider|модель>": {"available": false}} —
пропуск рельсы ДО выбора (D1 model_router); нет/битый — все доступны. Файл статусов
генерирует script-only cron; hook сам команд не вызывает.
CLI:
  python router_hook.py --card card.json [--active A.json] [--log L.md] [--status S.json]
  python router_hook.py --selftest   # ≥6 кейсов в temp-каталогах, любой cwd, exit 0
"""
import argparse, json, os, sys, tempfile  # noqa: E401 — стиль card_readiness.py; stdlib, 0 сети
from datetime import datetime
from pathlib import Path

HOOK_VERSION = "v5"
FLEET_TASK_TYPES = ("research", "code", "review", "ops")
HERE = Path(__file__).resolve().parent
# Приоритет пути лога: --log → log_file из ROUTER_ACTIVE.json → HERMES_ROUTING_LOG →
# дефолт раскладки флота (стиль констант model_router.ROUTING_DOC):
DEFAULT_LOG = Path("C:/Users/max/Desktop/all/ventures/docs/fleet-ops/model-routing-20261003/ROUTING-LOG.md")

if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # noqa: E701 — Windows UTF-8
if str(HERE) not in sys.path: sys.path.insert(0, str(HERE))  # noqa: E701
import model_router  # noqa: E402 — тот же каталог; правила/паттерны только из него


def load_active(path):
    """ROUTER_ACTIVE.json → нормализованный dict; любой сбой → off (канон 7)."""
    try:
        data = json.loads(Path(str(path)).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = None
    if not isinstance(data, dict) or data.get("mode") not in ("off", "shadow", "enforce"):
        return {"mode": "off", "classes": [], "status_file": None, "log_file": None, "degraded": True}
    classes = data.get("classes")
    return {"mode": data["mode"], "status_file": data.get("status_file"),
            "classes": [str(c) for c in classes] if isinstance(classes, list) else [],
            "log_file": data.get("log_file"), "degraded": False}


def load_status(path):
    """Статус доступности (формат D1): dict или None (нет/битый → все доступны)."""
    if not path:
        return None
    try:
        data = json.loads(Path(str(path)).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) and data else None


def _log_path(active, override=None):
    for cand in (override, active.get("log_file"), os.environ.get("HERMES_ROUTING_LOG")):
        if cand:
            return Path(str(cand))
    return DEFAULT_LOG


def _write_log(card, rec, decision, path):
    """Одна строка на диспатч по контракту ROUTING-LOG.md (append-only таблица —
    ручные строки company сохраняются). Сбой записи не ломает диспатч: False."""
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        model, pinned = decision["model_display"], str(card.get("pinned_model") or "")
        matched = "—" if not pinned else ("да" if pinned in (model, str(rec.get("model") or "")) else "нет")
        issued = "да (enforce)" if decision["action"] == "override" else f"нет ({decision['mode']})"
        why = decision["mode"] + ("; degrade" if decision["degrade"] else "") + f"; {rec.get('reason') or ''}"
        row = (f"| {now} | {card.get('task_id') or '—'} | {rec.get('class') or 'degrade'} "
               f"| {model} | {pinned or '—'} | {matched} | {issued} | {why[:220]} |")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(row + "\n")
        return True
    except OSError:
        return False


def _degrade_rec(reason):
    return {"class": None, "model": "default", "provider": None, "pattern": None,
            "reason": reason, "rules_fired": ["degrade"],
            "router_version": model_router.ROUTER_VERSION, "rules_sha": model_router.RULES_SHA}


def decide(card, active_path=None, log_path=None, status_path=None):
    """Карта (dict) → решение {mode, action: none|log|override, ...}. Не бросает:
    любой сбой деградирует безопасно (канон 7) и не останавливает диспатч."""
    card = dict(card) if isinstance(card, dict) else {}
    active = load_active(active_path or (HERE / "ROUTER_ACTIVE.json"))
    if active["mode"] == "off":
        return {"mode": "off", "action": "none", "hook_version": HOOK_VERSION}
    status = load_status(status_path or active.get("status_file"))
    tt = str(card.get("task_type") or "").strip().lower()
    degrade = tt not in FLEET_TASK_TYPES
    if degrade:
        rec = _degrade_rec("degrade: нет task_type → профильный дефолт (канон 7)")
    else:
        routed = dict(card)
        if card.get("protected"):
            routed["owner_facing"] = True  # R2: явный protected равен owner_facing
        try:
            rec = model_router.classify(routed, status)
        except Exception as exc:  # сбой классификатора → деградация, не остановка
            degrade = True
            rec = _degrade_rec(f"degrade: исключение классификатора {type(exc).__name__}")
    enforce = (active["mode"] == "enforce" and not degrade
               and rec.get("class") in active["classes"])
    decision = {
        "mode": active["mode"], "action": "override" if enforce else "log",
        "degrade": degrade, "class": rec.get("class"), "model": rec.get("model"),
        "provider": rec.get("provider"), "pattern": rec.get("pattern"),
        "model_display": ("default (профильный дефолт)" if degrade
                          else f"{rec.get('provider')}/{rec.get('model')}"),
        "rules_sha": rec.get("rules_sha"), "router_version": rec.get("router_version"),
        "hook_version": HOOK_VERSION, "reason": rec.get("reason"),
        "rules_fired": rec.get("rules_fired")}
    decision["logged"] = _write_log(card, rec, decision, _log_path(active, log_path))
    return decision


def _case(tmp, idx, name, card, active, expect, status=None):
    d = Path(tmp) / f"case{idx}"
    d.mkdir(parents=True, exist_ok=True)
    apath = d / "ROUTER_ACTIVE.json"
    apath.write_text(active if isinstance(active, str) else json.dumps(active), encoding="utf-8")
    spath = None
    if status is not None:
        spath = d / "status.json"
        spath.write_text(json.dumps(status), encoding="utf-8")
    lpath = d / "ROUTING-LOG.md"
    r = decide(card, active_path=str(apath), log_path=str(lpath),
               status_path=str(spath) if spath else None)
    ok = all(r.get(k) == v for k, v in expect.items() if not k.startswith("_"))
    text = lpath.read_text(encoding="utf-8") if lpath.exists() else ""
    if "_log" in expect:
        ok = ok and expect["_log"] in text
    if "_nolog" in expect:
        ok = ok and not lpath.exists()
    print(f"{'PASS' if ok else 'FAIL'}  {name} → action={r.get('action')} "
          f"class={r.get('class')} model={r.get('model')}")
    return ok


def selftest():
    short = lambda full: full.split("/", 1)[1]  # noqa: E731
    code_models = model_router.ROUTES["code"]["models"]
    first = short(code_models[0])
    non_custom = [short(m) for m in code_models if not m.startswith("custom/")]
    card = {"task_id": "t_selftest", "title": "Реализовать парсер логов",
            "body": "модуль и тесты", "task_type": "code"}
    print(f"router_hook {HOOK_VERSION} (model_router {model_router.ROUTER_VERSION}, "
          f"rules_sha {model_router.RULES_SHA}) — selftest, 0 сети")
    ok = True
    with tempfile.TemporaryDirectory(prefix="router_hook_st_") as tmp:
        cases = [
            ("off: выход пустой, действий нет", card, {"mode": "off"},
             {"action": "none", "_nolog": True}, None),
            ("shadow: строка лога, модель не ставится", card, {"mode": "shadow", "classes": []},
             {"action": "log", "_log": "t_selftest"}, None),
            ("enforce: класс в списке → override", card, {"mode": "enforce", "classes": ["code"]},
             {"action": "override", "model": first}, None),
            ("enforce: класс вне списка → как shadow", card, {"mode": "enforce", "classes": ["ops"]},
             {"action": "log"}, None),
            ("нет task_type → degrade (даже в enforce)", {"title": "x", "body": ""},
             {"mode": "enforce", "classes": ["code"]},
             {"action": "log", "degrade": True, "model": "default", "_log": "degrade"}, None),
            ("битый ROUTER_ACTIVE.json → off", card, "{mode: broken,,",
             {"action": "none", "_nolog": True}, None),
        ]
        if non_custom:
            cases.insert(5, ("status-skip: провайдер custom недоступен", card,
                             {"mode": "enforce", "classes": ["code"]},
                             {"action": "override", "model": non_custom[0]},
                             {"custom": {"available": False}}))
        for i, (name, c, a, e, s) in enumerate(cases, 1):
            ok &= _case(tmp, i, name, c, a, e, status=s)
    print(f"итог: {'ALL PASS' if ok else 'ЕСТЬ ПАДЕНИЯ'}")
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Нативный hook автороутинга (SPEC v5): карта → класс → модель → паттерн.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--card", metavar="FILE|-", help="JSON карты: title, body, task_type, protected, "
                   "owner_facing, prior_run_failed, author_model[, task_id, pinned_model]")
    g.add_argument("--selftest", action="store_true", help="≥6 кейсов во временных каталогах, exit 0/1")
    ap.add_argument("--active", metavar="A.JSON", help="путь ROUTER_ACTIVE.json (дефолт — рядом с hook)")
    ap.add_argument("--log", metavar="L.MD", help="путь ROUTING-LOG.md (перекрывает log_file)")
    ap.add_argument("--status", metavar="S.JSON", help="статус доступности (перекрывает status_file)")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    try:
        raw = sys.stdin.read() if args.card == "-" else Path(args.card).read_text(encoding="utf-8")
        card = json.loads(raw)
    except (OSError, ValueError) as exc:
        print(f"ошибка: --card не прочитан: {exc}", file=sys.stderr)
        return 2
    if not isinstance(card, dict):
        print("ошибка: карта должна быть JSON-объектом", file=sys.stderr)
        return 2
    print(json.dumps(decide(card, active_path=args.active, log_path=args.log,
                            status_path=args.status), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
