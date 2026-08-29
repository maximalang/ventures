# Universal Fleet Migration

## Scope

Immediate cutover from all actual `rr-*` profile directories to the ten-role universal roster. Old profile directories remain present as a frozen rollback contour for at least seven days; no destructive deletion is performed.

## Profile mapping

| Old profile | Universal recipients | Migrated responsibility |
|---|---|---|
| `rr-support` | `company`, `qa`, `tech` | coordination, acceptance, engineering routing |
| `rr-backend` | `tech`, `operations`, `qa` | application/data engineering, runtime operations, DB acceptance |
| `rr-frontend` | `tech`, `design`, `ux`, `qa` | frontend implementation, design, conversion UX, browser QA |
| `rr-ops` | `operations` | VDS, CI/CD, backups, monitoring and rollback |
| `rr-critic` | `qa`, `company` | independent adversarial review and high-cost decision escalation |
| `rr-mkt-lead` | `product`, `sales`, `company` | GTM priority, pipeline and portfolio decision |
| `rr-mkt-content` | `product`, `sales` | content planning and conversion copy |
| `rr-mkt-seo` | `research`, `qa` | competitive monitoring and SEO audit |
| `rr-mkt-smm` | `sales`, `product` | channel strategy; publishing remains approval-gated |
| `rr-pool` | none | infrastructure-only pool; never an owner/squad role |

## Durable-data decisions

- Universal SOULs keep role-agnostic rules and now explicitly require task type plus automatic policy enforcement.
- RR-specific operational procedure is centralized in `rr-project`; repository details remain in RR `AGENTS.md`/`CLAUDE.md`.
- Stable facts are migrated only after semantic comparison; duplicate repo/branch/evidence rules are not copied.
- Temporary progress, stale PR/SHA/issue IDs and one-shot logs are discarded from durable memory.
- Safe archives contain only SOUL, `profile.yaml`, Markdown memories and skill files. `.env*`, `auth.json`, credentials, sessions, dumps and request dumps are excluded by construction.

## Cron plan

| Source | Target | Decision |
|---|---|---|
| `rr-ops` `rr-ops VDS zombie cleanup gate` | `operations` | migrate script/job, then pause source |
| `rr-mkt-seo` competitor digest | `research` | migrate monitor script/skill/job, then pause source |
| `rr-mkt-seo` monthly SEO audit | `qa` | recreate with RR workdir and required skills, then pause source |
| `rr-mkt-content` weekly ping | `product` | recreate only if current prompt is still useful; otherwise retire with reason |

## Cutover/rollback

`scripts/fleet_migration.py snapshot` creates sanitized ZIP archives plus SHA-256 manifest and captures active assignments/routing/cron evidence. `cutover --dry-run` and `rollback --dry-run` are non-mutating checks. Real cutover uses official `hermes kanban reassign/comment` and `hermes config set`; rollback replays the captured old owners and routing. Old cron is never re-enabled by rollback.
