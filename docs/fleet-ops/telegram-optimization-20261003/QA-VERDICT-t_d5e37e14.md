# QA VERDICT — t_d5e37e14 (independent SOURCE-only QA of t_cef261ac + product artifacts t_6282d6b9)

Дата: 2026-10-03 · QA: отдельный worker, модель run: glm-5.3-flash · Метод: независимый rerun + собственные пробы, read-only против live company skills и durable evidence root. Live config/SOUL/skill/cron/model-записей нет.

## Вердикт

PASS — пакет t_cef261ac готов к bounded operations/company применению после go-анкора owner.
Продуктовые артефакты t_6282d6b9 соответствуют контракту (SOURCE-only, 5 шаблонов T1–T5, 12 fixtures S01–S12, runtime-клеймы отсутствуют корректно).

## Evidence

1. Свежий прогон авторского suite: `python tests/test_hub_packet.py` → `Ran 17 tests in 0.227s / OK`, exit 0
   (лог: kanban-workspace t_d5e37e14/qa-suite-fresh-run.txt).
2. Независимый probe (qa_probe.py в kanban-workspace, 15 проверок, 15/15 PASS, exit 0; машиночитаемо qa_probe_result.json):
   - C1 durable-дерево 24/24 файлов совпадает с HUB-PACKET-BUILD-t_cef261ac/DURABLE-TREE-SHA256.txt (нет missing/extra/mismatch);
   - C2+C15 live anchors (оба skill-дерева, 29 файлов) байт-в-байт == MANIFEST before_tree до и после QA (дрейфа нет);
   - C3 все candidate-хеши == MANIFEST candidate_tree; C4 rollback-снапшоты байт-равны live-источникам;
   - C5 frontmatter кандидатов байт-идентичен live (имена/триггеры сохранены);
   - C6 полное покрытие исходников срезами без потерянного контента (hermes-agent: fm 0..506 + 10 срезов до 13494/13494; fleet-token-economy: fm 0..99 + 8 срезов до 19878/19878);
   - C7 все 19 verbatim-срезов присутствуют байт-в-байт в назначении, маркеры/указатели на месте, HA-RT сохранён построчно + 3 добавленные строки, lever-4 owner-директива байт-exact в хабе;
   - C8 коррекции C1a/C1b/C2 применены, устаревшие строки отсутствуют во всём применённом дереве, owner-бан reset + факт плагина hermes-session-reset-policy 0.3.0 в levers-playbook;
   - C9 редукция пересчитана независимо: bytes 36294→12928 (−64.38%), chars 33372→12523 (−62.47%), манифест сходится, обе ≥60%;
   - C10 PRODUCT-BRIEF.md sha256 86faeddb…, SCENARIOS.json sha256 286d7202… == PRODUCT-DELIVERY.json; S01–S12 уникальны, у каждого ≥3 pass_oracle + fail_example + source_refs; runtime_results=null, not_user_observations=true; independent_qa_status «pending t_d5e37e14» (SCENARIOS.json) подтверждается этим отчётом;
   - C11 claim'ов «экономия токенов» нет; везде chars/bytes ≠ tokens, cash-экономия не заявляется;
   - C12 APPLY-ROLLBACK.md покрывает все 4 якорных хеша и все 9 новых ссылок командами apply/rollback;
   - C13 три независимых лога прогона (run2219-durable, admin, свежий QA) содержат «Ran 17 tests … OK»;
   - C14 гигиена пакета: только задокументированные top-level пути.
3. Воспроизведение сборки: build_packet.py (копия с перенаправленным workspace в kanban-workspace QA) выполнен, rc=0; все 16 генерируемых файлов побайтно идентичны durable-пакету. 5 отличий — не-генерируемые authored-файлы (README.md, APPLY-ROLLBACK.md, INVARIANT-MAP.md, reference/COMMUNICATION-TEMPLATES.md, tests/test_hub_packet.py), что соответствует заявленному методу сборки.
4. Независимый полнотекстовый аудит (qa_audit.py, exit 0): ни одна непустая prose-строка live-хабов не потеряна (hub→refs/hub); каждая prose-строка новых refs трассируется в live-источник — исключения только документированные: provenance-баннеры «moved … (t_cef261ac …)» и точные рендеры коррекций C1a/C1b/C2. Gate-маркерных литералов в пакете нет; COMMUNICATION-TEMPLATES.md явно помечен как рекомендация, не обязательная надстройка.

## Ограничения (не блокируют)

- Статическая offline-проверка: символьная редукция ≠ токены/деньги; runtime-эффект доказывается только шагом 6 контракта (естественные вызовы ≥10/stratum после bounded применения).
- Live-применение QA не выполнял и не разрешает:.Apply = operations/company после go-анкора owner, rollback-список проверен на полноту (C12).

## Артефакты QA

- C:/Users/max/AppData/Local/hermes/kanban/boards/fleet-ops/workspaces/t_d5e37e14/qa_probe.py (+qa_probe_result.json)
- C:/Users/max/AppData/Local/hermes/kanban/boards/fleet-ops/workspaces/t_d5e37e14/qa_audit.py
- C:/Users/max/AppData/Local/hermes/kanban/boards/fleet-ops/workspaces/t_d5e37e14/qa-suite-fresh-run.txt
- C:/Users/max/AppData/Local/hermes/kanban/boards/fleet-ops/workspaces/t_d5e37e14/qa_build_repro.py (+восстановленный HUB-PACKET/)
- Этот отчёт: C:/Users/max/Desktop/all/ventures/docs/fleet-ops/telegram-optimization-20261003/QA-VERDICT-t_d5e37e14.md
