# CONTENT_SOURCES.md — карта источников готовых тем и роликов для легальной перевыкладки (Wardogs/gaming-линия)

Задача: t_db3fb98d (task_type: research). Директива владельца 09.10.2026: «рассмотреть каналы с поисками готовых тем и роликов, которые можно перевыкладывать на наши каналы». Первая волна — GAMING (Wardogs/Ruspawn24); facts/psych на паузе.
Дата среза: **2026-10-09**. Автор: research.
Границы соблюдены: research/read-only; без регистраций, публикаций, аккаунт-действий, без spend; снапшоты точечные.
Evidence-снапшоты: `docs/video/evidence/t_db3fb98d/` (тексты официальных страниц + SHA256SUMS.txt). Каждый claim: URL + дата доступа + confidence (H/M/L/null).

---

## 0. Вердикт одной строкой

**Сырая перевыкладка чужих роликов = НЕ делать** (copyright strike + YT reused-content демонетизация + платформенные анти-репост фильтры). **Рабочая форма** = (а) контент с чистой лицензией/разрешением (CC/CC0-стоки, пресс-киты, клиппинг-кампании с явной лицензией), (б) **transformative re-edit** через наш конвейер CLIPS_PIPELINE (своя нарезка, субтитры, озвучка, монтаж), (в) нативные remix-механики платформ (YT Shorts Remix, TikTok Stitch, IG Remix), где правообладатель уже разрешил семплирование, и (г) собственные геймплейные записи под fan-content-политиками издателей. Это согласуется с REPUBLISH_SOURCES_0610.md §0 (2026-10-07, H — repo).

---

## 1. LEGAL REUSE: источники с чистой лицензией

### 1.1 YouTube Creative Commons (CC BY) — лицензионно можно, практически рискованно

* **Поиск по CC-фильтру** в YT: фильтр «Creative Commons» в расширенном поиске; URL-форма `https://www.youtube.com/results?search_query=<запрос>&sp=EgIwAQ%253D%253D` (sp=EgIwAQ== = CC-фильтр). Live-проверка 2026-10-09: запрос `gaming gameplay` → фильтр работает, выданы результаты (снапшот `evidence/t_db3fb98d/yt_cc_filter_gaming_live.txt`). Confidence: **H** (механика), объём качественного gaming-инвентаря под RU-нишу = **низкий** (M — по live-выборке: свежие CC-ролики в gaming немногочисленны).
* **Официальные условия**: «If you're using someone else's work under the Creative Commons Attribution license, you need to give them credit (attribution)»; монетизация CC-контента разрешена, «if the license agreement grants you rights to use it commercially» — иногда требуется кредит автора/proof of purchase. CC-метка не может стоять на видео с Content ID claim. Источник: https://support.google.com/youtube/answer/2797468?hl=en (доступ 2026-10-09, снапшот `yt_cc_license_2797468.txt`). Confidence: **H**.
* **Атрибуция по правилам YT**: Title of the work / Author / Source URL / «is licensed under CC BY» — в описании или в самом видео (text overlay или voiceover). Там же. **H**.
* **Риск-оговорка**: даже с валидной CC-лицензией ролик без трансформации подпадает под reused-content-политику YT (§4 ниже) — «Content downloaded or copied from another online source without any substantive modifications» не монетизируется. Вывод: CC-видео годятся только как **исходник для re-edit** (нарезка+озвучка+субтитры), не для перезалива. Confidence: **H** (прямая цитата политики).
* Предыдущая оценка REPUBLISH_SOURCES_0610.md §7 «не рекомендуется без юриста» (2026-10-07) **подтверждается**: использовать точечно, с обязательной атрибуцией и трансформацией.

### 1.2 CC0/RF-видеостоки с гейминг-футажом (B-roll для re-edit)

