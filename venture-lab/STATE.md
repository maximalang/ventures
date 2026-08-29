# Project State — Venture Lab

## Phase
Discovery

## Current objective
Сформировать evidence-backed shortlist до 3 идей и провести одну через GO/NO-GO.

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

## Next action
Полевой validation-спринт H1 (2–3 недели, $0 обязательных): 15 интервью (5×S1/S2/S3, product), 7-email sequence (S1/S2, sales — требует user-approval по APPROVALS.md до отправки), промо-лендинг + WCMS-скан (≥50 портфелей или ≥30 регистраций), 3 agency discovery-call (S2, ≥1 LOI) → карточка агрегации результатов спринта принимает GO/NO-GO по гейтам вердикта. Еженедельный мониторинг btibor91/release notes OpenAI до вердикта (kill-фактор S07).
