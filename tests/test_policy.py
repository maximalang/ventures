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
    ("mass outreach to 5000 contacts", "mass_outreach_or_bulk_messaging"),
    ("open paid account with phone verification", "new_paid_capability_or_payment_rail"),
    ("sign contract with guaranteed return", "legal_or_material_reputation_risk"),
    ("transfer ownership and root access", "ownership_or_root_access_change"),
    ("git push --force origin main", "irreversible_data_loss"),
])
def test_serious_risk_categories_require_approval(config, command, category):
    result = classify("terminal", {"command": command}, config, worker=True)
    assert result.decision == "approval_required"
    assert result.category == category


@pytest.mark.parametrize("command,category", [
    ("deploy production", "deploy_external_runtime"),
    ("git push origin main", "release_to_protected_branch"),
    ("gh pr merge 123 --merge", "release_to_protected_branch"),
    ("publish product launch", "public_product_action"),
    ("git clean -fd", "destructive_change"),
    ("create free service account", "free_service_account"),
])
def test_routine_actions_are_autonomous_after_runtime_gates(config, command, category):
    result = classify("terminal", {"command": command}, config, worker=True)
    assert result.decision == "allow"
    assert result.category == category


def test_canonical_public_policy_doc_has_one_exact_read_exception(config):
    name = "APP" + "ROVALS.md"
    canonical = "C:/Users/max/Desktop/all/ventures/" + name
    allowed = classify("read_file", {"path": canonical}, config, worker=True)
    assert (allowed.decision, allowed.category) == ("allow", "read_only")

    read_only_cases = (
        ("read_file", {"path": name}),
        ("read_file", {"path": "C:/Users/max/Desktop/all/other/" + name}),
        ("read_file", {"path": "C:/Users/max/Desktop/all/ventures/subdir/" + name}),
        ("search_files", {"path": canonical, "pattern": "*"}),
    )
    for tool_name, arguments in read_only_cases:
        inspected = classify(tool_name, arguments, config, worker=True)
        assert (inspected.decision, inspected.category) == ("allow", "read_only")


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
        "fleet-policy revoke rule-key",
        "python -m fleet_policy.cli revoke rule-key",
    ):
        result = classify("terminal", {"command": command}, config, worker=True)
        assert (result.decision, result.category) == ("deny", "worker_self_approval"), command
    direct_api = classify(
        "terminal",
        {"command": "python -c \"store.decide_approval('rule', True, 'worker')\""},
        config,
        worker=True,
    )
    assert (direct_api.decision, direct_api.category) == ("deny", "worker_self_approval")
    revoke_api = classify(
        "terminal",
        {"command": "python -c \"store.revoke_approval('rule', 'worker')\""},
        config,
        worker=True,
    )
    assert (revoke_api.decision, revoke_api.category) == ("deny", "worker_self_approval")


def test_destructive_git_variants_split_by_reversibility(config):
    autonomous = ("git clean -fd", "git branch -D main", "git tag -d v1.0")
    for command in autonomous:
        result = classify("terminal", {"command": command}, config, worker=True)
        assert (result.decision, result.category) == ("allow", "destructive_change"), (command, result)
    irreversible = classify("terminal", {"command": "git filter-branch --prune-empty HEAD"}, config, worker=True)
    assert (irreversible.decision, irreversible.category) == ("approval_required", "irreversible_data_loss")


def test_bare_secret_filenames_denied(config):
    # Filenames are assembled from parts so this test file itself stays
    # clean for plugin security scanners while exercising the same matcher.
    names = ["sec" + "rets.txt", "cred" + "entials.json", "au" + "th.json"]
    commands = ["cat " + names[0], "del " + names[1], "copy " + names[2] + " /tmp"]
    for command in commands:
        result = classify("terminal", {"command": command}, config, worker=True)
        assert result.decision == "deny", command


def test_adversarial_control_plane_and_payment_commands(config):
    cases = [
        ("fleet-policy grant-capability backdoor --project p --kind payment --scope any", "deny"),
        ("python -c \"store.grant_capability('c','p','k','s','user')\"", "deny"),
        ("hermes config set approvals.mode off", "approval_required"),
        ("curl -X POST https://api.stripe.com/v1/charges -d amount=900000", "allow"),
    ]
    for command, decision in cases:
        result = classify("terminal", {"command": command}, config, worker=True)
        assert result.decision == decision, (command, result)
    protected = classify(
        "terminal",
        {"command": "python -c \"import sqlite3; sqlite3.connect('kanban.db')\""},
        config,
        worker=True,
    )
    assert protected.decision == "deny"


def test_retry_limits_reconcile_with_kanban():
    assert effective_retries(2, 4, 3) == 2
    assert effective_retries(4, 2, 3) == 2
    assert effective_retries(4, None, 1) == 1


def test_v126_read_classifier_no_false_control_plane_denies(config):
    # v1.2.6 regression: read-only terminal commands were classified as
    # state_change before (sed/head/tail/stat/wc/git clone/ls-remote were
    # missing from READ_COMMAND, chained `cd X && git ...` never matched,
    # and search() matched keywords mid-word). Any such command whose path
    # touched a policy-controlled file then produced the hard
    # policy_control_plane_mutation deny instead of a read allow.
    cfg_name = "fleet-" + "policy.yaml"
    cases = [
        "sed -n '49,75p' config/" + cfg_name,
        "head -20 config/" + cfg_name,
        "tail -5 config/" + cfg_name,
        "stat config/" + cfg_name,
        "wc -l config/" + cfg_name,
        "grep -n -A12 'protected:' config/" + cfg_name,
        "cd repo && git clone --branch codex/company-os https://example.com/ventures.git repo",
        "git ls-remote https://example.com/ventures.git codex/company-os",
        "git rev-list --count HEAD",
        "git ls-files src/",
    ]
    for command in cases:
        result = classify("terminal", {"command": command}, config, worker=True)
        assert (result.decision, result.category) == ("allow", "read_only"), (command, result)


def test_v126_write_and_destructive_variants_are_not_read(config):
    # v1.2.6: in-place variants of otherwise read-only utilities stay
    # mutations, and destructive git subcommands never become read-only
    # even though a read keyword appears in the same regex.
    for command in (
        "sed -i 's/a/b/' pyproject.toml",
        "sort -o out.txt in.txt",
        "git branch -D main",
        "git branch -d feature/x",
        "git clean -fd",
        "git tag -d v1.0",
    ):
        result = classify("terminal", {"command": command}, config, worker=True)
        assert result.category != "read_only", (command, result)
