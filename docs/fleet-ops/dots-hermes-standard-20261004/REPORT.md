# Dots → существующий workflow Hermes: сравнение и стандарт совместимости

**Статус: ЗАВЕРШЕНО И ПРИНЯТО (2026-10-04).** Сравнение 17 механик принято независимо (QA run2319, typed PASS; исправленный receipt QA-CANDIDATE-FIXED.json, consumer-приёмка 8/8), company GO exact-head выдан (COMPANY-GO.md), применение выполнено operations run2320 (12/12 целей, APPLY-VERIFY 98/98), финальная приёмка установки — независимый QA run2321 (typed PASS, батарея 286/286, loader-probe 12/12, линии author/issuer/reviewer не пересекаются), company read-only readback живых целей 12/12 (NATIVE-FINAL-READBACK.json). Итоговая приёмка: FINAL-ACCEPTANCE.md, COMPANY-SOURCE-ACCEPTANCE.json. История промежуточных hold/defect этапов сохранена в тех же артефактах.

## Что изменено в подходе

- Сопоставлены **17 механизмов M01–M17**, а не только названия функций: Dots → официальная документация Hermes → установленный/source механизм → действующий fleet-канон → существующий владелец → дубль/конфликт/предел → решение. Полная матрица — [COMPANY-MATRIX.md](COMPANY-MATRIX.md).
- Самостоятельный шаблон ответственности из первого переноса заменяется **адаптером к действующим правилам**, а не вторым workflow. Долгоживущая продуктовая ответственность и конечная исполняемая карта разведены; отдельная schema, очередь, scheduler, координатор, память или approval-процесс не добавляются.
- Канонические процедуры остаются у существующих владельцев. Приоритет — текущие owner-правила, native schema и Fleet Policy; внешний материал — данные для сравнения, не новые разрешения.
- В существующий **fleet-skills-rollout** активного company-профиля уже добавлено правило предварительного поэлементного сравнения механик и безопасной замены старого hook новым. Это процедурная запись в текущем workflow, не разрешение синхронизировать чужие корни.
- Для 12 ранее разрешённых целей подготовлена замена только прежней reference и её собственного hook; имя entrypoint сохранено. Оригинальные ревизии корней и остальные Markdown-файлы сохраняются. Полная синхронизация деревьев, новые модели, config, cron, контроллеры, аккаунты, подписки и бизнес-действия вне scope.

## Проверяемое evidence

- SOURCE subject: [SUBJECT.json](SUBJECT.json), SHA256 `2fedef53211adc07445caee7d4d3ef3cac4df5e7544508ca35a26e040774600e`; 6 frozen members. Это документный head, не Git/live-runtime HEAD.
- Baseline: 26 локальных source inputs, 12 публичных Hermes-статей (raw + text), 12 installed-doc snapshots, 12 target preimages; документация и наблюдаемая runtime-работа не смешиваются.
- Read-only dry-run: **134/134** фактических байтовых/frontmatter/diff checks; **6/6** unit tests чистого helper, exit 0. [DRY-RUN.json](DRY-RUN.json). Это НЕ смысловой PASS, НЕ подтверждение регистрации loader во всех профилях, НЕ проверка будущего поведения модели.
- Независимый QA первоначального source этапа реально работал на **glm-5.3 / zai**: 58 main API calls, task/session-bound natural stamps; preliminary prose «30/30» не используется. Genuine частичные checker/output сохранены в [PRESERVED-QA-2318.json](PRESERVED-QA-2318.json) и `preserved-qa2318/`. Это main lineage, не недоказанная полная auxiliary-chain.

## История незавершённости и её закрытие (сохранена, не подменена)

- Первая попытка QA (run2318) завершилась WITHHELD после отклонённого optional content-search; фаза была переформулирована без discovery, частичные результаты сохранены (PRESERVED-QA-2318.json).
- Run2319 дал typed PASS, но оригинальный машиночитаемый receipt QA-CANDIDATE.json оказался непотребляемым из-за дублей ключей (доказано QA2319-CONSUMER-CHECK.json / CONSUMER-DEFECT-ANALYSIS.json). Компания не переписывала артефакты ревьюера: исправление исполнено независимой qa-картой t_29903deb (run44) как QA-CANDIDATE-FIXED.json, оригинал сохранён.
- Apply-карта t_63f62c17 удерживалась до потребляемого receipt и company exact-head GO (COMPANY-GO.md); затем operations выполнил apply (run2320), а независимая QA-линия приняла установку (run2321, FINAL-QA typed PASS). Все этапы и отказы сохранены в нативной истории карт.

## Финансовый scope

Scope — внутренний fleet-ops методический разбор и normalization 2026-10-04 до фактического конца QA/apply; source — native runs, manifests и natural stamps, финансовый ledger не измерялся. Confirmed revenue, refunds, incremental paid costs, new commitments и estimated usage cost — `null` с причиной отсутствия соответствующего измерения. Новая платная операция не предусмотрена; это не утверждение о нулевой стоимости inference и не заявление экономии.
