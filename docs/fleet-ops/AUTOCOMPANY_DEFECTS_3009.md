# AUTOCOMPANY DEFECTS — 30.09.2026

Реестр недоработок автокомпании по итогам полного sweep (запрошен владельцем 30.09).
Метод: `hermes kanban diagnostics` + `dispatch --dry-run` по 8 доскам, show-опрос 48 blocked-карт,
чтение исходников respawn-guard (`hermes_cli/kanban_db_dispatch.py`), pool guard + metadata-проба пула.
Все утверждения ниже имеют tool-evidence от 30.09.2026 18:00–21:00 RTZ2.

## ВЕРДИКТ ПО КВОТЕ GPT (владелец: «квоты должно хватать» — ПОДТВЕРЖДЕНО)
- Пул openai-codex: 2 PLUS креда (pri0/pri1), GUARD: PASS, `limit_reached=None`, активных model-cooldowns НЕТ.
- «Quota wall» на t_f28982d3 — событие 28.09 (окно Z.AI/GLM 429 в qa-лэйне + пул), давно прошло.
- Карта держится НЕ квотой, а stale-ловушкой respawn-guard (дефект D1). Квота достаточна.
- Замечание: switcher n=8 vs live pool n=2 — 6 аккаунтов в coldstore (решение владельца 25.09).
  Расширение состава пула = только решение владельца.

## REMEDIATION LOG — 30.09 turn-2 (исполнено company, verified)
- Оживлены 6 мёртвых карт (readback: все running/ready):
  - t_9c461308 (blocker_auth retest, 17ч простаивала на missing task_type) → RUNNING
  - t_523c4c93 (freelance rails inventory, 301ч на missing task_type) → RUNNING
  - t_a1565747, t_67e1a175, t_62fd4ed9, t_6ba71b0a (4 crash-лупа в triage) → specify → running/ready
- Заведена системная tech-карта **t_1b5e3e56** (fleet-ops, @tech, task_type: code): infra-kill
  (gateway drain/nightly restart → terminal_worker_reaped) должен REQUEUE без зачёта провала,
  не crash→triage. Readback: на fleet-ops, маркер intact, assignee tech. Spec:
  ventures/docs/fleet-ops/specs/infra-kill-requeue-3009.md
- Пул GPT: guard PASS + metadata-проба (квота достаточна). Агенты здоровы (спавны capped, ~11 завершений 30.09).

## CENSUS — 48 blocked по 14 deny-классам (30.09, tool-evidence)
| Класс | N | Лечение |
|---|---|---|
| needs_input (owner/handoff) | 15 | часть = слово владельца (5), часть = handoff-маршрут company |
| initial_status / wake-condition | 7 | проверить wake-условия; time-gate t_d4f0152b (382ч) перезрел |
| policy_control_plane_mutation | 5 | rescope спека в repo-branch proposal (не live-контроль) |
| evidence_gate_missing (+2 nonce) | 6 | GO-якорь binding; корни RR-цепочки (гейтятся решением PR242) |
| worker_code_execution | 3 | rescope в tool-based flow (гранты запрещены 16.09) |
| gate_forgery | 3 | company-разбор по event-log |
| secret_read_or_write | 2 | rescope на легальный маршрут (env-only токены) |
| missing_or_unknown_task_type | 2 | ИСПРАВЛЕНО company (t_9c461308, t_523c4c93) |
| irreversible_data_loss | 1 | слово владельца (t_be62f94d) |
| budget_exhausted | 1 | слово владельца (t_4fb46ca3, 420ч) |
| transient/capability/other | 3 | cooldown (штатно), capability-маршрут, zai429-дрейф |
Отдельно: **43 карты в triage** (fleet-ops 18, rr-team 12, venture-lab 4, portfolio 2 + recovered) —
не диспетчеризуются (dispatcher берёт только ready). Слепой specify --all НЕ безопасен (version-churn
+ «сбор без исполнения» в venture-lab) → нужен умный авто-triage-recovery (см. план).


