# SPEC: RR techstack-enrichment пилот (rev.1, 27.09.2026, author: company)

## Контекст и anchor
Решение владельца 27.09.2026: пилот обогащения лидов Recruiter Radar
техстек-сигналами. Локальная capability `webstack-scanner` УЖЕ построена и
проверена company (Defender clean, тест-прогоны hh.ru/vercel.com/RR):
канон запуска и правила — `C:/Users/max/Desktop/all/tools/capabilities/webstack-scanner/ACCESS.md`
(прочитать ПЕРЕД кодингом).
Anchor: origin/main head `3de9d87de3f6f7e4c5f31026260d78ceaf51b61f` (27.09.2026).
GO-якорь `decision:company=go` — отдельным комментарием на карте задачи.
Репо: `C:/Users/max/Desktop/all/recruiter-radar` (origin https://github.com/maximalang/recruiter-radar.git).

## Deliverable (ровно один PR)
Ветка `codex/techstack-enrichment` в ОТДЕЛЬНОМ git worktree (главный worktree
занят грязной веткой codex/dashboard-visual-refresh — НЕ трогать, не
переключать, не stash'ить). Состав:

1. Модуль обогащения: вход — домен компании лида; запуск CLI webstack-scanner
   (канон-команда из ACCESS.md) subprocess'ом с timeout 40 с и 1 retry;
   парсинг JSON-выхода; fail-closed: при fetch_error пишется error-evidence,
   пайплайн не падает.
2. Контракт сигнала: каждый найденный инструмент → запись evidence
   `{source:"techstack", tool, categories, confidence, version, scanned_at,
   domain}` в evidence_bundle лида по модели данных AGENTS.md §6.
   Только компании-уровень: никаких персональных email/телефонов (AGENTS.md §4).
3. Rate-limit guard: последовательные сканы, delay ≥1 с, ≤200 доменов на
   прогон, флаг полного отключения enrichment (feature flag, default off).
4. Unit-тесты на записанных JSON-фикстурах (БЕЗ живого HTTP в тестах):
   happy path, fetch_error fail-closed, guard-лимиты, маппинг в evidence.
5. Демо-батч: 20 реальных доменов из существующих данных RR (read-only; если
   локально недоступны — 20 публичных доменов RU mid-market из фикстур/док
   репо) → артефакт `artifacts/techstack-pilot/results.jsonl` + summary
   (доля доменов с ≥1 инструментом, топ-10 инструментов, суммарное время).
6. PR по AGENTS.md §1/§3: base — активная интеграционная ветка (проверить
   открытые PR и git branch -r; если явной нет — черновик в main).
   НЕ мержить: merge — отдельная gate-цепочка (ci/review/rollback).

## Acceptance (evidence — обычными словами в комментарий карты)
- Команды проверок репо (по CLAUDE.md) зелёные: команда + итог.
- Unit-тесты: команда + число passed.
- Демо: путь results.jsonl + числа (N доменов, % с инструментами, время).
- PR URL + точный SHA head ветки + git diff --stat сводка.
- Формальные gate-маркеры НЕ писать: их ставит qa на карте-потребителе.

## Запреты
- merge/push в main, deploy, миграции прод-БД (демо — read-only).
- живые сканы в unit-тестах/CI; демо-батч строго ≤20 доменов, delay ≥1 с.
- чтение .env*/секретов; персональные данные в артефактах.
- правки самой capability webstack-scanner (дефект → комментарий карты).
- скан доменов, рвущих TLS (ozon/avito/tbank-класс): пропуск + фиксация в summary.
- массовый outreach любого вида (AGENTS.md §4).

## Tool map
read_file/search_files — исследование репо; write_file/patch — код;
terminal — git/тесты/сканы (python-канон из ACCESS.md). code_execution
НЕдоступен. Коммитить каждые 20–30 мин работы (защита от loop-guard потерь).

## Финансы
0₽: локальный сканер, без платных API. stackfull.lol API — опциональный
второй источник (только последовательные вызовы), НЕ критичная зависимость.
Kill-критерий пилота (мониторит company): нет роста квалификации лидов
за 2 недели использования → модуль остаётся за флагом off, пилот закрыт.
