# Runbook: деплой control-plane fleet-policy (operator-only)

Статус: нормативный маршрут деплоя (v1.2.37, карта t_e393b6e8,
RECOVERY-PROGRAM RR-3, правило PROGRAM 1 и 5 от 04.10.2026).

## Роли и контракт

| Роль | Действия | Запрещено |
|---|---|---|
| worker (любой профиль) | правки ИСХОДНИКОВ в repo (ветка → PR → гейты → merge в `codex/company-os`); подготовка bundle (`build_release_bundle` → `verify-bundle`) и runbook-заметок; блокировка карты с `[continues: company]` | любой деплой/правка живого control-plane (`profiles/*/plugins/fleet-policy`, `.state/fleet-policy.db`, живой `config/fleet-policy.yaml`) — deny `policy_control_plane_mutation` / `deploy_external_runtime` by design |
| company (operator-сессия, interactive) | тегирование trunk; запуск `scripts/deploy_policy.sh`; перезапуск gateway-сессий; shadow-наблюдение; откат | деплой нетегированным контентом; правка файлов на месте |
| owner | решение об эскалациях approval_required; слово на нестандартные откаты | — |

Живой control-plane ВСЕГДА соответствует тегу repo. Dirty-дрейф запрещён
(RR-1): любой незакоммиченный дифф живого клона сначала захватывается
в trunk (capture-карта), затем деплой идёт из тега.

## Предусловия деплоя

1. PR слит в `codex/company-os`; CI зелёный на exact head.
2. Версия уникальна (`scripts/check_version_uniqueness.py` — CI-гейт).
3. Тег существует и указывает на trunk-коммит релиза:
   `git -C <repo> rev-list -n1 refs/tags/<tag>^{commit}`.
4. Гейты деплоя заармлены по контракту карты активации
   (ci/review от QA, backup/rollback от operations, GO-якорь company —
   только binding-строкой правомочного автора на карте).

## Команда

```bash
bash scripts/deploy_policy.sh \
  --repo  C:/Users/max/Desktop/all/ventures \
  --tag   v1.2.37
```

Флаги: `--plugin-dir` (по умолчанию
`%LOCALAPPDATA%/hermes/profiles/company/plugins/fleet-policy` — корень
симлинк-фермы), `--profiles-root`, `--skip-tests` (только повторный деплой
уже доказанного тега), `--dry-run` (все проверки, без изменений),
`--force` (осознанный деплой поверх дрейфа — требует предварительного
capture).

Что делает скрипт (по шагам):

1. резолвит тег в `--repo`, печатает SHA и версию `plugin.yaml` тега;
2. поднимает detached-worktree тега и прогоняет в нём полный тест-сьют
   + `build-bundle` + `verify-bundle` (доказательство тега);
3. fail-closed проверки живого клона: должен быть git-клоном; грязный
   tracked-tree деплоится только если его СОДЕРЖИМОЕ идентично тегу
   (кейс RR-1 «capture уже в repo») или с `--force`;
4. `git fetch <repo> tag <tag>` + `git checkout --detach <tag-sha>` в
   живом клоне; `.state/` gitignored — event-store не трогается;
5. аудит `profiles/*/plugins/fleet-policy`: симлинки на company-клон —
   ок; `REAL_DIR_NEEDS_MANUAL_SYNC` — отдельная копия, требует ручной
   синхронизации (скрипт её НЕ трогает);
6. печатает JSON-манифест: `tag_sha`, `live_prev_sha`, `live_new_sha`,
   `drift`, `bundle_verified`, команда rollback.

## Пост-деплой

1. Перезапустить/обновить gateway-сессии профилей — pre-tool hooks
   перечитываются при старте сессии.
2. Версионная проба: `fleet-policy --version` (или
   `python -m fleet_policy.cli show --config`) — версия == тегу.
3. Shadow-окно (по контракту карты активации): наблюдать deny-события
   `fleet-policy events --since <дата> --decision deny` и
   `budget_or_loop_stop`; аномалия → откат.
4. Манифест деплоя (JSON из stdout) приложить комментарием к карте
   активации — это evidence деплоя.

## Откат

```bash
git -C "%LOCALAPPDATA%/hermes/profiles/company/plugins/fleet-policy" checkout --detach <live_prev_sha>
```

`live_prev_sha` — в манифесте деплоя. После отката: перезапуск
gateway-сессий + версионная проба. Откат — действие operations/tech
по гейту rollback карты активации (авторы гейта: tech, operations).

## Read-only диагностика для воркеров (без heredoc-проб)

Санкционированный маршрут (все команды read-only, mode=ro, без migrate):

```bash
fleet-policy --root <repo> status
fleet-policy --root <ventures-root> events --task <t_id> --since 2026-10-04 --decision deny
fleet-policy --root <ventures-root> task --id <t_id>
fleet-policy --root <repo> show --config
```

или `python -m fleet_policy.cli <та же форма>` (в repo: `uv run --frozen`).
Heredoc/многострочные sqlite-пробы остаются fail-closed — это дизайн,
а не баг; deny-сообщение указывает этот маршрут.
