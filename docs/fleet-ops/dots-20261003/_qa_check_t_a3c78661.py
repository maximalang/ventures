# Independent QA check script for t_a3c78661 (read-only on subject).
# Implements QA-SPEC Q1-Q4, Q9 assertions independently of producer scripts,
# plus input-hash verification and programmatic report-line checks for the
# operator-flagged evidence-report discrepancies. Writes QA-CHECK-t_a3c78661.json.
import hashlib, json, os, sys

PACKET = r"C:\Users\max\Desktop\all\ventures\docs\fleet-ops\dots-20261003"
PROFILES_ROOT = r"C:\Users\max\AppData\Local\hermes\profiles"
DEFAULT_HERMES = r"C:\Users\max\AppData\Local\hermes"
CAND_SHA256 = "f2a85ced87b620bf08cdfc2f3de85ce004a2912efded4da85b668148f00dce6f"
CAND_SHA1 = "fd6c26f5dbebba33baa17761f43a80e22ed17427"
HOOK_SHA256 = "2e10a1c6153947db1c2f335ea7037fa0522111f5be6ec31d83ebb345b9768ec9"
AUTHOR_READBACK_SHA = "68def3834652ad7a161a579ee0141e02df3e8a0160c3c0596eb1a706ce2cc351"

def rb(p):
    with open(p, "rb") as f:
        return f.read()
def h256(b): return hashlib.sha256(b).hexdigest()
def h1(b): return hashlib.sha1(b).hexdigest()

R = {"checks": {}, "findings": [], "targets": {}}
def ok(name, cond, detail=""):
    R["checks"][name] = {"pass": bool(cond), "detail": detail}
    return bool(cond)

# ---------- 0. input hash verification ----------
brain = json.loads(rb(os.path.join(PACKET, "BRAIN-PACKET.json")).decode("utf-8"))
members = brain["input_members"]
mem_res = []
for m in members:
    p = m["path"]
    exists = os.path.isfile(p)
    b = rb(p) if exists else b""
    good = exists and len(b) == m["bytes"] and h256(b) == m["sha256"]
    mem_res.append({"name": m["name"], "exists": exists, "hash_ok": good})
ok("inputs.brain_members", all(x["hash_ok"] for x in mem_res),
   "%d/%d members hash-verified" % (sum(x["hash_ok"] for x in mem_res), len(mem_res)))
R["brain_members_count"] = len(members)
R["brain_members_detail"] = mem_res

brain_bytes = rb(os.path.join(PACKET, "BRAIN-PACKET.json"))
R["brain_packet_sha256"] = h256(brain_bytes)
cand_path = os.path.join(PACKET, "METHOD-CANDIDATE.md")
cand = rb(cand_path)
ok("inputs.candidate_sha256", h256(cand) == CAND_SHA256, h256(cand))
ok("inputs.candidate_sha1", h1(cand) == CAND_SHA1, h1(cand))
hook = rb(os.path.join(PACKET, "LOAD-HOOK.md"))
ok("inputs.hook_sha256", h256(hook) == HOOK_SHA256, h256(hook))
R["candidate_lines"] = cand.decode("utf-8", "replace").splitlines()
R["candidate_line_count"] = len(R["candidate_lines"])

# ---------- Q1: targets count/dedupe/collision/reference existence ----------
tb = json.loads(rb(os.path.join(PACKET, "TARGETS-BASELINE.json")).decode("utf-8"))
targets = tb["targets"]
profiles = [t["profile"] for t in targets]
roots = [t["root_path"] for t in targets]
refs = [t["new_reference_path"] for t in targets]
ok("Q1.count_12", len(targets) == 12, "n=%d" % len(targets))
ok("Q1.profiles_unique", len(set(profiles)) == 12, str(sorted(profiles)))
ok("Q1.paths_unique", len(set(roots)) == 12 and len(set(refs)) == 12, "")
ok("Q1.no_case_collisions",
   len({p.lower() for p in profiles}) == 12 and
   len({r.lower() for r in roots}) == 12 and
   len({r.lower() for r in refs}) == 12, "")
ok("Q1.reference_exists_all", all(os.path.isfile(r) for r in refs),
   "missing=%s" % [r for r in refs if not os.path.isfile(r)])
