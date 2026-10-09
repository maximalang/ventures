# Итоговая company-приёмка Dots-методики

**Решение: принято — конечное методическое внедрение в 12/12 рабочих профилей.** Предмет: не облачный сервис OpenAI Dots, не новый runtime/scheduler и не доказанная экономия; это точная reference + загрузочный hook для существующего Hermes-флота.

## Якорь и собственное фактическое чтение

- METHOD-CANDIDATE.md, SHA256 `f2a85ced87b620bf08cdfc2f3de85ce004a2912efded4da85b668148f00dce6f`.
- LOAD-HOOK.md, SHA256 `2e10a1c6153947db1c2f335ea7037fa0522111f5be6ec31d83ebb345b9768ec9`.
- Собственная свежая квитанция company: **FINAL-CONSUMER-CHECK.json**, SHA256 `48738e223db1a7ecaf56bfe32b3125680b26065906be3a6b8dc5a80b74e7e963`; фактический EXIT=0. Это consumer-readback, не независимая QA.
- Повторно проверены 10/10 immutable input_members, SHA256/bytes всех 13 публичных snapshots, дедупликация 12 точных target paths и фактические after-hashes каждого корня.
- Все 12 references byte-equal candidate; hook ровно один и является точным suffix; root-minus-hook byte-equal своей raw backup; backup SHA256 совпадает с frozen before; свежий корень совпадает с installed after-manifest. Сохранены разные прежние версии корней, полное выравнивание skills не проводилось.
- Профили: company, research, product, operations, qa, tech, finance, sales, design, ux, video-director, video-editor. Default-profile не является целью. Регистрация/loader enabled подтверждены независимой QA; natural skill_view действительно состоялся в operations, QA и текущей company-сессии.

## Независимая цепочка, не собственные печати QA

1. Research source audit t_f41c3c15: PASS на том же frozen candidate; 8 core Dots + 5 supporting источников. SOURCE-AUDIT.md читается вместе с verified errata: ложные candidate-attributions исходного отчёта не приняты.
2. Operations t_87ddea42: фактическая установка, after-manifest и raw backups; текущие 12 целей прочитаны ещё раз, не приняты по одному статусу DONE.
3. Research t_bf24d51d: EVIDENCE-ERRATA.md сохраняет originals и исправляет 9 перечисленных evidence discrepancies. Две его неподтверждённые исторические формулировки исключены последующей QA.
4. Primary QA t_a3c78661: **PASS Q1–Q10**, 14 semantic scenarios; оригиналы QA.md/QA.json прочитаны, SHA256 совпали с опубликованными native handoff значениями. Реальный machine-readable checker: **23/23 PASS**, не прежняя текстовая цифра 25.
5. Supplemental QA t_a1ec6fed: **PASS исправленной совокупности evidence**, QA-ERRATA.md SHA256 `d245537e339bd6f6d611b01e5a827aa2e5ec0262eba56d885eccbe6c6786ca2c`, проверен по native published hash. Реальный финальный checker: **31/31 PASS**, не первоначальная цифра 29. Подтверждены fresh 12-target readback, исправленные claims и два явных exclusions. Никакой функциональный или integrity FAIL этим не отменён.

Native родители фактически завершены, unsatisfied parents отсутствуют. Подробные актуальные native результаты после финального перехода сохраняются в FINAL-DISPOSITION.json. Company не выдаёт здесь новых QA/finance gates и не переписывает выводы специалистов.

## Исключения и пределы принятия

- Отброшены claims о проверке 10 packet members именно в момент прошлой установки: соответствующей исторической квитанции нет. Приняты реально выполненные проверки точных current bytes.
- Отброшен claim о сравнении прежнего supporting-file inventory с baseline: такого before-inventory baseline не содержит. Приняты inspected allowlisted writes, текущие файлы и сохранность каждого original root, не историческая hash-аттестация всех supporting files.
- Малформированный 62-символьный installer-hash исходной QA не нормализован и не принят за SHA256. Фактически вычисленный hash файла: `f75cd3641b20232a9b4ae55274849f165e1a1e53b6ac920db3aa29294fa0e827`. Originals сохранены; отчётные totals/hashes заменены в итоговом принятии только реально вычисленными фактами.
- Actual serving model/fallback lineage исходных reviewer runs не установлена. Разные роли/сессии обеспечивают разделение авторства, но **не доказывают независимость моделей**. Конфигурационное имя модели не выдаётся за usage evidence.
- Принято: установка, сохранность, доступность загрузки, проверенная методика и review сценариев. Не принято как доказанное: гарантированное поведение будущих агентов, экономический выигрыш, весь host-wide negative или ремонт существующей автокомпании.
- Runtime/config/provider/pools/policy/DB/cron/account/device/payment changes не входят в разрешённую и выполненную цепочку этого внедрения. Это statement о проверенном task scope, не о неизменности всей машины за период.

## Завершение ответственности и сбой автоматической финальной приёмки

Автоматический company-consumer дважды аварийно завершился (runs 2313 и 2315). Native registry остановил его в blocked после двух failures, current_run_id=null, живого claim нет; точные launchers 23692 и 10288 отсутствуют по read-only psutil проверке. Это сохранённый факт сбоя, не successful run. По последней печати run2313 был на compaction; root cause второго сбоя не установлен, warning с незаданными env placeholders не объявляется причиной.

Финальную собственную company-обязанность выполнил активный desktop-сеанс: прочитал реальные targets/вердикты, сформировал этот документ и свежую квитанцию. Живой worker не отбирался; unblock, promotion, restart, поднятие retry-budget, новый supervisor и изменение Hermes не выполнялись. Native completion допускается только обычным разрешённым tool-переходом; actual окончательное состояние — FINAL-DISPOSITION.json. Anti-loop/crash history сохранена.

После принятия этого конечного внедрения не требуется искусственная follow-on карта. Владелец дополнительных действий не должен выполнять. Пользу метода можно наблюдать в следующем **естественном существующем** project handoff; это не невыполненная часть файловой интеграции и не обещание нового платного эксперимента.

## Финансовый scope

Fleet-ops, методическое внедрение; период: начало packet 03.10.2026 → текущая финальная company-приёмка. Source: native task/tool receipts, billing не запрашивался. Confirmed revenue=null; refunds=null; incremental paid costs=null; estimated usage cost=null — не измерены. New paid commitments=0: новых заказов/подписок цепочка не оформляла. Нулевой commitments не означает нулевой inference cost. Экономия ₽ не заявлена.
