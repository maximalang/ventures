# Dots-style responsibilities: адаптация для Hermes fleet

Original fleet method derived from public OpenAI Dots guides. Это методика, не установленный OpenAI Dots, не permission grant и не новая реализация scheduler. Authority: действующие AGENTS/OPERATING_SYSTEM/APPROVALS, Fleet Policy, профиль и конкретная карта; они имеют приоритет над этой reference. Model/provider routing не изменяется.

## Когда читать

Company/product читают при принятии или пересмотре долгоживущей ответственности, подготовке bounded delegation, анализе WAIT/stop или cross-channel continuity. Worker читает только релевантные части для своей scoped карты; не получает общий мандат CEO. Не загружать полный исследовательский архив на каждый мелкий шаг.

## 1. Ответственность → конечная проверяемая работа

Долгоживущая ответственность описывает результат, за которым следит owner. Одна конечная карта описывает инкремент с deliverable, acceptance, границами и exact anchor. Оба сохраняются в **существующей** карте/CHARTER/STATE/handoff; не создавай второй task registry, JSON wake-queue или DB ради этой методики.

До dispatch установи:

- Accountability: один company/product lead; worker owner отдельного инкремента.
- Result: measurable metric/accepted artifact, horizon и evidence source.
- Truth: canonical board/task/STATE и допустимые input sources; freshness и неизвестное.
- Scope: что разрешено действующим mandate, что запрещено, capability limits и серьёзные escalation classes.
- Work: deliverable, acceptance с SHA/path/числом/readback, границы и точная система/голова.
- Continuation: wake condition/доказанное событие либо schedule с timezone/expiry; конечное состояние и kill criterion.
- Attention: существующий authorized destination, что interrupt-worthy и что остаётся в Kanban.
- Verification: independent reviewer, actual subject identity и rollback.

Если один из четырёх card-contract элементов неясен, сначала retrieval/re-scope; если только владелец может решить — одна форма вопросов. Не делегируй неопределённость исполнителю. Не создавай карты ради занятости.

Компактный шаблон, **не новая обязательная storage schema**:

```text
Responsibility: <goal + horizon>; accountable owner: <profile>
Truth/source: <board/task/STATE + timestamp>; metric/evidence: <definition>
Allowed/banned: <existing capability + boundaries>; kill/rollback: <condition>
Increment: <one deliverable>; acceptance: <exact output>; anchor: <system/head>
Continuation: <ACTION task / confirmed WAIT registration / typed BLOCKED>
Attention: <existing channel + threshold>; independent verifier: <profile>
```

## 2. Разделяй исследования и разрешённые действия

Proactive research читает разрешённые источники, сохраняет bounded findings и предлагает проверяемый next action. Находка сама по себе не разрешает send, publish, spend, write, account/device connection или browser/computer control. Assigned recurring work может делать уже разрешённые действия, но его contract, capability и schedule проверяются отдельно.

Связь с app или chat не равна permission на любое action. Draft ≠ send. Наличие credentials ≠ scope grant. Owner intent не отменяет Fleet Policy или независимые gates. Уважай текущие serious-only escalation classes; не превращай каждое routine decision в owner approval.

## 3. Координатор не является dispatcher

Company выбирает ответственность/инкремент, предоставляет context и читает результат. Native Kanban dispatcher владеет eligibility/claim/spawn/recovery. Specialist выполняет finite deliverable; QA независимо проверяет; consuming step использует exact accepted output. Не добавляй второго scheduler/writer, LLM busy-loop, cron-unblock lane или прямой SQL.

Background delegate_task не durable: exit/session end может прервать children. Используй его только для уместного bounded анализа; materially authoritative QA/finance — отдельные независимые профили через Kanban. Producer DONE лишь освобождает review child; не делает review PASS. При доступном native handoff завершай свой deliverable, не удерживай worker до бизнес-исхода; company остаётся accountability owner.

## 4. ACTION / WAIT / BLOCKED и зарегистрированное продолжение

- ACTION: один реальный следующий разрешённый increment, owner и exact native task readback.
- WAIT: реальное condition/dependency/wake; если требуется fixed timing — сохранённый schedule с timezone, duration/expiry, source, threshold и destination. Запиши registration ref, будущее check_at и readback. Текст «проверю завтра» не registration.
- BLOCKED: конкретная capability/input/dependency/transient причина, responsible owner и факт, почему нельзя разрешить её самостоятельно. Не повторяй неизменный deny/unblock. Capacity backpressure здорового worker не означает failure.

