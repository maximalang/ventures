"""Release attestation v1 (1.2.11): fail-closed build/verify of RELEASE-ATTESTATION.json.

Canonical interface (pinned on card t_762adc2b, comment 1):
- artifact schema marker ``hermes-fleet-release-attestation/v1``;
- canonical encoding: UTF-8 JSON, sorted keys, compact separators, exactly one
  trailing newline;
- ``attestation_sha256`` = SHA-256 of the canonical object with that field omitted;
- never infer gates or accept default success values.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]

from fleet_policy.release_attestation import (  # noqa: E402
    ATTESTATION_FILENAME,
    ATTESTATION_SCHEMA,
    TARGET_PROFILES,
    AttestationError,
    attestation_digest,
    build_attestation,
    build_attestation_file,
    canonical_bytes,
    verify_attestation_file,
)

HEAD_SHA = "edf0e455433f9e9cea09af345ef1048bbd5bda4a"
TREE_SHA = "65a3345f4fbfabf43576b1ab61c04ef7cf227d9e"
MANIFEST_SHA = "7b9a70d32c722fb1e8bba45c2722672ea842e1a51b13dc173cd20823a56e91b7"
PAYLOAD_SHA = "8cf1970699862536d08c804b0d3f026184220abcf54e707089f83e67aec02b80"
EVIDENCE_SHA_A = "9173f76999cbbdfdb3db824d4fe3c84c95d2361b300ef3a5054773eb298bb17a"
EVIDENCE_SHA_B = "2bb1db47b2d94089eb32a3a71f38585a16cc7860c791a7257786e71df0ced467"
EVIDENCE_SHA_C = "c5004cab49dbadcd0fbc6759bc1f4abb235e41b54e4446e70387e2f37e0d8ad1"
EVIDENCE_SHA_D = "ed673ff31b302ffc1747861975e267ca6bc2d51f1365e854fe3d23fd67b85139"

REQUIRED_TOP_FIELDS = [
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
]


def valid_evidence() -> dict:
    return {
        "schema": ATTESTATION_SCHEMA,
        "release_id": "rel-2026-09-05-a1",
        "created_at_utc": "2026-09-05T04:30:00Z",
        "task_id": "t_fdeb5580",
        "repository": "maximalang/ventures",
        "version": "1.2.11",
        "implementation_profile": "tech",
        "source": {"head_sha": HEAD_SHA, "tree_sha": TREE_SHA, "base_ref": "codex/company-os"},
        "ci": {
            "provider": "github-actions",
            "run_id": "101195525317",
            "workflow": "fleet-policy-ci.yml",
            "head_sha": HEAD_SHA,
            "conclusion": "success",
        },
        "gates": {
            "ci": {
                "task_id": "t_ae40358c",
                "run_id": "480",
                "profile": "qa",
                "status": "pass",
                "evidence_sha256": EVIDENCE_SHA_A,
            },
            "review": {
                "task_id": "t_b0010001",
                "run_id": "481",
                "profile": "qa",
                "status": "pass",
                "evidence_sha256": EVIDENCE_SHA_B,
            },
            "qa": {
                "task_id": "t_c0020002",
                "run_id": "482",
                "profile": "qa",
                "status": "pass",
                "evidence_sha256": EVIDENCE_SHA_C,
            },
            "rollback": {
                "task_id": "t_d0030003",
                "run_id": "483",
                "profile": "operations",
                "status": "pass",
                "evidence_sha256": EVIDENCE_SHA_D,
            },
        },
        "decision": {"task_id": "t_e0040004", "profile": "company", "status": "go"},
        "bundle": {
            "release_manifest_sha256": MANIFEST_SHA,
            "payload_sha256": PAYLOAD_SHA,
            "file_count": 87,
        },
        "deployment": {
            "target_profiles": list(TARGET_PROFILES),
            "expected_payload_sha256": PAYLOAD_SHA,
        },
    }


def _subprocess_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ)
    src = str(ROOT / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env.pop("HERMES_KANBAN_TASK", None)
    env.pop("HERMES_KANBAN_DB", None)
    if extra:
        env.update(extra)
    return env


def _cli(*argv: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "fleet_policy.cli", *argv],
        cwd=ROOT,
        env=env or _subprocess_env(),
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------- happy path


def test_build_attestation_happy_path_is_canonical_and_digested():
    evidence = valid_evidence()
    artifact = build_attestation(evidence)
    assert artifact["attestation_sha256"] == attestation_digest(evidence)
    for field in REQUIRED_TOP_FIELDS:
        assert artifact[field] == evidence[field]
    encoded = canonical_bytes(artifact)
    text = encoded.decode("utf-8")
    assert text.endswith("\n") and not text.endswith("\n\n")
    reparsed = json.loads(text)
    assert reparsed == artifact
    assert text == json.dumps(artifact, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def test_build_rejects_evidence_that_already_carries_digest():
    evidence = valid_evidence()
    evidence["attestation_sha256"] = attestation_digest(evidence)
    with pytest.raises(AttestationError):
        build_attestation(evidence)


def test_build_does_not_mutate_evidence_input():
    evidence = valid_evidence()
    snapshot = copy.deepcopy(evidence)
    build_attestation(evidence)
    assert evidence == snapshot


@pytest.mark.parametrize("field", REQUIRED_TOP_FIELDS)
def test_build_rejects_missing_top_level_field(field):
    evidence = valid_evidence()
    del evidence[field]
    with pytest.raises(AttestationError):
        build_attestation(evidence)


def test_build_rejects_unknown_top_level_field():
    evidence = valid_evidence()
    evidence["extra_field"] = 1
    with pytest.raises(AttestationError):
        build_attestation(evidence)


@pytest.mark.parametrize(
    "section,extra",
    [
        ("source", "note"),
        ("ci", "url"),
        ("decision", "signed_by"),
        ("bundle", "note"),
        ("deployment", "note"),
    ],
)
def test_build_rejects_unknown_nested_field(section, extra):
    evidence = valid_evidence()
    evidence[section][extra] = "x"
    with pytest.raises(AttestationError):
        build_attestation(evidence)


def test_build_rejects_unknown_gate_identity_field():
    evidence = valid_evidence()
    evidence["gates"]["ci"]["approved_by"] = "someone"
    with pytest.raises(AttestationError):
        build_attestation(evidence)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda ev: ev["source"].pop("tree_sha"),
        lambda ev: ev["ci"].pop("conclusion"),
        lambda ev: ev["decision"].pop("status"),
        lambda ev: ev["bundle"].pop("file_count"),
        lambda ev: ev["deployment"].pop("expected_payload_sha256"),
        lambda ev: ev["gates"]["qa"].pop("evidence_sha256"),
    ],
)
def test_build_rejects_missing_nested_field(mutation):
    evidence = valid_evidence()
    mutation(evidence)
    with pytest.raises(AttestationError):
        build_attestation(evidence)


def test_build_rejects_wrong_schema_marker():
    evidence = valid_evidence()
    evidence["schema"] = "hermes-fleet-release-attestation/v2"
    with pytest.raises(AttestationError):
        build_attestation(evidence)


@pytest.mark.parametrize(
    "field_path,bad_value",
    [
        (("source", "head_sha"), "edf0e455433f9e9cea09af345ef1048bbd5bda4"),   # 39 hex
        (("source", "head_sha"), "EDF0E455433f9e9cea09af345ef1048bbd5bda4a"),  # uppercase
        (("source", "head_sha"), "zedf0e455433f9e9cea09af345ef1048bbd5bda4a"),  # non-hex
        (("source", "tree_sha"), "65a3345f4fbfabf43576b1ab61c04ef7cf227d9"),
        (("ci", "head_sha"), "edf0e455433f9e9cea09af345ef1048bbd5bda4a0"),      # 41 hex
        (("bundle", "release_manifest_sha256"), MANIFEST_SHA[:63]),
        (("bundle", "payload_sha256"), PAYLOAD_SHA.upper()),
        (("deployment", "expected_payload_sha256"), "not-a-digest"),
        (("task_id",), "t_fdeb558"),          # 7 hex
        (("task_id",), "t_FDEB5580"),         # uppercase hex
        (("task_id",), "x_fdeb5580"),         # wrong prefix
        (("task_id",), "t_fdeb55801"),        # 9 hex
        (("decision", "task_id"), "t_1234567"),
        (("gates", "ci", "task_id"), "t_BADBADBA"),
        (("created_at_utc",), "2026-09-05T04:30:00+03:00"),  # offset instead of Z
        (("created_at_utc",), "2026-09-05 04:30:00Z"),       # space separator
        (("created_at_utc",), "2026-09-05T04:30:00.123Z"),   # fractional seconds
        (("created_at_utc",), "2026-09-05T04:30Z"),          # no seconds
    ],
)
def test_build_rejects_malformed_ids_hashes_and_timestamps(field_path, bad_value):
    evidence = valid_evidence()
    node = evidence
    for key in field_path[:-1]:
        node = node[key]
    node[field_path[-1]] = bad_value
    with pytest.raises(AttestationError):
        build_attestation(evidence)


def test_build_rejects_mismatched_ci_head():
    evidence = valid_evidence()
    evidence["ci"]["head_sha"] = TREE_SHA  # valid 40-hex, but != source.head_sha
    with pytest.raises(AttestationError):
        build_attestation(evidence)


@pytest.mark.parametrize("conclusion", ["failure", "cancelled", "success ", "SUCCESS"])
def test_build_rejects_non_success_ci_conclusion(conclusion):
    evidence = valid_evidence()
    evidence["ci"]["conclusion"] = conclusion
    with pytest.raises(AttestationError):
        build_attestation(evidence)


def test_build_rejects_gate_key_set_drift():
    evidence = valid_evidence()
    del evidence["gates"]["rollback"]
    with pytest.raises(AttestationError):
        build_attestation(evidence)
    evidence = valid_evidence()
    evidence["gates"]["backup"] = dict(evidence["gates"]["rollback"])
    with pytest.raises(AttestationError):
        build_attestation(evidence)


@pytest.mark.parametrize("status", ["warn", "skip", "Pass", "PASS", ""])
def test_build_rejects_non_pass_gate_status(status):
    evidence = valid_evidence()
    evidence["gates"]["qa"]["status"] = status
    with pytest.raises(AttestationError):
        build_attestation(evidence)


def test_build_rejects_duplicate_gate_identities():
    evidence = valid_evidence()
    evidence["gates"]["review"]["task_id"] = evidence["gates"]["ci"]["task_id"]
    evidence["gates"]["review"]["run_id"] = evidence["gates"]["ci"]["run_id"]
    evidence["gates"]["review"]["profile"] = evidence["gates"]["ci"]["profile"]
    with pytest.raises(AttestationError):
        build_attestation(evidence)


@pytest.mark.parametrize("gate", ["review", "qa"])
@pytest.mark.parametrize("profile", ["company", "tech"])
def test_build_rejects_review_or_qa_gate_profile_conflict(gate, profile):
    # implementation_profile is "tech" in the fixture: review/qa gates must be
    # independent of both company and the implementing profile.
    evidence = valid_evidence()
    evidence["gates"][gate]["profile"] = profile
    with pytest.raises(AttestationError):
        build_attestation(evidence)


def test_build_rejects_identical_review_and_qa_identities():
    evidence = valid_evidence()
    evidence["gates"]["qa"]["task_id"] = evidence["gates"]["review"]["task_id"]
    evidence["gates"]["qa"]["run_id"] = evidence["gates"]["review"]["run_id"]
    evidence["gates"]["qa"]["profile"] = evidence["gates"]["review"]["profile"]
    with pytest.raises(AttestationError):
        build_attestation(evidence)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda ev: ev["decision"].update({"profile": "tech"}),
        lambda ev: ev["decision"].update({"status": "no-go"}),
        lambda ev: ev["decision"].update({"status": "GO"}),
    ],
)
def test_build_rejects_invalid_company_decision(mutation):
    evidence = valid_evidence()
    mutation(evidence)
    with pytest.raises(AttestationError):
        build_attestation(evidence)


@pytest.mark.parametrize("bad_count", [0, -1, "87", 87.0, None])
def test_build_rejects_invalid_bundle_file_count(bad_count):
    evidence = valid_evidence()
    evidence["bundle"]["file_count"] = bad_count
    with pytest.raises(AttestationError):
        build_attestation(evidence)


def test_build_rejects_payload_digest_mismatch():
    evidence = valid_evidence()
    evidence["deployment"]["expected_payload_sha256"] = MANIFEST_SHA
    with pytest.raises(AttestationError):
        build_attestation(evidence)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda ev: ev["deployment"].update({"target_profiles": list(TARGET_PROFILES)[:-1]}),
        lambda ev: ev["deployment"].update({"target_profiles": list(TARGET_PROFILES) + ["company"]}),
        lambda ev: ev["deployment"].update({"target_profiles": list(TARGET_PROFILES) + ["intern"]}),
        lambda ev: ev["deployment"].update({"target_profiles": "company"}),
        lambda ev: ev["deployment"].update({"target_profiles": []}),
    ],
)
def test_build_rejects_target_profile_set_violations(mutation):
    evidence = valid_evidence()
    mutation(evidence)
    with pytest.raises(AttestationError):
        build_attestation(evidence)


def test_build_accepts_target_profiles_in_any_order():
    evidence = valid_evidence()
    evidence["deployment"]["target_profiles"] = list(reversed(TARGET_PROFILES))
    artifact = build_attestation(evidence)
    assert artifact["deployment"]["target_profiles"] == list(reversed(TARGET_PROFILES))


@pytest.mark.parametrize(
    "field_path",
    [("release_id",), ("repository",), ("version",), ("implementation_profile",),
     ("source", "base_ref"), ("ci", "provider"), ("ci", "run_id"), ("ci", "workflow")],
)
@pytest.mark.parametrize("bad_value", ["", "   ", None, 5])
def test_build_rejects_empty_or_non_string_text_fields(field_path, bad_value):
    evidence = valid_evidence()
    node = evidence
    for key in field_path[:-1]:
        node = node[key]
    node[field_path[-1]] = bad_value
    with pytest.raises(AttestationError):
        build_attestation(evidence)


# ------------------------------------------------------- file build / verify


def test_build_attestation_file_round_trip(tmp_path):
    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text(json.dumps(valid_evidence(), indent=2), encoding="utf-8")
    output_path = tmp_path / "out" / ATTESTATION_FILENAME
    digest = build_attestation_file(evidence_path, output_path)
    assert output_path.is_file()
    text = output_path.read_text(encoding="utf-8")
    assert text.endswith("\n") and not text.endswith("\n\n")
    artifact = json.loads(text)
    assert artifact["attestation_sha256"] == digest
    verified = verify_attestation_file(output_path)
    assert verified == artifact


def test_build_attestation_file_atomic_on_invalid_evidence(tmp_path):
    evidence = valid_evidence()
    evidence["ci"]["conclusion"] = "failure"
    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
    output_path = tmp_path / "out" / ATTESTATION_FILENAME
    with pytest.raises(AttestationError):
        build_attestation_file(evidence_path, output_path)
    assert not output_path.exists()


def test_build_attestation_file_rejects_invalid_json_input(tmp_path):
    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text("{not json", encoding="utf-8")
    with pytest.raises(AttestationError):
        build_attestation_file(evidence_path, tmp_path / ATTESTATION_FILENAME)


def test_build_attestation_file_rejects_non_object_input(tmp_path):
    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text(json.dumps([valid_evidence()]), encoding="utf-8")
    with pytest.raises(AttestationError):
        build_attestation_file(evidence_path, tmp_path / ATTESTATION_FILENAME)


def test_build_is_offline_and_leaves_no_state(tmp_path):
    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text(json.dumps(valid_evidence()), encoding="utf-8")
    build_attestation_file(evidence_path, tmp_path / ATTESTATION_FILENAME)
    leftovers = sorted(p.name for p in tmp_path.iterdir())
    assert leftovers == ["RELEASE-ATTESTATION.json", "evidence.json"]
    assert not (tmp_path / ".state").exists()
    assert not (tmp_path / "fleet-policy.db").exists()


def _write_artifact(tmp_path, artifact: dict, *, text: str | None = None) -> Path:
    path = tmp_path / ATTESTATION_FILENAME
    payload = text if text is not None else canonical_bytes(artifact).decode("utf-8")
    path.write_text(payload, encoding="utf-8")
    return path


def _built_artifact(tmp_path) -> tuple[Path, dict]:
    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text(json.dumps(valid_evidence()), encoding="utf-8")
    output_path = tmp_path / ATTESTATION_FILENAME
    build_attestation_file(evidence_path, output_path)
    return output_path, json.loads(output_path.read_text(encoding="utf-8"))


def test_verify_rejects_digest_mismatch(tmp_path):
    path, artifact = _built_artifact(tmp_path)
    artifact["attestation_sha256"] = EVIDENCE_SHA_A
    path.write_text(canonical_bytes(artifact).decode("utf-8"), encoding="utf-8")
    with pytest.raises(AttestationError):
        verify_attestation_file(path)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda a: a["gates"]["qa"].update({"status": "warn"}),
        lambda a: a["ci"].update({"conclusion": "failure"}),
        lambda a: a["ci"].update({"head_sha": TREE_SHA}),
        lambda a: a["deployment"].update({"expected_payload_sha256": MANIFEST_SHA}),
        lambda a: a.__setitem__("extra", 1),
        lambda a: a["bundle"].pop("payload_sha256"),
        lambda a: a["gates"].pop("ci"),
        lambda a: a.update({"version": ""}),
    ],
)
def test_verify_re_applies_every_field_invariant(tmp_path, mutation):
    path, artifact = _built_artifact(tmp_path)
    mutation(artifact)
    # Recompute the digest so only the mutated field itself can fail: verify
    # must still reject the artifact on the invariant, not only on the digest.
    digest = attestation_digest({k: v for k, v in artifact.items() if k != "attestation_sha256"})
    artifact["attestation_sha256"] = digest
    path.write_text(canonical_bytes(artifact).decode("utf-8"), encoding="utf-8")
    with pytest.raises(AttestationError):
        verify_attestation_file(path)


def test_verify_rejects_non_canonical_encoding(tmp_path):
    path, artifact = _built_artifact(tmp_path)
    pretty = json.dumps(artifact, indent=2, sort_keys=True) + "\n"
    path.write_text(pretty, encoding="utf-8")
    with pytest.raises(AttestationError):
        verify_attestation_file(path)


def test_verify_rejects_missing_trailing_newline(tmp_path):
    path, artifact = _built_artifact(tmp_path)
    path.write_text(canonical_bytes(artifact).decode("utf-8").rstrip("\n"), encoding="utf-8")
    with pytest.raises(AttestationError):
        verify_attestation_file(path)


def test_verify_rejects_invalid_json(tmp_path):
    path = tmp_path / ATTESTATION_FILENAME
    path.write_text("{broken", encoding="utf-8")
    with pytest.raises(AttestationError):
        verify_attestation_file(path)


def test_verify_rejects_non_object_artifact(tmp_path):
    path = tmp_path / ATTESTATION_FILENAME
    path.write_text(json.dumps([]), encoding="utf-8")
    with pytest.raises(AttestationError):
        verify_attestation_file(path)


# ----------------------------------------------------------------- CLI layer


def test_cli_build_then_verify_exit_zero_with_machine_json(tmp_path):
    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text(json.dumps(valid_evidence()), encoding="utf-8")
    output_path = tmp_path / ATTESTATION_FILENAME

    built = _cli("build-release-attestation", "--input", str(evidence_path), "--output", str(output_path))
    assert built.returncode == 0, built.stderr
    built_payload = json.loads(built.stdout)
    assert built_payload["ok"] is True
    assert built_payload["output"] == str(output_path)
    assert built_payload["attestation_sha256"] == attestation_digest(valid_evidence())
    assert output_path.is_file()

    verified = _cli("verify-release-attestation", "--input", str(output_path))
    assert verified.returncode == 0, verified.stderr
    verified_payload = json.loads(verified.stdout)
    assert verified_payload["ok"] is True
    assert verified_payload["attestation_sha256"] == built_payload["attestation_sha256"]


def test_cli_build_failure_exits_nonzero_and_writes_nothing(tmp_path):
    evidence = valid_evidence()
    evidence["gates"]["review"]["status"] = "warn"
    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
    output_path = tmp_path / ATTESTATION_FILENAME

    result = _cli("build-release-attestation", "--input", str(evidence_path), "--output", str(output_path))
    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["errors"]
    assert not output_path.exists()


def test_cli_verify_failure_exits_nonzero_with_reasons(tmp_path):
    path, artifact = _built_artifact(tmp_path)
    artifact["ci"]["conclusion"] = "failure"
    digest = attestation_digest({k: v for k, v in artifact.items() if k != "attestation_sha256"})
    artifact["attestation_sha256"] = digest
    path.write_text(canonical_bytes(artifact).decode("utf-8"), encoding="utf-8")

    result = _cli("verify-release-attestation", "--input", str(path))
    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["errors"]


def test_cli_verify_missing_input_exits_nonzero(tmp_path):
    result = _cli("verify-release-attestation", "--input", str(tmp_path / "missing.json"))
    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is False


def test_cli_attestation_commands_work_in_worker_environment(tmp_path):
    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text(json.dumps(valid_evidence()), encoding="utf-8")
    output_path = tmp_path / ATTESTATION_FILENAME
    env = _subprocess_env({"HERMES_KANBAN_TASK": "t_ci_simulated"})

    built = _cli("build-release-attestation", "--input", str(evidence_path), "--output", str(output_path), env=env)
    assert built.returncode == 0, built.stderr
    verified = _cli("verify-release-attestation", "--input", str(output_path), env=env)
    assert verified.returncode == 0, verified.stderr


def test_cli_build_missing_input_file_exits_nonzero(tmp_path):
    result = _cli(
        "build-release-attestation",
        "--input", str(tmp_path / "missing.json"),
        "--output", str(tmp_path / ATTESTATION_FILENAME),
    )
    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
