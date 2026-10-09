"""v1.2.43 — read-lane false-positive fixes for the sqlite3/fd-dup shapes.

Card: fleet-ops t_40022daf. Live incident evidence (policy event-store,
ventures .state/fleet-policy.db):

- event f3b2e0d2cd9e0edaedaccbbaa88849fd7fa1b2703ce03f4ab4222876c09578ba
  (2026-10-08T14:13:22Z, task t_40022daf call 41): a READ-ONLY sqlite3
  `mode=ro` SELECT whose FTS query text contained a risk keyword was
  classified effect=state_change -> irreversible_data_loss ->
  approval_required. The quoted span was never masked because sqlite3 sits
  in _INTERPRETER_PROGRAMS (its SQL argument is treated as code), so the
  ONLY protection is the read-lane itself — and the read-lane rejected the
  command for three independent lexical reasons fixed here.

Root causes under test:
- A: `_sqlite_stage_is_read_only` rejected any statement containing `;`,
  including the standard single trailing statement terminator.
- B: `_SHELL_METACHARACTERS` matched the `&` inside fd duplication
  (`2>&1`), contradicting its own comment — every read pipeline with
  stderr redirection failed closed into state_change and the keyword
  rules.
- C: the fd-duplication token (`2>&1`) consumed a positional slot in the
  sqlite lane, so exactly-two-positionals validation failed.

Security invariants pinned here (must NOT regress):
- write SQL via sqlite3 (`drop table`, multi-statement chains) stays
  escalated;
- shell backgrounding (`cmd &`) and write-both redirect (`&> file`) stay
  fail-closed;
- interpreter code strings (`python -c ...`) keep their nested literals
  scanned — prompt data embedded in code is NOT masked (evasion guard).
"""

from __future__ import annotations

from fleet_policy.policy import classify


READ = ("read", "read_only", "allow")


def _classify(config, command: str):
    result = classify("terminal", {"command": command}, config, worker=True)
    return result.effect, result.category, result.decision


# --- RED (fixed by v1.2.43) ---------------------------------------------


def test_sqlite_ro_select_trailing_semicolon_stays_read(config):
    command = 'sqlite3 "file:C:/x/state.db?mode=ro" "SELECT COUNT(*) FROM events;"'
    assert _classify(config, command) == READ


def test_sqlite_ro_select_keyword_in_quoted_sql_stays_read(config):
    # The exact 2026-10-08 incident shape (event f3b2e0d2...): a risk
    # keyword inside the FTS query literal must not escalate a read.
    command = (
        'sqlite3 "file:C:/x/state.db?mode=ro" "SELECT substr(m.content,1,200) '
        "FROM messages_fts f JOIN messages m ON m.rowid=f.rowid "
        "WHERE messages_fts MATCH 't_x irreversible' LIMIT 3;\" 2>&1 | head -10"
    )
    assert _classify(config, command) == READ


def test_sqlite_ro_pragma_trailing_semicolon_stays_read(config):
    command = 'sqlite3 "file:C:/x/db.db?mode=ro" "PRAGMA index_list(\'events\');"'
    assert _classify(config, command) == READ


def test_read_pipeline_with_fd_duplication_stays_read(config):
    assert _classify(config, "ls -la src/ 2>&1 | head -5") == READ


def test_chained_read_with_fd_duplication_stays_read(config):
    command = "grep -rn deploy src/ 2>&1 | head -5 && ls tests/"
    assert _classify(config, command) == READ


def test_grep_bare_mutator_keyword_stays_read(config):
    # v1.2.22 covered the quoted form only; the bare pattern hit the same
    # literal trap through the MUTATOR scan.
    assert _classify(config, "grep -rn deploy src/") == READ


def test_grep_bare_mutator_keyword_with_pipe_stays_read(config):
    assert _classify(config, "grep -rn publish src/ 2>&1 | head -5") == READ


def test_rg_bare_mutator_keyword_stays_read(config):
    assert _classify(config, "rg deploy") == READ


def test_find_name_value_stays_read(config):
    assert _classify(config, "find . -name deploy") == READ


def test_find_mutating_primary_stays_closed(config):
    effect, _category, _decision = _classify(config, "find . -delete")
    assert effect == "state_change"


