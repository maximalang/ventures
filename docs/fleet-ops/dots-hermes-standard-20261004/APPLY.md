# APPLY — dots-hermes-standard-20261004 consumer application (run 2320)

- card: `t_63f62c17` (fleet-ops, task_type=ops)
- issuer: operations (hands-writer), под `decision: company=go` (COMPANY-GO.md, 2026-10-04T04:21:42+03:00)
- source head (SUBJECT.json): `2fedef53211adc07445caee7d4d3ef3cac4df5e7544508ca35a26e040774600e` — verified byte-equal перед записью
- typed installation result: **applied 12/12**

## Что записано

24 файла, только из allowlist `permitted_live_writes_for_later_review` (BASELINE.json sha256 `5490e880…fa61f817`):

1. `references/dots-operating-method.md` → байты REFERENCE-CANDIDATE.md (`80933ccf…f4def`, 7821 B) в 12 корнях.
2. `SKILL.md` → старый hook-суффикс (458 B, `2e10a1c6…8ec9`) заменён на HOOK-CANDIDATE (`40b6f5e5…c88d`, 697 B), ровно один суффикс на корень.

Метод: staging в same-directory temp `*.applytmp-run2320-<ts>` → полный readback intended bytes → `os.replace`; непосредственно перед каждым replace повторная валидация live-хэша (F9). Прерываний не было, partial-файлов нет, temp-остатков нет.

## Gates (evidence chain)

- source QA (независимая): QA-CANDIDATE-FIXED.json sha256 `ed4d00c92f5b5574f22980f7b37db2c5d45008113e5e7efc192b6412f7ca75d3`, typed_verdict_word=PASS, 17/17 + 17/17 (t_29903deb, run 44)
- consumer acceptance: CONSUMER-ACCEPTANCE-RECEIPT.json sha256 `30a1e12ed2eb612298f1c6ade32981934811d7fa934e14eaf928af7d4b14868d` (8/8, main_pair_overlap=false)
- company GO: COMPANY-GO.md, exact-head binding совпал с замороженным SUBJECT

## Проверки (operations self-check)

- APPLY-VERIFY.json: **98/98 pass** — reference byte-equal payload 12/12; one new hook и no old hook 12/12; root-minus-new-hook == before-minus-old-hook 12/12; captured Markdown tree unchanged 12/12 (кроме двух intended targets); entrypoint link resolves 12/12; frontmatter valid 12/12; backup coverage 12/12; unique 12 profiles / 24 paths.
- APPLY-LOADER.json: **12/12 loaded** — реальный hermes loader (`tools.skills_tool._find_all_skills`, vendored install venv) против scoped temp-копий каждого корня: skill `company-os` разрешается, description парсится.
- APPLY.json (машинный): sha256 `e7fe29209540279aa2edd393ed94403a28a3bbb4b2f6cffdc554431839763495`.

## Backup / rollback

- До-образы: `apply-backups/<profile>/{SKILL.md, dots-operating-method.md}` — хэши совпадают с BASELINE before-hashes (проверено батареей).
- Baseline snapshots `before/` и `before-trees/` неизменны; старые `docs/fleet-ops/dots-20261003` и архив не тронуты.
- Rollback-процедура и own after-hashes: APPLY.json → `rollback`. При позднейшей чужой правке — HOLD, не откатывать вслепую.

## Limits / financial unknowns

- Статическая установка файлов; не подтверждает будущее послушание моделей или live stop.
- Loader readback подтверждает discovery/parse entrypoint'а, не runtime-поведение.
- confirmed revenue / refunds / incremental paid costs / new commitments / estimated usage = null (нет измерения ledger в скоупе; не утверждение «0 ₽»).

## Артефакты (durable, in-root)

- `APPLY-run2320-20261004T012335Z.json` — per-target before/after записи
- `APPLY-VERIFY.json` — батарея 98/98
- `APPLY-LOADER.json` — loader readback 12/12
- `APPLY.json` — машинный манифест
- `apply-backups/<12 профилей>/` — до-образы
