# OpenAI Dots: исследование и решение для флота

Пакет начат 03.10.2026. Owner исследования и решения: company. Это brain-brief, а не утверждение о выполненном rollout или независимый QA PASS.

## 1. Что именно изучено

Под «новым dot-подходом из ChatGPT» в этой работе понимается **OpenAI Dots**, а не Chain/Tree/Diagram of Thought и не новая техника скрытого рассуждения. Первичные источники описывают постоянного агента, который получает ответственность, помнит существенный контекст, координирует исполнителей и возвращается к работе между разговорами. Это отдельный продукт/режим взаимодействия, не универсальное доказательство качества модели.

Прочитаны и сохранены основной обзор, старт, задачи/память, контроль, компьютеры/приложения, каналы, enterprise-администрирование и enterprise local-computer access. Индекс ChatGPT подтверждает шесть основных Dots-страниц и дополнительную страницу local access; администраторский guide связан из Controls. Исходные alias /codex/dots/... перенаправились на canonical /docs/dots/.... В `SOURCES.json` и `SOURCES-ADDENDUM.json` находятся URL, время, доступность и SHA256 фактических файлов. Семь первоначальных + одна дополнительная Dots-страница = восемь основных источников; пять поддерживающих = тринадцать файлов источников.

Важно: `chatgpt-permissions.md` — **Codex permission profiles**, не инструкция Dots и не формат Hermes Fleet Policy. Не переносить его TOML в конфигурацию флота. OpenAI-анонс извлечён лишь частично; help-статья 20001530 недоступна (403/timeout). Они не используются как полные первичные snapshots. Полнота здесь означает опубликованные перечисленные Dots-guides, а не весь ChatGPT, закрытую реализацию или испытание аккаунта.

Ни доступность Dots на наших аккаунтах, ни тариф/регион, ни его UI, cloud computer, качество выполнения или оплата не проверялись. Маркетинговые заявления не превращаются в measurements. Исследование документации отделено от использования внешнего сервиса.

## 2. Устройство подхода

| Элемент | Что действительно описано | Практическое значение |
|---|---|---|
| Responsibility вместо разового prompt | Агенту объясняют результат, источники, границы и условия вмешательства; можно вести несколько ответственностей | Продолжать цель, а не обнулять её после каждого ответа |
| Координатор + исполнители | Background agents, отдельные видимые Work/Codex/cloud threads; работа продолжается между разговорами | Общение владельца не должно блокироваться длинным исполнением |
| Проверка результата | Completed run сам по себе не доказывает achieved/delivered result | Нужны результат, ошибки, независимая приёмка и delivery readback |
| Scheduled work | Сохранённое расписание с задачей, time zone, duration/end date, условиями уведомления и destination | Фраза «проверять ежедневно» не создаёт действующее расписание |
| Event monitoring | Только когда источник поддерживает события и агент подтверждает регистрацию | Подключить Slack ≠ настроить watcher; нельзя обещать неподдерживаемый trigger |
| Proactive research | Read-only исследования и private notes; само исследование не отправляет сообщения и не меняет apps/browser/computer | Разделять discovery и разрешённый action, не расширять полномочия по находке |
| Контекст / память / заметки | Selected context, relevant ChatGPT memory, отдельные заметки агента; ни одно не является полной стенограммой | Durable task truth отделить от памяти; new worker получает точный пакет контекста |
| Каналы | Один dot через ChatGPT/Slack/Teams, но отдельные видимые диалоги; relevant context может использоваться между ними | Continuity не даёт права переносить private data на другую аудиторию |
| Computers / apps / messaging | Разные независимые подключения; cloud browser не наследует local sessions | Канал общения не capability; перенос выполнения не переносит session или старую задачу |
| Controls | Automatic action review, optional scoped custom rules, отдельные plugin permissions и built-in safeguards | Инструкция не sandbox и не обход требований; capability и action permission проверяются отдельно |
| Stop / pause / schedules | Pause main task, stop delegated tasks и cancel schedule — разные операции; completed actions не откатываются | Остановка — проверка всех частей ответственности, а не закрытие чата |
| Feedback | Уточнения и новые решения обновляют полезные заметки | Сохранять исправление в надлежащем task skill, не в глобальной памяти всё подряд |

Источники таблицы: [S2]–[S8] ниже. Более подробные правила остановки: Controls, строки 86–105; read-only proactive research: Tasks and memory, 125–138; completed run: там же 45–47; private sharing: 108–119.

## 3. Компьютеры, безопасность и эксплуатационные ограничения

