# SPEC: досье best-practices LLM-роутинга (фаза A, fast-lane)

Исполнитель: research (custom/kimi-k3 max, дефолт профиля). Родитель программы:
`ventures/docs/fleet-ops/model-routing-20261003/PROGRAM.md` — прочитать первым.
Следующий владелец результата: company (пост-аудит выборки).

## Deliverable

Файл `C:/Users/max/Desktop/all/ventures/docs/fleet-ops/model-routing-20261003/RESEARCH.md`
— досье внешних практик роутинга LLM, применимых к мультипрофильному флоту на Hermes.

## Обязательные разделы

1. **Паттерны (≥8)**, каждый = название + 1–2 абзаца + КОНКРЕТНОЕ ЧИСЛО + URL
   первоисточника. Стартовый набор (найдено company, проверить и раскрыть):
   - RouteLLM: https://www.lmsys.org/blog/2024-07-01-routellm , https://arxiv.org/html/2406.18665v4 , https://github.com/lm-sys/routellm (40–85% экономия при 95% качества; overhead правил <1ms).
   - Лестница рунгов (rules→weighted→latency→cost→semantic→cascades) и «routing ≠ failover»: https://www.truefoundry.com/blog/llm-routing-cost-quality-aware-model-selection
   - Каскады и confidence-эскалация: https://tianpan.co/blog/2025/11/03/llm-routing-model-cascades
   - Инженерный гид 2026 (savings matrix, silent quality tax): https://www.digitalapplied.com/blog/llm-model-routing-2026-cost-quality-optimization-engineering-guide
   Дополнить минимум 3 своими: FrugalGPT (arXiv), LiteLLM router docs, OpenRouter
   auto-router, vLLM semantic router, NotDiamond/Martian — что найдётся живым поиском.
   Темы обязательны: verifier drift / эскалация как живая стоимость; измерение качества
   (offline evals, LLM-judge, A/B против бизнес-метрик); feature-flag rollout малой долей;
   cost attribution per route до инвойса; caching-взаимодействие роутинга.
2. **«Не применять у нас» (≥3)** с причиной от ограничений программы: пер-сообщенческое
   переключение в живой сессии (ломает prompt cache); embedding-роутер без измеренной
   пользы (у нас caller сам маркирует task_type); тихий fallback (запрещён владельцем).
3. **Маппинг на флот**: короткая таблица «паттерн → как ложится на канон-инварианты №1–10 из PROGRAM.md».

## Acceptance (измеримое)

- RESEARCH.md существует по точному пути; ≥8 паттернов, у КАЖДОГО число и URL; ≥3
  анти-паттерна; таблица маппинга присутствует; ≤500 строк.
- Ни одного числа без URL (галлюцинации недопустимы: профиль research = kimi, ставка на
  grounded-citations — каждое число проверяемо по ссылке).
- Пост-аудит company: выборочная проверка 3 URL на соответствие чисел.

## Запрещено

- Любые изменения конфигов/канбана/профилей; создание аккаунтов; платные API; live
  inference-пробы. Только web_search/web_extract и запись ОДНОГО файла RESEARCH.md.
- Не открывать .env*/auth.json. Не трогать чужие доски. Не выдумывать числа.

## Cost/kill/rollback

Cost: токены research-профиля (DashScope, операционка). Kill: досье противоречит канону
или числа не подтверждаются по URL → переделка карты, не активация. Rollback: файл
удаляется/заменяется, влияния на живые системы ноль.
