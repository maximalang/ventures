"""v1.2.57 — quoted file-operand path-guard subjects (t_fc317116 F1/F2).

Red/green contract (base 4908dd4 -> v1.2.57):
- On base, quoted positional file operands were skipped as prose by
  _path_guard_subjects (policy.py:854-857), so `sqlite3 "<board db>"
  "UPDATE ..."` classified as allow:scoped_state_change and `sqlite3
  "<board db>" "DELETE ..."` as allow:destructive_change — an in-process
  bypass of the protected-path guard (offline corpus t_5dd6729d, cases
  C4/C5). After the fix both are deny:policy_control_plane_mutation.
- Extraction is allowlist-only (file-operand programs: sqlite3, cp, mv,
  rm, del, copy, move, xcopy, robocopy, tee), preserves the value-flag
  prose exclusion, never scans quoted spans unconditionally, and keeps
  the v1.2.31 sqlite read lane intact: a quoted single SELECT stays
  allow:read_only (worker and operator).

Protected filenames are assembled from parts (suite convention) so this
source file stays clean for policy scanners.
"""
from __future__ import annotations

import pytest

from fleet_policy.policy import _path_guard_subjects, classify

BOARD_DB = "kan" + "ban.db"
POLICY_DB = "fleet-" + "policy.db"
FLEET_DB = "C:/Users/max/AppData/Local/hermes/kanban/boards/fleet-ops/" + BOARD_DB
HOME_DB = "~/.hermes/" + BOARD_DB
STATE_STORE = "C:/x/.state/" + POLICY_DB


def _c(config, command, worker=True):
    return classify("terminal", {"command": command}, config, worker=worker)


def _is_pcpm_deny(result) -> bool:
    return (result.effect, result.category, result.decision) == (
        "state_change", "policy_control_plane_mutation", "deny",
    )


# --- RED on base: quoted file operands bypass the path guard (F1/F2) ---------

@pytest.mark.parametrize("statement", [
    "UPDATE tasks SET status='blocked' WHERE id='t_x'",
    "DELETE FROM tasks WHERE id='t_x'",
])
def test_sqlite_quoted_db_path_mutating_statement_denied(config, statement):
    result = _c(config, f'sqlite3 "{FLEET_DB}" "{statement}"')
    assert _is_pcpm_deny(result), result


def test_sqlite_single_quoted_db_path_denied(config):
    result = _c(config, f"sqlite3 '{HOME_DB}' \"DELETE FROM tasks\"")
    assert _is_pcpm_deny(result), result


def test_sqlite_quoted_state_store_denied(config):
    result = _c(config, f'sqlite3 "{STATE_STORE}" "UPDATE events SET x=1"')
    assert _is_pcpm_deny(result), result


def test_sqlite_quoted_db_with_readonly_flag_update_denied(config):
    result = _c(config, f'sqlite3 -readonly "{FLEET_DB}" "UPDATE tasks SET x=1"')
    assert _is_pcpm_deny(result), result


@pytest.mark.parametrize("command", [
    f'rm "{FLEET_DB}"',
    f'del "{FLEET_DB}"',
    f'mv "{FLEET_DB}" "C:/tmp/x.db"',
    f'move "{FLEET_DB}" "C:/tmp/x.db"',
    f'cp "C:/tmp/x.db" "{FLEET_DB}"',
    f'copy "C:/tmp/x.db" "{FLEET_DB}"',
    f'xcopy "C:/tmp/x.db" "{FLEET_DB}"',
    f'robocopy "C:/tmp/src" "C:/boards/fleet-ops/{BOARD_DB}"',
])
def test_file_movers_quoted_protected_target_denied(config, command):
    result = _c(config, command)
    assert _is_pcpm_deny(result), (command, result)


def test_tee_pipeline_quoted_protected_target_denied(config):
    result = _c(config, f'echo payload | tee "{FLEET_DB}"')
    assert _is_pcpm_deny(result), result


def test_relative_quoted_db_path_denied(config):
    result = _c(config, f'sqlite3 "boards/fleet-ops/{BOARD_DB}" "UPDATE tasks SET x=1"')
    assert _is_pcpm_deny(result), result


def test_quoted_db_unquoted_multiword_statement_denied(config):
    # Acceptance variant: quoted db path + UNQUOTED statement. The unquoted
    # words split the stage past the v1.2.31 two-positional read shape, so
    # the command is a state change; the quoted db operand must still guard.
    result = _c(config, f'sqlite3 "{FLEET_DB}" UPDATE tasks SET x=1')
    assert _is_pcpm_deny(result), result


