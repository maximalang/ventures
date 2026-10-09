# PROBLEMS_SWEEP_0110 — проблемы автокомпании и агентов 28.09–01.10, причины

Автор: company. Основание: запрос владельца 01.10 16:20 (тред 131). Метод: read-only sweep — gateway/errors/agent логи, kanban-доски (8), incident-доки, AUTOCOMPANY_DEFECTS_3009.md (D1–D12), FLEET-UPDATE-AUDIT.md (F1–F6), NEW-DEFECTS.md (N1–N2), KANBAN_TENANT_DIAG_2909.md, qa-compressor-independence-3009.md, LINEAGE_READBACK.md, OFFICIAL-RECOVERY-BASELINE.md. Все числа — из tool-выводов 01.10 16:31–16:45 RTZ2.

## A. Диспетчер и воркеры (live, деградация)

### A1. Dispatcher-stuck лупы — 293 warning за 3 дня, сегодня до 46 stuck-ticks подряд
- Evidence: gateway.log «kanban dispatcher stuck: ready queue non-empty … 0 workers spawned. Last tick held back: active_pr=1, blocker_auth=1» (06:31–16:33 01.10, каждые 5–8 мин); утром также rate_limit_cooldown=1–3, rate_limited=2.
- Причина-цепочка (D1, Hermes bug «blocker_auth stale-stamp trap»): rate-limit requeue штампует last_failure_error «quota wall» без зачёта провала → успешный run штамп НЕ стирает → guard check_respawn_guard (kanban_db_dispatch.py:1586) матчит старый текст → blocker_auth без TTL → ready-карта t_f28982d3 (rr-team, «RR cabinet → Linear-grade») вечная парковка (ready 56.8ч на 30.09, сегодня всё ещё ready, bk=None, latest fail «pid 18760 exited rate-limited»).
- Фикс staged fc2fa0c53f (fix/blocker-auth-ttl-f1f2), НО его QA-ретест t_72d9f80e сам умер 2× («pid 23320 not alive») → rollout стоит. Второй слой причины — zai/GLM 429 (см. B1).

### A2. Деградация воркер-рантайма — тренд ухудшается ежедневно
- Zombie reaps: 47 (29.09) → 130 (30.09) → 201 (01.10, день не кончен). Crashed: 2 → 6 → 17. Timed_out: 1 → 1 → 8. Пик: 00:19 01.10 spawned=5 crashed=5 (fleet-ops, одновременно).
- Причины (подтверждённые классы):
  1. Runtime-лимиты впритирку: карты убиты при превышении на 16–45с — t_5a542ba5 (5416>5400), t_1a68eede (2445>2400), t_cd4f2ee6 (612>600), t_cd64142f (1836>1800, running) → requeue → повторные прогоны сгорают впустую.
  2. «pid not alive» — воркеры умирают до reclaim: t_72d9f80e ×2, t_c7b8189d ×2, t_9fa5cac5, triage-лупы D8 (t_67e1a175 ×4 CRITICAL). Контекст 01.10: source-swap 12e4d3e2 + layer re-apply 12:26 (43 dirty) + утренняя нехватка диска (C2) — вероятные триггеры роста крешей; точная атрибуция НЕ подтверждена (нужна отдельная диагностика).
  3. Quota wall (B1) — requeue-шторм rr-team/seo-site.

### A3. Тихий дедлок поддеревьев (D2)
- recompute_ready (kanban_db.py:2188) продвигает todo→ready только при done/archived ВСЕХ родителей; blocked-корень морозит потомков без алерта.
- Масштаб 30.09: fleet-ops 50 todo, rr-team 26, seo-site 5, video 2, portfolio 2, возраст 10–17 дней. Сегодня: fleet-ops 61 todo + 21 triage, rr-team 24 todo + 11 triage.
- Пример: RR PR242 корень t_8a4d4f03 (ждёт слово владельца 106ч на 30.09) держит ~15 карт.

## B. Модели и квоты

### B1. Z.AI/GLM quota wall — узкое место QA-потока
- QA-карты выходят rate-limited и requeue: rr-team t_9ca672e0, t_93520136, t_cb532497, t_5907d2f4, t_f28982d3; seo-site t_fc450735; fleet-ops t_72d9f80e. Диспетчер: rate_limit_cooldown=1–3 весь день.
- Причина: QA primary = glm-5.3/zai, квота исчерпывается; дрейф на Sol для positive-stamp ЗАПРЕЩЁН корректно (независимость вердикта) → пропускная способность QA падает → merge-цепочки (PR242, PR198, PR255) стоят без вердиктов.

