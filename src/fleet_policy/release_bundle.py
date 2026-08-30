from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

RELEASE_PATHS = (
    "pyproject.toml",
    "uv.lock",
    "plugin.yaml",
    "README.md",
    "CHANGELOG.md",
    "config",
    "src",
    "tests",
    "scripts",
    "integrations/hermes/fleet-policy-plugin",
)

_EXCLUDED_PARTS = {".git", ".venv", ".state", ".pytest_cache", "__pycache__"}
_EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
_MANIFEST_NAME = "RELEASE-MANIFEST.json"


def _included(path: Path) -> bool:
    return not any(part in _EXCLUDED_PARTS for part in path.parts) and path.suffix not in _EXCLUDED_SUFFIXES


def release_inventory(root: str | Path) -> list[str]:
    root = Path(root)
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and _included(path)
    )


def _copy_path(source_root: Path, destination_root: Path, relative: str) -> None:
    source = source_root / relative
    if not source.exists():
        raise FileNotFoundError(f"release path is missing: {relative}")
    if source.is_symlink() or (source.is_dir() and any(path.is_symlink() for path in source.rglob("*"))):
        raise ValueError(f"release source contains a symbolic link: {relative}")
    destination = destination_root / relative
    if source.is_dir():
        shutil.copytree(
            source,
            destination,
            dirs_exist_ok=False,
            ignore=shutil.ignore_patterns(".git", ".venv", ".state", ".pytest_cache", "__pycache__", "*.pyc", "*.pyo"),
        )
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_release_bundle(source_root: str | Path, destination_root: str | Path) -> list[str]:
    source_root = Path(source_root).resolve()
    destination_root = Path(destination_root).resolve()
    if destination_root.exists():
        raise FileExistsError(f"release destination already exists: {destination_root}")
    if destination_root == source_root or source_root in destination_root.parents:
        raise ValueError("release destination must be outside the source tree")

    destination_root.mkdir(parents=True)
    try:
        for relative in RELEASE_PATHS:
            _copy_path(source_root, destination_root, relative)
        inventory = release_inventory(destination_root)
        manifest = {
            "schema": "fleet-policy-release-bundle-v1",
            "files": [
                {"path": relative, "sha256": _sha256(destination_root / relative)}
                for relative in inventory
            ],
        }
        (destination_root / _MANIFEST_NAME).write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return release_inventory(destination_root)
    except Exception:
        shutil.rmtree(destination_root, ignore_errors=True)
        raise


def verify_release_bundle(bundle_root: str | Path) -> list[str]:
    bundle_root = Path(bundle_root).resolve()
    manifest_path = bundle_root / _MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "fleet-policy-release-bundle-v1":
        raise ValueError("unsupported release manifest schema")
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise ValueError("release manifest files must be a list")

    expected: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
            raise ValueError("invalid release manifest entry")
        relative = str(entry["path"])
        if relative in expected:
            raise ValueError(f"duplicate release manifest path: {relative}")
        raw_candidate = bundle_root / relative
        candidate = raw_candidate.resolve()
        if bundle_root not in candidate.parents or raw_candidate.is_symlink():
            raise ValueError(f"release path escapes bundle: {relative}")
        digest = str(entry["sha256"])
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError(f"invalid release checksum: {relative}")
        expected[relative] = digest

    actual = set(release_inventory(bundle_root)) - {_MANIFEST_NAME}
    if actual != set(expected):
        raise ValueError("release bundle inventory differs from manifest")
    for relative, digest in expected.items():
        if _sha256(bundle_root / relative) != digest:
            raise ValueError(f"release bundle checksum mismatch: {relative}")
    return sorted(actual)
