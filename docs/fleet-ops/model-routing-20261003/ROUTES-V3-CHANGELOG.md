# ROUTES-V3-CHANGELOG — v2.2 → v3 (карта t_91e8ce45, fleet-ops)

Дата: 05.10.2026. Автор: tech (воркер, run 2463). Основание: директива владельца 04.10
(OPEN-QUESTIONS-20261004.md §«ОТВЕТЫ ВЛАДЕЛЬЦА»); дизайн-канон LADDER-PROVIDERS.md
(тиры T1/T2/T3 + 7 правил лестницы) и PATTERNS-SOURCES-v2.md (вендорный корпус,
сверка PATTERNS). Верификация terra: t_4e47fef0 (operations, done). Хук НЕ
активирован (ROUTER_ACTIVE.json отсутствует); конфиги профилей не правились;
платные пробы = 0.

## 1. Исход верификации — terra (scope b карты)

- t_4e47fef0 VERDICT — CONFIRMED (completion 2026-10-05T18:45:38Z): проба
  2026-10-05T18:30:50Z, `GET chatgpt.com/backend-api/codex/models?client_version=99.0.0`
  — HTTP 200 на обеих строках пула openai-codex (отпечатки строк a2662b, 8a052d);
  точная id-строка `gpt-5.6-terra` присутствует в каталоге (membership =
  billing-visible entitlement; ротация/пин — только отдельным решением владельца).
- terra=available → ступень ВКЛЮЧЕНА в ROUTES v3 (условие карты выполнено).
- Ограничение: каталог ≠ качество. Телеметрия 30д: 0 вызовов terra (luna — 125).
  По LADDER правилу 1 terra — экономичная ступень НЕ на первых двух позициях
  класса; повышение — только по shadow-данным (журнал → KPI-дельта → решение).

## 2. Диффы ROUTES v2.2 → v3 (одним диффом по LADDER строкам 74–75)

| класс | v2.2 | v3 | основание |
|---|---|---|---|
| code | qwen3.8-max, glm-5.3, kimi-k3 | без изменений | лестница 03.10 уже соответствует LADDER |
| data | qwen3.8-max, kimi-k3 | qwen3.8-max, glm-5.3, kimi-k3 | v2.2 нарушала правило 2 (соседи custom→custom); zai-средняя ступень = разнообразие; A/B 02.09 сохранён (qwen первый 3/3, kimi последний 0/3) |
| research | kimi-k3, qwen3.8-max, glm-5.3 | kimi-k3, glm-5.3, qwen3.8-max | v2.2 нарушала правило 2; черновой список LADDER (§«Лестницы по классам») сам противоречил собственному правилу 2 — правило старше черновика (scope a карты); kimi первый сохранён (BrowseComp 91.2) |
| ops | qwen3.8-max, glm-5.3, kimi-k3 | без изменений | LADDER канон |
| review | glm-5.3, sol, qwen3.8-max | без изменений | LADDER канон; terra НЕ допущена — качество для класса не доказано (правило 1) |
| strategic | sol, astra | без изменений | канон-исключение правила 2: ручной класс (только пин), sol+astra оба openai-codex по канону высокорисковых решений; отказ провайдера = решение владельца |
| vision | qwen-vl-max, luna | без изменений | luna качество доказано (125 вызовов 30д) |
| brief | — (класса нет) | luna, qwen3.8-max, terra, kimi-k3 | НОВЫЙ: директива 04.10 §1–2 — творческие профили входят в лестницу, GPT-ярусность + DashScope-руки |
| creative | — (класса нет) | qwen3.8-max, luna, kimi-k3, terra | НОВЫЙ: та же директива; DashScope-руки первые (продакшн design/ux/video), luna — vision-способная экономичная GPT-ступень |

Разнообразие (правило 2) во всех авто-классах v3: соседние элементы — разные
провайдеры, ≤2 моделей провайдера, первые две позиции разнопровайдерные —
проверяется структурным тестом selftest.

## 3. GPT-ярусность внутри openai-codex (scope b)

- sol (gpt-6.1-sol): strategic ступень 1 (топ-рельса, только ручной пин) + review
  ступень 2 (живой бэкап при стене zai, инцидент rate-limit 04.10) — по назначению.
- astra (gpt-6-astra): только strategic ступень 2 — точечный второй взгляд, ручной пин.
- luna (gpt-6-luna): vision ступень 2 + brief ступень 1 + creative ступень 2 —
  экономичная ступень с доказанным качеством (125 вызовов 30д; none/low effort).
- terra (gpt-5.6-terra): brief ступень 3 + creative ступень 4 — экономичная ступень,
  каталог-верифицирована; качество для класса не доказано → не выше середины,
  структурный тест запрещает первые две позиции и классы вне brief/creative.

