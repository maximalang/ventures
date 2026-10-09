# ДИРЕКТИВЫ ВЛАДЕЛЬЦА Д0-регистрации (23.09 late) — durable-копия (workspace t_a78264a3 зачищен при archive)

Применяются ко всем per-platform картам цепочки Д0: t_b1ef75d3 (TikTok) → t_59dc700e (Pinterest) → t_92b79401 (YouTube) → t_fa0b8ec3 (Telegram) → t_4ac6890d (VK). Трекер: CHANNELS_WAVE1.md (рядом).

1. **VK — РАЗРЕШЕНО с номером флота +790****6092** (владелец 23.09: «номер у вас должен быть, на него можно сделать вк»). Это НЕ phone-gate-стоп: номер выдан владельцем флоту (тот же, что TG-аккаунт). Порядок: vk.ru → создать аккаунт → ввести +790****6092 → SMS-код. Если код НЕ читается автономно — ОДИН запрос владельцу через owner_inbox (critical, key vk-sms-code) «пришлите код VK с +790****6092» и ждать, НЕ спамить повторными submit (лимит кодов). После входа: оформить 3 сообщества/профиля по брендам (Wardogs/Facts/Psychology), доступы в capabilities/vk/ACCESS.md (SMS-коды не хранить).
2. **TikTok — делать без ожидания.** Блокера по Google-входу нет: сессия maxiduoservice ЖИВА на CDP 9222 и сохраняется в профиле (cookies персистентны) — входить заново каждый раз НЕ надо, просто «Continue with Google» → account chooser → Maxi. Если session-chooser глючит — один раз пройти accounts.google.com на 9222 до залогиненного состояния (readback myaccount.google.com), дальше сессия переживает перезапуски браузера. TikTok×3 по брендам, Pinterest×2 — тот же OAuth-маршрут (или email-signup с кодом из Gmail на 9222).
3. **Donut — резерв 4 Google-аккаунтов** (владелец 23.09): если потребуется разнос каналов по разным Google (link-ban-риск) или один аккаунт упрётся в лимиты — использовать Donut-профили (Desktop/Donut-Portable/Donut.exe, не в PATH). Сейчас НЕ нужно, только при упоре. Donut = только мультиаккаунт-задачи (fleet-browser-routing).
4. **IG не трогать** до 24.09 ~21:00 (cooldown, scraping_warning) — t_d9c24d40 scheduled.
5. **Пароли (правило владельца 23.09, постоянное)**: гугл-аккаунты можно использовать где удобнее; если сервис требует ПАРОЛЬ (новый гугл-акк, password-логин) — ОДИН запрос владельцу (owner_inbox), он выдаёт пароль сам (vault/masked-промпт или лично в окне — НЕ текстом в чат). Никогда не генерировать/не писать пароли в файлы воркером.

## Факт run 151/153/154 (probe company 22:58/23:52): зарегистрировано 0/14
- TikTok: не залогинен (has_login_btn:true); вкладка signup/phone-or-email/email открыта — email-ветка рабочая, код на Gmail.
- VK: id.vk.ru/auth?action=signup открыт, требует телефон → вводить номер флота (п.1).
- Pinterest: не залогинен; run 154 доходил до pin2_after_name (возможно аккаунт наполовину создан — проверить перед созданием).
- YouTube: brandaccounts/create вернул 404, create_channel/account_advanced в ERR_FAILED — идти через youtube.com → avatar → «Создать канал» (brand-каналы без popup).
- Telegram: web.telegram.org открыт; каналы создавать MTProto (reference telegram-mtproto-onboarding.md).

## Урок budget_exhausted ×3 (company 23.09): монолит «14 каналов» не влезает в бюджет рана ~150 вызовов. Per-platform карты: жёсткий бюджет ≤60–80, CHANNELS_WAVE1.md ПЕРВЫМ вызовом + дописка после каждого канала, partial-результат честно фиксировать и complete. Один шаг = один CDP-вызов с readback, sleep≤3, ≤3 повтора, не поллить в цикле, не открывать все платформы сразу.