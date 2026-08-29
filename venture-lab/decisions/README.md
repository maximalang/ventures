# Venture Lab — Decision log

Каталог решений проекта Venture Lab. Формат каждого файла: **ID / date / status / context / decision / evidence / consequences** (ADR-подобный, по `OPERATING_SYSTEM.md` каждый проект обязан вести `decisions/`).

## Правила

- Один файл — одно решение; номера сквозные (`0001`, `0002`, ...), не переиспользуются.
- Решение не переопределяется задним числом: изменение решения = новый файл с `Supersedes`.
- Evidence-ссылки обязательны: Kanban task id, commit SHA, путь к артефакту или URL.
- Статусы: `Accepted` → `Superseded by 00XX` | `Deprecated`.

## Реестр

| ID | Дата | Статус | Решение |
|---|---|---|---|
| [0001](0001-h1-needs-evidence-field-gate.md) | 2026-08-29 | Accepted | Discovery 2 H1: NEEDS-EVIDENCE — field validation gate, build запрещён до полного GO |

Согласовано с `../CHARTER.md` (Current gate), `../STATE.md` (Phase/objective), root `PORTFOLIO.md` (фаза Venture Lab = Discovery, следующий gate = GO/NO-GO), `OPERATING_SYSTEM.md`, `APPROVALS.md` (publication/outreach/deploy/расходы вне scope; работа только в `codex/*`).
