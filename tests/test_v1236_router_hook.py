"""v1.2.36 — SPEC v5: нативный автороутинг в pre-claim пути диспатча.

Уровни: (1) scripts/router_hook.py — selftest/бюджет строк/0 сети/режимы
off-shadow-enforce/degrade/status-skip; (2) src/fleet_policy/router_bridge.py
— флаг, shadow без мутаций, enforce-команды, деградации; (3) плагин —
flag-gated best-effort вызов внутри kanban_task_claimed.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "scripts" / "router_hook.py"
ROUTER = ROOT / "scripts" / "model_router.py"
PLUGIN = ROOT / "integrations" / "hermes" / "fleet-policy-plugin" / "__init__.py"
# Живой router v6.2 после t_8e388c6e (промоушен 09.10): репо-копия байт-в-байт;
# sha256 считается по LF-форме (см. _norm), CRLF-worktree live даёт тот же хэш.
ROUTER_LIVE_SHA = "10d4d59333e2cd57260601633a2ff52023fe296abe32c1835b4fafaf24b19607"
FORBIDDEN_IMPORTS = {
    "socket", "urllib", "requests", "http", "ftplib", "smtplib", "telnetlib",
    "subprocess", "ssl", "xmlrpc", "websocket", "asyncio",
}


def _norm(path: Path) -> bytes:
    """Байты с LF-нормализацией: Windows-checkout (autocrlf) == LF-эталон."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def hook():
    return _load_module("rh_v1236_test", HOOK)


@pytest.fixture(scope="module")
def router():
    return _load_module("mr_v1236_test", ROUTER)


@pytest.fixture()
def bridge():
    from fleet_policy import router_bridge

    yield router_bridge
    router_bridge._HOOK_CACHE.clear()
    router_bridge._BOARD_DB_CACHE.clear()


def _active(tmp_path, data, name="ROUTER_ACTIVE.json"):
    p = tmp_path / name
    p.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
    return p


CODE_CARD = {"task_id": "t_v1236", "title": "Реализовать парсер логов",
             "body": "модуль и тесты", "task_type": "code"}


# --- уровень 1: репо-копия model_router и бюджет/чистота hook ---------------


def test_repo_model_router_matches_live_bytes():
    assert hashlib.sha256(_norm(ROUTER)).hexdigest() == ROUTER_LIVE_SHA


def test_hook_line_budget_and_lf_identity():
    data = _norm(HOOK)
    assert data.count(b"\n") <= 220  # wc -l ≤ 220 (SPEC v5)