## D1. BLOCKER_AUTH STALE-STAMP TRAP (Hermes bug) — КРИТИЧЕСКИЙ, подтверждён dry-run
- СТАТУС ФИКСА 30.09 21:32: retest-карта t_9c461308 DONE — company-воркер установил авторитетную
  модельную независимость (author tech=qwen3.8-max runs 1829/1836, brain=gpt-6.1-sol → единственная
  валидная positive-stamp модель = qa primary glm-5.3/zai; qwen и sol ЗАПРЕЩЕНЫ для положительной
  печати; негативные вердикты валидны под любой моделью). Маршрутизированы: t_72d9f80e (независимый
  exact-SHA QA-ретест fc2fa0c53f, 8 проверок, 42/42 focused battery) → t_159f1f52 (company-решение:
  валидация независимости вердикта + promotion routing). Кандидат STAGE-ONLY (live HEAD 31c5d57ec6
  не тронут); merge только через consumer-карту с полной gate-цепочкой.
- ВНИМАНИЕ: t_72d9f80e сейчас throttled Z.AI/GLM 429 (last_fail «pid 3152 exited rate-limited quota
  wall»). Система обрабатывает корректно: latest run=rate_limited → rate_limit_cooldown путь (retry
  spaced, НЕ вечный park) — в отличие от t_f28982d3, где latest=changes_requested → blocker_auth trap.
  Rollout D1 дождётся восстановления zai-квоты; sol-дрейф для positive-stamp верно запрещён.

- Механизм: rate-limit requeue штампует `last_failure_error` «…quota wall…» без зачёта провала;
  последующий успешный run (`changes_requested`/`review_requested`/`completed`) штамп НЕ стирает;
  guard `check_respawn_guard` (kanban_db_dispatch.py:1586–1589) матчит `_RESPAWN_BLOCKER_RE`
  (`\b(quota|rate-limit|429|auth|…)\b`) по СТАРОМУ тексту → `blocker_auth` БЕЗ TTL → вечная парковка.
  Защита rate_limit_cooldown (строки 1569–1580) срабатывает только если ПОСЛЕДНИЙ run = rate_limited.
- Жертва (сейчас одна на весь флот, dry-run по 8 доскам): t_f28982d3 (rr-team, ready 56.8ч,
  «RR cabinet → Linear-grade ideal»). Run #10 rate_limited 28.09 14:21 → run #11 changes_requested
  28.09 14:37 → с тех пор 0 спавнов. Диспетчер сегодня: 81 stuck-tick `held back: blocker_auth`.
- ФИКС УЖЕ ЕСТЬ: staged-коммит fc2fa0c53f (branch fix/blocker-auth-ttl-f1f2-t_cdd8d1b9, local only,
  live не тронут) — rework QA NO-GO findings F-1/F-2 от кандидата 54a138f7b1.
- СТАТУС 30.09 20:35: retest-карта t_9c461308 была мертва 17ч из-за отсутствия `task_type:` в первой
  строке тела (missing_or_unknown_task_type ci=1). Company исправил тело + unblock → карта RUNNING.
  Дальше: вердикт retest → при GO rollout в live → t_f28982d3 освободится сам.

## D2. ТИХИЙ ДЕДЛОК ПОДДЕРЕВЬЕВ (dependency gating без эскалации)
- `recompute_ready` (kanban_db.py:2188) promotes todo→ready ТОЛЬКО когда все родители done/archived.
  Заблокированный корень морозит всю цепочку потомков в todo БЕЗ единого алерта.
- Масштаб: fleet-ops 50 todo, rr-team 26, seo-site 5, video 2, portfolio 2 — возраст 10–17 дней.
- Пример: RR PR242 — корень t_8a4d4f03 (ждёт решение владельца 106ч) → t_e1062f20 → QA/owner-preview/
  merge-карты (t_81696f76, t_f0202ff8, t_8163213a, t_4dc329cc…) — ~15 карт стоят молча.
- Недоработка: нет вотчера «поддерево заморожено > N дней» и нет агрегации в owner-digest.

## D3. ЗАПРОСЫ РЕШЕНИЙ ВЛАДЕЛЬЦА НЕ ДОХОДЯТ ДО ВЛАДЕЛЬЦА
- Карты с needs_input «нужно решение владельца» лежат в канбане без доставки:
  t_8a4d4f03 (106ч), t_4fb46ca3 (420ч!), t_f9b89160 (129ч), t_be62f94d (24ч), t_0d1c79f5 (130ч).
- Секция «👑 Слово милорда» в OWNER-INBOX не агрегирует kanban-блоки → владелец узнаёт о висящих
  решениях только спросив сам (этот диалог — доказательство).
- Фикс-план: ежедневный sweep blocked(needs_input/owner-маркеры) → owner_inbox (не print/send напрямую).

