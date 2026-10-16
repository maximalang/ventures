"""v1.2.50 — the deny callback must never hold a worker's tool call open.

Incident 2026-10-16 (board fleet-ops, 11:36-12:48): every card of that window
lacked its ``task_type`` marker, so ``pre_tool_call`` denied on *every* tool
call and ran its card projection — a nested ``hermes kanban block``, ~8s of
process start on this host — synchronously in front of it. The hook's 20s bound
then expired (``TimeoutExpired 20.10s`` on skills_list / kanban_block /
kanban_comment / memory), the worker crash-looped three times and the
dispatcher stalled 54 ticks.

These tests are fixtures only: a synthetic board DB, a tmp policy store and a
stubbed CLI. No live profile, board, gateway or ``hermes`` invocation.
"""
from __future__ import annotations

import importlib.util
import json
import sqlite3
import subprocess
import time
from pathlib import Path

from fleet_policy.projector import HermesProjector, ProjectionExecutor
from fleet_policy.storage import PolicyStore

PLUGIN = Path(__file__).parents[1] / "integrations" / "hermes" / "fleet-policy-plugin" / "__init__.py"
MARKER_LESS = "marker-less card body: no task_type line here"
TIMEOUT_RULES = "missing_or_unknown_task_type"

# The columns the plugin's read model resolves task context from.
SCHEMA = """
CREATE TABLE tasks (
    id TEXT PRIMARY KEY, title TEXT, body TEXT, assignee TEXT, status TEXT,
    started_at REAL, max_retries INTEGER, skills TEXT, current_run_id TEXT
);
CREATE TABLE task_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, author TEXT, body TEXT
);
"""


