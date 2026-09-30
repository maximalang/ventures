"""v1.2.33 — automatic stale queue GC (spec: v1224-gc-spec-20260918).

Renumbered from the spec's v1.2.24 per the repo's version-reservation rule
(docs/FLEET_POLICY.md): 1.2.24–1.2.31 are released on trunk and 1.2.32 is
claimed by open PR #51, so this feature lands as 1.2.33.

Red/green contract (base 287e86c → v1.2.33): every test below fails on the
base commit (``fleet_policy.queue_gc`` does not exist; ``PolicyStore`` has no
GC methods) and passes with the implementation.

Feature scope (audit structural proposal, approved by company):
1. stale_terminal_task — pending approval bindings whose bound task is
   terminal (done/archived/superseded) are auto-rejected with a ``gc:``
   attribution; decided rows stay immutable audit.
2. duplicate_binding — same (task, action, target) pending more than once:
   keep the newest (created_at, then rule_key), reject the older.
3. dead notifications — pending outbox rows with no resolvable board binding
   (pre-v1.2.14 format or malformed payload) and rows bound to terminal
   cards dead-letter through the PR40 outbox machinery (status='dead',
   suppression_reason, resolved_at).

Hard invariants locked here by fixture (never by live row ids):
- fresh owner-bound pending approvals are preserved (active, blocked,
  unresolvable, or board-less bindings are NEVER touched);
- no over-delete: only exact rule matches, only ``pending`` rows, bounded
  per-run cap, every action logged as an event;
- config-gated, default OFF: absent/invalid config = disabled; dry-run is
  write-free; enforce requires enabled config even from the CLI.
"""
from __future__ import annotations

import json

import pytest

from fleet_policy.queue_gc import (
    DEFAULT_MAX_ACTIONS_PER_RUN,
    HARD_MAX_ACTIONS_PER_RUN,
    GcSettings,
    QueueGarbageCollector,
)
from fleet_policy.storage import PolicyStore

BOARD = "fleet-ops"


# --------------------------------------------------------------- fixtures

def _store(tmp_path) -> PolicyStore:
    store = PolicyStore(tmp_path / "policy.db")
    store.migrate()
    return store


def _approval(store, rule_key, task_id, *, action="terminal", target="cmd",
              args_hash="h1", board=BOARD, created_at="2026-09-16T10:00:00Z",
              status="pending", decided_by=None):
    with store.connect() as connection:
        connection.execute(
            "INSERT INTO approvals(rule_key,task_id,action,target,args_hash,"
            "status,created_at,board,decided_by) VALUES(?,?,?,?,?,?,?,?,?)",
            (rule_key, task_id, action, target, args_hash, status,
             created_at, board, decided_by),
        )


def _outbox(store, event_id, payload, *, status="pending",
            created_at="2026-09-16T10:00:00Z"):
    encoded = payload if isinstance(payload, str) else json.dumps(payload)
    with store.connect() as connection:
        connection.execute(
            "INSERT INTO notification_outbox(event_id,payload_json,status,created_at)"
            " VALUES(?,?,?,?)",
            (event_id, encoded, status, created_at),
        )


def _approval_row(store, rule_key):
    with store.connect() as connection:
        return connection.execute(
            "SELECT * FROM approvals WHERE rule_key=?", (rule_key,)
        ).fetchone()


def _outbox_row(store, event_id):
    with store.connect() as connection:
        return connection.execute(
            "SELECT * FROM notification_outbox WHERE event_id=?", (event_id,)
        ).fetchone()


def _events(store, kind):
    with store.connect() as connection:
        return list(connection.execute(
            "SELECT * FROM events WHERE kind=? ORDER BY created_at", (kind,)
        ))


def _resolver(mapping, raises=()):
    """Fake live-status resolver recording every (board, task) lookup."""
    calls: list[tuple[str, str]] = []

    def resolve(board: str, task_id: str):
        calls.append((board, task_id))
        if (board, task_id) in raises:
            raise OSError("transport exploded")
        return mapping.get((board, task_id))

    resolve.calls = calls
    return resolve


def _settings(**over) -> GcSettings:
    base = {"enabled": True, "mode": "enforce",
            "max_actions_per_run": DEFAULT_MAX_ACTIONS_PER_RUN}
    base.update(over)
    return GcSettings(**base)