## D4. POLICY-СТЕНЫ С ЖИРОСЖИГАЮЩИМИ ЛУПАМИ (call_index-марш)
- Работник повторяет запрещённое действие ДЕСЯТКИ раз до финального блока:
  evidence_gate_missing ci=119 (t_ee208805), gate_forgery ci=106 (t_2899e1ed), ci=72 (t_1a68eede),
  ci=70 (t_6f920d4f), ci=46 (t_49b32419), worker_code_execution ci=40 (t_274e8966),
  secret_read_or_write ci=36 (t_5a542ba5), irreversible_data_loss ci=31 (t_be62f94d), и др.
- Недоработка: нет раннего deny-breaker (стоп после 2–3 одинаковых deny + авто-карта rescope).
  Дисциплина same_failure_loop есть в доктрине company, но не enforcement в воркер-рантайме.

## D5. GO-ЯКОРЯ НЕ ПРИВЯЗАНЫ (корень #2 от 25.09 всё ещё жив)
- 4 карты 220+ч на evidence_gate_missing: t_ee208805 (222ч), t_6f920d4f (223ч), t_fabf97d6 (258ч),
  t_ca56be86 (223ч); + 2 review_probe_nonce-обёртки: t_4a5b52f1 (22ч), t_fd605212 (21ч).
- Лечение по канону: якорь decision:company=go head=<sha> отдельным комментарием НА ТОЙ ЖЕ карте,
  не re-unblock. Часть карт устарела по head — нужен re-anchor sweep с актуальными SHA.

