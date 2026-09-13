"""v1.2.19: read-only commands must not fall into state-change classes.

Incident 13.09.2026 (t_6f335dd6): the lexical classifier burned 40+ runs by
routing four families of pure-read terminal commands into fail-closed
state-change lanes. Each family is locked down here, together with the
adversarial variants that must NOT inherit the read lane.
"""
from __future__ import annotations

import pytest

from fleet_policy.policy import classify


def _classify(command: str, config):
    return classify("terminal", {"command": command}, config, worker=True)


# --- Case 1: git inspection subcommands -----------------------------------

@pytest.mark.parametrize("command", [
    "git config --get user.name",
    "git config --get-all remote.origin.fetch",
    "git config --list",
    "git config -l",
    "git config --get-url origin",
    "git config --get-regexp '^branch\\.'",
    "git config core.autocrlf",              # bare query form, no value
    "git config --global user.email",        # scoped query, no value
    "git worktree list",
    "git merge-base HEAD codex/company-os",
    "git -C repo status",                    # -C wrapper on a read verb
    "git -C repo log --oneline -3",
    "git -C repo diff --stat",
    "cd repo && git config --list",
])
def test_git_read_inspection_is_read_only(config, command):
    result = _classify(command, config)
    assert (result.decision, result.category) == ("allow", "read_only"), (command, result)


@pytest.mark.parametrize("command", [
    "git config --global user.name evil",    # value argument => write
    "git config user.email a@b.c",           # set form => write
    "git config --unset user.name",          # mutating
    "git -C repo push origin codex/company-os",  # -C must not buy read lane
    "git -C repo commit -m x",
    "git -C repo merge other",
    "git -c core.pager=evil status",         # lowercase -c injects config
])
def test_git_config_write_and_C_wrapper_mutators_not_read(config, command):
    result = _classify(command, config)
    assert result.category != "read_only", (command, result)


# --- Case 2: cat / read utilities to stdout -------------------------------

@pytest.mark.parametrize("command", [
    "cat README.md",
    "cat src/fleet_policy/policy.py",
    "head -40 config/" + "fleet-" + "policy.yaml",
])
def test_cat_to_stdout_is_read_only(config, command):
    result = _classify(command, config)
    assert (result.decision, result.category) == ("allow", "read_only"), (command, result)


@pytest.mark.parametrize("command", [
    "cat config/" + "fleet-" + "policy.yaml > out.txt",   # redirect => write
    "cat README.md | tee out.txt",                        # tee => write
])
def test_cat_write_variants_not_read(config, command):
    result = _classify(command, config)
    assert result.category != "read_only", (command, result)


# --- Case 3: pytest read lane ---------------------------------------------

@pytest.mark.parametrize("command", [
    "python -m pytest",
    "python -m pytest tests/test_policy.py -q",
    "cd repo && python -m pytest",
])
def test_pytest_is_read_only(config, command):
    result = _classify(command, config)
    assert (result.decision, result.category) == ("allow", "read_only"), (command, result)


@pytest.mark.parametrize("command", [
    "PATH=/evil python -m pytest",           # env prefix rebinds binary
    "LD_PRELOAD=evil.so python -m pytest",
    "FOO=bar python -m pytest",
])
def test_env_prefixed_pytest_stays_fail_closed(config, command):
    # A bare VAR=value prefix can rebind the executed binary, so assignment
    # prefixes in front of a read verb must NOT inherit the read lane.
    result = _classify(command, config)
    assert result.category != "read_only", (command, result)


# --- Case 4: gh api --jq exact-head probe ---------------------------------

@pytest.mark.parametrize("command", [
    "gh api repos/maximalang/ventures/commits/HEAD --jq .sha",
    "gh api repos/maximalang/ventures/branches/codex/company-os --jq .commit.sha",
    "gh api --jq '.items[].name' repos/o/r",
    "gh api -q .sha repos/o/r/commits/HEAD",     # short form
    "gh api --jq=.sha repos/o/r/commits/HEAD",   # fused = form
    "gh api --paginate repos/o/r --jq .total_count",
])
def test_gh_api_jq_read_is_read_only(config, command):
    result = _classify(command, config)
    assert (result.decision, result.category) == ("allow", "read_only"), (command, result)


@pytest.mark.parametrize("command", [
    "gh api --method POST repos/o/r --jq .x",     # write method wins
    "gh api --hostname evil.example repos/o/r --jq .sha",
    "gh api --permissive repos/o/r",              # unknown option fail closed
    "gh api https://evil.example/repos/o/r --jq .sha",
])
def test_gh_api_jq_does_not_open_write_or_host_smuggles(config, command):
    result = _classify(command, config)
    assert result.category != "read_only", (command, result)