def _enabled_config(**over) -> dict:
    section = {"enabled": True, "mode": "enforce"}
    section.update(over)
    return {"queue_gc": section}


# ------------------------------------------------------- settings contract

def test_settings_default_off_and_invalid_config_falls_back(tmp_path):
    # Absent section → disabled, dry-run, default cap.
    settings = GcSettings.from_config({})
    assert settings.enabled is False
    assert settings.mode == "dry_run"
    assert settings.max_actions_per_run == DEFAULT_MAX_ACTIONS_PER_RUN

    # Non-bool enabled / garbage mode / broken cap → safe fallbacks.
    settings = GcSettings.from_config(
        {"queue_gc": {"enabled": "yes", "mode": "destroy", "max_actions_per_run": -3}}
    )
    assert settings.enabled is False
    assert settings.mode == "dry_run"
    assert settings.max_actions_per_run == DEFAULT_MAX_ACTIONS_PER_RUN

    # Valid section is respected; the cap is clamped to the hard maximum.
    settings = GcSettings.from_config(
        {"queue_gc": {"enabled": True, "mode": "enforce", "max_actions_per_run": 10**9}}
    )
    assert settings.enabled is True
    assert settings.mode == "enforce"
    assert settings.max_actions_per_run == HARD_MAX_ACTIONS_PER_RUN


def test_disabled_config_is_a_full_noop(tmp_path):
    """Config gate default OFF: hook automation scans nothing, writes nothing."""
    store = _store(tmp_path)
    _approval(store, "rk_stale", "t_done")
    _outbox(store, "ev_orphan", {"decision": "deny"})  # no board binding
    collector = QueueGarbageCollector(
        store, settings=GcSettings.from_config({}), resolver=_resolver({})
    )
    report = collector.run(scope="drain")
    assert report["enabled"] is False
    assert report["applied"] is False
    assert report["actions"] == []
    assert report["counts"] == {}
    assert report["scanned_approvals"] == 0
    assert report["scanned_notifications"] == 0
    assert _approval_row(store, "rk_stale")["status"] == "pending"
    assert _outbox_row(store, "ev_orphan")["status"] == "pending"
    assert _events(store, "queue_gc_action") == []


# ------------------------------------------------- rule 1: stale terminal

def test_stale_terminal_task_pending_is_auto_rejected(tmp_path):
    store = _store(tmp_path)
    _approval(store, "rk_done", "t_done")
    _approval(store, "rk_arch", "t_arch", created_at="2026-09-16T11:00:00Z")
    _approval(store, "rk_super", "t_super", created_at="2026-09-16T12:00:00Z")
    resolver = _resolver({
        (BOARD, "t_done"): "done",
        (BOARD, "t_arch"): "archived",
        (BOARD, "t_super"): "superseded",
    })
    collector = QueueGarbageCollector(store, settings=_settings(), resolver=resolver)
    report = collector.run(scope="drain")
    assert report["applied"] is True
    assert report["counts"]["stale_terminal_task"] == 3
    for key in ("rk_done", "rk_arch", "rk_super"):
        row = _approval_row(store, key)
        assert row["status"] == "rejected"
        assert row["decided_by"].startswith("gc:stale_terminal_task:")
        assert row["decided_at"] is not None
    # One live lookup per distinct binding (cache), not per row.
    assert resolver.calls == [(BOARD, "t_done"), (BOARD, "t_arch"), (BOARD, "t_super")]


def test_gc_touches_only_pending_rows_of_exact_matches(tmp_path):
    """Decided rows are immutable audit; active-task rows are preserved."""
    store = _store(tmp_path)
    # Terminal task, but the row is already decided/consumed/expired/revoked.
    # Distinct args_hashes: the UNIQUE binding index covers decided rows too.
    _approval(store, "rk_approved", "t_done", args_hash="h_appr",
              status="approved", decided_by="user")
    _approval(store, "rk_rejected", "t_done", args_hash="h_rej",
              status="rejected", decided_by="user")
    _approval(store, "rk_consumed", "t_done", args_hash="h_cons",
              status="consumed", decided_by="user")
    _approval(store, "rk_expired", "t_done", args_hash="h_exp",
              status="expired", decided_by="drain")
    _approval(store, "rk_revoked", "t_done", args_hash="h_rev",
              status="revoked", decided_by="user")
    # Pending row whose task is ACTIVE — the fresh owner-bound class.
    _approval(store, "rk_fresh", "t_live")
    resolver = _resolver({(BOARD, "t_done"): "done", (BOARD, "t_live"): "running"})
    collector = QueueGarbageCollector(store, settings=_settings(), resolver=resolver)
    report = collector.run(scope="drain")
    assert report["counts"] == {}
    assert report["actions"] == []
    assert _approval_row(store, "rk_approved")["status"] == "approved"
    assert _approval_row(store, "rk_approved")["decided_by"] == "user"
    assert _approval_row(store, "rk_rejected")["status"] == "rejected"
    assert _approval_row(store, "rk_consumed")["status"] == "consumed"
    assert _approval_row(store, "rk_expired")["status"] == "expired"
    assert _approval_row(store, "rk_revoked")["status"] == "revoked"
    assert _approval_row(store, "rk_fresh")["status"] == "pending"


