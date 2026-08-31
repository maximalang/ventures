from __future__ import annotations

import json
import subprocess
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path

from .storage import PolicyStore

Runner = Callable[[Sequence[str], int], subprocess.CompletedProcess[str]]


def subprocess_runner(command: Sequence[str], timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(command), check=False, capture_output=True, text=True, timeout=timeout, shell=False)


class HermesProjector:
    CLOSED_TASK_STATUSES = frozenset({"done", "archived", "superseded"})
    LOOKUP_TIMEOUT_SECONDS = 5

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
        card = payload.get("approval_card") or {}
        return "\n".join([
            "APPROVAL REQUIRED",
            f"Проект/задача: {card.get('project_task', 'unknown')}",
            f"Действие: {card.get('action', payload.get('action', 'unknown'))}",
            f"Зачем: {card.get('why', 'policy gate')}",
            f"Evidence: {card.get('evidence', 'unavailable')}",
            f"Риск: {card.get('risk', payload.get('reason', 'unknown'))}",
            f"Rollback: {card.get('rollback', 'stop before execution')}",
            f"Binding: {card.get('rule_key', 'unknown')}",
            "Выбор: APPROVE | REJECT | CHANGE <условие>",
        ])

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
                sections.append(json.dumps(payload, ensure_ascii=False, indent=2))
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
                result = self.runner(command, 15)
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
