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
    pattern_category: str = "unknown"
    call_index: int = 0
    #: v1.2.10 item C — set only on the review-probe nonce lane: a stable
    #: per-run identifier proving the refusal is an expected QA artifact,
    #: not a worker failure; the lane never grows loop counters.
    deny_nonce: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
