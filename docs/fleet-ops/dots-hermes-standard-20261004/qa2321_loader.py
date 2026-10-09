# Independent loader readback: real hermes loader against scoped temp copies of each live root.
import importlib, json, os, shutil, sys, tempfile
from pathlib import Path

REPO = r"C:\Users\max\AppData\Local\hermes\hermes-agent"
sys.path.insert(0, REPO)
os.chdir(REPO)  # project skill dirs resolved from cwd; repo has none in scan roots

ROOT = Path(r"C:\Users\max\Desktop\all\ventures\docs\fleet-ops\dots-hermes-standard-20261004")
base = json.loads((ROOT / "BASELINE.json").read_text(encoding="utf-8"))
profiles = [t["profile"] for t in base["targets"]]

results = {}
for t in base["targets"]:
    prof = t["profile"]
    tmp = Path(tempfile.mkdtemp(prefix=f"qa2321-loader-{prof}-"))
    try:
        skill_dst = tmp / "skills" / "company-os"
        skill_dst.mkdir(parents=True)
        src_skill = Path(t["root_path"]).parent
        shutil.copy2(src_skill / "SKILL.md", skill_dst / "SKILL.md")
        (skill_dst / "references").mkdir()
        for f in src_skill.rglob("*.md"):
            if f.parent.name == "references" and f.name == "dots-operating-method.md":
                shutil.copy2(f, skill_dst / "references" / f.name)
        os.environ["HERMES_HOME"] = str(tmp)
        for mod in ("tools.skills_tool", "tools.skills_tool_plugin", "agent.skill_utils",
                    "hermes_constants", "hermes_cli.config", "gateway.session_context"):
            sys.modules.pop(mod, None)
        import tools.skills_tool as st
        importlib.reload(st)
        st._SKILLS_CACHE.clear()
        raw = st.skills_list()
        data = json.loads(raw)
        names = [s["name"] for s in data.get("skills", [])]
        entry = next((s for s in data.get("skills", []) if s["name"] == "company-os"), None)
        hook_txt = (skill_dst / "SKILL.md").read_text(encoding="utf-8")
        results[prof] = {
            "loaded": entry is not None,
            "names": [n for n in names if "company" in n or "dots" in n],
            "description": (entry or {}).get("description", "")[:80],
            "category": (entry or {}).get("category"),
            "hook_present_in_served_root": "references/dots-operating-method.md" in hook_txt,
        }
    except Exception as ex:
        results[prof] = {"loaded": False, "error": f"{type(ex).__name__}: {ex}"}
    finally:
        os.environ.pop("HERMES_HOME", None)
        shutil.rmtree(tmp, ignore_errors=True)

ok = all(v.get("loaded") and v.get("hook_present_in_served_root") for v in results.values())
out = {"probe": "qa run2321 independent loader readback (tools.skills_tool.skills_list, fresh HERMES_HOME per profile)",
       "n": len(results), "all_loaded": ok, "results": results}
print(json.dumps(out, ensure_ascii=False, indent=1))
Path(r"C:\Users\max\AppData\Local\hermes\profiles\qa\cache\scratch\t_63f62c17-qa2321\QA2321-LOADER.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
sys.exit(0 if ok else 1)
