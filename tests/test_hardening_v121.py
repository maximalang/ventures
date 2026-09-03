from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import yaml
import pytest

from fleet_policy.policy import classify

ROOT = Path(__file__).parents[1]


def test_worker_execute_code_requires_exact_one_time_approval(runtime, task_context, monkeypatch):
    args = {"code": "print('bounded diagnostic')"}
    first = runtime.pre_tool_call("execute_code", args, task_context)
    assert (first.decision, first.rule_id) == ("approval_required", "worker_code_execution")
    assert first.approval_card is not None

    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    key = first.approval_card["rule_key"]
    assert runtime.store.decide_approval(key, True, "user", confirm_code=key[-8:])

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


def test_release_bundle_inventory_is_stable_after_generated_egg_info(tmp_path):
    from fleet_policy.release_bundle import build_release_bundle, release_inventory, verify_release_bundle

    source = tmp_path / "exact-source"
    shutil.copytree(
        ROOT,
        source,
        ignore=shutil.ignore_patterns(
            ".git", ".venv", ".state", ".pytest_cache", "__pycache__", "*.egg-info", "*.pyc", "*.pyo"
        ),
    )
    clean_bundle = tmp_path / "clean-bundle"
    generated_bundle = tmp_path / "generated-bundle"
    build_release_bundle(source, clean_bundle)

    metadata = source / "src" / "ventures_fleet_policy.egg-info"
    metadata.mkdir()
    (metadata / "PKG-INFO").write_text("generated metadata\n", encoding="utf-8")
    build_release_bundle(source, generated_bundle)

    clean_inventory = verify_release_bundle(clean_bundle)
    generated_inventory = verify_release_bundle(generated_bundle)
    assert clean_inventory == generated_inventory
    assert clean_inventory == [item for item in release_inventory(clean_bundle) if item != "RELEASE-MANIFEST.json"]
    assert not any(part.endswith(".egg-info") for item in generated_inventory for part in item.split("/"))


def test_default_bundle_is_self_contained_for_drift_and_rr_guidance(tmp_path, monkeypatch):
    from fleet_policy.release_bundle import build_release_bundle, verify_release_bundle

    bundle = tmp_path / "bundle"
    build_release_bundle(ROOT, bundle)
    assert verify_release_bundle(bundle)

    drift = subprocess.run(
        [sys.executable, "-m", "fleet_policy.cli", "--root", str(bundle), "drift-check"],
        cwd=bundle,
        capture_output=True,
        text=True,
    )
    assert drift.returncode == 0, drift.stderr
    assert json.loads(drift.stdout) == {"missing": [], "ok": True}

    monkeypatch.delenv("HERMES_VENTURES_ROOT", raising=False)
    monkeypatch.setenv("HERMES_KANBAN_BOARD", "rr-team")
    module_path = bundle / "integrations" / "hermes" / "fleet-policy-plugin" / "__init__.py"
    spec = importlib.util.spec_from_file_location("fleet_policy_plugin_bundle_guidance", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    guidance = module.project_guidance(None)
    assert "# Recruiter Radar project guidance" in guidance


def test_release_bundle_rejects_rewritten_manifest_missing_canonical_payload(tmp_path):
    from fleet_policy.release_bundle import build_release_bundle, verify_release_bundle

    bundle = tmp_path / "bundle"
    build_release_bundle(ROOT, bundle)
    (bundle / "plugin.yaml").unlink()
    manifest_path = bundle / "RELEASE-MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"] = [entry for entry in manifest["files"] if entry["path"] != "plugin.yaml"]
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    try:
        verify_release_bundle(bundle)
    except ValueError as exc:
        assert "missing required release path: plugin.yaml" in str(exc)
    else:
        raise AssertionError("rewritten manifest unexpectedly verified without canonical payload")