def test_fresh_bindings_preserved_by_fixture_invariant(tmp_path):
    """Audit class `pending_fresh` (13 items): every non-terminal resolution
    keeps the binding pending — active statuses, unresolvable (None),
    resolver transport errors, and board-less legacy rows."""
    store = _store(tmp_path)
    _approval(store, "rk_running", "t_run")
    _approval(store, "rk_blocked", "t_blk")
    _approval(store, "rk_ready", "t_rdy")
    _approval(store, "rk_unresolvable", "t_gone")
    _approval(store, "rk_exploding", "t_boom")
    _approval(store, "rk_boardless", "t_done", board="")
    resolver = _resolver(
        {
            (BOARD, "t_run"): "running",
            (BOARD, "t_blk"): "blocked",
            (BOARD, "t_rdy"): "ready",
            (BOARD, "t_gone"): None,
        },
        raises={(BOARD, "t_boom")},
    )
    collector = QueueGarbageCollector(store, settings=_settings(), resolver=resolver)
    report = collector.run(scope="drain")
    assert report["counts"] == {}
    for key in ("rk_running", "rk_blocked", "rk_ready", "rk_unresolvable",
                "rk_exploding", "rk_boardless"):
        assert _approval_row(store, key)["status"] == "pending", key
    # The board-less row is never resolved live (no board to query).
    assert (BOARD, "") not in resolver.calls
    assert ("", "t_done") not in resolver.calls


# ------------------------------------------- rule 2: duplicate bindings

def test_duplicate_binding_keeps_newest_rejects_older(tmp_path):
    store = _store(tmp_path)
    _approval(store, "rk_old", "t_live", args_hash="h_old",
              created_at="2026-09-16T10:00:00Z")
    _approval(store, "rk_mid", "t_live", args_hash="h_mid",
              created_at="2026-09-16T11:00:00Z")
    _approval(store, "rk_new", "t_live", args_hash="h_new",
              created_at="2026-09-16T12:00:00Z")
    collector = QueueGarbageCollector(
        store, settings=_settings(), resolver=_resolver({(BOARD, "t_live"): "running"})
    )
    report = collector.run(scope="drain")
    assert report["counts"]["duplicate_binding"] == 2
    assert _approval_row(store, "rk_old")["status"] == "rejected"
    assert _approval_row(store, "rk_mid")["status"] == "rejected"
    assert _approval_row(store, "rk_old")["decided_by"].startswith("gc:duplicate_binding:")
    assert _approval_row(store, "rk_new")["status"] == "pending"


def test_duplicate_tie_breaks_deterministically_on_rule_key(tmp_path):
    store = _store(tmp_path)
    same = "2026-09-16T10:00:00Z"
    _approval(store, "rk_a", "t_live", args_hash="h_a", created_at=same)
    _approval(store, "rk_b", "t_live", args_hash="h_b", created_at=same)
    collector = QueueGarbageCollector(store, settings=_settings(), resolver=None)
    collector.run(scope="ensure")
    assert _approval_row(store, "rk_a")["status"] == "rejected"
    assert _approval_row(store, "rk_b")["status"] == "pending"


