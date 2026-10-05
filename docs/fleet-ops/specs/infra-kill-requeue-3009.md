# SPEC — infra-kill requeue (terminal_worker_reaped must not crash→triage)

## Проблема (подтверждена evidence 30.09)
Ночной gateway-рестарт (04:00, nightly update drain: `taskkill /T` на fleet-worker'ах)
убивает in-flight kanban-воркеров. Диспетчер помечает run как `crashed`
(событие `terminal_worker_reaped`, «pid N not alive»), инкрементирует
`consecutive_failures`, и после max_retries(2) карта падает в `triage`, откуда
НЕ восстанавливается автоматически (specify — ручной).

Evidence: рестарт 2026-09-21 04:00 («Received UNKNOWN as a planned gateway stop —
exiting cleanly», cold boot 04:07) осиротил 3 карты в один момент:
- rr-team t_62fd4ed9 (@tech) — terminal_worker_reaped, ~224h в triage
- rr-team t_e232b78a (@tech) — terminal_worker_reaped, ~224h
- fleet-ops t_a1565747 (@tech) — terminal_worker_reaped, ~225h
`reconcile_orphans=True` (одобрено владельцем 18.09) их НЕ подобрал: к моменту
рестарта воркеры уже были terminal (exited), т.е. это «dead worker reap», а не
«live orphan reconcile».

Существующий корректный прецедент: rate_limited-путь «requeued WITHOUT counting
a failure» (kanban_db_dispatch.py) и `infrastructure_cooldown` для spawn_failed
с флагом infrastructure. Infra-kill по drain НЕ пользуется ни тем, ни другим.

## Deliverable
Когда воркер умирает от ИНФРАСТРУКТУРНОГО события (gateway drain/restart,
SIGTERM/taskkill от nightly update, terminal_worker_reaped без in-band провала
задачи), run классифицируется как infra-interruption:
- карта REQUEUE (ready/todo по dependency-состоянию), НЕ crashed;
- `consecutive_failures` НЕ инкрементируется;
- карта НЕ падает в triage из-за infra-kill.

Настоящий crash задачи (worker сам упал на своём коде/баге, не от drain)
ДОЛЖЕН по-прежнему считаться crashed и идти к breaker'у — не ослаблять.

## Acceptance (измеримо)
1. Unit/integration-тест: симуляция terminal_worker_reaped с infra-признаком →
   карта остаётся ready/todo, consecutive_failures не растёт, triage не случается.
2. Тест: genuine crash (non-infra) → по-прежнему crashed + failure counted (регресс-guard).
3. pytest/target-сьют зелёные на exact head; вывод тестов в evidence.
4. Критерий различения infra-kill vs genuine-crash документирован (по какому полю/
   метаданным run определяется infra-признак: drain-метка, сигнал, exit-контекст).

## Границы / bans
- НЕ трогать credential pool / auth / model routing.
- НЕ ослаблять детекцию настоящих crash'ей и breaker (max_retries).
- НЕ менять live-конфиги; работа в git worktree → PR (consumer/merge отдельной卡).
- Read-only диагностика live-состояния; никакого force-claim/прямых DB-мутаций.

## Anchor / routing
- Целевой репо: hermes-agent (dispatcher/supervisor: kanban_db_dispatch.py,
  local_runtime/supervisor.py — где terminal_worker_reaped → outcome).
- exact head выводит воркер из live checkout; GO-якорь decision:company=go
  ставится компанией на merge-стадии (consumer-карта), НЕ в этой карте.
- assignee: tech. Независимый reviewer: qa (exact-head, author≠reviewer).

## Связь
- Родственный фикс (уже в пути): blocker_auth TTL fc2fa0c53f / retest t_9c461308 —
  ТА ЖЕ тема «infra/quota-смерть воркера не должна вечно парковать карту».
- Эта карта = drugaя половина: infra-kill на этапе dispatch/reap.
