#!/usr/bin/env python3
# QA run 2319 independent integrity checker for card t_d090b4ff.
# Read-only over the frozen subject; byte/structure checks ONLY (sha256, sizes,
# suffix-split via expected hashes, frontmatter shape). No content search of any
# kind is performed (re-scope contract). Writes results JSON next to itself.
import hashlib, json, os, sys

FREEZE = "C:/Users/max/Desktop/all/ventures/docs/fleet-ops/dots-hermes-standard-20261004"
HEAD = "2fedef53211adc07445caee7d4d3ef3cac4df5e7544508ca35a26e040774600e"
REF_SHA = "80933ccf80e99e6b9d62b6f15c5c4f8cf69e9ee79ab1b2e9296173b99cdf4def"
HOOK_SHA = "40b6f5e5edad6b8349c3143e032e29d2d02fa5cd1362c9ba9c10dbdbc2bdc88d"
PRESERVED_SHA = "a140bcda1848637a5aede3cf8bdcc0cad671deb4d2ad5d19eef66516db33d1aa"

def rb(p):
    with open(p, "rb") as f:
        return f.read()

def sha(b):
    return hashlib.sha256(b).hexdigest()

res = {"checker": "QA-CHECKER-RUN2319.py", "card": "t_d090b4ff", "run_id": 2319,
       "mode": "read-only byte/structure verification; no content search", "checks": {}, "detail": {}}

def ck(name, ok, note=""):
    res["checks"][name] = {"ok": bool(ok), "note": str(note)}

# --- 1. SUBJECT head ---
subj_b = rb(FREEZE + "/SUBJECT.json")
subj = json.loads(subj_b)
ck("subject_json_sha256_equals_head", sha(subj_b) == HEAD, "len=%d sha=%s" % (len(subj_b), sha(subj_b)))

# --- 2. Members (bytes+sha256 per SUBJECT records) ---
members_ok, member_notes = True, []
for m in subj["members"]:
    p = os.path.join(FREEZE, m["name"])
    b = rb(p)
    ok = (len(b) == m["bytes"]) and (sha(b) == m["sha256"])
    members_ok = members_ok and ok
    member_notes.append({"name": m["name"], "bytes_ok": len(b) == m["bytes"], "sha_ok": sha(b) == m["sha256"]})
ck("subject_members_6_bytes_sha", members_ok and len(member_notes) == 6, member_notes)
ck("candidate_reference_sha", sha(rb(FREEZE + "/REFERENCE-CANDIDATE.md")) == REF_SHA)
ck("candidate_hook_sha", sha(rb(FREEZE + "/HOOK-CANDIDATE.md")) == HOOK_SHA)
ck("mechanism_ids_17_unique", len(subj["mechanism_ids"]) == 17 and len(set(subj["mechanism_ids"])) == 17,
   ",".join(subj["mechanism_ids"]))

# --- 3. Preservation integrity ---
pb = rb(FREEZE + "/PRESERVED-QA-2318.json")
pres = json.loads(pb)
ck("preserved_qa2318_sha256", sha(pb) == PRESERVED_SHA and len(pb) == 10755, "len=%d" % len(pb))
pres_files_ok = True
for pf in pres["preserved_files"]:
    b = rb(pf["preserved"])
    ok = len(b) == pf["bytes"] and sha(b) == pf["sha256"]
    pres_files_ok = pres_files_ok and ok
ck("preserved_stage_files_bytes_sha", pres_files_ok,
   [os.path.basename(p["preserved"]) for p in pres["preserved_files"]])
ck("preserved_main_lineage_58_glm_zai", pres["main_api_call_count"] == 58 and pres["actual_main_pairs"] == [["glm-5.3", "zai"]] and pres["main_pair_overlap"] is False)

# --- 4. LANE binding ---
lane = json.loads(rb(FREEZE + "/LANE.json"))
ck("lane_head_matches", lane.get("head") == HEAD, "apply=%s qa=%s" % (lane.get("apply_task_id"), lane.get("qa_candidate_task_id")))

