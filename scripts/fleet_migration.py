from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
import yaml
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

HERMES_HOME = Path("C:/Users/max/AppData/Local/hermes")
VENTURES = Path("C:/Users/max/Desktop/all/ventures")
STATE = VENTURES / ".state" / "fleet-migration"
UNIVERSAL = ["company", "tech", "product", "design", "ux", "qa", "research", "sales", "finance", "operations"]
RR_MAPPING = {
    "rr-support": "company", "rr-backend": "tech", "rr-frontend": "tech", "rr-ops": "operations",
    "rr-critic": "qa", "rr-mkt-lead": "product", "rr-mkt-content": "product", "rr-mkt-seo": "research",
    "rr-mkt-smm": "sales", "rr-pool": "company",
}
TASK_ROUTING = {
    "t_3a11233f": ("qa", "review"), "t_7313c72d": ("tech", "code"),
    "t_c815a6ea": ("operations", "ops"), "t_d4c32f16": ("qa", "review"),
    "t_721c2650": ("research", "research"), "t_2c503ba1": ("qa", "review"),
    "t_810174f5": ("operations", "ops"), "t_cca55a95": ("qa", "review"),
    "t_efc0eb73": ("qa", "review"), "t_62fd4ed9": ("tech", "code"),
    "t_6ba71b0a": ("operations", "ops"), "t_22c1e44b": ("tech", "code"),
    "t_451d3661": ("qa", "review"),
}
ACTIVE = ("triage", "todo", "scheduled", "ready", "running", "review", "blocked")


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("HERMES_DELEGATED_CHILD_CONTEXT", None)
    result = subprocess.run(list(args), check=False, capture_output=True, text=True, timeout=180, env=env)
    if check and result.returncode:
        raise RuntimeError(f"exit {result.returncode}: {' '.join(args)}\n{result.stdout}\n{result.stderr}")
    return result


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rr_profiles() -> list[str]:
    root = HERMES_HOME / "profiles"
    return sorted(path.name for path in root.iterdir() if path.is_dir() and path.name.startswith("rr-"))


def active_tasks(board: str = "rr-team") -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for status in ACTIVE:
        result = run("hermes", "kanban", "--board", board, "list", "--status", status, "--json")
        tasks.extend(json.loads(result.stdout or "[]", strict=False))
    return tasks


def sanitized_profile_files(profile: str) -> list[Path]:
    root = HERMES_HOME / "profiles" / profile
    allowed: list[Path] = []
    for exact in (root / "SOUL.md", root / "profile.yaml", root / "memories" / "MEMORY.md", root / "memories" / "USER.md"):
        if exact.is_file():
            allowed.append(exact)
    skills = root / "skills"
    if skills.is_dir():
        for path in skills.rglob("*"):
            relative = path.relative_to(root).as_posix().lower()
            unique_rr_skill = relative.startswith("skills/recruiter-radar/") or "/rr-" in relative
            prohibited = any(
                part.lower().startswith(".env")
                or part.lower() == "auth.json"
                or "credential" in part.lower()
                or part.lower() in {"sessions", "request_dump", "dumps"}
                for part in path.parts
            )
            if path.is_file() and unique_rr_skill and not prohibited:
                allowed.append(path)
    return allowed


