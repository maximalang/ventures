# FINAL-ACCEPTANCE — Dots ↔ Hermes compatibility standard (2026-10-04)

decision: company=accept
head: 2fedef53211adc07445caee7d4d3ef3cac4df5e7544508ca35a26e040774600e
task_type: ops

## Итог

Внешняя механика OpenAI Dots НЕ переносилась как отдельный workflow. Она
сравнена поэлементно с 17 существующими механиками Hermes (M01–M17) и
стандартизирована в существующем workflow:

1. **Сравнение (без конфликтов/дублей).** COMPANY-MATRIX.md: для каждого
   внешнего механизма зафиксрованы официальный Hermes-механизм, существующий
   fleet-владелец, статус (REUSE_CANON / TRANSLATE / REJECT), и решение.
   Никакая вторая schema, очередь, координатор или обязательный
   responsibility-шаблон не создаются; канонические процедуры остаются у
   текущих владельцев (kanban-card-authoring, company-os, sdlc-review,
   fleet-skills-rollout, Fleet Policy).
2. **Стандартизация на существующем workflow.** Единственный артефакт на
   профили — одна reference (`references/dots-operating-method.md`, переводчик
   к существующим правилам) и один загрузочный hook-абзац в SKILL.md.
   Процедура scoped-additive rollout стандартизирована в самом
   `fleet-skills-rollout` (PROCEDURE-DELTA.md) — то есть стандарт живёт в
   существующем скилле, а не рядом с ним.
3. **Приёмка цепочкой независимых линий.**
   - Source-candidate: QA run2319 (glm-5.3/zai) — typed PASS, M01–M17 17/17,
     S01–S17 17/17; integrity 19/19. Дефект машиночитаемого receipt
     (дубли ключей) доказан компанией (QA2319-CONSUMER-CHECK.json,
     CONSUMER-DEFECT-ANALYSIS.json) и исправлен независимой QA-картой
     t_29903deb (run44): QA-CANDIDATE-FIXED.json
     sha256=ed4d00c92f5b5574f22980f7b37db2c5d45008113e5e7efc192b6412f7ca75d3;
     consumer-приёмка компании 8/8 (CONSUMER-ACCEPTANCE-RECEIPT.json).
   - Company GO exact-head: COMPANY-GO.md.
   - Apply: operations run2320 (kimi-k3/custom) — 12/12 целей,
     APPLY-VERIFY 98/98, APPLY-LOADER 12/12.
   - Финальная приёмка установки: QA run2321 (glm-5.3/zai, 21/21 main-штампов)
     — FINAL-QA typed PASS, собственная батарея 286/286, loader-probe 12/12,
     попарных пересечений линий author/issuer/reviewer нет.
   - Company read-only readback живых целей: NATIVE-FINAL-READBACK.json
     12/12 all_ok (reference byte-exact 12/12, hook-параграф встроен 12/12,
     байтов старого hook нет).

## Границы принятых утверждений

- Принято: статическая установка/сравнение/стандартизация. НЕ утверждается:
  будущая «поведенческая послушность» моделей, live runtime-эффекты, stop-
  поведение, экономика.
- Финансовый scope: confirmed revenue=null, refunds=null, incremental paid
  costs=null (платных вызовов не было), new commitments=null, estimated usage
  cost=null — не измерялось; штампы serving ≠ биллинг; это НЕ утверждение
  «0 ₽».
- Owner input не требовался; все операции в пределах существующих мандатов.

## Rollback

12/12 backup-директорий сохранены (own-bytes, проверено батареей QA2321);
прежний стандарт dots-20261003 сохранён byte-equal. Откат = восстановление
before-байтов из backups + снятие hook-абзаца; процедура — APPLY.md.
