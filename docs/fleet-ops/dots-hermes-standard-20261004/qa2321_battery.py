# QA-2321 independent verification battery (reviewer: qa, session glm-5.3/zai)
# Read-only vs live targets + freeze dir; no writes outside scratch output JSON.
import hashlib, json, os, re, sys
from pathlib import Path

ROOT = Path(r"C:\Users\max\Desktop\all\ventures\docs\fleet-ops\dots-hermes-standard-20261004")
OUT = Path(r"C:\Users\max\AppData\Local\hermes\profiles\qa\cache\scratch\t_63f62c17-qa2321")
OUT.mkdir(parents=True, exist_ok=True)

REF_SHA = "80933ccf80e99e6b9d62b6f15c5c4f8cf69e9ee79ab1b2e9296173b99cdf4def"
HOOK_SHA = "40b6f5e5edad6b8349c3143e032e29d2d02fa5cd1362c9ba9c10dbdbc2bdc88d"
BASELINE_SHA = "5490e880fcd4d596029d127e1a1bf4011df7003b53e9faca3fef9680fa61f817"
HEAD = "2fedef53211adc07445caee7d4d3ef3cac4df5e7544508ca35a26e040774600e"
QA_FIXED_SHA = "ed4d00c92f5b5574f22980f7b37db2c5d45008113e5e7efc192b6412f7ca75d3"
CONSUMER_SHA = "30a1e12ed2eb612298f1c6ade32981934811d7fa934e14eaf928af7d4b14868d"
APPLY_JSON_SHA = "e7fe29209540279aa2edd393ed94403a28a3bbb4b2f6cffdc554431839763495"

checks = {}
details = {}
fails = []

def chk(name, ok, detail=""):
    checks[name] = bool(ok)
    if not ok:
        fails.append(name)
        details[name] = str(detail)[:300]

def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()

def fm_block(text):
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])
    return None

# ---------- A. freeze-chain integrity ----------
base = json.loads((ROOT / "BASELINE.json").read_text(encoding="utf-8"))
chk("A:baseline_sha256", sha(ROOT / "BASELINE.json") == BASELINE_SHA, sha(ROOT / "BASELINE.json"))
subj = json.loads((ROOT / "SUBJECT.json").read_text(encoding="utf-8"))
chk("A:subject_head", sha(ROOT / "SUBJECT.json") == HEAD, sha(ROOT / "SUBJECT.json"))
for m in subj["members"]:
    p = ROOT / m["name"]
    ok = p.exists() and p.stat().st_size == m["bytes"] and sha(p) == m["sha256"]
    chk(f"A:member:{m['name']}", ok, getattr(p, "exists", lambda: False) and p.stat().st_size if p.exists() else "missing")
chk("A:qa_candidate_fixed_sha256", sha(ROOT / "QA-CANDIDATE-FIXED.json") == QA_FIXED_SHA, sha(ROOT / "QA-CANDIDATE-FIXED.json"))
chk("A:consumer_receipt_sha256", sha(ROOT / "CONSUMER-ACCEPTANCE-RECEIPT.json") == CONSUMER_SHA, sha(ROOT / "CONSUMER-ACCEPTANCE-RECEIPT.json"))
chk("A:apply_json_sha256", sha(ROOT / "APPLY.json") == APPLY_JSON_SHA, sha(ROOT / "APPLY.json"))

go = (ROOT / "COMPANY-GO.md").read_text(encoding="utf-8")
chk("A:company_go_binds_head", HEAD in go and "decision: company=go" in go)

ref_bytes = (ROOT / "REFERENCE-CANDIDATE.md").read_bytes()
hook_bytes = (ROOT / "HOOK-CANDIDATE.md").read_bytes()
chk("A:ref_bytes_len", len(ref_bytes) == 7821, len(ref_bytes))
chk("A:hook_bytes_len", len(hook_bytes) == 697, len(hook_bytes))

old_hook_entry = [i for i in base["inputs"] if i["kind"] == "old-hook"][0]
old_hook_path = ROOT / "local" / "old-hook.md"
chk("A:old_hook_frozen", old_hook_path.exists() and sha(old_hook_path) == old_hook_entry["sha256"] and old_hook_path.stat().st_size == 458)
old_hook_bytes = old_hook_path.read_bytes()