| # | Источник | Что есть для gaming | Лицензия (verbatim-суть) | Evidence | Confidence |
|---|---|---|---|---|---|
| 1 | **Mixkit** https://mixkit.co/free-stock-video/game/ | **848 free game stock videos** (категория Game: геймеры за ПК, ретро-неон, мобильный гейминг и т.п.) | Stock Video Free License: «can be used in your commercial and non-commercial projects, for free… download, copy, modify, distribute, publicly perform and broadcast… Attribution is not required»; отдельно перечислено «YouTube videos, Social Media video posts, Online marketing ads, Commercial projects». Есть Restricted-лицензия для части айтемов — проверять на странице каждого файла | страница категории (web_extract 2026-10-09); полный текст Free License — снапшот `evidence/t_db3fb98d/mixkit_stock_video_free_license.txt` (https://mixkit.co/license/#videoFree, 2026-10-09) | **H** |
| 2 | **Pexels** https://www.pexels.com/search/videos/gaming/ | видео «gaming» (люди за ПК/консолями, стрим-сетапы); каталог с этого хоста за Cloudflare-стеной (403 live 2026-10-09), лицензия доступна | Pexels License: «All photos and videos… free to use. Attribution is not required… You can modify». Запрещено: продавать unaltered copies, редистрибуция на др. стоках, implied endorsement | https://www.pexels.com/license/ (web_extract 2026-10-09) | **H** (лицензия) / каталог **недоступен** с текущего egress |
| 3 | **Pixabay** https://pixabay.com/videos/search/gaming/ | gaming-видео; каталог за Cloudflare (403 live 2026-10-09) | Content License: free, no attribution, modify/adapt. Запрещено: standalone resale; **коммерческое использование контента с узнаваемыми торговыми марками/логотипами/брендами запрещено** (важно для gaming-футажа с логотипами игр!) | https://pixabay.com/service/license-summary/ (web_extract 2026-10-09) | **H** (лицензия) / каталог недоступен |
| 4 | **Coverr** https://coverr.co/ | стоковое видео (gaming-категория не проверялась live) | «Use Content for Free… commercial and non-commercial… attribution not required». Запрещено: **использование для AI-обучения/датасетов**; не все права очищены (бренды/трейдмарки без releases) | https://coverr.co/license (curl 200, 2026-10-09; текст в снапшоте сессии) | **H** |
| 5 | **Videvo** https://www.videvo.net/stock-video-footage/gaming/ | gaming-категория заявлена | **НЕ ПРОВЕРЕНО**: 403 с текущего egress (live 2026-10-09), Wayback не использовался. Лицензии Videvo смешанные (Free/Videvo Attribution/Standard) — обязательная per-file проверка перед использованием | доступ невозможен | **null** (не восполнять догадкой) |

Примечание: стоки дают **не «готовые виральные нарезки»**, а B-roll. Для Wardogs-линии это фон/перебивки в transformative re-edit (интро, переходы, «геймер за ПК»-сцены), не ядро контента.

### 1.3 Пресс-киты и контент-политики издателей игр

