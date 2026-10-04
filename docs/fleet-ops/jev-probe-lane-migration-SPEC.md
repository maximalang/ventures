# SPEC (rev.2 26.09): jev-access-probe — верификация устойчивости fleet-Edge lane

Дата: 26.09.2026. Board: fleet-ops, карта t_2899e1ed, assignee operations. Тип: ops. Бюджет: 0 ₽, без новых аккаунтов.
Rev.2: базовая миграция УЖЕ выполнена company 26.09 — скоуп карты сужен до верификации и hardening. Миграцию не повторять.

## Контекст (инцидент 24–26.09, расследован company)
- Сторож a873ef92862c лежал ~2 суток (fail_streak=25). Причины: (1) venv browser-use runner'а сломался в nightly-миграции python (самовосстановился, импорты проверены); (2) runner без пина падал в fallback «найди/подними Chrome владельца» → DevToolsActivePort fatal.
- Канон флота (fleet-browser-routing): headless Edge CDP 9222 (Fleet-Browser). Chrome — не базовый браузер; его использование было багом fallback-пути runner'а, а не проектным решением.
- Патч company 26.09 в scripts/jev_access_probe.py: `_lane_env()` пиннет `BU_CDP_WS` на ws fleet Edge (из /json/version); при 9222 down — одна попытка self-heal идемпотентным лаунчером `Desktop/Fleet-Browser/start-fleet-browser.cmd`, затем outcome=error stage=lane_down. Chrome-фолбэк исключён (runner не запускается без lane). `_REASONS` дополнен lane_down. Проверено: py_compile OK, `_lane_env()` резолвит ws.

## Скоуп карты (верификация + hardening, миграцию НЕ повторять)
1. Подтвердить 3 последовательных cron-прогона сторожа с валидным исходом (full/keyed/loggedin — любой не-error): evidence = строки scripts/jev_access_probe.state.json (last_probe, last_outcome, fail_streak) с timestamp'ами. Ручные пробы бизнес-логики ЗАПРЕЩЕНЫ (каждая = OTP-письмо); читать только state-файл и tmp/bu-typesafe.log.
2. Тест restart-устойчивости БЕЗ убийства боевого fleet Edge: сухой прогон `_lane_env()` (exec определений до `def main`) — при недоступном 9222 должен вернуть None без запуска browser-use. Недоступность имитировать временным неверным портом в ТЕСТОВОЙ копии скрипта, не в боевом.
3. Код-ревью пути lane_down → notify()/owner_inbox (info-уровень через существующую логику 3-сбоев-подряд); без живой отправки владельцу.
4. Обновить ACCESS.md в capabilities/jev: lane fleet Edge 9222 + BU_CDP_WS-пин + поведение lane_down (2–4 строки фактов).
5. Outcome-комментарий на карте: evidence по пп.1–4 + финансовый scope (0 ₽, incremental null).

## Запрещено
- Ручные пробы вне cron (каждая проба = OTP-письмо).
- Печать ключа/куков/секретов; чтение .env*.
- Изменение частоты cron и контрактa исходов без записи в outcome.
- Chrome владельца с флагом --remote-debugging-port без явного ГО владельца (security posture).

## Acceptance
- 3× валидный исход подряд в state-файле (last_outcome ≠ error), fail_streak=0.
- Сухой прогон: 9222 недоступен → `_lane_env()`=None, browser-use не запускается (Chrome-фолбэк невозможен).
- ACCESS.md обновлён; outcome-комментарий с evidence по пп.1–4 скоупа на карте.
