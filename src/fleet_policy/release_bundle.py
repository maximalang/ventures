from __future__ import annotations

import hashlib
import json
import shutil
import stat
from pathlib import Path

RELEASE_PATHS = (
    "pyproject.toml",
    "uv.lock",
    "plugin.yaml",
    "AGENTS.md",
    "APPROVALS.md",
    "README.md",
    "CHANGELOG.md",
    "OPERATING_SYSTEM.md",
    "PORTFOLIO.md",
    "config",
    "src",
    "tests",
    "scripts",
    "skills/company-os",
    "skills/rr-project",
    "integrations/hermes/fleet-policy-plugin",
)

_DIRECTORY_RELEASE_PATHS = {
    "config",
    "src",
    "tests",
    "scripts",
    "skills/company-os",
    "skills/rr-project",
    "integrations/hermes/fleet-policy-plugin",
}
_EXCLUDED_PARTS = {".git", ".venv", ".state", ".pytest_cache", "__pycache__"}
_EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
_GENERATED_METADATA_SUFFIXES = (".egg-info", ".dist-info", ".egg")
_MANIFEST_NAME = "RELEASE-MANIFEST.json"
_REPARSE_POINT_ATTRIBUTE = 0x400


def _is_generated_metadata_part(part: str) -> bool:
    return part.lower().endswith(_GENERATED_METADATA_SUFFIXES)


def _included(path: Path) -> bool:
    if any(part in _EXCLUDED_PARTS or _is_generated_metadata_part(part) for part in path.parts):
        return False
    return path.suffix not in _EXCLUDED_SUFFIXES


def _generated_metadata(root: Path) -> list[str]:
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if any(_is_generated_metadata_part(part) for part in path.relative_to(root).parts)
    )


def _copy_ignore(_directory: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        lowered = name.lower()
        if (
            name in _EXCLUDED_PARTS
            or lowered in _EXCLUDED_PARTS
            or _is_generated_metadata_part(lowered)
            or lowered.endswith(tuple(_EXCLUDED_SUFFIXES))
        ):
            ignored.add(name)
    return ignored


def _is_link_or_reparse(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError as exc:
        raise ValueError(f"cannot inspect release path: {path}") from exc
    return bool(attributes & _REPARSE_POINT_ATTRIBUTE)


def _assert_tree_has_no_links(root: Path, label: str) -> None:
    if _is_link_or_reparse(root):
        raise ValueError(f"{label} contains link or reparse point: .")
    if root.is_file():
        return
    if not root.is_dir():
        raise ValueError(f"{label} is neither a file nor a directory: {root}")

    pending = [root]
    while pending:
        current = pending.pop()
        try:
            children = list(current.iterdir())
        except OSError as exc:
            raise ValueError(f"cannot inspect release directory: {current}") from exc
        for child in children:
            relative = child.relative_to(root).as_posix()
            if _is_link_or_reparse(child):
                raise ValueError(f"{label} contains link or reparse point: {relative}")
            try:
                mode = child.lstat().st_mode
            except OSError as exc:
                raise ValueError(f"cannot inspect release path: {child}") from exc
            if stat.S_ISDIR(mode):
                pending.append(child)
            elif not stat.S_ISREG(mode):
                raise ValueError(f"{label} contains unsupported filesystem entry: {relative}")


def release_inventory(root: str | Path) -> list[str]:
    root = Path(root)
    _assert_tree_has_no_links(root, "release bundle")
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and _included(path)
    )


def _copy_path(source_root: Path, destination_root: Path, relative: str) -> None:
    source = source_root / relative
    if not source.exists():
        raise FileNotFoundError(f"release path is missing: {relative}")
    _assert_tree_has_no_links(source, f"release source {relative}")
    destination = destination_root / relative
    if source.is_dir():
        shutil.copytree(
            source,
            destination,
            dirs_exist_ok=False,
            ignore=_copy_ignore,
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
    bundle_root = Path(bundle_root).absolute()
    _assert_tree_has_no_links(bundle_root, "release bundle")
    leaked_metadata = _generated_metadata(bundle_root)
    if leaked_metadata:
        raise ValueError(
            "release bundle contains generated package metadata: " + ", ".join(sorted(set(leaked_metadata)))
        )
    for relative in RELEASE_PATHS:
        required = bundle_root / relative
        if not required.exists():
            raise ValueError(f"missing required release path: {relative}")
        if _is_link_or_reparse(required):
            raise ValueError(f"release required path is a link or reparse point: {relative}")
        if relative in _DIRECTORY_RELEASE_PATHS and not required.is_dir():
            raise ValueError(f"required release path is not a directory: {relative}")
        if relative not in _DIRECTORY_RELEASE_PATHS and not required.is_file():
            raise ValueError(f"required release path is not a file: {relative}")

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
