# Spec: TG-переименование канала Facts — factsfactory_ru → factsfactory

Запрос владельца: 24.09.2026, тред 20 группы «𝗕 🌐 и CX»: «канал https://t.me/factsfactory_ru надо переименовать в просто factsfactory».
Канон: NAMING_APPROVED.md — factsfactory есть УТВЕРЖДЁННЫЙ primary handle бренда Facts (title «Фабрика Фактов»). Это восстановление канона, а не новое имя.

## Цель
Канал Facts, id 4144667917 (сейчас username factsfactory_ru, title «Фабрика Фактов»). Title НЕ менять. Трогать только username ЭТОГО канала; ggrespawn и psychlogist НЕ трогать.

## Вход (секреты не печатать)
- Сессия: C:/Users/max/Desktop/all/tools/capabilities/telegram/session.string + telegram-live-values.json (api_id/api_hash) — НЕ выводить в лог/отчёт.
- Эталонный скрипт-паттерн: capabilities/telegram/rename_canon_t_eee1848b.py (Telethon, CheckUsernameRequest/UpdateUsernameRequest). Написать свой скрипт в capabilities/telegram/ (имя с task-id), НЕ heredoc.
- История: CHANNELS.md (в том же каталоге) — факт 24.09: при прошлом переименовании все candidates были «fragment-purchase или taken», применён суффикс _ru.

## Шаги
1. Telethon-подключение, get_entity по id 4144667917, зафиксировать текущий username.
2. CheckUsernameRequest(channel, "factsfactory") — ЕДИНСТВЕННАЯ авторитетная проверка (HTTP-страница t.me не отличает свободный от fragment-reserved):
   - **Свободен (True)** → UpdateUsernameRequest(channel, "factsfactory") → readback: HTTP t.me/s/factsfactory = 200 с title «Фабрика Фактов» + telethon resolve factsfactory → id 4144667917. Обновить CHANNELS.md (таблица + rename history с датой/задачей). Комментарий-резюме с evidence.
   - **UsernamePurchaseAvailableError (fragment-резерв)** → НЕ покупать, НЕ ретраить. Эскалация владельцу через owner_inbox (key tg-factsfactory-fragment, уровень normal): «handle factsfactory зарезервирован на fragment; выкуп за TON = решение владельца; ссылка https://fragment.com/username/factsfactory». Карточку завершить с честным результатом «эскалировано, переименование невозможно без выкупа».
   - **UsernameOccupiedError** → не ретраить; та же эскалация (key tg-factsfactory-taken) + в отчёте перечислить API-проверенные альтернативы (CheckUsername по: factsfactoryru, factsfactory_ru уже наш). Решение об альтернативе — за владельцем.
3. FloodWaitError на любом шаге → записать retry_at (now + seconds), НЕ спамить; канал за последние сутки уже менял username (restore ggrespawn 10:15) — лимит вероятен. При флоуде: комментарий с retry_at + complete с результатом «отложено до <время>» (или schedule, если доступно).
4. РОВНО одна попытка UpdateUsername за run (лимиты Telegram на смену username).

## Границы
- Публикация контента запрещена; аутрич запрещён; другие каналы/аккаунты не трогать.
- Покупка на fragment (TON/крипто) = owner decision, вне скоупа карты.
- Секреты (session.string, api_hash) не печатать нигде.

## Выход
Обновлённый CHANNELS.md (или эскалация без правок таблицы) + комментарий-резюме: состояние → действие → evidence (readback HTTP/telethon вывод или точная ошибка API). Финансовый scope: paid=0, fragment-выкуп=null (не выполнялся).
