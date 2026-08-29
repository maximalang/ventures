from __future__ import annotations

import re
from pathlib import Path

REQUIRED_APPROVAL_PHRASES = {
    "deploy_external_runtime": r"production/staging deploy|external runtime",
    "public_outreach_or_publication": r"публичн|рассыл|реклам|outreach",
    "payments_subscriptions_or_budget": r"расход|подпис|плат[её]ж|бюджет",
    "destructive_delete_cleanup_or_migration": r"удален|migration|cleanup",
    "rewrite_history": r"rewrite history",
    "protected_branch_push_or_merge": r"merge/push.*main|protected branch",
    "new_credentials_or_permissions": r"credentials/permissions",
    "security_or_privacy_change": r"security/privacy",
    "private_to_public": r"private.*public",
}


def approval_drift(root: str | Path, config: dict) -> list[str]:
    root = Path(root)
    approvals = (root / "APPROVALS.md").read_text(encoding="utf-8")
    configured = set(config["policy_rules"]["approval_required"])
    problems: list[str] = []
    for rule, pattern in REQUIRED_APPROVAL_PHRASES.items():
        if rule not in configured:
            problems.append(f"config missing rule: {rule}")
        if not re.search(pattern, approvals, re.I):
            problems.append(f"APPROVALS.md missing policy phrase for: {rule}")
    return problems
