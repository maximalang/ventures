# RR: Dependency Remediation Plan — npm audit prod-находки

Статус: ПЛАН (scoping-карта t_b4254bf9, без правок кода). Дата анализа: 2026-09-30.
Anchor: `main @ a043fe8c20246b44becf2c80fb34695d0961ff36` (= origin/main на момент анализа, проверено).
Метод: read-only клон в scratch-workspace карты, `npm audit --json` (omit=dev, level=moderate), `npm outdated --json`, `npm view` по registry, GitHub advisories API (`gh api /advisories`). Ни один package.json/lockfile/код в репозитории не изменён.
Окружение анализа: node v26.7.0 / npm 11.19.0 локально; CI использует node 22 — при верификации батчей запускать npm на node 22 (см. §5).

## 1. Ключевой факт: расхождение с CI-раном (9 → 8 находок)

Контекст карты: CI run 36668058958 на этом же SHA сообщил 9 находок (1 critical, 6 high, 2 moderate), включая `minimatch`.
Локальный аудит того же SHA сегодня даёт **8 находок (1 critical, 5 high, 2 moderate), `minimatch` НЕ флагается** (`npm audit --omit=dev --audit-level=moderate` exit=1).

Причина: advisory-дрейф. Все три актуальных minimatch-advisory имеют 3.x-диапазоны, закрытые уже в ≤3.1.4:
- GHSA-7r86-cg39-jmmj (high): `< 3.1.3` → patched 3.1.3
- GHSA-23c5-xmqv-rm74 (high): `< 3.1.4` → patched 3.1.4
- GHSA-3ppc-4f35-3m26 (high): `< 3.1.3` → patched 3.1.3

В lockfile стоит minimatch **3.1.5** (последняя 3.x, `npm view "minimatch@>=3.1.5 <4"` = только 3.1.5) — формально patched по всем трём. Вывод: 9-я находка CI — состояние advisory-базы на момент рана (диапазоны позже скорректированы), а не ошибка lockfile. Тот же дрейф ранее менял severity js-yaml (critical→high). План учитывает оба состояния: minimatch вынесен в условный batch 3.

## 2. Инвентарь находок (a043fe8c, 2026-09-30)

| # | Пакет | Severity | Locked | Мин. fix | Рек. | Тип bump | Правка манифеста | Поверхности |
|---|-------|----------|--------|----------|------|----------|------------------|-------------|
| 1 | next | **critical** | 16.2.11 | 16.3.3 | 16.3.7 | minor (внутри ^16.2.11) | нет (lock-only) | apps/web runtime, next/image, CI build |
| 2 | nodemailer | high | 9.0.1 | 10.0.6 | 10.0.13 | **major 9→10** | apps/web/package.json | apps/web/lib/email/transport.ts (доставка дайджестов) |
| 3 | js-yaml | high | 3.15.1 | 3.15.2 | 3.15.2 | patch (внутри ^3.14.2) | нет (lock-only) | dev/coverage-граф (@istanbuljs/load-nyc-config), runtime-импортов нет |
| 4 | brace-expansion | high | 5.0.9 | 5.0.12 | 5.0.12 | patch, НО exact-pin | root package.json: dependencies + overrides (2 строки) | транзитив minimatch (glob/test-exclude — dev-граф), runtime-импортов нет |
| 5 | undici | high | 6.28.0 | 6.28.1 | 6.28.1 | patch (внутри ^6.27.0) | нет (lock-only) | packages/db/scripts/adapters/hh.mjs (ingest-фetch), apps/web (объявлен) |
| 6 | sharp | high | 0.35.3 | 0.35.4 | 0.35.5 | patch (внутри ^0.35.3) | нет (lock-only, override ^0.35.3 допускает) | apps/web/scripts/generate-app-icons.mjs (build-time), next/image optimization |
| 7 | socks | moderate | 2.8.9 | — (флаг только через ip-address) | 2.8.10 (опц.) | patch (внутри ^2.8.9) | нет | packages/db hh.mjs (SOCKS-прокси), teleproto→socks (Telegram-доставка) |
| 8 | ip-address | moderate | 10.3.1 | 10.7.1 | 10.7.2 | minor (10.x), НО exact-override | root package.json: overrides (1 строка) | socks-граф: hh.mjs proxy, teleproto |
| 9 | minimatch | (CI: high) | 3.1.5 | не флагается сегодня | 3.1.5 (latest 3.x) | — | — | glob@7, test-exclude (dev-граф); runtime-импортов нет |

