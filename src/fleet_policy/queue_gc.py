"""Automatic stale queue GC — v1.2.33 (spec: v1224-gc-spec-20260918).

Renumbered from the spec's v1.2.24 per the version-reservation rule
(docs/FLEET_POLICY.md): 1.2.24–1.2.31 are released on trunk and 1.2.32 is
claimed by open PR #51.

The company queue audit (2026-09-16 snapshot, QA-finalized) found the
operator approval/notification queues dominated by dead weight: of 61
pending approval bindings, 42 were bound to terminal tasks and 6 were
duplicate (task, action, target) groups; of 14 pending owner notifications,
12 carried pre-v1.2.14 payloads with no resolvable board binding. Those
rows sat in the queues forever: v1.2.14 expiry only runs in the operator
drain sweep, never on the ensure side, and it cannot see unbound rows at
all.

This module garbage-collects exactly those classes at approval/notification
ensure/drain time:

- ``stale_terminal_task`` — a pending approval binding whose bound task
  resolves live to a terminal status (done/archived/superseded) is
  auto-rejected with ``gc:`` attribution. Board-less bindings and bindings
  whose live status is unresolvable (transport error, unknown card) are
  PRESERVED: fail closed, the v1.2.14 doctrine.
- ``duplicate_binding`` — the same (task, action, target) pending more than
  once: keep the newest (``created_at``, then insertion ``rowid``), reject
  the older siblings.
- ``dead_notification_unresolvable`` — a pending outbox row whose payload
  is malformed or carries no explicit board/task binding (pre-v1.2.14
  format) is dead-lettered through the PR40 outbox machinery.
- ``dead_notification_terminal_task`` — a pending outbox row bound to a
  provably terminal card is dead-lettered the same way.

Hard invariants (each locked by tests/test_v1233_stale_queue_gc.py):
fresh owner-bound pending approvals are never touched; only ``pending``
rows of an exact rule match move; one shared per-run cap bounds every
write; every action — including dry-run intentions — is logged as an
event; and the whole feature is config-gated, default OFF.

Config contract (absent section = disabled; invalid values fall back):

    queue_gc:
      enabled: false        # master switch; live activation is a separate
                            # gated downstream card (dry-run first)
      mode: dry_run         # dry_run = log intended actions, write nothing
      max_actions_per_run: 25   # hard-clamped to HARD_MAX_ACTIONS_PER_RUN

Wiring:
- ensure side (``FleetPolicyRuntime.pre_tool_call``): pure-store rules only
  (``duplicate_binding``) — the worker hot path never performs live board
  lookups, so no resolver is injected there.
- drain side (``fleet-policy drain-notifications`` and the explicit
  ``fleet-policy queue-gc`` probe): all rules with a live-status resolver
  injected from ``HermesProjector``. Hook automation runs only when
  ``queue_gc.enabled`` is true; an explicit CLI ``--mode dry_run`` probe
  scans even on a disabled config (QA evidence path) but never writes, and
  ``--mode enforce`` never bypasses the config gate.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

from .projector import HermesProjector
from .redaction import stable_id
from .storage import PolicyStore, utc_now

Resolver = Callable[[str, str], "str | None"]

DEFAULT_MAX_ACTIONS_PER_RUN = 25
HARD_MAX_ACTIONS_PER_RUN = 200
_MODES = ("dry_run", "enforce")

RULE_STALE_TERMINAL = "stale_terminal_task"
RULE_DUPLICATE_BINDING = "duplicate_binding"
RULE_DEAD_UNRESOLVABLE = "dead_notification_unresolvable"
RULE_DEAD_TERMINAL_TASK = "dead_notification_terminal_task"


@dataclass(frozen=True, slots=True)
class GcSettings:
    """Fail-safe config projection: anything missing or invalid means OFF."""

    enabled: bool = False
    mode: str = "dry_run"
    max_actions_per_run: int = DEFAULT_MAX_ACTIONS_PER_RUN

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "GcSettings":
        section = config.get("queue_gc") if isinstance(config, dict) else None
        if not isinstance(section, dict):
            return cls()
        enabled = section.get("enabled") is True
        mode = section.get("mode")
        if mode not in _MODES:
            mode = "dry_run"
        cap = section.get("max_actions_per_run")
        if isinstance(cap, bool) or not isinstance(cap, int) or cap <= 0:
            cap = DEFAULT_MAX_ACTIONS_PER_RUN
        return cls(enabled=enabled, mode=mode,
                   max_actions_per_run=min(cap, HARD_MAX_ACTIONS_PER_RUN))


class QueueGarbageCollector:
    """One bounded GC pass over the pending approval/notification queues."""

    def __init__(self, store: PolicyStore, *, settings: GcSettings | None = None,
                 resolver: Resolver | None = None) -> None:
        self.store = store
        self.settings = settings or GcSettings()
        self.resolver = resolver

    # ------------------------------------------------------------- helpers

    def _noop_report(self, scope: str) -> dict[str, Any]:
        return {
            "enabled": self.settings.enabled,
            "mode": self.settings.mode,
            "scope": scope,
            "applied": False,
            "scanned_approvals": 0,
            "scanned_notifications": 0,
            "counts": {},
            "actions": [],
            "capped": False,
        }

    def _budget(self, limit: int | None) -> int:
        cap = limit
        if isinstance(cap, bool) or not isinstance(cap, int) or cap <= 0:
            cap = self.settings.max_actions_per_run
        return max(1, min(int(cap), HARD_MAX_ACTIONS_PER_RUN))

    def _resolve(self, cache: dict[tuple[str, str], str | None],
                 board: str, task_id: str) -> str | None:
        key = (board, task_id)
        if key in cache:
            return cache[key]
        status: str | None = None
        if self.resolver is not None:
            try:
                raw = self.resolver(board, task_id)
            except Exception:
                raw = None  # transport failure = unresolvable = preserved
            if isinstance(raw, str) and raw.strip():
                status = raw.strip().lower()
        cache[key] = status
        return status

    # ----------------------------------------------------------------- run

    def run(self, *, scope: str = "drain", mode: str | None = None,
            limit: int | None = None) -> dict[str, Any]:
        """Execute one GC pass and return the machine-readable report.

        ``scope="ensure"`` runs pure-store rules only (duplicate bindings);
        ``scope="drain"`` runs every rule with the injected resolver. An
        explicit ``mode`` (CLI probe) scans even on a disabled config;
        writes still require ``enabled`` AND ``mode == "enforce"``.
        """
        explicit = mode in _MODES
        if not self.settings.enabled and not explicit:
            return self._noop_report(scope)
        effective = mode if explicit else self.settings.mode
        applied = self.settings.enabled and effective == "enforce"
        budget = self._budget(limit)

        actions: list[dict[str, Any]] = []
        capped = False
        cache: dict[tuple[str, str], str | None] = {}

        def _add(rule: str, key: str, task_id: str | None,
                 board: str | None, reason: str) -> None:
            if len(actions) >= budget:
                return
            actions.append({
                "rule": rule, "key": key, "task_id": task_id,
                "board": board or None, "reason": reason, "applied": applied,
            })

        # ---- approvals: duplicate groups (pure store), then stale terminal
        approval_rows = self.store.pending_approval_gc_rows()
        groups: dict[tuple[str, str, str], list[Any]] = {}
        for row in approval_rows:
            groups.setdefault(
                (str(row["task_id"]), str(row["action"]), str(row["target"])), []
            ).append(row)
        older_duplicate_keys: set[str] = set()
        for members in groups.values():
            if len(members) > 1:
                # Rows arrive ordered by (created_at, rowid): the last member
                # is the newest and survives; every older sibling is a
                # candidate.
                for older in members[:-1]:
                    older_duplicate_keys.add(str(older["rule_key"]))

        for row in approval_rows:
            if len(actions) >= budget:
                capped = True
                break
            rule_key = str(row["rule_key"])
            task_id = str(row["task_id"])
            board = str(row["board"] or "")
            if rule_key in older_duplicate_keys:
                _add(RULE_DUPLICATE_BINDING, rule_key, task_id, board, "keep_newest")
                continue
            if scope == "drain" and self.resolver is not None and board and task_id:
                status = self._resolve(cache, board, task_id)
                if status is not None and status in HermesProjector.CLOSED_TASK_STATUSES:
                    _add(RULE_STALE_TERMINAL, rule_key, task_id, board,
                         f"task_status:{status}")

        # ---- notifications: unresolvable payloads, then terminal bindings
        notification_rows: list[Any] = []
        if scope == "drain":
            notification_rows = self.store.pending_notification_gc_rows()
        for row in notification_rows:
            if len(actions) >= budget:
                capped = True
                break
            event_id = str(row["event_id"])
            try:
                payload = json.loads(row["payload_json"])
            except Exception:
                payload = None
                malformed = True
            else:
                malformed = False
            if malformed or not isinstance(payload, dict):
                _add(RULE_DEAD_UNRESOLVABLE, event_id, None, None,
                     "malformed_payload" if malformed else "unresolvable_binding")
                continue
            binding = HermesProjector.notification_binding(payload)
            if binding is None:
                _add(RULE_DEAD_UNRESOLVABLE, event_id, None, None,
                     "unresolvable_binding")
                continue
            board, task_id = binding
            if self.resolver is not None:
                status = self._resolve(cache, board, task_id)
                if status is not None and status in HermesProjector.CLOSED_TASK_STATUSES:
                    _add(RULE_DEAD_TERMINAL_TASK, event_id, task_id, board,
                         f"task_status:{status}")

        # ---- apply (enforce only) + log every action (both modes)
        counts: dict[str, int] = {}
        for action in actions:
            rule = action["rule"]
            counts[rule] = counts.get(rule, 0) + 1
            if applied:
                if rule in (RULE_DUPLICATE_BINDING, RULE_STALE_TERMINAL):
                    written = self.store.gc_reject_approval(
                        action["key"], rule, action["reason"])
                else:
                    written = self.store.gc_dead_notification(
                        action["key"], action["reason"])
                action["applied"] = bool(written)
            action_id = stable_id("queue_gc_action", rule, action["key"], effective)
            self.store.record_event(
                action_id, action_id, action["task_id"], "queue_gc_action",
                {
                    "rule": rule, "key": action["key"],
                    "task_id": action["task_id"], "board": action["board"],
                    "reason": action["reason"], "scope": scope,
                    "mode": effective, "applied": bool(action["applied"]),
                },
                False,
            )
        if actions:
            run_id = stable_id("queue_gc_run", scope, effective, utc_now())
            self.store.record_event(
                run_id, run_id, None, "queue_gc_run",
                {
                    "scope": scope, "mode": effective, "applied": applied,
                    "counts": counts, "capped": capped,
                    "scanned_approvals": len(approval_rows),
                    "scanned_notifications": len(notification_rows),
                },
                False,
            )

        return {
            "enabled": self.settings.enabled,
            "mode": effective,
            "scope": scope,
            "applied": applied,
            "scanned_approvals": len(approval_rows),
            "scanned_notifications": len(notification_rows),
            "counts": counts,
            "actions": actions,
            "capped": capped,
        }
