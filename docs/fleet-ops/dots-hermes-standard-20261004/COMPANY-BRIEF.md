# Dots ↔ Hermes: стандарт совместимости, не второй workflow

## Явный контракт до диспатча

**Deliverable:** поэлементная сравнительная матрица Dots → опубликованный Hermes → реально существующий канон флота; точный минимальный compatibility-adapter вместо установленного самостоятельного Dots-плейбука; обратимое применение только к прежним reference/hook в 12 allowlisted `company-os`; независимая приёмка содержания до применения и установленного результата после него.

**Acceptance:** покрыть ровно M01–M17 из этого брифа, каждый с Dots-источником/разделом, Hermes-источником/разделом, существующим владельцем механики, classification, конфликтом/дублем и решением. Для каждого нормативного предложения candidate указать прежний источник правила или пометить дополнительное разъяснение, не новую обязанность. Не должно быть второй schema/очереди/координатора/обязательного responsibility-шаблона. Exact-head QA до установки; после — 12/12 одинаковых references, ровно один новый hook, root без собственного hook побайтово равен исходному root без старого hook; все остальные captured Markdown-файлы каждого company-os неизменны; YAML/frontmatter и ссылки проверены. PASS требует независимого природного serving lineage, не ярлыка профиля. Итог не является доказательством будущего поведения, полного live stop или экономии.

**Границы:** не менять текущий runtime, providers/models/pools/config, разрешения, cron/senders/подписки/сchedules, бизнес-проекты, карточки других линий, первичный frozen Dots-пакет или целые деревья skills. Не читать secret-bearing файлы или сырые task/control stores. Никакой установки облачного Dots, новых сервисов/аккаунтов, paid inference-проб, payment/spend, второго scheduler, blanket rollout канона company поверх более старых корней. First deny/drift → partial evidence + stop, не обход и не blind unblock. Эта работа не чинит дефекты автономной компании и не расширяет security/privacy authority.

**Anchor / owner:** company — brain и decision-owner стандарта; operations — единственный hands-writer; qa — независимый reviewer. Целевая система — существующие company-os 12 профилей из BASELINE.json. Frozen baseline SHA256 `5490e880fcd4d596029d127e1a1bf4011df7003b53e9faca3fef9680fa61f817`; прежняя методика SHA256 `f2a85ced87b620bf08cdfc2f3de85ce004a2912efded4da85b668148f00dce6f`. Hermes checkout HEAD `9aae3c23e2c4f39f77d8d54b5e72ba4b90f4ba8f`, fleet repo HEAD `b586b6cd2b05d61b78e0208863a1319d75a93afe`; оба dirty, поэтому HEAD не заменяет frozen actual-byte hashes и не аттестует загруженный процесс. BASELINE хранит 8 ранее независимо проверенных Dots snapshots, 12 свежих полных public Hermes articles, 12 локальных source-docs и фактические правила/корни целей.

## Решение company о форме стандарта

Предыдущий STUDY §4 содержит полезное высокоуровневое сопоставление, но это не достаточная поэлементная приёмка отсутствия семантических дублей. Его исследование/QA файлов сохраняются как история, не переобъявляются недействительными и не выдаются за новую стандартизацию.

Канон остаётся **Orient → Decide → Squad → Execute → Verify → Handoff → State update** из OPERATING_SYSTEM.md. Внешний Dots-словарь — только перевод к этому workflow. Нельзя присоединить параллельно ещё один нормативный responsibility-contract. Default disposition: REUSE_CANON; REMOVE_DUPLICATE для отдельных повторных шаблонов; CLARIFY_EXISTING только для ошибочно обещанной механики; NO_INSTALL для внешних возможностей. Расхождение published docs, installed source, текущего tool schema и наблюдавшегося поведения показать раздельно; наличие документации не attestation действующей capability.

### Обязательное покрытие сравнительной матрицы

