"""Additive exact-head source provisioning and identity receipts."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "evidence"
OUT.mkdir(exist_ok=True)
SOURCE = "C:/Users/max/AppData/Local/hermes/hermes-agent"
AUTHOR = SOURCE + "/.worktrees/tg-qwen-profile-routing-bounded-20261003"
HEAD = "c605e5b618cf20a2d94422bd2c995b864bd986c8"
BASE = "9aae3c23e2c4f39f77d8d54b5e72ba4b90f4ba8f"
PUBLISHED = Path("C:/Users/max/Desktop/all/ventures/docs/fleet-ops/telegram-optimization-20261003/TGR-01B-fix.patch")
ALLOWED = {"gateway/run_config_loaders.py", "gateway/run_turn.py", "gateway/slash_commands_model.py", "tests/gateway/test_profile_channel_override_routing.py"}
UNTOUCHED = ["gateway/run.py", "gateway/run_adapters.py", "gateway/run_profile_reconcile.py", "gateway/run_agent_cache.py", "gateway/session.py", "gateway/session_identity.py", "gateway/config.py", "tests/gateway/test_channel_overrides.py", "scripts/run_tests.sh"]
assert re.fullmatch(r"[0-9a-f]{40}", HEAD)
assert re.fullmatch(r"[0-9a-f]{40}", BASE)
commands = []
def cmd(args, cwd=None):
    p = subprocess.run(args, cwd=cwd, capture_output=True, stdin=subprocess.DEVNULL, timeout=120)
    commands.append({"argv": args, "cwd": str(cwd) if cwd else None, "exit_code": p.returncode, "stdout": p.stdout.decode("utf-8", "replace"), "stderr": p.stderr.decode("utf-8", "replace")})
    if p.returncode:
        (OUT / "provision-failure.json").write_text(json.dumps(commands, indent=2), encoding="utf-8")
        raise RuntimeError(f"command failed: {args}, exit {p.returncode}")
    return p.stdout

assert cmd(["git", "-C", AUTHOR, "rev-parse", "HEAD"]).decode().strip() == HEAD
assert not cmd(["git", "-C", AUTHOR, "status", "--porcelain"]).strip()
assert cmd(["git", "-C", AUTHOR, "show", "-s", "--format=%P", HEAD]).decode().strip() == BASE
base_tree = ROOT / "base-r2301"
head_tree = ROOT / "head-r2301"
for p in [base_tree, head_tree]:
    if p.exists():
        raise RuntimeError(f"target already exists: {p}")
cmd(["git", "clone", "--shared", SOURCE, str(base_tree)])
assert cmd(["git", "-C", str(base_tree), "rev-parse", "HEAD"]).decode().strip() == BASE
cmd(["git", "clone", "--shared", "--single-branch", "--branch", "wt/t_ced9d357", SOURCE, str(head_tree)])
assert cmd(["git", "-C", str(head_tree), "rev-parse", "HEAD"]).decode().strip() == HEAD
for p in [base_tree, head_tree]:
    assert not cmd(["git", "-C", str(p), "status", "--porcelain"]).strip()
raw_scope = cmd(["git", "-C", str(head_tree), "diff", "--name-status", BASE, HEAD])
paths = {line.split("\t")[-1] for line in raw_scope.decode().splitlines()}
assert paths == ALLOWED, paths
assert not cmd(["git", "-C", str(head_tree), "diff", BASE, HEAD, "--", *UNTOUCHED]).strip()
patch = cmd(["git", "-C", str(head_tree), "format-patch", "-1", "--stdout", HEAD])
assert patch == PUBLISHED.read_bytes(), "submitted patch differs byte-for-byte"
(OUT / "qa-exact-head.patch").write_bytes(patch)
source_diff = cmd(["git", "-C", str(head_tree), "diff", BASE, HEAD, "--", "gateway/run_config_loaders.py", "gateway/run_turn.py", "gateway/slash_commands_model.py"])
(OUT / "production-diff.txt").write_bytes(source_diff)
result = {"task_id": "t_307fc218", "run_id": 2301, "recorded_at": datetime.now(timezone.utc).isoformat(), "head": HEAD, "base": BASE, "direct_parent_matches_base": True, "base_tree": str(base_tree), "head_tree": str(head_tree), "changed_paths": sorted(paths), "untouched_paths_empty_diff": UNTOUCHED, "patch_matches_submitted_bytes": True, "patch_bytes": len(patch), "patch_sha256": hashlib.sha256(patch).hexdigest(), "diff_sha256": hashlib.sha256(source_diff).hexdigest(), "missing_path": "tests/gateway/test_profile_route_ownership.py", "missing_base": not (base_tree / "tests/gateway/test_profile_route_ownership.py").is_file(), "missing_head": not (head_tree / "tests/gateway/test_profile_route_ownership.py").is_file(), "commands": commands}
(OUT / "identity.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in result.items() if k != "commands"}, indent=2))