def test_duplicate_rule_matches_only_exact_groups(tmp_path):
    """Same task with a different action or target is NOT a duplicate;
    a lone pending binding is never a duplicate."""
    store = _store(tmp_path)
    _approval(store, "rk_t1", "t_live", action="terminal", target="cmd-a", args_hash="h1")
    _approval(store, "rk_t2", "t_live", action="write_file", target="cmd-a", args_hash="h2")
    _approval(store, "rk_t3", "t_live", action="terminal", target="cmd-b", args_hash="h3")
    _approval(store, "rk_other_task", "t_other", action="terminal", target="cmd-a",
              args_hash="h1")
    collector = QueueGarbageCollector(store, settings=_settings(), resolver=None)
    report = collector.run(scope="ensure")
    assert report["counts"] == {}
    for key in ("rk_t1", "rk_t2", "rk_t3", "rk_other_task"):
        assert _approval_row(store, key)["status"] == "pending"


def test_ensure_scope_runs_pure_store_rules_without_resolver(tmp_path):
    """Ensure-side GC is pure-store: duplicates yes, live-status rules no,
    notifications not scanned."""
    store = _store(tmp_path)
    _approval(store, "rk_stale", "t_done")  # would need a live lookup
    _approval(store, "rk_dup_old", "t_live", args_hash="h1",
              created_at="2026-09-16T10:00:00Z")
    _approval(store, "rk_dup_new", "t_live", args_hash="h2",
              created_at="2026-09-16T11:00:00Z")
    _outbox(store, "ev_orphan", {"decision": "deny"})
    collector = QueueGarbageCollector(store, settings=_settings(), resolver=None)
    report = collector.run(scope="ensure")
    assert report["scope"] == "ensure"
    assert report["counts"] == {"duplicate_binding": 1}
    assert _approval_row(store, "rk_dup_old")["status"] == "rejected"
    assert _approval_row(store, "rk_dup_new")["status"] == "pending"
    assert _approval_row(store, "rk_stale")["status"] == "pending"
    assert _outbox_row(store, "ev_orphan")["status"] == "pending"
    assert report["scanned_notifications"] == 0


# ------------------------------------------------ rule 3: dead letters

def test_dead_notifications_unresolvable_and_terminal(tmp_path):
    store = _store(tmp_path)
    # Pre-v1.2.14 shape: no board/task binding at all.
    _outbox(store, "ev_orphan", {"decision": "deny", "rule_id": "x"})
    # Malformed payload bytes.
    _outbox(store, "ev_broken", "{not-json")
    # Bound to a terminal card.
    _outbox(store, "ev_dead_task", {"task_id": "t_done", "board": BOARD,
                                    "decision": "approval_required"})
    # Bound to an active card — preserved.
    _outbox(store, "ev_live", {"task_id": "t_live", "board": BOARD,
                               "decision": "approval_required"})
    # Bound but currently unresolvable — preserved (fail closed).
    _outbox(store, "ev_unknown", {"task_id": "t_gone", "board": BOARD,
                                  "decision": "deny"})
    resolver = _resolver({(BOARD, "t_done"): "done", (BOARD, "t_live"): "running",
                          (BOARD, "t_gone"): None})
    collector = QueueGarbageCollector(store, settings=_settings(), resolver=resolver)
    report = collector.run(scope="drain")
    assert report["counts"]["dead_notification_unresolvable"] == 2
    assert report["counts"]["dead_notification_terminal_task"] == 1
    for event_id, reason in (("ev_orphan", "unresolvable_binding"),
                             ("ev_broken", "malformed_payload"),
                             ("ev_dead_task", "task_status:done")):
        row = _outbox_row(store, event_id)
        assert row["status"] == "dead", event_id
        assert row["resolved_at"] is not None
        assert row["suppression_reason"] == f"gc:{reason}"
        assert row["claim_token"] is None
    assert _outbox_row(store, "ev_live")["status"] == "pending"
    assert _outbox_row(store, "ev_unknown")["status"] == "pending"


def test_dead_letter_rule_skips_non_pending_outbox_rows(tmp_path):
    store = _store(tmp_path)
    payload = {"task_id": "t_done", "board": BOARD, "decision": "deny"}
    _outbox(store, "ev_sent", payload, status="sent")
    _outbox(store, "ev_dead", payload, status="dead")
    _outbox(store, "ev_suppressed", payload, status="suppressed")
    _outbox(store, "ev_dispatching", payload, status="dispatching")
    resolver = _resolver({(BOARD, "t_done"): "done"})
    collector = QueueGarbageCollector(store, settings=_settings(), resolver=resolver)
    report = collector.run(scope="drain")
    assert report["scanned_notifications"] == 0
    assert report["counts"] == {}
    assert _outbox_row(store, "ev_sent")["status"] == "sent"
    assert _outbox_row(store, "ev_dead")["status"] == "dead"
    assert _outbox_row(store, "ev_suppressed")["status"] == "suppressed"
    assert _outbox_row(store, "ev_dispatching")["status"] == "dispatching"