def _load_plugin(name: str):
    spec = importlib.util.spec_from_file_location(name, PLUGIN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _board_db(tmp_path: Path, *, task_id: str, run_id: str) -> Path:
    path = tmp_path / "kanban.db"
    connection = sqlite3.connect(path)
    try:
        connection.executescript(SCHEMA)
        connection.execute(
            "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?)",
            (task_id, "marker-less card", MARKER_LESS, "tech", "running", 1.0, 2,
             json.dumps([]), run_id),
        )
        connection.commit()
    finally:
        connection.close()
    return path


def _wire(module, tmp_path, monkeypatch, *, task_id: str = "t_nomarker", run_id: str = "run-1"):
    """Point one freshly loaded plugin at a marker-less card and a tmp store."""
    db = _board_db(tmp_path, task_id=task_id, run_id=run_id)
    monkeypatch.setenv("HERMES_KANBAN_DB", str(db))
    monkeypatch.setenv("HERMES_KANBAN_TASK", task_id)
    monkeypatch.setenv("HERMES_KANBAN_BOARD", "fleet-ops")
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    runtime = module.runtime()
    monkeypatch.setattr(runtime, "store", store)
    monkeypatch.setattr(module, "_RUNTIME", runtime)
    return runtime, store


def _count(store: PolicyStore, kind: str) -> int:
    with store.connect() as connection:
        return int(connection.execute("SELECT COUNT(*) FROM events WHERE kind=?", (kind,)).fetchone()[0])


def test_deny_stays_bounded_and_projects_once_per_run(tmp_path, monkeypatch):
    module = _load_plugin("fp_plugin_bounded_callback")
    _runtime, store = _wire(module, tmp_path, monkeypatch)
    calls: list[str] = []

    def wedged(board: str, task_id: str, message: str, *, block: bool = True) -> dict[str, int]:
        calls.append(task_id)
        time.sleep(4.0)  # a CLI that cannot finish inside the callback budget
        return {"block": 0}

    monkeypatch.setattr(module._PROJECTOR, "comment_and_block", wedged)

    started = time.monotonic()
    decisions = [module.pre_tool_call("skills_list", {}) for _ in range(5)]
    elapsed = time.monotonic() - started

    assert [item["action"] for item in decisions] == ["block"] * 5
    assert all(TIMEOUT_RULES in item["message"] for item in decisions)
    # Acceptance: deny -> the denied tool call returns in well under 2s ...
    assert elapsed < 2.0, f"denied tool calls took {elapsed:.2f}s"
    # ... and the card is projected exactly once per run, not once per tool call.
    assert len(calls) == 1
    assert _count(store, "projection_claim") == 1
    module._PROJECTIONS.join(timeout=10)
    assert _count(store, "projection_failed") == 0


def test_projection_timeout_never_escapes_the_callback(tmp_path, monkeypatch):
    module = _load_plugin("fp_plugin_timeout_survival")
    _runtime, store = _wire(module, tmp_path, monkeypatch)
    calls: list[str] = []

    def exploding(board: str, task_id: str, message: str, *, block: bool = True) -> dict[str, int]:
        calls.append(task_id)
        raise subprocess.TimeoutExpired(
            cmd=["hermes", "kanban", "block"], timeout=HermesProjector.BLOCK_TIMEOUT_SECONDS
        )

    monkeypatch.setattr(module._PROJECTOR, "comment_and_block", exploding)

    started = time.monotonic()
    for _ in range(3):
        decision = module.pre_tool_call("kanban_block", {"task_id": "t_nomarker", "reason": "probe"})
        assert decision["action"] == "block"
    elapsed = time.monotonic() - started
    assert elapsed < 2.0, f"a timed-out projection leaked into the callback ({elapsed:.2f}s)"

    # The refusal survives; the failed delivery is audited once and not replayed.
    module._PROJECTIONS.join(timeout=10)
    assert calls == ["t_nomarker"]
    assert _count(store, "projection_claim") == 1
    assert _count(store, "projection_failed") == 1


def test_failed_projection_keeps_claim_and_audits_without_replay(tmp_path, monkeypatch):
    module = _load_plugin("fp_plugin_failed_projection")
    runtime, store = _wire(module, tmp_path, monkeypatch)
    calls: list[str] = []
    monkeypatch.setattr(
        module._PROJECTOR, "comment_and_block",
        lambda board, task_id, message, *, block: calls.append(task_id) or {"block": 1},
    )
    payload = {"task_id": "t_nomarker", "rule_id": TIMEOUT_RULES,
               "board": "fleet-ops", "run_key": "run-1"}

    module._project(payload)
    module._project(dict(payload))  # a second deny in the same run must not replay the CLI
    module._PROJECTIONS.join(timeout=10)

    assert calls == ["t_nomarker"]
    assert _count(store, "projection_claim") == 1
    assert _count(store, "projection_failed") == 1
    # The claim is KEPT: only a new run may retry the delivery.
    assert runtime.claim_projection(payload) is False
    assert runtime.claim_projection({**payload, "run_key": "run-2"}) is True


def test_fast_projection_lands_inside_the_callback(tmp_path, monkeypatch):
    module = _load_plugin("fp_plugin_fast_path")
    _runtime, store = _wire(module, tmp_path, monkeypatch)
    calls: list[tuple[str, str, bool]] = []
    monkeypatch.setattr(
        module._PROJECTOR, "comment_and_block",
        lambda board, task_id, message, *, block: calls.append((board, task_id, block)) or {"block": 0},
    )

    module._project({"task_id": "t_nomarker", "rule_id": TIMEOUT_RULES,
                     "board": "fleet-ops", "run_key": "run-1"})

    # The fast path stays synchronous, so a healthy CLI still parks the card
    # before the callback returns — asynchrony must not cost the card move.
    assert calls == [("fleet-ops", "t_nomarker", True)]
    assert _count(store, "projection_failed") == 0


def test_broken_claim_never_raises_into_the_callback(tmp_path, monkeypatch):
    module = _load_plugin("fp_plugin_broken_claim")
    runtime, _store = _wire(module, tmp_path, monkeypatch)

    def broken(payload: dict) -> bool:
        raise sqlite3.OperationalError("policy store unavailable")

    monkeypatch.setattr(runtime, "claim_projection", broken)
    module._project({"task_id": "t_nomarker", "rule_id": TIMEOUT_RULES, "board": "fleet-ops"})
    assert module.pre_tool_call("skills_list", {})["action"] == "block"


def test_projection_executor_isolates_delivery_errors():
    executor = ProjectionExecutor(fast_path_seconds=1.0)
    seen: list[str] = []

    def exploding() -> None:
        seen.append("ran")
        raise RuntimeError("wedged projection")

    assert executor.submit(exploding) is not None
    executor.join(timeout=5)
    assert seen == ["ran"]


def test_block_cli_timeout_is_bounded_below_the_hook_budget():
    seen: list[tuple[str, int]] = []

    def runner(command, timeout):
        seen.append((str(command[4]), timeout))
        return subprocess.CompletedProcess(command, 0, "", "")

    projector = HermesProjector(runner)
    assert projector.comment_and_block("fleet-ops", "t_x", "msg", block=True) == {"block": 0}
    assert projector.comment_and_block("fleet-ops", "t_x", "msg", block=False) == {"comment": 0}
    assert seen == [
        ("block", HermesProjector.BLOCK_TIMEOUT_SECONDS),
        ("comment", HermesProjector.BLOCK_TIMEOUT_SECONDS),
    ]
    # The former hard-coded 20s bound equalled the hook budget that expired.
    assert 0 < HermesProjector.BLOCK_TIMEOUT_SECONDS < 20


def test_typed_block_kind_is_a_single_call_on_a_patched_host():
    seen: list[list[str]] = []

    def runner(command, timeout):
        seen.append(list(command))
        return subprocess.CompletedProcess(command, 0, "", "")

    projector = HermesProjector(runner)
    assert projector.comment_and_block("fleet-ops", "t_x", "msg") == {"block": 0}
    assert len(seen) == 1
    assert seen[0][-2:] == ["--kind", "policy_denied"]


def test_typed_kind_rejection_falls_back_to_the_supported_verb():
    """The host CLI lost its fleet-patched verb: the card must still land.

    Live 2026-10-16: an unpatched ``hermes kanban block`` answers
    ``invalid choice: 'policy_denied'`` with rc=2, so before this fallback the
    projection never moved the card at all.
    """
    seen: list[list[str]] = []
    rejection = ("usage: hermes kanban block [-h] [--ids IDS [IDS ...]]\n"
                 "hermes kanban block: error: argument --kind: invalid choice: "
                 "'policy_denied' (choose from 'capability', 'dependency', "
                 "'needs_input', 'transient')")

    def runner(command, timeout):
        seen.append(list(command))
        if "policy_denied" in command:
            return subprocess.CompletedProcess(command, 2, "", rejection)
        return subprocess.CompletedProcess(command, 0, "", "")

    projector = HermesProjector(runner)
    result = projector.comment_and_block("fleet-ops", "t_x", "FLEET POLICY BLOCKED msg")

    assert result == {"block": 0, "block_kind": "needs_input"}
    assert [call[-2:] for call in seen] == [
        ["--kind", "policy_denied"], ["--kind", "needs_input"],
    ]
    # Same card, same rule text, same bound: only the disposition verb changed.
    assert [call[5] for call in seen] == ["t_x", "t_x"]
    assert [call[6] for call in seen] == ["FLEET POLICY BLOCKED msg"] * 2
    assert {call[1] for call in seen} == {"kanban"}


def test_other_cli_errors_do_not_trigger_the_fallback():
    seen: list[list[str]] = []

    def runner(command, timeout):
        seen.append(list(command))
        return subprocess.CompletedProcess(command, 2, "", "error: unrecognized arguments")

    projector = HermesProjector(runner)
    assert projector.comment_and_block("fleet-ops", "t_x", "msg") == {"block": 2}
    assert len(seen) == 1


def test_degraded_disposition_is_audited_without_a_failure(tmp_path, monkeypatch):
    module = _load_plugin("fp_plugin_kind_fallback")
    _runtime, store = _wire(module, tmp_path, monkeypatch)
    monkeypatch.setattr(
        module._PROJECTOR, "comment_and_block",
        lambda board, task_id, message, *, block: {"block": 0, "block_kind": "needs_input"},
    )

    module._project({"task_id": "t_nomarker", "rule_id": TIMEOUT_RULES,
                     "board": "fleet-ops", "run_key": "run-1"})
    module._PROJECTIONS.join(timeout=10)

    assert _count(store, "projection_claim") == 1
    assert _count(store, "projection_fallback") == 1
    assert _count(store, "projection_failed") == 0
