# Project State — Venture Lab

## Phase
Discovery

## Current objective
Собрать field evidence по H1 (Custom GPT Escape & Compliance) до рекомендации GO/NO-GO в рамках гейта NEEDS-EVIDENCE (decisions/0001-h1-needs-evidence-field-gate.md): проблемные интервью, предзаказы/LOI, usage signal по venture-lab/sprint-H1-tracker-2026-08-29.md.

## Constraints
- Один новый venture одновременно.
- До 5 параллельных workers; squad 2–5 ролей.
- Build только после GO.

## Active risks/blockers
- Discovery 1 завершена 2026-08-29: реестр 7 гипотез, shortlist 3 (H1 Custom GPT Escape & Compliance, H2 Agent Cost Guard, H3 Art.50 Transparency Scanner) — venture-lab/discovery-2026-09.md.
- Review product 2026-08-29: shortlist подтверждён без изменений (H1 CEC → Discovery 2); вердикт и замечания — в Kanban t_a136511b (review approved, коммит ревью в codex/discovery-2026-09).
- Discovery 2 H1, линза research завершена 2026-08-29: платформа подтвердила/усилила «why now» (16.08 закрытие создания GPT на personal, 30.11 shutdown Agent Builder, стандарт Agent Plugins/Skills 06.08); wedge «конвертация» обесценен (бесплатный gpt2skill.com + вероятная нативная GPT→Skills конвертация OpenAI, leak 2026-08-17); v1 «GPT Estate Manager» (аудит/инвентарь/экспорт/отчёт рисков) — venture-lab/discovery2-H1-research-2026-08-29.md, коммит f1b45ff.
- Discovery 2 H1, все 4 линзы завершены 2026-08-29: product t_af24b763 (NEEDS-EVIDENCE), critic t_999cf8dd (NEEDS-EVIDENCE), finance t_05e5f18f (NEEDS-EVIDENCE), sales t_d17fba46 (GO, только как $0-полевой тест).
- **Вердикт Discovery 2 H1: NEEDS-EVIDENCE (2026-08-29, агрегация t_f3573ec1)** — build запрещён до гейта. Условие GO: ≥10 проблемных интервью с ≥3 подтверждениями боли на сегмент + ≥3 предзаказа/LOI + ≥50 просканированных портфелей или ≥30 регистраций. Kill-критерии: шип нативной GPT→Skills конвертации OpenAI; <30% интервью с подтверждением боли; прямой конкурент-автоматизация в S2. Compliance-требование к v1: user-authorized экспорт-путь (ToS-запрет «programmatically extract», S21). Артефакты: venture-lab/discovery2-H1-aggregate-2026-08-29.md (сквозной Source register 18 источников, verify 19/19 PASS) + venture-lab/evidence-discovery2-H1/ (14 снапшотов дословных цитат + verify_citations.py).
- Спринт H1 открыт 2026-08-29 (карточка t_e56b725d): tracking-инфраструктура venture-lab/sprint-H1-tracker-2026-08-29.md + 2 CSV (интервью/signals) + evidence e23–e24. День 0: kill K1 НЕ сработал (в release notes/help center за август 2026 конвертации нет; сторонний блог про «one-click migrate» классифицирован LOW/unverified), но риск эскалировал — OpenAI Academy (last updated 2026-08-27, e23) официально подтвердила роадмап конвертации GPT→Skills без даты. Kill K3 прелюминарно не сработал (один поиск — слабое негативное доказательство, повтор на неделе 1).
- Блокеры спринта: email-секвенция и посты — user-approval по APPROVALS.md; промо-лендинг — approval публикации + плейсмента ($0-варианты не верифицированы); WCMS-метод — RESOLVED 2026-08-29 (карточка t_9b0bda2c): метрика переименована в «consented GPT portfolio inventory scan», протокол и правила счёта — venture-lab/sprint-H1-g3-portfolio-scan-protocol-2026-08-29.md, raw-регистр — venture-lab/sprint-H1-scans-2026-08-29.csv (seed-строки = примеры протокола §5, не полевые данные); остаточный блокер G3 — продвижение скана (approval B1/B2). Полевые цифры не двигаются до approvals: 0 интервью / 0 completed scans / 0 регистраций на день 0.

## Next action
Разблокировать спринт H1: (1) user-approval на email-секвенцию 7 писем S1/S2 и посты-кейсы (APPROVALS.md, APPROVAL REQUIRED в Bot Chat компании), (2) approval публикации промо-лендинга + выбор $0-плейсмента, (3) approval на продвижение consented portfolio-scan — метод определён (t_9b0bda2c): venture-lab/sprint-H1-g3-portfolio-scan-protocol-2026-08-29.md, сбор полевых данных только после approvals, (4) E4-проверка «migrate GPT» в реальном ChatGPT-аккаунте (10 мин). Параллельно: еженедельный kill-мониторинг K1 (проверка №1 — 2026-08-29, не сработал; снапшоты e23–e24) и повторная S2-конкурентная проверка. Полевые цифры → venture-lab/sprint-H1-tracker-2026-08-29.md; агрегация результатов спринта — отдельной карточкой (GO не объявляется на этом уровне).
