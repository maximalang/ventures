"""v1.2.13 M2: deterministic pristine-manifest semantics.

The release-attestation pristine manifest MUST record the sha256 of each
path's CANONICAL git-blob bytes (LF), never the bytes of a local checkout.
The pre-fix manifest hashed the Windows CRLF working-tree bytes, so it matched
0/57 files on a Linux CI checkout (autocrlf=false) and was therefore
non-deterministic across platforms — the defect this test locks down.

The oracle recomputes every hash from ``git cat-file`` against the pinned
pristine ref, which yields LF blob bytes independent of core.autocrlf, the
platform, or the local checkout. A CRLF byte in any blob is itself a hard
failure: canonical content is LF, so a CRLF blob would mean the manifest was
regenerated from checkout bytes again.

Git object availability is a property of the checkout, not of the manifest's
correctness: when the git binary or the pinned ref is genuinely absent (e.g. a
shallow clone without history) the test skips with an explicit reason rather
than silently passing. CI checks out full history (fetch-depth: 0), so there
the oracle runs and every hash is asserted.
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
MANIFEST = ROOT / "manifest-pristine-v1211.txt"
# The commit that introduced the pristine manifest; every recorded hash is the
# sha256 of that commit's canonical (LF) git blob for the path. Pinned so the
# oracle is reproducible and never drifts with HEAD.
PRISTINE_REF = "a81431afb8bf33cfc6ddc5c2c4d990a7fe049df5"


def _parse_manifest() -> list[tuple[str, str]]:
    raw = MANIFEST.read_bytes()
    # The manifest file itself is canonical LF; a CRLF manifest would be a
    # regression of the same non-determinism the hashes guard against.
    assert b"\r\n" not in raw, "manifest must use LF newlines"
    assert raw.endswith(b"\n") and not raw.endswith(b"\n\n"), "exactly one trailing LF"
    lines = raw.decode("utf-8").split("\n")[:-1]
    entries: list[tuple[str, str]] = []
    for line in lines:
        digest, star_path = line.split(" ", 1)
        assert len(digest) == 64, f"bad sha256 width: {line}"
        assert all(c in "0123456789abcdef" for c in digest), f"non-hex sha: {line}"
        assert star_path.startswith("*"), f"missing sha256sum binary marker: {line}"
        path = star_path[1:]
        assert path and ".." not in path.split("/"), f"unsafe path: {line}"
        entries.append((digest, path))
    assert entries, "manifest is empty"
    paths = [path for _, path in entries]
    assert len(paths) == len(set(paths)), "duplicate manifest path"
    return entries


def _blob_bytes(paths: list[str]) -> dict[str, bytes]:
    if shutil.which("git") is None:
        pytest.skip("git binary unavailable; cannot verify pristine manifest")
    spec = "".join(f"{PRISTINE_REF}:{p}\n" for p in paths).encode("utf-8")
    proc = subprocess.run(
        ["git", "cat-file", "--batch"], cwd=ROOT, input=spec, capture_output=True,
    )
    if proc.returncode != 0:
        pytest.skip(
            f"pristine ref {PRISTINE_REF[:12]} unavailable in this checkout "
            f"(shallow clone?); CI uses fetch-depth: 0"
        )
    out = proc.stdout
    blobs: dict[str, bytes] = {}
    pos = 0
    for path in paths:
        header_end = out.index(b"\n", pos)
        header = out[pos:header_end].decode("utf-8").split(" ")
        assert header[1] == "blob", f"{path} is not a blob at pristine ref: {header}"
        size = int(header[2])
        start = header_end + 1
        blobs[path] = out[start:start + size]
        pos = start + size + 1
    return blobs


def test_pristine_manifest_records_canonical_lf_blob_hashes():
    entries = _parse_manifest()
    blobs = _blob_bytes([path for _, path in entries])
    for digest, path in entries:
        blob = blobs[path]
        # Canonical content is LF; a CRLF blob means checkout bytes leaked back
        # into the manifest generation (the exact defect under test).
        assert b"\r\n" not in blob, f"{path}: blob carries CRLF, not canonical LF"
        actual = hashlib.sha256(blob).hexdigest()
        assert actual == digest, (
            f"{path}: manifest hash {digest} != canonical LF-blob sha256 {actual}"
        )
