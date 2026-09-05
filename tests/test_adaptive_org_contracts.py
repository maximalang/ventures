from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from contracts.adaptive_org.v1.validator import (
    BASE,
    ContractError,
    SCHEMA_FILES,
    canonical_payload_hash,
    effective_dry_run,
    validate_agent_change,
    validate_bet_set,
    validate_document,
)

FIXTURES = BASE / "fixtures"


def load(group: str, name: str):
    return json.loads((FIXTURES / group / name).read_text(encoding="utf-8"))


def test_all_schemas_are_valid_draft_2020_12():
    Draft202012Validator.check_schema(load_schema("common.schema.json"))
    for filename in SCHEMA_FILES.values():
        Draft202012Validator.check_schema(load_schema(filename))


def load_schema(name: str):
    return json.loads((BASE / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "fixture",
    ["product_manifest.json", "agent_manifest.json", "bet.json", "agent_change.json"],
)
def test_positive_fixtures(fixture: str):
    document = load("positive", fixture)
    validate_document(document)


def test_unknown_requires_null_with_reason():
    with pytest.raises(ContractError, match="schema_invalid:primary_metric"):
        validate_document(load("negative", "unknown_without_reason.json"))


@pytest.mark.parametrize("fixture", ["identity_mismatch.json", "identity_malformed.json"])
def test_invalid_identities_are_rejected(fixture: str):
    with pytest.raises(ContractError):
        validate_document(load("negative", fixture))


def test_money_requires_integer_minor_units_and_currency():
    with pytest.raises(ContractError, match="schema_invalid:financial_metrics"):
        validate_document(load("negative", "money_not_minor_units.json"))


def test_only_one_active_bet_per_product():
    with pytest.raises(ContractError, match="duplicate_active_bet:recruiter-radar"):
        validate_bet_set(load("negative", "duplicate_active_bets.json"))


def test_forbidden_transition_is_rejected():
    with pytest.raises(ContractError, match="schema_invalid:requested_transition"):
        validate_document(load("negative", "forbidden_transition.json"))


def test_stale_revision_is_rejected():
    change = load("negative", "stale_revision.json")
    with pytest.raises(ContractError, match="stale_revision"):
        validate_agent_change(change, current_revision=3)


def test_idempotent_replay_and_changed_payload_conflict():
    change = load("positive", "agent_change.json")
    prior = {change["idempotency_key"]: copy.deepcopy(change)}
    assert validate_agent_change(change, current_revision=3, prior_requests=prior) == "replay"

    changed = copy.deepcopy(change)
    changed["manifest_hash"] = "sha256:" + "b" * 64
    assert canonical_payload_hash(changed) != canonical_payload_hash(change)
    with pytest.raises(ContractError, match="idempotency_conflict"):
        validate_agent_change(changed, current_revision=3, prior_requests=prior)


def test_unknown_prior_outcome_requires_reconciliation():
    change = load("positive", "agent_change.json")
    with pytest.raises(ContractError, match="reconcile_required"):
        validate_agent_change(change, current_revision=3, prior_outcome="unknown")


def test_dry_run_defaults_true_and_explicit_false_is_preserved():
    change = load("positive", "agent_change.json")
    assert effective_dry_run(change) is True
    change["requested_transition"]["dry_run"] = False
    assert effective_dry_run(change) is False


def test_secret_shaped_extra_fields_are_not_contract_data():
    manifest = load("positive", "agent_manifest.json")
    manifest["api_token"] = "must-not-be-here"
    with pytest.raises(ContractError, match="schema_invalid"):
        validate_document(manifest)