ok("Q1.root_exists_all", all(os.path.isfile(r) for r in roots), "")
EXPECTED = ["company","research","product","operations","qa","tech","finance",
            "sales","design","ux","video-director","video-editor"]
ok("Q1.exact_profile_set", sorted(profiles) == sorted(EXPECTED), str(sorted(profiles)))

roll = json.loads(rb(os.path.join(PACKET, "ROLLOUT.json")).decode("utf-8"))
roll_profiles = [e["profile"] for e in roll["entries"]]
ok("Q1.rollout_matches_baseline", sorted(roll_profiles) == sorted(profiles), "")

# ---------- Q2: reference hashes ----------
ref_hashes = {}
ref_equal_candidate_bytes = {}
for t in targets:
    b = rb(t["new_reference_path"])
    ref_hashes[t["profile"]] = h256(b)
    ref_equal_candidate_bytes[t["profile"]] = (b == cand)
ok("Q2.all_refs_equal_candidate_sha", all(v == CAND_SHA256 for v in ref_hashes.values()), "")
ok("Q2.unique_hash_count_1", len(set(ref_hashes.values())) == 1,
   "unique=%s" % sorted(set(ref_hashes.values())))
ok("Q2.refs_byte_equal_candidate", all(ref_equal_candidate_bytes.values()), "")

# ---------- Q3: hook once, valid link, minus-hook == backup ----------
q3 = {}
for t, e in zip(targets, roll["entries"]):
    p = t["profile"]
    root = rb(t["root_path"])
    cnt = root.count(hook)
    # link validity: hook mentions relative reference that exists in same root
    link_ok = (b"references/dots-operating-method.md" in hook and
               os.path.isfile(os.path.join(t["skill_root"], "references", "dots-operating-method.md")))
    # minus-hook reconstruction
    mode = None
    backup_path = e["backup_root"]["path"]
    backup = rb(backup_path)
    if root.endswith(hook):
        base = root[:-len(hook)]
        if base == backup:
            mode = "direct"
        elif base.endswith(b"\n") and base[:-1] == backup:
            mode = "lf_inserted"
    backup_sha_ok = h256(backup) == e["backup_root"]["sha256"] == e["original_root_sha256"] == t["baseline_sha256"]
    fm_ok = root.startswith(b"---") and b"\n---" in root[:2000]
    q3[p] = {"hook_count": cnt, "link_ok": link_ok, "minus_hook_mode": mode,
             "backup_sha_ok": backup_sha_ok, "frontmatter_ok": fm_ok}
ok("Q3.hook_count_1_all", all(v["hook_count"] == 1 for v in q3.values()),
   json.dumps({k: v["hook_count"] for k, v in q3.items()}))
ok("Q3.link_valid_all", all(v["link_ok"] for v in q3.values()), "")
ok("Q3.minus_hook_reproduces_backup", all(v["minus_hook_mode"] in ("direct", "lf_inserted") for v in q3.values()),
   json.dumps({k: v["minus_hook_mode"] for k, v in q3.items()}))
ok("Q3.backup_sha_chain_ok", all(v["backup_sha_ok"] for v in q3.values()), "")
ok("Q3.frontmatter_intact", all(v["frontmatter_ok"] for v in q3.values()), "")
R["targets"] = q3

# ---------- Q4: fresh root hashes vs producer after-manifest; inventory; default profile ----------
drift = {}
for t, e in zip(targets, roll["entries"]):
    p = t["profile"]
    fresh = h256(rb(t["root_path"]))
    drift[p] = {"fresh": fresh, "manifest_after": e["root_sha256_after"],
                "match": fresh == e["root_sha256_after"]}
ok("Q4.fresh_matches_after_manifest", all(v["match"] for v in drift.values()),
   json.dumps({k: v["match"] for k, v in drift.items()}))
R["root_drift"] = drift
inv = {}
for t in targets:
    root_dir = t["skill_root"]
    files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            files.append(os.path.relpath(fp, root_dir))
    inv[t["profile"]] = sorted(files)
