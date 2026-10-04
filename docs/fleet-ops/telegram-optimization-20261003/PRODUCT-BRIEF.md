# Telegram: качество без лишнего контекста

Source-only brief · t_6282d6b9 · owner результата: company; product ведёт гипотезу.
Anchor: существующий профиль company и DECISION-AND-CONTRACT.md [1]. Не установка.

## Страница 1 — пользователь, маршруты, ответы

Job владельца: быстро понять результат или риск и продолжить дело в своём топике, не теряя цель, источники, вложения и уточнения. Риск гипотезы: сокращение текста может скрыть незавершённость или ухудшить продолжение работы. Интервью и эффект после изменения не измерены.

Evidence [1–2]: в наблюдаемые 23,515 ч медиана полного входа Qwen — 316 154, Sol — 164 533 токена; медиана некэшированного входа при известном кэше — 1 842,5 / 3 115. Отдельный семидневный аудит: skill_view вернул 6 816 429 уникальных символов. Это не атрибуция повторного входа и не счёт.

### Маршрутизация — без новой топологии

| Вход | Ответ / guard |
|---|---|
| Owner DM: root и существующие топики | Тот же проверенный chat/thread; топики изолированы. |
| Forum -1004426332349: 1 и project-топики | Диалог в исходном thread; не переносить контекст соседей. |
| Forum: 281 | Уведомления сюда; прямой вопрос не игнорировать, не запускать чужую работу. |
| Часовой дайджест | Существующая доставка, даже пустая; не заменять тишиной. |
| Инцидент / busy-steering / вложение | Сохранить адрес, важный алерт, подтверждение уточнения и связанный файл. |

Topic ID брать из текущего разрешённого readback, не из имени/памяти. Объединять только последовательные сообщения и подписи в одной проверенной route; новых настроек batching не вводить без consumer evidence [3].

### Пять адаптивных шаблонов — выбрать, не заполнить все

T1 · Короткий вопрос: «[Прямой ответ]. [Нужная оговорка]». Обычно 1–3 предложения.

T2 · Итог работы: «[Результат]. Проверено: [существенный факт]. [Оставшийся риск]. Подробности — [файл]». Обычно до 6 коротких смысловых строк; ненужное убрать. Для долгой работы: одно короткое подтверждение, затем только значимый этап и проверенный итог.

T3 · Сбой: «[Что не завершено и чем это грозит]. Подтверждено: [последний успешный факт]. Далее: [безопасный шаг / ответственный]». Не называть ошибку успехом и не скрывать её за отключёнными tool-пузырьками.

T4 · Решение владельца: «Милорд, [что требует именно вашей capability/печати и почему]. [Один естественный вопрос с понятным последствием выбора]?» Например: «Разрешаете открыть окно для ручного входа?» Не просить approval для routine work, пароль или код в чате.

T5 · Подробности по запросу: «[Ответ на уточнение]. [Нужные основания и неопределённость]. Полный разбор — [файл]». Явный запрос на полноту важнее лимита строк. Чат — чистый Markdown, детали — читаемый артефакт; технические термины сохраняются. Стиль замка/милорда — логично, без декора; JSON, служебные IDs и gate-маркеры владельцу не показывать [4].

<!-- PAGE BREAK -->

## Страница 2 — дельта, эксперимент, приёмка

### Точная дельта против текущего поведения

SOUL company L62, L68–72 уже требует краткости, результата первым, стиля и деталей в артефакте: НЕ дописывать дубли в SOUL и не вводить обязательный форматный skill. Новое здесь — проверяемые route/exception fixtures и необязательный справочник выбора T1–T5 для hands packet.

Display уже группирует tool-progress, не показывает previews/reasoning и сохраняет warnings/steering. Кандидат tool_progress=off уменьшает визуальный шум, НЕ токены. Кандидат compression.threshold_tokens=128000 — триггер, НЕ жёсткий потолок API-входа; это отдельный native-пакет на весь company, включая Desktop/cron [1].

