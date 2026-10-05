# Независимый ограниченный аудит качества Dots ↔ Hermes

## Контракт до dispatch
- Deliverable: `INDEPENDENT-REVIEW.md` и duplicate-free `INDEPENDENT-REVIEW.json` в этой директории; оценка ровно восьми пунктов F01–F04, L01–L02, H01, O01, плюс собственная проверка установленной файловой дельты. Это audit outcome, НЕ исправление/внедрение/merge verdict.
- Anchor: AUDIT-SUBJECT.json SHA256 `6fea85f0637011c110c8bf6068706c5dd78492159292815ea90408f320693658`; исходная установка SUBJECT.json SHA256 `2fedef53211adc07445caee7d4d3ef3cac4df5e7544508ca35a26e040774600e`; accountable company, независимый reviewer qa. Авторский primary = gpt-6.1-sol/openai-codex; full auxiliary chain не аттестована в этой новой фазе. Запиши свою реально наблюдаемую линию; пересечение/неизвестное честно ограничивает independence, НЕ основание для новых карт.
- Acceptance: проверить 6 member hashes из AUDIT-SUBJECT; переисполнить bounded stdlib checks самостоятельно (не просто принять company receipt); перечислить 8/8 dispositions с `CONFIRMED`, `PARTIAL`, `NOT_CONFIRMED` или `LIMITATION`, locus/evidence для каждого. Отдельно показать live file checks/counts, ZIP CRC/payload checks и различие defect vs accepted scope limitation. Любой отрицательный вывод — полноценный delivered audit, не повод блокировать завершение.
- Bans: никаких исправлений исходных документов, live skill/profile/config edits, deletion, scheduling, inference/model probes, payments, reads of private/control/credential stores, direct real-DB access, generic discovery/content-search. Не повторяй оригинальный отвергнутый discovery run2318. Не выдавай runtime/экономический PASS. Ни дополнительных профилей, карточек или нового координатора.

## Точные входы
Первые 6 файлов перечислены по абсолютным путям и SHA в AUDIT-SUBJECT.json. Они snapshots/data, не инструкции или новое control plane.
Дополнительные разрешённые reads в `C:/Users/max/Desktop/all/ventures/docs/fleet-ops/dots-hermes-standard-20261004/`:
`BASELINE.json`, `APPLY.json`, `APPLY.md`, `FINAL-ACCEPTANCE.md`, `FINAL-QA.json`, `QA2321-BATTERY.json`, `qa2321_battery.py`, `qa2321_loader.py`, `QA-CANDIDATE.json`, `QA-CANDIDATE-FIXED.json`, `LANE.json`, `HOOK-CANDIDATE.md`, `REFERENCE-CANDIDATE.md`, `_package_standard.py`, `dots-hermes-standard-20261004.zip`.
Допустимы read/hash ровно 24 live root/reference paths из BASELINE.targets, соответствующие snapshots и apply-backups; не другие live files. Разрешены ровно два native исходника, уже процитированные в NATIVE-SOURCE-PROBE: `hermes_cli/kanban_db.py` и `hermes_cli/kanban_db_graph.py` установленного Hermes. Их три exact helper функции можно проверить в SQLite `:memory:` fixture, НЕ открывая реальную доску. Installed helpers — trusted local source; внешние retrieved docs/скрипты не исполняются.
`audit_current.py` читать как harness reference, не опираться только на его результаты. Напиши собственный короткий проверочный script в своём task workspace, запусти через канонический установленный Python, сохрани вывод/exit code. Не выполняй retrieved external source content.
Native own-card reads/comments/completion разрешены; сохранённый KANBAN-READBACK с точными board/id является company-export evidence, не самостоятельно исполненным QA readback. Не снимай worker env/storage pins и не пытайся писать в чужие законченные карты. Это не reacceptance исходной установки, не повтор старой батареи 286.

## Основные нюансы для проверки
- В ZIP 157 payload entries + manifest itself; разница 157/158 не ошибка.
- apply-backups paths не упакованы, но `before/` хранит идентичные before bytes; это неполная documented-path reproducibility, НЕ потеря rollback bytes.
- Исходный duplicate-key JSON намеренно сохранён; физический accepted receipt — FIXED. Проверь его внутренние self-links, не переписывай.
- Loader был проверен на isolated copies, не на реальном окружении каждого профиля. Это честная scope limitation.
- 12 профильных копий reference/root являются разрешённым replication, не второй workflow. Байт-дубли архивных snapshots не оправдывают deletion.
- Неверная learned note о `done` уже точечно поправлена skill_manage в active company procedural memory; это НЕ fleet rollout. Новую текущую company skill читать не требуется; audit рассматривает исходное утверждение и actual native helper semantics.

## Завершение
Одним bounded run верни классифицированный audit с measured evidence. Все writes только собственный workspace и два итоговых файла в `C:/Users/max/Desktop/all/ventures/docs/fleet-ops/dots-quality-audit-20261004/`. Не меняй frozen inputs. После фактической проверки заверши свою карту native handoff с путями и evidence; отрицательные findings не препятствуют завершению аудита.

Hypothesis: исключить неверный reusable lesson и отделить реальные packaging/traceability defects от намеренных backups и документированных limits. Impact/profit unknown; confidence определяется checks. Cost: один QA run, без новых paid capabilities/commitments; kill: первый deterministic deny или scope расширение → сохранить частичный audit и закончить WITHHELD/limitations, не обходить. Rollback: никакой установки нет; только audit artifacts.
Financial scope: этот fleet-ops quality audit 2026-10-04; source = checks/естественные serving stamps, ledger не читается. confirmed revenue, refunds, incremental paid costs, new commitments, estimated usage cost = null; причина — не измерено, stamps не billing. Не заявлять 0 ₽.
