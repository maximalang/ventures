# Supplemental independent QA checker for t_a1ec6fed (read-only on subject).
# Basis: re-implements the acceptance assertions of the original QA script
# (_qa_check_t_a3c78661.py) without overwriting its artifact, plus errata-hash,
# original-report byte-unchanged, and original-QA artifact hash checks.
# Writes QA-ERRATA-CHECK-t_a1ec6fed.json only.
import hashlib, json, os, sys

PACKET = r"C:\Users\max\Desktop\all\ventures\docs\fleet-ops\dots-20261003"
PROFILES_ROOT = r"C:\Users\max\AppData\Local\hermes\profiles"
DEFAULT_HERMES = r"C:\Users\max\AppData\Local\hermes"
CAND_SHA256 = "f2a85ced87b620bf08cdfc2f3de85ce004a2912efded4da85b668148f00dce6f"
CAND_SHA1 = "fd6c26f5dbebba33baa17761f43a80e22ed17427"
HOOK_SHA256 = "2e10a1c6153947db1c2f335ea7037fa0522111f5be6ec31d83ebb345b9768ec9"
ERRATA_SHA256 = "e07e24518f29029102deb430f92f0c061512fff9e3ca5caeede222b551485c94"
QA_MD_SHA256 = "6567e7c91103c0ee34b6262de238843ec055d8c342ac4df8342260c3b7dcc6cd"
QA_JSON_SHA256 = "7f45e721449ce9c28cd011e1e6805059b6b96d3cc1c0786d0be40fbd00bc7451"
SA_SHA256 = "9bc7d4a5c71a2befb1f6c7947c5a4805ad7cf03ae4ba7f9c9bf8631dc3acbca4"
ROLLOUT_MD_SHA256 = "b01b0cdce4124a44010f83ee61483d5d1a33c3e30c39e4fce53e902afed1dd36"
ROLLOUT_JSON_SHA256 = "1d63c2f8d33bbde63074fe186c464580e86b6e04e197b477cc2a8fba88b7cdc1"
BRAIN_SHA256 = "f76a04a02d97e19a97d3dc912a11569d64e608c728aeed342536b5fe719d9bc9"

def rb(p):
    with open(p, "rb") as f:
        return f.read()
def h256(b): return hashlib.sha256(b).hexdigest()
def h1(b): return hashlib.sha1(b).hexdigest()

R = {"checks": {}, "findings": []}
def ok(name, cond, detail=""):
    R["checks"][name] = {"pass": bool(cond), "detail": detail}
    return bool(cond)

# ---------- A. frozen inputs still byte-identical ----------
cand = rb(os.path.join(PACKET, "METHOD-CANDIDATE.md"))
hook = rb(os.path.join(PACKET, "LOAD-HOOK.md"))
brain_bytes = rb(os.path.join(PACKET, "BRAIN-PACKET.json"))
ok("A.candidate_sha256", h256(cand) == CAND_SHA256, h256(cand))
ok("A.candidate_sha1", h1(cand) == CAND_SHA1, h1(cand))
ok("A.hook_sha256", h256(hook) == HOOK_SHA256, h256(hook))
ok("A.brain_packet_sha256", h256(brain_bytes) == BRAIN_SHA256, h256(brain_bytes))
brain = json.loads(brain_bytes.decode("utf-8"))
members = brain["input_members"]
mem_res = []
for m in members:
    p = m["path"]
    exists = os.path.isfile(p)
    b = rb(p) if exists else b""
    good = exists and len(b) == m["bytes"] and h256(b) == m["sha256"]
    mem_res.append({"name": m["name"], "hash_ok": good})
ok("A.brain_members_10_10", len(members) == 10 and all(x["hash_ok"] for x in mem_res),
   "%d/%d OK" % (sum(x["hash_ok"] for x in mem_res), len(mem_res)))
R["brain_members_count"] = len(members)

