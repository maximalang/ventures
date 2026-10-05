# Аудит качества Dots ↔ Hermes

## Вывод
Файловая интеграция соответствует принятой дельте на всех 12 профилях. Новой параллельной очереди, координатора или обязательного шаблона не добавлено: изменены прежняя reference и её загрузочный абзац. Однако утверждать «всё без недоработок» нельзя: имеются проблемы полноты воспроизводимого пакета, внутренних ссылок receipt и канонической истории приёмки. Ошибочный reusable lesson о finished-картах точечно исправлен в company.

Предмет — операционная методика, не установка OpenAI Dots, не новый облачный сервис и не grant новых разрешений. Проверено состояние файлов и доказательств; будущие действия агентов, экономическая выгода и реальная eligibility каждого live loader не объявляются проверенными.

## Проверенные факты
- Текущие live file checks: 108/108, 12/12 targets; одна точная новая reference, один новый hook, старый hook отсутствует, остальной корень побайтово сохранён относительно собственного before.
- Исходный document head: `2fedef53211adc07445caee7d4d3ef3cac4df5e7544508ca35a26e040774600e`. Это SHA256 документа SUBJECT, не Git SHA.
- Исходный принятый ZIP: SHA256 `661c522692d2bd9c896a627bfe545531fa69db7c54d2e648e480a337c604e201`, 1309730 B. CRC без ошибок, все 157 payload hashes совпадают. 158 ZIP entries = 157 payload + manifest itself; разница счётчиков не дефект.
- Последняя независимая приёмка исходной установки: native QA run2321, сохранённые 286/286 и isolated loader 12/12. Эти исторические проверки не названы новой батареей этого аудита.
- Native task readback подтверждает исходные две карты на fleet-ops и отдельное receipt-correction дело на default; все done. Прежний `unknown task` не доказывает запрет finished-карт.

## Реальные дефекты / замечания
1. **Неверный learned rule (F01).** В procedural skill ошибочно предписывалось создавать standalone дело после done, поскольку якобы done запрещает comment/parent links. Точный native helper source и контролируемый in-memory fixture опровергают такую общую семантику. Исправлено ТОЛЬКО в active company `exact-head-acceptance-qa`; исходная установка и другие профили не переписаны. Fixture не является live Fleet Policy admission test.
2. **Самодостаточность пакета (F02).** Архив цел по хэшам, но не включает шесть названных исходников/квитанций проверок и 24 документированных `apply-backups` путей. Rollback bytes НЕ утрачены: в `before/` лежат побайтово идентичные 24 альтернативы. Нужны supplement + явная карта соответствия, а не молчаливое изменение принятого ZIP.
3. **Неверная самоидентификация receipt (F03).** Принятый физический `QA-CANDIDATE-FIXED.json` всё ещё внутри называет `QA-CANDIDATE.json` / this file. Исправленный receipt нормально потребляется по явному принятому пути; автоматическое следование внутренним ссылкам может увести к сохранённому defective original. Историю QA не переписывать; исправлять отдельным final index/provenance.
4. **Разрозненная история приёмки (F04).** QA PASS есть в исходной apply-карте и файлах; final company acceptance осталась в файлах, а не в её треде. Mechanical receipt-fix оказался на default, не fleet-ops. Это traceability gap, а не провал установки или потеря QA. Причина каждого исторического lookup-error полностью не доказана.

### Шесть отсутствующих в ZIP именованных inputs
- `qa2321_battery.py`
- `qa2321_loader.py`
- `QA-CHECKER-RUN2319.py`
- `APPLY-run2320-20261004T012335Z.json`
- `preserved-qa2318/qa_dryrun_12targets.py`
- `preserved-qa2318/qa_dryrun_stage1.json`

## Дубли и мусор
- Инвентаризировано 192 локальных файлов; шесть byte-equal групп, 579689 B (~0.553 MiB) избыточных копий. Большинство — intentional before/apply-backup snapshots и разрешённая профильная репликация. Не обнаружено вторых действующих hook/workflow в проверенной дельте.
- Сохранённый defective `QA-CANDIDATE.json` содержит четыре duplicate keys; исправленный approved receipt duplicate-free. Это история дефекта, не повод удалять original.
- `_company_readback.py` и `_qa_verify.py` — non-final вспомогательные версии, вместе 11733 B; кандидаты для отдельного historical/tools раздела. Место ничтожно; больше пользы от понятного index, чем от удаления.
- `LANE.json` продолжает содержать исходное held-состояние: это audit-binding snapshot, не текущая очередь. Указать дату/supersession в final index. Не синхронизировать файл с живой доской как второй registry.

