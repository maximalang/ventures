# qa-compressor-independence-3009 — отвязка compression-слота профиля qa от модели исполнителя

Owner: company. Бюджет: 0₽, без новых обязательств (kimi-k3 на существующей DashScope-рельсе). task_type: ops. Координационная карта-родитель: t_c9b8f189 (ДПО t2 I1).

## Дефект I1 (evidence — уже разрешённые артефакты, новых сканов НЕ делать)
- QA-карта t_7e298d3e, finding I1 (severity BLOCK, owner company): финальный snapshot 2026-09-30T04:04:47.978755+00:00, файл `boards/general/workspaces/t_7e298d3e/evidence/model_identity_diagnostic.json`: QA-сессия 20260930_060228_432c9e = gpt-6.1-sol/openai-codex 27 calls + **qwen3.8-max/custom 1 call, task=compression** (first_seen=last_seen=1790740513.9075866); author_model_overlap=true; assertion финализатора exit 1.
- Автор фикса (t_0b41da7f run 66, сессия 20260930_050232_a9894a) = qwen3.8-max/custom, 81 вызов. Пересечение полной цепочки runtime+compression = {qwen3.8-max} → модельная независимость QA-вердикта утрачена (VERDICT REVISED: FAIL, durable-комментарий QA от 30.09 07:10 RTZ2).
- Корень: aux-канон 20.09 зафиксировал compression=custom/qwen3.8-max по всему флоту, а дефолтный исполнитель tech — тоже qwen3.8-max. Для профиля qa owner-прецедент 03.09 «gate independence» уже вывел delegation-слот на kimi-k3 (канон 20.09 сохраняет это исключение дословно: «qa→kimi-k3, gate independence preserved»), но compression-слот исключён не был. Дефект структурный: ЛЮБОЙ tech-фикс (qwen) + ЛЮБАЯ автокомпрессия в qa-run = отравление вердикта.

## Решение company (30.09)
Перепин ТОЛЬКО профиля qa: auxiliary.compression → provider `custom`, model `kimi-k3`, reasoning `max`. Обоснование: распространение собственного owner-carve-out 03.09/20.09 (gate independence qa-aux от модели исполнителя) на compression-слот; kimi-k3 = та же модель и та же рельса, что уже одобрена owner'ом для qa-delegation. Остальные профили и остальные ключи qa-конфига НЕ меняются (compression=qwen 20.09 для не-qa профилей остаётся в силе). Owner информируется штатным ежедневным дайджестом; rollback готов до применения.

## Процедура (change control по доктрине, метод 21.09)
1. Backup: скопировать `C:/Users/max/AppData/Local/hermes/profiles/qa/config.yaml` в `%LOCALAPPDATA%/hermes/config-backups/qa-compressor-<UTC-ts>/config.yaml` (создать каталог).
2. Прочитать файл, найти фактический блок compression внутри auxiliary (точные имена ключей определить по месту; ожидаемо provider/model/reasoning). Зафиксировать текущие значения фактически (ожидаемо custom/qwen3.8-max/max; если отличаются — записать как есть и сохранить цель: модель ≠ qwen3.8-max).
3. Правка минимальная, текстовая: записать в `config.yaml.tmp`, валидировать YAML (safe_load + residual-key walk: ВСЕ ключи файла кроме затронутых в compression-блоке побайтово неизменны; snapshot «до/после» ключей main/delegation/vision/прочих aux/fallbacks/retries/pools), и только после полной валидации — os.replace (правило патчеров 11.09).
4. Semantic diff backup↔итог: изменены только строки compression-блока. Diff-файл сохранить в тот же backup-каталог.
5. Валидация конфига штатной командой проверки (config check); если команда недоступна — достаточно валидации п.3 (YAML + residual-key walk), зафиксировать это в отчёте.
6. Readback: перечитать файл; в комментарий карты привести ТОЛЬКО итоговый compression-блок (3–5 строк). Весь файл в комментарий/отчёт НЕ копировать; если в файле встретятся значения, похожие на inline-credential, — не цитировать и не копировать их.
7. Рестарт gateway НЕ требуется: kanban-воркеры читают конфиг профиля при спавне; действенность докажет usage-readback следующего естественного qa-run (карта retest, спека specs/qa-t2-retest-i1.md).

## Запреты
- Любые изменения иных профилей и любых других ключей qa-конфига.
- Чтение .env*, auth/credential-хранилищ, дампов.
- Inference-пробы «для проверки модели» (платные синтетические пробы запрещены); действенность = usage-строки следующего естественного qa-run.
- Обход policy deny: при любом deny — НЕ обходить, park needs_input с точным текстом deny и шагом процедуры.
- Повтор отвергнутых control-plane сканов (сырые скрипты поверх kanban.db и т.п.).

## Acceptance (measurable)
- В `profiles/qa/config.yaml`: compression-слот = provider custom, model kimi-k3, reasoning max.
- Semantic diff = ровно один изменённый блок; backup + diff на диске (абсолютные пути в metadata complete).
- Readback-цитата блока в комментарии карты; config-check (или YAML-валидация + residual-key walk) exit 0.
- Невыполнимость (deny/лок/иное) — честный park needs_input с точной причиной; owner company.

## Rollback
Восстановление config.yaml из backup-каталога (копия → .tmp → валидация → os.replace), readback, комментарий на карте. Триггер: несогласие owner или дефект.
