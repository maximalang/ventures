"""v1.2.34: FP corpus from card t_d94dde9d (run-2125 live reproduction) and
TP controls proving no true positive weakened.

FP classes (each must NOT deny):
  1. board-DB / control-plane literals inside read-only probes (version-probe
     chains, sha256sum+cut probes of plugin files, sqlite read lane);
  2. python -c sqlite mode=ro SELECT probes and python-wrapped gh GET reads;
  2b. deny phrases QUOTED as data (echo/grep prose, git commit -m message,
      heredoc report lines);
  3. remote gh reads through python wrappers;
  4. git-tracked product source whose name contains the sec+ret token;
  5. bare tool version probes (python/py/node/npm/uv/git/sqlite3/gh).

TP controls (each must stay denied / gated):
  - python -c sqlite WITHOUT mode=ro, with mutation SQL, executescript/DROP,
    non-template statements, open()/os. usage; python -v REPL flag;
  - remote gh WRITES through python wrappers, shell=True forms;
  - approval-mutator names bare in a command or heredoc body, and inside
    bash -c / python -c / eval / awk / ssh executable spans;
  - real rm -rf, force-push, control-plane writes, secret reads;
  - foreign / unbound / self-attested gate heads stay fail-closed; the new
    64-hex sha256 anchor flow arms only on exact-prefix binding.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from fleet_policy.models import remediation_for
from fleet_policy.policy import classify

# guarded names assembled from parts (source-file scanner convention)
BOARD_DB = "C:/x/" + "kan" + "ban.db"
CFG_NAME = "fleet-" + "policy.yaml"
CFG_PATH = "config/" + CFG_NAME
SECRET_TOKEN = "sec" + "ret"
CREDENTIAL_TOKEN = "cre" + "dential"
RULE = SECRET_TOKEN + "_read_or_write"
CONTROL_PLANE_RULE = "policy_control_plane_mutation"


def _classify(command: str, config):
    return classify("terminal", {"command": command}, config, worker=True)


# ---------------------------------------------------------------------------
# FP class 5 + W2(a): bare version probes are reads
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("command", [
    "python --version",
    "python -V",
    "py --version",
    "python3.11 --version",
    "node --version",
    "node -v",
    "npm --version",
    "npm -v",
    "uv --version",
    "git --version",
    "sqlite3 --version",
    "gh --version",
    "jq --version",
    "python.exe --version",
    "python --version && git --version && node --version && gh --version"
    " && uv --version && sqlite3 --version && npm --version",
])
def test_fp5_version_probes_are_read_only(config, command):
    result = _classify(command, config)
    assert (result.effect, result.decision, result.category) == (
        "read", "allow", "read_only",
    ), (command, result)


@pytest.mark.parametrize("command", [
    "python -v",                        # verbose-import REPL, not a probe
    "python --version extra-arg",       # not a bare two-token stage
    "python --version && rm -rf C:/x/repo",
    "echo x | python",                  # bare REPL stage reading stdin
])
def test_tp5_version_probe_lane_stays_narrow(config, command):
    assert _classify(command, config).category != "read_only", command


# ---------------------------------------------------------------------------
# FP class 1: the live run-2125 reproduction and control-plane read probes
# ---------------------------------------------------------------------------

def test_fp1_live_repro_chain_is_read_only(config):
    # exact shape of the run-2125 denial: hash probes + section markers +
    # directory listing + version probe, chained around plugin sources
    command = (
        "cd C:/tmp/fp-probe && sha256sum src/fleet_policy/policy.py "
        "src/fleet_policy/runtime.py plugin.yaml | cut -c1-16; echo ===; ls; "
        "python --version"
    )
    result = _classify(command, config)
    assert (result.effect, result.decision, result.category) == (
        "read", "allow", "read_only",
    ), result


def test_fp1_policy_controlled_read_probes_allowed(config):
    for command in (
        f"sha256sum {CFG_PATH} | cut -c1-16",
        f"shasum -a 256 {CFG_PATH}",
        f'sqlite3 {BOARD_DB} "SELECT status FROM tasks"',
        f'grep -n "protected:" {CFG_PATH}; echo ===; head -5 {CFG_PATH}',
        f"wc -l {CFG_PATH} && stat {CFG_PATH} && python --version",
    ):
        result = _classify(command, config)
        assert (result.effect, result.decision) == ("read", "allow"), (command, result)
        assert result.category == "read_only", (command, result)


# ---------------------------------------------------------------------------
# FP class 2: python -c sqlite mode=ro probes (W2(b), supersedes the v1.2.31
# "stays denied" re-scope per the company decision of 02.10.2026)
# ---------------------------------------------------------------------------

def _sqlite_probe(db: str = BOARD_DB, sql: str = "SELECT id, title FROM tasks") -> str:
    return (
        "import sqlite3; "
        f"conn = sqlite3.connect('file:{db}?mode=ro', uri=True); "
        f"rows = conn.execute('{sql}').fetchall(); "
        "print(rows); conn.close()"
    )


def test_fp2_python_sqlite_mode_ro_select_is_read(config):
    result = _classify(f'python -c "{_sqlite_probe()}"', config)
    assert (result.effect, result.decision, result.category) == (
        "read", "allow", "read_only",
    ), result


def test_fp2_python_sqlite_print_wrapped_and_cte_forms(config):
    for code in (
        "import sqlite3; conn = sqlite3.connect('file:" + BOARD_DB
        + "?mode=ro', uri=True); print(conn.execute('SELECT COUNT(*) FROM tasks').fetchall()); conn.close()",
        "import sqlite3; conn = sqlite3.connect('file:" + BOARD_DB
        + "?mode=ro', uri=True); rows = conn.execute('WITH t AS (SELECT 1 AS x) SELECT x FROM t').fetchall(); print(rows); conn.close()",
        "import sqlite3; conn = sqlite3.connect('file:C:/x/app.db?mode=ro', uri=True); rows = conn.execute('PRAGMA table_info(tasks)').fetchall(); print(rows); conn.close()",
    ):
        result = _classify(f'python -c "{code}"', config)
        assert (result.effect, result.decision, result.category) == (
            "read", "allow", "read_only",
        ), (code, result)


@pytest.mark.parametrize("code", [
    # no mode=ro in the file: URI
    "import sqlite3; conn = sqlite3.connect('file:" + BOARD_DB
    + "', uri=True); rows = conn.execute('SELECT 1').fetchall(); print(rows); conn.close()",
    # plain path, no file: URI (the test_policy v1.2.11 shape)
    "import sqlite3; sqlite3.connect('" + BOARD_DB + "')",
    # bare connect expression, no assignment (the v1.2.23 adversary shape)
    "import sqlite3; sqlite3.connect('file:" + BOARD_DB + "?mode=ro', uri=True)",
    # mutation SQL literal
    "import sqlite3; conn = sqlite3.connect('file:C:/x/app.db?mode=ro', uri=True); conn.execute('DELETE FROM tasks'); conn.close()",
    # executescript / DROP
    "import sqlite3; conn = sqlite3.connect('file:C:/x/app.db?mode=ro', uri=True); conn.executescript('DROP TABLE tasks'); conn.close()",
    # spliced statements
    "import sqlite3; conn = sqlite3.connect('file:" + BOARD_DB
    + "?mode=ro', uri=True); rows = conn.execute('SELECT 1; DELETE FROM tasks').fetchall(); print(rows)",
    # non-template statement (os import + usage)
    "import sqlite3; conn = sqlite3.connect('file:C:/x/app.db?mode=ro', uri=True); import os; print(os.listdir('.')); conn.close()",
    # filesystem write
    "import sqlite3; conn = sqlite3.connect('file:C:/x/app.db?mode=ro', uri=True); f = open('x', 'w'); conn.close()",
    # non-literal execute argument
    "import sqlite3; conn = sqlite3.connect('file:C:/x/app.db?mode=ro', uri=True); sql = 'SELECT 1'; rows = conn.execute(sql).fetchall(); print(rows)",
    # shell escape
    "import sqlite3; conn = sqlite3.connect('file:C:/x/app.db?mode=ro', uri=True); import subprocess; print(subprocess.run(['rm'])); conn.close()",
])
def test_tp2_python_sqlite_negatives_never_read(config, code):
    result = _classify(f'python -c "{code}"', config)
    assert result.category != "read_only", (code, result)


def test_tp2_python_c_shape_negatives_never_read(config):
    for command in (
        'python -c "print(1)" extra-arg',      # extra argument
        "python -c print(1)",                  # unquoted code
        'python -m timeit "print(1)"',         # not -c
        'python -c ""',                        # empty code
        'node -c "print(1)"',                  # not python
    ):
        assert _classify(command, config).category != "read_only", command


def test_tp2_board_db_probe_without_ro_stays_denied(config):
    # policy-controlled store, no mode=ro: the control-plane deny stands
    code = (
        "import sqlite3; conn = sqlite3.connect('file:" + BOARD_DB
        + "', uri=True); rows = conn.execute('SELECT 1').fetchall(); print(rows); conn.close()"
    )
    result = _classify(f'python -c "{code}"', config)
    assert (result.decision, result.category) == ("deny", CONTROL_PLANE_RULE), result


# ---------------------------------------------------------------------------
# FP class 3: remote gh reads through python wrappers; TP: gh writes
# ---------------------------------------------------------------------------

def test_fp3_python_wrapped_gh_reads_are_read_only(config):
    for code in (
        "import subprocess; result = subprocess.run(['gh', 'api', 'repos/maximalang/ventures/pulls/51'], capture_output=True, text=True, timeout=60); print(result.stdout)",
        "import subprocess, json; result = subprocess.run(['gh', 'pr', 'view', '51', '--repo', 'maximalang/ventures'], capture_output=True, text=True); data = json.loads(result.stdout); print(data)",
        "import subprocess; result = subprocess.run(['gh', 'api', 'repos/maximalang/ventures/git/ref/heads/codex/company-os', '--jq', '.object.sha'], capture_output=True, text=True); print(result.stdout)",
        "import subprocess; result = subprocess.run(['gh', 'pr', 'checks', '51', '--repo', 'maximalang/ventures'], capture_output=True, text=True); print(result.stdout)",
    ):
        result = _classify(f'python -c "{code}"', config)
        assert (result.effect, result.decision, result.category) == (
            "read", "allow", "read_only",
        ), (code, result)


@pytest.mark.parametrize("code", [
    # POST through the api verb
    "import subprocess; result = subprocess.run(['gh', 'api', '--method', 'POST', 'repos/o/r/issues', '-f', 'title=x'], capture_output=True, text=True); print(result.stdout)",
    # merge verb
    "import subprocess; result = subprocess.run(['gh', 'pr', 'merge', '51'], capture_output=True, text=True); print(result.stdout)",
    # shell=True string form — the shell=... literal below is TEST DATA for
    # the deny control (never executed); the helper in this module uses the
    # safe list form.
    "import subprocess; result = subprocess.run('gh api repos/o/r', shell=True, capture_output=True, text=True); print(result.stdout)",
    # os.popen form
    "import os; result = os.popen('gh api repos/o/r'); print(result.read())",
    # stdin piping
    "import subprocess; result = subprocess.run(['gh', 'api', 'repos/o/r'], input=b'x', capture_output=True, text=True); print(result.stdout)",
])
def test_tp3_python_wrapped_gh_writes_never_read(config, code):
    result = _classify(f'python -c "{code}"', config)
    assert result.category != "read_only", (code, result)


# ---------------------------------------------------------------------------
# FP class 2b + W4: quoted deny phrases are data; executable spans stay code
# ---------------------------------------------------------------------------

def test_fp2b_quoted_deny_phrases_are_data(config):
    read_cases = [
        'echo "decide_approval is a store function"',
        'grep -rn "consume_exact_approval" src/',
        'grep -rn "fleet-policy approve" docs/',
        'git log --grep="delete" --oneline',
        "cat <<'EOF'\nNote: \"force-push to main\" is prohibited.\nEOF",
    ]
    for command in read_cases[:-1]:
        result = _classify(command, config)
        assert (result.effect, result.decision, result.category) == (
            "read", "allow", "read_only",
        ), (command, result)
    # heredoc prose: state_change (newline), but no evidence-gated category
    result = _classify(read_cases[-1], config)
    assert result.decision == "allow", result
    assert result.category == "scoped_state_change", result


def test_fp2b_commit_message_prose_not_gated(config):
    result = _classify('git commit -m "cleanup: remove stale cache handling"', config)
    assert (result.decision, result.category) == ("allow", "repository_change"), result


def test_tp2b_executable_spans_stay_scanned(config):
    deny_cases = [
        ("bash -c \"store.decide_approval('rule', True, 'worker')\"",
         "worker_self_approval"),
        ("python -c \"store.decide_approval('rule', True, 'worker')\"",
         "worker_self_approval"),
        ("python - <<'EOF'\nstore.decide_approval('rule', True, 'worker')\nEOF",
         "worker_self_approval"),
        ("awk 'BEGIN{system(\"decide_approval\")}'", "worker_self_approval"),
        ("eval \"consume_exact_approval\"", "worker_self_approval"),
        ("sh -c 'mark_expected_failure t s r'", "worker_self_approval"),
    ]
    for command, expected in deny_cases:
        result = _classify(command, config)
        assert (result.decision, result.category) == ("deny", expected), (command, result)
    # NOTE: the rule-table rm pattern requires a whitespace/start boundary
    # before rm, so QUOTED `rm -rf` payloads never matched it even on
    # v1.2.31 (pre-existing lexical shape, unchanged by W4 — the span here
    # stays unmasked because eval is an executor). The controls below use
    # the bare forms the pattern actually gates.
    gated_cases = [
        "eval rm -rf /tmp/probe-target",
        "ssh remote-host rm -rf /srv/app/releases",
    ]
    for command in gated_cases:
        result = _classify(command, config)
        assert result.decision == "approval_required", (command, result)
        assert result.category == "irreversible_data_loss", (command, result)


def test_tp2b_unbalanced_quoting_fails_closed(config):
    # a stray apostrophe must not exempt the trailing deny phrase
    command = "echo don't && decide_approval"
    result = _classify(command, config)
    assert result.decision == "deny", result
    assert result.category == "worker_self_approval", result


# ---------------------------------------------------------------------------
# FP class 4 + W1: tracked sec-token product source
# ---------------------------------------------------------------------------

def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=str(repo), check=True, capture_output=True)


@pytest.fixture()
def product_repo(tmp_path: Path) -> Path:
    root = tmp_path / "product"
    (root / "agent").mkdir(parents=True)
    (root / "agent" / f"{SECRET_TOKEN}_scope.py").write_text(
        "SCOPE = 1\n", encoding="utf-8"
    )
    (root / "agent" / f"{CREDENTIAL_TOKEN}_pool.py").write_text(
        "class Pool:\n    pass\n", encoding="utf-8"
    )
    # matched but NOT committed -> stays denied
    (root / "agent" / f"{SECRET_TOKEN}_scratch.py").write_text("x = 1\n", encoding="utf-8")
    # hard secret store, deliberately tracked -> stays denied
    (root / ".env.production").write_text("A=B\n", encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "fixture@example.com")
    _git(root, "config", "user.name", "fixture")
    _git(root, "add",
         f"agent/{SECRET_TOKEN}_scope.py",
         f"agent/{CREDENTIAL_TOKEN}_pool.py",
         ".env.production")
    _git(root, "commit", "-q", "-m", "fixture")
    return root


def test_fp4_tracked_secret_named_source_reads_allowed(product_repo, config):
    target = product_repo / "agent" / f"{SECRET_TOKEN}_scope.py"
    result = classify("read_file", {"path": str(target)}, config, worker=True)
    assert (result.effect, result.decision) == ("read", "allow"), result
    assert result.category != RULE
    terminal = _classify(f"grep -n SCOPE {target}", config)
    assert (terminal.decision, terminal.category) == ("allow", "read_only"), terminal


def test_fp4_relative_paths_resolve_via_workdir_and_cwd(product_repo, config, monkeypatch):
    rel = f"agent/{SECRET_TOKEN}_scope.py"
    with_workdir = classify(
        "read_file", {"path": rel, "workdir": str(product_repo)}, config, worker=True
    )
    assert (with_workdir.effect, with_workdir.decision) == ("read", "allow"), with_workdir
    monkeypatch.chdir(product_repo)
    via_cwd = classify("read_file", {"path": rel}, config, worker=True)
    assert (via_cwd.effect, via_cwd.decision) == ("read", "allow"), via_cwd


def test_tp4_negative_controls_stay_denied(product_repo, config):
    for name in (f"agent/{SECRET_TOKEN}_scratch.py", ".env.production"):
        result = classify("read_file", {"path": str(product_repo / name)}, config, worker=True)
        assert (result.decision, result.category) == ("deny", RULE), (name, result)
    ghost = classify(
        "read_file", {"path": str(product_repo / "agent" / f"ghost_{SECRET_TOKEN}.py")},
        config, worker=True,
    )
    assert (ghost.decision, ghost.category) == ("deny", RULE), ghost


# ---------------------------------------------------------------------------
# TP baseline: real mutations, secret reads, control-plane writes
# ---------------------------------------------------------------------------

def test_tp_control_plane_writes_still_denied(config):
    for tool, args in (
        ("write_file", {"path": CFG_PATH, "content": "x"}),
        ("patch", {"path": CFG_PATH, "old_string": "a", "new_string": "b"}),
        ("terminal", {"command": f"sed -i 's/a/b/' {CFG_PATH}"}),
        ("terminal", {"command": f"git add {CFG_PATH} && git status"}),
    ):
        result = classify(tool, args, config, worker=True)
        assert (result.decision, result.category) == (
            "deny", CONTROL_PLANE_RULE,
        ), (tool, args, result)


def test_tp_secret_reads_still_denied(config):
    for command in ("cat .env.production", "head -20 auth.json", "cat secrets.txt"):
        result = _classify(command, config)
        assert result.decision == "deny", (command, result)
        assert result.category == RULE, (command, result)


def test_tp_real_destructive_forms_still_gated(config):
    rm = _classify("rm -rf C:/Users/max/Desktop/all/ventures", config)
    assert rm.decision == "approval_required", rm
    assert rm.category == "irreversible_data_loss", rm
    force = _classify("git push --force origin main", config)
    assert force.decision == "approval_required", force
    assert force.category == "irreversible_data_loss", force
    push = _classify("git push origin main", config)
    assert (push.decision, push.category) == ("allow", "release_to_protected_branch"), push


def test_tp_approval_mutators_still_denied(config):
    for command in (
        "fleet-policy approve rule-key",
        "decide_approval",
        "mark_expected_failure t_test sig r1",
    ):
        result = _classify(command, config)
        assert result.decision == "deny", (command, result)
        assert result.category == "worker_self_approval", (command, result)


# ---------------------------------------------------------------------------
# W2(c): honest remediation route on control-plane denies
# ---------------------------------------------------------------------------

def test_w2c_control_plane_remediation_documents_read_access():
    route = remediation_for(CONTROL_PLANE_RULE)
    assert route is not None
    assert route["who"] == "company"
    assert "read_file" in route["how"]
    assert "sqlite3 -readonly" in route["how"]


# ---------------------------------------------------------------------------
# W3: 64-hex sha256 head binding (verbal decisions / artifact flows)
# ---------------------------------------------------------------------------

_H64 = "b" * 64
_H64_FOREIGN = "c" * 64
_H40 = "a" * 40


def _ctx(records, assignee="tech"):
    return {
        "task_body": "task_type: ops",
        "assignee": assignee,
        "comment_records": records,
    }


def _go_and_gate(gate_head, *, go_head=_H64, gate="ci", gate_author="qa", task_type="ops"):
    return [
        {"author": "company", "body": f"decision:company=go\nhead={go_head} task_type: {task_type}"},
        {"author": gate_author, "body": f"gate:{gate}=pass\nhead={gate_head} task_type: {task_type}"},
    ]


def test_w3_sha256_anchor_arms_gate_on_exact_head(runtime):
    missing = runtime.missing_gates("deploy_external_runtime", _ctx(_go_and_gate(_H64)))
    assert "ci" not in missing
    assert "backup" in missing and "rollback" in missing


def test_w3_prefix_binding_of_sha256_anchor_arms(runtime):
    missing = runtime.missing_gates("deploy_external_runtime", _ctx(_go_and_gate(_H64[:40])))
    assert "ci" not in missing


def test_w3_foreign_and_unbound_heads_fail_closed(runtime):
    foreign = runtime.missing_gates(
        "deploy_external_runtime", _ctx(_go_and_gate(_H64_FOREIGN))
    )
    assert "ci" in foreign
    unbound = runtime.missing_gates("deploy_external_runtime", _ctx([
        {"author": "company", "body": f"decision:company=go\nhead={_H64} task_type: ops"},
        {"author": "qa", "body": "gate:ci=pass\ntask_type: ops"},
    ]))
    assert "ci" in unbound


def test_w3_40_hex_git_flow_unchanged(runtime):
    armed = runtime.missing_gates(
        "deploy_external_runtime", _ctx(_go_and_gate(_H40, go_head=_H40))
    )
    assert "ci" not in armed
    foreign = runtime.missing_gates(
        "deploy_external_runtime", _ctx(_go_and_gate("f" * 40, go_head=_H40))
    )
    assert "ci" in foreign


def test_w3_self_attestation_still_fails_closed(runtime):
    # public_product_action requires review+qa; the card's own assignee
    # cannot attest review even with a perfect 64-hex binding
    missing = runtime.missing_gates("public_product_action", _ctx(
        _go_and_gate(_H64, gate="review", gate_author="qa", task_type="review"),
        assignee="qa",
    ))
    assert "review" in missing
