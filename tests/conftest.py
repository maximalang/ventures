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
    context = {
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
    # v1.2.12 C1: gate verdicts are bound to an expected head. The default
    # context carries the branch head so gate evidence in tests can bind to
    # it; a test can override `head` for foreign/missing-head scenarios.
    context["head"] = "a" * 40
    return context


_HEAD = "a" * 40
_TYPE = "task_type: code"


def bound_passes(*pairs: tuple[str, str]) -> list[dict]:
    """v1.2.12 C1 helper: authorized PASS records bound to the default
    context head and card class, e.g. bound_passes(("tech", _gate("ci")))."""
    return [
        {"author": author, "body": f"{marker} head={_HEAD} {_TYPE}"}
        for author, marker in pairs
    ]