# original affected reports byte-unchanged vs spec fingerprints
sa = rb(os.path.join(PACKET, "SOURCE-AUDIT.md"))
rmd = rb(os.path.join(PACKET, "ROLLOUT.md"))
rjs = rb(os.path.join(PACKET, "ROLLOUT.json"))
ok("A.originals_byte_unchanged",
   h256(sa) == SA_SHA256 and h256(rmd) == ROLLOUT_MD_SHA256 and h256(rjs) == ROLLOUT_JSON_SHA256,
   "SA=%s RM=%s RJ=%s" % (h256(sa)[:12], h256(rmd)[:12], h256(rjs)[:12]))

# errata + original QA artifacts present at expected hashes
err = rb(os.path.join(PACKET, "EVIDENCE-ERRATA.md"))
ok("A.errata_sha256", h256(err) == ERRATA_SHA256, h256(err))
qa_md = rb(os.path.join(PACKET, "QA.md"))
qa_js = rb(os.path.join(PACKET, "QA.json"))
ok("A.original_QA_md_sha256", h256(qa_md) == QA_MD_SHA256, h256(qa_md))
ok("A.original_QA_json_sha256", h256(qa_js) == QA_JSON_SHA256, h256(qa_js))

# ---------- B. Q1 targets ----------
tb = json.loads(rb(os.path.join(PACKET, "TARGETS-BASELINE.json")).decode("utf-8"))
targets = tb["targets"]
profiles = [t["profile"] for t in targets]
roots = [t["root_path"] for t in targets]
refs = [t["new_reference_path"] for t in targets]
ok("B.Q1_count_12", len(targets) == 12, "n=%d" % len(targets))
ok("B.Q1_profiles_unique", len(set(profiles)) == 12, str(sorted(profiles)))
ok("B.Q1_paths_unique", len(set(roots)) == 12 and len(set(refs)) == 12, "")
ok("B.Q1_no_case_collisions",
   len({p.lower() for p in profiles}) == 12 and
   len({r.lower() for r in roots}) == 12 and
   len({r.lower() for r in refs}) == 12, "")
EXPECTED = ["company","research","product","operations","qa","tech","finance",
            "sales","design","ux","video-director","video-editor"]
ok("B.Q1_exact_profile_set", sorted(profiles) == sorted(EXPECTED), str(sorted(profiles)))
ok("B.Q1_root_exists_all", all(os.path.isfile(r) for r in roots), "")
ok("B.Q1_reference_exists_all", all(os.path.isfile(r) for r in refs),
   "missing=%s" % [r for r in refs if not os.path.isfile(r)])
roll = json.loads(rjs.decode("utf-8"))
roll_profiles = [e["profile"] for e in roll["entries"]]
ok("B.Q1_rollout_matches_baseline", sorted(roll_profiles) == sorted(profiles), "")

# ---------- C. Q2 fresh reference hashes ----------
ref_hashes = {}
for t in targets:
    ref_hashes[t["profile"]] = h256(rb(t["new_reference_path"]))
ok("C.Q2_all_refs_equal_candidate", all(v == CAND_SHA256 for v in ref_hashes.values()), "")
ok("C.Q2_unique_hash_count_1", len(set(ref_hashes.values())) == 1,
   "unique=%s" % sorted(set(ref_hashes.values())))
R["ref_hashes_fresh"] = ref_hashes

# ---------- D. Q3 hook + backups ----------
q3 = {}
for t, e in zip(targets, roll["entries"]):
    p = t["profile"]
    root = rb(t["root_path"])
    cnt = root.count(hook)
    link_ok = (b"references/dots-operating-method.md" in hook and
               os.path.isfile(os.path.join(t["skill_root"], "references", "dots-operating-method.md")))
    mode = None
    backup = rb(e["backup_root"]["path"])
    if root.endswith(hook):
        base = root[:-len(hook)]
        if base == backup:
            mode = "direct"
        elif base.endswith(b"\n") and base[:-1] == backup:
            mode = "lf_inserted"
    backup_sha_ok = (h256(backup) == e["backup_root"]["sha256"] ==
                     e["original_root_sha256"] == t["baseline_sha256"])
    fm_ok = root.startswith(b"---") and b"\n---" in root[:2000]
    q3[p] = {"hook_count": cnt, "link_ok": link_ok, "minus_hook_mode": mode,
             "backup_sha_ok": backup_sha_ok, "frontmatter_ok": fm_ok}
