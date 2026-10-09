"""v1.2.23: stdout-only echo/printf stages must not poison pure-read
diagnostics into policy_control_plane_mutation denies.

Incident 17.09.2026 (t_e7a0a31f, t_d654a389, shadow baseline F1): the
dominant false-positive first-pass failure family was read-only inspection
chained with echo section markers, e.g.
``grep -n "^protected:" config/fleet-policy.yaml; echo "=== x ==="; grep …``
or ``git merge-base --is-ancestor A B && echo OK || echo NO``. The echo
stage alone classified the whole command state_change, so the path guard
saw a policy-controlled operand with effect != read and hard-denied with
"policy-controlled files are immutable for the fleet" — although nothing
wrote anything.

Each read family below is locked GREEN, together with the adversarial
variants that must NOT inherit the read lane.
"""
from __future__ import annotations

import pytest

from fleet_policy.policy import classify


def _classify(command: str, config):
    return classify("terminal", {"command": command}, config, worker=True)


CFG_NAME = "fleet-" + "policy.yaml"


# --- read-only diagnostics with echo markers (the live incident family) ----

@pytest.mark.parametrize("command", [
    f'grep -n -A 25 "^protected:" config/{CFG_NAME}; echo "=== basenames:"; grep -n x src/fleet_policy/policy.py',
    'git merge-base --is-ancestor da0c742 origin/codex/company-os && echo "IN base" || echo "NOT in base"',
    'ls C:/x && echo === && cat C:/y/policy.py',
    f'cd C:/x && cat config/{CFG_NAME} && echo ===CONFIGPY=== && cat src/fleet_policy/config.py',
    f'wc -l PORTFOLIO.md APPROVALS.md AGENTS.md; echo "---probes---"; ls CHARTER.md',
    'echo hello',
    'echo "=== section ==="',
    'printf "x=%s\\n" 42',
    'true',
])
def test_echo_marker_read_diagnostics_are_read_only(config, command):
    result = _classify(command, config)
    assert (result.decision, result.category) == ("allow", "read_only"), (command, result)


# --- adversarial variants must NOT inherit the read lane -------------------

@pytest.mark.parametrize("command", [
    f'echo hi > config/{CFG_NAME}',            # redirect => write marker
    f'echo "x" | tee config/{CFG_NAME}',       # tee => write marker
    'echo $(cat .env)',                        # command substitution fail-closed
    'echo hi `cat auth.json`',                 # backticks fail-closed
    'wc -l PORTFOLIO.md 2>&1; echo x',         # fd-dup `2>&1` trips the metacharacter scan
    'FOO=bar echo hi',                         # env prefix stays fail-closed
    'date',                                    # date stays fail-closed (clock-set forms)
    'python -c "import sqlite3; sqlite3.connect(\'file:C:/x/kanban.db?mode=ro\', uri=True)"',
    # v1.2.31: `sqlite3 <db> "SELECT ..."` moved OUT of this adversary list
    # into the read lane per the company re-scope of 25.09.2026 (read-only
    # diagnostics — SELECT included — must not classify as mutations on
    # policy-controlled paths). The narrow lane boundary (read verbs only;
    # mutations, dot-commands, splicing, interactive sessions stay out) is
    # pinned by test_sqlite_read_lane_boundary_v1231 below and by
    # tests/test_v1231_limits.py. In-process python sqlite access above
    # stays denied (arbitrary code, not a lexical read shape).
])
def test_echo_read_lane_adversaries_stay_out(config, command):
    result = _classify(command, config)
    assert result.category != "read_only", (command, result)


def test_sqlite_read_lane_boundary_v1231(config):
    """v1.2.31: single-statement read-verb SQL against a policy-controlled
    store is a read; every other sqlite3 shape stays out of the read lane."""
    board_db = "C:/x/" + "kan" + "ban.db"
    allowed = _classify(f'sqlite3 {board_db} "SELECT body FROM tasks"', config)
    assert (allowed.effect, allowed.decision, allowed.category) == (
        "read", "allow", "read_only",
    ), allowed
    for command in (
        f'sqlite3 {board_db} "DELETE FROM tasks"',
        f'sqlite3 {board_db} "SELECT 1; DELETE FROM tasks"',
        f'sqlite3 {board_db} ".dump"',
        f'sqlite3 {board_db}',
        f'sqlite3 {board_db} "PRAGMA journal_mode=delete"',
    ):
        assert _classify(command, config).category != "read_only", command


def test_policy_controlled_write_still_hard_denied(config):
    """The mutation side of the guard is untouched by this change."""
    result = classify(
        "write_file", {"path": f"config/{CFG_NAME}", "content": "x"}, config, worker=True
    )
    assert result.decision == "deny"
    assert result.category == "policy_control_plane_mutation"
