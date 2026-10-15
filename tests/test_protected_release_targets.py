"""Protected releases are mutation destinations, not source/text matches."""
from __future__ import annotations

import pytest

from fleet_policy.policy import classify

RELEASE = "release_to_protected_branch"


@pytest.mark.parametrize("command", [
    "git push origin feature/x && git log --format=HEAD:main",
    "git push HEAD:feature/x",
    "git push +HEAD:feature/x",
    "git push origin feature/x ; git log --format=HEAD:main",
    "git push origin feature/x | git log --format=HEAD:main",

    "git push origin feature/x || git log --format=HEAD:main",
    "git push origin feature/x\ngit log --format=HEAD:main",
    "git push origin main:feature/x",
    "git push origin refs/heads/main:refs/heads/feature/x",
    "git push origin main:feature/main",
    "git push origin feature/main",
    "git push origin refs/tags/main",
    "git push main feature/x",
    "git -C main push origin feature/x",
    "git -c alias.sample=main push origin feature/x",
    "git push --repo main feature/x",
    "git push --receive-pack main origin feature/x",
    "git push origin HEAD:main --dry-run",
    "git rebase origin/main",
    "git merge-base HEAD origin/main",
    "git rev-parse --verify origin/main",
    "git log --grep=push main",
    "git diff --name-only feature/push main",
    "git ls-remote origin main",
    "git fetch origin main",
    "git merge origin/main",  # merge operand is a source, not the checkout
    "git switch feature/x && git merge main",
    "printf 'git push origin HEAD:main'",
    "bash -c 'git push origin feature/x && git log --format=HEAD:main'",
    "echo push && echo main",
])
def test_non_release_operands_and_stage_boundaries(config, command):
    assert classify("terminal", {"command": command}, config, worker=True).category != RELEASE


@pytest.mark.parametrize("command", [
    "git push HEAD:main",
    "git push +HEAD:refs/heads/main",
    "git push origin HEAD:main",
    "git push origin feature/x main",

    "git push origin main",
    "git push origin HEAD:refs/heads/main",
    'git push origin HEAD:"main"',
    "git push origin :",
    "git push --push-option --dry-run origin HEAD:main",
    "git push origin :main",
    "git push origin HEAD:master",
    "git push origin HEAD:production",
    "git push origin HEAD:release",
    "git push origin 'HEAD:main'",
    'git push origin "HEAD:main"',
    "git -C repo push origin HEAD:main",
    "git -c key=value push origin HEAD:main",
    "git --no-pager push origin HEAD:main",
    "git push --repo=origin HEAD:main",
    "git push --repo origin HEAD:main",
    "git push --receive-pack helper origin HEAD:main",
    "git push origin refs/heads/*:refs/heads/*",
    "git push origin --all",
    "git push origin --mirror",
    "gh pr merge 71 --squash",
    "gh --repo maximalang/ventures pr merge 71",
    "cd repo && git push origin HEAD:main",
    "git log main ; git push origin HEAD:main",
    "git switch main && git merge feature/x",
    "git checkout -b main && git merge feature/x",
    "bash -c 'git push origin HEAD:main'",
    "python -c 'subprocess.run(\"git push origin HEAD:main\", shell=True)'",
    "GIT_TERMINAL_PROMPT=0 git push origin HEAD:main",
])
def test_actual_protected_mutation_destinations(config, command):
    result = classify("terminal", {"command": command}, config, worker=True)
    assert (result.decision, result.category) == ("allow", RELEASE)


def test_configured_protected_refs_are_exact_and_case_sensitive(config):
    config = dict(config, protected=dict(config["protected"], branches=["codex/company-os", "Main"]))
    for ref in ("codex/company-os", "refs/heads/codex/company-os", "Main"):
        result = classify("terminal", {"command": f"git push origin HEAD:{ref}"}, config, worker=True)
        assert result.category == RELEASE
    for ref in ("main", "feature/codex/company-os", "refs/tags/Main"):
        result = classify("terminal", {"command": f"git push origin HEAD:{ref}"}, config, worker=True)
        assert result.category != RELEASE


def test_runtime_still_requires_evidence_for_protected_push(runtime, task_context):
    result = runtime.pre_tool_call(
        "terminal", {"command": "git push origin HEAD:main"}, task_context,
    )
    assert (result.decision, result.rule_id) == ("deny", "evidence_gate_missing")


@pytest.mark.parametrize("separator", ["&&", ";", "|"])
def test_runtime_feature_push_is_not_blocked_by_later_query(runtime, task_context, separator):
    result = runtime.pre_tool_call(
        "terminal",
        {"command": f"git push origin feature/x {separator} git log --format=HEAD:main"},
        task_context,
    )
    assert result.decision == "allow"
    assert result.rule_id != "evidence_gate_missing"


def test_force_push_keeps_serious_risk_precedence(config):
    result = classify("terminal", {"command": "git push --force origin HEAD:main"}, config, worker=True)
    assert (result.decision, result.category) == ("approval_required", "irreversible_data_loss")
