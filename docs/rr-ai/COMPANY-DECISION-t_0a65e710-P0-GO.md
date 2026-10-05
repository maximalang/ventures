# COMPANY DECISION — t_0a65e710: GO на P0 (только bounded non-LLM evidence test), corrected contracts issued

Дата: 02.10.2026 ~02:30 MSK. Автор: company (task-scoped run карты t_0a65e710, board rr-team).
Роль решения: единственная business disposition фазы re-spec после независимого QA re-review (SPEC 2.0 §10). Решение операционное в пределах фазы; LLM/build/merge GO — НЕ выдаются этой записью (merge train — отдельная автономная рутина по gate-цепочкам, см. §4).

## 0. Якоря и входы (verified)
- Canonical SPEC: C:/Users/max/Desktop/all/ventures/docs/rr-ai/SPEC-ai-summary-assist.md, version 2.0, sha256=65f28c45b4ce43aa5004613386ed2515aaf8db9a10a6267963df3d411e408067, 292 строки / 74965 байт. Company readback 02.10 01:53 (sha256sum) — совпал с авторским финалом и QA-PASS; SPEC этим решением НЕ изменён (hash-якорь сохранён).
- Автор: t_b898ec69 (product, gpt-6.1-sol) — handoff-only коррекция §12, TOCTOU-контроль.
- QA re-review: t_a5071b8b PASS run 915 (qa, glm-5.3-flash, provider zai) ≠ авторская модель — независимость соблюдена; attachment QA-REVIEW-t_a5071b8b-SPEC-2.0.md. Вердикт doc-only: НЕ GO, НЕ carry-over PASS 1.1. Findings F-1..F-4 (info) — disposition ниже.
- Live gh readback company 02.10 02:0x: main a043fe8c20246b44becf2c80fb34695d0961ff36; PR260 OPEN @a3011cb7ff4ce7e833ebed760446cc69e4809694; PR262 OPEN @2b8fd4e61f113b5ca813971e012fc3c83f52aa84; PR263 OPEN @0e3b0b17ebdac067b9b5ab37cdab009c810acd8c; PR242 OPEN @49d8daae40b405f9a46a2de6ad574e8fa2a6406f; PR261 CLOSED mergedAt=null @6c6f615da8685148fad96903814d6c3dc633633f.

## 1. РЕШЕНИЕ
decision:company=go — ТОЛЬКО на один bounded non-LLM evidence test по SPEC 2.0 §7.2 L181-205 (P0: moderated paired workflow test; 5 добровольных agency-рекрутёров × 2 arms × 2 matched profile-level кейса = 20 study plans; детерминированный/исследовательский агрегат с честной маркировкой; cash cap 0 RUB).
Не является: GO на строительство profile-level aggregate, GO на merge/deploy этим решением (merge train — §4, по стандартной gate-архитектуре), GO на любой LLM. Product/demand/LLM-economics verdict остаётся NEEDS-EVIDENCE (SPEC §7.5). LLM capability/cost/privacy не проверены production: никаких реальных вызовов/новых провайдеров/spend до независимого finance gate + company LLM mandate + legal/privacy review.
observation_status на момент решения: not collected — P0 маршрутизирован, не выполнен; participants/observations null (авторский handoff 02.10 01:32 UTC: 0 реальных вызовов, 0 записей БД, spend 0). «Routed P0 ≠ executed P0».

## 2. Карты авторизованного теста (созданы этим решением)
- Сбор evidence: t_f6003f8c (assignee research; named owner = research; parent = t_0a65e710). Контракт: P0-COLLECTION-CONTRACT.md sha256=fe8bbde91c8aeb5d6b5f2d4b9bc96d1b35c0e70fd7bcd61af3a6d1d399774890. Timeline pre-committed: Phase A дедлайн 2026-10-05T18:00+03:00; frozen start_at planned 2026-10-06T10:00+03:00 (крайний 2026-10-09T10:00+03:00); analysis_at = frozen start_at + 7 дней (planned 2026-10-13T10:00+03:00); статус-комментарий 2026-10-04T18:00+03:00.
- QA-верификация собранных наблюдений: t_3cf9e103 (assignee qa; parent = t_f6003f8c; авто-старт после complete сбора).
- Product-интерпретация и company business verdict: маршрутизируются company ПОСЛЕ QA-верификации (отдельные карты; verdict-точка = analysis_at).
- Recruitment-эскалация: если каналов не хватает, сборщик блокируется needs_input с точным единственным вопросом владельцу (реферал 5 добровольных agency-рекрутёров); company interactive маршрутизирует вопрос владельцу одним form. Owner-touchpoint возможен на checkpoint 12:00/18:00 02.10.

