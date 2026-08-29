from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "fleet_migration.py"


def load_module():
    spec = importlib.util.spec_from_file_location("fleet_migration_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_snapshot(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    payload = {
        "active_tasks": [],
        "routing_snapshot": {
            "kanban_config": {
                "exit_code": 0,
                "stdout": (
                    "orchestrator_profile: default\n"
                    "default_assignee: rr-support\n"
                    "max_in_progress: null\n"
                ),
            }
        },
    }
    raw = json.dumps(payload)
    (root / "snapshot.json").write_text(raw, encoding="utf-8")
    digest = hashlib.sha256(raw.encode()).hexdigest()
    (root / "snapshot.sha256").write_text(f"{digest}  snapshot.json\n", encoding="utf-8")


def test_rollback_dry_run_restores_all_config_fields(tmp_path, monkeypatch):
    module = load_module()
    make_snapshot(tmp_path)
    monkeypatch.setattr(module, "latest_snapshot", lambda: tmp_path)
    actions = module.rollback(dry_run=True)
    config = {item["key"]: item["value"] for item in actions if item["action"] == "config"}
    assert config == {
        "kanban.orchestrator_profile": "default",
        "kanban.default_assignee": "rr-support",
        "kanban.max_in_progress": None,
    }


def test_rollback_rejects_tampered_snapshot(tmp_path, monkeypatch):
    module = load_module()
    make_snapshot(tmp_path)
    (tmp_path / "snapshot.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(module, "latest_snapshot", lambda: tmp_path)
    with pytest.raises(RuntimeError, match="checksum mismatch"):
        module.rollback(dry_run=True)
