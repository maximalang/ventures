from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

import yaml

from fleet_policy.policy import classify

ROOT = Path(__file__).parents[1]


def test_worker_execute_code_requires_exact_one_time_approval(runtime, task_context, monkeypatch):
    args = {"code": "print('bounded diagnostic')"}
    first = runtime.pre_tool_call("execute_code", args, task_context)
    assert (first.decision, first.rule_id) == ("approval_required", "worker_code_execution")
    assert first.approval_card is not None

    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    assert runtime.store.decide_approval(first.approval_card["rule_key"], True, "user")

    task_context["tool_call_id"] = "changed-code"
    changed = runtime.pre_tool_call("execute_code", {"code": "print('different')"}, task_context)
    assert (changed.decision, changed.rule_id) == ("approval_required", "worker_code_execution")

    task_context["tool_call_id"] = "approved-code"
    allowed = runtime.pre_tool_call("execute_code", args, task_context)
    assert (allowed.decision, allowed.rule_id) == ("allow", "approved_once")

    task_context["tool_call_id"] = "replayed-code"
    replay = runtime.pre_tool_call("execute_code", args, task_context)
    assert (replay.decision, replay.rule_id) == ("approval_required", "worker_code_execution")


def test_non_worker_execute_code_remains_available(config):
    result = classify("execute_code", {"code": "print('operator')"}, config, worker=False)
    assert (result.decision, result.category) == ("allow", "scoped_state_change")


def test_free_text_report_cannot_trigger_self_approval_deny(config, runtime, task_context):
    report = "QA verified that the worker_self_approval guard blocks fleet-policy approve rule-key"
    arguments = {"task_id": "t_test", "body": report}
    result = classify("kanban_comment", arguments, config, worker=True)
    assert (result.decision, result.category) == ("allow", "scoped_state_change")

    decision = runtime.pre_tool_call("kanban_comment", arguments, task_context)
    assert (decision.decision, decision.rule_id) == ("allow", "scoped_state_change")


def test_release_manifest_covers_runtime_and_review_surfaces():
    from fleet_policy.release_bundle import RELEASE_PATHS

    required = {
        "pyproject.toml",
        "uv.lock",
        "plugin.yaml",
        "config",
        "src",
        "tests",
        "scripts",
        "integrations/hermes/fleet-policy-plugin",
    }
    assert required <= set(RELEASE_PATHS)


def test_release_bundle_builder_is_deterministic_and_excludes_local_state(tmp_path):
    from fleet_policy.release_bundle import build_release_bundle, release_inventory, verify_release_bundle

    first = tmp_path / "first"
    second = tmp_path / "second"
    build_release_bundle(ROOT, first)
    build_release_bundle(ROOT, second)
    assert release_inventory(first) == release_inventory(second)
    inventory = release_inventory(first)
    assert "pyproject.toml" in inventory
    assert "plugin.yaml" in inventory
    assert "integrations/hermes/fleet-policy-plugin/plugin.yaml" in inventory
    assert not any(part in item.split("/") for item in inventory for part in (".git", ".venv", ".state", "__pycache__", ".pytest_cache"))
    verified = verify_release_bundle(first)
    assert verified == sorted(set(inventory) - {"RELEASE-MANIFEST.json"})

    (first / "plugin.yaml").write_text("tampered", encoding="utf-8")
    try:
        verify_release_bundle(first)
    except ValueError as exc:
        assert "checksum mismatch" in str(exc)
    else:
        raise AssertionError("tampered bundle unexpectedly verified")


def test_bundle_cli_does_not_initialize_policy_state(tmp_path):
    from fleet_policy.release_bundle import build_release_bundle

    source = tmp_path / "source"
    build_release_bundle(ROOT, source)
    destination = tmp_path / "destination"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "fleet_policy.cli",
            "--root",
            str(source),
            "build-bundle",
            "--output",
            str(destination),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout)["files"] > 0
    assert not (source / ".state").exists()


def test_package_plugin_and_cli_versions_match():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    root_plugin = yaml.safe_load((ROOT / "plugin.yaml").read_text(encoding="utf-8"))
    integration_plugin = yaml.safe_load(
        (ROOT / "integrations" / "hermes" / "fleet-policy-plugin" / "plugin.yaml").read_text(encoding="utf-8")
    )
    result = subprocess.run(
        [sys.executable, "-m", "fleet_policy.cli", "--version"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    versions = {
        project["project"]["version"],
        str(root_plugin["version"]),
        str(integration_plugin["version"]),
        payload["version"],
    }
    assert versions == {"1.2.1"}


def test_ci_is_pinned_frozen_and_exercises_release_contract():
    path = ROOT / ".github" / "workflows" / "fleet-policy-ci.yml"
    workflow = path.read_text(encoding="utf-8")
    assert "permissions:\n  contents: read" in workflow
    assert "actions/checkout@11d5960a326750d5838078e36cf38b85af677262" in workflow
    assert "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065" in workflow
    setup_uv = "astral-sh/setup-uv@d4b2f3b6ecc6e67c4457f6d3e41ec42d3d0fcb86"
    assert setup_uv in workflow
    command = "uv run --frozen python -m pytest tests/ -q"
    assert workflow.count(command) == 2
    assert "HERMES_KANBAN_TASK: t_ci_simulated" in workflow
    assert "build-bundle" in workflow
    assert "verify-bundle" in workflow
