# QA-CANDIDATE — независимая source-candidate приёмка (финал, run 2319)

TYPED VERDICT (word-form): **PASS** — приёмка source-candidate ONLY (содержание REFERENCE-CANDIDATE.md + HOOK-CANDIDATE.md на exact head). Это НЕ приёмка установки, loader-поведения, live-поведения или экономики.

- Карта: t_d090b4ff (fleet-ops), run 2319, profile qa, session 20261004_030640_cd335f.
- Exact subject head: SUBJECT.json SHA256 `2fedef53211adc07445caee7d4d3ef3cac4df5e7544508ca35a26e040774600e`.
- REFERENCE-CANDIDATE.md SHA256 `80933ccf80e99e6b9d62b6f15c5c4f8cf69e9ee79ab1b2e9296173b99cdf4def` (7821 B).
- HOOK-CANDIDATE.md SHA256 `40b6f5e5edad6b8349c3143e032e29d2d02fa5cd1362c9ba9c10dbdbc2bdc88d` (697 B).
- Полный машинный вердикт: QA-CANDIDATE.json (рядом). Чекер: QA-CHECKER-RUN2319.py -> QA-RUN2319-INTEGRITY.json (19/19 ok, exit 0).

## 1. Integrity-батарея рана 2319 (собственный чекер QA-CHECKER-RUN2319.py, независимо от company DRY-RUN)

19/19 ok, exit 0: subject head = 2fedef53…608e; 6/6 members bytes+sha; 12/12 live preimages unchanged (на момент рана); baseline-секции inputs 26/26, installed_docs 12/12, public_hermes_docs 24/24, targets 51/51 — 0 unverified; PRESERVED-QA-2318.json sha a140bcda…d1aa (10755 B) + все preserved stage-файлы совпали; DRY-RUN suffix-split пересчитан побайтово: old hook 458 B sha 2e10a1c6… exactly-once в каждом из 12 корней, candidate root = base + новый hook (3 distinct корня: company 7c498bbb…, research a1793d7c…, shared-10 331ac2fb…), expected_after_reference у всех 12 = sha reference-кандидата; frontmatter (name/description) и entrypoint-ссылка references/dots-operating-method.md валидны во всех 3 базах; company selftest 134/134 — пересчитано, не скопировано. Наследуемое run 2318 (integrity 25/25, dry-run 12/12, word-form PASS до артефактов, lineage 58/58) перепроверено, а не принято на веру.

## 2. Полные поимённые чтения (без content-search поверхностей)

- D1–D8: все 8 Dots-источников прочитаны полностью (overview 18981 chars; getting-started; tasks-memory; controls; computers-apps; channels; enterprise-admin 15463; enterprise-local-access 24355).
- H1–H12: все 12 Hermes-статей прочитаны (kanban 1762 строк; delegation 792; cron 1546; webhooks; memory; skills 1273; sessions 1297; security 1201; hooks 2478; context-files 299; subagent-lifecycle 69; profiles — полностью).
- F1–F9: OPERATING_SYSTEM.md, APPROVALS.md, company-os SKILL.md, outcome-loop.md, kanban-card-authoring SKILL.md, fleet-workflow-efficiency SKILL.md, fleet-notification-ops (руководящие секции), fleet-browser-routing (routing table), scoped-additive-rollouts.md — прочитаны.
- Published vs installed drift подтверждён фактически: installed-docs/kanban.md (122585 chars, 58 заголовков H1/H2) отличается от public/hermes-kanban.txt (114586 chars, 38 заголовков); +12 секций только в installed (вкл. «Kanban vs. delegate_task», «PR completion contracts»), в published — 5 рендер-артефактов примеров. Различение evidence-слоёв матрицы обосновано.

## 3. M01–M17 (каждая ячейка сверена с фактическим текстом; вывод = решение матрицы)

