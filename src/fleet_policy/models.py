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
    # Машиночитаемый маршрут продолжения (17.09, канон «deny = пауза, не стоп»):
    # {"how": str, "who": "worker"|"company"|"owner"}. how — что сделать для
    # продолжения; who — кому это под силу. Отсутствует (None) у allow.
    remediation: dict[str, str] | None = None

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Обратная совместимость: потребители v1.x не знают поле — держим его
        # только в denial-payload, у allow оставляем None (не сериализуем шум).
        if not d.get("remediation"):
            d.pop("remediation", None)
        return d


# Единая таблица маршрутов продолжения (источник правды; 17.09).
# key = rule_id, value = (how, who). how — конкретный следующий шаг;
# who = worker (воркер продолжает сам в этом же ране) | company | owner.
REMEDIATIONS: dict[str, tuple[str, str]] = {
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
        "у карты конфликт маркеров типа — только company переносит работу на новую карту (litерал тега в теле/комментарии неисправим)",
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
    found = REMEDIATIONS.get(str(rule_id or ""))
    if not found:
        return None
    return {"how": found[0], "who": found[1]}
