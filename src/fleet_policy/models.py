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
    # v1.2.25: единая таблица маршрутов продолжения (источник правды; канон 17.09
    # «deny = пауза, не стоп»). who = worker (воркер продолжает сам в этом же
    # ране — карта НЕ паркуется) | company | owner.
    "worker_code_execution": (
        "инструмент запрещён у воркеров; используй read_file/search_files/terminal; повтори вызов в этой же форме",
        "worker",
    ),
    "evidence_gate_missing": (
        "собери evidence по чек-листу карты и выложи канонический однострочный маркер отдельным комментарием (gate:X=pass + head), затем повтори",
        "worker",
    ),
    "missing_or_unknown_task_type": (
        "первая строка тела карты должна быть 'task_type: research|code|review|ops' — запроси company-правку тела и повтори",
        "company",
    ),
    "task_type_conflict": (
        "у карты конфликт маркеров типа — только company переносит работу на новую карту (литерал тега в теле/комментарии неисправим)",
        "company",
    ),
    "budget_exhausted": (
        "hard-бюджет исчерпан; продолжение = новый scoped-ран по контракту компании (самовозобновление запрещено)",
        "company",
    ),
    "approval_binding_missing": (
        "запроси binding через штатный approval-поток; самому себе binding выдать нельзя",
        "company",
    ),
    "same_failure_loop": (
        "тот же сбой 3 раза — не варьируй вызов; поменяй подход или верни карту компании с diagnosis",
        "worker",
    ),
    "identical_call_loop": (
        "идентичный вызов повторен — измени аргументы по смыслу задачи или верни карту компании с diagnosis",
        "worker",
    ),
    "policy_control_plane_mutation": (
        "правка самой политики запрещена; оформи отдельную tech-карту с диагнозом",
        "company",
    ),
    "worker_self_approval": (
        "сам себе печать ставить нельзя; запроси правомочного автора (gate_authors) комментарием на карте",
        "company",
    ),
    "secret_read_or_write": (
        "секреты вне правил; стоп, не повторяй вызов, пометь карту needs_input",
        "owner",
    ),
    "gate_forgery": (
        "подделка гейта; стоп; разбор компанией по event-log",
        "company",
    ),
}


def remediation_for(rule_id: str) -> dict[str, str] | None:
    """Маршрут продолжения для rule_id; None = класс без известного маршрута."""
    route = REMEDIATIONS.get(str(rule_id or ""))
    return {"how": route[0], "who": route[1]} if route else None