## Оптимизации: по убыванию полезности
1. **Authoritative final index.** Однозначно разделить accepted current, historical negative/checkpoint и reproduction tools; зафиксировать физический FIXED путь, исходные SHA и связать final acceptance с exact native card/board. Acceptance: все current pointers разрешаются; historical ничего не затёрто.
2. **Reproducibility supplement.** Упаковать шесть пропущенных именованных inputs и документировать 24 before/ ↔ apply-backups альтернативы. Acceptance: named-source closure + byte-verified rollback mapping + CRC/payload SHA. Исходный ZIP сохранить неизменным.
3. **Один компактный реальный smoke-case при естественной работе.** Зафиксировать live selection/eligibility и выполненный исход existing workflow на существующей карте без новой очереди или inference-пробы. Acceptance: реально наблюдаемая загрузка и bounded результат; runtime/стоимость до этого неизвестны. Это предложение следующей проверки, НЕ уже выполненный тест.
4. **Hygiene без разрушения evidence.** Разнести финальные и historical/helpers в index; архивный snapshot оставить. Массовая чистка, новая schema/координатор и whole-skill sync не оправданы.

Уже реализованная компактность: reference сокращена с 12995 до 7821 B (−5174 B, −39.8% байтов). Hook уже условный. Это не измерение токенов, ускорения или денежной экономии.

## Безопасные процедурные поправки этого аудита
- Active company `exact-head-acceptance-qa`: ошибки `unknown task` / `unknown parent task(s)` классифицируются как lookup failures; проверить exact id, explicit board и storage routing, не создавать standalone лишь для обхода ошибки. `PROCEDURE-CORRECTION.json` хранит исходную и исправленную формулировку.
- Active company `fleet-skills-rollout/references/scoped-additive-rollouts.md`: добавлены проверки archive named-source/rollback closure, корректный self-excluded manifest count, явный final receipt index и обязательная сверка исходника checker с разрешённой областью чтения. Изменения подтверждены `skill_manage`; это не новый rollout/независимый PASS.
- Установленные company-os корни/reference на 12 профилях, исходные QA receipts, исходный ZIP, модели, cron и policy не менялись этой проверкой; ничего не удалено. Изменены лишь два procedural skill активного company; чужие профили не редактировались.

## Границы доказанности
- Архитектурная корректность и установка не означают будущего behavioral compliance или прибыльности.
- Isolated loader показывает доступность/парсинг копии, не full disabled-state/collision resolution в каждом живом профиле.
- Native in-memory fixture исключает status=done как общую причину запретов на data-layer; не аттестует реальный policy writer.
- Source/QA outputs сохранены, не переизданы компанией; ошибки истории не скрыты.

## Новая независимая перепроверка и точность её приёмки
Профиль qa выполнил отдельный run2333 и завершил native audit-карту (`done`, outcome `completed`). Проверочный код и raw output не потеряны после workspace cleanup: сохранены native attachments и их побайтовые `qa-proof/` копии. SHA исходника/вывода сверены с handoff; исходный текст reviewer не изменён.

- Собственный live file прогон qa: **120/120**, 12/12 целей, 6/6 frozen member SHA. Это отдельный пересчёт, не переписанные исторические 286.
- Company consumer: **15/15** проверок формата, 8 уникальных dispositions, binding hashes, retained code/output, ZIP, live count и rollback alternatives. `QA-CONSUMER-CHECK.json` содержит реальные predicates.
- 8/8 пунктов получили disposition: F01–F04, L02 и O01 — CONFIRMED; L01 и H01 — PARTIAL. L01 — честное ограничение, H01 — главным образом intentional backups, O01 — рекомендация, не новый выполненный функционал.
- **Пять замечаний по исходной интеграционной фазе:** F01/F02/F03/F04/L02. F01 исправлен точечно в active company; **четыре остаются открытыми** — упаковка, self-links receipt, traceability и labeling исходного held-snapshot. Эти замечания не означают повреждённую установку.
- Не приняты избыточные утверждения reviewer: будто неверный урок был распространён на весь флот или установлена точная причина всех исторических ошибок. Reviewer сообщает glm-5.3-flash/zai, но полная served-model/auxiliary независимость не аттестована этим ограниченным handoff.
- Source review выявил и процедурный огрех нового checker: дополнительный legacy LOAD-HOOK read и recursive inventory публичного standard-каталога шире конечного списка QA-SPEC. Поэтому не подтверждается его заявление об исключительном соблюдении списка. Разрешённые live/ZIP/fixture результаты полезны и проверены; дополнительные inventory-числа — corroboration собственного directory-аудита company, не strict-scope PASS. Это не новый grant для подобных расширений.
- Подробные consumer precision exclusions: `CONSUMER-LIMITS.md`; оригинальные `INDEPENDENT-REVIEW.md/.json` сохранены без правок. Аудит получен с ограничениями; это **не новый rollout/runtime gate**.
- Дополнительно фактически проверено: final company comment успешно добавлен к уже `done` аудит-карте и прочитан обратно с exact board/id (`QA-NATIVE-FINAL-READBACK.json`). Это реальный положительный пример post-done comment в данном разрешённом случае, не универсальная policy-санкция и не объяснение прошлых сбоев.

