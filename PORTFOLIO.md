# Portfolio Registry

## Политика регистрации

Автономно управляются только проекты, явно внесённые сюда. Самостоятельный продукт/venture регистрируется при наличии git repo, accountable owner и измеримой primary metric; затем получает Hermes Project, отдельную Kanban-доску и thin project skill.

Board taxonomy: `portfolio` — стратегия/капитал/инкубация; отдельная board на зарегистрированный продукт; `fleet-ops` — общие capabilities/accounts/infra; `general` — разовые непроектные задачи.

## Активные проекты

| Проект | Путь | Hermes Project | Kanban | Фаза | Владелец | Следующий gate |
|---|---|---|---|---|---|---|
| Recruiter Radar | `C:/Users/max/Desktop/all/recruiter-radar` | `project` (радар) | `rr-team` | Launch readiness | `company` | Универсальный squad назначается по task type; закрыть backlog и launch-гейты; рутинные merge/deploy автономны после VDS snapshot+backup и остальных evidence-гейтов из `APPROVALS.md` |
| Venture Lab | `C:/Users/max/Desktop/all/ventures/venture-lab` | `venture-lab` | `venture-lab` | Discovery | `company` | Выбрать один venture через evidence + GO/NO-GO |
| SEO Utility Site | `C:/Users/max/Desktop/all/mvp-peni-site` | `seo-site` | `seo-site` | Pre-launch / local MVP | `company` | Снять source-integrity blocker и получить независимый QA; публикация до этого запрещена, затем включить измерение |

## Primary metrics

- Recruiter Radar — `accepted_evidence_backed_leads_28d`.
- Venture Lab — `evidence_backed_go_no_go_decisions_28d`.
- SEO Utility Site — `successful_organic_calculations_28d`.

## Portfolio queue

- Одновременно допускается **ровно один** новый venture в активной валидации/строительстве.
- Новая идея сначала попадает на `portfolio` board как hypothesis card.
- После GO профиль `company` может автоматически создать локальную папку, git-репозиторий и **private** GitHub repo.
- Каждый новый продукт после GO получает собственные Hermes Project + Kanban board и строки в этом реестре.

## Portfolio health

- Максимум 5 одновременно работающих Kanban workers.
- Squad на задачу: 2–5 необходимых ролей, не весь флот.
- Закрытая задача обязана иметь проверяемый artifact/evidence либо честный NO-GO.
- Revenue record и продажа Recruiter Radar заблокированы до: бэкапы, live-proof, lineage/replay, 7 дней чистого Clock.
