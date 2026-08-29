# Portfolio Registry

## Политика регистрации

Автономно управляются только проекты, явно внесённые сюда. Самостоятельный продукт/venture регистрируется при наличии git repo, accountable owner и измеримой primary metric; затем получает Hermes Project, отдельную Kanban-доску и thin project skill.

Board taxonomy: `portfolio` — стратегия/капитал/инкубация; отдельная board на зарегистрированный продукт; `fleet-ops` — общие capabilities/accounts/infra; `general` — разовые непроектные задачи.

## Активные проекты

| Проект | Путь | Hermes Project | Kanban | Фаза | Владелец | Следующий gate |
|---|---|---|---|---|---|---|
| Recruiter Radar | `C:/Users/max/Desktop/all/recruiter-radar` | `project` (радар) | `rr-team` | Launch readiness | `company` | Универсальный squad назначается по task type; закрыть backlog и launch-гейты; deploy только после VDS snapshot+backup и требует approval |
| Venture Lab | `C:/Users/max/Desktop/all/ventures/venture-lab` | `venture-lab` | `venture-lab` | Discovery | `company` | Выбрать один venture через evidence + GO/NO-GO |
| SEO Utility Site | `C:/Users/max/Documents/seo-niche-research/mvp-peni-site` | `seo-site` | `seo-site` | Pre-launch / local MVP | `company` | Исправить source-integrity regression, получить независимый QA и закрыть publication gates перед organic pilot |

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
