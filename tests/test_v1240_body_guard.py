"""v1.2.40 (t_f0599145) — pre-claim валидация тела карты (body guard).

Уровни: (1) src/fleet_policy/body_guard.py — чистота модуля (0 сети/0
subprocess-импортов), --selftest ≥6 кейсов из любого cwd, CLI exit-коды;
(2) validate() — матрица правил: маркер task_type строго в первой строке
(BOM/регистр/мусорное значение), секции deliverable/acceptance/bans/anchor
(EN+RU синонимы, markdown, скобочный квалификатор — FP-регрессия t_22153d76),
строгость по created_by (owner advisory / agent strict / неизвестен = strict),
режимы off|warn|enforce (мусор → warn); (3) guard_step — флаг enabled только
явный true, событие policy-store kind=body_guard, отказ store терпим,
created_by из ctx важнее board-DB, fallback read-only запросом board-DB;
(4) плагин — kanban_task_claimed: deny card_structurally_broken (BLOCK →
record_event significant + проекция блока), advisory для owner-карт
(комментарий без блока), при error старого task_type-пути стража не
дублирует проекцию, взрыв стражи не ломает claim (канон 7).
"""
from __future__ import annotations

import ast
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "src" / "fleet_policy" / "body_guard.py"
PLUGIN = ROOT / "integrations" / "hermes" / "fleet-policy-plugin" / "__init__.py"
FORBIDDEN_IMPORTS = {
    "socket", "urllib", "requests", "http", "ftplib", "smtplib", "telnetlib",
    "subprocess", "ssl", "xmlrpc", "websocket", "asyncio",
}

from fleet_policy import body_guard  # noqa: E402  (pytest pythonpath=src)

GOOD_BODY = "\n".join([
    "task_type: code",
    "Починить парсер.",
    "DELIVERABLE: PR + тесты",
    "ACCEPTANCE: suite green",
    "BANS: policy-denial -> partial+stop",
    "ANCHOR: QA-потомок",
])
MARKERLESS_BODY = "Починить парсер.\nDELIVERABLE: x\nACCEPTANCE: y\nBANS: z\nANCHOR: w"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules.setdefault(name, module)
    spec.loader.exec_module(module)
    return module


def _run(args, cwd, tmp_path, extra_env=None):
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONHASHSEED": "0"}
    if extra_env:
        env.update(extra_env)
    return subprocess.run([sys.executable, str(GUARD), *args], cwd=str(cwd),
                          env=env, capture_output=True, text=True, timeout=120)


def _board_db(tmp_path: Path, task_id: str = "t_bg1", created_by: str | None = "tech",
              with_column: bool = True) -> Path:
    """Мини-копия канбан-БД для fallback-теста read_created_by."""
    db = tmp_path / "kanban.db"
    conn = sqlite3.connect(db)
    if with_column:
        conn.execute("CREATE TABLE tasks (id TEXT PRIMARY KEY, created_by TEXT, board TEXT)")
        conn.execute("INSERT INTO tasks (id, created_by, board) VALUES (?,?,?)",
                     (task_id, created_by, "b"))
    else:
        conn.execute("CREATE TABLE tasks (id TEXT PRIMARY KEY, board TEXT)")
        conn.execute("INSERT INTO tasks (id, board) VALUES (?,?)", (task_id, "b"))
    conn.commit()
    conn.close()
    return db


class _StoreSpy:
    def __init__(self, boom: bool = False):
        self.events: list[tuple] = []
        self.boom = boom

    def record_event(self, *args):
        if self.boom:
            raise RuntimeError("store down")
        self.events.append(args)
        return True


# --- уровень 1: чистота модуля, selftest, CLI --------------------------------

