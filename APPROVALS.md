# Approval Policy

## Автономно разрешено

- web/market/user research с источниками;
- планы, specs, документы, локальные artifacts;
- изменения кода в изолированной ветке `codex/*`, тесты, build, review;
- commit и push в `codex/*`;
- после зафиксированного GO: локальная папка, git init и **private GitHub repo**;
- создание/маршрутизация Kanban tasks и read-only проверки состояния.

## Требует решения пользователя

До ответа соответствующая задача должна быть `blocked` с типом `APPROVAL` и не обходиться параллельной задачей.

- production/staging deploy и действия, меняющие внешний runtime;
- публичная публикация, рассылка, пост, реклама или outreach;
- любые расходы, подписки, платёжные настройки и изменение бюджета;
- удаление, irreversible migration, destructive cleanup, rewrite history;
- merge/push в `main` или другую protected branch;
- выдача новых credentials/permissions, изменение security/privacy policy;
- публичность GitHub repo (private → public).

## Формат approval

Профиль `company` пишет в свой Bot Chat:

```text
APPROVAL REQUIRED
Проект/задача: <board + task id + title>
Действие: <точно что будет изменено>
Зачем: <gate/метрика>
Evidence: <URL/SHA/путь/вывод>
Риск: <worst case>
Rollback: <как откатить>
Выбор: APPROVE | REJECT | CHANGE <условие>
```

Approval должен быть привязан к конкретному действию; общее «делай всё» не переносится на будущие действия.
