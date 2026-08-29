from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

Decision = Literal["allow", "deny", "approval_required"]


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    decision: Decision
    rule_id: str
    reason: str
    task_id: str
    project: str
    profile: str
    action: str
    target: str
    args_hash: str
    timestamp: str
    budget_snapshot: dict[str, Any]
    approval_card: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
