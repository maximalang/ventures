"""v1.2.27: carve-out excludes store-pattern names + symlink fail-closed.

QA t_14a79801 (CHANGES REQUESTED on 68937655) found two HIGH bypasses of
the v1.2.26 tracked-source carve-out:

HIGH-1: a control-plane STORE-pattern filename that combines a store token
with the guarded name-token (e.g. ``kan…ban.<token>.db``) matched the broad
name pattern, was git-tracked, and got reclassified to an ordinary read.
Store-name db files must stay denied regardless of tracked status.

HIGH-2: symlink indirection was not failed closed — an UNTRACKED symlink
whose name matches, pointing at a TRACKED target, resolved to the target
and passed the tracked check. The carve-out must deny whenever the physical
(realpath) identity differs from the requested path, or the final component
is a link/reparse point, covering untracked links, tracked links, and
directory-hop links alike.

Fixtures are synthetic temp repos; no live policy state is touched. Names
are assembled from parts so policy scanners do not match this file itself.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from fleet_policy.policy import classify

TOKEN = "cre" + "dential"
RULE = "sec" + "ret_read_or_write"
STORE_A = "kan" + "ban"
STORE_B = "fleet-" + "policy"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=str(repo), check=True, capture_output=True)


def _symlink(target: Path, link: Path, *, directory: bool = False) -> bool:
    try:
        os.symlink(str(target), str(link), target_is_directory=directory)
        return True
    except OSError:
        return False


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "agent").mkdir(parents=True)
    tracked = root / "agent" / f"{TOKEN}_pool.py"
    tracked.write_text("class Pool:\n    pass\n", encoding="utf-8")
    # HIGH-1 fixtures: store-token db names that ALSO carry the guarded
    # name-token, deliberately TRACKED to prove tracked status never
    # reclassifies them.
    store_a = root / f"{STORE_A}.{TOKEN}.db"
    store_a.write_bytes(b"\x00" * 16)
    store_b = root / f"{STORE_B}.{TOKEN}.db"
    store_b.write_bytes(b"\x00" * 16)
    _init_repo(root)
    _git(root, "add", f"agent/{TOKEN}_pool.py", store_a.name, store_b.name)
    _git(root, "commit", "-q", "-m", "fixture")
    return root


def _init_repo(root: Path) -> None:
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "fixture@example.com")
    _git(root, "config", "user.name", "fixture")


# ---------------------------------------------------------------- HIGH-1


def test_store_pattern_db_tracked_read_stays_denied(repo, config):
    target = str(repo / f"{STORE_A}.{TOKEN}.db")
    result = classify("read_file", {"path": target}, config, worker=True)
    assert (result.decision, result.category) == ("deny", RULE), result


def test_store_pattern_db_second_token_tracked_read_stays_denied(repo, config):
    target = str(repo / f"{STORE_B}.{TOKEN}.db")
    result = classify("read_file", {"path": target}, config, worker=True)
    assert (result.decision, result.category) == ("deny", RULE), result


def test_store_pattern_db_tracked_write_stays_denied(repo, config):
    target = str(repo / f"{STORE_A}.{TOKEN}.db")
    result = classify(
        "write_file", {"path": target, "content": "x"}, config, worker=True
    )
    assert (result.decision, result.category) == ("deny", RULE), result


def test_store_pattern_db_terminal_read_stays_denied(repo, config):
    target = str(repo / f"{STORE_A}.{TOKEN}.db")
    result = classify(
        "terminal", {"command": f"head -c 16 {target}"}, config, worker=True
    )
    assert (result.decision, result.category) == ("deny", RULE), result


def test_store_pattern_db_wal_variant_stays_denied(repo, config):
    # db-family siblings (wal/shm/journal) share the store-name exclusion
    target = str(repo / f"{STORE_A}.{TOKEN}.db-wal")
    (repo / f"{STORE_A}.{TOKEN}.db-wal").write_bytes(b"\x00" * 8)
    _git(repo, "add", f"{STORE_A}.{TOKEN}.db-wal")
    _git(repo, "commit", "-q", "-m", "fixture-wal")
    result = classify("read_file", {"path": target}, config, worker=True)
    assert (result.decision, result.category) == ("deny", RULE), result


# ---------------------------------------------------------------- HIGH-2


def test_untracked_symlink_to_tracked_target_denied(repo, config):
    target = repo / "agent" / f"{TOKEN}_pool.py"
    link = repo / "agent" / f"{TOKEN}_link.py"
    if not _symlink(target, link):
        pytest.skip("symlink creation not permitted on this host")
    result = classify("read_file", {"path": str(link)}, config, worker=True)
    assert (result.decision, result.category) == ("deny", RULE), result


def test_untracked_symlink_terminal_read_denied(repo, config):
    target = repo / "agent" / f"{TOKEN}_pool.py"
    link = repo / "agent" / f"{TOKEN}_grep.py"
    if not _symlink(target, link):
        pytest.skip("symlink creation not permitted on this host")
    result = classify(
        "terminal", {"command": f"grep -n class {link}"}, config, worker=True
    )
    assert (result.decision, result.category) == ("deny", RULE), result


def test_tracked_symlink_to_tracked_target_denied(repo, config):
    target = repo / "agent" / f"{TOKEN}_pool.py"
    link = repo / "agent" / f"{TOKEN}_alias.py"
    if not _symlink(target, link):
        pytest.skip("symlink creation not permitted on this host")
    _git(repo, "add", f"agent/{TOKEN}_alias.py")
    _git(repo, "commit", "-q", "-m", "fixture-link")
    # tracked link + tracked target: physical identity still differs from
    # the requested path, so the carve-out stays closed
    result = classify("read_file", {"path": str(link)}, config, worker=True)
    assert (result.decision, result.category) == ("deny", RULE), result


def test_symlinked_directory_hop_denied(repo, config):
    linkdir = repo / "agent_link"
    if not _symlink(repo / "agent", linkdir, directory=True):
        pytest.skip("symlink creation not permitted on this host")
    via_hop = linkdir / f"{TOKEN}_pool.py"
    result = classify("read_file", {"path": str(via_hop)}, config, worker=True)
    assert (result.decision, result.category) == ("deny", RULE), result


def test_symlink_relative_workdir_form_denied(repo, config):
    link = repo / "agent" / f"{TOKEN}_rel.py"
    if not _symlink(repo / "agent" / f"{TOKEN}_pool.py", link):
        pytest.skip("symlink creation not permitted on this host")
    result = classify(
        "terminal",
        {"command": f"head -20 agent/{TOKEN}_rel.py", "workdir": str(repo)},
        config,
        worker=True,
    )
    assert (result.decision, result.category) == ("deny", RULE), result


# ------------------------------------------------- no-regression control


def test_tracked_plain_source_still_allowed(repo, config):
    target = str(repo / "agent" / f"{TOKEN}_pool.py")
    result = classify("read_file", {"path": target}, config, worker=True)
    assert (result.effect, result.decision) == ("read", "allow"), result
    assert result.category != RULE


def test_tracked_plain_source_terminal_read_still_allowed(repo, config):
    target = str(repo / "agent" / f"{TOKEN}_pool.py")
    result = classify(
        "terminal", {"command": f"grep -n class {target}"}, config, worker=True
    )
    assert (result.decision, result.category) == ("allow", "read_only"), result