## Статус доработок после аудита (2026-10-04, owner-directed)
Рекомендации аудита исполнены как отдельные добавленные артефакты; исходные принятые файлы и оба ZIP-источника не переписывались.

- **F02 (полнота пакета) — закрыта.** `dots-hermes-standard-20261004-supplement.zip` SHA256 `f82577f33d58477a46e8e003c9bb63d1d44bdda43e12dc56d80d66014ea7dfc8` (119 261 B, 35 записей): все 34 локально не упакованных файла, включая 6 именованных исходников/квитанций проверок; `SUPPLEMENT-MANIFEST.json` содержит побайтовую сверку 24 документированных `apply-backups` путей против `before/` (все byte-exact). CRC и SHA всех участников проверены при сборке.
- **F03 (self-links receipt) — закрыта индексом.** `FINAL-INDEX.md`/`FINAL-INDEX.json` фиксируют: потреблять `QA-CANDIDATE-FIXED.json` по явному имени; внутренние ссылки — исторические. Receipt не переписывался.
- **F04 (traceability) — закрыта.** Traceability-комментарии добавлены и подтверждены readback: `t_63f62c17` comment_id 5672 (fleet-ops, канонический CLI-readback присутствует) и `t_29903deb` comment_id 81 (default). Индекс связывает все четыре карты фазы/аудита.
- **L02 (LANE.json) — закрыта индексом.** Помечен как устаревший до-релизный снимок, вытесненный native done-состояниями; файл не изменялся.
- **O01 — выполнена первая часть:** authoritative entry index создан; live smoke-case на существующем workflow остаётся будущей проверкой, не выдаётся за выполненную.
- Итог по пяти замечаниям исходной фазы: F01 был исправлен точечно ранее; F02/F03/F04/L02 закрыты доработкой без перезаписи истории. Поведенческий/экономический эффект по-прежнему не измерялся.

## Финансовый scope
Fleet-ops quality audit, 2026-10-04; source: local checks и естественные serving stamps, billing/ledger не читаются. confirmed revenue, refunds, incremental paid costs, new commitments, estimated usage cost = null (не измерено). Установка/укорочение текста не доказали финансового эффекта.

## Указатель доказательств этого аудита
- `AUDIT-SUBJECT.json` — immutable input manifest, SHA `6fea85f0637011c110c8bf6068706c5dd78492159292815ea90408f320693658`.
- `AUDIT-EVIDENCE.json` — inventory/JSON/ZIP/duplicate/rollback checks координатора.
- `LIVE-SNAPSHOT.json` — bounded текущие 12 профильных file snapshots и 108 predicates.
- `NATIVE-SOURCE-PROBE.json` — native helper source hashes/code и controlled fixture.
- `KANBAN-READBACK.json` — исходные exact board/id readbacks, не второй registry.
- `PROCEDURE-CORRECTION.json` — исходный и исправленный reusable lesson.
- `INDEPENDENT-REVIEW.md/.json` — независимые reviewer outputs без переписывания.
- `qa-proof/independent_checks.py` + `qa-proof/independent_checks_out.json` — сохранённые code/raw evidence; native attachment hashes сверены.
- `QA-CONSUMER-CHECK.json` + `CONSUMER-LIMITS.md` — consumer predicates и precise bounded exclusions.

Предложения улучшения не выданы за выполненные fixes. Оригинальные файлы установки/приёмки и архив остались неизменными; destructive cleanup не производился.