## D6. ДЕФЕКТЫ АВТОРСТВА КАРТ
- completion_contract с литеральным плейсхолдером «OWNER/REPO»: t_27fb939d — работа ГОТОВА
  (PR #51, head d033221c, verify success, 830 passed ×2), но kanban_complete отклоняется 30ч.
  Валидатор card_readiness.py плейсхолдеры контракта не ловит.
- missing task_type: t_9c461308 (17ч) и t_523c4c93 (301ч!) — ОБЕ ИСПРАВЛЕНЫ company 30.09 20:30
  (prepend маркера + unblock + readback: обе RUNNING).
- Вывод: пре-диспатч валидатор нужно применять и к company-созданным картам, и к contract-полям.

## D7. ПРОСРОЧЕННЫЕ TIME-GATE НИКТО НЕ ПРОВЕРЯЕТ
- t_d4f0152b «QA time gate: 168h SHADOW soak» — blocked 382ч; soak истёк ~214ч назад; статус не пересмотрен.
- t_c0635a88 (Jev wave1) — 176ч initial_status; portfolio wake-conditions t_c271e06b/t_71002457 — 257ч,
  ждут rollout t_498a2d8f Phase R (проверить статус rollout и разбудить/закрыть).
- Недоработка: нет check_at-вотчера для time-gated карт.

## D8. TRIAGE-LANE CRASH-ЛУПЫ
- t_67e1a175 (seo-site, 4× CRITICAL «pid not alive»), t_62fd4ed9 (rr-team 2×), t_6ba71b0a (rr-team 2×),
  t_a1565747 (fleet-ops 2×). Карты висят в triage без авто-ремонта и без эскалации.

## D9. QA-ЛЭЙН: ДРЕЙФ МОДЕЛЕЙ + ATTESTATION-ЗАЗОРЫ
- zai/GLM 429 → дрейф на Sol: t_61c28da2 (judge: «rate-limited by Z.AI HTTP 429», turn budget 6/6).
- Аттестация моделей не сходится с пином: t_34b4af08 (run=GPT-6 Sol при primary GLM-5.3, нет
  подтверждённого отказа primary → QA-печать удержана), t_f3d3b319 (attestation found=false).
- Resume-guard карта t_90fbcdec сама заблокирована (policy_control_plane_mutation ci=29, 12ч).
- Следствие: QA-вердикты не ставятся → merge-цепочки стоят (в т.ч. PR242, PR198).

## D10. PR-ACCEPTANCE ГЕЙТ ЯДРА ПАДАЕТ НА ВАЛИДНОМ PR (Hermes bug)
- t_e22b2313: hotfix доставлен (PR8 head 4f3e9401, exact-head CI verify+py36-runtime SUCCESS),
  но kanban_complete невозможен: kanban_pr_acceptance.py:64 делает GET /repos/maximal… и
  детерминированно падает → 57ч. Нужна отдельная tech-карта с диагнозом (wrong owner/repo resolution?).

## D11. DISPATCHER-STUCK АЛЕРТЫ ТОЛЬКО В ЛОГ
- 81 stuck-tick за 30.09 в gateway.log, ни одного уведомления company/owner.
  Аномалия «ready-очередь есть, спавнов нет» должна идти во internal-журнал/owner-inbox.

## D12. TRANSIENT/CAPABILITY-БЛОКИ БЕЗ МАРШРУТА ОБХОДА
- t_afe35c1f: VK SSL connection-block (cooldown по ACCESS.md — штатно, transient).
- t_0d1c79f5: TikTok UK-egress сломан — socks5 127.0.0.1:10808 занят Incy VPN (требует auth,
  Donut не хранит auth); других UK-выходов нет. Варианты: auth/порт от владельца ИЛИ альтернативный
  UK-egress ищет компания. 130ч.
- t_1d575a91: runtime запуска запрещает skill-edit → COMPANY_RESCOPE не завершаем; нужен запуск
  с правом правки и точные пути PLAN/skill.
- t_93520136/t_4a5b52f1/t_fd605212: QA-прогоны упираются в review_probe_nonce — нужен разрешённый
  маршрут DB-тестов/read-only аттестации (без повторения deny).

## ЧТО ЖДЁТ СЛОВА ВЛАДЕЛЬЦА (свод на 30.09 20:40)
1. RR PR242 pass-8 (t_8a4d4f03, 106ч): (a) владелец токенизует pass-8 сам, или (b) авторизовать
   второй value-preserving коммит (999px→--radius-pill; 6/7px→canonical-токены) с переанкерингом
   acceptance на head 1d32431d. Держит всю merge-цепочку PR242 (~15 карт).
2. Free-GPT пул (t_f9b89160, 129ч): вариант B одобрен 25.09; ждём сигнал о добавлении free-акков.
3. Бюджет (t_4fb46ca3, 420ч = 17.5 суток): «Гигиена RR live-репо после восстановления 725 удалений» —
   hard budget wall_clock исчерпан; продлить бюджет или закрыть карту.
4. Необратимая операция (t_be62f94d, 24ч): «RR Phase 0: PR-очередь 237/235/223/238/226 до merge-ready» —
   policy-блок irreversible_data_loss ci=31; санкционировать с backup-гейтом или перескоупить.
5. TikTok egress (t_0d1c79f5, 130ч): Incy VPN занял socks5-порт и требует auth — дать auth/освободить
   порт, либо поручить компании найти альтернативный UK-выход (публикации TikTok×3 стоят).
6. В очереди за PR242 (придут после разблокировки цепочки): owner-preview t_4dc329cc, t_2f28ff35,
   owner visual verdict t_f0202ff8.

## УЖЕ СДЕЛАНО COMPANY В ЭТОМ ПРОХОДЕ (30.09 20:25–20:40)
- t_9c461308: тело исправлено (task_type: review) + unblock → RUNNING (retest фикса D1).
- t_523c4c93: тело исправлено (task_type: research) + unblock → RUNNING (301ч простоя снят).
- Пул GPT: guard PASS + metadata-проба (квота достаточна, cooldowns пусты).
- Полный sweep: 48 blocked классифицированы, dry-run по 8 доскам (единственная parked-карта — t_f28982d3).

## ПЛАН ЛЕЧЕНИЯ (автономно, без слова владельца)
1. Дождаться вердикта t_9c461308 → при GO rollout blocker_auth TTL фикса → t_f28982d3 оживает.
2. Owner-decision digest: sweep needs_input с owner-маркерами → OWNER-INBOX «👑 Слово милорда» (D3).
3. Re-anchor sweep 4 evidence_gate_missing карт с актуальными SHA (D5).
4. Rescope 3 worker_code_execution карт под tool-based flow (гранты не выдаём — запрет 16.09) (D4).
5. Разбор gate_forgery ×3 по event-log (t_2899e1ed, t_9ca672e0, t_49b32419) (D4).
6. t_27fb939d: починить completion_contract (плейсхолдер OWNER/REPO) и принять готовый PR#51 (D6).
7. Time-gate sweep: t_d4f0152b (soak истёк) — проверить evidence и снять/закрыть (D7).
8. Tech-карта на kanban_pr_acceptance.py:64 bug (D10).
9. Triage crash-лупы: диагностика 4 карт, ремонт/закрытие (D8).
10. Frozen-subtree вотчер + dispatcher-stuck алерт во internal-журнал (D2/D11).
