# ADR-0001: Discovery 2 H1 — вердикт NEEDS-EVIDENCE, field validation gate

## ID
0001

## Date
2026-08-29

## Status
Accepted

## Context
Discovery 2 по гипотезе H1 «Custom GPT Escape & Compliance» завершён всеми четырьмя линзами (2026-08-29, агрегация — Kanban t_f3573ec1, артефакт `../discovery2-H1-aggregate-2026-08-29.md`, коммит fc50374b249711da82fb0640d55bb524d5ea69da):

- product t_af24b763 — NEEDS-EVIDENCE;
- critic t_999cf8dd — NEEDS-EVIDENCE;
- finance t_05e5f18f — NEEDS-EVIDENCE;
- sales t_d17fba46 — GO только как $0-полевой тест.

Сходящийся вердикт агрегации: **NEEDS-EVIDENCE** — evidence для GO недостаточен, но и оснований для NO-GO нет. Спринт field validation открыт (Kanban t_e56b725d); на день 0 полевые цифры нулевые, outreach/landing-гейты стоят на user-approval по `APPROVALS.md`.

## Decision
1. Фаза остаётся **Discovery**; current gate Venture Lab = **Discovery 2 H1 field validation, вердикт NEEDS-EVIDENCE**.
2. **Build запрещён** до прохождения полного GO gate.
3. Условия GO: ≥10 проблемных интервью с ≥3 подтверждениями боли на сегмент + ≥3 предзаказа/LOI + ≥50 просканированных портфелей или ≥30 регистраций.
4. Kill-критерии: шип нативной GPT→Skills конвертации OpenAI; <30% интервью с подтверждением боли; прямой конкурент-автоматизация в S2.
5. Compliance-требование к v1 (если GO): user-authorized экспорт-путь (ToS-запрет «programmatically extract», evidence S21).

## Evidence
- Агрегация: t_f3573ec1 → `../discovery2-H1-aggregate-2026-08-29.md` (сквозной Source register 18 источников; grounded-citations verify 19/19 PASS), commit fc50374b249711da82fb0640d55bb524d5ea69da.
- Дословные снапшоты: `../evidence-discovery2-H1/` (14 снапшотов + `../evidence-discovery2-H1/verify_citations.py`, отчёт `../evidence-discovery2-H1/verify-report.md`).
- Линзы: t_af24b763 (product), t_999cf8dd (critic), t_05e5f18f (finance), t_d17fba46 (sales).
- Спринт field validation: t_e56b725d → `../sprint-H1-tracker-2026-08-29.md` (+ `../sprint-H1-interviews-2026-08-29.csv`, `../sprint-H1-signals-2026-08-29.csv`); kill-check №1 2026-08-29: K1 не сработал, снапшоты e23–e24.
- State: `../STATE.md` (Phase Discovery, objective — сбор field evidence), `../CHARTER.md` (Current gate).

## Consequences
- GO/смена фазы этим файлом не объявляются: фаза Discovery сохраняется, строка Venture Lab в root `PORTFOLIO.md` (фаза Discovery, следующий gate — GO/NO-GO по evidence) остаётся валидной.
- Полевые метрики фиксируются только в sprint-трекере t_e56b725d; агрегация результатов спринта — отдельной карточкой.
- Публикация/outreach/deploy/расходы не входят в это решение и требуют отдельного user-approval по `APPROVALS.md`.
- При срабатывании kill-критерия или по результатам агрегации спринта решение пересматривается новым файлом (Supersedes), а не правкой этого.