Важно про паттерн репозитория: root package.json содержит ~300 объявленных транзитивных пинов + секцию `overrides` (`brace-expansion: "5.0.9"`, `ip-address: "10.3.1"`, `postcss: ^8.5.18`, `sharp: ^0.35.3`). Exact-пины в overrides **блокируют** лечение lockfile-only: `npm update ip-address` не сдвинет версию против override. Поэтому пункты 4 и 8 требуют точечных правок манифеста.

### Advisory-детализация

1. **next** (critical): GHSA-p293-qw3h-jr36 — unauthenticated RCE на windows-hosted серверах (`>=16.0.0 <16.3.3`); GHSA-2xp9-vwfh-vxw4 — unauthenticated RCE в Image Optimization API при AVIF (`>=16.0.0 <16.3.3`). Прод-хостинг Linux (railway.toml / timeweb) → windows-вектор контекстно снижен, AVIF-вектор актуален, если включена оптимизация изображений. Оба критерия закрываются 16.3.3+; latest 16.3.7 удовлетворяет ^16.2.11 (root и apps/web) и peer better-auth (`^14||^15||^16`).
2. **nodemailer** (high): 7 advisory. Ключевые: GHSA-v53p-9fqp-m79j (high, `<=10.0.5`, quadratic backtracking в addressparser — закрывает ВСЕ 9.x и 10.0.0–10.0.5, поэтому промежуточный bump 9.0.1→9.1.1 бессмыслен); GHSA-2x7j-588g-ccc2 (high, `<9.1.0`, O(n²) addressparser DoS); GHSA-6vj9-mwq6-2f5v (moderate, `>=5.0.0 <10.0.2`, process-global DNS cache — cross-tenant утечка SMTP-credentials); GHSA-8vvx-rff5-p5rq (moderate, `<10.0.2`); GHSA-8m3c-c648-2xjj, GHSA-wmmp-3585-3rmp, GHSA-cc9r-2j5m-2m83 (moderate, `<9.1.0`/`<=9.1.0`). Минимальная полностью чистая версия — **10.0.6**; рекомендованная 10.0.13 (latest).
3. **js-yaml** (high): GHSA-2883-xcg3-v3hh — maxTotalMergeKeys не ограничивает CPU при пустых merge-источниках (`>=3.0.0 <3.15.2`). Fix 3.15.2 — patch внутри ^3.14.2 (подтверждено `npm outdated`: wanted=3.15.2). Мажорная миграция на 5.x для audit-green НЕ нужна.
4. **brace-expansion** (high-агрегат): GHSA-q2hr-2g5m-vwhr (moderate, `>=4.0.0 <5.0.12`, quadratic CPU DoS), GHSA-qhr7-859c-m2p7 (high, `>=4.0.0 <5.0.11`, recursion stack exhaustion), GHSA-6j4f-fj2g-mc7p (high, `>=4.0.0 <5.0.10`). Диапазоны начинаются с 4.0.0 — 1.x/2.x не затронуты. Fix 5.0.12; из-за exact-пина (dependency + override) нужна правка 2 строк root package.json. Потребитель — minimatch (ожидает ^1.1.7, но override уже сейчас форсирует 5.0.9 и dev-граф работает) → 5.0.12 того же мажора, нового риска нет.
5. **undici** (high): GHSA-rfgv-xxqx-mfg5 (high, `>=6.7.0 <6.28.1`, DoS через unrequested WebSocket subprotocol), GHSA-3wwx-pv8p-q78v (moderate, `>=6.25.0 <6.28.1`, permessage-deflate), GHSA-r53p-7pc4-xj5r (low, `<6.28.1`, response splitting через retry interceptor). Fix 6.28.1 существует (`npm view undici@6.28.1`), входит в ^6.27.0. Мажор 8.x не требуется.
6. **sharp** (high): GHSA-rgj7-g3m4-5g8c — уязвимости бандла libheif (GHSA-g89c-p67h-r497, GHSA-2jg2-4ch7-h545), `<0.35.4`. Fix 0.35.4/0.35.5; ^0.35.3 (dependency и override) допускает 0.35.5 → lock-only. Карта-заказчик относила sharp к batch 2 как «major», фактически это patch того же минора — риск низкий.
7. **socks** (moderate): собственная оценка npm — флаг через зависимость ip-address (`via: ["ip-address"]`); socks 2.8.9/2.8.10 обе объявляют `ip-address: ^10.1.1`. Лечится bump-ом ip-address; опционально socks→2.8.10 (patch внутри ^2.8.9 в packages/db; teleproto требует ^2.6.2 — совместимо).
8. **ip-address** (moderate): GHSA-rpw4-54j3-4h4q (isLinkLocal fe80::/64 вместо fe80::/10 — SSRF/bypass на on-link хосты), GHSA-2vr4-cq9g-pvrc (NAT64 64:ff9b:1::/48 не распознаётся), GHSA-j6r3-76f7-8jcv (isInSubnet сравнивает разные family — allowlist bypass), GHSA-h3mg-xc3c-68pw (unbounded parse diagnostic — stall/crash). Все `<=10.7.0` → fix 10.7.1+, рекомендовано 10.7.2. Точка использования — SOCKS-путь ingest-адаптера hh.mjs и teleproto: SSRF-класс релевантен для прокси-траста.
9. **minimatch**: см. §1 — сегодня не флагается; 3.1.5 = latest 3.x и patched по всем актуальным GHSA. Runtime-импортов в first-party коде нет (grep по apps/packages/scripts/tools/.github/operator-auth на a043fe8c).

