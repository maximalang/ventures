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
    def __init__(self, runner: Runner = subprocess_runner):
        self.runner = runner

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
        """Deliver pending notifications in ONE bounded bot turn.

        The batch is atomically claimed (claim_token) so concurrent drains
        cannot duplicate it; a timeout or failed turn releases the claim and
        the rows stay pending for the next cycle. Delivery acceptance is a
        single exit-code check, not full agent-turn completion.
        """
        claimed = store.claim_pending_notifications(batch_limit)
        if claimed is None:
            return 0
        claim_token, rows = claimed
        event_ids = [str(row["event_id"]) for row in rows]
        sections: list[str] = []
        for row in rows:
            payload = json.loads(row["payload_json"])
            if payload.get("decision") == "approval_required":
                sections.append(self.approval_text(payload))
            else:
                sections.append(json.dumps(payload, ensure_ascii=False, indent=2))
        text = "\n\n---\n\n".join(sections)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as handle:
            handle.write(text)
            temp_path = Path(handle.name)
        try:
            command = [
                "hermes", "-p", profile, "chat", "--in", "~", "-c", "Bot Chat",
                "--create-if-missing", "-Q", "--max-turns", "1", "--query-file", str(temp_path),
            ]
            try:
                result = self.runner(command, 15)
            except subprocess.TimeoutExpired:
                store.release_notification_claim(claim_token, event_ids)
                return 0
            if result.returncode != 0:
                store.release_notification_claim(claim_token, event_ids)
                return 0
            return store.mark_claimed_notifications_sent(claim_token, event_ids)
        finally:
            temp_path.unlink(missing_ok=True)
