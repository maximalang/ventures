# Dots ↔ Hermes: compatibility entrypoint

Это перевод внешних терминов к **существующему** workflow Hermes-флота, а не самостоятельный операционный стандарт. Канон: актуальные профиль/задача, AGENTS.md, OPERATING_SYSTEM.md, APPROVALS.md и Fleet Policy. Старое имя `dots-operating-method.md` сохранено для совместимости ссылок. Dots не установлен; новых прав, сервисов, моделей, контроллеров или storage schema этот файл не создаёт.

## Когда читать

Только при сравнении внешней агентной методики с Hermes, неоднозначности ownership/continuation/stop или переносе handoff между каналами. Для обычной scoped карты достаточно её native context и релевантного установленного skill: дополнительный Responsibility-шаблон не требуется. Полная сравнительная матрица и snapshots находятся в `C:/Users/max/Desktop/all/ventures/docs/fleet-ops/dots-hermes-standard-20261004/`; это audit-артефакты, не инструкции для каждого run.

## Один workflow и владельцы механик

Применяется прежний цикл **Orient → Decide → Squad → Execute → Verify → Handoff → State update** из `C:/Users/max/Desktop/all/ventures/OPERATING_SYSTEM.md`.

| Термин Dots | Уже существующий Hermes/fleet counterpart | Где брать действующее правило |
|---|---|---|
| Responsibility | Активная ставка, CHARTER/STATE, один accountable lead, native outcome_ref | OPERATING_SYSTEM; company-os / outcome-loop, если установлен |
| Delegated work | Конечная native Kanban-карта: deliverable, acceptance, boundaries, anchor | Точная карта; kanban-card-authoring, если установлен |
| Background coordination | Один dispatcher, native parent edges, claims/review; ограниченные process-local subagents | Фактический native tool schema; fleet-workflow-efficiency |
| Recurring / event work | Имеющиеся cron, webhook, selected native delivery и watchers | Действующая регистрация и её readback; существующий профильный ops skill |
| Memory / notes | Task truth в Kanban/STATE; процедуры в relevant skill; узкие факты в memory/fact store | Текущие memory/skill/context правила профиля |
| Channels / computers / apps | Существующие session/audience boundaries и scoped capabilities | Установленные browser-routing/vault и notification procedures; APPROVALS |
| Review / completion / controls | Independent QA/finance, exact subject, native handoff и target readback | Точные evidence gates и reviewers; канон, не словарь Dots |

Названия skills — указатели на существующих владельцев процедуры, не обещание их наличия у любого профиля. Если нужный skill/surface отсутствует, используй уже разрешённый native contract или зафиксируй конкретный capability gap; не устанавливай второй runtime и не обращайся к чужим внутренним хранилищам. ACTUAL tool schema и текущие полномочия важнее описания в public docs.

## Разъяснения в рамках прежних правил

- **Одна истина, один handoff.** Цель/metric/horizon остаются в прежнем CHARTER/STATE/карте, а phase_result/evidence/observation/next disposition — в уже используемом native summary/metadata. Не заводи отдельный responsibility object, второй tracker, дублирующий envelope или набор handoff-полей.
- **Завершение поручения не равно завершению ставки.** Specialist сдаёт конечный deliverable и передаёт его существующему reviewer/consumer; не держит карту открытой до выручки. Продолжение product outcome-loop решает accountable lead. Не создавай follow-up ради самого факта закрытия карты; любая следующая работа должна иметь существующий результат, owner и измеримый смысл. Незавершённые элементы фазы получают прежний disposition_ref.
- **WAIT не создаёт wake.** Dependency, сохранённый cron или поддержанная selected delivery проверяются по их регистрации. `kanban_schedule` лишь паркует карточку: marker/check_at/status не создают таймер. Следуй прежним ACTION/WAIT/BLOCKED и recovery правилам, не добавляй scheduler, polling-loop или массовые подписки. Разрешённый детерминированный native polling сам по себе не дефект.
- **Cancel не значит stopped.** Применяй текущие scoped stop/recovery и backup/scope/rollback процедуры только через доступные разрешённые surfaces. Запрос отмены, terminal status карточки, завершение launcher и остановка descendants — разные evidence. Отсутствующая native операция — gap, не разрешение на forced completion, takeover или обход. Read back затронутые children/wakes/side effects; не затрагивай unrelated work и не обещай отмену уже выполненного внешнего действия.
- **Контекст не даёт доступ или право разглашения.** Переход канала/host не переносит task/session/grants автоматически. Finding, draft, login, connector или прочитанный контекст не разрешают send/spend/publish и не расширяют аудиторию. Прежние scoped capabilities и serious-only escalation сохраняются.
- **Документация не attestation.** Published Dots/Hermes docs, source checkout, installed files, actual issuer/model, live behavior и platform delivery проверяются отдельно. DONE/hash/самоотчёт не заменяют независимый verdict. Эта адаптация не доказывает full live stop, future obedience, sandbox/privacy enforcement или экономический эффект.

Исследование Dots и полные fact/source mappings сохраняются в `dots-20261003` и новой сравнительной матрице. Enterprise/cloud/local-access Dots остаются **NO_INSTALL** в этом scope. OpenAI custom rules, cloud hooks, retention/residency не импортируются и не считаются гарантиями Hermes. Финансы и исправления оформляются ровно по действующим outcome-loop / relevant-skill правилам, без отдельного финансового или feedback-протокола.
