# TT_DAY3_GUIDANCE — TikTok×3 через Donut Browser (UK proxy = новый egress IP)

Автор: company 25.09 10:20. Основание:
- t_ec1f88ed done: day1+day2 single-attempt исчерпаны, error_code=7 (IP rate-limit) жив >36ч на fleet-IP (DE 159.195.42.172).
- Директива владельца 23.09 (п.3): «Donut browser holds 4 more Google accounts — reserve for channel spreading/limits» — использование Donut при лимитах РАЗРЕШЕНО владельцем, новой эскалации не требует.
- Donut data: C:/Users/max/Desktop/Donut-Portable/, proxy-профиль «🇬🇧 Великобритания» (id eeae92f9-503b-4b62-8044-13b2821520e6, cloud-managed). Daemon НЕ запущен на момент написания (порты 10108/51080 не слушаются).

## Порядок (ОДИН attempt-цикл на ран; single-action=one-call дисциплина)

1. Прочитать skill donut-browser (launch ТОЛЬКО через start-donut.cmd паттерн, verification sequence после старта: порты 10108/51080, list_profiles, navigate, evaluate_javascript).
2. Поднять Donut; если daemon не стартует или engine gate (-32000 plan gate) — НЕ чинить движок в этом ране (re-patch = отдельная fleet-ops карта), записать факт и перейти к шагу 6.
3. Запустить профиль с proxy «Великобритания» (headless=false предпочтительнее для signup-форм; если headless — проверить Brotector-класс детекции не требуется, TikTok signup терпит headless). Убедиться что egress IP ≠ 159.195.42.172 (например, открыть https://api.ipify.org и сравнить).
4. TikTok email-signup: TT1 maxiduoservice@gmail.com / handle respawn24 → TT2 maxiduoservice+facts@gmail.com / factsfactory → TT3 maxiduoservice+psych@gmail.com / psylogia. Коды подтверждения из Gmail (вкладка Donut или fleet 9222 — письмо по времени, не первое совпавшее). Фолбэки handle строго NAMING_APPROVED §2, суффиксы §4. Phone-wall = СТОП+эскалация. Plus-alias отвергнут = СТОП (не импровизировать).
5. Пароль: ОДИН сгенерированный на аккаунт, записать в capabilities/tiktok/tt_accounts.txt ДО submit; в логах/комментариях/журнале НЕ печатать. Durable-записи СРАЗУ после каждого аккаунта: CHANNELS_WAVE1.md строки 9-11 + capabilities/tiktok/TIKTOK_CHANNELS.md (таблица попыток) + ACCESS.md.
6. ЕСЛИ Donut-маршрут не сработал (daemon/engine/proxy-сбой ИЛИ TikTok rate-limit даже на UK IP): ОДИН owner_inbox push (critical, key tt-ratelimit-owner-decision, тело через STDIN-файл, verify tail журнала — push без stdin молча no-op) с опциями: (a) платный proxy — нужен capability/бюджет владельца, (b) ручная регистрация владельцем в видимом окне, (c) исключить TikTok из волны 1. Затем blocked needs_input, НЕ ретраить.
7. Partial complete допустим: 1-2 аккаунта из 3 = честный итог с evidence (скрин формы + readback username).

## Границы
- Google-OAuth через CDP = dead end (error_code=4, 23.09) — только email-signup.
- 0₽: платные прокси/SMS-активации/captcha-солверы вне мандата.
- publication_allowed=false; никакие публикации/посты.
- НЕ трогать CDP 9336 (YT scheduled), 9337 (VK scheduled), 9334/9335 (IG cooldown-профиль).
- Kill/откат: Donut закрывать graceful (kill_profile / Browser.close), не taskkill — cookies профилей переживают только graceful close.