### B2. QA-независимость: compression-отравление (I1, 30.09)
- qa-сессия 20260930_060228: serving gpt-6.1-sol + compression qwen3.8-max = модель автора фикса (tech=qwen) → author_model_overlap=true → вердикт t_7e298d3e REVISED: FAIL.
- Причина: aux-канон 20.09 зафиксировал compression=qwen3.8-max флоту, но qa-delegation carve-out (kimi-k3, gate independence 03.09) на compression-слот распространён не был.
- Лечение: перепин qa compression→custom/kimi-k3/max (backup config-backups/qa-compressor-20260930T050119Z); действенность = usage-readback следующего естественного qa-run (инструмент lineage_readback.py введён, LINEAGE_READBACK.md).

### B3. Attestation-зазоры (D9)
- t_34b4af08: run=GPT-6 Sol при пине GLM-5.3 без подтверждённого отказа primary → печать удержана. t_f3d3b319: attestation found=false. Resume-guard карта t_90fbcdec сама blocked (policy_control_plane_mutation ci=29).

### B4. Sol 6.1 миграция — в целом чистая, два хвоста
- «Model context warmed: gpt-6.1-sol -> 272000 tokens (detected)» (03:22, 05:02, 12:27 01.10); 400/invalid-model в agent.log = 0. Rollback-бэкап sol61-20260929T191706Z на месте.
- Хвост 1: финальный usage-readback первого естественного run по картам не завершён (требование канона 29.09).
- Хвост 2: WARNING «resolve_provider_client: openai-codex requested but no Codex OAuth token found» ×8 (03:22 01.10, окно recovery) — наблюдать; если повторится в штатных run — диагностика auth-пути aux-клиента.

## C. Платформа / обновление Hermes (ночь 30.09 → 01.10)

### C1. Официальное обновление упало (hermes-update-lock-20260930-224002.log, exit 1 ×2 в 22:39/22:47)
- Причина 1 (CONFIRMED): после commit публикации удаление retired-дерева .previous-git-2.53.0 уперлось в загруженный usr/bin/bash.exe (WinError 5) → InstallError; retry умер идентично в _settle_previous_entry.
- Причина 2 (CONFIRMED): rollback завершился, но удаление .displaced-*/DLLs/libcrypto-3-x64.dll подняло OSError ВНУТРИ except-блока → подменил оригинальную ошибку («source preparation failed»).
- Причина 3: pm doctor exit 1 «python: realized bytes do not match recorded digest».
- Статус recovery (OFFICIAL-RECOVERY-BASELINE.md): source обновлён до clean 12e4d3e2, receipt «partial»; Desktop rebuild НЕ завершён (vendor windows.ps1 exit 4 — приложение не вышло по Quit); host gateway восстановлен (PID 11600); Jev cron暂停 02:40. Кандидат-фикс pm/install.py t_91dbfaf5 (head 6f82d6d9, 12 тестов GREEN, RED-on-base доказан), независимая QA t_0ab59219 — Block 1 (identity) DONE; merge/активация = решение владельца.
- N1 (HIGH, латентный): Desktop-кнопка Update всегда handoff --branch main (updates.json {branch:main}; checkout.ts:139 игнорирует живую ветку) → нажатие в окне park(03:55)–apply(05:00) смержит origin/main в layer-ветку вне всех контролей. Precondition-риск миграции Option A.

### C2. Диск и state.db
- company state.db = 5.41 ГБ (16:35 01.10), рос +80 МБ за сутки; ночью 01.10 на C: было ~2 ГБ → «database or disk is full» (официальный SQLite backup preflight провалился). Сейчас 34 ГБ свободно (89% used), но рост DB не управляется retention — повтор возможен.

### C3. Layer-дрейф (F4)
- Ветка company/autocompany-rebased-p0-v5-local отстаёт на 1745 официальных коммитов; nightly re-apply 43 файлов 3way по движущейся цели; конфликт уже случался (22.09 cli.py «Applied with conflicts»). Лечение: плановый rebase или Option A (merge upstream в layer-ветку) — но только после закрытия N1.

### C4. Nightly false-negatives (F1/F2)
- 28/29/30.09 rc=1 три ночи подряд: PS 5.1 $ErrorActionPreference=Stop превращает benign stderr (Config ref '${env:...KEN}') в NativeCommandError; gateway при этом восстанавливался (gateway_state.json running + telegram connected). Следствие: HermesNightlyUpdate Last Result=1, доверие к nightly-сигналу подорвано.

### C5. Мелочь платформы
- F5: 9 orphaned update-autostash (29.08–12.09) с реальными изменениями — не восстановлены, не дропнуты.
- F6: update-тесты не запускаются из venv (home_io_guard abort на stdlib под Hermes home) — base-attribution регрессий заблокирована.
- F3:disabled HermesFleetPatchApply всё ещё зарегистрирован — риск случайного re-enable (двойной apply + двойной restart gateway).

## D. Governance / policy / канбан (реестр D1–D12 от 30.09, статус на 01.10)

