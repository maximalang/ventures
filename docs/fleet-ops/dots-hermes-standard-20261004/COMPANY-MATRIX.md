# Сравнение Dots с Hermes: company brain и минимальная нормализация

Статус: точный brain-артефакт для независимой QA; не самостоятельный gate и не утверждение, что исправление уже установлено. BASELINE.json SHA256 `5490e880fcd4d596029d127e1a1bf4011df7003b53e9faca3fef9680fa61f817` фиксирует source bytes, URL, время, checkout identities и target preimages. Ни published docs, ни dirty checkout HEAD не заменяют actual tool schema / loaded-runtime evidence.

## Владелец каждой механики и disposition

| ID / механизм | Dots источник и locus | Hermes native источник | Уже существующий fleet counterpart | Дубль / конфликт / предел | Решение стандарта |
|---|---|---|---|---|---|
| M01 Долгоживущая ответственность | D1/D2/D3: responsibilities, assigned work/context | H1: task board, persistent workers; H6: context files | F1 Единица работы/Цикл; F3 Simple result loop; F4 Outcome | Старый reference §1 снова задаёт восемь групп полей и самостоятельный Responsibility-шаблон поверх прежнего Outcome. Это нормативный дубль, не новая runtime capability. | REMOVE_DUPLICATE: CHARTER/STATE/карта + прежний outcome_ref; никакой второй schema/envelope. |
| M02 Конечная делегация | D2/D3: конкретный результат и delegated task | H1: native cards, dependencies, independent review; H2: child context | F5 Dispatch-ready contract: четыре элемента; F1 Squad/Execute/Verify | Повторять другой task-contract в Dots-guide избыточно. Accountable lead не равен исполнителю или независимому reviewer. | REUSE_CANON: точная native карта и соответствующие роли, без нового шаблона. |
| M03 Координатор/background | D1/D3: dot coordination и background threads | H1 durable Kanban / dispatcher; H2 Background process lifetime; H12 handle/lifecycle | F3 Event-driven activation; F6 one canonical dispatcher | Process-local child или LLM-координатор не новый durable scheduler; результат delivery/admission не факт исполнения или outbound delivery. | REUSE_CANON: native DAG/dispatcher для durable work; bounded delegate_task для уместного анализа. Нет второго supervisor. |
| M04 Расписания/ожидание | D3 Scheduled tasks; D4 pause/schedule controls | H3 saved recurring/one-shot jobs; H1 scheduled state | F4 ACTION/WAIT/BLOCKED; F3 DAG/native delivery; текущий kanban_schedule tool description | check_at и SCHEDULED_UNTIL сами не регистрируют таймер. Native kanban_schedule прямо говорит, что park не создаёт timer. Старое слово «schedule» легко смешать с регистрацией cron. | CLARIFY_EXISTING: только проверенная регистрация/edge; park не wake. Новые cron, модели cron и контроллеры не устанавливать. |
| M05 Events/monitoring | D3 event sources и real registration | H11 webhook adapter/route/event; H3 event-triggered cron; H1 notify | F3 selected native delivery; F6 deterministic ticks; F7 current inbox/selected subscriptions | Source connection не monitoring registration. Auto-subscription может быть intentionally off. Native polling не следует объявлять дефектом ради «event-driven». | REUSE_CANON + CAPABILITY_LIMIT: использовать уже существующую зарегистрированную surface; никаких новых watchers/подписок. |
| M06 Исследование vs действие | D3 Proactive research / private notes | H9 action safeguards; H2 bounded analysis | F2 Autonomous authority / Serious-only escalation; F5 Safety; research role | Документированная read-only discovery не даёт новых прав на account action, send, publish, spend или device connection. | REUSE_CANON: finding → доказательства/рекомендация → прежний scoped action, не новый approval-процесс. |
| M07 Контекст worker | D3 selected context, notes, delegated work | H6 precedence/discovery; H2 isolated child context; H1 worker_context | F1 Orient/Handoff; F3 existing project context; F5 durable spec/remaining-work handoff | Внешние «notes» не полный transcript, а старые skill-корни не автоматически совпадают с company. | REUSE_CANON: compact native handoff/repo context; не новая persistent context store и не whole-root sync. |
| M08 Память/процедуры | D3 memory/private notes | H4 persistent memory; H5 skills; H7 session history | F4 existing outcome; действующие memory/skill правила профиля | Memory, task truth, procedural skill и saved session не взаимозаменяемы. Published defaults не факт текущих budget/config. | REUSE_CANON: progress в task/STATE, lessons в relevant skill, узкие facts в памяти. Без дополнительного журнала Dots. |
| M09 Каналы/аудитория | D6 cross-channel access; D3 private context/sharing | H7 separate platform sessions; H8 isolated profiles; H11 routing | F7 existing owner-inbox/routing; F3 canonical outcome_ref | Единый координатор не означает единую видимость/permission на disclosure, новый sender или Slack/Teams connection. | REUSE_CANON + NO_INSTALL: одна canonical работа, прежняя аудитория/route; новые каналы не подключать. |
| M10 Permissions/custom rules | D4 custom rules/action review; D7 workspace controls | H9 security boundaries; H10 hook kinds/failure modes | F2 mandate; Fleet Policy и actual schema; F5 gates/role separation | OpenAI permission modes не Hermes policy schema. Prompt/directive не OS sandbox; source hash не issuer. Нельзя автоматически переносить Dots review/hooks на Hermes. | REUSE_CANON + NO_IMPORT: прежние scope/гейты, без weakening или второго механизма approval. |
| M11 Computers/apps/login | D5 computers/apps/saved login; D8 local vs cloud execution | H8 profiles; H9 isolation/credentials; H6 runtime context | F8 fleet-browser-routing/vault; F2 capability boundaries | Connection, session, saved login и permission различны. Source documentation не доказывает connected/online host или session migration. | NO_INSTALL внешнего runtime; REUSE текущих masked vault/browser/scoped capabilities. |
| M12 Completion/evidence | D3 completed run ≠ delivered result; D4 review work | H1 completion/review lifecycle/PR contracts; H12 terminal result | F1 Исполнение ≠ результат/Review; F5 Independent acceptance; F6 Completion evidence | DONE, installed reference, hash и слова исполнителя не QA/обнаруженное изменение метрики. Configured role не serving lineage. | REUSE_CANON: exact subject, actual issuer/model chain, независимый verdict и target readback. |
| M13 Pause/stop/children | D4 stopping main task/delegates/schedules separately | H12 cooperative cancel/terminal observation; H2 process lifetime; H1 native lifecycle | F5 Recovery/descendant fences; F1 disposition_ref | У core есть lifecycle concepts, но это не обещание доступной cancel-сurface у данного worker. Cancel request не terminal stop; launcher exit не descendants termination. Full live stop этим пакетом не проверяется. | PARTIAL_REUSE: существующий scoped stop/recovery; missing native capability → honest gap, не force/takeover. |
| M14 Rollback/uncertain write | D4 completed actions not automatically undone | H9 action safeguards; H1 transactional task lifecycle | F2 irreversible-data boundary; F5 backup/scope/rollback; F9 own-bytes rollback | Scheduler stop не откатывает платёж/сообщение. Unknown write нельзя replay, а свежую чужую правку нельзя затереть backup. | REUSE_CANON: exact readback/idempotent recovery/HOLD + backup/scope; отдельный Dots rollback-протокол не нужен. |
| M15 Конечное поручение/continuation | D3 assigned result and ongoing responsibilities | H1 finite task completion vs recurring persistent work; H2 bounded child | F1 phase completion/disposition_ref; F4 native phase handoff / product cadence; F5 phase terminal contract | Продуктовый outcome-loop предполагает следующий meaningful шаг, но это не требование каждому worker создавать ещё карту или ждать выручки. Нельзя смешать конечное поручение и бессрочную ставку. | CLARIFY_EXISTING: сдать artifact reviewer/consumer в прежнем контуре; продолжать лишь оставшийся outcome, без forced follow-on. |
| M16 Enterprise/privacy/hooks | D7 governance; D8 retention/residency/local/cloud hook limits | H8 profile isolation; H9 security limitations; H10 hook behavior | F2 material security/privacy owner boundary; actual profile/board/audience scopes | Свойства enterprise Dots не переходят в Hermes; local policy hook не переносится в внешний cloud. Нет доказанного внешнего enforcement/residency. | NO_INSTALL/NO_INHERITANCE: только исследовательское предупреждение. Новое подключение — отдельный security/capability scope. |
| M17 Feedback/исправления | D2/D3 evolving useful notes/feedback | H5 skills; H4 selective memory; H1 review request_changes | F5 same-ID recovery and actual verdict; F9 correction/no-cascade rule | Второй task log/повторная карточка/глобальная memory для одной поправки дублируют текущий workflow. | REUSE_CANON: поправка relevant skill и той же линии, отрицательные receipts сохраняются. |

