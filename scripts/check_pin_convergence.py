#!/usr/bin/env python3
"""Pin-convergence check (v1.2.29).

Root cause addressed: the fleet's policy plugin is deployed as a git
checkout under each profile's plugin tree. After a release, profiles can sit
on different commits (partial rollout), so the gate behavior differs per
worker — exactly the drift that made runtime sha reconciliation necessary
during incident diagnosis.

Contract:
- expected sha = argv[1] (positional, required);
- profiles root = --profiles-root PATH or the HERMES_PROFILES_ROOT
  environment variable (required unless passed);
- every <profiles-root>/*/plugins/fleet-policy directory is one entry: its
  git HEAD sha (``git rev-parse HEAD``) and its plugin.yaml version;
- exit 0 only when EVERY entry resolves and equals the expected sha;
  otherwise exit non-zero and list the divergent entries;
- exit 2 on usage/environment errors (missing root, no entries, git binary
  unavailable).

Fail-closed: an entry whose sha cannot be resolved (not a git checkout, git
failure) is divergent, never skipped. Entries are discovered from the
filesystem under the given root only — this script never hardcodes any
machine-specific profile location.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

PLUGIN_SUBPATH = ("plugins", "fleet-policy")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_VERSION_LINE = re.compile(r'^\s*version:\s*"?([0-9][0-9A-Za-z.\-+]*)"?\s*$', re.M)


def parse_plugin_version(text: str) -> str | None:
    match = _VERSION_LINE.search(text)
    return match.group(1) if match else None


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=30
    )


def read_entry(plugin_dir: Path) -> dict:
    """Resolve one deployed plugin entry: sha + version (fail-closed)."""
    entry: dict = {"path": str(plugin_dir), "sha": None, "version": None, "error": None}
    manifest = plugin_dir / "plugin.yaml"
    if manifest.is_file():
        try:
            entry["version"] = parse_plugin_version(
                manifest.read_text(encoding="utf-8", errors="replace")
            )
        except OSError as exc:
            entry["error"] = f"plugin.yaml unreadable: {exc}"
    else:
        entry["error"] = "plugin.yaml missing"
    if shutil.which("git") is None:
        entry["error"] = entry["error"] or "git binary unavailable"
        return entry
    proc = run_git(["rev-parse", "HEAD"], cwd=plugin_dir)
    if proc.returncode == 0:
        sha = proc.stdout.strip().lower()
        if SHA_RE.match(sha):
            entry["sha"] = sha
        else:
            entry["error"] = f"unparsable HEAD: {sha[:80]!r}"
    else:
        detail = proc.stderr.strip().splitlines()[0][:160] if proc.stderr.strip() else "git rev-parse failed"
        entry["error"] = entry["error"] or detail
    return entry


def discover_entries(profiles_root: Path) -> list[dict]:
    if not profiles_root.is_dir():
        raise RuntimeError(f"profiles root is not a directory: {profiles_root}")
    entries: list[dict] = []
    for profile_dir in sorted(p for p in profiles_root.iterdir() if p.is_dir()):
        plugin_dir = profile_dir.joinpath(*PLUGIN_SUBPATH)
        if plugin_dir.is_dir():
            entry = read_entry(plugin_dir)
            entry["profile"] = profile_dir.name
            entries.append(entry)
    return entries


def evaluate(expected_sha: str, entries: list[dict]) -> dict:
    divergent = [
        {
            "profile": entry["profile"],
            "sha": entry["sha"],
            "version": entry["version"],
            "error": entry["error"],
        }
        for entry in entries
        if entry["sha"] != expected_sha
    ]
    return {
        "expected_sha": expected_sha,
        "entries": [
            {"profile": e["profile"], "sha": e["sha"], "version": e["version"]}
            for e in entries
        ],
        "converged": not divergent,
        "divergent": divergent,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("expected_sha", help="40-hex sha every deployment must sit on")
    parser.add_argument(
        "--profiles-root",
        default=None,
        help="root containing profile dirs (default: $HERMES_PROFILES_ROOT)",
    )
    args = parser.parse_args(argv)

    expected = args.expected_sha.strip().lower()
    if not SHA_RE.match(expected):
        print(json.dumps({"error": f"expected sha is not 40-hex: {args.expected_sha!r}"}), file=sys.stderr)
        return 2

    root_raw = args.profiles_root or os.environ.get("HERMES_PROFILES_ROOT")
    if not root_raw:
        print(json.dumps({"error": "profiles root not provided (pass --profiles-root or set HERMES_PROFILES_ROOT)"}), file=sys.stderr)
        return 2

    try:
        entries = discover_entries(Path(root_raw).expanduser().resolve())
    except RuntimeError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
    if not entries:
        print(json.dumps({"error": f"no deployed plugins under {root_raw}"}), file=sys.stderr)
        return 2

    verdict = evaluate(expected, entries)
    print(json.dumps(verdict, sort_keys=True))
    return 0 if verdict["converged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