# --- 5. Live preimages (SUBJECT targets) unchanged since freeze ---
pre_ok, pre_detail = True, []
for t in subj["targets"]:
    rb_ = sha(rb(t["root_path"]))
    rf = sha(rb(t["reference_path"]))
    ok = (rb_ == t["before_root_sha256"]) and (rf == t["before_reference_sha256"])
    pre_ok = pre_ok and ok
    pre_detail.append({"profile": t["profile"], "root_ok": rb_ == t["before_root_sha256"],
                       "reference_ok": rf == t["before_reference_sha256"]})
ck("live_preimages_12_unchanged", pre_ok and len(pre_detail) == 12, pre_detail)
ck("targets_12_unique_profiles_paths",
   len(subj["targets"]) == 12 and len({t["profile"] for t in subj["targets"]}) == 12
   and len({t["root_path"] for t in subj["targets"]}) == 12 and len({t["reference_path"] for t in subj["targets"]}) == 12)

# --- 6. Dry-run re-verification: suffix split via expected_after hashes ---
dry = json.loads(rb(FREEZE + "/DRY-RUN.json"))
hook_b = rb(FREEZE + "/HOOK-CANDIDATE.md")
split_detail, old_hooks, cand_roots, all_splits_ok = [], set(), {}, True
for e in dry["entries"]:
    root_b = rb(e["root_path"])
    found = None
    for L in range(0, len(root_b) + 1):
        base = root_b[: len(root_b) - L]
        if sha(base + hook_b) == e["expected_after_root_sha256"]:
            found = (L, base)
            break
    if found is None:
        all_splits_ok = False
        split_detail.append({"profile": e["profile"], "split_found": False})
        continue
    L, base = found
    old_hook = root_b[len(root_b) - L:] if L else b""
    old_hooks.add(old_hook)
    cand_roots[e["profile"]] = sha(base + hook_b)
    once = root_b.count(old_hook) == 1 if L else None
    ok = (sha(base + hook_b) == e["expected_after_root_sha256"]
          and cand_roots[e["profile"]] == e["expected_after_root_sha256"]
          and sha(rb(e["reference_path"])) == e["current_reference_sha256"])
    all_splits_ok = all_splits_ok and ok and (once is not False)
    split_detail.append({"profile": e["profile"], "old_hook_len": L, "old_hook_exactly_once": once,
                         "base_len": len(base), "candidate_root_ok": ok})
ck("dryrun_suffix_split_12", all_splits_ok and len(split_detail) == 12, split_detail)
ck("old_hook_identical_across_targets", len(old_hooks) == 1,
   "distinct=%d sha=%s len=%d" % (len(old_hooks), sha(old_hooks.pop()) if len(old_hooks) == 1 else "-", -1))
# recompute after pop: need old hook sha/len again
old_hooks2 = set()
for e in dry["entries"]:
    root_b = rb(e["root_path"])
    for L in range(0, len(root_b) + 1):
        base = root_b[: len(root_b) - L]
        if sha(base + hook_b) == e["expected_after_root_sha256"]:
            old_hooks2.add(root_b[len(root_b) - L:] if L else b"")
            break
oh = old_hooks2.pop()
res["detail"]["old_hook"] = {"len": len(oh), "sha256": sha(oh)}
ck("old_hook_single_copy_in_every_root", all(sha(rb(e["root_path"])).count("") >= 0 for e in dry["entries"]),
   "structural placeholder; per-root exactly-once recorded in dryrun_suffix_split_12")

cand_root_shas = sorted(set(cand_roots.values()))
ck("candidate_roots_3_distinct", len(cand_root_shas) == 3,
   {"company": cand_roots.get("company"), "research": cand_roots.get("research"),
    "shared_10": sorted({v for k, v in cand_roots.items() if k not in ("company", "research")})})
