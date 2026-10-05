# SOURCE-AUDIT — Dots methodology candidate (t_f41c3c15)

Date: 2026-10-04 (UTC+03:00)
Auditor: research (independent; не автор STUDY.md / METHOD-CANDIDATE.md / LOAD-HOOK.md — это company brain artifacts)
Subject: METHOD-CANDIDATE.md sha256=f2a85ced87b620bf08cdfc2f3de85ce004a2912efded4da85b668148f00dce6f, sha1=fd6c26f5dbebba33baa17761f43a80e22ed17427
Scope: content/source accuracy PASS|FAIL. Не QA gate, не разрешение rollout, не внедрение.

## VERDICT: PASS (content/source accuracy)

Все 8 первичных Dots-источников прочитаны полностью; supporting docs прочитаны по релевантным claims. Существенные claims STUDY.md и METHOD-CANDIDATE.md подтверждены canonical URL + разделом. Несоответствий действующему fleet mandate не обнаружено. Найдены только мелкие неточности в диапазонах строк одной строки-карты STUDY (см. Corrections, не блокируют).

## 1. Integrity (файлы и hashes)

Проверено sha256sum через terminal (exit 0):

- Manifests: SOURCES.json b4c56561… ✓, SOURCES-ADDENDUM.json 8b694582… ✓, TARGETS-BASELINE.json 5a10cadc… ✓ — совпали со spec.
- BRAIN-PACKET members: STUDY.md b466f497…, METHOD-CANDIDATE.md f2a85ced…, LOAD-HOOK.md 2e10a1c6…, SOURCE-AUDIT-SPEC.md 906ae6b7…, ROLLOUT-SPEC.md 5cfea6cb…, QA-SPEC.md 0a72c6f7…, CONSUMER-SPEC.md 2d57bce2… — все совпали с BRAIN-PACKET.json. candidate_content_sha1 fd6c26f5… совпал с sha1sum METHOD-CANDIDATE.md.
- 13 source files в sources/ — все 13 sha256 совпали с манифестами (sha256sum -c: 13× OK, exit 0). Никаких модификаций входов с момента заморозки.

Count: 8 core Dots sources (7 из SOURCES.json + 1 из SOURCES-ADDENDUM.json), 5 supporting (chatgpt-docs-index, chatgpt-permissions, hermes-docs-index, hermes-kanban, hermes-memory). Дедупликация не требуется — все path уникальны (проверено листингом + manifest count).

## 2. Fact → source mapping (каждый существенный claim)

Все URL — learn.chatgpt.com, retrieved 2026-10-03 ~20:54–20:56 UTC (manifest), прочитаны из локальных frozen копий с совпавшими hash.