# frozen inputs present & hash-matched (26)
bad_in = [i["name"] if "name" in i else i.get("kind", "?") for i in base["inputs"] if not (Path(i["path"]).exists() and sha(Path(i["path"])) == i["sha256"])]
chk("A:inputs_26_intact", len(base["inputs"]) == 26 and not bad_in, bad_in)

# before/ + before-trees/ snapshot integrity (24 + per-tree entries)
snap_bad, tree_frozen_bad, tree_count = [], [], 0
for t in base["targets"]:
    for kind in ("root", "reference"):
        s = t["snapshots"][kind]
        p = Path(s["path"])
        if not (p.exists() and p.stat().st_size == s["bytes"] and sha(p) == s["sha256"]):
            snap_bad.append(f'{t["profile"]}:{kind}')
    for e in t["markdown_tree"]:
        tree_count += 1
        p = Path(e["path"])
        if not (p.exists() and p.stat().st_size == e["bytes"] and sha(p) == e["sha256"]):
            tree_frozen_bad.append(f'{t["profile"]}:{e["relative_path"]}')
chk("A:before_snapshots_24_intact", not snap_bad, snap_bad)
# BASELINE markdown_tree entries: company=5, other 11 profiles=2 each -> 27 frozen tree files
chk("A:before_trees_count_27", tree_count == 27, tree_count)
chk("A:before_trees_intact", not tree_frozen_bad, tree_frozen_bad)

# ---------- B. live 12 targets ----------
targets = base["targets"]
profiles = [t["profile"] for t in targets]
chk("B:targets_12", len(targets) == 12, len(targets))
chk("B:unique_profiles_12", len(set(profiles)) == 12, profiles)
paths24 = [p for t in targets for p in (t["root_path"], t["reference_path"])]
chk("B:unique_paths_24", len(set(paths24)) == 24, len(set(paths24)))
perm = {pw["profile"]: pw["paths"] for pw in base["permitted_live_writes_for_later_review"]}
chk("B:allowlist_matches_targets", len(perm) == 12 and all(perm[t["profile"]] == [t["root_path"], t["reference_path"]] for t in targets))