class TestBodyGuardModule:
    def test_zero_forbidden_imports(self):
        tree = ast.parse(GUARD.read_text(encoding="utf-8"))
        used: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                used.update((alias.name or "").split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                used.add(node.module.split(".")[0])
        assert not (used & FORBIDDEN_IMPORTS)
        # канбан-БД читается штатным sqlite3 read-only, сеть исключена
        assert "sqlite3" in used

    @pytest.mark.parametrize("cwd_name", ["root", "tmp"])
    def test_selftest_exit_zero_from_any_cwd(self, cwd_name, tmp_path):
        cwd = ROOT if cwd_name == "root" else tmp_path
        result = _run(["--selftest"], cwd, tmp_path)
        assert result.returncode == 0, result.stderr[-2000:]
        assert result.stdout.count("PASS") >= 7  # ≥6 кейсов + итог ALL PASS
        assert "ALL PASS" in result.stdout

    def test_cli_body_file_pass_and_defect_exit_codes(self, tmp_path):
        good = tmp_path / "good.txt"
        good.write_text(GOOD_BODY, encoding="utf-8")
        r_ok = _run(["--body-file", str(good), "--created-by", "tech",
                     "--mode", "enforce", "--json"], tmp_path, tmp_path)
        assert r_ok.returncode == 0, r_ok.stderr[-1000:]
        payload = json.loads(r_ok.stdout)
        assert payload["decision"] == "pass" and payload["mode"] == "enforce"

        bad = tmp_path / "bad.txt"
        bad.write_text("свободный текст без маркера", encoding="utf-8")
        r_bad = _run(["--body-file", str(bad), "--created-by", "tech",
                      "--mode", "enforce"], tmp_path, tmp_path)
        assert r_bad.returncode == 1
        assert "missing_task_type_marker" in r_bad.stdout
        assert "body_sections_missing" in r_bad.stdout

        r_missing = _run(["--body-file", str(tmp_path / "nope.txt")], tmp_path, tmp_path)
        assert r_missing.returncode == 2


# --- уровень 2: матрица validate() --------------------------------------------

class TestValidate:
    def test_good_agent_card_passes(self):
        r = body_guard.validate(GOOD_BODY, created_by="tech", mode="enforce")
        assert r["decision"] == "pass" and r["defects"] == [] and r["owner_card"] is False

    def test_marker_deep_in_body_denied_with_precise_reason(self):
        body = "Починить парсер\n\ntask_type: code\nDELIVERABLE: x\nACCEPTANCE: y\nBANS: z\nANCHOR: w"
        r = body_guard.validate(body, created_by="tech", mode="enforce")
        assert r["decision"] == "deny"
        assert r["codes"] == ["missing_task_type_marker"]
        # точная причина цитирует фактическую первую строку
        assert "Починить парсер" in r["reason"]
        assert r["remediation"]["who"] == "company"
        assert "CARD_BODY_TEMPLATE" in r["remediation"]["how"]

    def test_invalid_marker_value_denied(self):
        r = body_guard.validate("task_type: build\nDELIVERABLE: x\nACCEPTANCE: y\n"
                                "BANS: z\nANCHOR: w", created_by="tech", mode="enforce")
        assert r["decision"] == "deny" and r["codes"] == ["invalid_task_type_value"]
        assert "build" in r["reason"]

    def test_bom_and_case_tolerated(self):
        r = body_guard.validate("\ufeffTASK_TYPE: Code\nDELIVERABLE: x\nACCEPTANCE: y\n"
                                "BANS: z\nANCHOR: w", created_by="tech", mode="enforce")
        assert r["decision"] == "pass"

    def test_agent_missing_sections_denied(self):
        r = body_guard.validate("task_type: ops\nDELIVERABLE: x\nACCEPTANCE: y",
                                created_by="company", mode="enforce")
        assert r["decision"] == "deny" and r["codes"] == ["body_sections_missing"]
        assert "BANS" in r["reason"] and "ANCHOR" in r["reason"]
        assert all(sev == "BLOCK" for sev, _c, _d in r["defects"])

    def test_owner_missing_sections_is_advisory(self):
        r = body_guard.validate("task_type: research\nсвободный текст владельца",
                                created_by="user", mode="enforce")
        assert r["decision"] == "warn" and r["owner_card"] is True
        assert all(sev == "WARN" for sev, _c, _d in r["defects"])
        assert "advisory" in r["reason"]

    def test_unknown_created_by_is_strict_fail_closed(self):
        body = "task_type: review\nDELIVERABLE: x\nACCEPTANCE: y\nBANS: z"
        for created_by in (None, "", "  "):
            r = body_guard.validate(body, created_by=created_by, mode="enforce")
            assert r["decision"] == "deny", created_by
            assert r["owner_card"] is False

    def test_ru_synonyms_md_headings_and_paren_qualifier_pass(self):
        body = ("task_type: code\n## Поставка\nмодуль\n- Критерии приёмки: тесты\n"
                "> ЗАПРЕТЫ: нет\nANCHOR (проверен company readback 22:0x): ok")
        assert body_guard.validate(body, created_by="qa", mode="enforce")["decision"] == "pass"
        # FP-регрессия t_22153d76: скобочный квалификатор между именем и ':'
        body2 = ("task_type: code\nDELIVERABLE: отчёт\nAcceptance criteria (v2): suite\n"
                 "BANS:\nЭскалация/якорь: QA")
        assert body_guard.validate(body2, created_by="tech", mode="enforce")["decision"] == "pass"

    def test_warn_mode_downgrades_everything(self):
        r = body_guard.validate("свободный текст", created_by="tech", mode="warn")
        assert r["decision"] == "warn" and r["mode"] == "warn"
        assert {"missing_task_type_marker", "body_sections_missing"} == set(r["codes"])
        assert all(sev == "WARN" for sev, _c, _d in r["defects"])

    def test_off_mode_is_silent(self):
        r = body_guard.validate("", created_by="tech", mode="off")
        assert r["decision"] == "pass" and r["defects"] == []

    @pytest.mark.parametrize("garbage", ["ENFORCE!", "strict", "1", ""])
    def test_garbage_mode_fails_safe_to_warn(self, garbage):
        assert body_guard.resolve_mode(garbage) == "warn"
        r = body_guard.validate("task_type: code\nDELIVERABLE: x", created_by="tech",
                                mode=garbage)
        # fail-safe: строгость не включается на мусоре — секционный дефект WARN
        assert r["mode"] == "warn"
        assert all(sev == "WARN" for sev, _c, _d in r["defects"])

    def test_empty_body_denied(self):
        r = body_guard.validate("", created_by="worker", mode="enforce")
        assert r["decision"] == "deny"
        assert set(r["codes"]) == {"missing_task_type_marker", "body_sections_missing"}

    def test_owner_set_config_shapes(self):
        assert body_guard.owner_set({"body_guard": {"owner_created_by": ["user", "Max"]}}) == {"user", "max"}
        assert body_guard.owner_set({"body_guard": {"owner_created_by": "user"}}) == {"user"}
        # мусор/пусто → дефолт
        assert body_guard.owner_set({"body_guard": {"owner_created_by": []}}) == {"user"}
        assert body_guard.owner_set({"body_guard": {"owner_created_by": 42}}) == {"user"}
        assert body_guard.owner_set({}) == {"user"}
        assert body_guard.is_owner("USER", {"user"}) and not body_guard.is_owner(None, {"user"})


# --- уровень 3: guard_step ------------------------------------------------------

class TestGuardStep:
    CONFIG = {"projects": {}, "body_guard": {"enabled": True, "mode": "enforce",
                                             "owner_created_by": ["user"]}}

    def _ctx(self, body=GOOD_BODY, created_by="tech", **extra):
        ctx = {"task_id": "t_bg1", "board": "b", "project": "fleet-ops",
               "task_body": body, "comments": [], "kanban_db": None}
        if created_by is not None:
            ctx["created_by"] = created_by
        ctx.update(extra)
        return ctx

    @pytest.mark.parametrize("config", [
        None, {}, {"body_guard": {}}, {"body_guard": {"enabled": False, "mode": "enforce"}},
        {"body_guard": {"enabled": "true", "mode": "enforce"}},
        {"body_guard": None},
    ])
    def test_flag_must_be_explicit_true(self, config):
        assert body_guard.guard_step(self._ctx(), "t_bg1", "b", 7, config) is None

    def test_mode_off_short_circuits_without_store_event(self):
        store = _StoreSpy()
        cfg = {"body_guard": {"enabled": True, "mode": "off"}}
        r = body_guard.guard_step(self._ctx(body="мусор"), "t_bg1", "b", 7, cfg, store=store)
        assert r["decision"] == "pass" and r["mode"] == "off"
        assert store.events == []

    def test_store_event_kind_body_guard(self):
        store = _StoreSpy()
        r = body_guard.guard_step(self._ctx(body=MARKERLESS_BODY), "t_bg1", "b", 42,
                                  self.CONFIG, store=store)
        assert r["decision"] == "deny"
        assert len(store.events) == 1
        event_id, correlation, task_id, kind, payload, significant = store.events[0]
        assert event_id == "body-guard:t_bg1:42"
        assert correlation == "42" and task_id == "t_bg1"
        assert kind == "body_guard" and significant is False
        assert payload["decision"] == "deny"
        assert payload["codes"] == ["missing_task_type_marker"]
        assert payload["guard_version"] == body_guard.GUARD_VERSION
        assert payload["owner_card"] is False

    def test_store_failure_tolerated(self):
        r = body_guard.guard_step(self._ctx(), "t_bg1", "b", 7, self.CONFIG,
                                  store=_StoreSpy(boom=True))
        assert r["decision"] == "pass"  # наблюдаемость не ломает валидацию

    def test_ctx_created_by_wins_over_db(self, tmp_path):
        db = _board_db(tmp_path, created_by="tech")
        ctx = self._ctx(body="task_type: research\nсвободный текст", created_by="user",
                        kanban_db=str(db))
        r = body_guard.guard_step(ctx, "t_bg1", "b", 7, self.CONFIG)
        assert r["owner_card"] is True and r["decision"] == "warn"
        assert r["created_by"] == "user"

    def test_db_fallback_owner_and_agent(self, tmp_path):
        owner_db = _board_db(tmp_path, created_by="user")
        ctx = {"task_id": "t_bg1", "board": "b", "task_body": "task_type: research\nтекст",
               "kanban_db": str(owner_db)}
        r = body_guard.guard_step(ctx, "t_bg1", "b", 7, self.CONFIG)
        assert r["created_by"] == "user" and r["owner_card"] is True and r["decision"] == "warn"

        (tmp_path / "agent").mkdir(exist_ok=True)
        agent_db = _board_db(tmp_path / "agent", created_by="tech")
        ctx2 = {"task_id": "t_bg1", "board": "b",
                "task_body": "task_type: research\nтекст", "kanban_db": str(agent_db)}
        r2 = body_guard.guard_step(ctx2, "t_bg1", "b", 7, self.CONFIG)
        assert r2["created_by"] == "tech" and r2["owner_card"] is False
        assert r2["decision"] == "deny"

    def test_unreadable_db_fails_closed_strict(self, tmp_path):
        # нет колонки created_by → SELECT падает → None → agent-семантика
        db = _board_db(tmp_path, with_column=False)
        assert body_guard.read_created_by({"kanban_db": str(db)}, "b", "t_bg1") is None
        # нет файла БД
        assert body_guard.read_created_by({"kanban_db": str(tmp_path / "no.db")}, "b", "t") is None
        # нет ни kanban_db, ни board
        assert body_guard.read_created_by({}, "", "t_bg1") is None


# --- уровень 4: интеграция плагина (kanban_task_claimed) ------------------------

class _Runtime:
    def __init__(self, config, store, task_type=("code", None)):
        self.config = config
        self.store = store
        self._tt = task_type

    def task_type(self, ctx):
        return self._tt

    def budget_snapshot(self, ctx, tt):
        return {}


_PLUGIN = None


def _plugin():
    global _PLUGIN
    if _PLUGIN is None:
        _PLUGIN = _load_module("_plugin_v1240", PLUGIN)
    return _PLUGIN


def _claim(monkeypatch, tmp_path, ctx, config, tt, guard_boom=False):
    """Прогон kanban_task_claimed со шпионами; возвращает (calls, projects,
    advisories, store)."""
    mod = _plugin()
    store = _StoreSpy()
    monkeypatch.setattr(mod, "runtime", lambda: _Runtime(config, store, tt))
    monkeypatch.setattr(mod, "load_task_context", lambda info, projects=None: dict(ctx))
    projects: list = []
    advisories: list = []
    monkeypatch.setattr(mod, "_project", lambda payload: projects.append(payload))
    monkeypatch.setattr(mod, "_project_advisory", lambda payload: advisories.append(payload))
    if guard_boom:
        def _boom(*args, **kwargs):
            raise RuntimeError("guard exploded")
        monkeypatch.setattr(body_guard, "guard_step", _boom)
    calls = []
    if not guard_boom:
        real = body_guard.guard_step
        monkeypatch.setattr(body_guard, "guard_step",
                            lambda *a, **k: (calls.append((a, k)), real(*a, **k))[1])
    assert mod.kanban_task_claimed("t_bg1", "b", "tech", 7) is None
    return calls, projects, advisories, store


GUARD_CFG = {"projects": {}, "body_guard": {"enabled": True, "mode": "enforce",
                                            "owner_created_by": ["user"]}}


class TestPluginClaimWiring:
    def _ctx(self, body, created_by="tech"):
        return {"task_id": "t_bg1", "board": "b", "project": "fleet-ops",
                "task_body": body, "comments": [], "kanban_db": None,
                "created_by": created_by, "task_status": "running",
                "current_run_id": 7}

    def test_deny_blocks_with_card_structurally_broken(self, monkeypatch, tmp_path):
        calls, projects, advisories, store = _claim(
            monkeypatch, tmp_path, self._ctx(MARKERLESS_BODY), GUARD_CFG, ("code", None))
        assert len(calls) == 1 and len(projects) == 1 and advisories == []
        payload = projects[0]
        assert payload["decision"] == "deny"
        assert payload["rule_id"] == "card_structurally_broken"
        assert payload["pattern_category"] == "card_body"
        assert "missing_task_type_marker" in payload["reason"]
        assert payload["remediation"]["who"] == "company"
        assert payload["action"] == "worker_launch" and payload["task_id"] == "t_bg1"
        kinds = [(e[3], e[5]) for e in store.events]
        assert ("body_guard", False) in kinds
        assert ("card_structurally_broken", True) in kinds

    def test_owner_card_warn_projects_advisory_without_block(self, monkeypatch, tmp_path):
        body = "task_type: research\nсвободный текст владельца"
        calls, projects, advisories, store = _claim(
            monkeypatch, tmp_path, self._ctx(body, created_by="user"), GUARD_CFG,
            ("research", None))
        assert projects == [] and len(advisories) == 1
        payload = advisories[0]
        assert payload["decision"] == "allow"
        assert payload["rule_id"] == "body_sections_advisory"
        assert "body_sections_missing" in payload["reason"]
        assert ("body_guard_advisory", True) in [(e[3], e[5]) for e in store.events]

    def test_good_card_passes_silently(self, monkeypatch, tmp_path):
        calls, projects, advisories, store = _claim(
            monkeypatch, tmp_path, self._ctx(GOOD_BODY), GUARD_CFG, ("code", None))
        assert len(calls) == 1 and projects == [] and advisories == []
        assert [(e[3], e[5]) for e in store.events] == [("body_guard", False)]

    def test_legacy_task_type_error_path_unchanged_and_guard_skipped(
            self, monkeypatch, tmp_path):
        # marker отсутствует ВЕЗДЕ → старый deny missing_or_unknown_task_type;
        # стража тела не вызывается и не дублирует проекцию
        calls, projects, advisories, store = _claim(
            monkeypatch, tmp_path, self._ctx(MARKERLESS_BODY), GUARD_CFG,
            (None, "missing task_type marker"))
        assert calls == [] and advisories == []
        assert len(projects) == 1
        assert projects[0]["rule_id"] == "missing_or_unknown_task_type"

    def test_guard_disabled_config_is_noop(self, monkeypatch, tmp_path):
        calls, projects, advisories, store = _claim(
            monkeypatch, tmp_path, self._ctx(MARKERLESS_BODY), {"projects": {}},
            ("code", None))
        # guard_step вызывается (флаг-гейтинг внутри него), но возвращает None:
        # ни событий, ни проекций
        assert len(calls) == 1 and projects == [] and advisories == []
        assert store.events == []

    def test_guard_explosion_never_breaks_claim(self, monkeypatch, tmp_path):
        _calls, projects, advisories, _store = _claim(
            monkeypatch, tmp_path, self._ctx(MARKERLESS_BODY), GUARD_CFG, ("code", None),
            guard_boom=True)
        assert projects == [] and advisories == []  # claim выжил, проекций нет

    def test_claim_source_keeps_guard_after_error_branch(self):
        src = PLUGIN.read_text(encoding="utf-8")
        assert "def _body_guard(" in src and "def _project_advisory(" in src
        fn = src.split("def kanban_task_claimed(", 1)[1].split("\ndef ", 1)[0]
        assert "_body_guard(ctx, task_id, board, assignee, run_id, task_type)" in fn
        # стража — только в ветке успешного task_type (нет двойных проекций)
        assert fn.index("if not error:") < fn.index("_body_guard(ctx")
        # контракт v1.2.36 сохранён: router_step остаётся до error-ветки
        assert fn.index("router_step(ctx") < fn.index("if not error:")