def test_grep_with_file_redirect_stays_closed(config):
    effect, _category, _decision = _classify(config, "grep deploy src/ > out.txt")
    assert effect == "state_change"


# --- TP: write SQL stays escalated ---------------------------------------


def test_sqlite_drop_table_stays_escalated(config):
    effect, category, decision = _classify(
        config, 'sqlite3 app.db "drop table users;"'
    )
    assert effect == "state_change"
    assert category == "irreversible_data_loss"
    assert decision == "approval_required"


def test_sqlite_multi_statement_chain_is_not_read(config):
    effect, category, _decision = _classify(
        config, 'sqlite3 "file:C:/x/db.db?mode=ro" "SELECT 1; drop table users;"'
    )
    assert effect == "state_change"
    assert category == "irreversible_data_loss"


def test_sqlite_double_semicolon_is_not_read(config):
    effect, _category, _decision = _classify(
        config, 'sqlite3 "file:C:/x/db.db?mode=ro" "SELECT 1;;"'
    )
    assert effect == "state_change"


def test_sqlite_dot_command_is_not_read(config):
    effect, _category, _decision = _classify(
        config, 'sqlite3 "file:C:/x/db.db?mode=ro" ".backup other.db"'
    )
    assert effect == "state_change"


# --- TP: shell write/background forms stay fail-closed -------------------


def test_background_job_still_fails_closed(config):
    effect, _category, _decision = _classify(config, "ls src/ &")
    assert effect == "state_change"


def test_write_both_redirect_still_fails_closed(config):
    effect, _category, _decision = _classify(config, "ls src/ &> listing.txt")
    assert effect == "state_change"


def test_file_redirect_still_fails_closed(config):
    effect, _category, _decision = _classify(config, "echo hi > /tmp/x.txt")
    assert effect == "state_change"


def test_background_after_fd_dup_still_fails_closed(config):
    effect, _category, _decision = _classify(config, "ls src/ 2>&1 &")
    assert effect == "state_change"


# --- Anti-evasion pin: interpreter code strings stay scanned --------------


def test_python_c_embedded_prompt_keyword_stays_escalated(config):
    # t_3d503c82 class: a natural-language prompt embedded in `python -c`
    # still trips the keyword scan. The sanctioned lane for prompt-heavy
    # runners is a script file via write_file + `python file.py` — file
    # contents are data, command strings are not. Masking nested literals
    # inside code would open an evasion vector (os.system('...')).
    command = (
        'python -c "import subprocess\n'
        "prompt = '''QA prompt: flag irreversible operations.'''\n"
        'print(len(prompt))"'
    )
    effect, category, decision = _classify(config, command)
    assert effect == "state_change"
    assert category == "irreversible_data_loss"
    assert decision == "approval_required"


def test_python_c_os_system_evasion_stays_escalated(config):
    # Inert classifier input: this string is never executed, only classified.
    # v1.2.43 widened the rm-lookbehind with quote chars, closing the
    # quote-adjacent evasion inside code spans (`os.system('rm -rf ...')`
    # previously slipped through as scoped_state_change/allow).
    command = "python -c \"import os; os.system('rm -rf /tmp/xyz')\""
    effect, category, decision = _classify(config, command)
    assert effect == "state_change"
    assert category == "irreversible_data_loss"
    assert decision == "approval_required"


def test_bash_c_rm_rf_evasion_stays_escalated(config):
    command = "bash -c 'rm -rf /tmp/xyz'"
    effect, category, decision = _classify(config, command)
    assert effect == "state_change"
    assert category == "irreversible_data_loss"
    assert decision == "approval_required"


# --- Existing TP controls (re-pinned for this fix's blast radius) ---------


def test_rm_rf_stays_escalated(config):
    _effect, category, decision = _classify(config, "cd /tmp && rm -rf target-dir")
    assert category == "irreversible_data_loss"
    assert decision == "approval_required"


def test_force_push_stays_escalated(config):
    _effect, category, decision = _classify(config, "git push -f origin feature-x")
    assert category == "irreversible_data_loss"
    assert decision == "approval_required"


def test_reset_hard_stays_escalated(config):
    _effect, category, decision = _classify(config, "git reset --hard HEAD~3")
    assert category == "irreversible_data_loss"
    assert decision == "approval_required"
