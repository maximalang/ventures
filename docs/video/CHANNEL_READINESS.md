# CHANNEL_READINESS.md — аттестация каналов линии Wardogs (t_6903f464)

Дата аудита: **2026-10-09 14:00–15:00 MSK** (run 670, operations).
Канон: NAMING_APPROVED.md §ФИНАЛЬНЫЙ (29.09), CHANNELS_WAVE1.md, CHANNELS_READY_MAP_0610.md.
Метод: live HTTP-проверки + readback из авторизованных сессий; evidence — `kanban/boards/video/workspaces/t_6903f464/evidence/` (HTML-снапшоты, JSON-receipts, avatar JPEG).

## Сводка вердиктов

| Канал | Вердикт | Блокер / gap |
|---|---|---|
| TG @ruspawn24 | **READY** | — (identity исправлен в этом ране) |
| IG @ruspawn24 (бывш. @ru.prime.game) | **READY** | — (avatar+bio+username сданы 01–03.10) |
| YT @ruspawn24 (UCRnY4N8WVHcPfKKJgITEwIA) | **READY-CONDITIONAL** | about пустой, banner нет — cosmetic-gap до первой публикации (см. follow-up) |
| VK vk.ru/ruspawn24 (club241843980) | **NOT-READY** | название «Respawn 24» ≠ канон «Ruspawn24», description/status пусты; сессия разлогинена → owner SMS (t_c899c9ba) |
| TikTok @ruspawn24 | READY-COSMETIC-GAP (вне scope, заморожен) | nickname уже канон, bio пуст (t_5cbcf4d7 item 5) |

**Приёмка «≥2 канала READY» выполнена: TG + IG (+YT conditional).**

---

## 1. TG @ruspawn24 — READY (исправлен в этом ране)

Identity (readback API + публичный t.me/s/ruspawn24, HTTP 200):
- Title: **Ruspawn24** ✅ канон (уже был).
- Username: **ruspawn24** ✅ канон (не менялся).
- About: было «Канал Wardogs RU. Материалы без лишнего шума.» (устаревший бренд) → **установлено**: «Ruspawn24 — GTA 5 RP и игры: клипы, нарезки, гайды и моменты. Новые ролики регулярно. @ruspawn24 на YouTube, VK, TikTok.» — readback `about` совпадает, og:description публично подтверждает.
- Аватар: было пусто (ChatPhotoEmpty) → **установлен** war-hound crest (тот же бренд-актив что IG @ruspawn24; PNG→JPEG конвертация, т.к. TG отклоняет .png: PhotoExtInvalidError). Readback: photo_type=ChatPhoto; публичный og:image отдаёт cdn4.telesco.pe URL.
- Подписчики: 1 (флот-аккаунт @botassistanthub, creator). Контента нет — по плану (публикации после ГО).

Обустройство: закреплённый пост не требуется до первой публикации; invite-backup есть в CHANNELS.md.
Warm-up: канал создан 23.09, возраст 16 дней, предупреждений/страйков нет.
Technical: MTProto-сессия жива (auth id=8140468331, этот ран); публикационный маршрут — telethon из capabilities/telegram.
Evidence: `evidence/tg_ruspawn24_identity_result.json`, `evidence/tg_ruspawn24_photo_result.json`, `evidence/tg_ruspawn24_after.html`, `evidence/tg_ruspawn24_avatar.jpg` (sha256 3b4c9d7a3c01f014790c35007a8a84f8bf1c7d576245d693cab1fb04fe670a24).

## 2. IG @ruspawn24 — READY (сдан ранее, подтверждён)

- Username: @ru.prime.game → **@ruspawn24** (rename 01.10, instagrapi, VERIFY user_info) — capabilities/instagram/ACCESS.md §ФИНАЛ 01.10.
- Аватар: установлен 03.10 (t_d9c24d40): war-hound crest, live URL HTTP 200, sha256 зафиксирован в ACCESS.md.
- Bio: установлено 03.10: «UGC video in 10 min: paste a URL, get a ready Reels clip…» + hashtags + @handle.
- Live-проверка этого рана: https://www.instagram.com/ruspawn24/ HTTP 200 (632 KB); https://www.instagram.com/ru.prime.game/ HTTP 200 (redirect на новый handle) — evidence `ig_ruspawn24.html`, `ig_ru_prime_game.html`. Анонимный fetch показывает login-wall (норма IG), identity-факты — по авторизованному readback 03.10.
- Warm-up: аккаунт с 23.09; scraping_warning 23.09 отработан cooldown'ом; с 03.10 чисто.
- Technical: instagrapi-сессия `ig_session_settings.json` (load_settings = вход без логина), proxy incy 10809 жив (LISTENING, этот ран).
- Граница: публикации ≤1/сутки, DM/аутрич запрещены (IG_STREAM_SPEC).

