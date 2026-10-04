"""Execute independent probes on exact head and base using canonical runner."""
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "evidence"
PYTHON = "C:/Users/max/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe"
BASH = "C:/Users/max/AppData/Local/hermes/tools/git-2.53.0+3-win32-x64/usr/bin/bash.exe"
PROBE = ROOT / "test_qa_tgr_routing.py"
TEMP = ROOT / "test-tmp"
env = dict(os.environ, HERMES_PYTHON=PYTHON, PYTHONUTF8="1", TMP=str(TEMP), TEMP=str(TEMP))
results = []
for label in ["head", "base"]:
    tree = ROOT / (label + "-r2301")
    name = "qa-independent-" + label + "-v5"
    junit = OUT / (name + ".xml")
    log_path = OUT / (name + ".log")
    argv = [BASH, "scripts/run_tests.sh", str(PROBE), "--", "-q", "-s", "--tb=short", "--junitxml=" + str(junit)]
    started = datetime.now(timezone.utc).isoformat()
    with log_path.open("wb") as log:
        p = subprocess.run(argv, cwd=tree, env=env, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, timeout=300)
    record = {"label": label, "argv": argv, "cwd": str(tree), "probe": str(PROBE), "started_at": started, "finished_at": datetime.now(timezone.utc).isoformat(), "exit_code": p.returncode, "log": str(log_path), "junit": str(junit), "cases": []}
    if junit.is_file():
        # Trusted local pytest output only; no remote or attacker XML input.
        root = ET.parse(junit).getroot()
        for case in root.iter("testcase"):
            failure, error, skipped = case.find("failure"), case.find("error"), case.find("skipped")
            status = "failed" if failure is not None else "error" if error is not None else "skipped" if skipped is not None else "passed"
            record["cases"].append({"name": case.get("name"), "classname": case.get("classname"), "status": status, "evidence": failure.text if failure is not None else error.text if error is not None else None})
        record["counts"] = {s: sum(c["status"] == s for c in record["cases"]) for s in ["passed", "failed", "error", "skipped"]}
        record["counts"]["total"] = len(record["cases"])
    results.append(record)
    (OUT / "probe-results-v5.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in record.items() if k not in ["argv", "cases"]}, ensure_ascii=False), flush=True)
