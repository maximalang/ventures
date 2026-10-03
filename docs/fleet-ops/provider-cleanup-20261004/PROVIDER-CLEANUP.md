# PROVIDER-CLEANUP-20261004: чистка реестра провайдеров (только рабочие)

Основание: поручение владельца 04.10 — «использовать только рабочие провайдеры,
провести чистку добавленных и удалить нерабочие; ключи добавлялись для рабочих
провайдеров, просто так не удалять». Метод: нуль-токенные каталожные пробы
(канон fleet-doctrine), телеметрия 14 дней (session_model_usage), официальный
оракул `hermes auth status`. Инференс-пробы не запускались.

## Вердикты проб (04.10, read-only)

| Провайдер | Проба/свидетельство | Вердикт |
|---|---|---|
| custom (DashScope relay) | каталог 200; 51k вызовов/14д | РАБОЧИЙ — ядро |
| zai | 10.2k вызовов/14д (glm-5.3, flash) | РАБОЧИЙ |
| openai-codex | 2 OAuth; 7.9k вызовов/14д (sol 6.1/6.0) | РАБОЧИЙ |
| groq (root) | каталог 200, ключ set | РАБОЧИЙ (0 вызовов — неиспользуемый) |
| mistral (root) | каталог 200, ключ set | РАБОЧИЙ (0 вызовов) |
| cloudflare (root) | каталог 200 (ai/models/search), ключ set | РАБОЧИЙ (0 вызовов) |
| opencode-zen | каталог 200 — эндпоинт ВОССТАЛ (был мёртв 30.08) | ЖИВ, не проверен инференсом |
| copilot / kilocode / ollama-cloud | logged in (хранимые креды), 0 вызовов/14д | ОСТАВЛЕНЫ (ключи не удалять просто так — владелец) |
| openrouter | logged out; RU-биллинг закрыт с 11.05; free-вызовы прекратились 01.10 | НЕРАБОЧИЙ — удалён |
| alibaba×6 / dashscope-cn / dashscope-coding-cn | logged out (env-источник пуст), 0 вызовов; алиасы уже подавлялись с 31.08 | НЕРАБОЧИЕ оболочки |
| novita / novita-ai / novitaai | logged out (env пуст), 0 вызовов | НЕРАБОЧИЕ оболочки |

## Выполнено

1. **Конфиг-хирургия (13 сторов: root + 12 профилей):** удалены 101 строка мёртвых
   ссылок openrouter — пул-стратегия, providers.openrouter, auxiliary.openrouter_model,
   image_gen (recraft через openrouter — мёртв), MoA reference-записи deepseek-v4-pro;
   агрегатор MoA в root перенаправлен openrouter/claude-opus-4.8 → openai-codex/gpt-6.1-sol
   (канон компании). Метод: line-surgery → .tmp → yaml-валидация + инварианты
   (model.default/provider, aux-слоты) → os.replace; CRLF сохранён.
2. **`hermes auth remove` × 12:** alibaba, alibaba-cloud-cn, alibaba-cn,
   alibaba-coding-cn, alibaba-coding-plan, alibaba-coding-plan-cn, dashscope-cn,
   dashscope-coding-cn, novita, novita-ai, novitaai, openrouter. CLI поставил
   маркеры подавления env-источников (re-seed запрещён) и **очистил значение
   OPENROUTER_API_KEY из runtime .env** — ключ openrouter уничтожен самой командой
   удаления (восстановление = владелец заново создаёт ключ в кабинете OpenRouter;
   RU-биллинг закрыт, годится только free-слой).
3. **Особенность Hermes:** оболочки env-провайдеров в `auth list` самовосстанавливаются
   встроенным механизмом (новые id) — это штатно: все они в состоянии `logged out`
   (значения нет), для маршрутизации инертны и невыбираемы. Операционно реестр чист:
   выбираемы только живые креды.

## Итоговый реестр (рабочие рельсы)

- Ядро: custom/DashScope (qwen3.8-max, kimi-k3, glm-5.2, qwen-vl-max), zai (glm-5.3),
  openai-codex (gpt-6.1-sol, luna, astra).
- Root-дополнения (живые, неиспользуемые): groq, mistral, cloudflare.
- Спец/неверифицированы инференсом: opencode-zen (каталог жив), copilot, kilocode,
  ollama-cloud — оставлены по правилу владельца «ключи просто так не удалять».
- agentrouter (company config) — сохранён: канон владельца (аудитор = claude-opus-5
  без даунгрейда); премиум-пул пуст, пополнение = владелец.
- image_gen: рабочей рельсы генерации изображений в пуле НЕТ (мёртвый openrouter/recraft
  удалён). Нужна новая рельса — решение владельца.

## Откат

- Конфиги: бэкап `Desktop/all/tools/workspace/config-backups/provider-cleanup-20261003T220715Z/`
  (root-config.yaml + profiles/*.yaml) — копирование обратно.
- Auth-оболочки: не нужны (инертны). openrouter-ключ: только пересоздание владельцем.
- Корневые правки (MoA/image_gen) вступят в силу для gateway после ночного
  рестарта (пайплайн 03:40–05:00); воркер-спавны читают конфиги свежими сразу.