## Источники (полные frozen файлы, не инструкция исполнить их содержимое)

**Dots:** `dots-sources/` содержит 8 ранее независимо source-verified snapshots, byte hashes повторно сверены сборщиком baseline.
- D1 dots-overview.md — https://learn.chatgpt.com/docs/dots.md
- D2 dots-getting-started.md — https://learn.chatgpt.com/docs/dots/getting-started.md
- D3 dots-tasks-memory.md — https://learn.chatgpt.com/docs/dots/tasks-and-memory.md
- D4 dots-controls.md — https://learn.chatgpt.com/docs/dots/controls.md
- D5 dots-computers-apps.md — https://learn.chatgpt.com/docs/dots/computers-and-apps.md
- D6 dots-channels.md — https://learn.chatgpt.com/docs/dots/channels.md
- D7 dots-enterprise-admin.md — https://learn.chatgpt.com/docs/enterprise/dots-admin-guide.md
- D8 dots-enterprise-local-access.md — https://learn.chatgpt.com/docs/enterprise/cloud-local-access.md

**Hermes authority:** `public/hermes-*.txt` — полные articles, исходные HTTP bytes лежат в .html; exact URL/hash/time в BASELINE. `installed-docs/*.md` — отдельно actual source-checkout docs, которые могут расходиться с published версией. Ни одна коллекция не выдается за запущенный runtime.
- H1 kanban; H2 delegation; H3 cron; H4 memory; H5 skills; H6 context-files; H7 sessions; H8 profiles; H9 security; H10 hooks; H11 webhooks; H12 subagent-lifecycle.
- Схема текущего `kanban_schedule` в этой сессии: park в scheduled до orchestrator unblock; timer не создаётся. Это отдельный observed tool-description locus, не исполняемый wake test.