Поверхности, затронутые находками (grep-верифицировано): `apps/web/lib/email/transport.ts` + `apps/web/src/__tests__/lib/email/transport-privacy.test.ts` (nodemailer); `apps/web/scripts/generate-app-icons.mjs` (sharp); `packages/db/scripts/adapters/hh.mjs` (socks SocksClient + undici Agent/fetch); next — весь apps/web. js-yaml/minimatch/brace-expansion — только dev/coverage-граф (jest/istanbul, glob, test-exclude) и пины; прямых импортов нет.

## 3. Инвентарь CI-гейтов аудита (на a043fe8c)

| Workflow | Команда | Строгость |
|----------|---------|-----------|
| .github/workflows/test.yml (×2, строки 515/533) | `npm audit --omit=dev --audit-level=high` | high |
| .github/workflows/better-auth-security.yml:65 | `npm audit --omit=dev --audit-level=moderate` | **moderate (строжайший)** |
| .github/workflows/evidence-radar-contracts.yml:47 | `npm audit --omit=dev --audit-level=high` | high |
| .github/workflows/operator-mcp-security.yml (×2) | `npm audit --omit=dev --audit-level=high` | high |

Целевое состояние: 0 prod-находок уровня moderate и выше → все четыре гейта зелёные. Промежуточные состояния: после batch 1 останутся next (critical) + nodemailer (high) → high-гейты ещё красные; полное озеленение — только после batch 2.

## 4. План батчами

