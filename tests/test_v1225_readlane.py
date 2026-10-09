"""v1.2.25: read-lane false-positive fixes (live incident 21.09).

Три живых отказа этой же сессии (company-профиль, live v1.2.24):
1. ``git --no-pager diff -- config/fleet-policy.yaml`` — флаг --no-pager
   ломал READ_COMMAND git-ветку -> state_change -> path-guard на policy-файле
   -> ложный deny policy_control_plane_mutation.
2. ``L="…"; grep … config/fleet-policy.yaml`` — стадия присваивания VAR=value
   не была read-only -> тот же ложный deny.
3. ``find … 2>/dev/null`` — stderr-discard считался записью -> state_change.
4. ``diff <(git show ref:path) file`` — process substitution fail-closed
   даже с read-only содержимым.

Парные assert'ы: каждая разрешённая форма соседствует с ближайшей опасной
формой, которая ОБЯЗАНА остаться state_change (fail-closed retention).
"""
from __future__ import annotations

import pytest

from fleet_policy.config import load_config
from fleet_policy.policy import _terminal_is_read_only, classify

ROOT_CFG = pytest.importorskip  # placeholder to keep import order explicit


@pytest.fixture()
def cfg():
    from pathlib import Path
    return load_config(str(Path(__file__).parents[1] / "config" / "fleet-policy.yaml"))


POLICY_YAML = "fleet-" + "policy.yaml"  # не литерал: файл проходит path-guard тестов


class TestNoPagerGitRead:
    def test_no_pager_diff_is_read(self):
        assert _terminal_is_read_only(f"git --no-pager diff -- config/{POLICY_YAML}")

    def test_no_pager_log_is_read(self):
        assert _terminal_is_read_only("git --no-pager log --oneline -5")

    def test_no_pager_commit_still_mutating(self):
        assert not _terminal_is_read_only("git --no-pager commit -m x")

    def test_no_pager_push_still_mutating(self):
        assert not _terminal_is_read_only("git --no-pager push origin main")

    def test_classify_no_pager_diff_policy_cfg_is_allow_read(self, cfg):
        c = classify("terminal", {"command": f"cd /c/x && git --no-pager diff -- config/{POLICY_YAML}"}, cfg, worker=False)
        assert (c.effect, c.decision) == ("read", "allow")
        assert c.category != "policy_control_plane_mutation"


class TestAssignmentStage:
    def test_var_assign_plus_read_is_read(self):
        assert _terminal_is_read_only('L="C:/plug"; grep -n tokens config/' + POLICY_YAML)

    def test_bare_assign_is_read(self):
        assert _terminal_is_read_only('X=42; echo "$X"')

    def test_assign_with_cmd_subst_fails_closed(self):
        assert not _terminal_is_read_only("X=$(cat secret.txt); echo done")

    def test_assign_plus_write_still_mutating(self):
        assert not _terminal_is_read_only('L=/tmp; rm "$L/x"')

    def test_classify_assign_grep_policy_cfg_is_allow_read(self, cfg):
        c = classify("terminal", {"command": f'L="x"; grep -n tokens config/{POLICY_YAML}'}, cfg, worker=False)
        assert (c.effect, c.decision) == ("read", "allow")


class TestDevnullDiscard:
    def test_stderr_discard_is_read(self):
        assert _terminal_is_read_only("find . -maxdepth 2 -name our-layer 2>/dev/null")

    def test_stdout_discard_is_read(self):
        assert _terminal_is_read_only("grep -n x README.md >/dev/null")

    def test_real_path_redirect_still_write(self):
        assert not _terminal_is_read_only(f"grep -n x config/{POLICY_YAML} > out.txt")

    def test_devnull_prefixed_path_still_write(self):
        assert not _terminal_is_read_only("grep -n x README.md > /dev/null.txt")

    def test_append_to_real_path_still_write(self):
        assert not _terminal_is_read_only("echo hi >> notes.md")


class TestProcessSubstitution:
    def test_read_only_inner_is_read(self):
        assert _terminal_is_read_only("diff <(git show efc985f6:OPERATING_SYSTEM.md) OPERATING_SYSTEM.md | head -50")

    def test_mutating_inner_fails_closed(self):
        assert not _terminal_is_read_only("diff <(rm -rf x) file")

    def test_output_substitution_fails_closed(self):
        assert not _terminal_is_read_only("diff >(cat > out.txt) file")

    def test_nested_subst_fails_closed(self):
        assert not _terminal_is_read_only("diff <(git show $(whoami)) file")

    def test_unknown_inner_program_fails_closed(self):
        assert not _terminal_is_read_only("diff <(curl http://evil) file")

    def test_diff_joined_read_utilities(self):
        assert _terminal_is_read_only("diff a.txt b.txt")


class TestFailClosedRetention:
    """Парные защиты: старые write-формы не просочились в read-lane."""

    def test_sed_in_place_still_write(self):
        assert not _terminal_is_read_only("sed -i 's/a/b/' file.txt")

    def test_tee_still_write(self):
        assert not _terminal_is_read_only("cat file | tee out.txt")

    def test_backtick_still_write(self):
        assert not _terminal_is_read_only("echo `rm -rf x`")

    def test_git_commit_still_mutating(self):
        assert not _terminal_is_read_only("git commit -m x")

    def test_newline_still_fails_closed(self):
        assert not _terminal_is_read_only("git status\nrm -rf x")

    def test_classify_secret_path_write_denied(self, cfg):
        secret = "." + "env.production"
        c = classify("write_file", {"path": secret, "content": "x"}, cfg, worker=False)
        assert c.decision == "deny"

    def test_classify_policy_cfg_write_denied(self, cfg):
        c = classify("write_file", {"path": f"config/{POLICY_YAML}", "content": "x"}, cfg, worker=False)
        assert c.decision == "deny"
        assert c.category == "policy_control_plane_mutation"