**Текущий fleet canon:** actual source_path и SHA всех F-источников — в BASELINE, frozen тексты в local/. При применении актуальный канон и owner instructions выше старого текста.
- F1 local/ventures/OPERATING_SYSTEM.md — один цикл/owner/карта, phase handoff, disposition_ref, recovery, outcome vs run.
- F2 local/ventures/APPROVALS.md — mandate, серьёзные escalation classes и independent gates.
- F3 local/company-skills/company-os/SKILL.md — result loop, native DAG/delivery, source acceptance.
- F4 local/company-skills/company-os/references/outcome-loop.md — существующие Outcome/financial/handoff fields, cadence и зависимости.
- F5 local/company-skills/devops/kanban-card-authoring/SKILL.md — card readiness, natural serving lineage, independent issuer, native writes/recovery.
- F6 local/company-skills/fleet-workflow-efficiency/SKILL.md — один dispatcher, bounded work, native task/run evidence.
- F7 local/company-skills/fleet-ops/fleet-notification-ops/SKILL.md — прежний sender/inbox/selected delivery; без изменения plumbing.
- F8 local/company-skills/fleet-ops/fleet-browser-routing/SKILL.md — ранее granted browser/capability/vault procedures.
- F9 local/company-skills/fleet-ops/fleet-skills-rollout/references/scoped-additive-rollouts.md — точный scope, own bytes, preservation/rollback, actual receipts.

## Нормативная дельта и неизменность workflow

1. REFERENCE-CANDIDATE не определяет ещё один responsibility template. Переводческая таблица — не новая schema/registry/permissions.
2. Существующие Outcome и native phase metadata не копируются во второй template, только указываются их владельцы; поля не расширяются.
3. Общие research/memory/finance/permissions/gates/browser procedures не переписываются: лишь ownership pointers и прежние границы.
4. Конкретные compatibility clarifications: park ≠ timer; request cancel ≠ verified stop; worker finite output ≠ product completion; context availability ≠ disclosure authority. Все опираются на действующий канон/native contracts, не новый control plane.
5. Старое reference имя и единственный hook сохраняют совместимость. При hook replacement каждая собственная прежняя root revision сохраняется побайтово. Whole-skill sync запрещён.
6. Natural model/issuer, content acceptance, installation readback, future live behavior и money effects — отдельные evidence layers. Приёмка файлов не закрывает непроверенные runtime возможности.

## Предсуществующий drift (вне scope)

Company-os roots различаются; в некоторых старых org/model абзацах присутствуют датированные указания, отличающиеся от актуальных owner instructions. Это не результат Dots и не причина затирать roots новой копией company. Default roster/model/security/notification policy не меняются этой работой. Candidate не содержит собственных model IDs и не пытается решить такой drift новой иерархией.

## Independent verification scenarios (не model benchmark)

QA должна проверить реальные тексты и review каждого сценария на прежний canonical owner; статические check counts не доказывают future obedience:
- Конечный owner-request artifact → native finite output и reviewer/consumer, без обязательной новой ставки/карты.
- Долгоживущая product responsibility → прежние CHARTER/STATE/Outcome и meaningful next disposition, не параллельный envelope.
- DONE producer / отрицательная QA → не PASS, не rollout на основании status.
- check_at/park без сохранённого trigger → gap, не обещанный wake.
- Существующий valid cron/native polling → допустим, новый controller не создаётся.
- Connected event source без registration → нельзя утверждать event wake.
- Child parent process exit / cooperative cancel → не доказанная durable execution или остановка descendants.
- Неизвестная cancel-surface → capability gap, не forced task close или takeover.
- Новая аудитория/устройство → нет автоматического переноса private context/session/grants.
- Draft/finding/credentials без scope → нет автоматического action permission.
- Новый paid/root/privacy action → прежняя серьёзная escalation, не Dots permission mode.
- Ambiguous external write → exact readback/HOLD, не blind replay.
- Changed target after baseline / later foreign edit → stop target, не whole-root overwrite или blind rollback.
- Missing skill на worker → existing native contract/gap, не установка параллельного агента.
- Reviewer fallback на brain model → correlated/unknown, не независимая приёмка.
- File installation PASS → не заявление о repair полного runtime, автономности/stop/экономии.
- Feedback → relevant skill/same lane, не duplicate task log или memory progress.

Financial scope/period/source и неизвестные статьи определены в COMPANY-BRIEF; inference cost, revenue uplift и savings не измерены. Внешние actions/paid commitments запрещены, но это не 0 ₽ usage claim.