def test_release_bundle_rejects_rewritten_manifest_with_wrong_required_path_type(tmp_path):
    from fleet_policy.release_bundle import build_release_bundle, verify_release_bundle

    bundle = tmp_path / "bundle"
    build_release_bundle(ROOT, bundle)
    config = bundle / "config"
    shutil.rmtree(config)
    config.write_text("not a directory", encoding="utf-8")
    manifest_path = bundle / "RELEASE-MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"] = [entry for entry in manifest["files"] if not entry["path"].startswith("config/")]
    manifest["files"].append({"path": "config", "sha256": hashlib.sha256(config.read_bytes()).hexdigest()})
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    try:
        verify_release_bundle(bundle)
    except ValueError as exc:
        assert "required release path is not a directory: config" in str(exc)
    else:
        raise AssertionError("rewritten manifest unexpectedly verified with a file replacing a required directory")


def _poison_manifest(manifest_path):
    # The verifier must reject the filesystem entry before parsing this input.
    manifest_path.write_text("{", encoding="utf-8")


def test_release_bundle_rejects_nested_directory_symlink_before_manifest(tmp_path):
    from fleet_policy.release_bundle import build_release_bundle, verify_release_bundle

    bundle = tmp_path / "bundle"
    build_release_bundle(ROOT, bundle)
    nested = bundle / "src" / "fleet_policy"
    outside = tmp_path / "outside" / "fleet_policy"
    outside.mkdir(parents=True)
    (outside / "__init__.py").write_text("marker = 67\n", encoding="utf-8")
    shutil.rmtree(nested)
    try:
        nested.symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlink is unavailable: {exc}")
    _poison_manifest(bundle / "RELEASE-MANIFEST.json")

    with pytest.raises(ValueError, match="link or reparse point"):
        verify_release_bundle(bundle)


@pytest.mark.skipif(os.name != "nt", reason="Windows junction semantics")
def test_release_bundle_rejects_nested_windows_junction_before_manifest(tmp_path):
    from fleet_policy.release_bundle import build_release_bundle, verify_release_bundle

    bundle = tmp_path / "bundle"
    build_release_bundle(ROOT, bundle)
    nested = bundle / "src" / "fleet_policy"
    outside = tmp_path / "outside" / "fleet_policy"
    outside.mkdir(parents=True)
    (outside / "__init__.py").write_text("marker = 67\n", encoding="utf-8")
    shutil.rmtree(nested)
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(nested), str(outside)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    assert nested.is_dir() and not nested.is_symlink()
    _poison_manifest(bundle / "RELEASE-MANIFEST.json")

    with pytest.raises(ValueError, match="link or reparse point"):
        verify_release_bundle(bundle)


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
    assert versions == {"1.2.7"}


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