| # | Издатель/игра | Что разрешено | URL | Дата | Confidence |
|---|---|---|---|---|---|
| 6 | **Bulkhead — WARDOGS** (наша якорная игра) | Официальный пресс-кит доступен публично: `DOWNLOAD OFFICIAL PRESS KIT` → https://www.wardogs.com/_files/archives/aa46ea_664b3b2986d743bd867a079736ba78a6.zip?dn=WD_PressKit_January2026_General.zip (страница https://www.wardogs.com/press-kit, curl 200 2026-10-09). Пресс-кит = легальный источник артов/логотипов/футажа промо-характера; точные права внутри zip **не читаны** (нет массовых загрузок по BANS) — открыть и зафиксировать LICENSE/README на стадии SOURCE первого пакета | wardoogs.com/press-kit | 2026-10-09 | **H** (доступность) / условия внутри = null до вскрытия |
| 7 | **Bulkhead Wardog Partner Program** | Портал для content-creator коллабораций: «first look at what BULKHEAD has planned for future Content Creator collaborations… looking for passionate FPS enthusiasts who produce standout videos and streams»; форма заявки: платформа (YT/Twitch/TikTok), FPS-тайтлы; только по инвайтам для listed FPS (BF/COD/EFT и др.) | https://bulkhead.com/partner-program/ (curl 200, 2026-10-09) | 2026-10-09 | **H** (существование и форма) |
| 8 | **Epic Games (Fortnite/Unreal)** | Fan Content Policy: некоммерческий fan content по умолчанию; **исключение — монетизация web-видео рекламой разрешена индивидуальным фанам** («individual fans are permitted to monetize web videos (such as YouTube) with advertisements»); обязателен дисклеймер: «Portions of the materials used are trademarks and/or copyrighted works of Epic Games, Inc. All rights reserved by Epic. This material is not official and is not endorsed by Epic.»; Epic может отозвать разрешение в любой момент | https://legal.epicgames.com/epicgames/fan-art-policy (curl 200, 2026-10-09, verbatim в снапшоте сессии) | 2026-10-09 | **H** |
| 9 | **Take-Two / Rockstar (GTA5 — ядро нашей ниши: GTA5RP)** | Политика публикации геймплея: некоммерческое использование без спойлеров — не возражают; коммерческое — отдельное согласование (зафиксировано в REPUBLISH_SOURCES_0610.md §5, 2026-10-07, H — repo). **Live-реверификация 09.10 НЕ удалась**: support.rockstargames.com недоступен с текущего egress (ERR_HTTP2_PROTOCOL_ERROR, live-браузер 2026-10-09), Wayback-копия URL исключена из архива («This URL has been excluded from the Wayback Machine», 2026-10-09). Статус: опираемся на repo-фиксацию 07.10; перед первой публикацией GTA5-материала с монетизацией — реверификация с другого egress обязательна | https://support.rockstargames.com/articles/7b1aeoMFTV0iUDGhStTXvz/policy-on-posting-copyrighted-rockstar-games-material | 2026-10-09 (доступ заблокирован) | **M** (по repo 07.10; live не подтверждён) |
| 10 | **Gaijin (RU-издатель: War Thunder, Enlisted, Crossout — «популярные RU-игры»)** | Контент-правила есть по адресу https://gaijin.net/en/legaldocs/content-usage-rules, но страница за SSO-логином (live 2026-10-09 — отдаёт форму Gaijin Single Sign On). Содержимое = **null**, не восполнять догадкой. Обход закрытого источника не выполнялся (по правилам SOUL) | gaijin.net/en/legaldocs/content-usage-rules | 2026-10-09 | **null** |
| 11 | **Supercell / Blizzard / Ubisoft / Riot** | Сводка политик с URL зафиксирована в REPUBLISH_SOURCES_0610.md §5 (2026-10-07, H/M — repo): Supercell fan-content с условиями монетизации; Blizzard Video Policy; Ubisoft разрешает монетизацию через партнёрки; Riot — общая ToS | см. REPUBLISH_SOURCES_0610.md §5 | 2026-10-07 | **M** (репозиторная фиксация, live 09.10 не реверифицирован) |

**Ключевое правило (§5 REPUBLISH_SOURCES, 2026-10-07, H — repo):** политики издателей регулируют **собственные записи геймплея автора**, а НЕ право нарезать чужие стримы. Для нарезок чужих стримов нужно разрешение стримера или клиппинг-кампания, где автор сам выложил исходники (Klipni Wardogs RU — наш текущий якорь, см. REPUBLISH_SOURCES_0610.md §1).

### 1.4 Free asset packs / CC0-архивы (графика, звук, иконки — для оформления клипов)

