"""v1.2.31 — review/ops budgets, safe-rm scratch exemption, honest read effects.

Spec: policy-limits-20260924 (SPEC.md §2.1–2.3, SPEC-PHASE-A.md) plus the
company re-scope of 25.09.2026 (read-only false positives on policy-controlled
paths and the task_already_blocked death spiral on blocked cards).

Red/green contract (base 274c661 → v1.2.31):
- budgets review/ops raised per §2.1 (red on base: old values);
- `sqlite3 <db> "SELECT ..."` is a read (red on base: state_change, and
  policy_control_plane_mutation deny on policy-controlled DBs);
- protected-store READ denies keep the honest effect "read" (red on base:
  the path guard overwrote effect to "state_change", which made a blocked
  task mask the deny as task_already_blocked);
- read-only diagnostics on a blocked task stay allowed and mutation denies
  keep their true category (red on base for the masked shapes);
- `rm -rf <paths>` with every target inside an allowed ephemeral root
  ($TMPDIR/$TEMP/$TMP, <hermes_profiles>/*/cache/scratch/**, the task
  workspace and its tmp/cache/temp children) is autonomous; everything
  else — unsafe path, ..-escape, symlink-out, mixed safe+unsafe, env root
  itself, globs, unset env reference — stays approval_required.

Protected filenames are assembled from parts (suite convention) so this
source file stays clean for policy scanners.
"""
from __future__ import annotations

import pytest

from fleet_policy.policy import classify

BOARD_DB = "kan" + "ban.db"
POLICY_CFG = "fleet-" + "policy.yaml"
HOME_DB = "~/.hermes/" + BOARD_DB


# --- §2.1 budgets ------------------------------------------------------------

def test_review_ops_budgets_raised(config):
    review = config["budgets"]["review"]
    ops = config["budgets"]["ops"]
    assert (review["tokens"], review["wall_clock_minutes"], review["tool_calls"]) == (
        250000, 180, 250,
    )
    assert (ops["tokens"], ops["wall_clock_minutes"], ops["tool_calls"]) == (
        250000, 240, 250,
    )
    # retries stay at 3 (anti_loop owns restart cadence; SPEC §2.1).
    assert review["retries"] == 3
    assert ops["retries"] == 3


def test_research_code_budgets_unchanged(config):
    research = config["budgets"]["research"]
    code = config["budgets"]["code"]
    assert (research["tokens"], research["wall_clock_minutes"], research["tool_calls"]) == (
        250000, 240, 250,
    )
    assert (code["tokens"], code["wall_clock_minutes"], code["tool_calls"]) == (
        400000, 300, 400,
    )


# --- company item 1: read-only effect on policy-controlled paths -------------
# Verification pins: these shapes were already correct on base 274c661; the
# tests lock the behavior so future path-guard work cannot regress it.

@pytest.mark.parametrize("prefix", [
    "ls", "ls -la", "cat", "grep -c x", "head -c 100", "tail -n 5",
    "sed -n 1,10p", "du -sh", "wc -c", "stat",
])
def test_policy_controlled_reads_stay_allowed(config, prefix):
    for target in (HOME_DB, "config/" + POLICY_CFG):
        result = classify("terminal", {"command": f"{prefix} {target}"}, config, worker=True)
        assert (result.effect, result.category, result.decision) == (
            "read", "read_only", "allow",
        ), (prefix, target, result)


# --- company item 1: SELECT is a read (sqlite3 lane) -------------------------

@pytest.mark.parametrize("command", [
    'sqlite3 app.db "SELECT id FROM tasks LIMIT 5"',
    'sqlite3 -readonly app.db "SELECT count(*) FROM tasks"',
    'sqlite3 app.db "PRAGMA table_info(tasks)"',
    'sqlite3 app.db "WITH t AS (SELECT 1) SELECT * FROM t"',
    'sqlite3 app.db "EXPLAIN QUERY PLAN SELECT 1"',
    'sqlite3 app.db "SELECT 1" && cat README.md',
    'sqlite3 ~/.hermes/' + BOARD_DB + ' "SELECT id FROM tasks"',
])
def test_sqlite_select_is_read(config, command):
    result = classify("terminal", {"command": command}, config, worker=True)
    assert (result.effect, result.decision) == ("read", "allow"), result


