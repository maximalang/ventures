# Финальный указатель фазы dots-hermes-standard-20261004

Единственная точка входа по артефактам фазы. Kanban остаётся реестром задач; указатель не создаёт второй очереди или координатора. Принятые артефакты не изменялись.

## Актуальные (принятые)
- `SUBJECT.json` — binding точного документа (head `2fedef53…600e`).
- `REFERENCE-CANDIDATE.md` — принятая компактная reference (установлена на 12 профилях).
- `HOOK-CANDIDATE.md` — принятый условный загрузочный hook (абзац в 12 SKILL.md).
- `BASELINE.json` — замороженный baseline сравнения.
- `QA-CANDIDATE-FIXED.json` — принятый машинный receipt независимой QA (PASS). Потреблять по этому явному имени; внутренние ссылки на `QA-CANDIDATE.json` — исторические, к дефектному оригиналу не следовать.
- `CONSUMER-ACCEPTANCE-RECEIPT.json` — consumer-приёмка исправленного receipt 8/8.
- `COMPANY-GO.md` — exact-head GO.
- `APPLY-VERIFY.json` 98/98 · `APPLY-LOADER.json` 12/12.
- `FINAL-QA.json` (typed PASS) · `QA2321-BATTERY.json` 286/286 · `QA2321-LOADER.json` 12/12 — исторические прогоны, аудитом не перезапускались.
- `NATIVE-FINAL-READBACK.json` — read-only readback живых целей 12/12.
- `FINAL-ACCEPTANCE.md` / `COMPANY-SOURCE-ACCEPTANCE.json` — итоговая приёмка company=accept.
- `REPORT.md` — отчёт фазы «ЗАВЕРШЕНО И ПРИНЯТО» (заморожен).
- `PACKAGE-MANIFEST.json` — только внутри исходного ZIP: 157 payload, манифест сам себя не считает; 158-я запись ZIP — сам манифест.

SHA256 всех перечисленных файлов — в `FINAL-INDEX.json`.

## Историческое (не потреблять как актуальное)
- `QA-CANDIDATE.json` — дефектный оригинал receipt (дубли 4 ключей), сохранён как история дефекта.
- `PRESERVED-QA-2318.json` — снимок остановки run2318.
- `LANE.json` — до-релизный снимок (`release_state=held`); устарел, вытеснен native-состояниями done-карт; это audit-binding, не живое состояние.
- `before/` и `apply-backups/` — снимки/пути отката.

## Доска (task truth)
`fleet-ops`: t_d090b4ff (source QA) done · t_63f62c17 (apply + final QA) done · t_7638de4f (quality audit) done; `default`: t_29903deb (mechanical receipt fix) done.

## Пакеты
- `dots-hermes-standard-20261004.zip` — принятый архив, SHA256 `661c5226…e201`, 158 записей. Не изменялся.
- `dots-hermes-standard-20261004-supplement.zip` — послеаудитная доработка: SHA256 `f82577f3…dfc8`, 35 записей — 34 файла (6 именованных исходников проверок, 24 apply-backups, 4 вспомогательных) + `SUPPLEMENT-MANIFEST.json` с побайтовой сверкой 24 путей отката против `before/`. Закрывает пробел воспроизводимости F02; исходный ZIP не заменяет.

## Аудит качества
`../dots-quality-audit-20261004/`: `REPORT.md` (итог аудита), `INDEPENDENT-REVIEW.md/.json`, `QA-CONSUMER-CHECK.json` + `CONSUMER-LIMITS.md`, `QA-NATIVE-FINAL-READBACK.json`.

Финансовый scope: аудит и доработка fleet-ops, 2026-10-04; источник — локальные проверки и естественные штампы, ledger не читался. Выручка/возвраты/платежи/обязательства: новых нет; оценка стоимости использования не измерялась.
