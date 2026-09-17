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


if __name__ == "__main__":
    unittest.main()
