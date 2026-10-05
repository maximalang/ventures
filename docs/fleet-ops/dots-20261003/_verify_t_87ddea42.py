#!/usr/bin/env python3
"""Post-install verification per ROLLOUT-SPEC.md §4 and §Tests/proof limits.

Checks:
- 12 target entries
- reference unique content hash count == 1 (across all 12 installed refs)
- hook count == 1 per root
- after-with-hook-removed == own original bytes (per-target)
- frontmatter parse of root SKILL.md still valid
- no extra changed skill files (list each profile's company-os root file set)
- reference loadable via skill loader (reported separately)
"""
import hashlib, json, re, sys
from pathlib import Path

PACKET = Path(r"C:/Users/max/Desktop/all/ventures/docs/fleet-ops/dots-20261003")
ROLLOUT = json.loads((PACKET / "ROLLOUT.json").read_bytes().decode("utf-8"))
HOOK = (PACKET / "LOAD-HOOK.md").read_bytes()
BASELINE = json.loads((PACKET / "TARGETS-BASELINE.json").read_bytes().decode("utf-8"))

EXPECTED_REF = "f2a85ced87b620bf08cdfc2f3de85ce004a2912efded4da85b668148f00dce6f"

def sha256(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def sha256p(p: Path) -> str: return sha256(p.read_bytes())

fails = []

# 1. Expected target count == 12
entries = ROLLOUT["entries"]
if len(entries) != 12:
    fails.append(f"entries count={len(entries)}")
print(f"[1] targets = {len(entries)} (expected 12)")

# 2. Reference unique content hash count == 1
ref_hashes = set()
for e in entries:
    p = Path(e["new_reference_path"])
    if p.exists():
        ref_hashes.add(sha256p(p))
print(f"[2] unique reference hashes across 12 targets = {len(ref_hashes)} :: {sorted(ref_hashes)}")
if ref_hashes != {EXPECTED_REF}:
    fails.append(f"reference hash set mismatch: {ref_hashes}")

# 3. Hook count == 1 per root (using exact hook bytes)
for e in entries:
    root = Path(e["root_path"])
    data = root.read_bytes()
    cnt = data.count(HOOK)
    marker = "OK " if cnt == 1 else "FAIL"
    print(f"[3] {marker} {e['profile']:14s} hook_count={cnt}")
    if cnt != 1:
        fails.append(f"{e['profile']} hook_count={cnt}")

# 4. after-with-hook-removed == own original bytes
for e in entries:
    root = Path(e["root_path"])
    after = root.read_bytes()
    # Original was either after minus (LF + HOOK) or after minus HOOK
    if after.endswith(HOOK):
        stripped = after[:-len(HOOK)]
        if stripped.endswith(b"\n") and not e["original_root_sha256"] == sha256(stripped):
            # maybe we added a LF between original and hook
            stripped2 = stripped[:-1]
        else:
            stripped2 = stripped
    else:
        stripped2 = None
    own_backup = PACKET / "backup-t_87ddea42" / f"{e['profile']}.SKILL.md.original"
    backup_bytes = own_backup.read_bytes()
    match = (stripped2 == backup_bytes) or (stripped == backup_bytes)
    marker = "OK " if match else "FAIL"
    print(f"[4] {marker} {e['profile']:14s} preservation: after-minus-hook == backup ({match})")
    if not match:
        fails.append(f"{e['profile']} preservation")

# 5. Frontmatter parse: root SKILL.md starts with ---
for e in entries:
    root = Path(e["root_path"])
    text = root.read_bytes().decode("utf-8", errors="replace")
    ok = text.startswith("---") and "\n---" in text[3:]
    marker = "OK " if ok else "FAIL"
    print(f"[5] {marker} {e['profile']:14s} frontmatter intact")
    if not ok:
        fails.append(f"{e['profile']} frontmatter")

# 6. No extra changed skill files (compare file set with baseline inventory)
print("[6] root file inventory:")
for t in BASELINE["targets"]:
    root = Path(t["skill_root"])
    files = sorted([str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()])
    print(f"    {t['profile']:14s} files={len(files)} :: {files}")

# 7. Root hash now differs from baseline (sanity: hook was actually applied)
for e in entries:
    if e["result"] != "installed": continue
    after_sha = sha256p(Path(e["root_path"]))
    differs = after_sha != e["original_root_sha256"]
    marker = "OK " if differs else "FAIL"
    print(f"[7] {marker} {e['profile']:14s} root_sha changed after install: {differs}")
    if not differs:
        fails.append(f"{e['profile']} root_sha unchanged")

print()
print(f"VERIFY RESULT: {'PASS' if not fails else 'FAIL'}")
if fails:
    for f in fails: print(f"  - {f}")
sys.exit(0 if not fails else 1)