def test_integration_root_defaults_to_bundle_and_supports_override(monkeypatch, tmp_path):
    module_path = ROOT / "integrations" / "hermes" / "fleet-policy-plugin" / "__init__.py"
    monkeypatch.delenv("HERMES_VENTURES_ROOT", raising=False)
    spec = importlib.util.spec_from_file_location("fleet_policy_plugin_portable", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert module.CODE_ROOT == ROOT
    assert module.VENTURES_ROOT == ROOT

    monkeypatch.setenv("HERMES_VENTURES_ROOT", str(tmp_path))
    override_spec = importlib.util.spec_from_file_location("fleet_policy_plugin_override", module_path)
    override = importlib.util.module_from_spec(override_spec)
    assert override_spec.loader is not None
    override_spec.loader.exec_module(override)
    assert override.VENTURES_ROOT == tmp_path


def test_release_bundle_inventory_excludes_generated_package_metadata(tmp_path):
    from fleet_policy.release_bundle import build_release_bundle, release_inventory, verify_release_bundle

    bundle = tmp_path / "bundle"
    build_release_bundle(ROOT, bundle)

    # Simulate generated package metadata landing inside a canonical payload dir.
    egg_info = bundle / "src" / "ventures_fleet_policy.egg-info"
    egg_info.mkdir()
    (egg_info / "PKG-INFO").write_text("Metadata-Version: 2.1\n", encoding="utf-8")
    dist_info = bundle / "src" / "fleet_policy" / "fleet_policy-1.2.1.dist-info"
    dist_info.mkdir()
    (dist_info / "METADATA").write_text("Metadata-Version: 2.1\n", encoding="utf-8")

    inventory = release_inventory(bundle)
    leaked = [item for item in inventory if ".egg-info" in item or ".dist-info" in item]
    assert not leaked, leaked

    # A verified bundle must be fail-closed about generated metadata on disk.
    try:
        verify_release_bundle(bundle)
    except ValueError as exc:
        assert "generated package metadata" in str(exc)
    else:
        raise AssertionError("bundle with generated package metadata unexpectedly verified")


def test_release_bundle_build_excludes_source_package_metadata(tmp_path):
    from fleet_policy.release_bundle import RELEASE_PATHS, build_release_bundle, release_inventory

    source = tmp_path / "source"
    for relative in RELEASE_PATHS:
        target = source / relative
        if relative in {"config", "src", "tests", "scripts", "integrations/hermes/fleet-policy-plugin"}:
            target.mkdir(parents=True)
            (target / "payload.txt").write_text("x", encoding="utf-8")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("x", encoding="utf-8")
    egg_info = source / "src" / "ventures_fleet_policy.egg-info"
    egg_info.mkdir()
    (egg_info / "PKG-INFO").write_text("Metadata-Version: 2.1\n", encoding="utf-8")
    (source / "src" / "legacy.egg").mkdir()
    (source / "src" / "legacy.egg" / "EGG-INFO").mkdir()
    (source / "src" / "legacy.egg" / "EGG-INFO" / "PKG-INFO").write_text("x", encoding="utf-8")

    bundle = tmp_path / "bundle"
    build_release_bundle(source, bundle)
    inventory = release_inventory(bundle)
    leaked = [item for item in inventory if any(part.endswith((".egg-info", ".dist-info", ".egg")) for part in item.split("/"))]
    assert not leaked, leaked


def test_release_bundle_handles_generated_metadata_case_insensitively(tmp_path):
    from fleet_policy.release_bundle import build_release_bundle, verify_release_bundle

    source = tmp_path / "source"
    shutil.copytree(
        ROOT,
        source,
        ignore=shutil.ignore_patterns(
            ".git", ".venv", ".state", ".pytest_cache", "__pycache__", "*.egg-info", "*.pyc", "*.pyo"
        ),
    )
    mixed_case_metadata = source / "src" / "X.EGG-INFO"
    mixed_case_metadata.mkdir()
    (mixed_case_metadata / "PKG-INFO").write_text("Metadata-Version: 2.1\n", encoding="utf-8")

    bundle = tmp_path / "bundle"
    build_release_bundle(source, bundle)
    assert not any(
        part.lower().endswith((".egg-info", ".dist-info", ".egg"))
        for path in bundle.rglob("*")
        for part in path.relative_to(bundle).parts
    )

    leaked_metadata = bundle / "src" / "X.EGG-INFO"
    leaked_metadata.mkdir()
    (leaked_metadata / "PKG-INFO").write_text("Metadata-Version: 2.1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="generated package metadata"):
        verify_release_bundle(bundle)


def test_cli_default_root_finds_source_root_from_wheel_layout(monkeypatch, tmp_path):
    from fleet_policy import cli

    runtime_root = tmp_path / "runtime"
    (runtime_root / "src" / "fleet_policy").mkdir(parents=True)
    installed_cli = runtime_root / ".venv" / "Lib" / "site-packages" / "fleet_policy" / "cli.py"
    installed_cli.parent.mkdir(parents=True)
    installed_cli.touch()

    monkeypatch.delenv("HERMES_VENTURES_ROOT", raising=False)
    monkeypatch.setattr(cli, "__file__", str(installed_cli))

    assert cli.default_root({}) == runtime_root



def test_cli_default_root_is_portable_and_self_contained(monkeypatch, tmp_path):
    from fleet_policy import cli

    monkeypatch.delenv("HERMES_VENTURES_ROOT", raising=False)
    root = cli.default_root({})
    assert (root / "src" / "fleet_policy").is_dir()
    assert "desktop/all/ventures" not in root.as_posix().lower()

    monkeypatch.setenv("HERMES_VENTURES_ROOT", str(tmp_path))
    assert cli.default_root({}) == tmp_path
    assert cli.default_root({"root": str(tmp_path / "explicit")}) == tmp_path / "explicit"