after_roots = {}
for t in targets:
    prof = t["profile"]
    lr, lf = Path(t["root_path"]), Path(t["reference_path"])
    chk(f"B:{prof}:root_exists", lr.exists())
    chk(f"B:{prof}:ref_exists", lf.exists())
    if not (lr.exists() and lf.exists()):
        continue
    rb = lr.read_bytes()
    chk(f"B:{prof}:reference_byte_equal_payload", lf.read_bytes() == ref_bytes)
    chk(f"B:{prof}:one_new_hook_suffix", rb.endswith(hook_bytes) and rb.count(hook_bytes) == 1, f"ends={rb.endswith(hook_bytes)} cnt={rb.count(hook_bytes)}")
    chk(f"B:{prof}:no_old_hook", rb.count(old_hook_bytes) == 0, rb.count(old_hook_bytes))
    bs = Path(t["snapshots"]["root"]["path"])
    bb = bs.read_bytes()
    chk(f"B:{prof}:before_old_hook_suffix_once", bb.endswith(old_hook_bytes) and bb.count(old_hook_bytes) == 1, f"ends={bb.endswith(old_hook_bytes)} cnt={bb.count(old_hook_bytes)}")
    chk(f"B:{prof}:remainder_byte_equal", rb[:-len(hook_bytes)] == bb[:-len(old_hook_bytes)])
    exp_after = hashlib.sha256(bb[:-len(old_hook_bytes)] + hook_bytes).hexdigest()
    live_root_sha = sha(lr)
    after_roots[prof] = live_root_sha
    chk(f"B:{prof}:after_root_equals_recomputed", live_root_sha == exp_after, f"{live_root_sha} vs {exp_after}")

    # captured markdown tree: name set + byte hashes (intended targets exempted by semantics)
    skill_dir = lr.parent
    captured = {e["relative_path"]: e for e in t["markdown_tree"]}
    actual = {}
    for p in skill_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() == ".md":
            actual[str(p.relative_to(skill_dir)).replace("\\", "/")] = p
    chk(f"B:{prof}:tree_name_set_unchanged", set(actual) == set(captured), f"+{sorted(set(actual)-set(captured))} -{sorted(set(captured)-set(actual))}")
    for rel, e in captured.items():
        if rel not in actual:
            chk(f"B:{prof}:tree:{rel}", False, "missing")
            continue
        got = sha(actual[rel])
        if rel == "references/dots-operating-method.md":
            chk(f"B:{prof}:tree:{rel}=candidate", got == REF_SHA, got)
        elif rel == "SKILL.md":
            chk(f"B:{prof}:tree:SKILL=after_root", got == exp_after, got)
        else:
            chk(f"B:{prof}:tree:{rel}_unchanged", got == e["sha256"], got)

    txt = rb.decode("utf-8")
    fm = fm_block(txt)
    fm_ok = False
    if fm:
        try:
            import yaml
            y = yaml.safe_load(fm) or {}
            fm_ok = (y.get("name") == "company-os") and bool(str(y.get("description", "")).strip())
        except Exception as ex:
            fm_ok = None
            details[f"B:{prof}:frontmatter_valid"] = f"yaml parse error: {ex}"
    chk(f"B:{prof}:frontmatter_valid", fm_ok is True, details.get(f"B:{prof}:frontmatter_valid", "no/invalid frontmatter"))
    chk(f"B:{prof}:entrypoint_link_resolves", "references/dots-operating-method.md" in txt and lf.exists())
    residue = [str(p) for p in skill_dir.rglob("*.applytmp*")]
    chk(f"B:{prof}:no_applytmp_residue", residue == [], residue)

# distinct after-root grouping (3 expected bases)
distinct_after = {}
for prof, s in after_roots.items():
    distinct_after.setdefault(s, []).append(prof)
chk("B:three_distinct_after_roots", len(distinct_after) == 3, {k[:12]: v for k, v in distinct_after.items()})
chk("B:company_group_solo", len(distinct_after.get(after_roots.get("company", ""), [])) == 1)
chk("B:research_group_solo", len(distinct_after.get(after_roots.get("research", ""), [])) == 1)

# ---------- C. run-2320 receipt cross-check ----------
run2320 = json.loads((ROOT / "APPLY-run2320-20261004T012335Z.json").read_text(encoding="utf-8"))
pt = run2320["per_target"]
chk("C:run2320_12_applied", len(pt) == 12 and all(x["status"] == "APPLIED" for x in pt), [x["status"] for x in pt])
rmap = {x["profile"]: x for x in pt}
for t in targets:
    prof = t["profile"]
    x = rmap.get(prof, {})
    chk(f"C:{prof}:receipt_before_matches_baseline", x.get("before_root_sha256") == t["before_root_sha256"] and x.get("before_reference_sha256") == t["before_reference_sha256"])
    chk(f"C:{prof}:receipt_after_ref", x.get("after_reference_sha256") == REF_SHA, x.get("after_reference_sha256"))
    chk(f"C:{prof}:receipt_after_root_live", x.get("after_root_sha256") == after_roots.get(prof), x.get("after_root_sha256"))
chk("C:run2320_errors_empty", run2320.get("errors") == [], run2320.get("errors"))
chk("C:run2320_summary", run2320.get("summary", {}).get("applied") == 12 and run2320["summary"].get("reference_sha256") == REF_SHA and run2320["summary"].get("hook_sha256") == HOOK_SHA)

