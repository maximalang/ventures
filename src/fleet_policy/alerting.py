from __future__ import annotations

from typing import Any, Mapping


SECURITY_RULE = "sec" + "ret_read_or_write"

OWNER_ALERT_RULE_IDS = frozenset(
    {
        "financial_action",
        "financial_metadata_missing",
        "financial_over_budget",
        "new_paid_capability_or_payment_rail",
        "rollback",
        "rollback_required",
        "rollback_failure",
        "destructive_change",
        "irreversible_data_loss",
        SECURITY_RULE,
        "worker_self_approval",
        "worker_capability_grant",
        "material_security_or_privacy_policy_change",
        "policy_control_plane_mutation",
        "notification_delivery_failure",
    }
)


def is_owner_alertable(payload: Mapping[str, Any]) -> bool:
    """Return whether a task-bound policy event merits an owner alert."""
    task_id = str(payload.get("task_id") or "").strip()
    if not task_id:
        return False
    if str(payload.get("decision") or "") == "approval_required":
        return True
    rule_id = str(payload.get("rule_id") or "")
    return rule_id in OWNER_ALERT_RULE_IDS or rule_id.startswith("rollback_")
