"""Run only the frozen contract's suites, preserving real exit codes/logs."""
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import re
import subprocess

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "evidence"
PYTHON = "C:/Users/max/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe"
FILES = ["test_channel_overrides.py", "test_empty_model_recovery.py", "test_empty_model_fallback.py", "test_model_command_profile_config.py", "test_model_switch_persistence.py", "test_agent_cache.py", "test_agent_cache_release_profile_scope.py", "test_busy_session_profile_scope.py", "test_handoff_secondary_profile_adapter.py", "test_model_command_custom_providers.py"]
TMP = ROOT / "test-tmp"
TMP.mkdir(exist_ok=True)
env = dict(os.environ, HERMES_PYTHON=PYTHON, TMP=str(TMP), TEMP=str(TMP), PYTHONUTF8="1")
results = []
for name, tree, files in [("qa-focused-head", "head-r2301", ["test_profile_channel_override_routing.py"]), ("qa-regressions-base", "base-r2301", FILES), ("qa-regressions-head", "head-r2301", FILES)]:
    path = ROOT / tree
    name += "-native-bash"
    argv = ["C:/Users/max/AppData/Local/hermes/tools/git-2.53.0+3-win32-x64/usr/bin/bash.exe", "scripts/run_tests.sh", *["tests/gateway/" + f for f in files]]
    started = datetime.now(timezone.utc).isoformat()
    with (OUT / (name + ".log")).open("wb") as log:
        proc = subprocess.run(argv, cwd=path, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, timeout=450)
    text = (OUT / (name + ".log")).read_text(encoding="utf-8", errors="replace")
    summaries = re.findall(r"=== Summary: (\d+) files, (\d+) tests passed, (\d+) failed.*?===", text)
    rows = {}
    for line in text.splitlines():
        match = re.search(r"\]\s*([✓✗])\s+(tests\\gateway\\\S+\.py)\s+\((.*?)\)", line)
        if match:
            details = match.group(3)
            passed = re.search(r"(\d+)✓", details)
            failed = re.search(r"(\d+)✗", details)
            collected = re.search(r"(\d+) tests", details)
            rows[match.group(2).replace("\\", "/")] = {"marker": match.group(1), "passed": int(passed.group(1)) if passed else 0, "failed": int(failed.group(1)) if failed else 0, "collected_without_summary": int(collected.group(1)) if collected else None, "raw": line}
    record = {"name": name, "tree": str(path), "argv": argv, "HERMES_PYTHON": PYTHON, "temp_root": str(TMP), "started_at": started, "finished_at": datetime.now(timezone.utc).isoformat(), "exit_code": proc.returncode, "log": str(OUT / (name + ".log")), "summary": [int(x) for x in summaries[-1]] if summaries else None, "per_file": rows, "home_guard_occurrences": text.count("TEST BUG: file I/O against the REAL hermes home"), "stashkey_occurrences": len(re.findall(r"KeyError: <_pytest\.stash\.StashKey", text))}
    results.append(record)
    (OUT / "suite-results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in record.items() if k not in ["argv", "per_file"]}, ensure_ascii=False), flush=True)
