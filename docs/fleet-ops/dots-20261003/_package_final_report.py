"""Package actual accepted files; no profile/registry writes."""
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED = "f2a85ced87b620bf08cdfc2f3de85ce004a2912efded4da85b668148f00dce6f"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def main():
    assert sha(ROOT / "METHOD-CANDIDATE.md") == EXPECTED
    before = load("TARGETS-BASELINE.json")["targets"]
    hook = (ROOT / "LOAD-HOOK.md").read_bytes()
    method = (ROOT / "METHOD-CANDIDATE.md").read_bytes()
    assert len(before) == len({x["profile"] for x in before}) == 12
    for target in before:
        raw = Path(target["root_path"]).read_bytes()
        assert raw.endswith(hook) and raw.count(hook) == 1
        assert hashlib.sha256(raw[:-len(hook)]).hexdigest() == target["baseline_sha256"]
        assert Path(target["new_reference_path"]).read_bytes() == method
    native = load("FINAL-DISPOSITION.json")
    assert native["board"] == "fleet-ops" and native["all_required_tasks_done"] is True
    assert native["accepted_candidate_sha256"] == EXPECTED
    assert len(native["tasks"]) == 6
    assert all(x["status"] == "done" for x in native["tasks"])
    assert load("QA.json")["verdict"] == "PASS"
    receipts = {}
    for name in ("QA-CHECK-t_a3c78661.json", "QA-ERRATA-CHECK-t_a1ec6fed.json"):
        checks = load(name)["checks"]
        assert checks and all(x["pass"] for x in checks.values())
        receipts[name] = {"count": len(checks), "passed": sum(x["pass"] for x in checks.values())}
    sources = load("SOURCES.json")["sources"] + load("SOURCES-ADDENDUM.json")["additional_core_sources"]
    assert len(sources) == len({x["name"] for x in sources}) == 13
    for entry in sources:
        path = Path(entry["path"])
        assert path.parent == ROOT / "sources"
        assert sha(path) == entry["file_sha256"] and path.stat().st_size == entry["file_bytes"]
    members = [
        "README.md", "REPORT.md", "STUDY.md", "METHOD-CANDIDATE.md", "LOAD-HOOK.md",
        "SOURCES.json", "SOURCES-ADDENDUM.json", "BRAIN-PACKET.json", "TARGETS-BASELINE.json",
        "SOURCE-AUDIT.md", "EVIDENCE-ERRATA.md", "ROLLOUT.md", "ROLLOUT.json",
        "QA.md", "QA.json", "QA-ERRATA.md", "QA-CHECK-t_a3c78661.json",
        "QA-ERRATA-CHECK-t_a1ec6fed.json", "ACCEPTANCE.md", "AUTHOR-READBACK.json",
        "CONSUMER-READBACK-20261004.json", "FINAL-SOURCE-READBACK.json", "FINAL-CONSUMER-CHECK.json", "FINAL-DISPOSITION.json",
        "DISPATCH.json", "DISPATCH-UPDATE.json", "_rollout_t_87ddea42.py",
        "_verify_t_87ddea42.py", "_qa_check_t_a3c78661.py", "_qa_errata_check_t_a1ec6fed.py",
    ] + sorted("sources/" + x.name for x in (ROOT / "sources").glob("*.md"))
    backups = sorted(p for p in (ROOT / "backup-t_87ddea42").glob("*") if p.is_file())
    assert len(backups) == 24, "Expect 12 raw original roots plus 12 reference-existence markers"
    members += [p.relative_to(ROOT).as_posix() for p in backups]
    assert len(members) == len(set(members))
    assert all((ROOT / name).is_file() for name in members)
    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ACCEPTED methodology/filesystem rollout; not OpenAI Dots software/runtime deployment",
        "candidate_sha256": EXPECTED,
        "verified_profile_count": len(before),
        "source_count": len(sources),
        "actual_QA_receipts": receipts,
        "proof_limits": "No measured economic benefit or universal future obedience; configured QA label is not actual serving lineage proof.",
        "financial": {"scope": "fleet-ops methodology integration", "period": "2026-10-03 packet start through final acceptance", "source": "task/tool receipts only; billing unavailable/not queried", "confirmed_revenue": None, "refunds": None, "incremental_paid_costs": None, "estimated_usage_cost": None, "new_paid_commitments": 0},
        "files": [{"name": name, "sha256": sha(ROOT / name), "bytes": (ROOT / name).stat().st_size} for name in members],
    }
    archive = ROOT / "dots-fleet-integrated-20261004.zip"
    assert not archive.exists(), "Refuse to overwrite a published archive"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name in members:
            z.write(ROOT / name, name)
        z.writestr("PACKAGE-MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    with zipfile.ZipFile(archive, "r") as z:
        assert z.testzip() is None
        assert set(z.namelist()) == set(members + ["PACKAGE-MANIFEST.json"])
        assert all(hashlib.sha256(z.read(x["name"])).hexdigest() == x["sha256"] for x in manifest["files"])
        member_count = len(z.namelist())
    print(json.dumps({"archive_path": str(archive), "archive_bytes": archive.stat().st_size, "archive_sha256": sha(archive), "archive_member_count": member_count, "source_count": len(sources), "verified_profiles": len(before), "actual_QA_checks": receipts, "ZIP_CRC_and_member_hashes": "PASS", "status": "ACCEPTED method only"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
