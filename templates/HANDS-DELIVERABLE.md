# HANDS-DELIVERABLE — <название поставки>

<!-- Шаблон hands-deliverable (company-os): исполнительская поставка «рук».
     Протокол синтеза: docs/fleet-ops/model-routing-20261003/SYNTHESIS-PROTOCOL.md.
     Каждый агентный бриф несёт официальный паттерн целевой модели (§4). -->

- Исполнитель (owner поставки): <профиль>
- Карта Kanban: <id> (task_type: research|code|review|ops)
- Дата / версия: <дата> / v<n>
- Brain-brief-источник: <ссылка>

## 1. Deliverable и acceptance
<Одна формула результата; критерии приёмки проверяемы (команда/exit-код/SHA/URL).>

## 2. Границы и bans
<Что запрещено; blast radius; rollback-путь; owner-гейты (deploy/spend/legal).>

## 3. Evidence-план
<Какие проверки будут прогнаны и что приложено к handoff: пути/SHA всех
изменённых файлов, команды+exit-коды, скриншоты/логи при необходимости.>

## 4. Паттерн целевой модели (PATTERNS v2 — обязательно)
<!-- Заполнить выводом: python scripts/model_router.py --patterns <model>
     (JSON: patterns_version=v2, rules_sha, 6-строчный блок). На claim штамп
     hook уже несёт блок «PATTERN v2 (<model>):» — спецификация исполнителя
     обязана ему соответствовать (как брифовать / требовать строго). -->
- Целевая модель: <provider/model> (rules_sha <12hex>)
```
<6 строк: как брифовать / требовать строго / страховка / анти-паттерн /
канонические настройки / источники>
```

## 5. Handoff
<Формат: РЕЗУЛЬТАТ → Artifact → Verification → Decision/Risks →
Next owner/APPROVAL. Отчёт — человеческим языком (SYNTHESIS-PROTOCOL.md §6).>