# ----------------------------------------------- invariants: cap + audit

def test_batch_cap_bounds_every_run_and_resumes(tmp_path):
    store = _store(tmp_path)
    for index in range(5):
        _approval(store, f"rk_{index}", f"t_done_{index}",
                  created_at=f"2026-09-16T1{index}:00:00Z")
    resolver = _resolver({(BOARD, f"t_done_{index}"): "done" for index in range(5)})

    first = QueueGarbageCollector(
        store, settings=_settings(max_actions_per_run=2), resolver=resolver
    ).run(scope="drain")
    assert first["capped"] is True
    assert sum(first["counts"].values()) == 2
    rejected = [key for key in (f"rk_{i}" for i in range(5))
                if _approval_row(store, key)["status"] == "rejected"]
    assert len(rejected) == 2

    second = QueueGarbageCollector(
        store, settings=_settings(max_actions_per_run=2), resolver=resolver
    ).run(scope="drain")
    assert sum(second["counts"].values()) == 2

    third = QueueGarbageCollector(
        store, settings=_settings(max_actions_per_run=2), resolver=resolver
    ).run(scope="drain")
    assert sum(third["counts"].values()) == 1
    assert third["capped"] is False
    statuses = [_approval_row(store, f"rk_{i}")["status"] for i in range(5)]
    assert statuses == ["rejected"] * 5

    # A settled queue produces an empty, uncapped report.
    fourth = QueueGarbageCollector(
        store, settings=_settings(max_actions_per_run=2), resolver=resolver
    ).run(scope="drain")
    assert fourth["counts"] == {}
    assert fourth["capped"] is False


def test_cap_is_shared_across_rules(tmp_path):
    store = _store(tmp_path)
    _approval(store, "rk_dup_old", "t_live", args_hash="h1",
              created_at="2026-09-16T10:00:00Z")
    _approval(store, "rk_dup_new", "t_live", args_hash="h2",
              created_at="2026-09-16T11:00:00Z")
    _approval(store, "rk_stale", "t_done", created_at="2026-09-16T09:00:00Z")
    _outbox(store, "ev_orphan", {"decision": "deny"})
    resolver = _resolver({(BOARD, "t_live"): "running", (BOARD, "t_done"): "done"})
    report = QueueGarbageCollector(
        store, settings=_settings(max_actions_per_run=2), resolver=resolver
    ).run(scope="drain")
    assert sum(report["counts"].values()) == 2
    assert report["capped"] is True


def test_dry_run_logs_intended_actions_without_writing(tmp_path):
    store = _store(tmp_path)
    _approval(store, "rk_stale", "t_done")
    _approval(store, "rk_dup_old", "t_live", args_hash="h1",
              created_at="2026-09-16T10:00:00Z")
    _approval(store, "rk_dup_new", "t_live", args_hash="h2",
              created_at="2026-09-16T11:00:00Z")
    _outbox(store, "ev_orphan", {"decision": "deny"})
    resolver = _resolver({(BOARD, "t_done"): "done", (BOARD, "t_live"): "running"})
    report = QueueGarbageCollector(
        store, settings=_settings(mode="dry_run"), resolver=resolver
    ).run(scope="drain")
    assert report["mode"] == "dry_run"
    assert report["applied"] is False
    assert report["counts"] == {
        "stale_terminal_task": 1, "duplicate_binding": 1,
        "dead_notification_unresolvable": 1,
    }
    assert all(action["applied"] is False for action in report["actions"])
    # Nothing moved.
    assert _approval_row(store, "rk_stale")["status"] == "pending"
    assert _approval_row(store, "rk_dup_old")["status"] == "pending"
    assert _outbox_row(store, "ev_orphan")["status"] == "pending"
    # Intended actions are still fully auditable.
    logged = _events(store, "queue_gc_action")
    assert len(logged) == 3
    for event in logged:
        payload = json.loads(event["payload_json"])
        assert payload["mode"] == "dry_run"
        assert payload["applied"] is False
        assert payload["rule"] and payload["key"] and payload["reason"]