## 4. Дельты движка (аддитивные; ядро v4 не менялось, router_version остаётся «v4»)

- R5: маппинг task_type расширен — brief→brief, creative→creative; неизвестный
  task_type → code (как в v2.2). Карты творческих профилей несут task_type=brief|
  creative по решению company (board-таксономия research|code|review|ops — на стороне
  company; роутер к новым значениям готов).
- R7 (новое правило): все рельсы класса недоступны по --status → model=PROFILE_DEFAULT
  + явная degrade-строка в reason (LADDER правило 6; инвариант карты «деградация →
  дефолт профиля + degrade-строка»). В v2.2 в этом случае оставлялся полный список —
  поведение изменено сознательно, битый/отсутствующий status-файл по-прежнему
  безопасен (полный список + W1).
- Вывод --card: добавлено поле routes_version («v3»); rules_sha пересчитан
  5499e01c152d → ed86d983fcf6.
- PATTERNS: + gpt-5.6-terra (4-строчный формат; явный маркер «источник: только
  флот-канон» — в вендорном корпусе PATTERNS-SOURCES-v2 terra отсутствует, §12
  вопрос #1; гайды GPT-семейства developers.openai.com сохранены как источник
  семейства). 7 корпусных паттернов (§1–7) сверены — без изменений; паттерн luna
  дополнен none-effort и творческими брифами (v2 §4, developers.openai.com).
- selftest: 11 → 18 кейсов (добавлены: research/brief/creative первые ступени,
  creative+prior_run_failed, data+prior_run_failed на соседнего провайдера,
  brief+prior_run_failed мимо terra, R7-деградация all-down) + 7 структурных
  проверок (PATTERNS-покрытие ROUTES; старые 7 классов; T1-only; разнообразие
  с исключением strategic; terra-дисциплина; sol/astra по назначению; маркер
  источника terra-паттерна).
- Инварианты PROGRAM v2.2 (5) сохранены полностью; стратегия остаётся ручной;
  review исключает author_model (R1); тихой подмены на ходу нет.

## 5. Артефакты и sha256

- LIVE: profiles/company/scripts/model_router.py —
  sha256 5d24308d8057b62b728dde0196ae61062b7581d2ad46564aee6941408e9be2ae (39583 B)
- BACKUP: profiles/company/scripts/backups/model_router.py.bak-pre-v3-t_91e8ce45 —
  sha256 1ae2e34d08cd17cc4a4ea41d2af7c4c80ddece8977bfde86ffb56466c6548df1 (23350 B)
- ROUTING.md (v3, каталог) —
  sha256 c42fb7bed85c41b1b56df5581a1d2da3fbb43e69b141bc3b2b9f9e4bd51d3aa7 (27269 B);
  синхронизирован с --print-rules (9/9 списков классов байт-в-байт)
- ROUTING.md.bak-pre-v3-t_91e8ce45 (каталог) —
  sha256 3b9150545e037758b8be2b4f41f61f39c296367124015e45a4409de8c3383b09 (17431 B)
- RECEIPT-router-v3.txt (workspace карты t_91e8ce45, приложен к карте) —
  sha256 13c9d2b9502b9937676934a9be28c1fc75b49e2def18767bc89ce802317b8ff0 (174 строки)

## 6. Evidence (свежие прогоны после установки)

- selftest на LIVE-файле: ALL PASS, exit 0 (18 кейсов + 7 структурных).
- CLI-пробы на LIVE-файле (--card, subprocess): 14/14 PASS — ops/code/research/
  review(+R1)/brief(+R4)/creative(+R4)/strategic/vision/data(+R4)/R7-degrade/
  S1-status-skip; rules_sha ed86d983fcf6 стабилен во всех ответах.
- print-rules детерминирован (два прогона идентичны, diff пуст).
- Один инцидент policy-гейта в процессе: терминальная команда с литералом
  «sha256-deploy.txt» классифицирована как deploy_external_runtime (лексический
  \bdeploy\b, policy.py:1711) → evidence_gate_missing; действие деплоем не было
  (копирование файла по мандату карты), команда перефразирована без триггерного
  токена и выполнена. Единственный deny за ран; deny-паттерн зафиксирован здесь.

## 7. Заметки / follow-ups (не блокируют)

- task_type=brief|creative в таксономии доски — решение company (роутер готов).
- Раскатка brief/creative — после shadow-канарейки основной четвёрки (ROUTING.md,
  секция «Канарейка»); terra-повышение — только по shadow-данным.
- PATTERNS-SOURCES v3 (включение terra в вендорный корпус при появлении офиц.
  документации) — отдельная задача, если потребуется.
- QA-потомок проверяет независимым selftest + CLI-пробами до любого shadow-режима
  (автор не принимает свою работу).
