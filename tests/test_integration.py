from __future__ import annotations

import json
import sqlite3
import subprocess

from fleet_policy.kanban_context import load_task_context
from fleet_policy.projector import HermesProjector
from fleet_policy.storage import PolicyStore


def make_kanban(path):
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE tasks(id TEXT PRIMARY KEY,title TEXT,body TEXT,assignee TEXT,status TEXT,started_at INTEGER,max_retries INTEGER,skills TEXT,current_run_id INTEGER);
        CREATE TABLE task_comments(id INTEGER PRIMARY KEY,task_id TEXT,body TEXT);
        """
    )
    connection.execute("INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?)", ("t1", "title", "body", "tech", "running", 1, 2, json.dumps(["rr-project"]), 7))
    connection.execute("INSERT INTO task_comments VALUES(1,'t1','task_type: code')")
    connection.commit()
    connection.close()


def test_context_reads_supported_task_fields(tmp_path):
    db = tmp_path / "kanban.db"
    make_kanban(db)
    ctx = load_task_context(
        {"task_id": "t1", "board": "rr-team", "profile": "tech"},
        {"rr-team": {"project": "recruiter-radar"}},
        {"HERMES_KANBAN_DB": str(db), "HERMES_KANBAN_TASK": "t1", "HERMES_KANBAN_BOARD": "rr-team"},
    )
    assert ctx["comments"] == ["task_type: code"]
    assert ctx["skills"] == ["rr-project"]
    assert ctx["project"] == "recruiter-radar"
    assert ctx["worker"] is True


def test_rr_guidance_does_not_apply_to_other_project(monkeypatch):
    import importlib.util
    from pathlib import Path
    module_path = Path(__file__).parents[1] / "integrations" / "hermes" / "fleet-policy-plugin" / "__init__.py"
    spec = importlib.util.spec_from_file_location("fleet_policy_plugin_test", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setenv("HERMES_KANBAN_BOARD", "venture-lab")
    assert module.rr_guidance({}) == ""
    monkeypatch.setenv("HERMES_KANBAN_BOARD", "rr-team")
    assert "Recruiter Radar" in module.rr_guidance({})


def test_projector_uses_real_cli_syntax_and_exactly_once_outbox(tmp_path):
    calls = []

    def runner(command, timeout):
        calls.append(list(command))
        return subprocess.CompletedProcess(command, 0, "ok", "")

    projector = HermesProjector(runner)
    result = projector.comment_and_block("rr-team", "t1", "evidence", block=True)
    assert result == {"block": 0}
    assert len(calls) == 1
    assert calls[0][:5] == ["hermes", "kanban", "--board", "rr-team", "block"]

    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    store.record_event("e1", "c1", "t1", "approval", {"decision": "approval_required"}, True)
    assert projector.drain_company(store) == 1
    assert projector.drain_company(store) == 0
    chat = calls[-1]
    assert chat[:4] == ["hermes", "-p", "company", "chat"]


def test_failed_company_notification_remains_pending(tmp_path):
    def runner(command, timeout):
        return subprocess.CompletedProcess(command, 1, "", "offline")

    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    store.record_event("e1", "c1", "t1", "deny", {"decision": "deny"}, True)
    assert HermesProjector(runner).drain_company(store) == 0
    assert len(store.pending_notifications()) == 1


def test_task_id_resolution_prefers_kanban_env_over_session_id(monkeypatch):
    import importlib.util
    from pathlib import Path
    module_path = Path(__file__).parents[1] / "integrations" / "hermes" / "fleet-policy-plugin" / "__init__.py"
    spec = importlib.util.spec_from_file_location("fleet_policy_plugin_resolve", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setenv("HERMES_KANBAN_TASK", "t_deadbeef")
    # Hermes hook kwargs carry the session-scoped id, not the board task.
    assert module._resolve_task_id({"task_id": "20260829_182523_93318d"}) == "t_deadbeef"
    monkeypatch.delenv("HERMES_KANBAN_TASK")
    assert module._resolve_task_id({"task_id": "20260829_182523_93318d"}) is None
    assert module._resolve_task_id({"task_id": "t_cafe1234"}) == "t_cafe1234"


def test_projection_never_auto_drains_company_notifications(tmp_path, monkeypatch):
    import importlib.util
    from pathlib import Path
    module_path = Path(__file__).parents[1] / "integrations" / "hermes" / "fleet-policy-plugin" / "__init__.py"
    spec = importlib.util.spec_from_file_location("fleet_policy_plugin_nospam", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    drained = {"count": 0}
    monkeypatch.setattr(module._PROJECTOR, "comment_and_block", lambda *a, **k: {"block": 0})
    monkeypatch.setattr(module._PROJECTOR, "drain_company", lambda *a, **k: drained.__setitem__("count", drained["count"] + 1))
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    runtime = module.runtime()
    monkeypatch.setattr(runtime, "store", store)
    monkeypatch.setattr(module, "_RUNTIME", runtime)

    # Three consecutive significant blocks must never auto-drain company.
    for n in range(3):
        store.record_event(f"sig-{n}", "c", "t_x", "policy_decision",
                           {"decision": "deny", "rule_id": f"r{n}", "task_id": "t_x"}, True)
        module._project({"task_id": "t_x", "rule_id": f"r{n}", "project": "rr-team"})
    assert drained["count"] == 0
    assert len(store.pending_notifications()) == 3


def test_failed_projection_releases_idempotency_claim(tmp_path, monkeypatch):
    import importlib.util
    from pathlib import Path
    module_path = Path(__file__).parents[1] / "integrations" / "hermes" / "fleet-policy-plugin" / "__init__.py"
    spec = importlib.util.spec_from_file_location("fleet_policy_plugin_retry_projection", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    runtime = module.runtime()
    monkeypatch.setattr(runtime, "store", store)
    monkeypatch.setattr(module, "_RUNTIME", runtime)
    monkeypatch.setattr(module._PROJECTOR, "comment_and_block", lambda *a, **k: {"block": 1})
    payload = {"task_id": "t_retry", "rule_id": "approval", "action": "terminal",
               "target": "deploy", "args_hash": "abc", "board": "rr-team"}
    module._project(payload)
    # Failed delivery released the claim; a later retry can claim again.
    assert runtime.claim_projection(payload) is True
