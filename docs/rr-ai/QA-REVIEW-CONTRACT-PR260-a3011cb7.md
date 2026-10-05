# QA REVIEW CONTRACT — PR260 exact head a3011cb7 (stage-1 acceptance review)

Статус: выпущен company-решением t_0a65e710 (02.10.2026). Потребитель: QA review-карта stage-1 (assignee qa). Repo: maximalang/recruiter-radar.
Цель: независимый exact-head acceptance review PR260 (D2 market-profile presets) и посадка gate-маркеров на merge consumer-карту (id в body QA-карты). Это НЕ merge-действие и НЕ аудит всего релиза — только stage-1 gate для PR260.

## Якоря
- PR260 OPEN, head a3011cb7ff4ce7e833ebed760446cc69e4809694, base main a043fe8c20246b44becf2c80fb34695d0961ff36 (company live readback 02.10 02:0x MSK).
- Коммиты: 9b028895 (test: freeze correlation clock in evidence-radar contract test), 711bec09 (feat: market-profile presets in pilot onboarding), a3011cb7 (fix: canonical visual primitives in preset picker styles).
- Автор-lane: t_3ef42b89 (tech, qwen3.8-max lineage). Reviewer обязан быть qa-профилем; независимо аттестовать СВОЮ фактическую serving-модель до вердикта (usage readback): дрейф на авторскую lineage (например zai 429 → sol-reroute) ДЕЛАЕТ ВЕРДИКТ НЕДЕЙСТВИТЕЛЬНЫМ — fail loud: завершить карту без маркеров, с явной записью о дрейфе. В handoff metadata обязательно worker_session_id для company-аттестации lineage.

## Scope review (diff a043fe8c..a3011cb7, 13 файлов по handoff D2)
Новые: apps/web/lib/marketProfilePresets.ts (registry+resolver, client-safe), app/onboarding/pilot/[orderId]/market-profile-preset-picker.tsx + .module.css, 4 тест-сьютa (registry/picker, action, scan-wiring, picker component). Изменённые: onboarding page.tsx + actions.ts, lib/payments.ts, paymentsTypes.ts, paymentsNormalize.ts (checkout_orders.payload JSONB optional key + normalize), src/__tests__/lib/intelligence/evidence-radar.test.ts (time-bomb fix).
Проверить по существу:
1. Scope-дисциплина: нет изменений лендинга, DB-схемы/миграций, query-planner (plan hashes не меняются), scoring/ranking/gates/suppression; preset id живёт только в checkout_orders.payload (optional key) + specialization-лейбл round-trip.
2. Registry/resolver: валидация id по registry; preset-fallback ТОЛЬКО для пустых полей; user edits всегда побеждают preset; remoteFriendly — чистая правда формы (без preset-fallback).
3. Scan-wiring: существующий profile→query-planner-v2 путь (HH_SEARCH_TEXT/SUPERJOB_KEYWORD/RABOTA_ROSSII_SEARCH_TEXT); планировщик не тронут.
4. Тесты: 4 новых сьюита покрывают registry/picker/action/scan-wiring; evidence-radar fix = now-pin без изменения контрактов.
5. Секреты/PII: нет в diff; payments*-файлы — только payload-нормализация (читать через read_file с явными диапазонами строк; grep по чувствительным словам в argv запрещён политикой — не использовать).
6. Exact-head CI: gh pr checks 260 / check-runs head a3011cb7 — зелёный набор feature-lanes; 4 красных npm-audit lanes сверить с baseline: идентичный красный набор на check-runs main tip a043fe8c, diff не трогает package-lock.json. Не идентифичен → finding (не сажать gate:ci).
7. Локальная независимая перепроверка (не доверять lane-числам): изолированный worktree git -C C:/Users/max/Desktop/all/recruiter-radar worktree add C:/tmp/rr-q1-pr260 a3011cb7 (living checkout не трогать: без fetch/checkout/reset в нём); npm run check (tsc) + targeted jest: 4 новых сьюита + evidence-radar + onboarding dir; полный web jest при бюджете — фактические counts в вердикт. Worktree в конце НЕ удалять (deletion-литералы запрещены политикой; cleanup — company).

## Вердикт и маркеры
- Формы: PASS / PASS-with-findings (ненумерованные мелкие — перечислить) / BLOCK (нумерованные findings: что, где file:line, почему gate-релевантно). Lifecycle-статус карты ≠ вердикт: вердикт — словом в комментарии на СВОЕЙ карте и в handoff.
- При PASS (включая PASS-with-findings без gate-релевантных): ОДИН комментарий на merge consumer-карте (id в body этой QA-карты), ровно три строки, без иного текста:
  gate:review=pass
  gate:ci=pass
  head=a3011cb7ff4ce7e833ebed760446cc69e4809694 task_type: ops
  Затем ОТДЕЛЬНЫЙ комментарий там же — evidence prose (проверки, counts, CI-сверка, worktree path). На СВОЕЙ карте маркеры НЕ писать (self-approval guard: review/qa-маркеры от собственного assignee мертвы/denied) — на своей карте только полный вердикт словом + evidence.
- При BLOCK: маркеры на consumer-карту НЕ сажаются; findings комментарием на своей карте + prose-заметка (без маркеров) на consumer-карте; complete с BLOCK-вердиктом в handoff. Merge train сам gate-ится на наличие маркеров.
- PR URL в комментариях не постить (active-PR respawn guard): использовать «PR260 @a3011cb7» + repo.

## Запреты
Изменения кода где-либо; commit/push/merge/force-push; создание/закрытие PR; само-маркеры на своей карте; kanban-DB reads; live-prod HTTP-пробы сайта (gh api/CI readback — можно); чтение секретов/env-шаблонов; удаление worktree; spend (0 RUB); execute_code отсутствует — скрипты через write_file + terminal; polling-циклы запрещены (identical_call_loop) — background+notify для длинного CI.
