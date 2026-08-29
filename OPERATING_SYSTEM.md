# Company Operating System

## Единица работы

Kanban task с одним владельцем, явным deliverable, acceptance criteria, зависимостями и evidence. Чат не является реестром задач.

## Цикл

1. **Orient** — прочитать `CHARTER.md`, `STATE.md`, релевантные decisions и Kanban context.
2. **Decide** — выбрать одно измеримое следующее действие; не создавать работу без связи с gate/метрикой.
3. **Squad** — назначить 2–5 ролей; один owner, остальные дают отдельные artifacts/review.
4. **Execute** — исследование, код, main merge, deploy, publishing и эксперименты автономны после role/evidence gates и внутри финансового мандата `APPROVALS.md`.
5. **Verify** — независимая проверка фактов, тестов, diff и claims; слова исполнителя не evidence.
6. **Handoff** — результат, пути/URL/SHA/exit codes, риски, решение и одна следующая задача фиксируются в Kanban.
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
- Ежедневная routine (`company-daily-ops`, 09:00): triage blocked/ready, approvals, stale Next Action, portfolio WIP.
- Еженедельная routine (`company-weekly-review`, пн 10:00): portfolio review, метрики, GO/NO-GO, риски и 1–3 приоритета.
- Никаких busy loops и циклов каждые 30 секунд.

## Флот (финальный ростер)

- Единый универсальный состав: `company`, `tech`, `product`, `design`, `ux`, `qa`, `sales`, `finance`, `research`, `operations`.
- `company` выбирает lead и squad 2–5 ролей; Kanban dispatcher запускает назначенного owner.
- Проектный контекст приходит из board/project metadata и каноничных правил соответствующего repo. Для `rr-team` автоматически применяется общий `rr-project` guidance; отдельных RR-ролей нет.
- Профили `rr-*` заморожены как rollback-контур на 7 дней после cutover, не получают новые assignments/routines и не входят в активный roster.
- SEO Utility Site зарегистрирован как отдельный продукт на board `seo-site`; существующие проекты доната и консоли пока не зарегистрированы в портфеле и автономно не управляются.