Cloud computer может оставаться доступным, когда личный компьютер выключен. Local Work/Codex требует online connected device и работающего приложения. Смена выбранного компьютера не переносит существующие tasks. Установка plugins и подключение channel/device — независимые разрешения. Сохранённый login и действующая browser session — разные сущности; документация Dots требует confirmation для нового применения saved login.

Публичные правила OpenAI включают automatic review до account-affecting/sharing actions. Custom rules могут задавать четыре intended modes: действовать без вопроса; действовать при явном запросе, иначе спрашивать; спрашивать перед действием; передавать шаг пользователю. Эти правила сами не дают access, не отменяют built-in safety и могут быть исполнены ошибочно. Это не доказательство техизоляции и не шаблон для ослабления Fleet Policy.

Enterprise guide добавляет feature enablement, workspace/plugin permissions, approval policy, data retention и governance. Local-access guide различает cloud coordination и tool execution; локальные требования не являются автоматически контролями cloud computer. Requirements и defaults имеют различный статус; наличие policy в UI требует проверки supported fields, platform и effective enforcement. Мы не импортируем OpenAI Agent Security/MDM/TOML и не меняем Hermes policy.

Существенные оговорки именно для Dots в текущем enterprise beta [S8, 107–135]: нет data/inference residency; ограничения для FedRAMP/EKM/UAE inference-residency workspaces; нет strict zero data retention, и API ZDR не переносится на этот продукт. Local files/tool results/context всё равно могут использоваться cloud coordination. `PreToolUse` callback timeout/error/malformed response может провалить hook без блокировки tool; hooks не покрывают каждый internal subagent path и не дают полного audit trail. Shell/prompt/local-directory/environment-scoped hooks при cloud orchestration не эквивалентны local-only Work/Codex. Поэтому наш local Fleet Policy/hook нельзя считать автоматически перенесённым в OpenAI Dots: реальное подключение потребовало бы отдельного security/privacy review и positive/negative enforcement tests. В этой интеграции подключения нет.

Private notes, training/data controls, workspace/audit settings — продуктовые свойства OpenAI в документированных пределах, не гарантии нашего флота. Любая реальная передача флота/личных данных внешнему Dots, подключение устройства или нового доступа — отдельный capability/security/privacy scope. В этом внедрении такой передачи нет.

## 4. Что у нас уже есть и что стоит перенести

| Dots-принцип | Существующий канон флота | Изменение этого пакета |
|---|---|---|
| Постоянный ответственный координатор | company, product owner, CHARTER/STATE, одна активная ставка | Явный responsibility envelope в существующем STATE/карте, не новая DB |
| Делегирование | Native Kanban dispatcher, специалисты, producer→QA→consumer | Отдельно формулировать результат ответственности и конечный deliverable worker |
| Работа между разговорами | Durable Kanban, native background/cron | WAIT с реальным зарегистрированным wake, а не обещание «сам вернусь» |
| Proactive research | research, scouts, watchers | Read-only finding→bounded recommendation; action только в прежнем mandate |
| Persistent context | Repo docs, task handoff, skills, selective memory | Компактный handoff без полных transcripts/секретов; corrections в relevant skill |
| Multi-channel continuity | Company entrypoint, board/task truth, established routing | Один canonical outcome_ref и authorized destination, без нового sender/channel |
| Permission review | APPROVALS.md, Fleet Policy, independent QA/finance | Только пояснение: access ≠ permission, draft ≠ send, completion ≠ acceptance |
| Controls / observability | Kanban runs, task context, evidence, rollback | Stop protocol охватывает children, wakes, schedules и uncertain side effects |

Новизна — **сборка существующих механизмов в ясный долгоживущий responsibility contract**, особенно различение research/action, WAIT registration, context/audience и полного stop. Не обещать «реализовали Dots»: product runtime, cloud computers, voice и OpenAI plugins не устанавливаются.

## 5. Интеграционное решение

**GO:** исходная, самостоятельно написанная методика `dots-operating-method.md` как reference существующего `company-os` во всех двенадцати рабочих профилях из `TARGETS-BASELINE.json`; небольшой load-hook в каждом существующем SKILL.md. Компания остаётся brain/accountable owner; operations — единственный hands-owner установки; research — независимая верификация source claims; qa — независимая приёмка точных файлов и границ; company — consumer проверенного результата.