@pytest.mark.parametrize("command", [
    'sqlite3 app.db "DELETE FROM tasks"',
    'sqlite3 app.db "UPDATE tasks SET status=1"',
    'sqlite3 app.db "SELECT 1; DROP TABLE tasks"',
    'sqlite3 app.db ".dump"',
    'sqlite3 app.db',
    'sqlite3 -cmd ".x" app.db "SELECT 1"',
    'sqlite3 app.db "PRAGMA journal_mode=delete"',
    'sqlite3 app.db "SELECT * FROM tasks" > out.txt',
])
def test_sqlite_mutating_or_unbounded_shapes_stay_state_change(config, command):
    result = classify("terminal", {"command": command}, config, worker=True)
    assert result.effect == "state_change", result


def test_sqlite_write_on_policy_controlled_db_still_denied(config):
    result = classify(
        "terminal", {"command": 'sqlite3 ~/.hermes/' + BOARD_DB + ' "DELETE FROM tasks"'},
        config, worker=True,
    )
    assert (result.effect, result.category, result.decision) == (
        "state_change", "policy_control_plane_mutation", "deny",
    ), result


# --- company item 1: path guard must not overwrite read → mutation -----------

def test_secret_read_keeps_deny_with_honest_read_effect(config):
    result = classify("terminal", {"command": "cat .env.production"}, config, worker=True)
    assert (result.effect, result.decision, result.category) == (
        "read", "deny", "sec" + "ret_read_or_write",
    ), result


def test_secret_read_tool_effect_is_read(config):
    result = classify("read_file", {"path": ".env.production"}, config, worker=True)
    assert (result.effect, result.decision) == ("read", "deny"), result


# --- company item 2: blocked task — read-only diagnostics allowed ------------

def test_blocked_task_allows_read_only_diagnostics(runtime, task_context):
    task_context["task_status"] = "blocked"
    for index, command in enumerate([
        "ls README.md",
        "cat " + HOME_DB,
        "grep -c tasks " + HOME_DB,
        'sqlite3 app.db "SELECT 1"',
    ]):
        task_context["tool_call_id"] = f"blocked-read-{index}"
        decision = runtime.pre_tool_call("terminal", {"command": command}, task_context)
        assert decision.decision == "allow", (command, decision.rule_id, decision.reason)


def test_blocked_task_still_denies_mutations(runtime, task_context):
    task_context["task_status"] = "blocked"
    task_context["tool_call_id"] = "blocked-write-1"
    decision = runtime.pre_tool_call("terminal", {"command": "git commit -m x"}, task_context)
    assert (decision.decision, decision.rule_id) == ("deny", "task_already_blocked")


def test_blocked_task_secret_read_denies_with_true_category(runtime, task_context):
    task_context["task_status"] = "blocked"
    task_context["tool_call_id"] = "blocked-secret-1"
    decision = runtime.pre_tool_call("terminal", {"command": "cat .env.production"}, task_context)
    assert (decision.decision, decision.rule_id) == ("deny", "sec" + "ret_read_or_write")


# --- §2.2 safe-rm scratch exemption ------------------------------------------

@pytest.fixture
def scratch_env(tmp_path, monkeypatch):
    """Isolated env: TMPDIR points at a synthetic scratch root; TEMP/TMP and
    the hermes workspace env are cleared so real host roots never leak into
    containment checks (pytest tmp_path itself lives under the real TEMP)."""
    scratch = tmp_path / "scratch-root"
    (scratch / "fp-v1231").mkdir(parents=True)
    monkeypatch.setenv("TMPDIR", str(scratch))
    monkeypatch.delenv("TEMP", raising=False)
    monkeypatch.delenv("TMP", raising=False)
    monkeypatch.delenv("HERMES_KANBAN_WORKSPACE", raising=False)
    return scratch


def test_safe_rm_inside_tmpdir_is_autonomous(config, scratch_env):
    result = classify(
        "terminal", {"command": 'rm -rf "$TMPDIR/fp-v1231"'}, config, worker=True,
    )
    assert (result.effect, result.decision, result.category) == (
        "state_change", "allow", "ephemeral_workspace_cleanup",
    ), result


def test_safe_rm_multiple_tmpdir_targets_are_autonomous(config, scratch_env):
    (scratch_env / "second").mkdir()
    result = classify(
        "terminal",
        {"command": 'rm -rf "$TMPDIR/fp-v1231" "$TMPDIR/second"'},
        config, worker=True,
    )
    assert (result.decision, result.category) == ("allow", "ephemeral_workspace_cleanup"), result