### Batch 1 — низкий риск (6 из 8 находок; lockfile + 3 строки манифеста)
Состав: js-yaml→3.15.2, brace-expansion→5.0.12, undici→6.28.1, sharp→0.35.5, ip-address→10.7.2, socks→2.8.10 (опц.).
Шаги (отдельная ветка/PR, напр. `codex/dep-remediation-batch1`):
1. Root package.json: `"brace-expansion": "5.0.12"` в dependencies И в overrides; `"ip-address": "10.7.2"` в overrides. (Опционально packages/db: `"socks": "^2.8.10"`.)
2. Пересборка lockfile на node 22: `npm install --package-lock-only` (см. §5 — оценка диффа).
3. Ревью `git diff package-lock.json`: ожидать только записи перечисленных пакетов (+ их integrity/resolved). Любой посторонний дрейф (caniuse-lite, electron-to-chromium и т.п.) → откатить и применить точечно `npm update js-yaml undici sharp socks --package-lock-only` (для brace-expansion/ip-address манифест уже правлен — они подхватятся).
4. Верификация: `npm audit --omit=dev --audit-level=moderate` → ровно 2 находки (next, nodemailer), exit=1 (ожидаемо до batch 2); `npm ci`; jest apps/web (`npm test` в apps/web) — coverage-граф (js-yaml/istanbul) задействован; build apps/web (sharp/next-image); smoke hh.mjs-адаптера или юнит-тесты packages/db, покрывающие proxy/fetch-путь (undici/socks/ip-address).
Риск: низкий. Все bumps — patch/minor внутри объявленных диапазонов; единственные содержательные изменения поведения — ip-address SSRF-классификаторы (строже, для прокси-пути желательно прогнать ingest-тесты) и sharp libheif (build-time + image-opt, тот же минор).

