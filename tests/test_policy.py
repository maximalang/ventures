from __future__ import annotations

from pathlib import Path

import pytest

from fleet_policy.policy import classify, effective_retries, infer_task_type
from fleet_policy.redaction import REDACTED, args_hash, redact

ROOT = Path(__file__).parents[1]


def test_task_type_exact_sources():
    assert infer_task_type("task_type: research") == ("research", None)
    assert infer_task_type(None, ["task_type=code"], []) == ("code", None)
    assert infer_task_type(None, [], ["task-type-review"]) == ("review", None)


def test_task_type_missing_unknown_and_conflict():
    assert infer_task_type("nothing")[0] is None
    assert infer_task_type("task_type: magic")[0] is None
    assert infer_task_type("task_type: code", ["task_type: review"])[0] is None


def test_redaction_and_stable_canonical_hash():
    first = {"b": 2, "authorization": "Bearer abcdefghijklmnop", "a": {"token": "secret"}}
    second = {"a": {"token": "different"}, "authorization": "Bearer zzzzzzzzzzzzzzzz", "b": 2}
    assert redact(first)["authorization"] == REDACTED
    assert args_hash(first) == args_hash(second)


def test_all_budget_types_present(config):
    assert set(config["budgets"]) == {"research", "code", "review", "ops"}
    assert config["budgets"]["research"]["tokens"] == 120000
    assert config["budgets"]["code"]["tool_calls"] == 140
    assert config["budgets"]["review"]["wall_clock_minutes"] == 45
    assert config["budgets"]["ops"]["tokens"] == 50000


def test_read_allow_and_secret_deny(config):
    assert classify("read_file", {"path": "README.md"}, config, worker=True).decision == "allow"
    result = classify("read_file", {"path": ".env.production"}, config, worker=True)
    assert (result.decision, result.category) == ("deny", "secret_read_or_write")


@pytest.mark.parametrize("command,category", [
    ("deploy production", "deploy_external_runtime"),
    ("git push origin main", "protected_branch_push_or_merge"),
    ("rm -rf build-cache", "destructive_delete_cleanup_or_migration"),
    ("gh repo edit --visibility public", "private_to_public"),
    ("grant new api key permission", "new_credentials_or_permissions"),
])
def test_approval_categories(config, command, category):
    result = classify("terminal", {"command": command}, config, worker=True)
    assert result.decision == "approval_required"
    assert result.category == category


def test_codex_push_allowed(config):
    result = classify("terminal", {"command": "git push -u origin codex/fleet-policy"}, config, worker=True)
    assert result.decision == "allow"


def test_worker_cannot_self_approve(config):
    result = classify("terminal", {"command": "fleet-policy approve abc"}, config, worker=True)
    assert (result.decision, result.category) == ("deny", "worker_self_approval")


def test_worker_self_approval_variants_denied(config):
    for command in (
        "fleet-policy.exe approve rule-key",
        ".venv/Scripts/fleet-policy approve rule-key",
        "python -m fleet_policy.cli approve rule-key",
        "uv run fleet-policy reject rule-key",
    ):
        result = classify("terminal", {"command": command}, config, worker=True)
        assert (result.decision, result.category) == ("deny", "worker_self_approval"), command


def test_destructive_git_variants_require_approval(config):
    for command in (
        "git clean -fd",
        "git branch -D main",
        "git filter-branch --prune-empty HEAD",
        "git tag -d v1.0",
    ):
        result = classify("terminal", {"command": command}, config, worker=True)
        assert result.decision == "approval_required", (command, result)


def test_bare_secret_filenames_denied(config):
    for command in ("cat secrets.txt", "rm credentials.json", "cp auth.json /tmp"):
        result = classify("terminal", {"command": command}, config, worker=True)
        assert result.decision == "deny", command


def test_retry_limits_reconcile_with_kanban():
    assert effective_retries(2, 4, 3) == 2
    assert effective_retries(4, 2, 3) == 2
    assert effective_retries(4, None, 1) == 1
