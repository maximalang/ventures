#!/usr/bin/env python3
"""Version-collision guard (v1.2.29).

Root cause addressed: the 1.2.25 duplicate — two branches picked the same
next version "by eye" and only the second to merge could keep its pin.

Contract (deterministic, exits non-zero on collision):

1. Branch version is read from the repo-root ``plugin.yaml``.
2. Released set comes from the trunk ``CHANGELOG.md`` (every ``## [X.Y.Z]``
   heading).
3. Open-PR heads are enumerated via ``gh pr list --json headRefName,headRefOid``
   and each head's version read via ``gh api
   repos/maximalang/ventures/contents/plugin.yaml?ref=<head>``.  When ``gh``
   is unavailable the script falls back to ``git ls-remote --heads origin``
   (read-only, no fetch) and skips version resolution for foreign heads,
   listing them as unverified.
4. FAIL if the branch version collides with the released set or another open
   PR — unless the colliding PR IS this branch's own head (matched by head
   sha, or by ref name when the sha is not yet pushed) or the working head
   equals the trunk head (fresh branch with no pin commit yet).

The JSON verdict printed on stdout:
``{version, released_max, collision, colliding_refs, unverified_refs}``.

Offline mode for tests/CI dry-runs: ``--offline-prs <file>`` supplies the PR
list as JSON ``[{headRefName, headRefOid, version}]`` and disables all
network access; ``--trunk-changelog <file>`` overrides the released-set
source (defaults to ``git show origin/<trunk>:CHANGELOG.md``, falling back to
the local CHANGELOG.md when the remote ref is unavailable).

This script never mutates anything: it only reads files and runs read-only
git/gh queries.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = "maximalang/ventures"
DEFAULT_TRUNK = "codex/company-os"
PLUGIN_REL = "plugin.yaml"
CHANGELOG_REL = "CHANGELOG.md"

_VERSION_LINE = re.compile(r'^\s*version\s*:\s*"?([0-9]+(?:\.[0-9]+)*)\s*"?\s*$', re.M)
_RELEASE_HEADING = re.compile(r"^##\s+\[(\d+\.\d+\.\d+)\]", re.M)


def parse_version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


def parse_plugin_version(text: str) -> str | None:
    match = _VERSION_LINE.search(text)
    return match.group(1) if match else None


def released_versions(changelog_text: str) -> set[str]:
    return set(_RELEASE_HEADING.findall(changelog_text))


def released_max(changelog_text: str) -> str | None:
    versions = released_versions(changelog_text)
    if not versions:
        return None
    return max(versions, key=parse_version)


def _run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", timeout=60
    )


def read_branch_version(root: Path) -> str:
    text = (root / PLUGIN_REL).read_text(encoding="utf-8")
    version = parse_plugin_version(text)
    if not version:
        raise SystemExit(f"no version line in {PLUGIN_REL}")
    return version


def read_trunk_changelog(root: Path, trunk: str) -> str:
    """Trunk CHANGELOG bytes via the remote-tracking ref; local file as fallback."""
    proc = _run(["git", "show", f"origin/{trunk}:{CHANGELOG_REL}"], cwd=root)
    if proc.returncode == 0 and proc.stdout.strip():
        return proc.stdout
    return (root / CHANGELOG_REL).read_text(encoding="utf-8")


def own_head(root: Path) -> str | None:
    proc = _run(["git", "rev-parse", "HEAD"], cwd=root)
    return proc.stdout.strip() if proc.returncode == 0 else None


def own_ref(root: Path) -> str | None:
    proc = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root)
    if proc.returncode != 0:
        return None
    ref = proc.stdout.strip()
    return None if ref in ("", "HEAD") else ref


def trunk_head(root: Path, trunk: str) -> str | None:
    proc = _run(["git", "rev-parse", f"origin/{trunk}"], cwd=root)
    return proc.stdout.strip() if proc.returncode == 0 else None


def gh_open_prs() -> list[dict]:
    """[{headRefName, headRefOid, version}] for open PRs against the repo."""
    proc = _run(
        ["gh", "pr", "list", "--repo", REPO, "--state", "open",
         "--json", "headRefName,headRefOid", "--limit", "200"]
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh pr list failed: {proc.stderr.strip()[:200]}")
    prs = json.loads(proc.stdout)
    for entry in prs:
        oid = entry.get("headRefOid") or ""
        if not re.fullmatch(r"[0-9a-f]{40}", oid):
            entry["version"] = None
            continue
        api = _run(
            ["gh", "api", f"repos/{REPO}/contents/{PLUGIN_REL}?ref={oid}",
             "--jq", ".content"]
        )
        if api.returncode == 0:
            try:
                raw = base64.b64decode(api.stdout, validate=True).decode("utf-8")
                entry["version"] = parse_plugin_version(raw)
                continue
            except Exception:
                pass
        entry["version"] = None
    return prs


def git_fallback_prs(root: Path) -> list[dict]:
    """gh absent: enumerate remote heads read-only; versions stay unresolved."""
    proc = _run(["git", "ls-remote", "--heads", "origin"], cwd=root)
    if proc.returncode != 0:
        raise RuntimeError(f"git ls-remote failed: {proc.stderr.strip()[:200]}")
    entries = []
    for line in proc.stdout.splitlines():
        sha, _, ref = line.partition("\t")
        name = ref.removeprefix("refs/heads/")
        entries.append({"headRefName": name, "headRefOid": sha.strip(), "version": None})
    return entries


def collect_prs(root: Path) -> tuple[list[dict], str]:
    if shutil.which("gh"):
        return gh_open_prs(), "gh"
    return git_fallback_prs(root), "git-ls-remote"


def evaluate(*, version: str, released: set[str], prs: list[dict],
             own_head: str | None, own_ref: str | None,
             trunk_head: str | None) -> dict:
    colliding: list[str] = []
    unverified: list[str] = []
    on_trunk_head = bool(own_head and trunk_head and own_head == trunk_head)
    if version in released and not on_trunk_head:
        colliding.append(f"released:{version}")
    for entry in prs:
        head = entry.get("headRefOid") or ""
        name = entry.get("headRefName") or ""
        is_own = (own_head and head == own_head) or (own_ref and name == own_ref)
        if is_own:
            continue
        entry_version = entry.get("version")
        if entry_version is None:
            unverified.append(name)
            continue
        if entry_version == version:
            colliding.append(name)
    return {
        "version": version,
        "released_max": max(released, key=parse_version) if released else None,
        "collision": bool(colliding),
        "colliding_refs": colliding,
        "unverified_refs": unverified,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="workspace repo root")
    parser.add_argument("--trunk", default=DEFAULT_TRUNK)
    parser.add_argument("--trunk-changelog", default=None,
                        help="offline override: changelog file for the released set")
    parser.add_argument("--offline-prs", default=None,
                        help="offline override: JSON file [{headRefName, headRefOid, version}]")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    version = read_branch_version(root)

    if args.trunk_changelog:
        changelog_text = Path(args.trunk_changelog).read_text(encoding="utf-8")
        trunk_head_sha = None
    else:
        changelog_text = read_trunk_changelog(root, args.trunk)
        trunk_head_sha = trunk_head(root, args.trunk)

    if args.offline_prs:
        prs = json.loads(Path(args.offline_prs).read_text(encoding="utf-8"))
        head = own_head(root)
        ref = own_ref(root)
    else:
        try:
            prs, _source = collect_prs(root)
        except RuntimeError as exc:
            print(json.dumps({"error": str(exc)}), file=sys.stderr)
            return 2
        head = own_head(root)
        ref = own_ref(root)

    verdict = evaluate(
        version=version,
        released=released_versions(changelog_text),
        prs=prs,
        own_head=head,
        own_ref=ref,
        trunk_head=trunk_head_sha,
    )
    print(json.dumps(verdict, sort_keys=True))
    return 1 if verdict["collision"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