# ---------- D. backups ----------
bdir = ROOT / "apply-backups"
bprof = sorted([d.name for d in bdir.iterdir() if d.is_dir()]) if bdir.is_dir() else []
chk("D:backup_12_dirs", bprof == sorted(profiles), bprof)
bextra = [d.name for d in bdir.iterdir() if not d.is_dir()] if bdir.is_dir() else ["no-dir"]
for t in targets:
    prof = t["profile"]
    d = bdir / prof
    files = sorted(p.name for p in d.iterdir()) if d.is_dir() else []
    chk(f"D:{prof}:backup_files_exact", files == ["SKILL.md", "dots-operating-method.md"], files)
    if files == ["SKILL.md", "dots-operating-method.md"]:
        chk(f"D:{prof}:backup_root=before", sha(d / "SKILL.md") == t["before_root_sha256"], sha(d / "SKILL.md"))
        chk(f"D:{prof}:backup_ref=before", sha(d / "dots-operating-method.md") == t["before_reference_sha256"], sha(d / "dots-operating-method.md"))
chk("D:backup_no_extra_files", bextra == [], bextra)

# ---------- E. APPLY-VERIFY / APPLY-LOADER internal parse ----------
av = json.loads((ROOT / "APPLY-VERIFY.json").read_text(encoding="utf-8"))["checks"]
expected_keys = {"unique_12_profiles", "unique_24_target_paths"} | {f'{p}:{c}' for p in profiles for c in ("reference_byte_equal_payload", "one_new_hook", "no_old_hook", "remainder_byte_equal_before_minus_old_hook", "captured_markdown_tree_unchanged", "entrypoint_link_resolves", "frontmatter_valid", "backup_covers_both_paths")}
chk("E:applyverify_98_keys_exact", set(av) == expected_keys and len(av) == 98, f"n={len(av)} diff={sorted(set(av) ^ expected_keys)[:8]}")
chk("E:applyverify_all_true", all(av.values()), [k for k, v in av.items() if not v])

al = json.loads((ROOT / "APPLY-LOADER.json").read_text(encoding="utf-8"))["loader_probe"]
chk("E:applyloader_12_profiles", set(al) == set(profiles), sorted(al))
chk("E:applyloader_all_loaded", all(v.get("loaded") is True for v in al.values()), {k: v.get("loaded") for k, v in al.items() if v.get("loaded") is not True})

# ---------- F. preserved old standard ----------
old_dir = Path(r"C:\Users\max\Desktop\all\ventures\docs\fleet-ops\dots-20261003")
chk("F:old_dots_dir_preserved", old_dir.is_dir())
if old_dir.is_dir():
    chk("F:old_load_hook_intact", (old_dir / "LOAD-HOOK.md").exists() and sha(old_dir / "LOAD-HOOK.md") == old_hook_entry["sha256"])
    bad_src = []
    for i in base["inputs"]:
        if i["kind"] == "verified-dots-source":
            sp = Path(i["source_path"])
            if not (sp.exists() and sha(sp) == i["sha256"]):
                bad_src.append(sp.name)
    chk("F:old_dots_sources_intact", len([i for i in base["inputs"] if i["kind"] == "verified-dots-source"]) == 8 and not bad_src, bad_src)

# ---------- G. APPLY.md semantics (no overclaims) ----------
amd = (ROOT / "APPLY.md").read_text(encoding="utf-8")
chk("G:applymd_limits_static_install", "Статическая установка файлов" in amd)
chk("G:applymd_no_obedience_claim", "не подтверждает будущее послушание" in amd)
chk("G:applymd_finance_null", "null" in amd and "не утверждение «0 ₽»" in amd)
chk("G:applymd_typed_result", "applied 12/12" in amd)
forbid = [w for w in ("гарантирует остановку", "полный live stop подтвержд", "экономический эффект подтвержд") if w in amd]
chk("G:applymd_no_forbidden_claims", forbid == [], forbid)

# ---------- result ----------
res = {
    "reviewer": "qa (run 2321, session independent)",
    "verdict_basis": "independent battery, not a copy of operations checker",
    "total_checks": len(checks),
    "passed": sum(1 for v in checks.values() if v),
    "failed": len(fails),
    "failures": fails,
    "failure_details": details,
    "distinct_after_roots": {k[:16]: v for k, v in distinct_after.items()},
}
(OUT / "QA2321-BATTERY.json").write_text(json.dumps({"checks": checks, "result": res}, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(res, ensure_ascii=False, indent=1))
sys.exit(0 if not fails else 1)