def test_explicit_dry_run_probe_works_on_disabled_config(tmp_path):
    """QA probe path: an explicit dry-run request scans and reports even
    while the config gate is OFF — but never writes queue rows."""
    store = _store(tmp_path)
    _approval(store, "rk_stale", "t_done")
    resolver = _resolver({(BOARD, "t_done"): "done"})
    collector = QueueGarbageCollector(
        store, settings=GcSettings.from_config({}), resolver=resolver
    )
    report = collector.run(scope="drain", mode="dry_run")
    assert report["enabled"] is False
    assert report["applied"] is False
    assert report["counts"] == {"stale_terminal_task": 1}
    assert _approval_row(store, "rk_stale")["status"] == "pending"
    # An explicit enforce on disabled config stays gated: scan, never apply.
    report = collector.run(scope="drain", mode="enforce")
    assert report["applied"] is False
    assert _approval_row(store, "rk_stale")["status"] == "pending"


def test_every_enforced_action_and_run_is_logged(tmp_path):
    store = _store(tmp_path)
    _approval(store, "rk_stale", "t_done")
    _approval(store, "rk_dup_old", "t_live", args_hash="h1",
              created_at="2026-09-16T10:00:00Z")
    _approval(store, "rk_dup_new", "t_live", args_hash="h2",
              created_at="2026-09-16T11:00:00Z")
    _outbox(store, "ev_orphan", {"decision": "deny"})
    resolver = _resolver({(BOARD, "t_done"): "done", (BOARD, "t_live"): "running"})
    report = QueueGarbageCollector(
        store, settings=_settings(), resolver=resolver
    ).run(scope="drain")
    assert report["applied"] is True
    logged = _events(store, "queue_gc_action")
    assert len(logged) == 3
    rules = sorted(json.loads(event["payload_json"])["rule"] for event in logged)
    assert rules == [
        "dead_notification_unresolvable", "duplicate_binding", "stale_terminal_task",
    ]
    for event in logged:
        payload = json.loads(event["payload_json"])
        assert payload["applied"] is True
        assert payload["scope"] == "drain"
    runs = _events(store, "queue_gc_run")
    assert len(runs) == 1
    summary = json.loads(runs[0]["payload_json"])
    assert summary["applied"] is True
    assert summary["counts"] == report["counts"]


# ---------------------------------------------------- runtime/CLI wiring

def test_runtime_maybe_queue_gc_is_config_gated(tmp_path, runtime):
    """FleetPolicyRuntime.maybe_queue_gc: no-op while the gate is OFF,
    active once the in-memory config enables it (hook automation path)."""
    _approval(runtime.store, "rk_dup_old", "t_test", args_hash="h1",
              created_at="2026-09-16T10:00:00Z")
    _approval(runtime.store, "rk_dup_new", "t_test", args_hash="h2",
              created_at="2026-09-16T11:00:00Z")
    report = runtime.maybe_queue_gc(scope="ensure")
    assert report["enabled"] is False
    assert _approval_row(runtime.store, "rk_dup_old")["status"] == "pending"

    runtime.config["queue_gc"] = {"enabled": True, "mode": "enforce"}
    report = runtime.maybe_queue_gc(scope="ensure")
    assert report["applied"] is True
    assert _approval_row(runtime.store, "rk_dup_old")["status"] == "rejected"
    assert _approval_row(runtime.store, "rk_dup_new")["status"] == "pending"


def test_pre_tool_call_ensure_dedupes_previous_binding(
    tmp_path, runtime, task_context, monkeypatch
):
    """End-to-end ensure-side wiring: a second approval_required binding for
    the same (task, action, target) with new args GCs the older pending one
    when the gate is enabled — and leaves everything alone when it is not."""
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    args_v1 = {"command": "mass outreach to 5000 contacts", "timeout": 60}
    args_v2 = {"command": "mass outreach to 5000 contacts", "timeout": 120}

    # Gate OFF (shipped default): both bindings coexist.
    first = runtime.pre_tool_call("terminal", args_v1, task_context)
    assert first.decision == "approval_required"
    key_v1 = first.approval_card["rule_key"]
    task_context["tool_call_id"] = "call-2"
    second = runtime.pre_tool_call("terminal", args_v2, task_context)
    assert second.decision == "approval_required"
    key_v2 = second.approval_card["rule_key"]
    assert key_v1 != key_v2
    assert _approval_row(runtime.store, key_v1)["status"] == "pending"

    # Gate ON: the next ensure tick rejects the older duplicate.
    runtime.config["queue_gc"] = {"enabled": True, "mode": "enforce"}
    task_context["tool_call_id"] = "call-3"
    args_v3 = {"command": "mass outreach to 5000 contacts", "timeout": 240}
    third = runtime.pre_tool_call("terminal", args_v3, task_context)
    assert third.decision == "approval_required"
    key_v3 = third.approval_card["rule_key"]
    # keep-newest across the whole pending group: only v3 survives.
    assert _approval_row(runtime.store, key_v3)["status"] == "pending"
    for stale_key in (key_v1, key_v2):
        row = _approval_row(runtime.store, stale_key)
        assert row["status"] == "rejected"
        assert row["decided_by"].startswith("gc:duplicate_binding:")


