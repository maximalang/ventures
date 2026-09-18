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
    # Canonical continuation route for a denied action; absent on allow.
    remediation: dict[str, str] | None = None

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if not d.get("remediation"):
            d.pop("remediation", None)
        return d


REMEDIATIONS: dict[str, tuple[str, str]] = {
    "evidence_gate_missing": ("collect required evidence, then retry", "worker"),
    "missing_or_unknown_task_type": ("specify a valid task type", "company"),
    "approval_binding_missing": ("obtain the exact approval binding", "company"),
    "secret_read_or_write": ("request owner-bound handling", "owner"),
    "same_failure_loop": ("change the approach; do not repeat the failed call", "worker"),
    "identical_call_loop": ("change the call meaningfully; do not repeat it", "worker"),
    "budget_exhausted": ("start a new scoped run", "company"),
}


def remediation_for(rule_id: str) -> dict[str, str] | None:
    route = REMEDIATIONS.get(str(rule_id or ""))
    return {"how": route[0], "who": route[1]} if route else None