ok("D.Q3_hook_count_1_all", all(v["hook_count"] == 1 for v in q3.values()),
   json.dumps({k: v["hook_count"] for k, v in q3.items()}))
ok("D.Q3_link_valid_all", all(v["link_ok"] for v in q3.values()), "")
ok("D.Q3_minus_hook_reproduces_backup",
   all(v["minus_hook_mode"] in ("direct", "lf_inserted") for v in q3.values()),
   json.dumps({k: v["minus_hook_mode"] for k, v in q3.items()}))
ok("D.Q3_backup_sha_chain_ok", all(v["backup_sha_ok"] for v in q3.values()), "")
ok("D.Q3_frontmatter_intact", all(v["frontmatter_ok"] for v in q3.values()), "")
R["targets_q3"] = {k: {kk: vv for kk, vv in v.items()} for k, v in q3.items()}

# ---------- E. Q4 fresh root hashes vs after-manifest; default profile ----------
drift = {}
for t, e in zip(targets, roll["entries"]):
    fresh = h256(rb(t["root_path"]))
    drift[t["profile"]] = {"fresh": fresh, "manifest_after": e["root_sha256_after"],
                           "match": fresh == e["root_sha256_after"]}
ok("E.Q4_fresh_matches_after_manifest_all12", all(v["match"] for v in drift.values()),
   json.dumps({k: v["match"] for k, v in drift.items()}))
R["root_drift_fresh"] = drift
def_co = os.path.join(DEFAULT_HERMES, "skills", "company-os")
def_ref = os.path.join(def_co, "references", "dots-operating-method.md")
def_skill = os.path.join(def_co, "SKILL.md")
def_hook_present = os.path.isfile(def_skill) and (hook in rb(def_skill))
ok("E.Q4_default_profile_untouched",
   (not os.path.isfile(def_ref)) and (not def_hook_present),
   "default_ref_exists=%s default_hook_present=%s" % (os.path.isfile(def_ref), def_hook_present))

# ---------- F. six original-report defect facts re-captured programmatically ----------
rep = {}
sa_lines = sa.decode("utf-8").splitlines()
rmd_lines = rmd.decode("utf-8").splitlines()
cand_text = cand.decode("utf-8", "replace")
cand_lines = cand_text.splitlines()
rep["SA47_48_codex_not_dots_attribution_present"] = any(
    ("codex-not-dots" in sa_lines[i]) for i in (46, 47) if i < len(sa_lines))
rep["SA57_65_R0_R6_attribution_present"] = (("R0" in sa_lines[56]) if len(sa_lines) > 56 else False) or \
                                            (("R6" in sa_lines[64]) if len(sa_lines) > 64 else False)
rep["candidate_contains_codex_or_DoT_or_deny_first"] = any(
    s in cand_text.lower() for s in ("codex", "dot ", "deny-first"))
rep["candidate_contains_R0_R6"] = ("R0" in cand_text) or ("R6" in cand_text)
rep["candidate_line34"] = cand_lines[33] if len(cand_lines) >= 34 else None
rep["ROLLOUT_line3_has_t_2c44dd2f"] = "t_2c44dd2f" in (rmd_lines[2] if len(rmd_lines) > 2 else "")
rep["ROLLOUT_line24_claims_11"] = "11 frozen BRAIN-PACKET members" in (rmd_lines[23] if len(rmd_lines) > 23 else "")
rep["ROLLOUT_line119_no_spend_incurred"] = "no spend authorized or incurred" in (rmd_lines[118] if len(rmd_lines) > 118 else "")
rep["brain_members_actual"] = len(members)
rollout_text = "\n".join(rmd_lines)
rb_sec = rollout_text[rollout_text.find("## Rollback"):] if "## Rollback" in rollout_text else ""
rep["rollback_sec_checks_ref_hash"] = CAND_SHA256[:12] in rb_sec
# OBS-1: candidate line 87 'idempotent recovery'
rep["candidate_line87_has_idempotent_recovery"] = (
    len(cand_lines) >= 87 and "idempotent recovery" in cand_lines[86])
