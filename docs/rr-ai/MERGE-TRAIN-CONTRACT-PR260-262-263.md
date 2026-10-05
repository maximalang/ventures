# MERGE TRAIN CONTRACT — PR260 → PR262 → PR263 (sequential, exact-head gate chain)

Статус: выпущен company-решением t_0a65e710 (02.10.2026). Потребитель: merge-consumer карта (assignee tech, marker ops-типа первой строкой). Repo: maximalang/recruiter-radar. Main checkout (грязный, НЕ трогать working tree): C:/Users/max/Desktop/all/recruiter-radar.
Решение владельца не требуется: merge в main после gate-цепочки — автономная рутина (user profile: «merge — только по gate-цепочке»). Карта создана blocked; разблокирует company interactive-сессия после посадки stage-1 маркеров и аттестации QA-lineage.

## Якоря (live readback company 02.10 02:0x MSK, gh api/pr view)
- main tip: a043fe8c20246b44becf2c80fb34695d0961ff36
- PR260 OPEN head a3011cb7ff4ce7e833ebed760446cc69e4809694 (D2 presets; lane t_3ef42b89 done)
- PR262 OPEN head 2b8fd4e61f113b5ca813971e012fc3c83f52aa84 (D4 channels; lane t_04c5e801 done)
- PR263 OPEN head 0e3b0b17ebdac067b9b5ab37cdab009c810acd8c (D1 sources 43; lane t_96e4e1b3 done)
- PR261 CLOSED unmerged @6c6f615d — НЕ трогать, не возрождать (директива владельца 01.10 22:35)
- PR242 OPEN @49d8daae — отдельная evidence lane (аттестация t_4d2eab28); этим поездом НЕ merges, copy-edit запрещён.

## Хотспот (обязателен к учёту)
apps/web/src/__tests__/lib/intelligence/evidence-radar.test.ts — идентичный time-bomb fix (now-pin correlateSignals) несётся в #260 (9b028895) и #262 (и, вероятно, #263). Второй/третий merge конфликтуют на том же hunk. Порядок поезда фиксирован: 260 → 262 → 263; после каждого landing следующий PR ребейзится на новый main (см. Stage protocol).

## Preconditions каждого stage (проверить ДО любого gated-действия; absence = STOP, не obход)
На ЭТОЙ карте должны существовать, все с binding-строкой head=<точный head stage> + тип ops (формат binding-строки: head=<full sha>, затем тип карты через двоеточие — как в stage-1 anchor-комментарии company):
1. qa-комментарий с маркерами gate:review=pass и gate:ci=pass + binding (автор qa; записи собственного assignee игнорируются политикой — свои не писать);
2. собственный (tech) комментарий gate:rollback=pass + тот же binding (rollback plan = git revert -m 1 <merge-sha>; source-merge rollback, не покрывает install/runtime — deploy вне scope);
3. company go-anchor: отдельный комментарий, первая строка decision:company=go, вторая head=<full sha> + тип ops. Stage-1 anchor (head a3011cb7…) уже posted company. Stage 2/3 anchor — ТОЛЬКО от company на фактический (post-rebase) head; никогда не переиспользовать anchor другого head (changed head invalidates binding); не fabricate маркеры (gate_forgery).
4. gh readback: PR state OPEN, headRefOid == head stage, mergeStateStatus MERGEABLE.
CI-ожидание: background + notify, без polling-циклов; heartbeat во время ожидания; evidence писать после каждого шага, не в конце.