Реальный новый рычаг hands: укоротить только company hermes-agent и fleet-token-economy, перенести глубину в адресные refs [5]. Сохранить имена/frontmatter-триггеры, все уникальные процедуры, cache/safety/owner invariants и существующие ссылки. Цель: ≥60% combined hub-character reduction; исходные hubs — 33 078 символов, не токенов. Нужны исчерпывающая карта переноса, hash каждого файла, разрешение refs, selective-retrieval тесты и rollback к исходным bytes. Исправить устаревшие blanket-советы о reset и «только новые sessions»: на host есть reset-policy plugin, hot reload проверять по installed consumer [1,3]. Это не разрешение reset/restart.

### Минимальный тест и stop rule

Сначала offline packet + независимый QA. Затем, только после bounded application, естественные сопоставимые Telegram-вызовы: ≥10 на каждый model/provider stratum; меньше — NEEDS-EVIDENCE. Сравнить median/p95 полного входа, cached/uncached отдельно, output/reasoning отдельно, latency, loads/repeats и quality failures; для 24/48 ч использовать сохранённую boundary и существующий аудит, не новый LLM-watcher [2]. Любая потеря цели/источника/steering, route leakage, warning/attachment failure — stop/rollback; отсутствие снижения измеренной метрики — не объявлять оптимизацией. Компания принимает бизнес-вердикт; product рекомендует по evidence.

Текстовый шум = лишние ответы/логи, потенциальный контекст; визуальный = bubbles, не token usage. Стабильный cache-prefix сохранять [6]; cache hit не уменьшает размер запроса до нуля. Символы/байты ≠ токены; usage/quota ≠ invoice. Costs и cash savings неизвестны, не 0.

### 12 acceptance-примеров (offline fixtures, НЕ live proof)

S01 короткий DM-вопрос → T1, ответ без загрузки форматного skill.
S02 долгий итог → T2, краткость + artifact, существенный риск виден.
S03 просьба о полном разборе → T5, полнота не обрезана до 6 строк.
S04 ошибка инструмента → T3, незавершённость/безопасный шаг, warning виден.
S05 owner-only capability → T4, один человеческий вопрос, без IDs/секретов.
S06 два DM-топика → отдельные ответы/контексты, никаких соседних данных.
S07 forum 1/project → исходный thread, не notifications 281.
S08 уведомление в 281 → уведомление; прямой вопрос получает ответ, без чужого dispatch.
S09 пустой часовой digest → доставка сохранена, не silent.
S10 busy-steering → короткое подтверждение, уточнение применено до нового действия.
S11 файл + подпись + повтор update → связаны в route, одна обработка, без потери вложения.
S12 compaction + cache → цель/refs/ограничения и tail сохранены; контекст/cache/cash не смешаны.

Развёрнутые входы, примеры ответов и pass/fail оракулы: SCENARIOS.json; source self-check не заменяет QA или runtime-тесты.

Handoff: tech t_cef261ac → qa t_d5e37e14 → bounded operations/company. Telegram-retirement t_b3e6c428 → t_45c34a6a и network t_930c007a не трогать. No live config/SOUL/skill/cron/model/other-profile writes; no secrets/history reset/paid probe/new watcher. Финансовый scope/period: этот brief; покупок/новых обязательств нет; usage cost/revenue/refunds = null (не атрибутированы).

Источники: [1] evidence-root/DECISION-AND-CONTRACT.md; [2] MEASUREMENT-REVIEW.md, measurement-strata.json; [3] Hermes official configuration + Telegram; [4] company/SOUL.md и fleet-notification-ops/references/tg-message-format.md; [5] Anthropic context engineering; [6] OpenAI prompt caching. Exact delivery hashes — PRODUCT-DELIVERY.json (brief + authored scenarios only; source-input hashing was not part of the requested brief). Official URLs: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/ ; https://hermes-agent.nousresearch.com/docs/user-guide/configuration ; https://platform.openai.com/docs/guides/prompt-caching ; https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents . Evidence-root: C:/Users/max/Desktop/all/ventures/docs/fleet-ops/telegram-optimization-20261003.