## 3. Findings QA (F-1..F-4) — dispositions
- F-1 RESOLVED: P0 идёт по правилу из текста SPEC на hash (L200): доля independently useful plans у treatment НЕ НИЖЕ control ни pooled, ни внутри каждого участника — БЕЗ декремента. LABEL NOTE «3 п.п.» (t_a5071b8b, 02.10 00:57) для P0 ОТМЕНЕНО. Записано в контракт сбора §8 и QA-верификации.
- F-2 RESOLVED: каноническая нумерация артефакта = version 2.0 (SPEC L3); лейбл «v1.2» в body предшественника устарел и не используется.
- F-3 RESOLVED: протокол P0 = §7.2 L181-205; указатель «§7.3» в opening body t_0a65e710 признан stale; все новые карты ссылаются на §7.2.
- F-4 ACCEPTED: цепочка версий 17bfccb2… (первый company readback 00:53) → 65f28c45… (финал по author handoff) воспроизводима; финальный якорь = 65f28c45…

## 4. Merge/release маршрутизация (disposition p.3 + предпосылка corrected-аудита)
Основание: implementation lanes D1/D2/D4 завершены (t_96e4e1b3, t_3ef42b89, t_04c5e801 — все done), PR260/262/263 OPEN unmerged, CI зелёный по diff-touched контекстам при pre-existing baseline-классе 4 npm-audit lanes (lockfile drift с 30.09 — отдельная operations-задача, вне этой фазы); hotspot: apps/web/src/__tests__/lib/intelligence/evidence-radar.test.ts — идентичный time-bomb-fix hunk в #260/#262 (вероятно #263): второй/третий merge конфликтуют; рекомендация lanes — приземлить один и ребейзить остальные. Merge в main после gate-цепочки — автономная рутина company (owner approval не требуется).
- Merge train (consumer-карта): t_edc2b4b9 (assignee tech, marker ops; создана blocked; контракт MERGE-TRAIN-CONTRACT-PR260-262-263.md sha256=a1bb2aa4593a295b4013585b89be007dfb7449384ca164e92789531151951247). Порядок: PR260 → PR262 → PR263; на каждый stage: точный head, qa review+ci маркеры с binding, собственный rollback-маркер, company go-anchor на точный head (one-time binding; post-rebase head ⇒ новый anchor через needs_input).
- Stage-1 QA review: t_a83e7f9e (assignee qa; independent exact-head acceptance review PR260 @a3011cb7; контракт QA-REVIEW-CONTRACT-PR260-a3011cb7.md sha256=9cce21900b0abc07bc840344595973c72826153d491fb43c1313e081b1d5b1a8; marker target t_edc2b4b9). Статус на запись решения: running.
- Stage-1 anchor: posted company на t_edc2b4b9 (комментарий 1863): decision:company=go / head=a3011cb7ff4ce7e833ebed760446cc69e4809694 task_type: ops.
- Unblock t_edc2b4b9: company interactive-сессия после (1) посадки qa-маркеров и (2) аттестации lineage stage-1 QA-вердикта по usage readback (worker_session_id в handoff t_a83e7f9e). Stage 2/3 anchors — тоже interactive company (по needs_input запросам worker'а).
- PR242: anchor-расхождение 9eaa919b (frozen) vs 49d8daae (remote head) разрешается evidence-based в своей lane (аттестация t_4d2eab28, done); copy-edit запрещён; frozen landing не трогать. PR261 @6c6f615d: CLOSED unmerged, остаётся закрытым (директива владельца 01.10 22:35), паттерны reusable только в новом разрешённом дизайне (SPEC §8).

## 5. Corrected audit/release contract (disposition p.1)
- t_f8701369 (functional truth re-audit): исходный контракт VOID (комментарии 1856/1857: «все 4 PR merged» недостижимо, draftOpener исключён из ядра, «старый D3 done ≠ shipped AI»). Карта остаётся HELD/SUPERSEDED (не unblock); supersession-запись с реквизитами исправленного контракта — комментарий 1865 на той карте. Формальное архивирование — pending action company interactive-сессии (из task-scoped run cross-card lifecycle недоступен; hold записан, не потерян).
- Successor: t_e2b754a0 «RR functional truth re-audit v2» (assignee research; parent = t_edc2b4b9 — стартует после приземления merge train; контракт AUDIT-CONTRACT-V2-functional-truth.md sha256=889c5de920759e6ef4e157b4d8841728d111e5f513b9a92381620a1c20bb83fa). Binding: SPEC 2.0 (hash 65f28c45…) + ФАКТИЧЕСКИ merged main момента выполнения (live gh readback; состав merges из handoff t_edc2b4b9). Claims C1-C6: D1 registry воспроизводимый пересчёт, D2 presets в onboarding path, D4 каналы code-level, C4 AI-scope truth (нет profile-агрегата на main; draftOpener не в core; нигде не заявлено как доступная функция), C5 frozen-landing spot-checks по обоим PR242-якорям, C6 release-граница per PR.

## 6. Метрика (disposition p.2) — ADOPTED до instrumentation
accepted_evidence_backed_leads_28d operational v1.0 ПРИНЯТО: METRIC-DEFINITION-accepted_evidence_backed_leads_28d-v1.0.md sha256=e36635dd2fd2d83bce5f984bb5cdd7fc94f0839caf1e5da97258e76516f6027e. Компоненты: acceptance timestamp (первый реальный ручной transition в contacted/replied/meeting/won, серверный UTC), dedup unit (workspace_id, org_id), evidence snapshot as-of acceptance (immutable, replayable), exclusions (test/synthetic/internal/bot, mock, auto-accept, missing/expired evidence, summary view, AI call, draft copy, study-решения P0, suppressed, без tenancy; missing = null не 0), policy gate (compliance действующих на t_accept deterministic gate + contact policy) + обязательный независимый query/replay test-suite до канонической отчётности. Конфликт единиц (§7.1): НЕ обнаружен (канон PORTFOLIO.md L17-20 = имя; dashboard 7/30d = status proxy, не метрика). SPEC-файл не изменён; снятие «provisional» в §7.1 — будущая авторская docs-ревизия.

## 7. Disposition всех карт фазы (на 02.10 02:30)
- t_0a65e710 (эта): complete с данным решением.
- t_b898ec69 / t_a5071b8b / t_18026ee9 / t_bf239163: done — closed.
- t_b64d86b6: done — PASS 1.1 SUPERSEDED (не acceptance для 2.0), carry-over запрещён.
- t_3ef42b89 (D2): done; PR260 unmerged → merge train stage 1 (t_edc2b4b9/t_a83e7f9e).
- t_04c5e801 (D4): done; PR262 unmerged → merge train stage 2.
- t_96e4e1b3 (D1): done; PR263 unmerged → merge train stage 3.
- t_4d2eab28 (PR242 аттестация): done; PR242 lane продолжается evidence-based, copy-edit запрещён.
- t_f8701369: HELD/SUPERSEDED (комментарии 1856/1857/1865); successor t_e2b754a0; архивирование — interactive company.
- Новые: t_f6003f8c (P0 сбор, todo gated), t_3cf9e103 (P0 QA-верификация, todo gated), t_edc2b4b9 (merge train, blocked до маркеров+unblock), t_a83e7f9e (stage-1 QA review, running), t_e2b754a0 (audit v2, todo gated).

## 8. Финансовый scope решения (period 01-02.10.2026, source: handoff'ы карт фазы + live readback)
- confirmed_revenue: null — не читалось в scope этой карты (БД/чеки вне скоупа; SPEC §2.2: БД не читалась).
- refunds: null — событий не зафиксировано в handoff'ах фазы; реестр не читался.
- incremental_paid costs: 0 RUB (факт: авторский и QA handoff'ы — spend_rub=0, 0 реальных LLM-вызовов, 0 платных API).
- new commitments: 0 RUB cash (все созданные карты: cash cap 0 RUB; paid API/provider запрещены до finance gate).
- estimated usage cost: null — внутренний труд не оценивался денежно (нет тарификации); LLM-стоимость отсутствует by design.
- budget: null (карта-предшественник budget=null; phase budget не утверждался).

## 9. Downside cap, kill criteria, rollback
- Downside cap: 0 RUB cash; bounded внутренний труд пяти карт; никаких production-изменений авторизовано (merge train — единственная write-операция, целиком за gate-цепочками); никаких live LLM.
- Kill criteria P0: (1) нет 5 согласившихся подходящих участников к дедлайну Phase A → NEEDS-EVIDENCE без продления; (2) fixtures/history/контроль не проходят независимую QA-валидацию (вторая неудача) → NEEDS-EVIDENCE; (3) полные данные не проходят pre-committed правила → NO-GO для AI-строительства данного формата (проблема source/fit → вернуть D1/D2); (4) safety violation (private-данные, core-мутация, неразрешённый outreach/spend, материальный unsupported fact) → немедленный STOP + incident review; (5) две попытки без новых evidence/участников → scope reduction / смена authorised test / STOP фазы.
- Rollback: P0 не имеет production-поверхности (research-артефакты изолированы, product feedback неприкосновенен, датасет в C:/tmp/rr-p0-evidence + closed-process consent-хранилище); merge train — per-merge revert -m 1 план (gate:rollback на каждый stage); audit — read-only.

## 10. Next actions / checkpoints / pending company actions
- next_action: P0 Phase A (recruitment+fixtures) на t_f6003f8c; stage-1 QA review на t_a83e7f9e (running).
- check_at фазы: 2026-10-02T18:00:00+03:00 (SPEC §10 decision checkpoint; промежуточный 12:00 MSK закрыт досрочно: QA re-review PASS 01:34 + эта disposition ~02:30).
- pending company interactive actions: (1) unblock t_edc2b4b9 после qa-маркеров + lineage-аттестации t_a83e7f9e; (2) архивировать t_f8701369 (SUPERSEDED, successor t_e2b754a0); (3) stage 2/3 anchors по needs_input; (4) возможный owner-touchpoint: реферал 5 добровольных agency-рекрутёров для P0 (поднять на checkpoint, если сборщик заблокируется); (5) рекомендовано вне фазы: отдельная operations-lane на lockfile audit-drift (4 красных npm-audit CI lanes на main с 30.09 — мешает gate:ci-чистоте всех будущих PR).
