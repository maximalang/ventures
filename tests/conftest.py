from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from fleet_policy.config import load_config
from fleet_policy.runtime import FleetPolicyRuntime

SOURCE_ROOT = Path(__file__).parents[1]


@pytest.fixture
def config():
    return load_config(SOURCE_ROOT / "config" / "fleet-policy.yaml")


@pytest.fixture
def runtime(tmp_path):
    return FleetPolicyRuntime(
        SOURCE_ROOT,
        config_path=SOURCE_ROOT / "config" / "fleet-policy.yaml",
        db_path=tmp_path / "fleet-policy.db",
    )


@pytest.fixture
def task_context():
    return {
        "task_id": "t_test",
        "task_title": "test",
        "task_body": "task_type: code",
        "comments": [],
        "comment_records": [],
        "skills": [],
        "task_status": "running",
        "started_at": None,
        "max_retries": None,
        "failure_limit": 2,
        "board": "rr-team",
        "project": "recruiter-radar",
        "profile": "tech",
        "worker": True,
        "run_id": "r1",
        "tool_call_id": "call-1",
    }