@pytest.mark.parametrize("path", [HOOK, ROUTER])
def test_zero_network_imports(path):
    tree = ast.parse(_norm(path).decode("utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    assert not (names & FORBIDDEN_IMPORTS), f"network/subprocess import in {path.name}"


def test_selftest_exit_zero_from_any_cwd(tmp_path):
    for cwd in (ROOT, tmp_path):
        proc = subprocess.run([sys.executable, str(HOOK), "--selftest"],
                              capture_output=True, text=True, cwd=str(cwd), timeout=120)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "ALL PASS" in proc.stdout
        assert proc.stdout.count("PASS") >= 7  # ≥6 кейсов SPEC + итог


def test_cli_card_contract(tmp_path, hook):
    active = _active(tmp_path, {"mode": "enforce", "classes": ["code"]})
    log = tmp_path / "ROUTING-LOG.md"
    card_file = tmp_path / "card.json"
    card_file.write_text(json.dumps(CODE_CARD), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(HOOK), "--card", str(card_file),
         "--active", str(active), "--log", str(log)],
        capture_output=True, text=True, cwd=str(tmp_path), timeout=60)
    assert proc.returncode == 0, proc.stderr
    decision = json.loads(proc.stdout)
    first = hook.model_router.ROUTES["code"]["models"][0]
    provider, model = first.split("/", 1)
    assert decision["action"] == "override"
    assert (decision["provider"], decision["model"]) == (provider, model)
    assert decision["rules_sha"] == hook.model_router.RULES_SHA
    assert log.read_text(encoding="utf-8").count("| t_v1236 |") == 1


# --- уровень 1: режимы SPEC v5 на decide() ----------------------------------


def test_mode_off_is_silent(tmp_path, hook):
    active = _active(tmp_path, {"mode": "off"})
    log = tmp_path / "ROUTING-LOG.md"
    d = hook.decide(CODE_CARD, active_path=str(active), log_path=str(log))
    assert d["action"] == "none"
    assert not log.exists()


def test_missing_or_corrupt_active_degrades_to_off(tmp_path, hook):
    log = tmp_path / "ROUTING-LOG.md"
    missing = hook.decide(CODE_CARD, active_path=str(tmp_path / "absent.json"), log_path=str(log))
    corrupt = hook.decide(CODE_CARD, active_path=str(_active(tmp_path, "{mode: broken,,")),
                          log_path=str(log))
    assert missing["action"] == "none" and corrupt["action"] == "none"
    assert not log.exists()


def test_shadow_logs_and_pins_nothing(tmp_path, hook):
    active = _active(tmp_path, {"mode": "shadow", "classes": ["code"]})
    log = tmp_path / "ROUTING-LOG.md"
    d = hook.decide(CODE_CARD, active_path=str(active), log_path=str(log))
    assert d["action"] == "log"  # даже для класса из списка: shadow не ставит модель
    assert d["logged"] is True
    row = log.read_text(encoding="utf-8")
    assert "| t_v1236 |" in row and "| code |" in row and "нет (shadow)" in row


def test_enforce_only_for_listed_classes(tmp_path, hook):
    log = tmp_path / "ROUTING-LOG.md"
    inside = _active(tmp_path, {"mode": "enforce", "classes": ["code"]}, "in.json")
    outside = _active(tmp_path, {"mode": "enforce", "classes": ["ops"]}, "out.json")
    d_in = hook.decide(CODE_CARD, active_path=str(inside), log_path=str(log))
    d_out = hook.decide(CODE_CARD, active_path=str(outside), log_path=str(log))
    first_model = hook.model_router.ROUTES["code"]["models"][0].split("/", 1)[1]
    assert d_in["action"] == "override" and d_in["model"] == first_model
    assert d_in["pattern"]  # паттерн выдаётся вместе с моделью
    assert d_out["action"] == "log"  # класс вне списка — как shadow


def test_missing_task_type_degrades_even_under_enforce(tmp_path, hook):
    active = _active(tmp_path, {"mode": "enforce", "classes": ["code", "ops"]})
    log = tmp_path / "ROUTING-LOG.md"
    d = hook.decide({"title": "Задача без маркера", "body": ""},
                    active_path=str(active), log_path=str(log))
    assert d["action"] == "log" and d["degrade"] is True
    assert d["model"] == "default" and d["provider"] is None
    assert "degrade" in log.read_text(encoding="utf-8")


def test_status_file_skips_rail_before_selection(tmp_path, hook):
    active = _active(tmp_path, {"mode": "enforce", "classes": ["code"]})
    status = _active(tmp_path, {"custom": {"available": False}}, "status.json")
    log = tmp_path / "ROUTING-LOG.md"
    d = hook.decide(CODE_CARD, active_path=str(active), log_path=str(log),
                    status_path=str(status))
    models = hook.model_router.ROUTES["code"]["models"]
    expected = next(m.split("/", 1)[1] for m in models if not m.startswith("custom/"))
    assert d["action"] == "override" and d["model"] == expected


def test_active_status_file_is_used_when_no_override(tmp_path, hook):
    active = _active(tmp_path, {"mode": "enforce", "classes": ["code"],
                                "status_file": str(_active(tmp_path, {"zai": {"available": False}}, "s2.json"))})
    d = hook.decide(CODE_CARD, active_path=str(active), log_path=str(tmp_path / "L.md"))
    models = hook.model_router.ROUTES["code"]["models"]
    expected = next(m.split("/", 1)[1] for m in models if not m.startswith("zai/"))
    # zai-рельса пропускается ДО выбора (status_file из active-файла, t_9d220da7:
    # проверка version-agnostic — v6.2 ставит zai/ первой рельсой класса code)
    assert d["model"] == expected


def test_log_write_failure_does_not_raise(tmp_path, hook):
    blocker = tmp_path / "blocker"
    blocker.write_text("file, not a dir", encoding="utf-8")
    active = _active(tmp_path, {"mode": "shadow", "classes": []})
    d = hook.decide(CODE_CARD, active_path=str(active),
                    log_path=str(blocker / "sub" / "ROUTING-LOG.md"))
    assert d["action"] == "log" and d["logged"] is False


# --- уровень 2: мост плагина -------------------------------------------------


def test_bridge_requires_explicit_flag(bridge, tmp_path):
    for cfg in (None, {}, {"router_hook": {}}, {"router_hook": {"enabled": False}},
                {"router_hook": {"enabled": "true"}}):
        assert bridge.router_step({}, "t_v1236", "", None, cfg) is None
    assert bridge.router_enabled({"router_hook": {"enabled": True}}) is True


def test_bridge_missing_hook_is_noop(bridge, tmp_path):
    cfg = {"router_hook": {"enabled": True, "script": str(tmp_path / "absent.py")}}
    assert bridge.router_step({}, "t_v1236", "", None, cfg) is None


class _SpyStore:
    def __init__(self, fail=False):
        self.events, self.fail = [], fail

    def record_event(self, event_id, correlation_id, task_id, kind, payload, significant=False):
        if self.fail:
            raise RuntimeError("store down")
        self.events.append((event_id, kind, payload))
        return True


def _cfg(tmp_path, active, **extra):
    cfg = {"router_hook": {"enabled": True, "script": str(HOOK),
                           "active_file": str(active), "log_file": str(tmp_path / "ROUTING-LOG.md")}}
    cfg["router_hook"].update(extra)
    return cfg


def _runner_fail(cmd, timeout):  # pragma: no cover - защитный spy
    raise AssertionError(f"CLI mutation in shadow: {cmd}")


def test_bridge_shadow_logs_without_mutation(bridge, tmp_path, monkeypatch):
    monkeypatch.setitem(bridge._BOARD_DB_CACHE, "fleet-ops", "")
    active = _active(tmp_path, {"mode": "shadow", "classes": ["code"]})
    store = _SpyStore()
    ctx = {"task_title": CODE_CARD["title"], "task_body": CODE_CARD["body"], "kanban_db": ""}
    d = bridge.router_step(ctx, "t_v1236", "fleet-ops", 11, _cfg(tmp_path, active),
                           store=store, task_type="code", runner=_runner_fail)
    assert d["action"] == "log" and d["logged"] is True
    assert (tmp_path / "ROUTING-LOG.md").read_text(encoding="utf-8").count("| t_v1236 |") == 1
    (event_id, kind, payload), = store.events
    assert kind == "router_hook" and event_id == "router:t_v1236:11"
    assert payload["mode"] == "shadow" and payload["applied"] is None


def test_bridge_enforce_sets_model_and_comment(bridge, tmp_path, monkeypatch):
    monkeypatch.setitem(bridge._BOARD_DB_CACHE, "fleet-ops", "")
    active = _active(tmp_path, {"mode": "enforce", "classes": ["code"]})
    calls = []

    class _Res:
        returncode = 0

    def runner(cmd, timeout):
        calls.append(list(cmd))
        return _Res()

    ctx = {"task_title": CODE_CARD["title"], "task_body": CODE_CARD["body"], "kanban_db": ""}
    d = bridge.router_step(ctx, "t_v1236", "fleet-ops", 12, _cfg(tmp_path, active),
                           store=_SpyStore(), task_type="code", runner=runner)
    hookmod = _load_module("rh_v1236_enf", HOOK)
    provider, model = hookmod.model_router.ROUTES["code"]["models"][0].split("/", 1)
    assert d["action"] == "override" and d["applied"] is True
    assert calls[0] == ["hermes", "kanban", "--board", "fleet-ops", "set-model",
                        "t_v1236", model, "--provider", provider]
    comment_cmd = calls[1]
    assert comment_cmd[:5] == ["hermes", "kanban", "--board", "fleet-ops", "comment"]
    body = comment_cmd[6]
    assert body.startswith(f"ROUTER {hookmod.model_router.ROUTER_VERSION}:") \
        and f"model={provider}/{model}" in body
    assert f"rules_sha={hookmod.model_router.RULES_SHA}" in body
    assert comment_cmd[-2:] == ["--author", "fleet-router"]


def test_bridge_pin_failure_skips_comment(bridge, tmp_path, monkeypatch):
    monkeypatch.setitem(bridge._BOARD_DB_CACHE, "fleet-ops", "")
    active = _active(tmp_path, {"mode": "enforce", "classes": ["code"]})
    calls = []

    class _Res:
        returncode = 1

    def runner(cmd, timeout):
        calls.append(list(cmd))
        return _Res()

    ctx = {"task_title": "x", "task_body": "y", "kanban_db": ""}
    d = bridge.router_step(ctx, "t_v1236", "fleet-ops", 13, _cfg(tmp_path, active),
                           task_type="code", runner=runner)
    assert d["applied"] is False and len(calls) == 1  # комментарий не пишется


def test_bridge_store_failure_is_tolerated(bridge, tmp_path, monkeypatch):
    monkeypatch.setitem(bridge._BOARD_DB_CACHE, "fleet-ops", "")
    active = _active(tmp_path, {"mode": "shadow", "classes": []})
    ctx = {"task_title": "x", "task_body": "y", "kanban_db": ""}
    d = bridge.router_step(ctx, "t_v1236", "fleet-ops", 14, _cfg(tmp_path, active),
                           store=_SpyStore(fail=True), task_type="code", runner=_runner_fail)
    assert d["action"] == "log"


def test_bridge_cli_env_strips_kanban_pins(bridge, monkeypatch):
    monkeypatch.setenv("HERMES_KANBAN_TASK", "t_foreign")
    monkeypatch.setenv("HERMES_KANBAN_DB", "C:/somewhere/kanban.db")
    env = bridge._cli_env()
    assert not any(k.startswith("HERMES_KANBAN_") for k in env)
    assert "PATH" in env


def test_card_payload_reads_pin_and_failure_from_board_db(bridge, tmp_path):
    db = tmp_path / "kanban.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE tasks (id TEXT, model_override TEXT, provider_override TEXT, "
                 "consecutive_failures INTEGER NOT NULL DEFAULT 0)")
    conn.execute("INSERT INTO tasks VALUES ('t_v1236', 'glm-5.3', 'zai', 2)")
    conn.commit()
    conn.close()
    ctx = {"task_title": "t", "body": "", "task_body": "b", "kanban_db": str(db)}
    card = bridge.card_payload(ctx, "t_v1236", "")
    assert card["pinned_model"] == "zai/glm-5.3"
    assert card["prior_run_failed"] is True
    assert "task_type" not in card  # без task_type — деградация на стороне hook'а