R["report_checks"] = rep
# defect presence must match errata's account: defects present in originals, absent in candidate
ok("F.defects_present_in_originals",
   all((rep["SA47_48_codex_not_dots_attribution_present"],
        rep["SA57_65_R0_R6_attribution_present"],
        rep["ROLLOUT_line3_has_t_2c44dd2f"],
        rep["ROLLOUT_line24_claims_11"],
        rep["ROLLOUT_line119_no_spend_incurred"])),
   json.dumps({k: rep[k] for k in (
       "SA47_48_codex_not_dots_attribution_present", "SA57_65_R0_R6_attribution_present",
       "ROLLOUT_line3_has_t_2c44dd2f", "ROLLOUT_line24_claims_11",
       "ROLLOUT_line119_no_spend_incurred")}))
ok("F.candidate_free_of_false_attributions",
   (not rep["candidate_contains_codex_or_DoT_or_deny_first"]) and
   (not rep["candidate_contains_R0_R6"]) and
   ("Attention" in (rep["candidate_line34"] or "")),
   "line34=%r" % rep["candidate_line34"])
ok("F.OBS1_candidate_line87_idempotent_recovery", rep["candidate_line87_has_idempotent_recovery"],
   cand_lines[86] if len(cand_lines) >= 87 else "")

# ---------- G. operator-flagged residual errata over-claims (mid-run note) ----------
g = {}
# G1: no install-time member-verification receipt exists anywhere in captured evidence
rjs_text = rjs.decode("utf-8")
inst_text = rb(os.path.join(PACKET, "_rollout_t_87ddea42.py")).decode("utf-8")
g["rollout_json_has_member_receipts"] = any(
    k in rjs_text for k in ('"input_members"', '"members"', '"brain"', '"preflight"'))
# installer hashes exactly: METHOD (sha256+sha1), HOOK, TARGETS baseline roots/reference
g["installer_hashes_fixed_inputs_only"] = (
    "EXPECTED_REFERENCE_SHA256" in inst_text and
    "EXPECTED_HOOK_SHA256" in inst_text and
    "EXPECTED_CANDIDATE_SHA1" in inst_text and
    "BRAIN" not in inst_text)
# G2: baseline carries no supporting-file before-inventory; verify check6 prints, does not compare
tb_keys = set(tb.keys())
t0_keys = set(tb["targets"][0].keys())
g["baseline_has_file_inventory"] = any("inventory" in k or "files" in k for k in tb_keys | t0_keys)
ver_text = rb(os.path.join(PACKET, "_verify_t_87ddea42.py")).decode("utf-8")
chk6 = ver_text[ver_text.find("# 6."):ver_text.find("# 7.")] if "# 6." in ver_text else ""
g["verify_check6_performs_comparison"] = ("!=" in chk6 or "==" in chk6 or "diff" in chk6.lower())
R["residual_errata_overclaims"] = {
    "E1_install_time_member_verification_unreceipted": (
        not g["rollout_json_has_member_receipts"]) and g["installer_hashes_fixed_inputs_only"],
    "E2_baseline_before_inventory_absent_no_comparison": (
        not g["baseline_has_file_inventory"]) and (not g["verify_check6_performs_comparison"]),
    "detail": g,
}
ok("G.E1_no_install_time_member_receipt",
   R["residual_errata_overclaims"]["E1_install_time_member_verification_unreceipted"],
   json.dumps(g))
ok("G.E2_no_before_inventory_no_comparison",
   R["residual_errata_overclaims"]["E2_baseline_before_inventory_absent_no_comparison"],
   "baseline_target_keys=%s" % sorted(t0_keys))

all_pass = all(c["pass"] for c in R["checks"].values())
R["overall_all_checks_pass"] = all_pass
R["check_count"] = len(R["checks"])

out_path = os.path.join(PACKET, "QA-ERRATA-CHECK-t_a1ec6fed.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(R, f, indent=2, ensure_ascii=False)
print("WROTE", out_path)
for k, v in R["checks"].items():
    print(("PASS " if v["pass"] else "FAIL ") + k + (" | " + v["detail"] if v["detail"] else ""))
print("CHECKS:", len(R["checks"]), "OVERALL:", "PASS" if all_pass else "FAIL")
sys.exit(0 if all_pass else 1)
