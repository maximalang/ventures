# SPEC: KPI-дельта — недельное измерение автороутинга (официальная практика №9)

Дата: 03.10.2026. Исполнитель: operations. Гейт: после независимой QA v4
(карта-предок). Основание: PROGRAM.md v2.2 «Метрики», CANON-MERGE §2.3 —
«роутинг на вайбах = скрытая регрессия; измеряем KPI-тройкой».

## Deliverables

1. `kpi_delta.py` (≤200 строк, stdlib, 0 сети, 0 записи в БД) в
   `C:/Users/max/AppData/Local/hermes/profiles/company/scripts/`:
   - Read-only срез `session_model_usage` тех же 13 профилей тем же методом, что
     BASELINE (URI mode=ro; поля input/output/cache_read/reasoning/calls).
   - Diff против `BASELINE-20261003.json`: дельты токенов по рельсам за окно.
   - Парсер `ROUTING-LOG.md`: строк журнала, доля override (совпало=нет по вине
     company), доля эскалаций (prior_run_failed).
   - Счётчик QA-блокировок по классам из VERDICT-MATRIX*.md (PASS/FAIL по картам
     программы; при отсутствии — 0 с пометкой).
   - Выход: `--week` печатает Markdown-сводку; `--selftest` — 3 встроенных кейса
     (парсер лога, diff-арифметика, пустые входы) exit 0/1.
2. Первый прогон: `KPI-WEEKLY-20261003.md` в директории программы (граница старта
   тени; дельты ≈ 0 — это нормально, фиксируется точка отсчёта KPI).

## Acceptance

- `python kpi_delta.py --selftest` exit 0.
- `--week` печатает непустую сводку; БД не изменена (открытие только mode=ro).
- wc -l ≤200; сетевых импортов нет; секреты не читаются (.env* не открывать).

## Запрещено

- Не трогать model_router.py, конфиги, кроны; никаких live inference; платных API нет.

## §QA (карта-потомок, qa)

Fresh --selftest exit 0; самодельный ROUTING-LOG-фрагмент считается верно (проверить
вручную 3 строки); diff-числа сходятся с ручной арифметикой по 2 рельсам; режим
только чтение (в выводе нет SQL-записей). Вердикт — дополнение VERDICT-MATRIX-v4.md
или отдельный VERDICT-KPI.md. Финансы: 0 ₽ incremental (05–06.10, source null).
