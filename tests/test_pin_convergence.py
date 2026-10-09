"""v1.2.29: pin-convergence check unit tests — FIXTURES ONLY.

Per card t_b6710b64 hard rules these tests build a synthetic profiles tree
under pytest tmp_path and never touch any live profile location. Covers:
all-converged pass, divergent sha, unresolvable entry (fail-closed), env
root resolution, missing root / no entries usage errors, version parsing.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "check_pin_convergence.py"
spec = importlib.util.spec_from_file_location("check_pin_convergence", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

SHA_A = "a" * 40
SHA_B = "b" * 40


def _init_repo(path: Path, sha_wanted: bool = True) -> str:
    """Make path a real git repo; return its HEAD sha."""
    subprocess.run(["git", "init", "-q"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@e.st"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=path, check=True, capture_output=True)
    (path / "seed.txt").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "seed"], cwd=path, check=True, capture_output=True
    )
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=path, check=True, capture_output=True, text=True
    )
    return proc.stdout.strip()


def _make_profiles_root(tmp_path: Path) -> Path:
    root = tmp_path / "profiles"
    root.mkdir()
    return root


def _deploy(root: Path, profile: str, version: str) -> Path:
    plugin_dir = root / profile / "plugins" / "fleet-policy"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.yaml").write_text(
        f'name: fleet-policy\nversion: "{version}"\n', encoding="utf-8"
    )
    _init_repo(plugin_dir)
    return plugin_dir


def _commit_new(plugin_dir: Path) -> str:
    (plugin_dir / "bump.txt").write_text("y", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=plugin_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "bump"], cwd=plugin_dir, check=True, capture_output=True
    )
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=plugin_dir, check=True, capture_output=True, text=True
    )
    return proc.stdout.strip()


def test_parse_plugin_version():
    assert mod.parse_plugin_version('version: "1.2.29"\n') == "1.2.29"
    assert mod.parse_plugin_version("version: 1.2.29\n") == "1.2.29"
    assert mod.parse_plugin_version("name: x\n") is None


def test_all_converged_passes(tmp_path, capsys):
    if mod.shutil.which("git") is None:
        pytest.skip("git binary unavailable")
    root = _make_profiles_root(tmp_path)
    first = _deploy(root, "alpha", "1.2.29")
    second = _deploy(root, "beta", "1.2.29")
    # Both repos share no objects; converge by committing the same second
    # commit content is NOT enough — instead point both at one sha by
    # checking out the first repo's commit into the second.
    proc = subprocess.run(
        ["git", "fetch", "-q", str(first), "HEAD"], cwd=second, capture_output=True
    )
    assert proc.returncode == 0, proc.stderr
    subprocess.run(
        ["git", "checkout", "-q", "FETCH_HEAD"], cwd=second, check=True, capture_output=True
    )
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=first, check=True, capture_output=True, text=True
    ).stdout.strip()
    rc = mod.main([sha, "--profiles-root", str(root)])
    assert rc == 0
    payload = __import__("json").loads(capsys.readouterr().out)
    assert payload["converged"] is True
    assert payload["divergent"] == []
    assert {e["profile"] for e in payload["entries"]} == {"alpha", "beta"}
    assert all(e["version"] == "1.2.29" for e in payload["entries"])


def test_divergent_sha_fails_and_lists_entries(tmp_path, capsys):
    if mod.shutil.which("git") is None:
        pytest.skip("git binary unavailable")
    root = _make_profiles_root(tmp_path)
    _deploy(root, "alpha", "1.2.29")
    lagging = _deploy(root, "beta", "1.2.28")
    expected = _commit_new(lagging)  # alpha sits on the older seed commit
    rc = mod.main([expected, "--profiles-root", str(root)])
    assert rc == 1
    payload = __import__("json").loads(capsys.readouterr().out)
    assert payload["converged"] is False
    assert payload["divergent"][0]["profile"] == "alpha"


def test_unresolvable_entry_fails_closed(tmp_path, capsys):
    root = _make_profiles_root(tmp_path)
    plugin_dir = root / "broken" / "plugins" / "fleet-policy"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.yaml").write_text('version: "1.2.29"\n', encoding="utf-8")
    # No git init: sha unresolvable — must be divergent, never skipped.
    rc = mod.main([SHA_A, "--profiles-root", str(root)])
    assert rc == 1
    payload = __import__("json").loads(capsys.readouterr().out)
    assert payload["converged"] is False
    assert payload["divergent"][0]["profile"] == "broken"
    assert payload["divergent"][0]["sha"] is None


def test_env_root_resolution(tmp_path, monkeypatch, capsys):
    root = _make_profiles_root(tmp_path)
    monkeypatch.setenv("HERMES_PROFILES_ROOT", str(root))
    rc = mod.main([SHA_A])
    assert rc == 2  # no entries under the env-provided root
    err = capsys.readouterr().err
    assert "no deployed plugins" in err


def test_missing_root_usage_error(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("HERMES_PROFILES_ROOT", raising=False)
    rc = mod.main([SHA_A])
    assert rc == 2
    assert "profiles root not provided" in capsys.readouterr().err


def test_bad_expected_sha_usage_error(tmp_path, capsys):
    rc = mod.main(["not-a-sha", "--profiles-root", str(tmp_path)])
    assert rc == 2
    assert "not 40-hex" in capsys.readouterr().err


def test_nonexistent_root_usage_error(tmp_path, capsys):
    rc = mod.main([SHA_A, "--profiles-root", str(tmp_path / "absent")])
    assert rc == 2
    assert "not a directory" in capsys.readouterr().err
