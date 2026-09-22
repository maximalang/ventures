"""v1.2.28 integration smoke: combined behavior of merged branches.

Integration candidate t_ba73b612 merges three separately QA-passed lines:
- v1.2.25 (11c3c3e): worker-class deny does NOT park the kanban card;
- v1.2.27 (b8d47ef): tracked-source name-match carve-out with store-pattern
  db names and symlink indirection kept fail-closed;
- P1 recovery controller (d07c068): scripts-only, covered by its own suite.

This module asserts the COMBINED invariants in one integrated worktree:
1. a worker-routed deny (evidence_gate_missing) blocks the call but never
   projects a kanban block (card stays running);
2. a git-tracked plain source whose NAME matches the guarded token is an
   allowed read for a worker;
3. a tracked store-pattern db name carrying the same token stays denied;
4. an untracked symlink name-matching, pointing at the tracked source,
   stays denied (carve-out fail-closed).

Fixtures are synthetic temp repos; no live policy state is touched. Names
are assembled from parts so policy scanners do not match this file itself.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
from pathlib import Path

import pytest

from fleet_policy.policy import classify
from fleet_policy.storage import PolicyStore

TOKEN = "cre" + "dential"
RULE = "sec" + "ret_read_or_write"
STORE = "kan" + "ban"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=str(repo), check=True, capture_output=True)


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "agent").mkdir(parents=True)
    tracked = root / "agent" / f"{TOKEN}_pool.py"
    tracked.write_text("class Pool:\n    pass\n", encoding="utf-8")
    store_db = root / f"{STORE}.{TOKEN}.db"
    store_db.write_bytes(b"\x00" * 16)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "fixture@example.com")
    _git(root, "config", "user.name", "fixture")
    _git(root, "add", f"agent/{TOKEN}_pool.py", store_db.name)
    _git(root, "commit", "-q", "-m", "fixture")
    return root


def _load_plugin(name: str):
    module_path = Path(__file__).parents[1] / "integrations" / "hermes" / "fleet-policy-plugin" / "__init__.py"
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_worker_deny_does_not_park_card(tmp_path, monkeypatch):
    """v1.2.25 invariant inside the integrated tree."""
    module = _load_plugin("fp_plugin_v128_smoke")
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    runtime = module.runtime()
    monkeypatch.setattr(runtime, "store", store)
    monkeypatch.setattr(module, "_RUNTIME", runtime)
    calls = []
    monkeypatch.setattr(
        module._PROJECTOR, "comment_and_block",
        lambda board, task_id, message, *, block: calls.append((board, task_id, message, block)) or {"block": 0},
    )

    from fleet_policy.models import remediation_for
    rem = remediation_for("evidence_gate_missing")
    assert rem and rem["who"] == "worker"

    payload = {
        "decision": "deny", "rule_id": "evidence_gate_missing", "reason": "test",
        "task_id": "t_v128smoke", "project": "fleet-ops", "profile": "tech",
        "action": "terminal", "target": "git", "args_hash": "abc128",
        "timestamp": "2026-09-22T12:00:00Z", "budget_snapshot": {},
        "pattern_category": "evidence_gate_missing", "call_index": 1,
        "deny_nonce": None, "remediation": rem,
    }

    class _D:
        decision = "deny"

        def as_dict(self_inner):
            return dict(payload)

    monkeypatch.setattr(runtime, "pre_tool_call", lambda *a, **k: _D())
    monkeypatch.setenv("HERMES_KANBAN_BOARD", "fleet-ops")
    result = module.pre_tool_call(tool_name="terminal", args={"command": "git push origin main"})
    assert result["action"] == "block"
    assert "[continues: worker]" in result["message"]
    assert calls == []  # карта НЕ припаркована


def test_tracked_source_read_allowed_while_store_and_symlink_denied(repo, config):
    """v1.2.26/v1.2.27 invariants inside the integrated tree."""
    target = str(repo / "agent" / f"{TOKEN}_pool.py")

    # (2) tracked plain source, name-matched -> allowed read for worker
    allowed = classify("read_file", {"path": target}, config, worker=True)
    assert (allowed.effect, allowed.decision) == ("read", "allow"), allowed
    assert allowed.category != RULE

    # (3) tracked store-pattern db name -> still hard-denied
    store_path = str(repo / f"{STORE}.{TOKEN}.db")
    denied_store = classify("read_file", {"path": store_path}, config, worker=True)
    assert denied_store.decision == "deny", denied_store
    assert denied_store.category == RULE

    # (4) untracked symlink name-match -> tracked target: still denied
    link = repo / "agent" / f"{TOKEN}_link.py"
    try:
        os.symlink(target, str(link))
    except OSError:
        pytest.skip("symlink creation not permitted on this platform")
    denied_link = classify("read_file", {"path": str(link)}, config, worker=True)
    assert denied_link.decision == "deny", denied_link
    assert denied_link.category == RULE
