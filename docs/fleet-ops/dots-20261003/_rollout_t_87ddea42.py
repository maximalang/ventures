#!/usr/bin/env python3
"""Read-only guard + backup + install for t_87ddea42.

Two phases (controlled by argv[1]):
  guard    - verify TARGETS-BASELINE.json against live FS; print per-target status; NO writes.
  install  - backup raw bytes, write reference, append hook, emit ROLLOUT.json.

All operations are byte-preserving (no newline normalization, no encoding transcode).
Never touches .env*, secrets, configs, DB, or other profiles' files.
"""
import hashlib, json, os, shutil, sys, time
from pathlib import Path

PACKET = Path(r"C:/Users/max/Desktop/all/ventures/docs/fleet-ops/dots-20261003")
BASELINE_PATH = PACKET / "TARGETS-BASELINE.json"
METHOD = PACKET / "METHOD-CANDIDATE.md"
HOOK = PACKET / "LOAD-HOOK.md"
BACKUP_DIR = PACKET / "backup-t_87ddea42"
ROLLOUT_JSON = PACKET / "ROLLOUT.json"

EXPECTED_REFERENCE_SHA256 = "f2a85ced87b620bf08cdfc2f3de85ce004a2912efded4da85b668148f00dce6f"
EXPECTED_HOOK_SHA256 = "2e10a1c6153947db1c2f335ea7037fa0522111f5be6ec31d83ebb345b9768ec9"
EXPECTED_CANDIDATE_SHA1 = "fd6c26f5dbebba33baa17761f43a80e22ed17427"

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_path(p: Path) -> str:
    return sha256_bytes(p.read_bytes())

def sha1_path(p: Path) -> str:
    return hashlib.sha1(p.read_bytes()).hexdigest()

def guard() -> int:
    baseline = json.loads(BASELINE_PATH.read_bytes().decode("utf-8"))
    targets = baseline["targets"]
    if len(targets) != 12:
        print(f"FATAL baseline targets count = {len(targets)}, expected 12")
        return 2

    method_sha = sha256_path(METHOD)
    method_sha1 = sha1_path(METHOD)
    hook_sha = sha256_path(HOOK)
    print(f"METHOD-CANDIDATE sha256={method_sha}")
    print(f"METHOD-CANDIDATE sha1  ={method_sha1}")
    print(f"LOAD-HOOK sha256       ={hook_sha}")
    if method_sha != EXPECTED_REFERENCE_SHA256: print("FATAL method sha256 drift"); return 3
    if method_sha1 != EXPECTED_CANDIDATE_SHA1: print("FATAL method sha1 drift"); return 3
    if hook_sha != EXPECTED_HOOK_SHA256: print("FATAL hook sha256 drift"); return 3

    failures = []
    for t in targets:
        profile = t["profile"]
        root = Path(t["root_path"])
        ref = Path(t["new_reference_path"])
        ok = True
        msgs = []
        if not root.exists():
            ok = False; msgs.append("root SKILL.md MISSING")
        else:
            cur = sha256_path(root)
            if cur != t["baseline_sha256"]:
                ok = False; msgs.append(f"root drift: baseline={t['baseline_sha256'][:12]}… now={cur[:12]}…")
        ref_exists_now = ref.exists()
        if t["reference_exists"] != ref_exists_now:
            ok = False; msgs.append(f"reference existence drift: baseline={t['reference_exists']} now={ref_exists_now}")
        if ref_exists_now:
            cur = sha256_path(ref)
            if cur != EXPECTED_REFERENCE_SHA256:
                ok = False; msgs.append(f"reference exists with unexpected sha256={cur[:12]}…")
        status = "OK " if ok else "DRIFT"
        print(f"{status} {profile:14s} root_exists={root.exists()} ref_exists={ref_exists_now} :: {'; '.join(msgs) or 'clean'}")
        if not ok: failures.append(profile)
    print(f"guard: {12 - len(failures)}/12 clean; drifts={failures}")
    return 0 if not failures else 4