### D-a. Policy-стены с жиросжигающими лупами (D4)
- Воркеры повторяли denied-действие десятки раз до финального блока: evidence_gate_missing ci=119 (t_ee208805), gate_forgery ci=106 (t_2899e1ed), ci=72, ci=70, ci=46, worker_code_execution ci=40, secret_read ci=36, irreversible ci=31. Нет раннего deny-breaker (стоп после 2–3 одинаковых deny + авто-rescope).
- Ложноположительные срабатывания классификатора на ТЕКСТОВЫХ токенах: 01.10 в run t_91dbfaf5 два deny evidence_gate_missing на чистые команды из-за слова «publication» (через дефис) в имени файла артефакта — тот же корень #1 от 25.09 (матч текстовых токенов), фикс v1.2.31/32 не покрыл эту форму.

### D-b. GO-якоря не привязаны (D5; корень #2 от 25.09 жив)
- 4 карты 220+ч на evidence_gate_missing (t_ee208805 222ч, t_6f920d4f 223ч, t_fabf97d6 258ч, t_ca56be86 223ч) + 2 review_probe_nonce-обёртки (t_4a5b52f1, t_fd605212). Якоря decision:company=go head=<sha> нет НА ТОЙ ЖЕ карте; часть head устарела → re-anchor sweep.

### D-c. Запросы решений не доходят до владельца (D3)
- needs_input-карты лежали 106–420ч без доставки: t_8a4d4f03 (106ч), t_4fb46ca3 (420ч — бюджет исчерпан), t_f9b89160 (129ч), t_be62f94d (24ч), t_0d1c79f5 (130ч). OWNER-INBOX «Слово милорда» не агрегирует kanban-блоки. Фикс-план: ежедневный sweep blocked(needs_input) → owner_inbox.

