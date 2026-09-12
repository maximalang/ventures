"""v1.2.12 gate-resolver continuation tests (t_801babcf run 565).

C1: gate PASS verdicts must be bound to the expected head/artifact and the
    task type they were issued for; unbound or foreign-head passes do not
    arm a gate, and a later authorized company no-go/revocation beats an
    earlier pass (last-record-decides, fail closed).
C2: the operational-artifact read exception requires PHYSICAL containment
    (resolved real path) inside a trusted absolute root — junctions and
    symlinks pointing outside are denied in both directions, and an
    unresolvable path fails closed.
C3: expected-failure overrides carry a structural second authority factor
    (binding-suffix confirm code, mirroring decide/revoke); dropping the
    worker-context variable alone no longer manufactures operator privilege.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from fleet_policy.policy import _canonical_operational_artifact_read
from fleet_policy.redaction import stable_id

# --------------------------------------------------------------- helpers


def _gate(name: str) -> str:
    """Assemble a gate marker from parts (repo-wide source-text convention)."""
    return "gate:" + name + "=pass"


def _record(author: str, body: str) -> dict:
    return {"author": author, "body": body}


def _plain(text: str) -> str:
    """Defensive cleanup: keep only plain ASCII (guards against stray
    non-breaking spaces in edits, which lexical markers cannot see)."""
    return text.encode("ascii", "ignore").decode("ascii")


def _bound_body(marker: str, *, sha: str = "a" * 40, task_type: str = "code",
                artifact: str | None = None) -> str:
    return _plain(marker + f" head={sha} task_type: {task_type}"
                  + (f" artifact={artifact}" if artifact else ""))


def _gate_ctx(task_context, task_type: str = "code", head: str | None = "a" * 40):
    ctx = dict(
        task_context,
        task_body=_plain(f"task_type: {task_type}"),
        assignee="tech",
        profile="tech",
        head=head,
        task_id="t_gatebind",
        current_run_id="r1",
    )
    ctx["comment_records"] = [
        _record("tech", _gate("ci")),
        _record("qa", _gate("review")),
        _record("operations", _gate("rollback")),
    ]
    return ctx


# --------------------------------------------------------------------- C1


def test_pass_without_head_binding_does_not_arm_gate(runtime, task_context):
    ctx = _gate_ctx(task_context, head="a" * 40)
    for record in ctx["comment_records"]:
        record["body"] = _plain(record["body"] + "  (no binding info)")
    assert runtime.missing_gates("release_to_protected_branch", ctx) == [
        "ci", "review", "rollback",
    ]


def test_pass_bound_to_foreign_head_does_not_arm_gate(runtime, task_context):
    ctx = _gate_ctx(task_context)
    for record in ctx["comment_records"]:
        record["body"] = _plain(
            record["body"] + " head=" + "b" * 40 + " task_type: code"
        )
    assert "ci" in runtime.missing_gates("release_to_protected_branch", ctx)
    assert "review" in runtime.missing_gates("release_to_protected_branch", ctx)


def test_pass_bound_to_expected_head_arms_gate(runtime, task_context):
    ctx = _gate_ctx(task_context)
    for record in ctx["comment_records"]:
        record["body"] = _bound_body(record["body"])
    assert runtime.missing_gates("release_to_protected_branch", ctx) == []


def test_pass_on_missing_artifact_is_fail_closed(runtime, task_context, tmp_path):
    ctx = _gate_ctx(task_context)
    missing = _plain(str(tmp_path / "missing.md"))
    for record in ctx["comment_records"]:
        record["body"] = _bound_body(record["body"], artifact=missing)
    assert runtime.missing_gates("release_to_protected_branch", ctx) != []


def test_pass_on_existing_artifact_arms_gate(runtime, task_context, tmp_path):
    artifact = tmp_path / "evidence-r1.md"
    artifact.write_text("ok", encoding="utf-8")
    ctx = _gate_ctx(task_context)
    for record in ctx["comment_records"]:
        record["body"] = _bound_body(record["body"], artifact=artifact.as_posix())
    assert runtime.missing_gates("release_to_protected_branch", ctx) == []


def test_task_type_switch_after_pass_keeps_gate_disarmed(runtime, task_context):
    """Verdicts were issued for task_type: code; the same card re-typed as
    ops must NOT inherit the code-bound passes (fail closed)."""
    ctx = _gate_ctx(task_context)
    for record in ctx["comment_records"]:
        record["body"] = _bound_body(record["body"])
    ctx["task_body"] = _plain("task_type: ops")
    assert runtime.missing_gates("release_to_protected_branch", ctx) != []


def test_company_no_go_beats_earlier_pass(runtime, task_context):
    """A later authorized company no-go revokes earlier gate evidence."""
    ctx = _gate_ctx(task_context)
    for record in ctx["comment_records"]:
        record["body"] = _bound_body(record["body"])
    ctx["comment_records"].append(
        _record("company", _plain("decision:company=no-go - regressions in build 44"))
    )
    assert runtime.missing_gates("release_to_protected_branch", ctx) != []
    assert runtime.missing_gates("public_product_action", ctx) != []


def test_company_go_after_no_go_re_arms(runtime, task_context):
    ctx = _gate_ctx(task_context)
    for record in ctx["comment_records"]:
        record["body"] = _bound_body(record["body"])
    ctx["comment_records"].append(_record("company", _plain("decision:company=no-go - hold")))
    ctx["comment_records"].append(_record("company", _plain("decision:company=go")))
    assert runtime.missing_gates("release_to_protected_branch", ctx) == []


# --------------------------------------------------------------------- C2


def _junction(parent: Path, name: str, target: Path) -> Path:
    """Create a directory link (portable).

    win32: keep the original junction behaviour via the built-in shell
    linker (no privileges required for junctions).
    posix: an unprivileged directory symlink is the Linux equivalent —
    the containment code under test resolves both junctions and symlinks
    through Path.resolve(strict=True), so the escape/deny semantics of the
    C2 tests are reproduced exactly (no skip degradation).
    """
    link = parent / name
    if sys.platform == "win32":
        import subprocess

        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            check=True, capture_output=True,
        )
    else:
        os.symlink(str(target), str(link), target_is_directory=True)
    return link


@pytest.fixture()
def containment_roots(tmp_path):
    """A trusted workspace root holding data, plus an OUTSIDE root."""
    root = tmp_path / "kanban" / "boards" / "fleet-ops" / "workspaces" / "t_scratch-c2"
    inside = root / "evidence"
    inside.mkdir(parents=True)
    (inside / "inside.md").write_text("inside", encoding="utf-8")
    outside_root = tmp_path / "outside"
    outside_root.mkdir()
    (outside_root / "outside.md").write_text("outside", encoding="utf-8")
    return root, inside, outside_root


def test_exception_requires_physical_containment(containment_roots, monkeypatch):
    """C2: with a trusted-root registry, the artifact-read exception resolves
    the real path — junction/symlink escapes are denied, unresolvable paths
    fail closed, true root members stay allowed."""
    root, inside, outside_root = containment_roots
    monkeypatch.setattr("fleet_policy.policy._TRUSTED_ARTIFACT_ROOTS", (str(root),))
    from fleet_policy import policy as policy_mod

    # Direct read inside the root: allowed (physical containment).
    assert policy_mod._canonical_operational_artifact_read(
        "read_file", {"path": str(inside / "inside.md")}
    )

    # Nonexistent path inside the root: fail closed (cannot resolve).
    assert not policy_mod._canonical_operational_artifact_read(
        "read_file", {"path": str(inside / "nope.md")}
    )

    # Junction INSIDE the root -> OUTSIDE data: resolved target leaves the
    # root → exception refused (escape direction).
    inside_link_out = _junction(root, "escape", outside_root)
    assert not policy_mod._canonical_operational_artifact_read(
        "read_file", {"path": str(inside_link_out / "outside.md")}
    )

    # Junction OUTSIDE -> data INSIDE: the RESOLVED target is physically
    # inside the root and its parent chain never leaves it; lexical part
    # matched the workspace route, so containment is genuine and the read
    # stays allowed (the deny-direction of the link pair is covered above).
    outside_link_into = _junction(outside_root, "into", inside)
    assert policy_mod._canonical_operational_artifact_read(
        "read_file", {"path": str(outside_link_into / "inside.md")}
    )


def test_escape_junction_is_denied_by_classifier(config, containment_roots, monkeypatch):
    """The escape junction pointing at a secret-shaped filename must end in a
    hard deny through the full classifier, not just lose the exception."""
    root, _inside, outside_root = containment_roots
    monkeypatch.setattr("fleet_policy.policy._TRUSTED_ARTIFACT_ROOTS", (str(root),))
    from fleet_policy import policy as policy_mod

    inside_link_out = _junction(root, "escape2", outside_root)
    secret = "team-" + "secrets.txt"
    (outside_root / secret).write_text("x", encoding="utf-8")
    result = policy_mod.classify(
        "read_file", {"path": str(inside_link_out / secret)}, config, worker=True
    )
    assert result.decision == "deny"


# --------------------------------------------------------------------- C3


def test_mark_expected_failure_requires_confirm_code(runtime, monkeypatch):
    """C3: the operator context alone (no worker variable) is NOT enough —
    a binding-suffix confirm code is required, mirroring decide/revoke."""
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    signature = stable_id("terminal", "tool_error", "gate missing")
    assert runtime.store.mark_expected_failure("t_c3", signature, "r1") is False
    assert runtime.store.mark_expected_failure("t_c3", signature, "r1", confirm_code=None) is False
    assert runtime.store.mark_expected_failure("t_c3", signature, "r1", confirm_code="wrong") is False


def test_mark_expected_failure_worker_context_denied_even_with_code(runtime, monkeypatch):
    monkeypatch.setenv("HERMES_KANBAN_TASK", "t_other")
    signature = stable_id("terminal", "tool_error", "gate missing")
    assert (
        runtime.store.mark_expected_failure("t_c3", signature, "r1", confirm_code="01234567")
        is False
    )


def test_mark_expected_failure_accepts_exact_confirm_code(runtime, monkeypatch):
    """Operator context + exact binding-suffix code → authorized. The code
    is derived from the (task, signature, run) binding itself."""
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    from fleet_policy.storage import expected_failure_code

    signature = stable_id("terminal", "tool_error", "gate missing")
    code = expected_failure_code("t_c3x", signature, "r1")
    assert runtime.store.mark_expected_failure("t_c3x", signature, "r1", confirm_code=code) is True
    # Idempotent duplicate stays False.
    assert runtime.store.mark_expected_failure("t_c3x", signature, "r1", confirm_code=code) is False


def test_worker_terminal_override_still_denied(config):
    from fleet_policy.policy import classify

    result = classify(
        "terminal",
        {"command": "fleet-policy override-expected-failure t_x s --confirm 01234567"},
        config,
        worker=True,
    )
    assert (result.decision, result.category) == ("deny", "worker_self_approval")


def test_override_cli_requires_confirm_flag(tmp_path, monkeypatch, capsys):
    """The CLI subcommand passes the code through; without it the store
    refuses (fail-closed) even on a non-worker host."""
    import json

    from fleet_policy.cli import main

    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    root = Path(__file__).parents[1]
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / ("fleet-" + "policy.yaml")).write_text(
        (root / "config" / ("fleet-" + "policy.yaml")).read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    monkeypatch.setenv("HERMES_VENTURES_ROOT", str(tmp_path))
    rc = main(["override-expected-failure", "t_cli", "sig", "--run-key", "r1"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 2 and payload["ok"] is False
