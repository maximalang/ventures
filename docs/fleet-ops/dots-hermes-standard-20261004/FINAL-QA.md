# FINAL-QA — независимая финальная приёмка применения (run 2321)

TYPED VERDICT (word-form): **PASS** — installation acceptance of dots-hermes-standard-20261004 на 12 живых профилях. Подтверждено: byte-exact применение approved source head, целостность captured tree, backups/rollback-материал, entrypoint/frontmatter, независимый loader-readback, отсутствие overclaim'ов. НЕ аттестуется: future model obedience, live stop/behavior, экономический эффект.

- Карта: t_63f62c17 (fleet-ops, ops), ревью-ран 2321, reviewer profile qa, сессия 20261004_042700_8fb555.
- Source head (SUBJECT.json): SHA256 `2fedef53211adc07445caee7d4d3ef3cac4df5e7544508ca35a26e040774600e` — перепроверен этим раном.
- Установленный reference: SHA256 `80933ccf80e99e6b9d62b6f15c5c4f8cf69e9ee79ab1b2e9296173b99cdf4def` (7821 B) — 12/12 byte-equal.
- Установленный hook: SHA256 `40b6f5e5edad6b8349c3143e032e29d2d02fa5cd1362c9ba9c10dbdbc2bdc88d` (697 B) — 12/12 ровно один, old hook (458 B, `2e10a1c6…8ec9`) 0 вхождений.

## 1. Собственная батарея (не копия чекера operations)

`QA2321-BATTERY.json`: **286/286 pass, exit 0**. Секции:
A) Freeze-цепочка: BASELINE `5490e880…1f817`; SUBJECT head `2fedef53…600e`; 6/6 members; QA-CANDIDATE-FIXED `ed4d00c9…75d3`; CONSUMER-ACCEPTANCE-RECEIPT `30a1e12e…868d`; APPLY.json `e7fe2920…3495`; COMPANY-GO биндит тот же head; inputs 26/26, snapshots 24/24, before-trees 27/27 побайтово.
B) Live 12 целей: reference byte-equal 12/12; one-new-hook+no-old-hook 12/12; remainder `after_root − hook == before_root − old_hook` 12/12 (побайтово, из frozen before-снапшотов, а не из чьих-то слов); after-root SHA пересчитан из арифметики и совпал с живым файлом 12/12; name-set captured Markdown tree без изменений 12/12; все прочие .md байт-равны baseline; frontmatter (name=company-os, description) и entrypoint-ссылка 12/12; *.applytmp-остатков нет. Группировка after-roots: 3 distinct (company `7c498bbb…` соло; research `a1793d7c…` соло; остальные 10 `331ac2fb…`) — совпадает с тремя distinct before-базами.
C) Receipt рана 2320: 12/12 APPLIED, before/after-хэши побочно совпали с BASELINE и живыми файлами, errors=[].
D) Backups: 12/12 профилей, ровно {SKILL.md, dots-operating-method.md}, хэши = before (материал own-bytes rollback подтверждён).
E) APPLY-VERIFY.json распарсен: 98 ключей ровно = ожидаемые 2+12×8, все true. APPLY-LOADER.json: 12 профилей, все loaded.
F) Прежний стандарт `dots-20261003` сохранён: LOAD-HOOK.md и 8 verified-dots-sources байт-равны входам BASELINE.
G) APPLY.md без overclaim'ов: «статическая установка», «не подтверждает будущее послушание», финансовые поля null + явное «не утверждение "0 ₽"»; запрещённых формулировок (full live stop / экономический эффект подтверждён) нет.

## 2. Независимый loader-readback (свой probe, не APPLY-LOADER.json)

`QA2321-LOADER.json`: реальный `tools.skills_tool.skills_list` vendored-инсталла против scoped temp-копий каждого живого корня (fresh HERMES_HOME, чистый кэш на профиль): **12/12 loaded**, name=`company-os`, description парсится, hook-ссылка присутствует в serving-корне. Exit 0. Предел: это discovery/parse readback, не поведение живого профиля в рантайме.

## 3. Serving-lineage (три непересекающиеся линии)

- Source author (brain): gpt-6.1-sol / openai-codex (AUTHOR-LINEAGE.json, сессия 20261003_231256_1a496e).
- APPLY issuer (operations, сессия 20261004_042155_ee47b0): main-линия 32 штампа = kimi-k3 / custom (`msg='work kanban task t_63f62c17'`); 1 штамп qwen3.8-max/custom — origin=background_review (skill-library), не main.
- Source reviewer (run 2319): 60 main-вызовов glm-5.3 / zai (QA2319-NATURAL-LINEAGE.json).
- Этот ревьюер (сессия 20261004_042700_8fb555): 21/21 main-штампов = glm-5.3 / zai; иных main-моделей в сессии не наблюдалось (отсутствие не доказано).
- Пересечения пар model/provider между author ↔ issuer ↔ этим ревьюером: НЕТ. Первоначальный source-вердикт и новый эмитент сохранены раздельно.

## 4. Сценарии и границы источника

QA-CANDIDATE-FIXED.json: M01–M17 = 17/17 confirmed, S01–S17 = 17/17 CONSISTENT — переприняты как approved source evidence (subject hashes unchanged, проверено секцией A), плюс мой контроль: installation-артефакты не заявляют full runtime stop / obedience / экономику (секция G).

## 5. Процессная заметка

В логах рана 2320 видна первая самобатарея operations 86/98 (12 падений `captured_markdown_tree_unchanged`) и первый loader-probe all-False до финальных 98/98 и 12/12. Расхождение разрешено НЕ доверием к нарративу, а собственной батареей этого рана: все 12 tree-проверок побайтово зелёные на живых файлах сейчас, loader 12/12 моим probe. Ни одного live-write вне allowlist не обнаружено (24/24 путей = permitted_live_writes).

## 6. Финансовый охват

scope: fleet-ops internal method normalization (COMPANY-BRIEF → финальное QA); source: натуральные штампы/чекеры этого рана; ledger не читался. confirmed_revenue / refunds / incremental_paid_costs / new_commitments / estimated_usage_cost = **null** (не измерено; не заявление «0 ₽»). Новых платных заказов/капабилитетов в скоупе нет.

## Артефакты

- FINAL-QA.md (этот файл), FINAL-QA.json (машинный, рядом)
- QA2321-BATTERY.json — 286/286, exit 0
- QA2321-LOADER.json — 12/12, exit 0