Подключить event source ≠ зарегистрировать monitoring. Не утверждай event-driven wake, бесконечную автономность или работу при выключенном host без live capability evidence. Детерминированный native polling допустим; внедрение event wake — отдельный scope. Расписание не создаётся этой reference. Не меняй существующие cron/model/provider settings.

Если sanctioned registration surface отсутствует, сохрани честный capability/continuation gap и task owner, а не изображай WAIT; company решает re-scope в существующем контуре. Не фабрикуй future receipt.

## 5. Контекст, память и каналы

Handoff содержит цель, точный output/anchor, разрешённые sources, существенные decisions, failure/unknown и следующий disposition; worker не получает автоматически все разговоры parent.

- Kanban/repo STATE — task truth и evidence.
- Relevant skill — повторяемый procedure и lessons/corrections этого вида работы.
- User memory/fact store — узкие долговременные факты, не progress log, secret store или весь transcript.
- Selected conversation context — информация для текущего взаимодействия, не обещание полного recall.

Одна ответственность имеет один canonical outcome_ref при переходе между desktop/TG/группой; не создавай duplicate work. Context availability не даёт disclosure permission другой аудитории. Не копируй private messages в team/topic без разрешённого scope. Не подключай Slack/Teams/новый sender для имитации Dots; пользуйся существующим owner-inbox/routing.

Финансы в любом handoff: scope, period, source; revenue/refunds/incremental paid costs/new commitments/estimated usage отдельно. Unknown = null + причина, не 0. Прогноз эффективности/токенов/₽ не выдаётся за measured saving.

## 6. Компьютер, session и capability

Messaging connection, app authorization, connected device, browser session и saved login — разные вещи. Перенос устройства не переносит существующую task/environment/session. Не читай .env/auth/secrets/dumps и не передавай credentials через conversation. Для website login используй текущие vault/browser-routing процедуры; для 2FA — masked UI. Не меняй saved credentials/recovery/ownership и не подключай OpenAI Dots к личному компьютеру в рамках этой методики.

Read-only source audit и source hash не доказывают installed runtime, model usage, sandbox enforcement, source issuer или actual delivery. Проверяй exact target соответствующей разрешённой surface; local tests ≠ live acceptance.

## 7. Полная остановка и rollback

Pause coordinator, stop current worker, stop delegated children, disable/delete future schedule и revoke capability — разные операции. Закрытие чата не делает их автоматически. При scoped stop:

1. Найди canonical responsibility и перечисли связанные активные карты/children, native wakes/schedules, external in-flight operations.
2. Через разрешённые native surfaces останови только выбранную ветку и отменяй её future work в пределах запроса. Не трогай unrelated healthy runs.
3. Read back exact targets; отметь completed actions и uncertain side effects. Не обещай rollback уже отправленного сообщения/платежа.
4. Назначь disposition для каждого незавершённого элемента: continued task, confirmed wake/check_at, true blocker или superseded target.

Ambiguous external write требует readback/idempotent recovery или hold, не blind replay. Destructive rollback требует прежних backup/scope gates. Эта reference не grants stop-all/root/delete authority.

## 8. Успех ≠ «агент что-то сделал»

Завершение run, наличие установленного SKILL.md или сообщение executor не подтверждают outcome. Прими finite artifact только по exact subject, independent review/QA и target readback. Main/deploy/publishing/spend gates не меняются. Если результат неизвестен/не доставлен — так и запиши.

Первая natural validation этой методики: один настоящий responsibility increment проходит company brief → finite specialist output → независимый reviewer → exact consumer readback; в handoff есть действительный ACTION/WAIT/BLOCKED и disposition. Не запускай платную model probe и не называй fixture/static check доказанным live behavior.

## 9. Reference scope и первичные источники

Adaptation basis: https://learn.chatgpt.com/docs/dots/getting-started ; /docs/dots/tasks-and-memory ; /docs/dots/controls ; /docs/dots/computers-and-apps ; /docs/dots/channels ; /docs/enterprise/dots-admin-guide ; /docs/enterprise/cloud-local-access . Snapshot/provenance: `C:/Users/max/Desktop/all/ventures/docs/fleet-ops/dots-20261003/`.

Только методический перенос. Нет установленного OpenAI Dots, paid commitment, нового plugin/daemon/scheduler, изменённого routing/security/privacy policy или гарантии будущей agent obedience. При конфликте с актуальным каноном сохрани его, останови несовместимый шаг и re-scope карту; не переписывай канон по этой reference.