# --- уровень 3: плагин — flag-gated best-effort вызов в kanban_task_claimed ---


def test_plugin_claim_calls_router_step_best_effort(monkeypatch):
    module = _load_module("fp_plugin_v1236", PLUGIN)
    from fleet_policy import router_bridge

    seen = {}

    def spy(ctx, task_id, board, run_id, config, store=None, task_type=None):
        seen.update(ctx=ctx, task_id=task_id, board=board, run_id=run_id,
                    config=config, store=store, task_type=task_type)
        return {"action": "log"}

    monkeypatch.setattr(router_bridge, "router_step", spy)

    class _Runtime:
        config = {"projects": {}, "router_hook": {"enabled": True}}
        store = object()

        def task_type(self, ctx):
            return "code", None

    monkeypatch.setattr(module, "runtime", lambda: _Runtime())
    monkeypatch.setattr(module, "load_task_context",
                        lambda base, projects: {"task_title": "t", "task_body": "task_type: code"})
    module.kanban_task_claimed(task_id="t_v1236a", board="fleet-ops", assignee="tech", run_id=7)
    assert seen["task_id"] == "t_v1236a" and seen["board"] == "fleet-ops"
    assert seen["run_id"] == 7 and seen["task_type"] == "code"
    assert seen["store"] is _Runtime.store


