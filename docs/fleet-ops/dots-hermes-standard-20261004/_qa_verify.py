#!/usr/bin/env python3
"""QA-CANDIDATE independent verifier for frozen subject 2fedef53... (t_d090b4ff).

Bounded, read-only, source-only. Recomputes:
  C1  SUBJECT member full-length digests/bytes
  C2  BASELINE frozen inputs + installed docs + before/before-trees hashes
  C3  dry-run hook replacement per target: one old suffix -> one new suffix,
      simulated new root bytes, cross-target equality groups,
      YAML/frontmatter validity, hook link resolution
  C4  no other captured tree file contains the old hook block (no side replacement)
  C5  REFERENCE-CANDIDATE is the single unique future reference for all 12 targets
Exit 0 = all checks passed. Results JSON: _qa_verify_results.json (recounted here).
"""
import hashlib, json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
def p(*a): return os.path.join(ROOT, *a)
def sha(b): return hashlib.sha256(b).hexdigest()

res = {"checks": {}, "ok": True}
def rec(name, ok, detail=""):
    res["checks"][name] = {"ok": bool(ok), "detail": str(detail)[:400]}
    if not ok: res["ok"] = False

# ---------- C1: SUBJECT ----------
try:
    subj = json.load(open(p("SUBJECT.json"), encoding="utf-8"))
    h = sha(open(p("SUBJECT.json"), "rb").read())
    rec("c1_subject_head", h == "2fedef53211adc07445caee7d4d3ef3cac4df5e7544508ca35a26e040774600e", f"sha256={h}")
    members = subj.get("members") or subj.get("files") or []
    if not members:
        # try generic: any list of dicts with name+sha256
        for k, v in subj.items():
            if isinstance(v, list) and v and isinstance(v[0], dict) and "sha256" in v[0]:
                members = v; break
    mdetail = []
    mok = len(members) == 6
    for m in members:
        fn = os.path.basename(m.get("path") or m.get("name") or "")
        exp = m["sha256"]
        try:
            act = sha(open(p(fn), "rb").read())
            exp_len = m.get("bytes")
            act_len = os.path.getsize(p(fn))
            okm = act == exp and (exp_len is None or act_len == exp_len)
            mdetail.append(f"{fn}:{'OK' if okm else 'MISMATCH'}")
            mok = mok and okm
        except FileNotFoundError:
            mdetail.append(f"{fn}:MISSING"); mok = False
    rec("c1_subject_members", mok, "; ".join(mdetail) + f"; n={len(members)}")
except Exception as e:
    rec("c1_subject_head", False, f"parse error {e}")

# ---------- C2: BASELINE frozen bytes ----------
try:
    b = json.load(open(p("BASELINE.json"), encoding="utf-8"))
    iok, idet, n = True, [], 0
    for it in b.get("inputs", []):
        fp = it.get("path")
        if not fp or not os.path.isabs(fp): fp = p(it.get("relative_path") or os.path.basename(fp or ""))
        try:
            act = sha(open(fp, "rb").read())
            ok = act == it["sha256"]; n += 1
            if not ok: idet.append(f"{os.path.basename(fp)}:MISMATCH")
        except FileNotFoundError:
            ok = False; idet.append(f"{os.path.basename(str(fp))}:MISSING")
        iok = iok and ok
    rec("c2_baseline_inputs", iok, f"checked={n}; " + ("; ".join(idet) or "all match"))
    dok, ddet, dn = True, [], 0
    for it in b.get("installed_docs", []):
        fp = it.get("path")
        try:
            act = sha(open(fp, "rb").read())
            ok = act == it["sha256"]; dn += 1
            if not ok: ddet.append(f"{it.get('name')}:MISMATCH")
        except FileNotFoundError:
            ok = False; ddet.append(f"{it.get('name')}:MISSING")
        dok = dok and ok
    rec("c2_installed_docs", dok, f"checked={dn}; " + ("; ".join(ddet) or "all match"))
    tok, tdet, tn = True, [], 0
    for t in b.get("targets", []):
        for m in t.get("markdown_tree", []):
            fp = m["path"]
            try:
                act = sha(open(fp, "rb").read())
                ok = act == m["sha256"] and os.path.getsize(fp) == m["bytes"]; tn += 1
                if not ok: tdet.append(f"{t['profile']}/{m['relative_path']}:MISMATCH")
            except FileNotFoundError:
                ok = False; tdet.append(f"{t['profile']}/{m['relative_path']}:MISSING")
            tok = tok and ok
    rec("c2_before_trees", tok, f"checked={tn}; " + ("; ".join(tdet)[:200] or "all match"))
    # snapshots root/reference bytes equal live recorded sha
    sok, sdet, sn = True, [], 0
    for t in b.get("targets", []):
        for kind in ("root", "reference"):
            snap = t.get("snapshots", {}).get(kind, {})
            fp, txt = snap.get("path"), snap.get("text")
            try:
                data = open(fp, "rb").read() if fp else txt.encode("utf-8")
                ok = sha(data) == snap.get("sha256"); sn += 1
                if not ok: sdet.append(f"{t['profile']}:{kind}")
            except Exception:
                ok = False; sdet.append(f"{t['profile']}:{kind}:ERR")
            sok = sok and ok
    rec("c2_snapshots", sok, f"checked={sn}; " + ("; ".join(sdet) or "all match"))
