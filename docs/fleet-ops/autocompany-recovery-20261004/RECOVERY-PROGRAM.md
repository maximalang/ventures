# RECOVERY-PROGRAM: замыкание контура автокомпании (04.10.2026)

Восстановление контекста 02–04.10 по поручению владельца: «исправить сам корень,
восстановить все задачи, которые улучшают и закрывают контур; правки не должны
лежать и ждать применения».

## Диагноз корней (company, 04.10, проверено кодом и git)

- **RR-1 Грязный control plane.** Живой fleet-policy = v1.2.34, существует только
  как 12 незакоммиченных файлов в detached-clone `profiles/*/plugins/fleet-policy`
  (HEAD 4908dd4d = v1.2.31), одинаково во всех 10 профилях. Trunk `codex/company-os`
  @287e86c = v1.2.31 и НЕ содержит v1.2.32→34 (W2(b) quote-aware split,
  W4 masked-quote-spans — grep `_mask_exempt_quote_spans`: trunk=0, live=2).
  Любой reinstall/откат теряет живые фиксы. PR #55 (v1.2.36, base=trunk) при
  деплое ОТКАТИЛ бы v1.2.34 — активация остановлена правильно.
- **RR-2 Третья линия.** Ветка `fix/deny-remediation-routes` (b07b07a, desktop
  checkout) не в trunk — ещё одна «лежащая правка».
- **RR-3 Маршрут деплоя не определён.** policy-controlled файлы лексически
  immutable для всех сессий флота (policy.py:1557-1560, hard deny, без approval
  route). Прошлые деплои шли через operator-сессии/лексическую непрозрачность.
  Карточки активации требовали деплой от воркера → гарантированный deny-луп
  (run 61, call_index=5). Нужны: operator deploy-скрипт + правило «воркер
  готовит bundle, company применяет».
- **RR-4 False-positive классы классификатора.** (a) heredoc/quote fail-closed →
  read-only диагностика (sqlite probe kanban db) классифицируется state_change →
  hard deny; (b) `ls` каталога сессий → secret_read_or_write (t_90c07896 run 41);
  (c) литеральные ловушки: gate-литералы в body → gate_forgery на эхе (run 55),
  task_type-литералы в комментариях → перманентное отравление карты (POISON).
  Deny-текст советует «tech-карту», хотя реальный маршрут деплоя — operator.
- **RR-5 Staged-дрейф.** 19 `*.new.py` в profiles/company/scripts (29.09–03.10):
  gateway_watchdog staged НОВЕЕ live (105 строк diff — не применён), card_readiness
  staged СТАРЕЕ live (протух), deny_triage_bot идентичен (применён). Механизма
  «примени или retire в той же сессии» нет.
- **RR-6 Висячие артефакты.** INSTRUCTION-DEBT.md не был приложен к карте
  (attachments пусто, scratch вычищен); спасён только потому, что воркер
  дублировал его в repo (instruction-quality-20261004/). Этап B и C PROGRAM.md
  не диспатчились.

## Карты восстановления (созданы 04.10)

| Карта | ID | Assignee | Содержание | Родители |
|---|---|---|---|---|
| A1 capture | t_945d1772 | tech | Захватить dirty-diff v1.2.32→34 в trunk коммитами + PR + тег v1.2.34; решить судьбу b07b07a; включить docs рабочего дерева | — |
| A1-QA | t_85547708 | qa | Независимая сверка PR-дерева с живым клоном, эмиссия ci/review на A1 | t_945d1772 |
| A1b integrate | t_b7fe9ddf | tech | Интегрировать trunk (v1.2.34) в feat/v1236-router-hook-native, version→1.2.36, CI, новый head SHA | t_945d1772 |
| A2-rearm | t_38c0f11a | qa | Перевыпуск ci/review на t_9eb08cc4 под новый head PR #55 | t_b7fe9ddf |
| активация | t_9eb08cc4 | operations+company | Merge PR #55 (воркер) → bundle+runbook → [continues: company] → operator-деплой v1.2.36 shadow (company) | t_38c0f11a |
| A2 root-fix | t_e393b6e8 | tech | FP-классы (a)(b)(c) + правдивый remediation-текст + deploy_policy.sh (operator) + регресс-тесты инцидентов 04.10 | t_945d1772 |
| B staged-sweep | t_1a1c8e5f | operations | Аудит 19+ `*.new.py` (pending/superseded/identical), применить pending с бэкапом+тестами, retire протухших, сторож staged-возраста | — |
| D stage-B | t_01ef3e7e | product | Instruction-quality этап B: draft-каркас (core-SOUL ~50 строк, fleet-слой, owner-style, visual-canon, memory-план, verb-ladder). Только draft, применение — слово владельца | — |
| (позже) stage-C | — | product/qa | Пилот на одном воркер-профиле + correction-rate до/после (2 недели) | D + слово владельца |

## Правила, вынесенные из инцидента

1. Деплой policy-controlled файлов — ТОЛЬКО operator-действие company (воркер:
   merge/bundle/runbook, затем [continues: company]).
2. Никаких литералов верификационных маркеров и task_type-токенов в телах карт
   и комментариях (кроме санкционированной binding-строки эмиссии).
3. Staged-правки применяются или retire-ятся в той же сессии; сторож сообщает о
   `*.new.py` старше 24ч.
4. Артефакты аудиторских карт — в repo (docs/), не в scratch; attachment обязателен.
5. Живой control plane всегда соответствует тегу repo; dirty-дрейф запрещён
   (deploy_policy.sh ставит из тега, не правкой на месте).

## Финансы

0 ₽ incremental (квоты профилей). Период: 04.10.2026. Источник: существующие
мандаты; новых обязательств нет.