def _patch_cli(cli_module, monkeypatch, runtime, statuses):
    class _FakeProjector:
        def live_task_status(self, board, task_id):
            return statuses.get((board, task_id))

        def expire_closed_approvals(self, store, **kwargs):
            return 0

        def drain_company(self, store, **kwargs):
            return 0

    monkeypatch.setattr(cli_module, "HermesProjector", _FakeProjector)
    monkeypatch.setattr(cli_module, "FleetPolicyRuntime", lambda *a, **k: runtime)


def test_cli_queue_gc_report_and_worker_env_guard(tmp_path, runtime, monkeypatch, capsys):
    import fleet_policy.cli as cli_module

    _approval(runtime.store, "rk_stale", "t_done")
    _patch_cli(cli_module, monkeypatch, runtime,
               {(BOARD, "t_done"): "done", (BOARD, "t_done2"): "done"})
    runtime.config["queue_gc"] = {"enabled": True, "mode": "enforce"}

    # Operator context: enforce applies and the report is machine-readable.
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    assert cli_module.main(["--root", str(tmp_path), "queue-gc"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["report"]["applied"] is True
    assert payload["report"]["counts"] == {"stale_terminal_task": 1}
    assert _approval_row(runtime.store, "rk_stale")["status"] == "rejected"

    # Worker context: enforce is refused fail-closed, rows untouched.
    _approval(runtime.store, "rk_stale_2", "t_done2")
    monkeypatch.setenv("HERMES_KANBAN_TASK", "t_ci_simulated")
    assert cli_module.main(
        ["--root", str(tmp_path), "queue-gc", "--mode", "enforce"]
    ) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert "worker" in payload["reason"]
    assert _approval_row(runtime.store, "rk_stale_2")["status"] == "pending"

    # Worker context: an explicit dry-run probe stays available (read-only
    # report; no queue writes).
    assert cli_module.main(
        ["--root", str(tmp_path), "queue-gc", "--mode", "dry_run"]
    ) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["report"]["applied"] is False
    assert payload["report"]["counts"] == {"stale_terminal_task": 1}
    assert _approval_row(runtime.store, "rk_stale_2")["status"] == "pending"


def test_cli_drain_notifications_runs_gc_before_delivery(
    tmp_path, runtime, monkeypatch, capsys
):
    import fleet_policy.cli as cli_module

    _approval(runtime.store, "rk_stale", "t_done")
    _outbox(runtime.store, "ev_orphan", {"decision": "deny"})
    _patch_cli(cli_module, monkeypatch, runtime, {(BOARD, "t_done"): "done"})
    runtime.config["queue_gc"] = {"enabled": True, "mode": "enforce"}
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)

    assert cli_module.main(["--root", str(tmp_path), "drain-notifications"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["queue_gc"]["counts"] == {
        "stale_terminal_task": 1, "dead_notification_unresolvable": 1,
    }
    assert _approval_row(runtime.store, "rk_stale")["status"] == "rejected"
    assert _outbox_row(runtime.store, "ev_orphan")["status"] == "dead"


def test_cli_drain_notifications_survives_gc_failure(
    tmp_path, runtime, monkeypatch, capsys
):
    """A GC blow-up must never break the drain itself (non-fatal wiring)."""
    import fleet_policy.cli as cli_module

    _patch_cli(cli_module, monkeypatch, runtime, {})

    def _boom(**kwargs):
        raise RuntimeError("gc exploded")

    monkeypatch.setattr(runtime, "maybe_queue_gc", _boom)
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    assert cli_module.main(["--root", str(tmp_path), "drain-notifications"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["sent"] == 0
    assert payload["queue_gc"] == {}