R["skill_root_inventory"] = inv
refcount = {p: sum(1 for f in fl if f.startswith("references\\")) for p, fl in inv.items()}
ok("Q4.company_refs_4_others_1",
   refcount.get("company") == 4 and all(v == 1 for k, v in refcount.items() if k != "company"),
   json.dumps(refcount))
# default profile untouched (out of scope)
def_co = os.path.join(DEFAULT_HERMES, "skills", "company-os")
def_ref = os.path.join(def_co, "references", "dots-operating-method.md")
def_skill = os.path.join(def_co, "SKILL.md")
def_hook_present = os.path.isfile(def_skill) and (hook in rb(def_skill))
ok("Q4.default_profile_untouched", (not os.path.isfile(def_ref)) and (not def_hook_present),
   "default_ref_exists=%s default_hook_present=%s" % (os.path.isfile(def_ref), def_hook_present))

# ---------- author readback receipt ----------
ar_path = os.path.join(PACKET, "AUTHOR-READBACK.json")
if os.path.isfile(ar_path):
    ar_sha = h256(rb(ar_path))
    R["author_readback"] = {"path": ar_path, "sha256": ar_sha,
                            "matches_operator_note": ar_sha == AUTHOR_READBACK_SHA}
else:
    R["author_readback"] = {"path": ar_path, "exists": False}

# ---------- operator-flagged report discrepancies (programmatic capture) ----------
rep = {}
rollout_lines = rb(os.path.join(PACKET, "ROLLOUT.md")).decode("utf-8").splitlines()
sa_path = os.path.join(PACKET, "SOURCE-AUDIT.md")
sa_lines = rb(sa_path).decode("utf-8").splitlines() if os.path.isfile(sa_path) else []
rep["ROLLOUT_line3"] = rollout_lines[2] if len(rollout_lines) > 2 else None
rep["ROLLOUT_line24"] = rollout_lines[23] if len(rollout_lines) > 23 else None
rep["ROLLOUT_line119"] = rollout_lines[118] if len(rollout_lines) > 118 else None
rep["ROLLOUT_line3_has_wrong_parent_t_2c44dd2f"] = "t_2c44dd2f" in (rep["ROLLOUT_line3"] or "")
rep["ROLLOUT_line24_claims_11_members"] = "11 frozen BRAIN-PACKET members" in (rep["ROLLOUT_line24"] or "")
rep["brain_manifest_members_actual"] = len(members)
rep["ROLLOUT_line119_conflates"] = "no spend authorized or incurred" in (rep["ROLLOUT_line119"] or "")
for ln in (47, 48, 57, 65):
    rep["SOURCE_AUDIT_line%d" % ln] = sa_lines[ln-1] if len(sa_lines) >= ln else None
cand_text = cand.decode("utf-8", "replace")
rep["candidate_contains_codex_not_dots"] = "codex-not-dots" in cand_text
rep["candidate_contains_R0_R6_sections"] = ("R0" in cand_text) or ("R6" in cand_text)
rep["source_audit_contains_codex_not_dots"] = any("codex-not-dots" in l for l in sa_lines)
rep["candidate_line34"] = R["candidate_lines"][33] if len(R["candidate_lines"]) >= 34 else None
# rollback section: reference delete step lacks freshness check
rollout_text = "\n".join(rollout_lines)
rb_sec = rollout_text[rollout_text.find("## Rollback"):] if "## Rollback" in rollout_text else ""
rep["rollback_ref_delete_has_hash_check"] = ("reference" in rb_sec and CAND_SHA256[:12] in rb_sec)
R["report_checks"] = rep

# ---------- packet dir listing ----------
R["packet_dir"] = sorted(os.listdir(PACKET))

all_pass = all(c["pass"] for c in R["checks"].values())
R["overall_all_checks_pass"] = all_pass

out_path = os.path.join(PACKET, "QA-CHECK-t_a3c78661.json")
R.pop("candidate_lines", None)  # keep output lean; line count retained
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(R, f, indent=2, ensure_ascii=False)
print("WROTE", out_path)
for k, v in R["checks"].items():
    print(("PASS " if v["pass"] else "FAIL ") + k + (" | " + v["detail"] if v["detail"] else ""))
print("OVERALL:", "PASS" if all_pass else "FAIL")
sys.exit(0 if all_pass else 1)
