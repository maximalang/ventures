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
- **Discovery 2:** для #1 — рынок и источники (`research`), пользовательская проблема (`product`), adversarial pre-mortem (`qa`), экономика (`finance`), канал продаж (`sales`) → `GO`, `NO-GO` или `NEEDS-EVIDENCE`.
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

## Адаптивный пул ролей

- Базовый доступный пул: `company`, `tech`, `product`, `design`, `ux`, `qa`, `sales`, `finance`, `research`, `operations`; это не фиксированный состав каждой команды.
- `company` выбирает accountable lead и минимальный squad 2–5 подходящих ролей. Новая специализированная роль или агент допускается только как scoped manifest с owner, TTL, eval, budget и capability references; создание профиля остаётся отдельной операцией под существующими gates.
- Проектный контекст приходит из board/project metadata и каноничных правил соответствующего repo. Для `rr-team` автоматически применяется общий `rr-project` guidance; отдельных RR-ролей нет.
- Профили `rr-*` удалены и не заморожены: они не входят в активный roster и не являются резервным контуром.
- SEO Utility Site зарегистрирован в портфеле на доске `seo-site` с primary metric `successful_organic_calculations_28d`; остальные существующие не-RR проекты (донат, консоль) не зарегистрированы и автономно не управляются.

## Provenance состояния

- Kanban и зарегистрированные Hermes Projects остаются operational truth; JSON manifests из `contracts/adaptive_org/v1/` — декларации, а не authorization, scheduler или новый evidence store.
- Каждый snapshot продукта ссылается на каноничные `source_refs`, фиксирует UTC `observed_at` и срок перепроверки `next_review_at`. Метрика без наблюдения записывается как `null` + `unknown_reason`, а не как ноль или оценка.
- `STATE.md` — человекочитаемая проекция. Каждое изменение phase/gate/metric должно сохранять ссылку на Kanban task, decision или измерение, из которого оно получено.