def snapshot() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = STATE / stamp
    archives = root / "archives"
    archives.mkdir(parents=True, exist_ok=True)
    profiles = rr_profiles()
    manifest: dict[str, Any] = {"created_at": stamp, "rr_profiles": profiles, "universal_profiles": UNIVERSAL, "profiles": {}}
    for profile in profiles:
        files = sanitized_profile_files(profile)
        archive = archives / f"{profile}-safe.zip"
        entries: list[dict[str, Any]] = []
        profile_root = HERMES_HOME / "profiles" / profile
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for path in files:
                relative = path.relative_to(profile_root).as_posix()
                bundle.write(path, relative)
                entries.append({"path": relative, "sha256": sha256(path), "bytes": path.stat().st_size})
        manifest["profiles"][profile] = {"archive": str(archive), "archive_sha256": sha256(archive), "files": entries}
    tasks = active_tasks()
    task_snapshot = [{key: task.get(key) for key in ("id", "title", "assignee", "status", "skills", "max_retries", "workspace_kind", "branch_name")} for task in tasks]
    manifest["active_tasks"] = task_snapshot
    commands = {
        "kanban_config": ["hermes", "config", "get", "kanban"],
        "profiles": ["hermes", "profile", "list"],
        "gateways": ["hermes", "gateway", "list"],
        "boards": ["hermes", "kanban", "boards", "list", "--json"],
    }
    manifest["routing_snapshot"] = {}
    for name, command in commands.items():
        result = run(*command, check=False)
        manifest["routing_snapshot"][name] = {"exit_code": result.returncode, "stdout": result.stdout}
    root.joinpath("snapshot.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    root.joinpath("snapshot.sha256").write_text(sha256(root / "snapshot.json") + "  snapshot.json\n", encoding="utf-8")
    STATE.joinpath("latest.txt").parent.mkdir(parents=True, exist_ok=True)
    STATE.joinpath("latest.txt").write_text(str(root), encoding="utf-8")
    return root


def latest_snapshot() -> Path:
    marker = STATE / "latest.txt"
    if not marker.is_file():
        raise RuntimeError("no migration snapshot; run snapshot first")
    return Path(marker.read_text(encoding="utf-8").strip())


def verified_snapshot(root: Path | None = None) -> tuple[Path, dict[str, Any]]:
    root = root or latest_snapshot()
    snapshot_path = root / "snapshot.json"
    checksum_path = root / "snapshot.sha256"
    expected = checksum_path.read_text(encoding="utf-8").split()[0]
    actual = sha256(snapshot_path)
    if actual != expected:
        raise RuntimeError(f"snapshot checksum mismatch: expected {expected}, got {actual}")
    return root, json.loads(snapshot_path.read_text(encoding="utf-8"))


def plan(snapshot_root: Path | None = None) -> list[dict[str, str]]:
    root = snapshot_root or latest_snapshot()
    data = json.loads((root / "snapshot.json").read_text(encoding="utf-8"))
    planned: list[dict[str, str]] = []
    for task in data["active_tasks"]:
        task_id = task["id"]
        if task_id not in TASK_ROUTING:
            raise RuntimeError(f"unmapped active task: {task_id} {task['title']}")
        owner, task_type = TASK_ROUTING[task_id]
        planned.append({"id": task_id, "from": task["assignee"], "to": owner, "status": task["status"], "task_type": task_type})
    return planned


def cutover(dry_run: bool = False) -> list[dict[str, Any]]:
    planned = plan()
    if dry_run:
        return planned
    evidence: list[dict[str, Any]] = []
    for item in planned:
        if item["from"] != item["to"]:
            result = run("hermes", "kanban", "--board", "rr-team", "reassign", item["id"], item["to"], "--reason", "Universal fleet cutover; source profile frozen")
            evidence.append({"action": "reassign", "id": item["id"], "exit_code": result.returncode})
        marker = f"task_type: {item['task_type']}\nrr-project: automatically applied by fleet-policy for board rr-team"
        result = run("hermes", "kanban", "--board", "rr-team", "comment", item["id"], marker, "--author", "ox-alpha")
        evidence.append({"action": "comment", "id": item["id"], "exit_code": result.returncode})
        if item["status"] == "blocked":
            result = run(
                "hermes", "kanban", "--board", "rr-team", "block", item["id"],
                "Cutover preservation: original blocked gate remains in force.", "--kind", "needs_input",
            )
            evidence.append({"action": "preserve_blocked", "id": item["id"], "exit_code": result.returncode})
    for key, value in (("kanban.orchestrator_profile", "company"), ("kanban.default_assignee", "company"), ("kanban.max_in_progress", "5")):
        result = run("hermes", "config", "set", key, value)
        evidence.append({"action": "config", "key": key, "value": value, "exit_code": result.returncode})
    return evidence


def rollback(dry_run: bool = False) -> list[dict[str, Any]]:
    root, data = verified_snapshot()
    evidence: list[dict[str, Any]] = []
    for task in data["active_tasks"]:
        action = {"id": task["id"], "to": task["assignee"]}
        if dry_run:
            evidence.append(action)
        else:
            result = run("hermes", "kanban", "--board", "rr-team", "reassign", task["id"], task["assignee"], "--reason", "Idempotent rollback to pre-cutover owner")
            evidence.append({**action, "exit_code": result.returncode})
            if task["status"] == "blocked":
                result = run(
                    "hermes", "kanban", "--board", "rr-team", "block", task["id"],
                    "Rollback preservation: original blocked gate remains in force.", "--kind", "needs_input",
                )
                evidence.append({"action": "preserve_blocked", "id": task["id"], "exit_code": result.returncode})
    previous = yaml.safe_load(data["routing_snapshot"]["kanban_config"]["stdout"]) or {}
    restore = (
        ("kanban.orchestrator_profile", previous.get("orchestrator_profile")),
        ("kanban.default_assignee", previous.get("default_assignee")),
        ("kanban.max_in_progress", previous.get("max_in_progress")),
    )
    for key, value in restore:
        encoded = "null" if value is None else json.dumps(value)
        if dry_run:
            evidence.append({"action": "config", "key": key, "value": value})
        else:
            result = run("hermes", "config", "set", key, encoded)
            evidence.append({"action": "config", "key": key, "value": value, "exit_code": result.returncode})
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("snapshot")
    cut = sub.add_parser("cutover"); cut.add_argument("--dry-run", action="store_true")
    roll = sub.add_parser("rollback"); roll.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.command == "snapshot":
        print(snapshot())
    elif args.command == "cutover":
        print(json.dumps(cutover(args.dry_run), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(rollback(args.dry_run), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
