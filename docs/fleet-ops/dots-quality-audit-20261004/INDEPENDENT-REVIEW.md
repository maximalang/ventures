# INDEPENDENT-REVIEW — Dots ↔ Hermes quality audit (t_7638de4f, profile qa, run 2333)

Дата: 2026-10-04T08:51:13Z. Класс результата: **audit outcome** (независимый
ограниченный re-execution аудит). Это НЕ исправление, НЕ внедрение, НЕ
merge/runtime verdict. Отрицательные и частичные выводы — часть доставленного
аудита, внедрение не выполнялось (scope: inspect-only).

## 1. Якоря и целостность входов

- AUDIT-SUBJECT.json SHA256 = `6fea85f0637011c110c8bf6068706c5dd78492159292815ea90408f320693658` — совпадает с якорем company-комментария карты.
- Исходная установка SUBJECT.json head = `2fedef53211adc07445caee7d4d3ef3cac4df5e7544508ca35a26e040774600e` — подтверждён по содержимому AUDIT-SUBJECT и FINAL-ACCEPTANCE.md.
- **6/6 member hashes MATCH** (sha256 + bytes пересчитаны из файлов, не приняты по receipt): audit_current.py, AUDIT-EVIDENCE.json, LIVE-SNAPSHOT.json, NATIVE-SOURCE-PROBE.json, KANBAN-READBACK.json, FINDINGS-DRAFT.json.

## 2. Метод (собственный прогон, не пересказ receipt)

- Собственный проверочный скрипт `independent_checks.py` написан с нуля в
  workspace задачи qa (sha256 `e0167ed666aa65438996c05860c2959ac25dc05dee3d5ee8f68d5b57b668a877`),
  исполнен каноническим установленным Python 3.11.9, **exit 0**;
  машинный вывод сохранён: `independent_checks_out.json`
  (sha256 `0ca6be5f3916c1d74cad0b21805725f4e327a7c5c4e218fd8e872d153c9e100d`).
- `audit_current.py` использован как harness reference; каждое число ниже
  получено собственной батареей. Читаны только разрешённые пути: 6 members
  AUDIT-SUBJECT; файлы dots-hermes-standard-20261004 из списка QA-SPEC;
  ровно 24 live root/reference пути из BASELINE.targets; два native исходника
  (`hermes_cli/kanban_db.py`, `hermes_cli/kanban_db_graph.py`) в SQLite
  `:memory:` fixture — реальная доска не открывалась.
- Линия этого рана (наблюдаемая): reviewer glm-5.3-flash/zai (run 2333).
  Автор аудируемых артефактов: gpt-6.1-sol/openai-codex. Оригинальные QA-линии
  run2319/run2321: glm-5.3/zai. Пересечений reviewer/author по main-штампам на
  доступных evidence не видно; полные auxiliary-цепочки прежних линий не
  аттестованы — independence ограничено так же, как预期 QA-SPEC.

## 3. Независимо измеренное

### Live file checks (ровно 24 разрешённых live-пути, 12 целей)
120/120 проверок пройдено: reference байт-в-байт = REFERENCE-CANDIDATE;
новый hook ровно 1 раз, старого hook-набора нет; live root == APPLY
after/intended; арифметика сохранения root (before−old_hook == live−new_hook);
before-снимки привязаны к BASELINE; apply-backups байт-равны before.

### Каталог стандарта
192 файла; 26 JSON; единственный JSON-дефект — намеренно сохранённый
дубликатный QA-CANDIDATE.json (ключи: checks_this_run, m01_m17,
scenarios_s01_s17, reviewer_lineage_run_2319). Python AST ошибок: 0.
Дубликатных групп: 6, избыточных байт: 579689 (36×12995, 30×2050, 4×15889,
3×3601, 2×6106, 2×4439) — все это before/apply-backups/before-trees/local
снимки (safety/provenance), не вторые live-workflows.

### ZIP
sha256 `661c522692d2bd9c896a627bfe545531fa69db7c54d2e648e480a337c604e201`,
1 309 730 B; CRC чист (testzip = null), bad members: 0; 157 payload + manifest
= 158 — **арифметика подтверждена, разница 157/158 не ошибка**; manifest сам
исключён из payload. Вне архива: 6 именованных check/source-файлов и все 24
documented apply-backups пути; при этом все 24 альтернативных before/-снимка
в архиве и байт-точны (rollback-байты НЕ потеряны).

### Native helpers (fixture, не live)
AST-извлечены те же три функции; файлы: kanban_db.py sha `ed19affa…`,
kanban_db_graph.py sha `b3aada2c…`. В `:memory:`: родитель `done` принимает
комментарий и освобождает ready-ребёнка; running/archived → todo; missing-id
контролы дают `unknown task …` / `unknown parent task(s): …`. Это семантика
data-слоя, НЕ live policy admission.

### Serving metadata (company-export evidence, консумировано как метаданные)
NATIVE-FINAL-READBACK.json: 12/12 row_ok, head 2fedef53. KANBAN-READBACK.json:
t_d090b4ff (fleet-ops) done, t_63f62c17 (fleet-ops) done, t_29903deb
(**default**) done.

