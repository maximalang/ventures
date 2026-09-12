"""Executable validation for Adaptive Organization v1 declarations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

BASE = Path(__file__).resolve().parent
COMMON_ID = "https://maximalang.github.io/ventures/contracts/adaptive_org/v1/common.schema.json"
SCHEMA_FILES = {
    "product_manifest/v1": "product_manifest.schema.json",
    "agent_manifest/v1": "agent_manifest.schema.json",
    "bet/v1": "bet.schema.json",
    "agent_change/v1": "agent_change.schema.json",
}

class ContractError(ValueError):
    """A stable, machine-readable contract failure."""


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_document(document: Mapping[str, Any]) -> None:
    version = document.get("schema_version")
    if version not in SCHEMA_FILES:
        raise ContractError("unknown_schema_version")
    common = _load_json(BASE / "common.schema.json")
    schema = _load_json(BASE / SCHEMA_FILES[version])
    registry = Registry().with_resources([(COMMON_ID, Resource.from_contents(common))])
    validator = Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.absolute_path))
    if errors:
        path = ".".join(str(part) for part in errors[0].absolute_path) or "$"
        raise ContractError(f"schema_invalid:{path}:{errors[0].message}")

    product_id = document.get("product_id")
    agent_id = document.get("agent_id")
    if agent_id is not None and not agent_id.startswith(f"{product_id}--"):
        raise ContractError("agent_product_identity_mismatch")


def validate_bet_set(bets: Iterable[Mapping[str, Any]]) -> None:
    active_products: set[str] = set()
    for bet in bets:
        validate_document(bet)
        if bet["state"] == "active":
            product_id = bet["product_id"]
            if product_id in active_products:
                raise ContractError(f"duplicate_active_bet:{product_id}")
            active_products.add(product_id)


def canonical_payload_hash(document: Mapping[str, Any]) -> str:
    payload = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def effective_dry_run(change: Mapping[str, Any]) -> bool:
    """Return the safe effective value; schema defaults do not mutate JSON."""
    return change["requested_transition"].get("dry_run", True)


def validate_agent_change(
    change: Mapping[str, Any],
    *,
    current_revision: int,
    prior_requests: Mapping[str, Mapping[str, Any]] | None = None,
    prior_outcome: str | None = None,
) -> str:
    validate_document(change)
    if change["expected_revision"] != current_revision:
        raise ContractError("stale_revision")

    # Fail-closed precedence: a reused key with a changed payload is always a
    # conflict; an unknown prior outcome always requires reconciliation first,
    # even for a byte-identical retry. "replay" is returned only when the prior
    # request is identical AND its outcome is known (not "unknown").
    prior_requests = prior_requests or {}
    key = change["idempotency_key"]
    known_prior = key in prior_requests
    if known_prior and canonical_payload_hash(prior_requests[key]) != canonical_payload_hash(change):
        raise ContractError("idempotency_conflict")
    if prior_outcome == "unknown":
        raise ContractError("reconcile_required")
    return "replay" if known_prior else "accepted"