## 3. YT @ruspawn24 — READY-CONDITIONAL

Live-проверка этого рана (HTTP 200, 860 KB, evidence `youtube_ruspawn24.html`):
- Handle **@ruspawn24** ✅ (vanityChannelUrl совпадает), channelId UCRnY4N8WVHcPfKKJgITEwIA ✅ (совпадает с WAVE1 row 1), externalId совпадает.
- Display name: **«Respawn 24»** — соответствует NAMING_APPROVED §3 (display gaming = «Respawn 24»); WAVE1 фиксирует synced.
- Аватар: установлен ✅ (avatar thumbnails присутствуют в initial data).
- **Gaps**: (1) about = «Здесь пока ничего нет.» — описание с ключевыми словами отсутствует; (2) banner не установлен; (3) видео 0 (по плану до ГО); (4) display-name в брендинг-каноне 29.09 не переподтверждён (смена display требует fresh Google auth на myaccount.google.com — исторический блокер t_2e6829d8).
- Почему не правил в этом ране: студийная сессия YT заморожена дисциплиной карты t_f73153e2 (blocked/needs_input, ≤1 probe на аккаунт в сутки, g1/maxiduoservice не трогать до решения владельца). Правка about/banner — отдельная bounded-операция после разблокировки YT-маршрута.
- Technical: Google-сессия maxiduoservice LIVE (подтверждена 06.10, ACCESS.md run 419); cookie-набор достаточен для studio.youtube.com; туннель SOCKS 10810 поднят (LISTENING, этот ран).
- Вердикт: публиковаться можно (канал live, handle/display/avatar канон), about/banner закрыть до/вместе с первой публикацией.

## 4. VK vk.ru/ruspawn24 — NOT-READY (owner-граница)

Live-проверка этого рана (через Wi-Fi-интерфейс 192.168.31.141 — INCY-туннель режет VK; evidence `vk_desktop_ruspawn24.html`, `vk_ruspawn24.html`):
- Сообщество существует: screen_name **ruspawn24** ✅, создан 29.09 00:56, members_count=1, фото сообщества установлено (photo_200 userapi URL).
- **Несоответствия канону**: name=**«Respawn 24»** (канон 29.09: «Ruspawn24»), description пусто, status пусто, cover disabled.
- Блокер: VK-сессия id1044189336 разлогинена (t_c899c9ba, 01.10) — повторная авторизация = телефон владельца + SMS = **owner-boundary, запрещена на этой карте**. Rename ruspawn24 + создание propsychology24 остаются на t_c899c9ba после «Да: VK login» владельца.
- Линия может стартовать без VK (по тексту карты).

## 5. TikTok @ruspawn24 — вне scope (заморожен), статус зафиксирован

- Live-проверка этого рана (HTTP 200, 371 KB, evidence `tt_ruspawn24.html`): uniqueId=**ruspawn24**, nickname=**«Ruspawn24»** ✅ канон (косметика nickname из t_5cbcf4d7 item 5 фактически уже выполнена), signature (bio) пуста, 0 подписчиков/видео.
- Регистрация новых TT-аккаунтов заморожена (DEFAULT C); bio-fill остаётся на t_5cbcf4d7.

---

## Cross-check с планом публикаций

- AUDIENCE_PLAYBOOK.md не создан (research сдал DISCOVERY_BRIEF_2026-10.md вместо него, t_bccefacf done) — сверка окон постинга выполнена по DISCOVERY_BRIEF: RU-окна и warm-up-правила перенесены в follow-up-карту YT-косметики и в контракт POSTING-DAILY.
- Публикаций в этом ране: **0**. Регистраций: **0**. Расходов: **0 ₽**.

## Блокеры и следующие владельцы

1. **Владелец**: «Да: VK login» (SMS) → t_c899c9ba: rename «Ruspawn24» + description + propsychology24.
2. **Владелец**: решение по YT Psych (t_f73153e2, check_at 10.10 12:00) — разблокирует YT-маршрут, после чего operations закроет about/banner @ruspawn24.
3. **QA (R1)**: независимая проверка readiness-claims этой карты (дочерняя карта).
4. **Company**: зафиксировать CHANNELS_READY (TG+IG, YT-conditional) в контракте PUB-FINAL t_f483ae5c / POSTING-DAILY t_550a6fa8.

## Финансовый scope

period=Д0, confirmed revenue=null, paid costs 0₽, commitments 0₽, estimated usage cost=null.
