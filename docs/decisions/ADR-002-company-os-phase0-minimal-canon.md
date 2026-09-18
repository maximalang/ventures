# ADR-002: Company OS Phase 0 — минимальный канон (task contract, recovery, outcome, финансы, rollback)

- Статус: accepted — bounded pilot Phase 0–1
- Дата: 2026-09-18
- Owner: operations
- Источник решения: `decision:company=go` по `portfolio/t_e691397b` (adversarial verdict v1). GO только для обратимого Phase 0–1 bounded pilot; fleet-wide автоматические переходы — NO-GO до независимого QA контроллера и readback backlog-reconciliation.

## Контекст

Снимок досок зафиксировал 60 blocked / 54 triage, 46 blocked старше 24ч, 34/60 с признаками уже выполненной или проверенной работы: control loop обрывался после detect/classify. Полный task contract из synthesis оказался слишком тяжёл для всех карточек. Требуется минимальный канон, закрывающий эти разрывы без live-изменений политики.

## Решение

1. **Минимальный контракт задачи**: owner, deliverable, acceptance/evidence, dependency, risk/rollback, next owner — обязательны для каждой карты; hypothesis-поля только для bet/experiment-карт (см. `OPERATING_SYSTEM.md`).
2. **Таксономия recovery**: transient / dependency / needs_input / capability / policy-false-positive с разрешёнными действиями на класс. Автоматика не снимает safety/owner-only блоки; resume при подтверждённом read-only false positive — одна попытка, readback, затем recovery review.
3. **Outcome vs output**: прогоны, тики и отчёты — evidence здоровья процесса, не прогресс. Закрытие фазы/ставки требует ≥1 verified outcome или явного `outcome=null` с причиной.
4. **Financial disclosure**: scope/period/source обязательны; confirmed revenue, refunds и estimated usage cost без evidence записываются как `null` + причина, не 0; gross revenue не представляется без costs и null-reasons.
5. **Rollback**: путь отката фиксируется до state-changing действия; kill switch немедленно выключает `--apply` при bypass любого fence (secret/self-approval/irreversible/spend/release), dry-run сохраняется; откат канона = git revert PR.

## Scope и ограничения

- Docs-only: никаких runtime/policy-активаций и изменений поведения fleet-policy в этом PR.
- Материальная активация (контроллер `--apply`, backlog reconciliation) остаётся за независимым QA PR41 и release gates — вне этого ADR.

## Kill criteria

- Любой bypass safety fence (secret, self-approval, irreversible, spend, release) — немедленное отключение автоматики.
- Рост median lead time >20% два цикла подряд без снижения defect escape — откат обязательных полей контракта.

## Rollback

`git revert` этого PR. Изменение обратимо: затронуты только канонические .md-документы, live-системы не изменены.