### D-d. Дефекты авторства карт (D6)
- completion_contract с литеральным плейсхолдером «OWNER/REPO»: t_27fb939d — работа готова (PR#51 head d033221c, verify success, 830 passed ×2), kanban_complete отклоняется 30ч+; card_readiness.py плейсхолдеры не ловит.
- missing task_type: t_9c461308 (17ч), t_523c4c93 (301ч) — исправлены company 30.09; вывод: валидатор нужен и для company-карт, и для contract-полей.

### D-e. Просроченные time-gate без ревизии (D7)
- t_d4f0152b «168h SHADOW soak»: blocked 382ч, soak истёк ~214ч назад — никто не пересмотрел. Jev t_c0635a88 176ч initial_status; portfolio wake-условия t_c271e06b/t_71002457 257ч. Нет check_at-вотчера.

### D-f. Triage crash-лупы (D8)
- t_67e1a175 (seo-site, 4× CRITICAL «pid not alive»), t_62fd4ed9, t_6ba71b0a (rr-team 2×), t_a1565747 (fleet-ops 2×) — висят в triage без авто-ремонта/эскалации.

### D-g. PR-acceptance гейт ядра падает на валидном PR (D10, Hermes bug)
- kanban_pr_acceptance.py:64 GET /repos/maximal… детерминированно падает → t_e22b2313 (hotfix готов: PR8 head 4f3e9401, CI SUCCESS) не закрывается 57ч+.

### D-h. Алерты только в лог (D11)
- 81 stuck-tick 30.09 — ноль уведомлений company/owner. dispatcher-stuck должен идти во internal-журнал/owner-inbox.

### D-i. Transient/capability без маршрута (D12)
- TikTok UK-egress: socks5 127.0.0.1:10808 занят Incy VPN (требует auth, Donut auth не хранит) → t_0d1c79f5 130ч, публикации TikTok×3 стоят. VK SSL cooldown (t_afe35c1f, штатно). t_1d575a91: runtime запрещает skill-edit → COMPANY_RESCOPE не завершить. QA-прогоны упираются в review_probe_nonce — нет разрешённого read-only маршрута аттестации.

## E. Окружение и интеграции

### E1. MCP-нестабильность
- timeweb: 762 «Failed to connect» за 3 дня; причина — ${env:...KEN} токен не задан в profile .env/secret source (474 config-warning «keeping the literal placeholder»). Reconcile-луп каждые ~10 мин: removed=[] added=['donut','timeweb'] — сервер добавляется и снова падает.
- donut/magic: CancelledError при коннекте.

### E2. Инцидент 29.09: env-отравление гейтвея (закрыт, остаток не закрыт)
- Воркер t_6e0b9c13 перезапустил гейтвей из своего контекста → PID 23836 унаследовал HERMES_KANBAN_DB/BOARD/WORKSPACE-пины → 12:46–21:21 (~8.5ч) диспатчилась ТОЛЬКО fleet-ops; все дочерние сессии читали/писали fleet-ops вместо своих досок.
- Фикс: VBS/CMD-лаунчеры скрабят 6 переменных (bak-20260929-envscrub) + чистый рестарт schtasks 21:21.
- НЕ закрыто: аудит загрязнения fleet-ops db за окно 12:46–21:21 (чужие записи от video/rr-team cron-лейнов) — пункт 2 «Отложено» в incident-доке до сих пор не исполнен.

### E3. Мелочи
- Telegram connect timeout 45s ×2 (30.09 04:14, 13:23, company) — transient, восстановлен.
- Plugin load failures: 268 за 3 дня (platforms a2a/teams/google_chat warnings — конфиг-хвосты).
- Gateway SystemExit 75 ежедневно ~01:00 (26/27/28/29.09) + unclean exits при рестартах — штатно ли это для nightly-окна, не атрибутировано.

## Свод причин (5 сквозных корня)
1. Нет канала эскалации из канбана: stuck/blocked/time-gate/owner-решения тонут в логах (A1-видимость, D2, D3, D7, D11). Один вотчер «поддерево заморожено >N дней» + sweep needs_input→owner-inbox сняли бы половину списка.
2. QA-поток = узкое место: zai-квота + правила независимости (верно) + рантайм-смерти самих QA-карт (A2) → вердикты не ставятся → merge-цепочки стоят (B1, B3, D-g).
3. Хрупкость Windows-платформы: файловые локи загруженных DLL/exe, disk-full, 5.4GB state.db без retention, PS 5.1 stderr-семантика (C1, C2, C4).
4. Policy-механика матчит текстовые токены и stale-штампы: ложные deny на именах файлов, blocker_auth без TTL, absence deny-breaker → жиросжигающие лупы и вечные парковки (A1, D-a, D-b).
5. Runtime-лимиты и авторство карт без запаса/валидации: kill при +16–45с к лимиту, плейсхолдеры в контрактах, missing task_type на 301ч (A2.1, D-d).

## Ждёт слова владельца (на 01.10 16:45)
1. RR PR242 pass-8 (t_8a4d4f03, ~130ч): (a) владелец токенизует pass-8 сам ИЛИ (b) авторизовать второй value-preserving коммит (999px→--radius-pill; 6/7px→canonical-токены) с переанкерингом acceptance на head 1d32431d. Держит ~15 карт.
2. PM locked-retired fix (t_91dbfaf5, head 6f82d6d9): QA t_0ab59219 идёт; merge/активация — решение владельца после QA PASS.
3. Desktop app: для полного rebuild нужен supported Quit живого Desktop-процесса (vendor-скрипт exit 4, приложение не выходит) — физическое действие владельца.
4. Free-GPT пул (t_f9b89160, 129ч+): вариант B одобрен 25.09, ждём сигнал о добавлении free-акков.
5. t_4fb46ca3 (420ч+): hard-бюджет исчерпан — продлить или закрыть.
6. t_be62f94d: policy-блок irreversible_data_loss — санкционировать с backup-гейтом или перескоупить.
7. TikTok egress (t_0d1c79f5, 130ч+): дать Incy auth/освободить порт ИЛИ поручить компании альтернативный UK-выход.

## Автономный план лечения company (без слова владельца)
1. Дожать QA-ретест t_72d9f80e (смена воркер-профиля/модели ретеста в рамках канона независимости) → rollout blocker_auth TTL fc2fa0c53f → t_f28982d3 оживает, stuck-лупы уходят.
2. Owner-decision sweep → OWNER-INBOX (D3) + frozen-subtree вотчер (D2) + dispatcher-stuck алерт во internal (D11).
3. Re-anchor sweep 4+2 evidence_gate_missing карт (D5); deny-breaker тех-карта (D4); tech-карта kanban_pr_acceptance.py:64 (D10).
4. Time-gate sweep t_d4f0152b/t_c0635a88/portfolio (D7); triage crash-лупы ×4 (D8).
5. Аудит загрязнения fleet-ops db за 29.09 12:46–21:21 (остаток E2).
6. Диск/DB: retention-ревизия state.db (5.4GB) + вотчер свободного места <10GB.
7. MCP timeweb: завести токен в разрешённый secret-путь профиля или снять сервер с reconcile-лупа (E1).
8. Nightly false-negative F1: тех-карта на nightly_update_gateway.ps1 ($ErrorActionPreference/health-check по gateway_state.json).
9. Usage-readback Sol 6.1 первого естественного run (B4); наблюдение за openai-codex OAuth warning.

Финансовый scope: период 28.09–01.10, подтверждённая выручка/refunds — null (вне scope задачи); новые платные обязательства — 0; потери от сгоревших rerun-прогонов (A2/D4) — оценка стоимости токенов не измерялась (null, причина: нет per-card usage-агрегации в этом sweep).
