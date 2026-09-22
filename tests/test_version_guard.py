"""v1.2.29: version-collision guard unit tests (fixture-based, NO network).

Covers scripts/check_version_uniqueness.py: released-set parsing from a
synthetic trunk CHANGELOG, collision detection against the released set and
other open PR heads, own-PR exemption (by head sha and by ref name),
trunk-head exemption, and the offline JSON verdict contract of main().
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

MODULE_PATH = pathlib.Path(__file__).parents[1] / "scripts" / "check_version_uniqueness.py"
spec = importlib.util.spec_from_file_location("check_version_uniqueness", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


CHANGELOG = """# Changelog

## [1.2.28] - 2026-09-22

### Changed
- Integration release.

## [1.2.9] - 2026-09-01

## [1.2.10] - 2026-09-02

## Unreleased

- not a version heading
"""


def pr(name, oid, version):
    return {"headRefName": name, "headRefOid": oid, "version": version}


def test_parse_plugin_version_quoted_and_plain():
    assert mod.parse_plugin_version('name: x\nversion: "1.2.29"\n') == "1.2.29"
    assert mod.parse_plugin_version("version: 1.2.5\n") == "1.2.5"


def test_released_versions_and_max():
    released = mod.released_versions(CHANGELOG)
    assert released == {"1.2.28", "1.2.9", "1.2.10"}
    assert mod.released_max(CHANGELOG) == "1.2.28"


def test_version_ordering():
    assert mod.parse_version("1.2.9") < mod.parse_version("1.2.10")
    assert mod.parse_version("1.2.10") < mod.parse_version("1.2.29")


def test_evaluate_clean_pass():
    verdict = mod.evaluate(
        version="1.2.29",
        released={"1.2.28"},
        prs=[pr("other", "b" * 40, "1.2.25")],
        own_head="a" * 40,
        own_ref="fix/mine",
        trunk_head="c" * 40,
    )
    assert verdict["collision"] is False
    assert verdict["colliding_refs"] == []
    assert verdict["version"] == "1.2.29"
    assert verdict["released_max"] == "1.2.28"


def test_evaluate_collision_with_released_set():
    verdict = mod.evaluate(
        version="1.2.28",
        released={"1.2.28", "1.2.27"},
        prs=[],
        own_head="a" * 40,
        own_ref="fix/mine",
        trunk_head="c" * 40,
    )
    assert verdict["collision"] is True
    assert "released:1.2.28" in verdict["colliding_refs"]


def test_evaluate_trunk_head_exempt_from_released_set():
    verdict = mod.evaluate(
        version="1.2.28",
        released={"1.2.28"},
        prs=[],
        own_head="c" * 40,
        own_ref=None,
        trunk_head="c" * 40,
    )
    assert verdict["collision"] is False


def test_evaluate_own_pr_exemption_by_sha():
    verdict = mod.evaluate(
        version="1.2.29",
        released={"1.2.28"},
        prs=[pr("fix/mine", "a" * 40, "1.2.29")],
        own_head="a" * 40,
        own_ref=None,
        trunk_head="c" * 40,
    )
    assert verdict["collision"] is False


def test_evaluate_own_pr_exemption_by_ref_name():
    verdict = mod.evaluate(
        version="1.2.29",
        released={"1.2.28"},
        prs=[pr("fix/mine", "d" * 40, "1.2.29")],
        own_head="a" * 40,
        own_ref="fix/mine",
        trunk_head="c" * 40,
    )
    assert verdict["collision"] is False


def test_evaluate_collision_with_other_open_pr():
    verdict = mod.evaluate(
        version="1.2.29",
        released={"1.2.28"},
        prs=[pr("other-branch", "e" * 40, "1.2.29")],
        own_head="a" * 40,
        own_ref="fix/mine",
        trunk_head="c" * 40,
    )
    assert verdict["collision"] is True
    assert "other-branch" in verdict["colliding_refs"]


def test_evaluate_unreadable_pr_head_is_not_a_collision_but_listed():
    verdict = mod.evaluate(
        version="1.2.29",
        released={"1.2.28"},
        prs=[pr("broken", "f" * 40, None)],
        own_head="a" * 40,
        own_ref="fix/mine",
        trunk_head="c" * 40,
    )
    assert verdict["collision"] is False
    assert verdict["unverified_refs"] == ["broken"]


def _make_root(tmp_path, version):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "plugin.yaml").write_text(
        f'name: fleet-x\nversion: "{version}"\n', encoding="utf-8"
    )
    return root


def test_main_offline_clean_verdict(tmp_path, capsys):
    root = _make_root(tmp_path, "1.2.29")
    changelog = tmp_path / "trunk-changelog.md"
    changelog.write_text(CHANGELOG, encoding="utf-8")
    prs_file = tmp_path / "prs.json"
    prs_file.write_text(
        json.dumps([pr("other", "b" * 40, "1.2.25")]), encoding="utf-8"
    )
    code = mod.main([
        "--root", str(root),
        "--trunk-changelog", str(changelog),
        "--offline-prs", str(prs_file),
    ])
    out = capsys.readouterr().out
    verdict = json.loads(out)
    assert code == 0
    assert verdict["version"] == "1.2.29"
    assert verdict["released_max"] == "1.2.28"
    assert verdict["collision"] is False
    assert verdict["colliding_refs"] == []


def test_main_offline_collision_exit_nonzero(tmp_path, capsys):
    root = _make_root(tmp_path, "1.2.28")
    changelog = tmp_path / "trunk-changelog.md"
    changelog.write_text(CHANGELOG, encoding="utf-8")
    prs_file = tmp_path / "prs.json"
    prs_file.write_text(json.dumps([]), encoding="utf-8")
    code = mod.main([
        "--root", str(root),
        "--trunk-changelog", str(changelog),
        "--offline-prs", str(prs_file),
    ])
    out = capsys.readouterr().out
    verdict = json.loads(out)
    assert code == 1
    assert verdict["collision"] is True
    assert "released:1.2.28" in verdict["colliding_refs"]