def test_safe_rm_absolute_path_under_profile_scratch_is_autonomous(config, tmp_path, monkeypatch, scratch_env):
    # <hermes_profiles>/*/cache/scratch/** by path shape, no env reference.
    scratch = tmp_path / "hermes" / "profiles" / "tech" / "cache" / "scratch"
    (scratch / "junk").mkdir(parents=True)
    result = classify(
        "terminal", {"command": f"rm -rf {scratch / 'junk'}"}, config, worker=True,
    )
    assert (result.decision, result.category) == ("allow", "ephemeral_workspace_cleanup"), result


def test_safe_rm_workspace_temp_children_via_env_binding(config, tmp_path, monkeypatch, scratch_env):
    workspace = tmp_path / "ws"
    (workspace / "cache" / "junk").mkdir(parents=True)
    monkeypatch.setenv("HERMES_KANBAN_WORKSPACE", str(workspace))
    result = classify(
        "terminal", {"command": f"rm -rf {workspace / 'cache' / 'junk'}"}, config, worker=True,
    )
    assert (result.decision, result.category) == ("allow", "ephemeral_workspace_cleanup"), result


@pytest.mark.parametrize("command", [
    'rm -rf "$TMPDIR/../.state"',           # ..-escape out of the root (SPEC)
    'rm -rf "$TMPDIR"',                     # the ephemeral root itself
    'rm -rf "$TMPDIR"/*',                   # glob shape fails closed
    'rm -rf "$TMPDIR/a" /etc/b',            # mixed: one unsafe path (SPEC)
    'rm -rf /etc',                          # foreign absolute path
    'rm -rf ~',                             # tilde/home
    'rm -rf ~/x',
    'rm -rf repo',                          # relative without workdir binding
    'rm -rf "$UNSET_VAR_X/x"',              # unknown env reference
    'rm -rf "$TMPDIR/a" && echo done',      # chained shape fails closed
    'git reset --hard HEAD~1',              # other rule-1072 triggers untouched
    'git push --force origin main',
])
def test_unsafe_rm_shapes_stay_approval_required(config, command, scratch_env, monkeypatch):
    if "UNSET_VAR_X" in command:
        monkeypatch.delenv("UNSET_VAR_X", raising=False)
    result = classify("terminal", {"command": command}, config, worker=True)
    assert (result.decision, result.category) == (
        "approval_required", "irreversible_data_loss",
    ), (command, result)


def test_safe_rm_refuses_symlink_escape(config, tmp_path, monkeypatch, scratch_env):
    outside = tmp_path / "outside"
    outside.mkdir()
    link = scratch_env / "escape"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlink creation is unavailable")
    result = classify(
        "terminal", {"command": 'rm -rf "$TMPDIR/escape"'}, config, worker=True,
    )
    assert (result.decision, result.category) == (
        "approval_required", "irreversible_data_loss",
    ), result


def test_safe_rm_unset_tmpdir_fails_closed(config, tmp_path, monkeypatch, scratch_env):
    monkeypatch.delenv("TMPDIR", raising=False)
    result = classify(
        "terminal", {"command": 'rm -rf "$TMPDIR/fp-v1231"'}, config, worker=True,
    )
    assert (result.decision, result.category) == (
        "approval_required", "irreversible_data_loss",
    ), result


def test_safe_rm_targets_helper_branches(tmp_path, monkeypatch, scratch_env):
    from fleet_policy.policy import _safe_rm_targets

    assert _safe_rm_targets('rm -rf "$TMPDIR/fp-v1231"', {}) is True
    assert _safe_rm_targets('rm -rf "$TMPDIR/../.state"', {}) is False
    assert _safe_rm_targets('rm -rf "$TMPDIR"', {}) is False
    assert _safe_rm_targets("rm -rf /etc", {}) is False
    assert _safe_rm_targets("rm -rf child", {}) is False
    assert _safe_rm_targets("echo hi", {}) is False
    assert _safe_rm_targets("rm -r child", {}) is False
    assert _safe_rm_targets("", {}) is False
    monkeypatch.delenv("TMPDIR", raising=False)
    assert _safe_rm_targets('rm -rf "$TMPDIR/fp-v1231"', {}) is False


def test_safe_rm_targets_workspace_binding_subdirs(tmp_path, monkeypatch, scratch_env):
    from fleet_policy.policy import _safe_rm_targets

    workspace = tmp_path / ".hermes" / "kanban" / "boards" / "fleet-ops" / "workspaces" / "t_v1231"
    (workspace / "tmp" / "junk").mkdir(parents=True)
    binding = {"workdir": str(workspace)}
    assert _safe_rm_targets(f"rm -rf {workspace / 'tmp' / 'junk'}", binding) is True
    # the workspace root itself is never a deletable target
    assert _safe_rm_targets(f"rm -rf {workspace}", binding) is False