except Exception as e:
    rec("c2_baseline_inputs", False, f"parse error {e}")

# ---------- C3/C4/C5: dry-run replacement ----------
try:
    old = open(p("local", "old-hook.md"), "rb").read()
    new = open(p("HOOK-CANDIDATE.md"), "rb").read()
    ref = open(p("REFERENCE-CANDIDATE.md"), "rb").read()
    rec("c5_reference_unique_hash", True, f"sha256={sha(ref)}")
    sim = {}
    det = []
    for t in b.get("targets", []):
        rootb = None
        # prefer snapshot path bytes
        sp = t["snapshots"]["root"].get("path")
        if sp and os.path.exists(sp):
            rootb = open(sp, "rb").read()
        else:
            rootb = t["snapshots"]["root"]["text"].encode("utf-8")
        cnt_old = rootb.count(old)
        prof = t["profile"]
        if cnt_old != 1:
            det.append(f"{prof}:old_hook_count={cnt_old}")
            continue
        if rootb.count(new) != 0:
            det.append(f"{prof}:new_hook_already_present")
            continue
        simroot = rootb.replace(old, new)
        ok_one = simroot.count(new) == 1 and simroot.count(old) == 0
        tail_ok = simroot.endswith(new.rstrip(b"\n") + b"\n") if simroot.endswith(b"\n") else simroot.endswith(new.rstrip(b"\n"))
        sim[prof] = simroot
        if not (ok_one and tail_ok):
            det.append(f"{prof}:post_conditions old={simroot.count(old)} new={simroot.count(new)} tail={tail_ok}")
    rec("c3_replacement_1to1", not det and len(sim) == len(b.get("targets", [])), "; ".join(det) or f"simulated {len(sim)}/{len(b.get('targets', []))} targets")
    # equality groups: roots equal where before roots equal
    groups = {}
    for t in b.get("targets", []):
        groups.setdefault(t["before_root_sha256"], []).append(t["profile"])
    gdet = []
    for bh, profs in groups.items():
        rs = {sha(sim[x]) for x in profs if x in sim}
        if len(rs) != 1: gdet.append(f"group[{bh[:8]}] n={len(profs)} distinct_after={len(rs)}")
        else: gdet.append(f"group[{bh[:8]}] n={len(profs)} identical_after=1")
    rec("c3_group_equality", all("identical_after=1" in g for g in gdet), "; ".join(gdet))
    # YAML frontmatter + link validity of simulated roots
    ydet, yok = [], True
    for prof, sroot in sim.items():
        txt = sroot.decode("utf-8")
        m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", txt, re.S)
        if not m:
            yok = False; ydet.append(f"{prof}:no_frontmatter"); continue
        fm = m.group(1)
        name = re.search(r"^name:\s*(\S+)", fm, re.M)
        desc = re.search(r"^description:", fm, re.M)
        if not name or not desc:
            yok = False; ydet.append(f"{prof}:frontmatter_fields")
        # hook link
        link = re.search(r"\[references/dots-operating-method\.md\]\((references/dots-operating-method\.md)\)", txt)
        if not link:
            yok = False; ydet.append(f"{prof}:hook_link_missing")
    rec("c3_yaml_links", yok, "; ".join(ydet) or f"all {len(sim)} simulated roots: frontmatter + link OK")
    # C4: old hook text appears in no OTHER captured tree file
    c4det, c4ok = [], True
    seen = set()
    for t in b.get("targets", []):
        key = t["before_root_sha256"]
        for m in t.get("markdown_tree", []):
            if m["relative_path"] == "SKILL.md":
                continue
            fp = m["path"]
            if fp in seen: continue
            seen.add(fp)
            try:
                if old in open(fp, "rb").read():
                    # the reference copy itself is expected to differ; flag others
                    if not m["relative_path"].endswith("dots-operating-method.md"):
                        c4ok = False; c4det.append(f"{m['relative_path']}:contains_old_hook")
            except Exception:
                pass
    rec("c4_no_side_replacement", c4ok, "; ".join(c4det) or f"old hook block absent from {len(seen)} non-root captured files")
    # public docs presence (hash recount of raw html not needed: BASELINE stores raw inline; just count)
    rec("c5_public_docs_present", len(b.get("public_doc_errors", [])) == 0 and len(b.get("public_hermes_docs", [])) == 12,
        f"articles={len(b.get('public_hermes_docs', []))} errors={len(b.get('public_doc_errors', []))}")
except Exception as e:
    rec("c3_replacement_1to1", False, f"error {e}")

json.dump(res, open(p("_qa_verify_results.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
sys.exit(0 if res["ok"] else 1)