**NO-GO в этом scope:** установка продукта Dots, новый paid plan, новые model/provider pins, OpenAI cloud/local access, новые plugins/connectors, новый scheduler/watcher/daemon, cron/model/pool/config/DB edits, второй реестр задач, чтение secrets или массовое изменение существующих карт. Текущее восстановление автокомпании `t_66a85749` и `t_4aabc1fb` не заменяется этим пакетом; проектные gates/main/deploy остаются отдельными. Не выдавать методическую установку за доказанный ремонт runtime.

Файлы интеграции: `METHOD-CANDIDATE.md` (канонический reference), `LOAD-HOOK.md` (единственная вставка в SKILL.md), `TARGETS-BASELINE.json` (точный allowlist), `ROLLOUT-SPEC.md` и `QA-SPEC.md`. Существующие разных версий company-os не выравниваются копированием whole root. Перед каждым patch — свежий SHA; при drift остановить этот target, не затирать конкурентные изменения. Collision нового reference запрещает overwrite без разбора. Backup только изменяемых файлов; rollback удаляет только собственный новый reference и восстанавливает собственный hook, сохраняя чужие более поздние изменения.

## 6. Acceptance и предел доказательств

1. Research читает все восемь Dots-источников и candidate, выдаёт `SOURCE-AUDIT.md` с fact→URL/section mapping, PASS/FAIL и явными gaps. Указанный Codex источник не принят за Dots.
2. Operations устанавливает reference и hook ровно в двенадцать allowlisted skill roots, сохраняет before/after hashes, diff, path, backup и process exit codes; счётчики проверяет программно. Иные профили/файлы не меняются.
3. QA независимо сверяет `12/12` references с exact accepted candidate hash, загрузочные hooks и сохранность каждого original root после удаления hook. Проверяет отсутствие разрешений на запрещённые изменения и executes deterministic integrity checks. Filesystem check ≠ доказательство future agent obedience.
4. Natural producer/reviewer runs применяют envelope к собственной этой ответственности, выдают ACTION/WAIT/BLOCKED и evidence с original scope. Actual reference load в operations/qa фиксируется tool output, не заявлением автора. Никаких платных synthetic inference probes.
5. Consumer читает actual targets и независимые verdicts. При PASS — методический rollout принят; поведенческая польза на следующем естественном проектном исходе остаётся измеряемой гипотезой, а не фабрикованным результатом.

Hypothesis: explicit responsibility contract уменьшает бессмысленные follow-ups, скрытые WAIT и scope leakage; primary observation — independently accepted responsibility with next disposition and no manual owner dispatch. Baseline effect/latency/token savings = null; не измерены. Confidence в source mapping: средняя до research review; effect: низкая до реального применения. Kill: противоречие действующему mandate, неподдерживаемая capability, drift/collision, самопринятие, обещание несуществующего wake или изменение вне allowlist. В таких случаях STOP + same-lane correction; no repeated unblock.

## 7. Деньги и handoff

Financial scope: fleet-ops, внутреннее методическое внедрение, период от начала пакета 03.10.2026 до приёмки. Source: tool receipts и scope этой работы; finance/billing API не запрашивались. Confirmed revenue=null (это не продуктовый revenue experiment); refunds=null (не собирались); incremental paid costs=null (нет bill/readback); estimated usage cost=null (inference accounting не извлечён); new paid commitments=0 (пакет их запрещает и не создаёт). Отсутствие нового заказа не означает стоимость inference 0 ₽.

Окончательное состояние: PENDING source audit, hands rollout и independent QA. Этот документ не является самостоятельным gate или completion. Decision-owner company закрывает ответственность только по реальным handoffs и readback; фоновые роли не перекладывают routine questions на владельца.

## Первичные ссылки

- [S1] Overview: https://learn.chatgpt.com/docs/dots
- [S2] Getting started: https://learn.chatgpt.com/docs/dots/getting-started
- [S3] Tasks and memory: https://learn.chatgpt.com/docs/dots/tasks-and-memory
- [S4] Controls: https://learn.chatgpt.com/docs/dots/controls
- [S5] Computers and apps: https://learn.chatgpt.com/docs/dots/computers-and-apps
- [S6] Channels: https://learn.chatgpt.com/docs/dots/channels
- [S7] Enterprise guide: https://learn.chatgpt.com/docs/enterprise/dots-admin-guide
- [S8] Local computer access: https://learn.chatgpt.com/docs/enterprise/cloud-local-access
- Index: https://learn.chatgpt.com/docs/llms.txt
- Hermes capability authority: https://hermes-agent.nousresearch.com/docs/ ; supporting snapshots канбан/память в SOURCES.json. Installed runtime не переаттестован.