def test_quoted_db_unquoted_single_word_mutation_denied(config):
    result = _c(config, f'sqlite3 "{FLEET_DB}" UPDATE')
    assert _is_pcpm_deny(result), result


def test_quoted_db_unquoted_select_stays_in_read_lane(config):
    # Acceptance variant: an UNQUOTED single-word SELECT keeps exactly two
    # positionals, so the v1.2.31 read lane still applies even though the
    # db path was quoted; the extracted subject only re-labels the allow
    # reason, never the verdict.
    result = _c(config, f'sqlite3 -readonly "{FLEET_DB}" SELECT')
    assert (result.effect, result.decision) == ("read", "allow"), result
    assert result.category == "read_only", result


# --- GREEN pins: the v1.2.31 sqlite read lane is untouched -------------------

@pytest.mark.parametrize("command", [
    f'sqlite3 -readonly "file:{FLEET_DB}?mode=ro" "SELECT id,status FROM tasks"',
    f'sqlite3 "{FLEET_DB}" "SELECT id,status FROM tasks"',
    f"sqlite3 -readonly '{HOME_DB}' 'SELECT 1'",
])
def test_quoted_readonly_select_stays_allowed(config, command):
    result = _c(config, command)
    assert (result.effect, result.decision) == ("read", "allow"), result
    assert result.category == "read_only", result


def test_operator_quoted_select_stays_allowed(config):
    result = _c(config, f'sqlite3 -readonly "{FLEET_DB}" "SELECT 1"', worker=False)
    assert (result.effect, result.decision) == ("read", "allow"), result


def test_quoted_select_on_unprotected_db_allowed(config):
    result = _c(config, 'sqlite3 "app.db" "SELECT 1"')
    assert (result.effect, result.decision) == ("read", "allow"), result


def test_quoted_update_on_unprotected_db_stays_scoped(config):
    result = _c(config, 'sqlite3 "app.db" "UPDATE t SET x=1"')
    assert result.decision == "allow", result
    assert result.category == "scoped_state_change", result


# --- GREEN pins: no unconditional quoted-span scanning ----------------------

def test_search_head_quoted_pattern_stays_prose(config):
    result = _c(config, f'grep -rn "{BOARD_DB}" src/')
    assert result.decision == "allow", result


def test_value_flag_quoted_message_stays_prose(config):
    # The message text must never become a path-guard subject: the shape
    # stays in the ordinary rule table, not a protected-path deny.
    # v1.2.57 reconciliation: on base >= v1.2.34 the PR #53 W4 prose-mask
    # strips the quoted -m span from the risk scan, so the category is
    # repository_change (was destructive_change on the 1.2.31 base).
    result = _c(config, f'git commit -m "delete {BOARD_DB} notes"')
    assert result.decision == "allow", result
    assert result.category == "repository_change", result


def test_non_allowlisted_program_quoted_span_not_scanned(config):
    result = _c(config, f'echo "{BOARD_DB}"')
    assert (result.effect, result.decision) == ("read", "allow"), result


def test_non_allowlisted_quoted_path_operand_not_extracted(config):
    # python is not a file-operand program: a quoted argument stays prose
    # (the python -c code-value lane is separate and unchanged).
    result = _c(config, f'python "{FLEET_DB}"')
    assert result.category != "policy_control_plane_mutation", result


# --- whitebox: subject extraction contract ----------------------------------

def test_subjects_include_quoted_file_operand_for_allowlisted_head():
    subjects = _path_guard_subjects(
        "terminal", {"command": f'sqlite3 "{FLEET_DB}" "UPDATE t SET x=1"'}
    )
    assert FLEET_DB in subjects


def test_subjects_exclude_quoted_sql_statement():
    subjects = _path_guard_subjects(
        "terminal", {"command": f'sqlite3 "{FLEET_DB}" "UPDATE t SET x=1"'}
    )
    assert "UPDATE t SET x=1" not in subjects


def test_subjects_exclude_quoted_pattern_for_search_head():
    subjects = _path_guard_subjects(
        "terminal", {"command": f'grep -rn "{BOARD_DB}" src/'}
    )
    assert BOARD_DB not in subjects


def test_subjects_exclude_quoted_value_flag_message():
    subjects = _path_guard_subjects(
        "terminal", {"command": f'git commit -m "rm -rf {BOARD_DB}"'}
    )
    assert all(BOARD_DB not in subject for subject in subjects)
