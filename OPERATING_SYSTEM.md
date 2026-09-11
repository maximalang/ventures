# Company Operating System

## Единица работы

Kanban task с одним владельцем, явным deliverable, acceptance criteria, зависимостями и evidence. Чат не является реестром задач.

## Цикл

1. **Orient** — прочитать `CHARTER.md`, `STATE.md`, релевантные decisions и Kanban context.
2. **Decide** — выбрать одно измеримое следующее действие; не создавать работу без связи с gate/метрикой. `company` владеет бизнес-вердиктом и капиталом; назначенный `product` lead ведёт пользовательскую гипотезу до рекомендации по проверенным фактам; `qa` и `finance` дают независимые verdicts и не подменяются `company` или `product`.
3. **Squad** — назначить 2–5 ролей; один owner, остальные дают отдельные artifacts/review.
4. **Execute** — исследование, код, main merge, deploy, publishing и эксперименты автономны после role/evidence gates и внутри финансового мандата `APPROVALS.md`.
5. **Verify** — независимая проверка фактов, тестов, diff и claims; слова исполнителя не evidence.
6. **Handoff** — в Kanban фиксируются изменение результата, факт против baseline, источник, неизвестное, одна следующая задача с owner/check_at и решение владельца фазы. Деньги всегда имеют scope/period/source; неизвестное записывается как `null` с причиной, не как 0. Фаза завершается native summary + metadata (`outcome_ref`, `phase_result`, `evidence_refs`, `observation_status`, `next_action`, `next_owner`, `check_at`); это соглашение существующих полей, не новая schema. Автор закрывает свой deliverable и освобождает pre-created review children, не удерживая фазу открытой до бизнес-исхода.
7. **State update** — обновлять `STATE.md` только при смене фазы, gate, решения или измеримого состояния.

## Forced convergence для нового venture

- **Discovery 1:** независимые идеи/сигналы → shortlist не более 3.
- **Discovery 2:** для #1 — рынок и источники (`research`), пользовательская проблема (`product`), pre-mortem (`critic`), экономика (`finance`), канал продаж (`sales`) → `GO`, `NO-GO` или `NEEDS-EVIDENCE`.
- **Build 1+:** после GO каждая итерация производит артефакт: repo, код, тест, лендинг, интервью-план или измеримый эксперимент. Чистая дискуссия запрещена.
- Один и тот же `Next Action` не переносится более двух циклов: на третьем — уменьшить scope, сменить подход или заблокировать с конкретным запросом.
- `NO-GO` — допустимый успешный результат при наличии evidence.

## Review pipeline

- Автор не принимает собственную работу.
- `qa` — независимый adversarial review и воспроизводимая проверка поведения/acceptance criteria; автор не принимает собственную работу.
- `finance` проверяет pricing, unit economics, бюджетные assumptions; не тратит деньги.
- Для дорогих portfolio/architecture/launch решений `company` запрашивает явный GPT cross-check; это не автоматический fallback.

## Ритм

- Event-driven dispatcher двигает готовые Kanban tasks.
- Ежедневная routine (`company-daily-ops`, 09:00): прочитать активную ставку, свежий evidence, непосредственный blocker и доступный бюджет; выбрать одно разрешённое действие и проверить точную карточку после перехода. Допустимы только ACTION, проверяемое WAIT с будущим `check_at`/условием пробуждения или обоснованный BLOCKED с конкретной причиной и owner. Здоровую running-задачу не трогать; неизменившийся deny не повторять и не обходить.
- После двух последовательных циклов без нового evidence или движения `company` обязана уменьшить scope, сменить разрешённый метод, остановить ставку либо назначить конкретное устранение причины; перенос той же формулировки не считается действием.
- Еженедельная routine (`company-weekly-review`, пн 10:00): сравнить прогноз с фактом, отдельно показать продуктовый outcome, scoped деньги и неизвестные суммы, затем выбрать continue/iterate/kill и зафиксировать один следующий измеримый task ref с owner/check_at. `NO-GO` и `NEEDS-EVIDENCE` допустимы, но не являются доказательством спроса или выручки.
- Никаких busy loops и циклов каждые 30 секунд.

## Флот (финальный ростер)

- Единый универсальный состав: `company`, `tech`, `product`, `design`, `ux`, `qa`, `sales`, `finance`, `research`, `operations`.
- `company` выбирает lead и squad 2–5 ролей; Kanban dispatcher запускает назначенного owner.
- Проектный контекст приходит из board/project metadata и каноничных правил соответствующего repo. Для `rr-team` автоматически применяется общий `rr-project` guidance; отдельных RR-ролей нет.
- Профили `rr-*` удалены и не заморожены: они не входят в активный roster и не являются резервным контуром.
- SEO Utility Site зарегистрирован в портфеле на доске `seo-site` с primary metric `successful_organic_calculations_28d`; остальные существующие не-RR проекты (донат, консоль) не зарегистрированы и автономно не управляются.