| # | Claim (STUDY/candidate) | Canonical source | Раздел / строки frozen файла | Verdict |
|---|---|---|---|---|
| 1 | Responsibility > одиночный prompt; correction перед расширением | dots#work-with-your-o | dots-overview.md «Work with your dot» 175–197 («Review the first result and correct any missing details before expanding the responsibility») | CONFIRMED |
| 2 | Делегирование: отдельный thread / task-local context (не вся переписка) | dots/tasks-and-memory#assigned-work | dots-tasks-memory.md 16–47; явно 40–43 («A new task receives instructions and context from your dot for that work. It has its own conversation; it doesn't automatically receive every conversation») | CONFIRMED |
| 3 | Saved schedule + event triggers | dots/tasks-and-memory#recurring-tasks | dots-tasks-memory.md 49–78 (Recurring tasks 49–69; Event monitoring 71–78; «Connecting Slack or another source alone doesn't create a monitoring task») | CONFIRMED |
| 4 | Completed run ≠ результат; review после завершения | dots/tasks-and-memory + dots/controls#review-work | dots-tasks-memory.md 45–47 («A completed run doesn't by itself confirm that the requested result was achieved or delivered»); dots-controls.md 9–19 | CONFIRMED |
| 5 | Proactive research read-only | dots/tasks-and-memory#proactive-research | dots-tasks-memory.md 125–138 («This background research … doesn't send messages, change connected apps, or control a browser or computer») | CONFIRMED |
| 6 | Отдельные saved notes ≠ полный transcript; смена ChatGPT memory setting не переписывает notes | dots/tasks-and-memory#persistent-memory | dots-tasks-memory.md 97–107 («These notes are separate from ChatGPT's saved memory and are not a complete transcript»; «Changing a ChatGPT saved-memory setting doesn't necessarily change the notes») | CONFIRMED |
| 7 | Cross-channel continuity ≠ авторизация публикации новой аудитории | dots/tasks-and-memory#across-messaging-channels | dots-tasks-memory.md 108–123 («doesn't grant permission to disclose it to another audience… sharing private details in a team channel still requires permission») | CONFIRMED |
| 8 | Device/app/session separation (cloud computer ≠ личный компьютер ≠ signed-in browser) | dots/computers-and-apps | dots-computers-apps.md 5–25, 62–90; dots-overview.md 107–123 (таблица connection purposes; «Connecting a messaging channel doesn't also connect your inbox, other apps, or local computer») | CONFIRMED |
| 9 | Permission review: automatic action review, может требовать approval или hand over | dots/controls#how-action-review-works | dots-controls.md 21–37 («an automatic review checks it against your instructions, permissions, custom rules, and built-in safety requirements… can proceed, needs your approval, or includes a step you must do yourself») | CONFIRMED |
| 10 | Full stop: Pause / delegated task stop / cancel schedule — раздельные действия | dots/controls#stop-work | dots-controls.md 86–97 (таблица различий Pause vs Activity stop vs Scheduled cancel; «Stopping work doesn't undo completed actions») | CONFIRMED |
| 11 | Enterprise/cloud-local policy scope: enforce_residency блокирует local access; residency/EKM/FedRAMP/AE exclusions; hooks/network precedence | enterprise/cloud-local-access | dots-enterprise-local-access.md прочитан полностью (219 строк): eligibility 107–113, residency safeguard 115–123, hooks 125–135, policy precedence 79–101, OTel/Compliance 178–186 | CONFIRMED (глава 4 spec выполнена: документ прочитан целиком, не только первая часть) |
| 12 | Custom rules: четыре режима, не отменяют built-in safety | dots/controls#set-custom-rules | dots-controls.md 39–73 (таблица 51–56; «They don't grant access… override built-in safety requirements») | CONFIRMED |
| 13 | Admin rollout: role-based access, отдельный opt-in для local computer, Slack enable не устанавливает app | enterprise/dots-admin-guide | dots-enterprise-admin.md 43–77, 99–107; FAQ 224–246 | CONFIRMED |
| 14 | Availability/plan/region/mobile/preview ограничения | dots#access | dots-overview.md 234–246 (Pro 100/200/500: 18+, вне EEA/UK/CH; Business Premium worldwide; Enterprise worldwide, off by default; mobile app — «when the supporting update is available», mobile web не поддерживается; «Dots are rolling out gradually. You may not see dots immediately, even if your plan is eligible») | CONFIRMED |
| 15 | Rollout/runtime limits кандидата: no Slack/Telegram connect, no accounts/devices, no Dots install | внутренний self-limit кандидата (§Rollout/runtime limits) | Согласуется с источниками: candidate нигде не заявляет фактическую доступность Dots на наших аккаунтах и не обещает каналы. Отдельно подтверждено источниками: Teams = «invite-only alpha» (dots-enterprise-admin.md 244), texting = «coming soon» (dots-channels.md 29), outbound dot calls = «planned for after launch» (dots-channels.md 13) — candidate эти ограничения не нарушает и не обещает обратного | CONFIRMED |
| 16 | Hermes-side claims кандидата: native Kanban dispatcher владеет eligibility/claim/spawn/recovery; delegate_task — ephemeral; shared memory перезагружает решающего | hermes/kanban, hermes/memory | hermes-kanban.md 116–138 (Kanban vs delegate_task таблица; dispatcher loop: reclaim stale/crashed, promote); hermes-memory.md 56 (per-profile memory scope), 95 (skill vs memory budget) | CONFIRMED |

## 3. Contamination checks (spec пункт 3)

- DoT (directly observed treatment) reasoning vs Dots product: STUDY.md корректно разводит — DoT-аналогия упомянута только как framing источника метода (sustained responsibility, review gaps), не как claim о продукте Dots. В candidate смешения нет.
- Codex permissions.md не принят за Dots/Hermes configuration: candidate правильно маркирует его «[codex-not-dots]… Do not apply to Dots or Hermes» и использует только для deny-first/least-privilege/blast-radius модели. STUDY фиксирует ту же границу. Проверено чтением chatgpt-permissions.md — документ действительно про Codex local sandbox profiles, отдельная система; кандидат не переносит его как конфигурацию Dots/Hermes. CONFIRMED.
- Enterprise local-access guide прочитан полностью (все 219 строк, включая hooks, OTel, end-user experience), а не только первая часть. CONFIRMED.
- Внешнее содержимое из источников не выполнялось; linked docs (agent-security, compliance-api и т.п.) не retrieve'ились — для оценки claims кандидата они не требуются; candidate сам явно отказывается от cloud/agent-security действий.

## 4. Соответствие действующему fleet mandate

Проверено против AGENTS.md / company-os skill / fleet-policy plugin context:

- Candidate усиливает существующие gates (Kanban review/release, QA, fleet-policy) и явно говорит «не обходить gate». Конфликтов нет.
- R0: «research owns no fleet-policy gate… never write gate:<name>=pass markers» — помечено как fleet context, не как claim из Dots-источников; корректно.
- Нет claims о revenue/savings; финансовые неизвестные сохранены (ROLLOUT spec: costs=null). Кандидат не содержит ₽ savings claims.
- Bans соблюдены мной при аудите: ничего не менял в inputs/profiles/config/DB; cards не создавал; secrets не читал; state-changing действий вне задачи не было.

## 5. Corrections / gaps (не блокируют PASS)

1. STUDY.md строка-карта «Full stop: Controls 86–105» — фактический раздел «## Stop work» занимает строки 86–97; 99–105 это «## Delete your dot». Содержание claim'а верно (оба раздела релевантны остановке), диапазон неточен. Рекомендация: читать как «Controls 86–105 (stop work + delete)».
2. STUDY.md «private sharing: Tasks and memory 108–119» — раздел «### Across messaging channels» занимает 108–123. Содержание подтверждено.
3. Кандидат ссылается на «Hermes deliverables artifacts receipt idempotency» (R6, строка 34) без привязки к конкретной строке hermes-kanban.md — механика подтверждается hermes-kanban.md 135 (artifacts staging) и 103–110 (recovery/completion), но это общее fleet-знание, не verbatim quote. Приемлемо для методологического адаптивного документа; зафиксировано как gap низкой важности.
4. «GPT-6 Astra» (dots-overview.md 12) — candidate не делает model claims; корректно не использует. Не gap, просто зафиксировано что доступность наших аккаунтов нигде не подтверждена — candidate это явно оговаривает.

## 6. Count verified

- Core Dots sources прочитаны полностью: 8/8 (overview, getting-started, tasks-memory, controls, computers-apps, channels, enterprise-admin, enterprise-local-access).
- Supporting прочитаны по релевантным claims: 5/5 (chatgpt-docs-index — Dots index 112–118 + local-access 140 ✓; chatgpt-permissions — полностью; hermes-docs-index — не цитирован существенными claims, пропуск допустим; hermes-kanban — claims 16; hermes-memory — claims 16).
- Hash-верификация: 3 manifest + 7 packet members + 13 sources = 23 файла, все OK.

## 7. Disposition

PASS content/source accuracy для METHOD-CANDIDATE.md @ sha256 f2a85ced… (sha1 fd6c26f5…).
Это НЕ QA PASS, НЕ разрешение live changes, НЕ внедрение. Parent DONE сам по себе не acceptance для t_87ddea42 — operations обязан дождаться именно этого verdict по точному subject, что и зафиксировано в его карточке company-комментарием (decision:company=go с conditional authority).

Next action: native dependent operations task t_87ddea42 (owner: operations) — install после этого PASS; затем independent consumer QA t_a3c78661 (owner: qa), final consumer t_895a7d39 (company). Исходное внедрение остаётся accountability company.

Financial scope: fleet-ops; period 03.10.2026 start → эта приёмка; source = task/tool receipts (этот run). Revenue/refunds/incremental costs/estimated usage = null (billing/revenue не измеряется в этой задаче). New paid commitments = 0. Никаких ₽ savings claims.
