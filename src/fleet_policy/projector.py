from __future__ import annotations

import json
import subprocess
import tempfile
from collections.abc import Callable, Sequence
from html import escape as _escape
from pathlib import Path

from .storage import PolicyStore

Runner = Callable[[Sequence[str], int], subprocess.CompletedProcess[str]]


def subprocess_runner(command: Sequence[str], timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(command), check=False, capture_output=True, text=True, timeout=timeout, shell=False)


class HermesProjector:
    CLOSED_TASK_STATUSES = frozenset({"done", "archived", "superseded"})
    LOOKUP_TIMEOUT_SECONDS = 5
    # One bounded bot turn: session resume + a single model turn. Measured
    # real latency is ~19s on this host (2026-09-01 probe); the former 15s
    # hard timeout made nearly every batch expire, releasing rows into an
    # endless retry cycle (586 failed vs 20 sent). 90s covers session resume
    # plus one turn with headroom while keeping the drain bounded.
    DELIVERY_TIMEOUT_SECONDS = 90

    def __init__(self, runner: Runner = subprocess_runner):
        self.runner = runner

    def live_task_status(self, board: str, task_id: str) -> str | None:
        """Read one task through the board-bound public Hermes CLI.

        A missing task, non-zero CLI result, malformed response, or expected
        transport error is intentionally indistinguishable to callers: none
        may be converted into a new active incident.
        """
        command = ["hermes", "kanban", "--board", board, "show", task_id, "--json"]
        try:
            result = self.runner(command, self.LOOKUP_TIMEOUT_SECONDS)
        except (subprocess.TimeoutExpired, OSError, subprocess.SubprocessError):
            return None
        if result.returncode != 0:
            return None
        try:
            response = json.loads(result.stdout)
        except (TypeError, json.JSONDecodeError):
            return None
        task = response.get("task") if isinstance(response, dict) else None
        status = task.get("status") if isinstance(task, dict) else None
        return status.lower() if isinstance(status, str) and status else None

    @staticmethod
    def notification_binding(payload: dict) -> tuple[str, str] | None:
        """Return only an explicit, unmodified board/task binding."""
        board = payload.get("board")
        task_id = payload.get("task_id")
        if not isinstance(board, str) or not board or not isinstance(task_id, str) or not task_id:
            return None
        return board, task_id

    def comment_and_block(self, board: str, task_id: str, message: str, *, block: bool = True) -> dict[str, int]:
        result: dict[str, int] = {}
        if block:
            blocked = self.runner(
                ["hermes", "kanban", "--board", board, "block", task_id, message, "--kind", "needs_input"], 20
            )
            result["block"] = int(blocked.returncode)
        else:
            comment = self.runner(
                ["hermes", "kanban", "--board", board, "comment", task_id, message, "--author", "fleet-policy"], 20
            )
            result["comment"] = int(comment.returncode)
        return result

    @staticmethod
    def approval_text(payload: dict) -> str:
        """v1.2.14: compact Russian HTML card (b/i/code, emoji icons) instead
        of raw field dumps. Every dynamic value is HTML-escaped because the
        TG adapter sends the text with ParseMode.HTML."""
        card = payload.get("approval_card") or {}
        esc = _escape
        action = card.get("action") or payload.get("action") or "unknown"
        risk = card.get("risk") or payload.get("reason") or "unknown"
        return "\n".join([
            "🔴 <b>APPROVAL REQUIRED</b>",
            f"👁 <b>Проект/задача:</b> {esc(card.get('project_task') or 'unknown')}",
            f"<b>Действие:</b> <code>{esc(action)}</code>",
            f"<b>Зачем:</b> {esc(card.get('why') or 'policy gate')}",
            f"<b>Evidence:</b> <code>{esc(card.get('evidence') or 'unavailable')}</code>",
            f"<b>Риск:</b> {esc(risk)}",
            f"<b>Rollback:</b> {esc(card.get('rollback') or 'stop before execution')}",
            f"<b>Binding:</b> <code>{esc(card.get('rule_key') or 'unknown')}</code>",
            "<i>Выбор: APPROVE | REJECT | CHANGE &lt;условие&gt;</i>",
        ])

    @staticmethod
    def event_text(payload: dict) -> str:
        """v1.2.14: non-approval significant events (deny/loop/rollback) as a
        compact HTML card. The former json.dumps(indent=2) dump was unreadable
        in TG and repeated identical noise per counter change."""
        esc = _escape
        decision = str(payload.get("decision") or "deny")
        icon = "🚫" if decision == "deny" else "🟠"
        lines = [
            f"{icon} <b>{esc(str(payload.get('rule_id') or decision).upper())}</b>",
            f"👁 <b>Задача:</b> <code>{esc(str(payload.get('task_id') or 'unknown'))}</code>"
            + (f" · доска <code>{esc(str(payload['board']))}</code>" if payload.get("board") else ""),
        ]
        reason = payload.get("reason")
        if reason:
            lines.append(f"<b>Причина:</b> {esc(str(reason))}")
        action = payload.get("action")
        if action:
            lines.append(f"<b>Действие:</b> <code>{esc(str(action))}</code>")
        snapshot = payload.get("budget_snapshot") or {}
        used, limits = snapshot.get("used") or {}, snapshot.get("limits") or {}
        if used and limits:
            spent = ", ".join(
                f"{esc(str(metric))} {int(used.get(metric, 0))}/{int(limits[metric])}"
                for metric in sorted(limits)
                if isinstance(limits.get(metric), int)
            )
            if spent:
                lines.append(f"📊 <b>Бюджет:</b> <i>{spent}</i>")
        return "\n".join(lines)

    def expire_closed_approvals(self, store: PolicyStore, *, limit: int = 50) -> int:
        """v1.2.14: sweep pending approval bindings through the live board.

        A binding whose card is provably CLOSED (done/archived/superseded)
        can never be consumed again, so it is written off as ``expired`` —
        never approved/rejected (that stays the owner's decision) and never
        silently deleted (the row keeps its audit trail). Unresolvable or
        board-less legacy rows are left pending: without live evidence a row
        must not be expired. Bounded by ``limit`` per drain tick."""
        expired = 0
        status_cache: dict[tuple[str, str], str | None] = {}
        for row in store.pending_approval_bindings()[:limit]:
            board = str(row["board"] or "")
            task_id = str(row["task_id"] or "")
            if not board or not task_id:
                continue
            binding = (board, task_id)
            if binding not in status_cache:
                status_cache[binding] = self.live_task_status(board, task_id)
            status = status_cache[binding]
            if status is not None and status in self.CLOSED_TASK_STATUSES:
                if store.expire_approval(str(row["rule_key"]), "drain", f"task_status:{status}"):
                    expired += 1
        return expired

    def drain_company(self, store: PolicyStore, *, profile: str = "company", batch_limit: int = 20) -> int:
        """Deliver active task-bound alerts in one bounded bot turn.

        Every row is claimed atomically before processing. Before Bot Chat sees
        any row, the projector reads its exact board/task through the public
        Kanban CLI. Closed tasks are resolved as ``suppressed`` with an audit
        reason; malformed/unresolvable rows are released pending and never
        become synthetic alerts. The live status cache bounds duplicate logical
        events to one read per exact board/task binding.
        """
        claimed = store.claim_pending_notifications(batch_limit)
        if claimed is None:
            return 0
        claim_token, rows = claimed
        status_cache: dict[tuple[str, str], str | None] = {}
        active_event_ids: list[str] = []
        sections: list[str] = []
        for row in rows:
            event_id = str(row["event_id"])
            try:
                payload = json.loads(row["payload_json"])
            except (TypeError, json.JSONDecodeError):
                store.release_notification_claim(claim_token, [event_id])
                continue
            if not isinstance(payload, dict):
                store.release_notification_claim(claim_token, [event_id])
                continue
            binding = self.notification_binding(payload)
            if binding is None:
                store.release_notification_claim(claim_token, [event_id])
                continue
            if binding not in status_cache:
                status_cache[binding] = self.live_task_status(*binding)
            status = status_cache[binding]
            if status is None:
                store.release_notification_claim(claim_token, [event_id])
                continue
            if status in self.CLOSED_TASK_STATUSES:
                store.suppress_claimed_notification(claim_token, event_id, f"task_status:{status}")
                continue
            if payload.get("decision") == "approval_required":
                sections.append(self.approval_text(payload))
            else:
                # v1.2.14: compact HTML card instead of a raw json.dumps dump.
                sections.append(self.event_text(payload))
            active_event_ids.append(event_id)
        if not active_event_ids:
            return 0
        text = "\n\n---\n\n".join(sections)
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as handle:
                handle.write(text)
                temp_path = Path(handle.name)
        except OSError:
            store.release_notification_claim(claim_token, active_event_ids)
            return 0
        try:
            command = [
                "hermes", "-p", profile, "chat", "--in", "~", "-c", "Bot Chat",
                "--create-if-missing", "-Q", "--max-turns", "1", "--query-file", str(temp_path),
            ]
            try:
                result = self.runner(command, self.DELIVERY_TIMEOUT_SECONDS)
            except (subprocess.TimeoutExpired, OSError, subprocess.SubprocessError):
                store.release_notification_claim(claim_token, active_event_ids)
                return 0
            if result.returncode != 0:
                store.release_notification_claim(claim_token, active_event_ids)
                return 0
            return store.mark_claimed_notifications_sent(claim_token, active_event_ids)
        finally:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