## Stage protocol
### Stage 1 — PR260 @a3011cb7 (маркеры от QA-карты stage-1; anchor posted)
1. Проверить preconditions 1-4. Head-дрейф (headRefOid != a3011cb7…) → STOP stage, block needs_input.
2. CI exact-head: gh pr checks 260 / check-runs на head. Ожидание: зелёные feature-lanes; 4 красных npm-audit lanes (security-audit, timeweb-oauth-security, AuthV2 security-smoke, commercial-signal-evidence-radar) = pre-existing baseline класс main-lockfile — сверить идентичность красного набора с check-runs main tip a043fe8c; diff lockfile не трогает (git diff a043fe8c..a3011cb7 --name-status). Красный набор НЕ идентичен baseline → STOP, block needs_input.
3. Merge: gh pr merge 260 --repo maximalang/recruiter-radar --merge --match-head-commit a3011cb7ff4ce7e833ebed760446cc69e4809694 (только --merge; squash/rebase запрещены). Exit-код не доказательство — readback обязателен.
4. Readback: gh pr view 260 state=MERGED + mergeCommit.oid; gh api commits/main → tip == merge sha. Check-runs на merge-commit: красный — сначала атрибуция (log failed step): pre-existing debt при инертном diff → оставить merge + remediation-заметка; вина diff → revert -m 1, инцидент-отчёт, STOP поезда.
5. Комментарий на карту: stage-1 evidence (head, mergeCommit.oid, main tip, CI-атрибуция).
### Stage 2 — PR262 (pre-rebase head 2b8fd4e6)
1. Оценить mergeability на новом main: gh pr view 262 mergeStateStatus + пробный merge-tree в ИЗОЛИРОВАННОМ scratch-клонe/worktree (никогда в живом checkout владельца). Конфликт ожидается (хотспот).
2. При конфликте: rebase ветки codex/d4-notification-channels на новый main в C:/tmp/rr-mt-262; дублирующий hunk хотспота разрешить в пользу приземлившейся main-версии; локальные проверки на post-rebase head (tsc, test:types, guard:router, затронутые jest-сьюты: notification ×5 + evidence-radar + полный web jest при бюджете); push --force-with-lease ТОЛЬКО в feature-ветку (никогда в main); pre-rebase head и post-rebase head — комментарием на карту. Force-with-lease может быть policy-gated у headless-воркеров: при deny НЕ варьировать команду — зафиксировать block needs_input с точным deny.
3. Новый head → новый CI (background+notify) → kanban_create qa-карты stage-2 (assignee qa, marker review-типа; deliverable: independent exact-head review PR262 на post-rebase head + маркеры review/ci с binding на ЭТУ карту; scope = D4 diff + rebase-resolution; independence: reviewer ≠ author lineage) → kanban_link(parent=<qa-карта>, child=<эта карта>) → kanban_block(kind=dependency).
4. После резюма: block needs_input с запросом stage-2 anchor (точный текст: требуется company go-anchor head=<новый sha> на этой карте; QA-маркеры посажены). Company interactive постит anchor и разблокирует.
5. Проверить preconditions → gate:rollback (новый binding) → merge --match-head-commit <новый head> → readback → evidence-комментарий.
### Stage 3 — PR263 (pre-rebase head 0e3b0b17, ветка codex/d1-source-registry-42)
Тот же протокол (mergeability → rebase при конфликте → CI → qa-карта stage-3 → dependency-block → needs_input anchor → rollback marker → merge → readback). D1 scope: source registry 43, docs, evidence bindings.
### Чисто mergeable без rebase
Если PR мерджится без конфликта: head не меняется, но stage ВСЁ РАВНО требует собственных qa-маркеров с binding на свой head и нового company anchor (anchor — exact one-time binding на head; stage-1 anchor покрывает только a3011cb7).

## Остановки и честность
- Gate не собран / QA BLOCK / CI-красный атрибутирован diff / head-дрейф → STOP stage; оставшиеся stages НЕ продолжать; complete с честным частичным итогом (какие stages приземлились с evidence) или block needs_input с точной причиной. Повторный идентичный deny = STOP, не retry-цикл.
- Lifecycle-статус ≠ вердикт: qa-карта может быть done с BLOCK-вердиктом — gate-маркеры на этой карте решают.
- Complete поезда: handoff metadata — на stage: PR, merged head, mergeCommit.oid, main tip readback, CI-атрибуция, pre/post-rebase heads, id qa-карт, anchor-evidence; cash 0 RUB; paid APIs 0. Дочерняя audit-карта (functional truth re-audit v2) стартует автоматически после complete.

## Запреты
Force-push в main/protected (force-with-lease — только feature-ветки при rebase-stage); squash/rebase-merge через GitHub; merge без полного набора маркеров stage; правка reviewed SHA (amend/rebase уже отревьюенного head вне rebase-stage процедуры); любые действия с PR242/PR261; copy-edit лендинга; deploy (отдельная lane); spend/платные API; чтение секретов/env-файлов; kanban-DB reads; удаление worktree (остаются — company чистит); execute_code отсутствует — скрипты через write_file + terminal.