def test_plugin_claim_survives_router_explosion(monkeypatch):
    module = _load_module("fp_plugin_v1236_boom", PLUGIN)
    from fleet_policy import router_bridge

    def boom(*args, **kwargs):
        raise RuntimeError("router on fire")

    monkeypatch.setattr(router_bridge, "router_step", boom)

    class _Runtime:
        config = {"projects": {}}
        store = object()

        def task_type(self, ctx):
            return "code", None  # без ошибки: deny-путь не срабатывает

    monkeypatch.setattr(module, "runtime", lambda: _Runtime())
    monkeypatch.setattr(module, "load_task_context", lambda base, projects: {})
    module.kanban_task_claimed(task_id="t_v1236b", board="fleet-ops", assignee="tech", run_id=8)
    # не бросил — claim не заблокирован (канон 7)


def test_plugin_source_keeps_call_flag_gated_and_guarded():
    src = _norm(PLUGIN).decode("utf-8")
    fn = src.split("def kanban_task_claimed(", 1)[1].split("\ndef ", 1)[0]
    assert "from fleet_policy.router_bridge import router_step" in fn
    assert "router_step(ctx, task_id" in fn
    assert "except Exception" in fn  # best-effort: никогда не блокирует claim
    assert fn.index("router_step(ctx") < fn.index("if not error:")  # до deny-возврата


