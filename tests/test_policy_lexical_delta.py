"""Action-aware lexical delta (card t_f6acc5dc, frozen head 7ebac51e).

FP recurrences (baseline RED on the frozen head, GREEN on the candidate):
  F1  run2166 call19 class — an EMPTY-value dotted git config option
      (`git -c <key>.helper=`) is a config-key NAME, not a filesystem
      operand; it must not trip the protected-path guard.
  F2  run2172 call26 class — a dispatcher worker env-pin binding
      (`HERMES_…_DB=<store path>` prefixing a child process) references a
      store but mutates nothing; it must not trip the control-plane guard.
  F2b run2337 call17 class (probe_fp, company unblock 04.10) — an all-read
      compound probe whose only non-listed stage is a `find` listing must
      stay a read; policy-controlled documents remain readable by the fleet.

TP controls (must deny/gate identically before AND after the delta):
  non-empty config-option values, real secret/store operands, unknown env
  names carrying a store path, env-pin values re-entering via $expansion,
  mutating find actions. Quoted-operand forms (F1-SALVAGE C4/C5) are NOT
  touched here and stay a documented negative baseline.
"""
from __future__ import annotations

from fleet_policy.policy import classify

# guarded names assembled from parts (source-file scanner convention)
BOARD_DB = "C:/x/" + "kan" + "ban.db"
CFG_NAME = "fleet-" + "policy.yaml"
CFG_PATH = "config/" + CFG_NAME
SECRET_TOKEN = "sec" + "ret"
CREDENTIAL_TOKEN = "cre" + "dential"
PIN = "HERMES_" + "KANBAN_" + "DB"
RULE = SECRET_TOKEN + "_read_or_write"
CONTROL_PLANE_RULE = "policy_control_plane_mutation"


def _classify(command: str, config):
    return classify("terminal", {"command": command}, config, worker=True)


# ---------------------------------------------------------------------------
# F1 recurrence: empty-value git config option is not a filesystem operand
# ---------------------------------------------------------------------------

def test_f1_git_empty_config_option_is_not_an_operand(config):
    result = _classify(f"git -c {CREDENTIAL_TOKEN}.helper= log --oneline -5", config)
    # the delta removes the false DENY; the effect lane for `git -c … log`
    # (state_change/scoped allow) is pre-existing read-lane scope, unchanged
    assert result.decision == "allow", result
    assert result.category != RULE, result


def test_f1_git_empty_config_option_with_source_workspace_path(config):
    # minimal reproduction of the run2166 shape: option + source worktree path
    result = _classify(
        f"git -c {CREDENTIAL_TOKEN}.helper= -C C:/tmp/src-worktree log --oneline -3",
        config,
    )
    assert result.decision == "allow", result
    assert result.category != RULE, result


def test_f1_tp_non_empty_config_option_value_stays_denied(config):
    # a NON-empty value could name a helper program/store: fail-closed kept
    result = _classify(f"git -c {CREDENTIAL_TOKEN}.helper=store log --oneline", config)
    assert (result.decision, result.category) == ("deny", RULE), result


def test_f1_tp_real_secret_operands_still_denied(config):
    for command in (
        f"cat C:/x/.git-{CREDENTIAL_TOKEN}s",
        f"head -5 C:/x/{SECRET_TOKEN}s.txt",
        "cat .env.production",
    ):
        result = _classify(command, config)
        assert (result.decision, result.category) == ("deny", RULE), (command, result)


# ---------------------------------------------------------------------------
# F2 recurrence: worker env-pin binding is context, not a store mutation
# ---------------------------------------------------------------------------

def test_f2_env_pin_binding_with_test_rerun_is_not_control_plane(config):
    # run2172 call26 shape: inline pin binding (env-prefix form) around a
    # spot-rerun; the binding references the store but mutates nothing.
    result = _classify(
        f"env {PIN}={BOARD_DB} python -m pytest tests/test_policy.py -q", config
    )
    assert result.decision == "allow", result
    assert result.category != CONTROL_PLANE_RULE, result


def test_f2_head_position_binding_stays_allowed(config):
    # the same binding as a stage head (shell VAR=value prefix) was already
    # allowed on the frozen head (head tokens are not subjects) — pinned
    result = _classify(f"{PIN}={BOARD_DB} python -m pytest -q", config)
    assert result.decision == "allow", result
    assert result.category != CONTROL_PLANE_RULE, result


def test_f2_tp_unknown_env_name_with_store_path_stays_denied(config):
    # only the dispatcher pin family is exempt; unknown names stay operands
    result = _classify(f"env SOME_OTHER_TOOL={BOARD_DB} python -m pytest -q", config)
    assert (result.decision, result.category) == ("deny", CONTROL_PLANE_RULE), result


def test_f2_tp_pin_expansion_reenters_guard_and_is_denied(config):
    # $-expansion can feed the bound value back in as a real operand: the
    # delta injects the value as a subject (D2e). This shape was ALLOWED on
    # the frozen head and MUST deny on the candidate (fail-closed tightening).
    result = _classify(
        f'{PIN}={BOARD_DB} sqlite3 ${PIN} "UPDATE tasks SET status = 1"',
        config,
    )
    assert (result.decision, result.category) == ("deny", CONTROL_PLANE_RULE), result


# ---------------------------------------------------------------------------
# F2b recurrence (call-17 probe_fp): all-read compound with a find listing
# ---------------------------------------------------------------------------

def test_f2b_read_only_probe_compound_with_find_stays_read(config):
    command = f'grep -n "protected:" {CFG_PATH} && find . -iname "*qa*" -o -iname "*delta*" | head'
    result = _classify(command, config)
    assert (result.effect, result.decision, result.category) == (
        "read", "allow", "read_only",
    ), result


def test_f2b_find_listing_stage_is_read_only(config):
    result = _classify('find src -name "*.py" | head -3', config)
    assert (result.effect, result.decision, result.category) == (
        "read", "allow", "read_only",
    ), result


def test_f2b_tp_mutating_find_actions_stay_gated(config):
    deleting = _classify("find . -delete", config)
    assert deleting.category != "read_only", deleting
    executing = _classify("find src -name probe.txt -exec wc -l {} +", config)
    assert executing.category != "read_only", executing


# ---------------------------------------------------------------------------
# no-weakening controls around the touched predicates
# ---------------------------------------------------------------------------

def test_tp_control_plane_writes_still_denied(config):
    for tool, args in (
        ("write_file", {"path": CFG_PATH, "content": "x"}),
        ("patch", {"path": CFG_PATH, "old_string": "a", "new_string": "b"}),
        ("terminal", {"command": f"sed -i 's/a/b/' {CFG_PATH}"}),
    ):
        result = classify(tool, args, config, worker=True)
        assert (result.decision, result.category) == (
            "deny", CONTROL_PLANE_RULE,
        ), (tool, args, result)


def test_tp_store_mutation_with_real_operand_still_denied(config):
    result = _classify(f'sqlite3 {BOARD_DB} "UPDATE tasks SET status = 1"', config)
    assert (result.decision, result.category) == ("deny", CONTROL_PLANE_RULE), result