- M01 — долгоживущая responsibility, accountable owner, horizon, metric, источники истины ↔ CHARTER/STATE/активная ставка/native outcome_ref. Исключить отдельный обязательный envelope и повторный набор полей.
- M02 — bounded delegated deliverable ↔ четыре элемента текущей карты (deliverable, acceptance, boundaries, anchor), специалисты и независимые evidence-gates. Не добавить второй task template.
- M03 — coordinator и background agents ↔ один native Kanban dispatcher/DAG/claims для durable work; delegate_task — ограниченный дочерний анализ, не постоянный supervisor.
- M04 — recurring/scheduled work ↔ имеющийся cron, timezone/expiry/registration/readback. Native kanban_schedule паркует, но не создаёт timer: status/marker/check_at не доказывают wake.
- M05 — event monitoring ↔ имеющиеся webhooks, native selected delivery, детерминированные watchers. Source connection не registration; разрешённый polling не запрещается и не заменяется новым контроллером.
- M06 — proactive read-only research ↔ research/scout finite evidence и прежний mandate последующего action. Finding/draft/access не дают новых прав на send/spend/publish.
- M07 — selected context и context handoff ↔ фактические AGENTS/SOUL/context files, native worker_context, repo docs и компактный существующий handoff. Не требовать полного transcript или новую persistent context DB.
- M08 — memory/private notes ↔ selective user/fact memory, task truth в Kanban/STATE, процедуры в relevant skill. Не создать второй log в глобальной памяти.
- M09 — continuity между ChatGPT/Slack/Teams ↔ существующие desktop/TG/session boundaries, один canonical task/outcome_ref и current authorized inbox/routing. Context availability не disclosure permission; новые каналы не подключать.
- M10 — custom controls/action review ↔ APPROVALS, Fleet Policy, независимые qa/finance и фактический tool schema. OpenAI permission modes не schema и не auth grant Hermes; инструкция не sandbox.
- M11 — computers/apps/saved login ↔ browser-routing, vault/маскированный ввод, existing scoped capabilities, различение host/session/task. Не импортировать cloud computer или grants, не обещать inherited session.
- M12 — run completion и achieved outcome ↔ exact artifact, native handoff, independent QA, target readback, actual issuer/model chain. Ни DONE, ни digest, ни hash сами не gate/продуктовый исход.
- M13 — pause/stop/cancel ↔ текущие finite ownership/recovery/descendant procedures и доступные native surfaces. Различать запрос cancel и verified terminal stop; отсутствие exposed cancellation не разрешает обход, forced completion или process takeover. Полный live stop не проверялся.
- M14 — reversal и ambiguous external actions ↔ существующий backup/scope/rollback и exact readback/idempotent recovery. Остановка не отменяет уже выполненный side effect; не replay неизвестного действия.
- M15 — конец scoped artifact и continuation ответственности ↔ native finite phase completion/disposition_ref и product outcome-loop. Не заставлять исполнителя порождать follow-up карту, удерживать deliverable до выручки или превращать каждое конечное поручение в вечную ставку. Следующая работа только для фактического оставшегося результата в уже существующем контуре.
- M16 — enterprise/local access/privacy ↔ текущие isolated profiles/boards/audience + security/privacy mandate; явно NO_INSTALL. Заявленные Dots hook/residency/retention свойства не гарантия контроля Hermes и наоборот.
- M17 — feedback/corrections ↔ текущий relevant skill, same-lane recovery и supersession. Не создать отдельные повторные поручения/глобальную память для той же поправки.

### Допустимая дельта

REFERENCE-CANDIDATE.md — короткий переводчик терминов и указатель на владельцев уже существующих процедур; старое имя dots-operating-method.md сохраняется как compatibility entrypoint, чтобы не плодить ещё один skill. Нет самостоятельного Responsibility-шаблона, двойных handoff-полей, новых обязательных состояний или общих account/permission-рецептов. HOOK-CANDIDATE.md замещает только прежний добавленный hook. COMPANY-MATRIX.md объясняет решения, остаётся audit-артефактом, а не инструкциями на каждый run. Полный первичный пакет и source provenance не переписываются.

Если разъяснение действительно противоречит действующему канону, reviewer возвращает конкретный locus; не переписывать канон ради Dots. Предсуществующий drift корней/model-слов пометить отдельно и оставить вне этой задачи.

## Конечный native pipeline

1. QA-CANDIDATE — source/semantic acceptance точных matrix/reference/hook; отрицательный verdict и unknown independence допустимы, но не PASS.
2. APPLY — operations, настоящий parent QA-CANDIDATE, exact approved head. До writes проверить word-form positive verdict + hashes, fresh baseline, issuer и company decision на APPLY. Backup/scope/rollback evidence — operations; review/qa evidence — только qa на APPLY. Завершить применение handoff в native review **на той же карте** (`kanban_request_review(reviewer='qa')`), не объявлять итоговую приёмку самому.
3. QA в native review APPLY — независимые readback всех 12 целей, сохранности captured tree, ссылки/loader, exact model lineage и смысловые сценарии. Авторские before/after counts перепарсить. `kanban_complete` только после acceptance; иначе native request_changes тому же implementer. Никакого отдельного company-consumer worker, per-card sleep-поллинга или нового wake loop.

Отсутствующий выбранный notify primitive и intentionally off auto-subscription не обходить CLI/SQL; не менять доставку под видом этой стандартизации. DAG/review остаются native control flow. Финальные owner-результаты короткие, artifact и native readback — источник истины.

## Наблюдение, стоимость, kill, rollback

Hypothesis: убрать нормативную дублирующую оболочку, сохранив единый owner каждой механики и прежнюю самостоятельность Hermes. Подтверждаемый результат этой работы — стандартизированное документальное внедрение; влияние на latency/выручку/token use и future obedience не измерено.

Financial scope: fleet-ops, внутренняя нормализация методики; период от 2026-10-03T22:33:54Z до фактической приёмки; source BASELINE/нативные task receipts, billing не извлечён. Confirmed revenue, refunds, incremental paid costs, new commitments и estimated usage cost = null с причиной (не revenue experiment / ledger не собран). Новые платные заказы и capabilities запрещены; это не утверждение, что inference бесплатна.

Kill: любой новый источник прав/контроллер/схема, конфликт с текущим mandate, неподдерживаемый wake/stop, drift, неизвестный issuer/коррелированная QA, write вне allowlist. Rollback только own replacement bytes, fresh after-hash и verified backup/scope; later edit означает HOLD, не blind restore. Старый архив не удалять. Все отрицательные verdicts сохранить.