- M01 REMOVE_DUPLICATE — старый метод §1 (before/company/dots-operating-method.md, строки 13–35) задаёт 8 групп полей и компактный Responsibility-шаблон; кандидат шаблон не содержит (таблица-переводчик; строка 27: «Не заводи отдельный responsibility object, второй tracker, дублирующий envelope или набор handoff-полей»). Владелец: CHARTER/STATE/карта + outcome_ref (F1/F4).
- M02 REUSE_CANON — строка 16: «Delegated work -> Конечная native Kanban-карта: deliverable, acceptance, boundaries, anchor»; второй task-template отсутствует; D2/D3 подтверждаются H1 native cards, F5.
- M03 REUSE_CANON — строка 17: один dispatcher, native parent edges, «ограниченные process-local subagents»; H2 (background non-durable, «recorded as unknown») и H12 (RECONNECT_UNAVAILABLE после рестарта, cooperative cancel) подтверждают; второй supervisor не вводится.
- M04 CLARIFY_EXISTING — строка 29: «WAIT не создаёт wake… kanban_schedule лишь паркует карточку: marker/check_at/status не создают таймер»; совпадает с наблюдаемой в этой сессии схемой kanban_schedule (park в scheduled, без таймера) и H3.
- M05 REUSE_CANON+CAPABILITY_LIMIT — строки 18/29: существующие cron/webhook/watchers; «Разрешённый детерминированный native polling сам по себе не дефект»; D6 строка 25 («Adding it to a channel doesn't establish a monitoring schedule») и H11 (route+HMAC регистрация).
- M06 REUSE_CANON — строка 31: находка/draft/login не разрешают send/spend/publish; D4 (research tools can't send), F2 mandate.
- M07 REUSE_CANON — строки 19/27: compact native handoff; H6/H2/H1; новая persistent context DB не вводится.
- M08 REUSE_CANON — строка 19: task truth в Kanban/STATE, процедуры в skill, узкие факты в memory; второй log не создаётся (H4/H5/H7 различены).
- M09 REUSE_CANON+NO_INSTALL — строки 20/31: переход канала не переносит grants, аудитория не расширяется; D6, H7/H8/H11.
- M10 REUSE_CANON+NO_IMPORT — строки 21/33: «канон, не словарь Dots»; OpenAI custom rules не импортируются; F2/Fleet Policy/actual schema — владелец.
- M11 NO_INSTALL — строки 20/31/33: cloud computer/grants не импортируются, inherited session не обещается; D5/D8, H8/H9/F8 (vault/masked ввод).
- M12 REUSE_CANON — строка 32: «Документация не attestation… DONE/hash/самоотчёт не заменяют независимый verdict»; D3 (completed-run не равен delivered), F1 «Исполнение ≠ результат», H12 immutable terminal result.
- M13 PARTIAL_REUSE — строка 30: cancel-запрос/terminal status/launcher exit/descendants — разные evidence; «Отсутствующая native операция — gap, не разрешение на forced completion, takeover или обход»; D4, H12/H2; полный live stop не аттестуется (честный предел, не дефект кандидата).
- M14 REUSE_CANON — строка 30: «не обещай отмену уже выполненного внешнего действия»; D4 (stopping doesn't undo completed actions), F2/F5/F9 (own-bytes rollback, exact readback).
- M15 CLARIFY_EXISTING — строка 28: «Завершение поручения не равно завершению ставки… Не создавай follow-up ради самого факта закрытия карты»; соответствует F1 disposition_ref и F4 dependency safety; forced follow-on не вводится, подавление честного remaining-work отсутствует (продолжение только «уже существующего результата, owner и измеримого смысла»).
- M16 NO_INSTALL/NO_INHERITANCE — строка 33: «Enterprise/cloud/local-access Dots остаются NO_INSTALL… не считаются гарантиями Hermes»; D7/D8, H8/H9/H10.
- M17 REUSE_CANON — строка 34: исправления по действующим relevant-skill/outcome-loop правилам, без отдельного feedback-протокола; H5 skills, H1 request_changes, F9 no-cascade.

Итог: 17/17 — решения матрицы подтверждены фактическим текстом кандидата и источников; overstated equivalence/absence не найдено; unsupported source claims не найдены.

## 4. Нормативные утверждения кандидата -> источник

| Утверждение (locus в REFERENCE-CANDIDATE.md) | Тип | Существующий источник |
|---|---|---|
| «Один workflow… Orient -> … State update» (стр. 11) | указатель | F1 OPERATING_SYSTEM.md цикл |
| Таблица терминов (стр. 13–21) | переводчик | владельцы: F1–F9, H1–H12, APPROVALS |
| «Не заводи отдельный responsibility object…» (стр. 27) | разъяснение | F1/F4 (Kanban = task truth; outcome_ref) |
| «Завершение поручения не равно завершению ставки» (стр. 28) | разъяснение | F1 disposition_ref; F4 dependency safety |
| «WAIT не создаёт wake…» (стр. 29) | разъяснение | наблюдаемая схема kanban_schedule (park, no timer); H3 |
| «Cancel не значит stopped» (стр. 30) | разъяснение | H12 cooperative cancel; F5 recovery |
| «Контекст не даёт доступ или право разглашения» (стр. 31) | разъяснение | F2 mandate; H9 |
| «Документация не attestation» (стр. 32) | разъяснение | F1 Verify; F5 evidence |
| «Enterprise… NO_INSTALL» (стр. 33) | граница | F2 serious escalation classes |
| «Финансы и исправления…» (стр. 34) | указатель | F4 outcome-loop financial fields |

Новых обязанностей, второй schema/очереди/координатора/обязательного шаблона/permission — не обнаружено. Единственный hook замещает прежний hook (F9 own-bytes, verified).

## 5. Сценарии S01–S17 (решения по реальному тексту кандидата; статические counts не использовались как семантика)

S01 CONSISTENT (стр. 28: finite output -> reviewer/consumer, без обязательной новой ставки) · S02 CONSISTENT (стр. 15: таблица -> прежние CHARTER/STATE/Outcome) · S03 CONSISTENT (стр. 32: DONE/hash/самоотчёт не PASS) · S04 CONSISTENT (стр. 29: check_at/park без регистрации -> gap) · S05 CONSISTENT (стр. 29: разрешённый polling допустим) · S06 CONSISTENT (стр. 18/30: подключение источника не регистрация wake) · S07 CONSISTENT (стр. 30: parent exit/cooperative cancel не durable stop) · S08 CONSISTENT (стр. 30: неизвестная cancel-surface -> gap, не takeover) · S09 CONSISTENT (стр. 31: новая аудитория -> нет переноса grants) · S10 CONSISTENT (стр. 31: draft/finding без scope -> нет action permission) · S11 CONSISTENT (стр. 33: paid/root/privacy -> прежняя escalation) · S12 CONSISTENT (стр. 30: ambiguous write -> readback/HOLD) · S13 CONSISTENT (механизм F9 + матрица: изменённая цель -> stop, не whole-root overwrite) · S14 CONSISTENT (стр. 23: отсутствующий skill -> capability gap, не второй runtime) · S15 CONSISTENT (фактическая независимость в §6: reviewer glm-5.3/zai vs author gpt-6.1-sol/openai-codex, overlap=false) · S16 CONSISTENT (стр. 32: file PASS не repair полного runtime) · S17 CONSISTENT (стр. 34: feedback -> relevant skill/same lane).

## 6. Serving lineage рана 2319 (натуральные штампы, не ярлык профиля)

- Reviewer (эта сессия 20261004_030640_cd335f, qa): main API-штампы в profiles/qa/logs/agent.log(+.1): 42/42 = glm-5.3 / zai (диапазон #1–#42 без пропусков; нижняя граница на момент записи артефакта — ран продолжается). Aux/compression/vision/fallback-цепочек с иными моделями в логе сессии не наблюдалось (честно: «не наблюдались», не «отсутствуют»).
- Brain author (AUTHOR-LINEAGE.json): gpt-6.1-sol / openai-codex (2 session-bound stamps, сессия 20261003_231256_1a496e).
- Пересечение пар model/provider: НЕТ (overlap=false) -> независимость по фактической serving-цепочке, не по назначению профиля.

## 7. Пределы (не устранены вердиктом)

- Source-only: установка, loader registration, natural load, live behavior, будущая obedience, полный live stop, sandbox/privacy enforcement, экономический эффект — НЕ аттестуются.
- Live preimages проверены на момент этого рана; APPLY обязан перепроверить хэши непосредственно перед каждой atomic write (F9).
- Aux-цепочки рана 2319 не наблюдались; их отсутствие не доказано.
- Published docs, installed source и loaded runtime различены (см. §2).
- Процессная заметка: одна terminal-команда записи этого файла (heredoc) получила детерминированный fleet-policy deny (review_probe_nonce); повтор запрещён, запись выполнена штатными write/patch-инструментами в freeze-каталог. На вердикт по содержанию не влияет.

## 8. Финансовый охват

scope: fleet-ops method normalization QA (partial); period: COMPANY-BRIEF (2026-10-03T22:33:54Z) -> фактическое окончание этого review; source: натуральные run/stamps/чекер-результаты этого рана; ledger не читался. confirmed_revenue / refunds / incremental_paid_costs / new_commitments / estimated_usage_cost = null (причина: не измерено; serving-штампы — не billing-записи). Новых платных действий нет; это не заявление о нулевой стоимости inference.
