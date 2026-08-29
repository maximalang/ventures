from __future__ import annotations

import re
from pathlib import Path

REQUIRED_APPROVAL_PHRASES = {
    "mass_outreach_or_bulk_messaging": r"mass outreach|bulk messaging",
    "financial_over_budget": r"exceeds.*limit|30,000",
    "new_paid_capability_or_payment_rail": r"paid capability|payment rail",
    "phone_kyc_domain_or_bank_owner_action": r"KYC|phone verification|domain or bank ownership",
    "legal_or_material_reputation_risk": r"legal|reputational",
    "ownership_or_root_access_change": r"ownership|root/admin",
    "irreversible_data_loss": r"irreversible data loss",
    "material_security_or_privacy_policy_change": r"security.*privacy|privacy.*security",
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
