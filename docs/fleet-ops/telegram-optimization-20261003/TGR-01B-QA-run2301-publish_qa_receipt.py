"""Content-validate source QA results and publish exact receipts/artifacts."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "evidence"
DURABLE = Path("C:/Users/max/Desktop/all/ventures/docs/fleet-ops/telegram-optimization-20261003")
PREFIX = "TGR-01B-QA-run2301-"
HEAD = "c605e5b618cf20a2d94422bd2c995b864bd986c8"
BASE = "9aae3c23e2c4f39f77d8d54b5e72ba4b90f4ba8f"
identity = json.loads((OUT / "identity.json").read_text(encoding="utf-8"))
suites = json.loads((OUT / "suite-results.json").read_text(encoding="utf-8"))
probes = json.loads((OUT / "probe-results-v5.json").read_text(encoding="utf-8"))
assert identity["head"] == HEAD and identity["base"] == BASE
assert identity["patch_matches_submitted_bytes"]
focus, regression_base, regression_head = suites
assert focus["exit_code"] == 0 and focus["summary"] == [1, 18, 0]
assert regression_base["exit_code"] == regression_head["exit_code"] == 1
assert regression_base["summary"] == regression_head["summary"] == [10, 18, 0]
def semantic_rows(record):
    return {path: {k: row[k] for k in ["marker", "passed", "failed", "collected_without_summary"]} for path, row in record["per_file"].items()}
assert semantic_rows(regression_base) == semantic_rows(regression_head)
assert (regression_base["home_guard_occurrences"], regression_base["stashkey_occurrences"]) == (10, 4)
assert (regression_head["home_guard_occurrences"], regression_head["stashkey_occurrences"]) == (10, 4)
head_probes, base_probes = probes
assert head_probes["counts"] == {"passed": 24, "failed": 4, "error": 0, "skipped": 0, "total": 28}
assert base_probes["counts"] == {"passed": 8, "failed": 20, "error": 0, "skipped": 0, "total": 28}
EXPECTED_FAILURES = {f"test_{surface}_agrees_with_effective_turn[{peer}]" for surface in ["real_model_listing", "real_telegram_picker"] for peer in ["dm", "forum"]}
actual_failures = {c["name"] for c in head_probes["cases"] if c["status"] == "failed"}
assert actual_failures == EXPECTED_FAILURES
base_cases = {c["name"]: c for c in base_probes["cases"]}
head_cases = {c["name"]: c for c in head_probes["cases"]}
for name in ["test_fresh_company_entrypoint[dm]", "test_fresh_company_entrypoint[negative-forum]"]:
    assert base_cases[name]["status"] == "failed" and head_cases[name]["status"] == "passed"
    text = base_cases[name]["evidence"]
    assert all(token in text for token in ["AssertionError", "qa-launch/v3", "qa-launcher", "qwen3.8-max", "custom"])
    assert not any(token in text for token in ["ImportError", "AttributeError", "TypeError"])
head_log = Path(head_probes["log"]).read_text(encoding="utf-8")
def observations(marker):
    return [json.loads(line.split(marker + " ", 1)[1]) for line in head_log.splitlines() if marker + " " in line and not line.lstrip().startswith("\u2551") and not "\u2551" in line]
pickers = observations("QA_PICKER")
slash = observations("QA_SLASH")
assert len(pickers) == len(slash) == 2
assert all(p["turn"] == ["qwen3.8-max", "custom"] and p["picker"] == ["gpt-6.1-sol", "openai-codex"] and p["reply"] is None for p in pickers)
assert all(s["turn"] == ["qwen3.8-max", "custom"] and '"model": "gpt-6.1-sol"' in s["reply"] and '"provider": "openai-codex"' in s["reply"] for s in slash)
assert "offline probe attempted external network" not in head_log
commands = []
for tree, sha in [(ROOT / "head-r2301", HEAD), (ROOT / "base-r2301", BASE), (Path("C:/Users/max/AppData/Local/hermes/hermes-agent/.worktrees/tg-qwen-profile-routing-bounded-20261003"), HEAD)]:
    for args in [["git", "-C", str(tree), "rev-parse", "HEAD"], ["git", "-C", str(tree), "status", "--porcelain"]]:
        p = subprocess.run(args, capture_output=True, timeout=30)
        commands.append({"argv": args, "exit_code": p.returncode, "stdout": p.stdout.decode().strip(), "stderr": p.stderr.decode().strip()})
        assert p.returncode == 0
        assert p.stdout.decode().strip() == (sha if args[-1] == "HEAD" else "")
rollback_argv = ["git", "-C", str(ROOT / "head-r2301"), "apply", "--reverse", "--check", str(OUT / "qa-exact-head.patch")]
p = subprocess.run(rollback_argv, capture_output=True, timeout=30)
assert p.returncode == 0, p.stderr
rollback = {"argv": rollback_argv, "exit_code": p.returncode, "stdout": p.stdout.decode(), "stderr": p.stderr.decode(), "applied": False, "scope": "isolated source patch applicability only"}
manifest = []
def publish(source, target):
    raw = source.read_bytes()
    if target.exists():
        assert target.read_bytes() == raw, f"existing durable artifact differs: {target}"
    else:
        target.write_bytes(raw)
    assert target.read_bytes() == raw
    manifest.append({"file": target.name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "source": str(source)})

names = ["identity.json", "production-diff.txt", "qa-exact-head.patch", "suite-results.json", "qa-focused-head.log", "qa-regressions-base.log", "qa-regressions-head.log", "qa-focused-head-native-bash.log", "qa-regressions-base-native-bash.log", "qa-regressions-head-native-bash.log", "probe-results.json"]
for version in range(1, 6):
    suffix = "" if version == 1 else "-v" + str(version)
    for label in ["head", "base"]:
        names.extend(["qa-independent-" + label + suffix + ".log", "qa-independent-" + label + suffix + ".xml"])
    if version > 1:
        names.append("probe-results-v" + str(version) + ".json")
for name in names:
    publish(OUT / name, DURABLE / (PREFIX + name))
for name in ["provision_review.py", "run_review_suites.py", "run_independent_probes.py", "test_qa_tgr_routing.py", "publish_qa_receipt.py"]:
    publish(ROOT / name, DURABLE / (PREFIX + name))

report = DURABLE / "TGR-01B-QA-VERDICT.md"
text = report.read_text(encoding="utf-8")
assert all(s in text for s in [HEAD, BASE, "verdict: BLOCK", "B1", "B2", "B3", "FINAL v5", "24 passed / 4", "18 passed / 0 failed", "UNVERIFIED", "t_25e773da"])
assert "_handle_model_command_locked:582-585" in text
publish(report, OUT / report.name)
receipt = {"schema": "tgr01b-source-qa-receipt-v1", "task_id": "t_307fc218", "board": "fleet-ops", "run_id": 2301, "source_author": {"task_id": "t_ced9d357", "implementation_run": 2225, "continuation_run": 2241, "serving_model": None, "serving_provider": None, "fallback": None, "usage_attested": False}, "reviewer": {"profile": "qa", "configured_model": "gpt-6.1-sol", "configured_provider": "openai-codex", "serving_model_attested": None, "serving_provider_attested": None, "fallback_attested": None, "usage_attested": False, "independence_proven": False, "model_evidence_limit": "native model_override/runtime context only; no exposed session_model_usage and no dispatcher session evidence"}, "created_at": datetime.now(timezone.utc).isoformat(), "period_started_at": datetime.fromtimestamp(1791057624, timezone.utc).isoformat(), "head": HEAD, "base": BASE, "verdict": "BLOCK", "scope": "offline source-only; no remote CI/live adoption", "positive_gates_issued": [], "blockers": [{"id": "B1", "severity": "high", "kind": "acceptance_defect", "summary": "real text/picker current route disagrees with ordinary turn for DM/forum", "failed_cases": sorted(actual_failures), "owner": "tech", "remediation_card": "t_25e773da"}, {"id": "B2", "severity": "high", "kind": "lineage_unproven", "owner": "company", "request_comment": 5592}, {"id": "B3", "severity": "medium", "kind": "status_coverage_gap", "needed_scoped_source": "gateway/slash_commands_status.py", "owner": "company", "product_status_defect_claimed": False}], "tests": {"focused": focus, "existing_regressions": {"base": regression_base, "head": regression_head, "observed_per_file_delta": [], "complete_suite_green": False, "not_verified_files": sorted(k for k, v in regression_head["per_file"].items() if v["marker"] == "\u2717"), "missing_path": "tests/gateway/test_profile_route_ownership.py"}, "independent_latest": probes, "head_behavioral_counts": {"passed": 23, "failed": 4, "locator_excluded": 1}, "redo_note": "v1 self-pipe and v3/v4 picker-catalogue harness issues are NOT product findings; v5 only counted"}, "observations": {"actual_picker": pickers, "actual_text": slash, "base_dm_forum_wrong_model_provider": True}, "identity": identity, "final_git_commands": commands, "rollback_check": rollback, "reviewed_source_writes": 0, "primary": {"task_id": "t_d088d7f1", "state": "done/superseded", "verdict": "NO_VERDICT"}, "next_owner": "company", "consumer_task": "t_32f46379", "disposition_ref": {"remediation": "t_25e773da", "decision": "t_32f46379"}, "receipt": {"status": "delivered_negative_verdict", "evidence_refs": [str(report), str(DURABLE / (PREFIX + "probe-results-v5.json")), str(DURABLE / (PREFIX + "suite-results.json"))], "next_action": "company consumes BLOCK; scope/lineage decision and parked tech remediation precede a new exact-head QA; no live adoption"}, "finance": {"scope": "run2301 offline source QA", "revenue": None, "refunds": None, "incremental_paid_cost": None, "estimated_usage_cost": None, "null_reason": "not investigated or attribution/invoice unavailable", "new_paid_commitments": 0}, "artifacts": manifest}
raw = json.dumps(receipt, ensure_ascii=False, indent=2).encode("utf-8")
receipt_path = DURABLE / "TGR-01B-QA-RECEIPT.json"
assert not receipt_path.exists(), "receipt target unexpectedly exists"
receipt_path.write_bytes(raw)
(OUT / receipt_path.name).write_bytes(raw)
assert json.loads(receipt_path.read_text(encoding="utf-8"))["tests"]["independent_latest"][0]["counts"]["total"] == 28
bundle = DURABLE / "TGR-01B-QA-run2301-evidence.zip"
assert not bundle.exists(), "bundle target unexpectedly exists"
with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for entry in manifest:
        if entry["file"] == report.name:
            continue
        path = DURABLE / entry["file"]
        if path.is_file():
            z.writestr(entry["file"], path.read_bytes())
    z.writestr(report.name, report.read_bytes())
    z.writestr(receipt_path.name, receipt_path.read_bytes())
with zipfile.ZipFile(bundle) as z:
    assert z.testzip() is None
    assert json.loads(z.read(receipt_path.name))["verdict"] == "BLOCK"
    assert z.read(report.name) == report.read_bytes()
summary = {"verdict": "BLOCK", "head": HEAD, "head_probes": head_probes["counts"], "base_probes": base_probes["counts"], "focused_summary": focus["summary"], "regression_exit_codes": [regression_base["exit_code"], regression_head["exit_code"]], "rollback_check_exit_code": 0, "tree_status": "all empty; head/base exact", "report": str(report), "receipt": str(receipt_path), "bundle": str(bundle), "bundle_sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(), "published_evidence_files": len(manifest)}
(OUT / "publication-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