# --- уровень 2b: hot-reload таблицы правил (t_9d220da7) ------------------------

HOOK_STUB = """
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import model_router


def decide(card, **kwargs):
    return {"rules_sha": model_router.RULES_SHA,
            "router_version": model_router.ROUTER_VERSION}
"""

MR_V1 = 'ROUTER_VERSION = "v-test-1"\nRULES_SHA = "aaa111aaa111"\n'
MR_V2 = 'ROUTER_VERSION = "v-test-2"\nRULES_SHA = "bbb222bbb222"\n'


def _mk_hook_dir(tmp_path):
    d = tmp_path / "scripts"
    d.mkdir()
    (d / "router_hook.py").write_text(HOOK_STUB, encoding="utf-8", newline="\n")
    (d / "model_router.py").write_text(MR_V1, encoding="utf-8", newline="\n")
    return d


def _bump(path, offset=5.0):
    st = path.stat()
    os.utime(path, (st.st_atime, st.st_mtime + offset))


@pytest.fixture()
def _router_module_isolation():
    # hook exec'ы делают sys.path.insert(HERE) и кладут model_router в
    # sys.modules — снимок/восстановление, чтобы тесты не текли друг в друга.
    saved = sys.modules.pop("model_router", None)
    saved_path = list(sys.path)
    try:
        yield
    finally:
        sys.modules.pop("model_router", None)
        if saved is not None:
            sys.modules["model_router"] = saved
        sys.path[:] = saved_path


def test_load_hook_reloads_on_model_router_swap(bridge, tmp_path, _router_module_isolation):
    """Замена ТОЛЬКО model_router.py между двумя decide() в ОДНОМ процессе
    меняет rules_sha решения без рестарта (t_9d220da7)."""
    d = _mk_hook_dir(tmp_path)
    hook_path = d / "router_hook.py"
    first = bridge.load_hook(hook_path)
    assert first.decide({"task_id": "t"})["rules_sha"] == "aaa111aaa111"

    (d / "model_router.py").write_text(MR_V2, encoding="utf-8", newline="\n")
    _bump(d / "model_router.py")  # hook-файл и его mtime не тронуты

    second = bridge.load_hook(hook_path)
    assert second.decide({"task_id": "t"})["rules_sha"] == "bbb222bbb222"


def test_load_hook_cache_hit_when_deps_unchanged(bridge, tmp_path, _router_module_isolation):
    d = _mk_hook_dir(tmp_path)
    first = bridge.load_hook(d / "router_hook.py")
    assert bridge.load_hook(d / "router_hook.py") is first


def test_load_hook_keeps_foreign_model_router(bridge, tmp_path, _router_module_isolation):
    foreign_dir = tmp_path / "foreign"
    foreign_dir.mkdir()
    (foreign_dir / "model_router.py").write_text(
        'ROUTER_VERSION = "v-foreign"\nRULES_SHA = "fff000fff000"\n',
        encoding="utf-8", newline="\n")
    spec = importlib.util.spec_from_file_location("model_router", foreign_dir / "model_router.py")
    foreign = importlib.util.module_from_spec(spec)
    sys.modules["model_router"] = foreign
    spec.loader.exec_module(foreign)

    d = _mk_hook_dir(tmp_path)
    assert bridge.load_hook(d / "router_hook.py") is not None
    assert sys.modules["model_router"] is foreign  # чужой каталог не вытесняется
