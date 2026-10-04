# Company exact-head decision — dots-hermes-standard-20261004

decision: company=go
head: 2fedef53211adc07445caee7d4d3ef3cac4df5e7544508ca35a26e040774600e
task_type: ops
date: 2026-10-04

## Что решено

Компания снимает удержание контролируемого применения (карта `t_63f62c17`, assignee
`operations`) и разрешает его исполнение строго по `APPLY-SPEC.md`:
12 целевых профилей, один hands-writer, native review на той же карточке.

## Основание (evidence chain)

1. Независимая семантическая приёмка source-candidate завершена: run2319,
   карточка `t_d090b4ff`, машинный вердикт `typed_verdict_word=PASS`,
   M01–M17 = 17/17 confirmed, S01–S17 = 17/17 consistent.
2. Первоначальный машинный receipt `QA-CANDIDATE.json` был непотребляем
   (дубли ключей: пополненные секции + устаревшие заглушки; доказано
   `QA2319-CONSUMER-CHECK.json`, `CONSUMER-DEFECT-ANALYSIS.json`).
3. Исправление исполнено независимой QA на карте `t_29903deb` (run 44,
   outcome=completed): `QA-CANDIDATE-FIXED.json`
   SHA256 = `ed4d00c92f5b5574f22980f7b37db2c5d45008113e5e7efc192b6412f7ca75d3`,
   5929 bytes; оригинал сохранён без изменений.
4. Consumer-приёмка компании 8/8 (`CONSUMER-ACCEPTANCE-RECEIPT.json`
   SHA256 = `30a1e12ed2eb612298f1c6ade32981934811d7fa934e14eaf928af7d4b14868d`):
   нет дублей ключей, PASS, 17/17 + 17/17, независимость линий (main_pair_overlap=false),
   head вшит, integrity 19/19, штампы подтверждены независимым readback
   (`QA2319-NATURAL-LINEAGE.json`: 60 main-вызовов glm-5.3/zai сессии
   20261004_030640_cd335f).
5. Биндинг предмета не изменился: SUBJECT.json / REFERENCE-CANDIDATE.md /
   HOOK-CANDIDATE.md / BASELINE.json — хэши совпали с замороженными.

## Границы

- Применение — только `REFERENCE-CANDIDATE.md` + `HOOK-CANDIDATE.md` в точные
  12 целей; scoped additive; прежние корни и чужие файлы не трогать.
- Никакой второй schema/очереди/координатора; канон — существующий workflow.
- Никаких платных обязательств, model/provider routing, live-инференса.

## Rollback

При расхождении с exact-head или отказе верификатора — stop, отчёт на карте,
state откатывается к pre-apply; `REPORT.md` помечается обратно в hold.