| # | Источник | Лицензия | Evidence | Confidence |
|---|---|---|---|---|
| 12 | **Kenney.nl** (тысячи game-ассетов) | **CC0** — verbatim со страницы ассета: «License: Creative Commons CC0» (пример https://kenney.nl/assets/pixel-platformer, live-браузер 2026-10-09; снапшот `evidence/t_db3fb98d/kenney_cc0_evidence.txt`) | CC0 = свободное коммерческое использование без атрибуции | **H** |
| 13 | **OpenGameArt.org** | Микс лицензий (CC0, CC-BY, GPL и др.) — есть раздел/фильтр CC0; per-file проверка обязательна | https://opengameart.org/ + https://opengameart.org/content/cc0 (curl 200, 2026-10-09) | **H** (структура) / per-file |
| 14 | **Game-icons.net** (4180+ иконок) | **CC BY 3.0** — verbatim: «provided under the terms of the Creative Commons 3.0 BY license… as long as you credit the original author… "Icons made by {author}. Available on https://game-icons.net" is fine» | https://game-icons.net/about.html (curl 200, 2026-10-09) | **H** |
| 15 | **Freesound.org** (звуки/SFX) | Микс CC0/CC-BY/NC; фильтр лицензий в поиске включает «Free Cultural Works approved (CC-BY или CC0)»; NC-файлы **исключить** (мы монетизируем) | https://freesound.org/help/faq/ (curl 200, 2026-10-09) | **H** |
| 16 | **YouTube Audio Library** | Royalty-free музыка/SFX для YT-монетизации — сам YT указывает её как безопасный источник музыки: «If you're looking to use someone else's music, check out YouTube's Audio Library» (answer/2797468, 2026-10-09, снапшот) | внутри YT Studio | **H** |

---

## 2. PERMISSION routes: разрешения авторов и нативные механики платформ

### 2.1 Нативные remix-механики (правообладатель уже разрешил семплирование кнопкой)

| # | Платформа | Механика | Правила (официально) | Evidence | Confidence |
|---|---|---|---|---|---|
| 17 | **YT Shorts Remix** | Sound (до 90 сек аудио; иногда лимит 30 сек по партнёрским соглашениям), Cut (1–5 сек сегмент аудио+видео), Green Screen (видео-фон), Collab, Template, + новый AI-Reimagine (EN only, rollout) | Ремикс доступен только там, где автор не ограничил его (настройка «restrict remixing» у правообладателя); «Shorts made with remixed content are attributed back to the original work»; перезалив ремикса, сделанного вне YT, с чужим copyright-материалом → Content ID claim/takedown | https://support.google.com/youtube/answer/10623810?hl=en (live-браузер 2026-10-09, снапшот `yt_remix_10623810.txt`) | **H** |
| 18 | **TikTok Stitch** | «Сшивание»: фрагмент чужого видео (длительность выбирается) + своя запись продолжения | Сшивать можно **только видео публичных аккаунтов** и только если автор разрешил Stitch в privacy-настройках («Все»/«Друзья»/«Только вы»); сшитое видео живёт в профиле снявшего; автор оригинала может удалить сшивания | https://support.tiktok.com/en/using-tiktok/creating-videos/stitch-settings (live-браузер 2026-10-09, снапшот `tt_stitch_settings.txt`) | **H** |
| 19 | **IG Remix** | Ремикс чужих Reels/постов — целиком или частично, на телефоне | «Любой человек может создать и скачать ремикс» — но автор управляет разрешением ремиксов (кто может: статья 792438641600810); функция недоступна на компьютерах | https://help.instagram.com/139004934231412/ (live-браузер 2026-10-09, снапшот `ig_remix_139004934231412.txt`) | **H** |
| 20 | **VK Клипы — репост/клипы-репост** | Официальная справка VK с текущего egress недоступна (vk.com — connection failure live 2026-10-09, curl и браузер); механика «репост клипа» существует в продукте, но правила/лимиты = **null** | По канону PLATFORM_ALGORITHMS.md §1.3 (2026-09-24, MED — repo): «Неоригинал/репосты без добавленной ценности — алгоритм не продвигает»; вотермарка чужой платформы → понижение рекомендаций | недоступно live | **null/M** (канон repo) |

**Практический вывод**: нативные remix-механики — единственный способ «использовать чужой ролик» без отдельного разрешения, но: (1) они дают семпл, а не полный ролик; (2) требуют мобильного приложения и живого аккаунта (account-actions в этой карте запрещены); (3) на YT ремикс-контент монетизируется в рамках обычных политик (см. §4). Для конвейера это **не ядро**, а тактический формат отдельных выпусков.

### 2.2 Коллаборации/репосты с разрешения авторов — как оформлять

* **Форма разрешения**: письменное (сообщение/e-mail/комментарий с фиксацией) разрешение конкретного автора на конкретный ролик, с полями: (а) какой материал (URL/ID), (б) какие платформы, (в) срок, (г) разрешена ли монетизация, (д) форма кредита. Снапшот разрешения (скрин/текст + дата + SHA256) идёт в rights-пакет CLIPS_PIPELINE §2.
* **Важно**: на YT разрешение автора **не защищает от reused-content-демонетизации** — «This policy applies even if you have permission from the original creator» (answer/1311392, 2026-10-09, снапшот). Разрешение снимает copyright-риск, но не снимает требование трансформации для монетизации.
* **Готовый легальный маршрут с лицензией**: клиппинг-кампании (Klipni Wardogs RU: 25 ₽/1000 подтверждённых, erid через платформу) — бренд сам вносит исходники и выдаёт лицензию правилами кампании. Детали, ставки и риски: REPUBLISH_SOURCES_0610.md §1 (2026-10-07, H — repo). Публикация кампанийных роликов НЕ совмещается с VK-партнёркой (правило §1.4 там же).
* **Bulkhead Partner Program** (№7 выше) — официальный канал получения эксклюзивных Wardogs-материалов и прав на коллаборацию; заявка = форма (0 ₽), но это account-action → **вне этой карты**, отдельное решение owner/ops.

---

## 3. TREND/ТЕМЫ: где брать готовые проверенные темы

| # | Источник | Что даёт | Статус live 2026-10-09 | Confidence |
|---|---|---|---|---|
| T1 | **TikTok Creative Center** https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en | Топ-100 хэштегов по отраслям/регионам (posts, trend, creators), тренды песен и креаторов — публично, без логина (детальные графики — после login) | HTTP 200, контент ранжирования хэштегов присутствует (web_extract 2026-10-09) | **H** (доступ) / gaming-срез = собрать отдельным прогоном |
| T2 | **YT-поиск с фильтрами** (`sp=`-коды: upload date, view count, CC) | «Проверенный спрос» = свежие ролики ниши с высокими просмотрами; CC-фильтр даёт ещё и лицензионно-чистый пул | Работает без логина (live-проверка CC-фильтра, снапшот `yt_cc_filter_gaming_live.txt`) | **H** |
| T3 | **YT Trending-страница** https://www.youtube.com/feed/trending | Исторически — тренды по категориям | **Консент-волл** с текущего egress (редирект на consent.youtube.com, gl=DE, 2026-10-09). Работоспособность в RU-регионе = null | **null** |
| T4 | **YT Charts** https://charts.youtube.com/charts/Shorts | Чарты Shorts/музыки | Редиректит на `/charts/unknown/ru/daily` с пустым телом (2026-10-09) — чарт Shorts по этому URL **не отдаётся**; статус продукта = null | **null** |
| T5 | **Статистика конкурентов** (какие нарезки собирают просмотры) | Метод канона: THEMES_MATRIX.md — «клипы 86к+ просм. на ролик в нише GTA5RP [25]» и др. (repo, H — repo-фиксация); механика снятия метрик — SPEC_B_themes.md §4 «что внутри gaming стреляет (фейлы, скилл-моменты, реакции, разборы)» | repo-канон | **M/H** (repo) |
| T6 | **VK Клипы-тренды** | Трендовая лента VK | vk.com недоступен с текущего egress (2026-10-09) = **null**; официальная справка не получена | **null** |
| T7 | **DISCOVERY_BRIEF_2026-10.md (repo, 2026-10-08)** | Связка: §7.2 «Gaming-ниша hooks: clipspeed reversal (scenario/POV слаб в gaming pool 0.57x) → gaming-хуки требуют A/B-теста, точные lift-цифры = null»; §7.5 «официальные пороги VK Клипы = null». Тема-отбор должен это учитывать: не переносить facts/psych-хуки в gaming вслепую | repo | **H** (repo) |

**Критерии отбора темы** (для стадии SOURCE, см. §5): (1) evidence спроса — просмотры/скорость набора у ≥2 независимых роликов-аналогов ниши (URL+дата); (2) конкуренция — сколько свежих (≤14 дней) аналогов, есть ли незанятый угол; (3) лицензионная чистота исходника; (4) соответствие gaming-хук-ограничению DISCOVERY_BRIEF §7.2 (A/B-тест хука обязателен); (5) стоп-лист тем: спорные/18+/политика (репутационный риск — эскалация owner).

---

## 4. RISK-оценка (честно)

### 4.1 Что НЕ делать вообще

1. **Сырой перезалив чужих роликов** (стримов, TikTok/YT-видео) без лицензии и трансформации — максимум риска:
   * Copyright: Content ID claim / takedown / strike (YT: https://support.google.com/youtube/answer/2797468, 2026-10-09 — «YouTube cannot grant you rights… If you want to use someone else's YouTube content, reach out to them directly»).
   * YT-монетизация: reused content — «channels that repurpose content that's already on YouTube or another online source without adding significant original commentary, substantive modifications, or educational or entertainment value»; запрещено в частности: «Clips of moments… edited together with little or no narrative», «Short videos you compiled from other social media websites», «Content downloaded or copied… without any substantive modifications», «Content uploaded many times by other creators». Источник: https://support.google.com/youtube/answer/1311392?hl=en (доступ 2026-10-09, снапшот `yt_monetization_policies_1311392.txt`). Confidence: **H**.
2. **Масс-продакшн по шаблону**: «inauthentic content» (переименовано из «repetitious» 15.07.2025) — «AI-generated content made with generic or unoriginal templates giving the impression of mass production without adding the creator's original, authentic insights» не монетизируется (там же, H). Прямо касается нашего конвейера: каждый клип должен иметь materially varied substance.
3. **Перезаливы с вотермаркой чужой платформы** (TikTok-лого на VK-клипе и т.п.) — понижение дистрибуции (PLATFORM_ALGORITHMS.md §1.3, repo, MED).
4. **Использование NC-лицензий** (CC-BY-NC и т.п.) в монетизируемых роликах — нарушение лицензии.
5. **GTA5RP-контент с коммерческой монетизацией до реверификации политики Take-Two/Rockstar** (№9: live-доступ 09.10 заблокирован, подтверждена только repo-фиксация 07.10 «коммерческое — отдельное согласование»).

### 4.2 Что разрешено-монетизируемо (официально, answer/1311392, 2026-10-09, H)

* «Reused content… is allowed if viewers can tell that there's a meaningful difference between the original video and your video»: критические разборы, переозвучка, reaction с комментариями, «Edited footage… where you add a storyline and commentary», «Edits to remixed content on Shorts… adding the original audio or video segment from other videos to your content», контент, где автор видим/объясняет свой вклад, «Edited footage with audio and visual effects on top of the video's reused content that demonstrates substantive editing».
* → **Наш безопасный стандарт**: чистый исходник (лицензия/разрешение) + transformative re-edit (своя нарезка, hook, субтитры, озвучка TTS/VO, motion) = то, что уже делает CLIPS_PIPELINE (стадии SCRIPT+TEMPLATE→RENDER). Reused-политика применяется **к каналу целиком** («applies to your channel as a whole») — один грязный перезалив ставит под удар монетизацию всего канала.

### 4.3 Платформенные лимиты/анти-репост фильтры

* **IG**: «оригинальный контент получает на 40–60% больше дистрибуции, чем репосты; ≥10 репостов за 30 дней → исключение из рекомендаций» (PLATFORM_ALGORITHMS.md §4.1, repo, MED).
* **VK**: неоригинал без добавленной ценности не продвигается; AI-лицо → ×0.5 охват (PLATFORM_ALGORITHMS.md §1.3, repo, MED/внутренний playbook).
* **YT**: см. §4.1–4.2; также «Unsatisfying or Off-putting Content» — эмоционально-манипулятивные формулы и взаимозаменяемые видео не монетизируются (answer/1311392, H).
* **TikTok**: stitch-контент ограничен настройками автора оригинала; сшитое видео отображается только в профиле снявшего (снапшот `tt_stitch_settings.txt`, H).

### 4.4 Матрица рисков (сводно)

| Вариант | Copyright | Монетизация | Дистрибуция | Вердикт |
|---|---|---|---|---|
| Сырой перезалив чужого | strike/takedown (H) | reused-content бан (H) | анти-репост фильтры (MED) | **ЗАПРЕЩЕНО** |
| Перезалив с мелким эдитом (кроп/скорость) | claim (H) | «minimal changes… violation» (H) | понижение (MED) | **ЗАПРЕЩЕНО** |
| CC-видео + атрибуция, без трансформации | легально по CC (H) | reused-content риск (H) | — | **НЕ для монетизации**; только как сырьё |
| Чистый исходник + полный transformative re-edit (наш конвейер) | минимальный (H) | разрешено при substantive editing (H) | обычная | **РАБОЧАЯ ФОРМА** |
| Нативный remix (YT/TT/IG) | разрешено механикой (H) | по обычным политикам (H) | обычная | **Тактика**, не ядро |
| Клиппинг-кампания (Klipni) | лицензия кампании (H — repo 07.10) | платит кампания (H — repo) | обычная | **РАБОЧАЯ ФОРМА** (якорь Wardogs RU) |
| Собственный геймплей под fan-policy издателя | по политике (H/M) | Epic: ad-монетизация разрешена (H); Rockstar: M — реверификация | обычная | **РАБОЧАЯ ФОРМА** (после проверки per-издатель) |

---

## 5. WORKFLOW: встройка в CLIPS_PIPELINE §2 SOURCE

Стадия SOURCE (владелец research) по CLIPS_PIPELINE.md §2 (repo): гейт = «Пак источника: права (лицензия+URL+снапшот), SHA256, ffprobe, evidence спроса. M0 motion-scan: freezedetect n=-50dB d=2.0 на 9:16-кропе каждого окна — ноль freeze>2с». Настоящая карта добавляет к этому гейту:

1. **Rights-пакет на каждый ролик** (обязательный минимум):
   * `license`: точное имя лицензии (CC0 / CC BY 3.0 / Mixkit Stock Video Free / Pexels License / Epic Fan Content / Klipni campaign terms / written permission) + verbatim-цитата ключевых пунктов;
   * `source_url` + `accessed_at` (дата);
   * `snapshot`: скачанный файл исходника + снапшот лицензионной страницы (text), SHA256 обоих (шаблон: `docs/video/evidence/t_db3fb98d/SHA256SUMS.txt`);
   * `attribution`: готовая строка кредита (для CC BY: «Title — Author — URL — licensed under CC BY»; для game-icons: «Icons made by {author}. Available on https://game-icons.net»; для Epic: полный дисклеймер из №8);
   * для разрешений: снапшот переписки/комментария + кто разрешил + scope (платформы/срок/монетизация).
2. **Тематический отбор** (критерии §3): evidence спроса ≥2 аналогов (URL+дата+просмотры), проверка конкуренции (≤14 дней свежие), соответствие gaming-хук A/B-ограничению (DISCOVERY_BRIEF §7.2), стоп-лист.
3. **Техническая проверка** (уже в гейте SOURCE): ffprobe-метрики + M0 freezedetect-скан.
4. **Routing по типу источника**:
   * стоки/CC0-ассеты → прямо в SOURCE-пак;
   * YT CC-видео → SOURCE-пак только вместе с планом трансформации (SCRIPT+TEMPLATE обязан добавить narrative/commentary — гейт reused-content §4.2);
   * клиппинг-кампании → SOURCE-пак = бриф кампании + правила площадки (snapshot+SHA256), публикация только в рамках кампании (REPUBLISH_SOURCES §1.4);
   * нативные remix → вне файлового конвейера (ручные мобильные сессии, account-actions = отдельные ops-карты с owner-гейтом);
   * press-kit издателя → вскрыть LICENSE/README zip'а, зафиксировать в rights-пакете до использования ассетов.
5. **Эскалации**: любой источник с лицензией, содержащей нестандартные ограничения (Restricted/NC/«no AI training» — например Coverr) → пометить и не использовать в AI-пайплайне без явной проверки; репутационно-спорные темы → owner.

---

## 6. Пробелы (null — не восполнять догадкой) и следующий шаг

1. **Rockstar/Take-Two live-политика**: support.rockstargames.com недоступен с текущего egress (ERR_HTTP2 2026-10-09), Wayback исключён → реверификация с другого egress/мобильной сети перед GTA5-монетизацией. Owner: research (след. карта) / ops.
2. **Videvo**: 403 (Cloudflare) — лицензии не проверены = null.
3. **Gaijin content-usage-rules**: за SSO = null (обход не выполнялся).
4. **VK**: весь домен недоступен с текущего egress (curl 000, браузер-таймаут) — правила репостов/клипов и тренды VK = null (в каноне PLATFORM_ALGORITHMS.md — MED-источники третьих сторон).
5. **YT Trending / Charts Shorts**: консент-волл / пустой редирект с DE-egress — как trend-источник = null; рабочая замена: T1 (TikTok CC) + T2 (YT-фильтры) + T5 (конкурент-статистика).
6. **Wardogs press-kit zip**: не вскрыт (BANS: no downloads объёмов) — условия использования ассетов = null до точечного вскрытия LICENSE/README на первом SOURCE-пакете.
7. **Pexels/Pixabay каталоги gaming**: 403 live (Cloudflare) — наличие конкретного gaming-инвентаря подтверждается только поисковыми описаниями (M); лицензии — H.

**Следующий шаг и owner**: company — (а) передать карту в video-director/tech как справочник стадии SOURCE; (б) решить по заявке в Bulkhead Partner Program (account-action, owner-гейт); (в) поставить задачу реверификации Rockstar/VK с живого egress (ops или живая Google-сессия 9222).

---

## Приложение A. Evidence-инвентарь

`docs/video/evidence/t_db3fb98d/` (SHA256 в `SHA256SUMS.txt`, создан 2026-10-09):

| Файл | Содержимое | Источник |
|---|---|---|
| yt_remix_10623810.txt | Полный текст официальной статьи YT «Create YouTube Shorts with remixed content» | support.google.com/youtube/answer/10623810, 2026-10-09 |
| yt_cc_license_2797468.txt (+ .html) | Официальная статья YT «Creative Commons» (условия, атрибуция, FAQ монетизации) | support.google.com/youtube/answer/2797468, 2026-10-09 |
| yt_monetization_policies_1311392.txt (+ .html) | «YouTube channel monetization policies»: inauthentic/reused/generic content (обновление 15.07.2025) | support.google.com/youtube/answer/1311392, 2026-10-09 |
| yt_cc_filter_gaming_live.txt | Live-снапшот выдачи YT CC-фильтра (gaming gameplay, sp=EgIwAQ==) | youtube.com/results, 2026-10-09 |
| tt_stitch_settings.txt | Официальная справка TikTok «Сшивание» (Stitch): правила, privacy, как сшить | support.tiktok.com/…/stitch-settings, 2026-10-09 |
| ig_remix_139004934231412.txt | Официальная справка IG «Создание ремикса видео» | help.instagram.com/139004934231412, 2026-10-09 |
| mixkit_stock_video_free_license.txt | Verbatim Mixkit Stock Video Free License | mixkit.co/license/#videoFree, 2026-10-09 |
| kenney_cc0_evidence.txt | Verbatim «License: Creative Commons CC0» (страница ассета Kenney) | kenney.nl/assets/pixel-platformer, 2026-10-09 |

Дополнительно (тексты в сессионных снапшотах, процитированы в карте): Pexels License (pexels.com/license), Pixabay Content License Summary (pixabay.com/service/license-summary), Coverr License (coverr.co/license), Epic Fan Content Policy (legal.epicgames.com), game-icons.net/about.html, freesound.org/help/faq, Wardogs press-kit (wardogs.com/press-kit + zip-ссылка), Bulkhead Partner Program (bulkhead.com/partner-program), TikTok Creative Center (ads.tiktok.com/business/creativecenter) — все доступы 2026-10-09.

Недоступные источники (помечены, не восполнены догадкой): support.rockstargames.com (ERR_HTTP2 + Wayback-excluded), videvo.net (403), gaijin.net legaldocs (SSO), vk.com (egress-fail), youtube.com/feed/trending (consent-wall), charts.youtube.com/charts/Shorts (пустой редирект), pexels.com/pixabay.com каталоги (Cloudflare 403).

*Файл: `C:/Users/max/Desktop/all/ventures/docs/video/CONTENT_SOURCES.md`*
