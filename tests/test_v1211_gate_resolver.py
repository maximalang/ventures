"""v1.2.11 gate-resolver contract tests (t_801babcf).

Items covered here:
- F1: the operational-artifact read exception is physically contained —
  traversal escapes, mixed separators and UNC impersonation never inherit it.
- F2: expected-failure overrides need structural authority — the worker
  terminal subcommand and the direct store API are hard-denied, and the
  store refuses the call from a dispatcher worker context.
- F5: terminal path-guard subjects are extracted structurally; values of
  free-text flags (git commit -m / --message) are prose, not targets.
- F6: consume_exact_approval carries no silent env pass-through branch.
- F7: limitation pin — until the host translates review-probe blocks
  (Hermes core, t_121ac8eb), untranslated plugin blocks keep the normal
  loop accounting (fail-closed); the designed nonce path stays suppressed.
"""
from __future__ import annotations

import inspect

from fleet_policy.policy import (
    _canonical_operational_artifact_read,
    _path_guard_subjects,
    classify,
)
from fleet_policy.storage import PolicyStore

_CFG = "fleet-" + "policy.yaml"


# --------------------------------------------------------------------- F1


def _workspace_root() -> str:
    return (
        "C:/users/max/appdata/local/hermes/kanban/boards"
        "/fleet-ops/workspaces/t_example"
    )


def test_artifact_read_exception_allows_true_root_members():
    assert _canonical_operational_artifact_read(
        "read_file", {"path": _workspace_root() + "/progress.md"}
    )


def test_artifact_read_exception_rejects_traversal_escape():
    escape = _workspace_root() + "/../../../../team-" + "secrets.txt"
    assert not _canonical_operational_artifact_read("read_file", {"path": escape})
    mixed = _workspace_root().replace("/", "\\") + "\\..\\..\\..\\..\\team-" + "secrets.txt"
    assert not _canonical_operational_artifact_read("read_file", {"path": mixed})


def test_artifact_read_exception_rejects_unc_impersonation():
    unc = "//evi" + "l/share/kanban/boards/b/workspaces/t/file.txt"
    assert not _canonical_operational_artifact_read("read_file", {"path": unc})


def test_traversal_to_secret_file_is_denied_not_exceptioned(config):
    escape = _workspace_root() + "/../../../../team-" + "secrets.txt"
    result = classify("read_file", {"path": escape}, config, worker=True)
    assert (result.decision, result.category) == ("deny", "secret_read_or_write"), result


# --------------------------------------------------------------------- F2


def test_worker_cannot_invoke_expected_failure_override_subcommand(config):
    for command in (
        "fleet-policy override-expected-failure t_x <sig>",
        "python -m fleet_policy.cli override-expected-failure t_x <sig>",
        "env -u HERMES_KANBAN_TASK fleet-policy override-expected-failure t_x s",
        "uv run fleet-policy override-expected-failure t_x s",
    ):
        result = classify("terminal", {"command": command}, config, worker=True)
        assert (result.decision, result.category) == ("deny", "worker_self_approval"), (
            command,
            result,
        )


def test_worker_cannot_call_mark_expected_failure_api(config):
    result = classify(
        "terminal",
        {"command": "python -c \"store.mark_expected_failure('t', 'sig', None)\""},
        config,
        worker=True,
    )
    assert (result.decision, result.category) == ("deny", "worker_self_approval"), result


def test_expected_failure_override_requires_operator_context(runtime, monkeypatch):
    # v1.2.12 C3: non-worker context alone no longer suffices — the exact
    # derived confirmation code is the second structural factor.
    from fleet_policy.storage import expected_failure_code

    code_1 = expected_failure_code("t_x", "sig-1", None)
    monkeypatch.setenv("HERMES_KANBAN_TASK", "t_other")
    assert runtime.store.mark_expected_failure("t_x", "sig-1", None, confirm_code=code_1) is False
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    assert runtime.store.mark_expected_failure("t_x", "sig-1", None, confirm_code="00000000") is False
    assert runtime.store.mark_expected_failure("t_x", "sig-2", None) is False
    code_2 = expected_failure_code("t_x", "sig-2", None)
    assert runtime.store.mark_expected_failure("t_x", "sig-2", None, confirm_code=code_2) is True


# --------------------------------------------------------------------- F5


def test_commit_message_mentioning_protected_config_flows(config):
    message = "docs: why " + _CFG + " is immutable"
    for command in (
        'git commit -m "' + message + '"',
        'git commit --message="' + message + '"',
    ):
        result = classify("terminal", {"command": command}, config, worker=True)
        assert result.decision == "allow", (command, result)


def test_prose_flag_values_are_not_guard_subjects():
    message = "docs: why " + _CFG + " is immutable"
    subjects = _path_guard_subjects(
        "terminal", {"command": 'git commit -m "' + message + '"'}
    )
    # The quoted message is prose; the remaining command tokens (git,
    # commit, -m) are not path-shaped filesystem operands, so nothing is
    # handed to the protected-path matcher at all.
    assert subjects == [], subjects


def test_real_operand_after_prose_stage_still_guarded(config):
    command = 'git commit -m "release notes" && cat team-' + "secrets.txt"
    result = classify("terminal", {"command": command}, config, worker=True)
    assert result.decision == "deny", result


# --------------------------------------------------------------------- F6


def test_consume_exact_approval_has_no_silent_env_branch():
    source = inspect.getsource(PolicyStore.consume_exact_approval)
    assert "pass" not in source, source
    assert "os.environ" not in source, source


# --------------------------------------------------------------------- F7


def test_untranslated_plugin_blocks_keep_loop_accounting(runtime, task_context):
    args = {"command": "flaky-probe"}
    task_context["tool_call_id"] = "pb-1"
    first = runtime.post_tool_call(
        "terminal", args, task_context, success=False,
        error_type="plugin_block", error_message="FLEET POLICY FAIL-CLOSED: X",
    )
    assert first is None, first
    task_context["tool_call_id"] = "pb-2"
    second = runtime.post_tool_call(
        "terminal", args, task_context, success=False,
        error_type="plugin_block", error_message="FLEET POLICY FAIL-CLOSED: X",
    )
    assert second is not None and second.get("rule_id") == "same_failure_loop", second


def test_translated_nonce_path_stays_suppressed(runtime, task_context):
    ctx = dict(task_context, task_body="task_type: review", profile="qa", assignee="tech")
    ctx["tool_call_id"] = "n-1"
    suppressed = runtime.post_tool_call(
        "terminal", {"command": "probe"}, ctx, success=False,
        error_type="review_probe_nonce", error_message="nonce=abc",
    )
    assert suppressed is None, suppressed