### Batch 2 — регрессионный риск (2 находки; разбить на два PR для изоляции)
**2a. next 16.2.11→16.3.7** (закрывает оба critical). Формально minor внутри ^16.2.11 (lock-only, `npm update next --package-lock-only`), НО по задокументированному опыту флота на 16.3.x известны две регрессии app-level: auth-v2 e2e pending-action таймаут (изменение redirect fetch, vercel/next.js issue #62561) и landing-тест «focus escaped mobile dialog» (playwright). Минимум для audit-green — 16.3.3; рекомендовано 16.3.7. Исполнительной карте batch 2a нужно сразу давать мандат на правку тестовых ожиданий под новое redirect-поведение (это правки кода — вне scope данной scoping-карты).
Верификация: полный e2e-lane (auth-v2 pending-action, landing playwright), apps/web jest, production build, прогон better-auth-security.yml-сценариев; аудит → остаётся только nodemailer.
**2b. nodemailer 9.0.1→10.0.13** (закрывает high + 5 moderate). Мажор 9→10: правка apps/web/package.json (`^9.0.1` → `^10.0.13`), `npm install --package-lock-only`, вычитка breaking-changes v10 против использования в transport.ts (createTransport-опции, disableFileAccess/disableUrlAccess-поведение, addressparser). Промежуточные 9.x (9.1.1) не лечат: верхняя находка `<=10.0.5`.
Верификация: transport-privacy.test.ts, все email-тесты apps/web, staging-SMTP smoke реальной отправки дайджеста (критический путь доставки); после этого `npm audit --omit=dev --audit-level=moderate` → **exit 0**, все гейты §3 зелёные.

### Batch 3 — условный (minimatch)
Действий не требует, пока аудит не флагует 3.1.5 (сегодня не флагует, §1). Если CI вновь покраснеет по minimatch из-за дрейфа advisory-базы: (а) зафиксировать фактический GHSA/диапазон свежим `npm audit --json`; (б) бэклорта в 3.x не существует (3.1.5 — потолок), значит решение — либо точечный override на потребителя (glob@7 и test-exclude объявляют ^3.x — глобальный override на 10.x сломает их API-совместимость: в 10.x минимatch — именованный экспорт), либо acceptance-решение владельца (находка в dev-графе, runtime-импортов нет). Не смешивать с batch 1/2.

## 5. Оценка пересборки lockfile

- Lockfile v3, workspaces `apps/*` + `packages/*`; root-манифест намеренно держит ~300 транзитивных пинов (замороженный граф). **Полная пересборка (`rm lock + npm install`) не рекомендована**: перерезолвит все caret-диапазоны (browserslist/caniuse-lite/electron-to-chromium и пр.), даст многотысячестрочный дифф и неконтролируемый дрейф поверх целевых фиксов.
- Целевой подход: точечные `npm update <pkg> --package-lock-only` + 3 строки манифеста (batch 1) / 1 строка (2b). Ожидаемый дифф lockfile: ~6–10 записей пакетов на батч (version/resolved/integrity + зависимости этих поддеревьев).
- Дифф-гейт обязателен: `git diff package-lock.json` reviewed построчно — посторонние записи = сигнал к точечному повтору.
- Выполнять на **node 22** (совпадает с CI `node-version: '22'`), чтобы npm-версия исполнителя и CI совпадали; локальный анализ шёл на npm 11.19.0 — на содержимое lockfile это не влияет (audit читает lock как есть), но для identical-результатов `install --package-lock-only` лучше node 22.
- `npm audit fix` НЕ применять вслепую: для nodemailer/next он либо не сработает (major вне диапазона), либо потянет `--force`-мажоры; только явные точечные update.

## 6. Сводка рисков

| Батч | Риск | Обоснование / мitigation |
|------|------|--------------------------|
| 1 | низкий | patch/minor внутри constraint; дифф-гейт lockfile; тесты coverage-графа + ingest-smoke |
| 2a (next) | средне-высокий | известные регрессии 16.3.x (e2e pending-action #62561, landing focus); отдельный PR, полный e2e-lane, мандат на правку тест-ожиданий |
| 2b (nodemailer) | средний | мажор на критическом пути доставки дайджестов; отдельный PR, privacy-тесты + staging-SMTP smoke |
| 3 (minimatch) | условный | сегодня не флагается; решение только по факту свежего GHSA |
| Сквозной | advisory-дрейф | находки/диапазоны меняются без изменений кода (кейс minimatch, js-yaml critical→high); перед каждым батчем снимать свежий `npm audit --json` и сверять с планом |

Порядок: batch 1 → 2a → 2b отдельными PR (атомарные диффы, изоляция регрессий); слияние — по стандартной цепочке независимых гейтов проекта (ci/review/rollback; для деплоя дополнительно qa/backup). Полное озеленение четырёх audit-гейтов — после 2b.

## 7. Evidence

- Клон: scratch-workspace карты t_b4254bf9, `git clone --filter=blob:none` → checkout a043fe8c…f36; `git rev-parse origin/main` = тот же SHA.
- `npm audit --omit=dev --audit-level=moderate --json` → exit=1, metadata `{critical:1, high:5, moderate:2, total:8}`; сырой JSON: `audit-prod.json` в scratch-клоне.
- `npm outdated --json` → next wanted 16.3.7; js-yaml wanted 3.15.2; brace-expansion wanted 5.0.9→latest 5.0.12; sharp wanted 0.35.5; minimatch wanted 3.1.5 (latest 10.2.6 — мажор не нужен).
- `npm view` (registry): nodemailer 9.x-потолок 9.1.1, 10.0.6+ существуют; undici@6.28.1 существует; socks 2.8.9 и 2.8.10 обе `ip-address: ^10.1.1`; ip-address 10.7.1/10.7.2; sharp 0.35.4/0.35.5; minimatch 3.x = только 3.1.5; js-yaml 3.15.2 существует.
- `gh api /advisories?affects=minimatch` → диапазоны 3.x закрыты в 3.1.3/3.1.4 (таблица §1).
- Lock-граф: потребители minimatch = glob(^3.1.1), test-exclude(^3.0.4); js-yaml = @istanbuljs/load-nyc-config(^3.13.1); brace-expansion = minimatch(^1.1.7, форсируется override); ip-address = socks(^10.1.1); socks = teleproto(^2.6.2), packages/db(^2.8.9); sharp = root(^0.35.3) + next(^0.34.5, override ^0.35.3); nodemailer = apps/web(^9.0.1); next = root+apps/web(^16.2.11), peer better-auth.
- Overrides root package.json: brace-expansion "5.0.9", ip-address "10.3.1", postcss "^8.5.18", sharp "^0.35.3".
- CI-гейты: grep по .github/workflows (§3), node-version '22'.
