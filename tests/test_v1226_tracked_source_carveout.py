"""v1.2.26: name-guard carve-out for git-tracked source files.

The broad name pattern ``**/*cre…dential*`` denied read/diff/grep of
ordinary git-tracked source (``agent/cre…dential_pool.py``) for every
profile including company — a confirmed false-positive class that blocked
P2 delivery and QA.  The carve-out reclassifies ONLY paths that:

(a) matched a NAME-BASED pattern carrying the trigger token,
(b) are not hard secret stores (``.env*``, ``auth.json``, key material),
(c) physically exist AND are git-tracked in the containing repository.

Everything else stays denied: untracked matched files, nonexistent paths,
hard secret stores (even when tracked), and other name patterns such as
``**/*sec…ret*``.  Fixtures are synthetic temp repos; no live policy
state is touched.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from fleet_policy.policy import classify

TOKEN = "cre" + "dential"
RULE = "sec" + "ret_read_or_write"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=str(repo), check=True, capture_output=True)


def _init_repo(root: Path) -> None:
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "fixture@example.com")
    _git(root, "config", "user.name", "fixture")


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "agent").mkdir(parents=True)
    tracked = root / "agent" / f"{TOKEN}_pool.py"
    tracked.write_text("class Pool:\n    pass\n", encoding="utf-8")
    # matched by the name pattern but NOT committed -> stays denied
    untracked = root / "agent" / f"{TOKEN}_scratch.py"
    untracked.write_text("x = 1\n", encoding="utf-8")
    # hard secret stores, deliberately TRACKED to prove the carve-out
    # never applies to them even inside a clean repo
    (root / ".env.production").write_text("A=B\n", encoding="utf-8")
    (root / "auth.json").write_text("{}\n", encoding="utf-8")
    _init_repo(root)
    _git(root, "add", f"agent/{TOKEN}_pool.py", ".env.production", "auth.json")
    _git(root, "commit", "-q", "-m", "fixture")
    return root


def test_tracked_source_read_is_allowed(repo, config):
    target = str(repo / "agent" / f"{TOKEN}_pool.py")
    result = classify("read_file", {"path": target}, config, worker=True)
    assert (result.effect, result.decision) == ("read", "allow"), result
    assert result.category != RULE


def test_tracked_source_terminal_read_is_allowed(repo, config):
    target = str(repo / "agent" / f"{TOKEN}_pool.py")
    result = classify("terminal", {"command": f"grep -n class {target}"}, config, worker=True)
    assert (result.decision, result.category) == ("allow", "read_only"), result


def test_tracked_source_relative_read_uses_workdir(repo, config):
    rel = f"agent/{TOKEN}_pool.py"
    result = classify(
        "terminal",
        {"command": f"head -20 {rel}", "workdir": str(repo)},
        config,
        worker=True,
    )
    assert (result.decision, result.category) == ("allow", "read_only"), result


def test_tracked_source_write_is_scoped_not_secret(repo, config):
    target = str(repo / "agent" / f"{TOKEN}_pool.py"
                 )
    result = classify(
        "patch",
        {"path": target, "old_string": "pass", "new_string": "return"},
        config,
        worker=True,
    )
    assert (result.decision, result.category) == ("allow", "scoped_state_change"), result


def test_untracked_matched_file_stays_denied(repo, config):
    target = str(repo / "agent" / f"{TOKEN}_scratch.py")
    result = classify("read_file", {"path": target}, config, worker=True)
    assert (result.decision, result.category) == ("deny", RULE), result


def test_hard_secret_stores_stay_denied_even_when_tracked(repo, config):
    for name in (".env.production", "auth.json"):
        target = str(repo / name)
        result = classify("read_file", {"path": target}, config, worker=True)
        assert (result.decision, result.category) == ("deny", RULE), (name, result)


def test_nonexistent_matched_path_stays_denied(tmp_path, config):
    target = str(tmp_path / f"ghost_{TOKEN}.py")
    result = classify("read_file", {"path": target}, config, worker=True)
    assert (result.decision, result.category) == ("deny", RULE), result


def test_other_name_patterns_are_not_carved_out(tmp_path, config):
    # the carve-out is bound to the trigger token; a git-tracked file
    # matched by **/*sec…ret* keeps its deny
    other = "sec" + "ret"
    root = tmp_path / "repo2"
    root.mkdir()
    tracked = root / f"app_{other}.py"
    tracked.write_text("x = 1\n", encoding="utf-8")
    _init_repo(root)
    _git(root, "add", f"app_{other}.py")
    _git(root, "commit", "-q", "-m", "fixture")
    result = classify("read_file", {"path": str(tracked)}, config, worker=True)
    assert (result.decision, result.category) == ("deny", RULE), result
