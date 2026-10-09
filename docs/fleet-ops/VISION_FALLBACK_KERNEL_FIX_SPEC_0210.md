# SPEC: auxiliary vision must honor fallback_chain and never carry model across providers
Дата: 02.10.2026. Автор: company. Anchor: hermes-agent main @ be5e9f72c6 (чистое дерево).
Доска: fleet-ops. Assignee: tech. QA: независимый exact-head review (kernel change).

## Инцидент (evidence)
02.10 09:13 и 09:29 (profiles/company/logs/agent.log):
- `agent.credential_pool: credential pool: no available entries (all exhausted or empty)`
- `resolve_provider_client: openai-codex requested but no Codex OAuth token found`
- `Vision provider openai-codex unavailable, falling back to auto vision backends`
- `Vision auto-detect: using main provider custom (qwen3.8-max)`
- `ERROR tools.vision_tools: 404 The model 'gpt-6.1-sol' does not exist` (request_id fc313059-cbf0-9f97-8b48-e581e9a2b72e) — имя codex-модели уехало на DashScope-эндпоинт.

## Дефекты ядра (agent/auxiliary_client.py)
1. `_resolve_call_client`, vision-ветка (~7286-7291): при client=None для явного провайдера сразу прыгает в auto-route, НЕ consult'я `auxiliary.vision.fallback_chain` — в отличие от не-vision ветки (~7301-7316), которая вызывает `_try_configured_fallback_for_unavailable_client(task, explicit)`.
2. Тот же прыжок передаёт `model=resolved_model` (gpt-6.1-sol — имя чужого провайдера) в `resolve_vision_provider_client(provider="auto", ...)`; `_finalize_vision_client` делает `final_model = resolved_model or default_model` → чужое имя форсится на main provider → 404. Комментарий в не-vision ветке прямо предписывает: "model=None so each provider uses its own default".
3. Побочный: даже при настроенной цепи call-time ladder после 404 не спас (цепь в конфиге компании добавлена в 09:28:36Z, тест 09:29:11 упал тем же 404 без видимой попытки openrouter) — проверить, доходит ли 404 model_not_found до `_ladder_provider_fallback` c task-chain (возможная причина: resolved_provider подменён на 'custom' → is_auto=False → только task chain; либо build openrouter-клиента тихо падает на DEBUG). Воспроизвести и починить/объяснить.

## Требуемое изменение (минимальное)
В vision-ветке `_resolve_call_client` при client is None и явном провайдере:
1. Сначала `_try_configured_fallback_for_unavailable_client(task='vision', explicit)` (+ async-обёртка как в 7311-7314).
2. Только если цепь пуста/исчерпана — auto-route с `model=None`.
Патч ≤ ~15 строк, зеркалит существующий паттерн не-vision ветки.

## Acceptance (evidence)
- Unit-тест(ы) из venv чекаута (`hermes-agent/venv/Scripts/python.exe -m pytest`): (a) явный провайдер недоступен + chain настроена → используется chain-провайдер/модель; (b) chain пуста → auto с model=None (final_model ≠ имя первоначального провайдера); (c) регрессия: доступный явный провайдер → без изменений.
- py_compile + существующие тесты auxiliary/vision не сломаны (прогнать профильные pytest из чекаута).
- Readback диффа в комментарии карты; полный SHA коммита.
- Workflow ядра (hermes-internals): staged .tmp → валидация → os.replace; НЕ коммитить в production main; слой = owner-fork integration branch company/autocompany-integration (remote fork) по канону owner-patches; resident-процессы подхватят после gateway restart (nightly layer apply).

## Запрещено
- Self-approval (review — независимый qa exact-head).
- `hermes update` / апстрим-изменения.
- Inference-пробы на аккаунтах владельца (openai-codex пул) — запрет 09.09; тесты только на моках/локальных.
- Чтение .env*/секретов.

## Контекст временного моста (уже сделано company, НЕ часть карты)
- fallback_chain (openrouter/nemotron-3-nano-omni:free) добавлена в 8 профилей: config-backups/vision-fallback-20261002T062836Z.
- Primary vision во всех 12 профилях временно: custom/qwen-vl-max без reasoning_effort (DashScope 400 на thinking_budget для не-thinking VL): config-backups/vision-bridge-20261002T064528Z + vision-noeffort-20261002T064653Z. Живой тест success 09:47.
- После merge kernel-фикса и восстановления codex-пула: company вернёт primary openai-codex/gpt-6.1-sol (канон 30.09) с рабочей цепью — отдельным решением, НЕ в этой карте.
