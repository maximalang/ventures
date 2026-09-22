import importlib.util
import json
import pathlib
import tempfile
import unittest

MODULE_PATH = pathlib.Path(__file__).parents[1] / "scripts" / "blocked_state_controller.py"
spec = importlib.util.spec_from_file_location("blocked_state_controller", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
import sys
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def show(reason="", *, comments=None, parents=None, event_kind="blocked"):
    return {
        "parents": parents or [],
        "comments": comments or [],
        "events": [{
            "kind": event_kind,
            "created_at": 100,
            "payload": {"reason": reason},
        }] if reason else [],
    }


def task(**overrides):
    value = {
        "id": "t_x",
        "title": "Example",
        "body": "task_type: ops\nDo work",
        "assignee": "operations",
        "status": "blocked",
        "priority": 5,
        "block_kind": "needs_input",
        "created_at": 10,
    }
    value.update(overrides)
    return value


class ClassificationTests(unittest.TestCase):
    def test_safety_deny_is_never_auto_applied(self):
        d = mod.classify(task(), show("FLEET POLICY BLOCKED [secret_read_or_write]"))
        self.assertEqual((d.classification, d.action, d.safe_to_apply), ("safety", "hold", False))

    def test_owner_boundary_is_escalated(self):
        t = task(body="task_type: ops\nStop for phone or KYC", block_kind="capability")
        d = mod.classify(t, show("owner capability required"))
        self.assertEqual((d.classification, d.owner, d.action), ("owner_only", "owner", "escalate"))

    def test_malformed_work_marker_routes_repair(self):
        d = mod.classify(task(body="No marker"), show("FLEET POLICY BLOCKED [missing_or_unknown_task_type]"))
        self.assertEqual((d.classification, d.action), ("malformed_card", "route_repair"))

    def test_completed_evidence_routes_administrative_review(self):
        s = show("FLEET POLICY BLOCKED [policy_control_plane_mutation]", comments=[
            {"author": "qa", "body": "Exact head verified; PASS"}
        ])
        d = mod.classify(task(), s)
        self.assertEqual((d.classification, d.action), ("completed_artifact", "route_review"))

    def test_open_dependency_waits(self):
        d = mod.classify(task(), show("temporary", parents=["t_parent"]), lambda _p: "running")
        self.assertEqual((d.classification, d.action), ("dependency", "wait"))

    def test_transient_is_bounded_unblock(self):
        d = mod.classify(task(block_kind="transient"), show("network timeout"))
        self.assertEqual((d.classification, d.action, d.safe_to_apply), ("transient", "unblock", True))

    def test_company_resume_is_bounded_unblock(self):
        s = show("generic", comments=[{"author": "company", "body": "decision:company=go"}])
        d = mod.classify(task(), s)
        self.assertEqual((d.classification, d.action, d.safe_to_apply), ("approved_resume", "unblock", True))

    def test_company_resume_on_triage_routes_review(self):
        s = show("generic", comments=[{"author": "company", "body": "decision:company=go"}])
        d = mod.classify(task(status="triage"), s)
        self.assertEqual((d.classification, d.action, d.safe_to_apply), ("triage_resume", "route_review", False))

    def test_russian_owner_boundary_is_escalated(self):
        t = task(body="task_type: ops\nStop on телефон or KYC", block_kind=None)
        d = mod.classify(t, show("missing_or_unknown_task_type"))
        self.assertEqual((d.classification, d.action), ("owner_only", "escalate"))

    def test_proven_read_false_positive_is_unblocked(self):
        d = mod.classify(task(), show("policy_control_plane_mutation command=read_file"))
        self.assertEqual((d.classification, d.action, d.safe_to_apply), ("proven_false_positive", "unblock", True))

    def test_ambiguous_control_plane_deny_routes_review(self):
        d = mod.classify(task(), show("policy_control_plane_mutation"))
        self.assertEqual((d.classification, d.action), ("policy_review", "route_review"))

    def test_loop_changes_method_instead_of_retry(self):
        d = mod.classify(task(), show("same_failure_loop"))
        self.assertEqual((d.classification, d.action, d.safe_to_apply), ("method_loop", "route_repair", False))


class DiscoveryTests(unittest.TestCase):
    def test_discovers_every_board_directory(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            for name in ("fleet-ops", "rr-team", "video", "freelance", "venture-lab"):
                d = root / name
                d.mkdir()
                (d / "kanban.db").write_bytes(b"")
            (root / "not-a-board").mkdir()
            self.assertEqual(
                mod.discover_boards(root),
                ["fleet-ops", "freelance", "rr-team", "venture-lab", "video"],
            )


class ApplyTests(unittest.TestCase):
    def test_unblock_requires_readback_and_records_cooldown(self):
        calls = []
        statuses = {"t_x": "blocked"}
        def fake_cli(board, args, timeout):
            calls.append((board, args))
            if args[0] == "unblock":
                statuses[args[1]] = "ready"
                return {"ok": True}
            if args[0] == "show":
                return {"task": {"id": args[1], "status": statuses[args[1]]}}
            raise AssertionError(args)
        with tempfile.TemporaryDirectory() as td:
            state = pathlib.Path(td) / "state.json"
            c = mod.Controller(apply=True, state_path=state, cli=fake_cli)
            cand = mod.Candidate("rr-team", task(), show("network timeout"), mod.Decision(
                "transient", "operations", "unblock", "typed transient", True
            ), 50)
            result = c.apply_candidate(cand)
            self.assertEqual(result["outcome"], "unblocked")
            self.assertEqual(result["after"], "ready")
            self.assertEqual(calls[0][0], "rr-team")
            c.state["last_run_at"] = c.now
            mod.atomic_json_write(state, c.state)
            persisted = json.loads(state.read_text(encoding="utf-8"))
            self.assertTrue(persisted["acted"])

    def test_action_limit_defers_without_mutation(self):
        def forbidden(*_args):
            raise AssertionError("CLI mutation must not run")
        c = mod.Controller(apply=True, action_limit=0, cli=forbidden)
        cand = mod.Candidate("fleet-ops", task(), show(), mod.Decision(
            "transient", "operations", "unblock", "typed transient", True
        ), 50)
        self.assertEqual(c.apply_candidate(cand)["reason"], "action_limit")

    def test_dry_run_never_calls_mutation(self):
        c = mod.Controller(apply=False, cli=lambda *_args: (_ for _ in ()).throw(AssertionError()))
        cand = mod.Candidate("fleet-ops", task(), show(), mod.Decision(
            "malformed_card", "company", "route_repair", "missing"
        ), 50)
        self.assertEqual(c.apply_candidate(cand), {"outcome": "dry_run", "proposed": "route_repair"})


class RecursionGuardTests(unittest.TestCase):
    def test_recovery_card_title_is_never_re_recovered(self):
        t = task(id="t_nested", title="Recover t_x: whatever")
        d = mod.classify(t, show("FLEET POLICY BLOCKED [same_failure_loop]"))
        self.assertEqual((d.classification, d.action, d.safe_to_apply), ("nested_recovery", "hold", False))

    def test_recursion_guard_not_bypassed_by_company_resume_v3(self):
        # P3 depth=0: even a company resume must not re-recover a recovery card.
        t = task(id="t_nested", title="Recover t_x: whatever")
        s = show("generic", comments=[{"author": "company", "body": "decision:company=go"}])
        d = mod.classify(t, s)
        self.assertEqual((d.classification, d.action, d.safe_to_apply), ("nested_recovery", "hold", False))


class PositionalTitleTests(unittest.TestCase):
    def test_create_uses_positional_title_before_flags(self):
        calls = []
        def fake_cli(board, args, timeout):
            calls.append((board, args))
            if args[0] == "list":
                return []  # no open recovery children
            if args[0] == "show":
                return {"task": {"id": args[1], "status": "blocked"}}  # live status
            return {"id": "t_new"}
        c = mod.Controller(apply=True, state_path=pathlib.Path(tempfile.mkdtemp()) / "s.json", cli=fake_cli)
        cand = mod.Candidate("fleet-ops", task(), show(), mod.Decision(
            "malformed_card", "company", "route_repair", "missing marker", True
        ), 50)
        result = c.apply_candidate(cand)
        self.assertEqual(result["outcome"], "routed")
        create_calls = [a for (_b, a) in calls if a[0] == "create"]
        self.assertTrue(create_calls, "expected a create CLI call")
        args = create_calls[0]
        self.assertEqual(args[1], "Recover t_x: Example")  # positional, no --title
        self.assertNotIn("--title", args)


class EnvHygieneTests(unittest.TestCase):
    def test_scrubbed_env_drops_delegation_and_board_vars(self):
        base = {"PATH": r"C:\\Windows", "LANG": "C"}
        dirty = dict(base)
        dirty.update({
            "HERMES_DELEGATED_CHILD_CONTEXT": "1",
            "HERMES_KANBAN_DB": "C:/elsewhere/kanban.db",
            "HERMES_KANBAN_BOARD": "other",
        })
        env = mod._scrubbed_env(base)
        self.assertIn("PATH", env)
        for key in ("HERMES_DELEGATED_CHILD_CONTEXT", "HERMES_KANBAN_DB", "HERMES_KANBAN_BOARD"):
            self.assertNotIn(key, env)

    def test_run_cli_strips_inherited_env(self):
        import os as _os
        _os.environ["HERMES_KANBAN_DB"] = "C:/pinned.db"
        try:
            c = mod.Controller(apply=False, cli=mod.run_cli)
            seen = {}
            real_run = __import__("subprocess").run
            def spy_run(cmd, **kwargs):
                seen.update(kwargs.get("env") or {})
                raise RuntimeError("stop")
            mod.subprocess.run = spy_run
            try:
                with self.assertRaises(RuntimeError):
                    c.cli("fleet-ops", ["list"], 5)
            finally:
                mod.subprocess.run = real_run
            self.assertNotIn("HERMES_KANBAN_DB", seen)
            self.assertIn("PATH", seen)
        finally:
            del _os.environ["HERMES_KANBAN_DB"]

    def test_run_cli_retries_windows_spawn_flake_then_succeeds(self):
        attempts = []
        real_run = mod.subprocess.run
        def flaky_run(cmd, **kwargs):
            attempts.append(cmd)
            if len(attempts) < 3:
                raise OSError(3221225794, "GetExitCodeProcess")
            class P:  # minimal CompletedProcess stand-in
                returncode = 0
                stdout = "[]"
                stderr = ""
            return P()
        mod.subprocess.run = flaky_run
        try:
            value = mod.run_cli("fleet-ops", ["list"], 5)
            self.assertEqual(value, [])
            self.assertEqual(len(attempts), 3)
        finally:
            mod.subprocess.run = real_run

    def test_run_cli_exhausts_retries(self):
        real_run = mod.subprocess.run
        def always_flaky(cmd, **kwargs):
            raise OSError(3221225794, "GetExitCodeProcess")
        mod.subprocess.run = always_flaky
        try:
            with self.assertRaises(RuntimeError):
                mod.run_cli("fleet-ops", ["list"], 5)
        finally:
            mod.subprocess.run = real_run

    def test_run_spawns_with_scrubbed_env(self):
        c = mod.Controller(apply=False, cli=mod.run_cli)
        seen = {}
        real_run = mod.subprocess.run
        def spy_run(cmd, **kwargs):
            seen.update(kwargs.get("env") or {})
            raise RuntimeError("stop")
        mod.subprocess.run = spy_run
        try:
            with self.assertRaises(RuntimeError):
                c.run(["fleet-ops"])
        finally:
            mod.subprocess.run = real_run
        self.assertIn("PATH", seen)
        self.assertNotIn("HERMES_DELEGATED_CHILD_CONTEXT", seen)


class StalenessGateTests(unittest.TestCase):
    def test_fresh_block_routes_recovery(self):
        d = mod.classify(task(), show("FLEET POLICY BLOCKED [evidence_gate_missing]"), None, now=100)
        self.assertEqual((d.classification, d.action, d.safe_to_apply), ("evidence_gap", "route_evidence", False))

    def test_stale_block_suggests_archive_review_not_recovery(self):
        now = 100 + int(mod.STALE_BLOCK_DAYS * 86400) + 3600
        d = mod.classify(task(), show("FLEET POLICY BLOCKED [evidence_gate_missing]"), None, now=now, stale_after_days=7.0)
        self.assertEqual((d.classification, d.action), ("stale_archive_review", "route_archive_review"))

    def test_staleness_uses_blocked_at_not_created_at(self):
        now = 100 + int(mod.STALE_BLOCK_DAYS * 86400) + 3600
        s = show("FLEET POLICY BLOCKED [evidence_gate_missing]")
        s["events"][0]["created_at"] = now - 60  # blocked recently
        d = mod.classify(task(), s, None, now=now, stale_after_days=7.0)
        self.assertEqual((d.classification, d.action), ("evidence_gap", "route_evidence"))

    def test_staleness_disabled_by_default_in_classify(self):
        d = mod.classify(task(), show("FLEET POLICY BLOCKED [evidence_gate_missing]"))
        self.assertEqual((d.classification, d.action), ("evidence_gap", "route_evidence"))

    def test_stale_archive_review_is_dry_run_only(self):
        c = mod.Controller(apply=True, state_path=pathlib.Path(tempfile.mkdtemp()) / "s.json",
                           cli=lambda *_a: (_ for _ in ()).throw(AssertionError("no CLI mutation")))
        now = int(mod._now_epoch()) + int(mod.STALE_BLOCK_DAYS * 86400)
        cand = mod.Candidate("fleet-ops", task(), show(), mod.Decision(
            "stale_archive_review", "company", "route_archive_review", "stale", False
        ), now)
        result = c.apply_candidate(cand)
        self.assertEqual(result, {"outcome": "dry_run", "proposed": "route_archive_review"})


class HeartbeatStallTests(unittest.TestCase):
    def test_detects_stalled_worker(self):
        now = int(mod._now_epoch())
        s = show("network timeout")
        s["events"].append({"kind": "heartbeat", "created_at": now - 8000})
        self.assertTrue(mod.detect_heartbeat_stall(task(), s, now=now))

    def test_alive_worker_not_stalled(self):
        now = int(mod._now_epoch())
        s = show("network timeout")
        s["events"].append({"kind": "heartbeat", "created_at": now - 60})
        self.assertFalse(mod.detect_heartbeat_stall(task(), s, now=now))

    def test_running_worker_is_out_of_scope(self):
        now = int(mod._now_epoch())
        s = show("network timeout")
        s["events"].append({"kind": "heartbeat", "created_at": now - 3600})
        self.assertFalse(mod.detect_heartbeat_stall(task(status="running"), s, now=now))

    def test_no_heartbeat_events_is_not_stall(self):
        now = int(mod._now_epoch())
        self.assertFalse(mod.detect_heartbeat_stall(task(), show("network timeout"), now=now))

    def test_stalled_worker_classifies_as_bounded_unblock(self):
        now = int(mod._now_epoch())
        s = show("network timeout")
        s["events"].append({"kind": "heartbeat", "created_at": now - 8000})
        d = mod.classify(task(), s, None, now=now)
        self.assertEqual((d.classification, d.action, d.safe_to_apply), ("heartbeat_stall", "unblock", True))


# ---------------------------------------------------------------------------
# P3 / RC4 additions: trust boundary, depth=0, word-boundary, dedup, cascade.
# ---------------------------------------------------------------------------

class TrustBoundaryTests(unittest.TestCase):
    def test_worker_authored_resume_is_ignored(self):
        # Spoofed worker resume must NOT unblock.
        s = show("generic", comments=[{"author": "worker", "body": "resume: please"}])
        d = mod.classify(task(), s)
        self.assertNotEqual(d.action, "unblock")
        self.assertFalse(d.safe_to_apply)

    def test_worker_authored_decision_go_is_ignored(self):
        s = show("generic", comments=[{"author": "worker", "body": "decision:company=go"}])
        d = mod.classify(task(), s)
        self.assertNotEqual(d.classification, "approved_resume")

    def test_company_authored_resume_still_accepted(self):
        s = show("generic", comments=[{"author": "company", "body": "resume: proceed"}])
        d = mod.classify(task(), s)
        self.assertEqual((d.classification, d.action, d.safe_to_apply), ("approved_resume", "unblock", True))


class DepthZeroTests(unittest.TestCase):
    def test_recovery_card_never_recovered_even_with_company_resume(self):
        # Recover(Recover(...)) forbidden unconditionally (depth=0).
        t = task(id="t_rec", title="Recover t_x: thing")
        s = show("generic", comments=[{"author": "company", "body": "decision:company=go"}])
        d = mod.classify(t, s)
        self.assertEqual((d.classification, d.action, d.safe_to_apply), ("nested_recovery", "hold", False))

    def test_safety_block_kind_never_resumed(self):
        t = task(block_kind="safety")
        s = show("generic", comments=[{"author": "company", "body": "resume: go"}])
        d = mod.classify(t, s)
        self.assertEqual((d.classification, d.action, d.safe_to_apply), ("depth_zero_hold", "hold", False))

    def test_worker_code_execution_block_kind_never_resumed(self):
        t = task(block_kind="worker_code_execution")
        s = show("generic", comments=[{"author": "company", "body": "resume: go"}])
        d = mod.classify(t, s)
        self.assertEqual((d.classification, d.action, d.safe_to_apply), ("depth_zero_hold", "hold", False))


class WordBoundaryTests(unittest.TestCase):
    def test_passport_does_not_count_as_completion(self):
        s = show("some block", comments=[{"author": "qa", "body": "checked passport control"}])
        d = mod.classify(task(body="task_type: ops\nreview the passport page"), s)
        self.assertNotEqual(d.classification, "completed_artifact")

    def test_unverified_does_not_count_as_completion(self):
        s = show("some block", comments=[{"author": "qa", "body": "still unverified"}])
        d = mod.classify(task(), s)
        self.assertNotEqual(d.classification, "completed_artifact")

    def test_bypass_does_not_count_as_completion(self):
        s = show("some block", comments=[{"author": "qa", "body": "add a bypass"}])
        d = mod.classify(task(), s)
        self.assertNotEqual(d.classification, "completed_artifact")

    def test_exact_head_phrase_still_counts(self):
        s = show("some block", comments=[{"author": "qa", "body": "exact head verified; PASS"}])
        d = mod.classify(task(), s)
        self.assertEqual(d.classification, "completed_artifact")

    def test_owner_term_substring_does_not_trigger(self):
        # 'владение' as substring inside a longer word must not escalate.
        t = task(body="task_type: ops\nобновить привладение данных", block_kind="needs_input")
        d = mod.classify(t, show("some reason"))
        self.assertNotEqual(d.classification, "owner_only")


class RecoveryDedupTests(unittest.TestCase):
    def _mk_controller(self, fake_cli):
        return mod.Controller(apply=True, state_path=pathlib.Path(tempfile.mkdtemp()) / "s.json", cli=fake_cli)

    def test_idempotency_key_excludes_classification(self):
        captured = {}
        def fake_cli(board, args, timeout):
            captured["args"] = args
            return {"id": "t_new"}
        c = self._mk_controller(fake_cli)
        cand = mod.Candidate("fleet-ops", task(), show(), mod.Decision(
            "malformed_card", "company", "route_repair", "m", True), 50)
        c._route_task(cand)
        key = captured["args"][captured["args"].index("--idempotency-key") + 1]
        self.assertEqual(key, "blocked-recovery:fleet-ops:t_x")
        self.assertNotIn("malformed_card", key)

    def test_open_recovery_child_blocks_second(self):
        existing = {"id": "t_r1", "title": "Recover t_x: prior", "status": "todo"}
        def fake_cli(board, args, timeout):
            if args[0] == "list":
                status = args[args.index("--status") + 1]
                return [existing] if status == "todo" else []
            if args[0] == "show":
                return {"task": {"id": args[1], "status": "blocked"}}
            raise AssertionError(args)
        c = self._mk_controller(fake_cli)
        cand = mod.Candidate("fleet-ops", task(), show(), mod.Decision(
            "malformed_card", "company", "route_repair", "m", True), 50)
        out = c._route_task(cand)
        self.assertEqual(out["outcome"], "skipped")
        self.assertEqual(out["reason"], "open recovery child exists")

    def test_terminal_original_skips_recovery(self):
        def fake_cli(board, args, timeout):
            if args[0] == "list":
                return []
            if args[0] == "show":
                return {"task": {"id": args[1], "status": "done"}}
            raise AssertionError(args)
        c = self._mk_controller(fake_cli)
        cand = mod.Candidate("fleet-ops", task(), show(), mod.Decision(
            "malformed_card", "company", "route_repair", "m", True), 50)
        out = c._route_task(cand)
        self.assertEqual(out["outcome"], "skipped")
        self.assertIn("terminal", out["reason"])


class CascadeDispositionTests(unittest.TestCase):
    def test_terminal_root_disposes_open_descendants(self):
        root = {"id": "t_root", "status": "archived"}
        desc = [
            {"id": "t_a", "status": "todo", "created_at": 0},
            {"id": "t_b", "status": "blocked", "created_at": 0},
            {"id": "t_c", "status": "done", "created_at": 0},
        ]
        rep = mod.compute_cascade_disposition(root, desc, now=10 * 86400, stale_after_days=7.0)
        self.assertTrue(rep["terminal_root"])
        self.assertEqual(rep["open_descendants"], 2)
        self.assertFalse(rep["phase_closeable"])  # open descendants remain
        dispositions = {r["task_id"]: r["disposition"] for r in rep["rows"]}
        self.assertEqual(dispositions["t_c"], "already_terminal")
        self.assertEqual(dispositions["t_a"], "superseded_by_root")  # stale
        self.assertIn("age_days_p50", rep)
        self.assertIn("age_days_p90", rep)

    def test_live_root_marks_pending(self):
        root = {"id": "t_root", "status": "running"}
        desc = [{"id": "t_a", "status": "todo", "created_at": 0}]
        rep = mod.compute_cascade_disposition(root, desc, now=86400)
        self.assertFalse(rep["terminal_root"])
        self.assertEqual(rep["rows"][0]["disposition"], "pending_root_disposition")

    def test_phase_closeable_when_no_open_descendants(self):
        root = {"id": "t_root", "status": "archived"}
        desc = [{"id": "t_a", "status": "done", "created_at": 0}]
        rep = mod.compute_cascade_disposition(root, desc, now=86400)
        self.assertTrue(rep["phase_closeable"])


class SloReportTests(unittest.TestCase):
    def test_slo_report_shape(self):
        cands = [
            mod.Candidate("b", task(status="blocked"), show(), mod.Decision("unclassified", "company", "route_review", "r"), 7200),
            mod.Candidate("b", task(id="t_r", title="Recover t_x: y", status="blocked"), show(), mod.Decision("nested_recovery", "company", "hold", "r"), 3600),
        ]
        rep = mod.slo_report(cands, 1)
        self.assertEqual(rep["candidates"], 2)
        self.assertEqual(rep["recovery_cards_open"], 1)
        self.assertIn("preventable_block_rate", rep)
        self.assertIn("blocked_age_h_p50", rep)
        self.assertIn("blocked_age_h_p90", rep)
        self.assertEqual(rep["recovery_duplicate_count"], 0)


if __name__ == "__main__":
    unittest.main()
