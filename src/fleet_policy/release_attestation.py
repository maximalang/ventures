"""Release attestation v1: fail-closed build/verify of RELEASE-ATTESTATION.json.

Canonical interface (pinned on card t_762adc2b):

- artifact ``RELEASE-ATTESTATION.json``, schema marker
  ``hermes-fleet-release-attestation/v1``;
- canonical encoding: UTF-8 JSON, sorted keys, compact separators, exactly one
  trailing newline;
- top-level ``attestation_sha256`` = SHA-256 of the canonical encoding of the
  object with that field omitted;
- gates (ci/review/qa/rollback) are copied verbatim from the evidence object:
  the builder never infers gates and never accepts default success values;
- any malformed ID/hash/timestamp, unknown or missing field, inconsistent
  head/payload, non-pass gate, duplicate identity, or digest mismatch fails
  the build and the verify.

Both operations are offline: no network, no policy database, no state files.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path

ATTESTATION_FILENAME = "RELEASE-ATTESTATION.json"
ATTESTATION_SCHEMA = "hermes-fleet-release-attestation/v1"

#: The ten canonical fleet profiles: the deployment plan must list each once.
TARGET_PROFILES = (
    "company",
    "tech",
    "product",
    "design",
    "ux",
    "qa",
    "sales",
    "finance",
    "research",
    "operations",
)

_REQUIRED_TOP_FIELDS = (
    "schema",
    "release_id",
    "created_at_utc",
    "task_id",
    "repository",
    "version",
    "implementation_profile",
    "source",
    "ci",
    "gates",
    "decision",
    "bundle",
    "deployment",
)
_DIGEST_FIELD = "attestation_sha256"
_GATE_NAMES = ("ci", "review", "qa", "rollback")
_GATE_FIELDS = ("task_id", "run_id", "profile", "status", "evidence_sha256")
_SOURCE_FIELDS = ("head_sha", "tree_sha", "base_ref")
_CI_FIELDS = ("provider", "run_id", "workflow", "head_sha", "conclusion")
_DECISION_FIELDS = ("task_id", "profile", "status")
_BUNDLE_FIELDS = ("release_manifest_sha256", "payload_sha256", "file_count")
_DEPLOYMENT_FIELDS = ("target_profiles", "expected_payload_sha256")

_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA64_RE = re.compile(r"^[0-9a-f]{64}$")
_TASK_ID_RE = re.compile(r"^t_[0-9a-f]{8}$")
_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class AttestationError(ValueError):
    """Any attestation build/verify failure. Carries the full error list."""

    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors))


def canonical_bytes(payload: dict) -> bytes:
    """Canonical encoding: UTF-8 JSON, sorted keys, compact separators, one newline."""
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    return text.encode("utf-8")


def attestation_digest(payload: dict) -> str:
    """SHA-256 of the canonical object with the digest field omitted."""
    stripped = {key: value for key, value in payload.items() if key != _DIGEST_FIELD}
    return hashlib.sha256(canonical_bytes(stripped)).hexdigest()


# ----------------------------------------------------------------- validators


def _nonempty_str(value, path: str, errors: list[str]) -> bool:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path} must be a non-empty string")
        return False
    return True


def _exact_keys(obj, expected: tuple[str, ...], path: str, errors: list[str]) -> bool:
    if not isinstance(obj, dict):
        errors.append(f"{path} must be an object")
        return False
    keys = set(obj)
    missing = [name for name in expected if name not in keys]
    unknown = sorted(keys - set(expected))
    if missing:
        errors.append(f"{path} is missing required field(s): {', '.join(missing)}")
    if unknown:
        errors.append(f"{path} has unknown field(s): {', '.join(unknown)}")
    return not missing and not unknown


def _sha40(value, path: str, errors: list[str]) -> None:
    if not (isinstance(value, str) and _SHA40_RE.match(value)):
        errors.append(f"{path} must be a lowercase 40-character hex commit/tree sha")


def _sha64(value, path: str, errors: list[str]) -> None:
    if not (isinstance(value, str) and _SHA64_RE.match(value)):
        errors.append(f"{path} must be a lowercase 64-character hex sha256 digest")


def _task_id(value, path: str, errors: list[str]) -> None:
    if not (isinstance(value, str) and _TASK_ID_RE.match(value)):
        errors.append(f"{path} must be a Kanban task id of the form t_<8 hex>")


def _timestamp(value, path: str, errors: list[str]) -> None:
    if not (isinstance(value, str) and _TIMESTAMP_RE.match(value)):
        errors.append(f"{path} must be a UTC RFC3339 timestamp ending in Z (no fractional seconds)")
        return
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        errors.append(f"{path} is not a valid calendar timestamp: {value}")


def validate_evidence(evidence, *, expect_digest: bool) -> list[str]:
    """Full fail-closed validation. Returns every problem found (empty = valid)."""
    errors: list[str] = []
    if not isinstance(evidence, dict):
        return ["evidence must be a JSON object"]

    expected_top = _REQUIRED_TOP_FIELDS + ((_DIGEST_FIELD,) if expect_digest else ())
    if not _exact_keys(evidence, expected_top, "attestation", errors):
        return errors

    if evidence["schema"] != ATTESTATION_SCHEMA:
        errors.append(f"schema must be exactly {ATTESTATION_SCHEMA}")
    for field in ("release_id", "repository", "version", "implementation_profile"):
        _nonempty_str(evidence[field], field, errors)
    _task_id(evidence["task_id"], "task_id", errors)
    _timestamp(evidence["created_at_utc"], "created_at_utc", errors)

    source = evidence["source"]
    if _exact_keys(source, _SOURCE_FIELDS, "source", errors):
        _sha40(source["head_sha"], "source.head_sha", errors)
        _sha40(source["tree_sha"], "source.tree_sha", errors)
        _nonempty_str(source["base_ref"], "source.base_ref", errors)

    ci = evidence["ci"]
    if _exact_keys(ci, _CI_FIELDS, "ci", errors):
        _nonempty_str(ci["provider"], "ci.provider", errors)
        _nonempty_str(ci["run_id"], "ci.run_id", errors)
        _nonempty_str(ci["workflow"], "ci.workflow", errors)
        _sha40(ci["head_sha"], "ci.head_sha", errors)
        if ci["conclusion"] != "success":
            errors.append("ci.conclusion must be exactly 'success'")
        elif isinstance(source, dict) and isinstance(source.get("head_sha"), str) \
                and _SHA40_RE.match(source["head_sha"]) and ci["head_sha"] != source["head_sha"]:
            errors.append("ci.head_sha must equal source.head_sha")

    gates = evidence["gates"]
    if _exact_keys(gates, _GATE_NAMES, "gates", errors):
        identities: set[tuple[str, str, str]] = set()
        implementation_profile = evidence.get("implementation_profile")
        for name in _GATE_NAMES:
            gate = gates[name]
            gate_path = f"gates.{name}"
            if not _exact_keys(gate, _GATE_FIELDS, gate_path, errors):
                continue
            _task_id(gate["task_id"], f"{gate_path}.task_id", errors)
            _nonempty_str(gate["run_id"], f"{gate_path}.run_id", errors)
            _nonempty_str(gate["profile"], f"{gate_path}.profile", errors)
            if gate["status"] != "pass":
                errors.append(f"{gate_path}.status must be exactly 'pass'")
            _sha64(gate["evidence_sha256"], f"{gate_path}.evidence_sha256", errors)
            identity = (str(gate["task_id"]), str(gate["run_id"]), str(gate["profile"]))
            if identity in identities:
                errors.append(f"{gate_path} identity (task_id, run_id, profile) duplicates another gate")
            identities.add(identity)
            if name in ("review", "qa") and isinstance(gate.get("profile"), str):
                if gate["profile"] in ("company", implementation_profile):
                    errors.append(
                        f"{gate_path}.profile must be independent of both company and the implementation profile"
                    )

    decision = evidence["decision"]
    if _exact_keys(decision, _DECISION_FIELDS, "decision", errors):
        _task_id(decision["task_id"], "decision.task_id", errors)
        if decision["profile"] != "company":
            errors.append("decision.profile must be exactly 'company'")
        if decision["status"] != "go":
            errors.append("decision.status must be exactly 'go'")

    bundle = evidence["bundle"]
    if _exact_keys(bundle, _BUNDLE_FIELDS, "bundle", errors):
        _sha64(bundle["release_manifest_sha256"], "bundle.release_manifest_sha256", errors)
        _sha64(bundle["payload_sha256"], "bundle.payload_sha256", errors)
        file_count = bundle["file_count"]
        if isinstance(file_count, bool) or not isinstance(file_count, int) or file_count < 1:
            errors.append("bundle.file_count must be a positive integer")

    deployment = evidence["deployment"]
    if _exact_keys(deployment, _DEPLOYMENT_FIELDS, "deployment", errors):
        _sha64(deployment["expected_payload_sha256"], "deployment.expected_payload_sha256", errors)
        targets = deployment["target_profiles"]
        if not isinstance(targets, list) or len(targets) != len(TARGET_PROFILES):
            errors.append(
                "deployment.target_profiles must list the ten canonical profiles exactly once each"
            )
        elif sorted(targets) != sorted(TARGET_PROFILES) or len(set(targets)) != len(TARGET_PROFILES):
            errors.append(
                "deployment.target_profiles must list the ten canonical profiles exactly once each"
            )
        elif any(not isinstance(item, str) for item in targets):
            errors.append("deployment.target_profiles entries must be strings")
        elif isinstance(bundle, dict) and _SHA64_RE.match(str(bundle.get("payload_sha256") or "")):
            if deployment["expected_payload_sha256"] != bundle["payload_sha256"]:
                errors.append("deployment.expected_payload_sha256 must equal bundle.payload_sha256")

    if expect_digest:
        digest = evidence.get(_DIGEST_FIELD)
        if not (isinstance(digest, str) and _SHA64_RE.match(digest)):
            errors.append(f"{_DIGEST_FIELD} must be a lowercase 64-character hex sha256 digest")
        elif digest != attestation_digest(evidence):
            errors.append(f"{_DIGEST_FIELD} does not match the canonical object digest")

    return errors


# ------------------------------------------------------------------- building


def build_attestation(evidence: dict) -> dict:
    """Validate evidence and return the canonical artifact with its digest.

    Never mutates the input; never infers gate values.
    """
    if not isinstance(evidence, dict):
        raise AttestationError(["evidence must be a JSON object"])
    if _DIGEST_FIELD in evidence:
        raise AttestationError(
            [f"evidence must not carry {_DIGEST_FIELD}: the digest is computed at build time"]
        )
    errors = validate_evidence(evidence, expect_digest=False)
    if errors:
        raise AttestationError(errors)
    artifact = copy.deepcopy(evidence)
    artifact[_DIGEST_FIELD] = attestation_digest(artifact)
    return artifact


def _read_evidence(input_path: Path) -> dict:
    try:
        text = input_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AttestationError([f"cannot read evidence file: {exc}"]) from exc
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AttestationError([f"evidence file is not valid JSON: {exc}"]) from exc
    if not isinstance(payload, dict):
        raise AttestationError(["evidence file must contain a JSON object"])
    return payload


def build_attestation_file(input_path: str | Path, output_path: str | Path) -> str:
    """Build the attestation from an evidence file; atomic write. Returns the digest."""
    input_path = Path(input_path)
    output_path = Path(output_path)
    artifact = build_attestation(_read_evidence(input_path))
    payload = canonical_bytes(artifact)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(output_path.name + ".tmp")
    try:
        temporary.write_bytes(payload)
        os.replace(temporary, output_path)
    except BaseException:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise
    return artifact[_DIGEST_FIELD]


# ------------------------------------------------------------------ verifying


def verify_attestation_file(path: str | Path) -> dict:
    """Verify an attestation artifact. Raises AttestationError on any violation."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AttestationError([f"cannot read attestation file: {exc}"]) from exc
    try:
        artifact = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AttestationError([f"attestation file is not valid JSON: {exc}"]) from exc
    if not isinstance(artifact, dict):
        raise AttestationError(["attestation file must contain a JSON object"])
    if canonical_bytes(artifact).decode("utf-8") != text:
        raise AttestationError(
            ["attestation file is not in canonical encoding (sorted keys, compact separators, one trailing newline)"]
        )
    errors = validate_evidence(artifact, expect_digest=True)
    if errors:
        raise AttestationError(errors)
    return artifact
