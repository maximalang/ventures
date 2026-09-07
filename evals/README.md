# Company OS evals v1 — LLM-judge harness

Герметичный (для CI) + живой (для gate-прогонов) харнесс оценки текстовых
выходов флота (дайджесты, решения, QA-вердикты, эскалации) по пяти
замороженным рубрикам. Карта t_b8a7c165, решение владельца 07.09.2026.

## Аттрибуция паттерна

Harness pattern (YAML-сценарии с замороженными рубриками, LLM-judge со
структурированным JSON-ответом 1–5, canary-сценарии испорченных выходов,
регрессионный baseline) адаптирован — не портирован — из
**SenteLabsAI/OpenExecutive** (Apache License 2.0, head `b071101`),
`packages/core/openexecutive/evals/`. Код в этом каталоге — оригинальная
реализация для maximalang/ventures; ни один исходник OpenExecutive не
скопирован. Judge-промпт, рубрики и гейт-правила выведены из канона
Company OS (evidence-first, kill-критерии, owner-коммуникация в
`OPERATING_SYSTEM.md` / `APPROVALS.md` / `README.md`).

## Состав

| Файл | Назначение |
|---|---|
| `rubrics.yaml` | 5 замороженных рубрик + конфигурация judge/gate/budget, `rubric_version` |
| `scenarios.yaml` | корпус v1: 4 benchmark + 1 reference (реальная запись decision-ledger #1) + 2 canary |
| `judge.py` | OpenAI-совместимый клиент рельса qa-профиля, замороженный промпт (sha256 в `rubrics.yaml`), JSON-парсер verdict, учёт токенов |
| `gate.py` | агрегация скоркарда + правила гейта + формат baseline |
| `run_evals.py` | CLI живого прогона: судит корпус, печатает скоркард, применяет гейт |
| `baseline.json` | замороженный baseline прогона v1 (эталон регрессии) |
| `../tests/test_evals_harness.py` | герметичные unit-тесты (парсер, агрегация, гейт, валидация корпуса) — без сети/ключей |

## Гейт (заморожен v1)

1. Среднее по benchmark-сценариям (все рубрики) **>= 3.5**.
2. Ни одна рубрика (среднее по benchmark) не упала **> 10%** относительно `baseline.json`.
3. Canary-детект: испорченный brief — среднее **<= 2.5** и `evidence_grounding`
   минимум на **1.0** ниже benchmark-близнеца.
4. Суммарный расход токенов судьи **<= 200 000** на прогон.

Судья — рельс qa-профиля (kimi-k3 по умолчанию, glm-5.2 как альтернатива)
через OpenAI-совместимый endpoint; ключ — переменная окружения рельса.
Судья никогда не является автором оцениваемого текста.

## Запуск

```bash
# герметичные тесты (CI, без сети)
uv run --frozen python -m pytest tests/test_evals_harness.py -q

# живой прогон + гейт (нужен ключ рельса qa в окружении)
python evals/run_evals.py
# альтернативная модель судьи
python evals/run_evals.py --judge-model glm-5.2
# перезапись baseline (осознанное действие при смене rubric_version)
python evals/run_evals.py --record-baseline
```

Exit code: 0 — гейт пройден, 1 — гейт провален, 2 — дрейф промпта судьи,
3 — сбой вызова судьи.

## Заморозка рубрик

Промпт судьи заморожен: его sha256 записан в `rubrics.yaml`
(`judge.prompt_sha256`) и проверяется при каждом запуске и в unit-тестах.
Изменение промпта/рубрик требует: поднять `rubric_version`, обновить пин
sha256, осознанно перезаписать `baseline.json` и поправить пин в
`tests/test_evals_harness.py`. Дрейф без этих шагов роняет прогон (exit 2).