## 4. Диспозиции 8/8

| ID | Вердикт | Суть | Locus / evidence | Severity |
|----|---------|------|------------------|----------|
| F01 | **CONFIRMED** | Ложное learned-правило «done отвергает комментарии/parent-links». Fixture: done принимает комментарий, ребёнок становится ready; ошибки — lookup-only; t_29903deb живёт на default-доске → причина исходных сбоев — не done-статус. | PROCEDURE-CORRECTION.json; kanban_db.py 1786–1806; kanban_db_graph.py 25–51; свой fixture | high (поправлено только в company skill, не fleet rollout) |
| F02 | **CONFIRMED** | ZIP валиден, но не самодостаточен для named checks и документированных rollback-путей: 6 источников + 24 apply-backups пути отсутствуют; 24 before/-альтернативы в архиве байт-точны. | свой ZIP-pass; APPLY.md; QA-CHECKER-RUN2319.py | medium |
| F03 | **CONFIRMED** | Исправленный receipt самоидентифицируется как дефектный: `artifact` и `artifacts.qa_candidate_json` ссылаются на QA-CANDIDATE.json (файл с дублями ключей). Явно-именованные потребители в безопасности; self-link-последователи могут попасть в сохранённый дубликатный файл. | QA-CANDIDATE-FIXED.json (прямой read) | medium |
| F04 | **CONFIRMED** | Финальная company-приёмка вне канонических тредов карт: в трёх тредах нет финального acceptance-комментария (11/6/2 комментария, все false); FINAL-ACCEPTANCE.md существует на диске и связывает head; трассировка фрагментирована, не отсутствует. | KANBAN-READBACK.json; FINAL-ACCEPTANCE.md | medium |
| L01 | **PARTIAL** | Runtime-эффект и полная live loader-eligible не проверены — это явное scope-limitation, не провал обещанных тестов. Показано: loader на изолированных копиях 12/12; файловые проверки 120/120. Не показано: disabled-state оригинальных профилей, коллизии, runtime invocation, stop/cancel, экономика. | FINAL-QA limits; qa2321_loader.py; LIVE-SNAPSHOT | informational |
| L02 | **CONFIRMED** | LANE release_state = held — устаревший pre-release снимок: все три привязанные карты фактически done. LANE объявляет audit binding, не второй реестр; без ярлыка supersession это stale-дефект, купированный декларацией. | LANE.json vs KANBAN-READBACK.json | low |
| H01 | **PARTIAL** | Дубликаты — намеренные preimages/backups, не вторые workflow (6 групп, 579689 B, recounted). Никаких удалений не оправдано. Малый истинный hygiene-остаток: два не-финальных helper-скрипта в корне (_company_readback.py 2356 B + _qa_verify.py 9377 B = 11733 B) вне ZIP. | AUDIT-EVIDENCE; свой инвентарь | low |
| O01 | **CONFIRMED** | Нужен один авторитетный entry-индекс (accepted vs historical receipts vs tools) и воспроизводимый frozen file-list: 34 локальных файла вне ZIP; связка F02/F03/L02 делает индекс самым дешёвым улучшением. Без новой schema/dispatcher/шаблона; hook уже conditional и scoped. Эффекты не измерены — рекомендация, не реализация. | _package_standard.py; свой список not-archived | low |

Defect vs accepted scope limitation: F01, F02, F03, F04, L02 — дефекты
(разной природы: неверный урок, packaging, traceability, stale snapshot);
L01 — принятая граница проверки; H01 — по большей части намеренный дизайн с
небольшим hygiene-остатком; O01 — оптимизация.

## 5. Дельта файлов аудита

До этого рана в директории: QA-SPEC.md, AUDIT-SUBJECT.json, audit_current.py,
AUDIT-EVIDENCE.json, LIVE-SNAPSHOT.json, KANBAN-READBACK.json,
SCOPE-SNAPSHOT.json, FINDINGS-DRAFT.json, PROCEDURE-CORRECTION.json,
NATIVE-SOURCE-PROBE.json. Этот ран добавляет ровно два файла:
INDEPENDENT-REVIEW.md и INDEPENDENT-REVIEW.json. Frozen inputs не менялись;
все остальные записи — только workspace задачи qa.

## 6. Итог

Установка байт-целостна на момент аудита: 120/120 собственных live-проверок,
ZIP чист, 6/6 member hashes. Подтверждённые дефекты: F01 (исправлен точечно,
не fleet-wide), F02, F03, F04, L02. L01 — честная граница. H01/O01 —
hygiene/optimization. Не заявляется: runtime-поведение, послушание моделей,
stop/cancel, loader-eligible в оригинальных профилях, экономика; не выдаётся
rollout/merge/implementation verdict.

Финансовый scope: fleet-ops quality audit 2026-10-04; source = проверки и
естественные serving-штампы, ledger не читался. confirmed revenue = null,
refunds = null, incremental paid costs = null, new commitments = null,
estimated usage cost = null (не измерено; это НЕ утверждение «0 ₽»).