def install() -> int:
    baseline = json.loads(BASELINE_PATH.read_bytes().decode("utf-8"))
    targets = baseline["targets"]
    method_bytes = METHOD.read_bytes()
    hook_bytes = HOOK.read_bytes()
    method_sha = sha256_bytes(method_bytes)
    hook_sha = sha256_bytes(hook_bytes)
    assert method_sha == EXPECTED_REFERENCE_SHA256, "method drift"
    assert hook_sha == EXPECTED_HOOK_SHA256, "hook drift"

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    started_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    entries = []
    for t in targets:
        profile = t["profile"]
        root = Path(t["root_path"])
        ref = Path(t["new_reference_path"])
        entry = {"profile": profile, "root_path": str(root), "new_reference_path": str(ref)}

        original_root_bytes = root.read_bytes()
        original_root_sha = sha256_bytes(original_root_bytes)
        entry["original_root_sha256"] = original_root_sha
        entry["baseline_root_sha256"] = t["baseline_sha256"]
        entry["root_fresh"] = (original_root_sha == t["baseline_sha256"])
        if not entry["root_fresh"]:
            entry["result"] = "skipped_root_drift"
            entries.append(entry); print(f"SKIP {profile}: root drift"); continue

        ref_existed = ref.exists()
        entry["reference_existed_before"] = ref_existed
        if ref_existed:
            existing = sha256_path(ref)
            entry["reference_prior_sha256"] = existing
            if existing != EXPECTED_REFERENCE_SHA256:
                entry["result"] = "skipped_reference_collision"
                entries.append(entry); print(f"SKIP {profile}: ref collision"); continue

        # Backup raw bytes of root SKILL.md
        b_root = BACKUP_DIR / f"{profile}.SKILL.md.original"
        b_root.write_bytes(original_root_bytes)
        entry["backup_root"] = {"path": str(b_root), "sha256": sha256_path(b_root), "bytes": len(original_root_bytes)}
        # Backup reference existence/nonexistence marker
        b_ref_marker = BACKUP_DIR / f"{profile}.reference.existence.json"
        marker = {"profile": profile, "reference_existed": ref_existed,
                  "path": str(ref),
                  "prior_sha256": entry.get("reference_prior_sha256")}
        b_ref_marker.write_text(json.dumps(marker, indent=2), encoding="utf-8")
        entry["backup_reference_marker"] = str(b_ref_marker)

        # 1) Write reference (byte-for-byte copy)
        ref.parent.mkdir(parents=True, exist_ok=True)
        # write to temp then atomic replace
        tmp_ref = ref.with_name(ref.name + ".tmp-" + str(os.getpid()))
        tmp_ref.write_bytes(method_bytes)
        if sha256_path(tmp_ref) != method_sha:
            entry["result"] = "failed_ref_validation"
            entries.append(entry); print(f"FAIL {profile}: ref tmp validation"); continue
        os.replace(tmp_ref, ref)
        entry["reference_sha256_after"] = sha256_path(ref)
        entry["reference_bytes_after"] = ref.stat().st_size

        # 2) Append hook to root SKILL.md exactly once
        # Determine if original ends with newline; preserve original bytes and append hook as-is.
        new_root_bytes = original_root_bytes
        if not new_root_bytes.endswith(b"\n"):
            new_root_bytes += b"\n"
        # Hook file begins with '\n## Dots-style...' — append byte-for-byte
        new_root_bytes += hook_bytes
        tmp_root = root.with_name(root.name + ".tmp-" + str(os.getpid()))
        tmp_root.write_bytes(new_root_bytes)
        # Validate: root after = original + optional LF + hook
        new_root_sha = sha256_path(tmp_root)
        # Verify hook appears exactly once in after bytes
        hook_count = new_root_bytes.count(hook_bytes)
        if hook_count != 1:
            entry["result"] = "failed_hook_count"
            entries.append(entry); print(f"FAIL {profile}: hook_count={hook_count}"); continue
        # Verify after-minus-hook == original (strip the appended tail)
        stripped = new_root_bytes[:-len(hook_bytes)]
        if stripped != original_root_bytes and stripped != original_root_bytes + b"\n":
            entry["result"] = "failed_preservation_strip"
            entries.append(entry); print(f"FAIL {profile}: preservation strip"); continue
        os.replace(tmp_root, root)
        entry["root_sha256_after"] = sha256_path(root)
        entry["root_bytes_after"] = root.stat().st_size
        entry["root_bytes_before"] = len(original_root_bytes)
        entry["hook_sha256"] = hook_sha
        entry["hook_appended_count"] = 1
        entry["commands"] = [
            f"read {root}",
            f"write tmp ref + atomic replace -> {ref}",
            f"append LOAD-HOOK.md bytes to tmp root + atomic replace -> {root}",
        ]
        entry["result"] = "installed"
        entries.append(entry)
        print(f"OK   {profile}: installed ref+hook")

    finished_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    rollout = {
        "task_id": "t_87ddea42",
        "started_at_utc": started_utc,
        "finished_at_utc": finished_utc,
        "subject": {
            "method_candidate_sha256": EXPECTED_REFERENCE_SHA256,
            "method_candidate_sha1": EXPECTED_CANDIDATE_SHA1,
            "load_hook_sha256": EXPECTED_HOOK_SHA256,
        },
        "entries": entries,
        "summary": {
            "targets": len(entries),
            "installed": sum(1 for e in entries if e["result"] == "installed"),
            "skipped_root_drift": sum(1 for e in entries if e["result"] == "skipped_root_drift"),
            "skipped_reference_collision": sum(1 for e in entries if e["result"] == "skipped_reference_collision"),
            "failed": sum(1 for e in entries if e["result"].startswith("failed")),
        }
    }
    ROLLOUT_JSON.write_text(json.dumps(rollout, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"ROLLOUT.json written: {ROLLOUT_JSON}")
    print(json.dumps(rollout["summary"], indent=2))
    return 0 if rollout["summary"]["failed"] == 0 else 5

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "guard"
    if mode == "guard":
        sys.exit(guard())
    elif mode == "install":
        sys.exit(install())
    else:
        print(f"unknown mode {mode}"); sys.exit(2)
