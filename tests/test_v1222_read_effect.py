"""v1.2.22 — quoted-literal false mutations and the `find` read whitelist.

Spec: policy-quoted-literal-fix-v2.md (supersedes the v1 runtime-only fix,
which was a proven no-op: at effect=read the lexical classifier already
returns read_only before any gated category, so a gated category implies
effect=state_change).

Root causes under test:
- MUTATOR scanned the RAW command text including quoted argument literals,
  so `grep -rn "deploy" scripts/` matched \\bdeploy\\b INSIDE the quotes,
  flipped a read to state_change, and fell into an evidence-gated lexical
  category (evidence_gate_missing DENY).
- `find` was absent from READ_COMMAND: every find was state_change, and
  path/pattern prose like "*cleanup*" then landed in destructive_change.

Fix under test:
- A: quoted spans are stripped BEFORE the MUTATOR scan in
  _terminal_is_read_only (same unquote regex as _has_write_marker); the
  RAW text still feeds the write-marker scan.
- B: `find` joins READ_COMMAND for read-only forms; its mutating options
  (-delete/-exec/-execdir/-ok/-okdir/-fls/-fprint) join the token-based
  write-marker scan so they stay state_change.
- C (defense-in-depth invariant): the evidence-gate condition also checks
  effect != "read", making "reads never require evidence gates" explicit.
"""

from __future__ import annotations

import pytest

from fleet_policy.policy import classify


# --- RED cases: quoted prose must never flip a read into a mutation -------


def test_grep_quoted_deploy_stays_read(config):
    result = classify("terminal", {"command": 'grep -rn "deploy" scripts/'}, config, worker=True)
    assert (result.effect, result.category, result.decision) == ("read", "read_only", "allow")


def test_find_quoted_cleanup_pattern_stays_read(config):
    result = classify("terminal", {"command": 'find . -path "*cleanup*"'}, config, worker=True)
    assert (result.effect, result.category, result.decision) == ("read", "read_only", "allow")


def test_chained_quoted_reads_stay_read(config):
    result = classify(
        "terminal", {"command": 'grep -rn "deploy" scripts/ && cat README.md'}, config, worker=True
    )
    assert (result.effect, result.category, result.decision) == ("read", "read_only", "allow")


@pytest.mark.parametrize(
    "command",
    [
        'grep -rn "deploy" scripts/',
        'grep -rn "rm -rf" docs/',
        'rg -n "push origin main" src/',
        "find . -name '*cleanup*'",
        'find . -path "*deploy*" -maxdepth 2',
        "find . -iname '*.tmp' -type f",
    ],
)
def test_quoted_mutator_words_never_flip_reads(config, command):
    result = classify("terminal", {"command": command}, config, worker=True)
    assert (result.effect, result.category, result.decision) == ("read", "read_only", "allow")


def test_unquoted_destructive_prose_in_find_args_stays_read(config):
    # The fix is about QUOTED literals; unquoted find operands were already
    # harmless because MUTATOR never matched them (spec RED2b control).
    result = classify("terminal", {"command": "find . -path ./cleanup -maxdepth 1"}, config, worker=True)
    assert (result.effect, result.category, result.decision) == ("read", "read_only", "allow")


# --- GREEN invariants: find's mutating options must stay state_change -----


@pytest.mark.parametrize(
    "command,category",
    [
        ("find . -name x -delete", "destructive_change"),
        ("find . -exec rm {} \\;", "destructive_change"),
        ("find . -exec rm {} ;", "destructive_change"),
        ("find . -name x -execdir rm {} \\;", "destructive_change"),
        ("find . -name x -ok rm {} \\;", "destructive_change"),
        ("find . -name x -okdir rm {} \\;", "destructive_change"),
        ("find . -fls listing.txt", "scoped_state_change"),
        ("find . -fprint listing.txt", "scoped_state_change"),
        ("cat README.md && find . -name x -delete", "destructive_change"),
    ],
)
def test_find_mutating_forms_stay_state_change(config, command, category):
    result = classify("terminal", {"command": command}, config, worker=True)
    assert result.effect == "state_change"
    assert (result.category, result.decision) == (category, "allow")


def test_find_plain_read_forms(config):
    for command in (
        "find . -name README.md",
        "find . -maxdepth 2 -type f",
        "find src -path '*test*'",
    ):
        result = classify("terminal", {"command": command}, config, worker=True)
        assert (result.effect, result.category, result.decision) == ("read", "read_only", "allow")


# --- GREEN invariants: existing behavior unchanged ------------------------


@pytest.mark.parametrize(
    "command",
    [
        "rm -rf build",
        "sed -i s/a/b/ file.txt",
        "echo a > f.txt",
        "docker compose up -d",
    ],
)
def test_genuine_mutations_unchanged(config, command):
    result = classify("terminal", {"command": command}, config, worker=True)
    assert result.effect == "state_change"
    assert result.decision != "deny" or result.rule_id != "read_only"


def test_push_to_protected_branch_stays_gated(config):
    result = classify("terminal", {"command": "git push origin main"}, config, worker=True)
    assert (result.effect, result.category, result.decision) == (
        "state_change", "release_to_protected_branch", "allow",
    )


def test_runtime_read_lane_never_requires_evidence_gates(runtime, task_context):
    """Invariant C at the runtime level: reads never hit missing_gates."""
    task_context["tool_call_id"] = "inv-1"
    gated = runtime.pre_tool_call("terminal", {"command": "git push origin main"}, task_context)
    assert (gated.decision, gated.rule_id) == ("deny", "evidence_gate_missing")

    task_context["tool_call_id"] = "inv-2"
    read = runtime.pre_tool_call("terminal", {"command": 'find . -path "*cleanup*"'}, task_context)
    assert (read.decision, read.rule_id) == ("allow", "read_only")