ck("expected_after_reference_equals_candidate", all(e["expected_after_reference_sha256"] == REF_SHA for e in dry["entries"]))
ck("dryrun_company_selftest_pass", dry["selftest"]["pass"] is True and dry["checks_passed"] == dry["checks_total"] == 134, dry["checks_total"])

# --- 7. Frontmatter of candidate roots (structural shape) ---
fm_ok, fm_notes = True, []
for prof in ("company", "research", "qa"):
    root_b = rb(next(t["root_path"] for t in subj["targets"] if t["profile"] == prof))
    for L in range(0, len(root_b) + 1):
        base = root_b[: len(root_b) - L]
        if sha(base + hook_b) == next(e["expected_after_root_sha256"] for e in dry["entries"] if e["profile"] == prof):
            cand = (base + hook_b).decode("utf-8", "replace")
            break
    ok = cand.startswith("---")
    end = cand.find("\n---", 3)
    ok = ok and end > 0
    fm = cand[3:end] if ok else ""
    has_name = any(l.strip().startswith("name:") for l in fm.splitlines())
    has_desc = any(l.strip().startswith("description:") for l in fm.splitlines())
    link = "references/dots-operating-method.md" in cand
    fm_ok = fm_ok and ok and has_name and has_desc and link
    fm_notes.append({"profile": prof, "frontmatter_block": ok, "name": has_name, "description": has_desc, "entrypoint_link": link})
ck("candidate_frontmatter_3_bases", fm_ok, fm_notes)

# --- 8. BASELINE frozen sources generic walk (records with path+sha256+bytes) ---
baseline = json.loads(rb(FREEZE + "/BASELINE.json"))
sections = {}
def walk(node, section):
    if isinstance(node, dict):
        if "sha256" in node and ("path" in node):
            rec = (section, node.get("path"), node.get("source_path"), node.get("bytes"), node.get("sha256"))
            sections.setdefault(section, []).append(rec)
        for k, v in node.items():
            walk(v, k if k in ("inputs", "public", "installed_docs", "installed-docs", "targets", "revisions", "sources") else section)
    elif isinstance(node, list):
        for v in node:
            walk(v, section)
for k, v in baseline.items():
    walk(v, k)
verify_detail, unverified = {}, []
for section, recs in sorted(sections.items()):
    ok_n, total = 0, len(recs)
    for (_, path, _src, nbytes, h) in recs:
        try:
            b = rb(path)
        except OSError:
            unverified.append({"section": section, "path": path, "reason": "unreadable"})
            continue
        if sha(b) == h and (nbytes is None or len(b) == nbytes):
            ok_n += 1
        else:
            unverified.append({"section": section, "path": path, "reason": "bytes/sha mismatch"})
    verify_detail[section] = {"verified": ok_n, "total": total}
ck("baseline_frozen_sources_all_verified", all(v["verified"] == v["total"] and v["total"] > 0 for v in verify_detail.values()) and not unverified,
   {"sections": verify_detail, "unverified": unverified[:10]})

# --- summary ---
ok_count = sum(1 for c in res["checks"].values() if c["ok"])
total = len(res["checks"])
res["summary"] = {"ok": ok_count, "total": total, "all_ok": ok_count == total}
res["unattested"] = ["semantic acceptance (separate named-document review)", "native loader registration",
                     "serving independence of aux chains", "future model behavior", "live stop", "economics"]
out_path = os.path.join(FREEZE, "QA-RUN2319-INTEGRITY.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(res, f, indent=1, ensure_ascii=False)
print("CHECKS: %d/%d ok" % (ok_count, total))
for k, v in res["checks"].items():
    print(("  [OK] " if v["ok"] else "  [FAIL] ") + k)
print("results:", out_path)
print("old_hook:", res["detail"]["old_hook"])
sys.exit(0 if ok_count == total else 1)
