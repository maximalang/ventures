# DISCOVERY_BRIEF_2026-10 — Распаковка канонических research-документов в короткий рабочий бриф

**Task:** t_bccefacf | **Owner:** company | **Task type:** research (read-only, 0 ₽) | **Date:** 2026-10-08
**Anchor:** `PLATFORM_ALGORITHMS.md` (330 строк), `SPEC_I2_ALGORITHMS.md`, `SPEC_J_views_growth.md`, `VIEWS_GROWTH_PLAYBOOK.md` (303 строки), `GROWTH_SCHEMES_0610.md` (118 строк), `PLATFORM_RANKING.md` (142 строки), `CLIPS_PRODUCTION_PLAN_0610.md` (G1-G5), `WARDOGS_FIRST_0310.md`, `CHANNELS_READY_MAP_0610.md`.
**Scope:** рекомендации и алгоритмы YT Shorts, VK Клипы, Instagram Reels, TikTok, Telegram (без платных бустов, без обхода региональных ограничений).

---

## 0. Мета-вывод (все источники сходятся)

Алгоритмы всех площадок 2025–2026 сошлись на одной механике:
> **тестовый посев на узкую выборку → решение о масштабировании по удержанию первых секунд (first-3s) и досмотру → rewatch/loop как сильнейший бустер.**

Просмотры — downstream от retention (quso.ai, 508k постов, 2026-06-29, HIGH). Подписчики почти не влияют на Shorts-раздачу (74% просмотров Shorts — от не-подписчиков; go-viral.app 2026-03-14, MED). Поэтому 80% усилий конвейера — в первые 3 секунды и в «петлю» последних 3 секунд.

**Confidence-шкала:**
- **HIGH** — официальная документация платформы ИЛИ исследование ≥30K единиц ИЛИ несколько независимых источников 2025–2026.
- **MED** — 1 независимое исследование / несколько отраслевых гайдов без первички.
- **LOW** — фольклор SMM-блогов; ориентир для теста, не для решений.

---

## 1. Рабочие сигналы по площадкам (top-5 на площадку)

### 1.1 YouTube Shorts
1. **VVSA (Viewed vs Swiped Away) ≥ 70%** — первичный гейт; <60% = коллапс (Galloway 3.3 млрд views; tubecreatorkit 2026). HIGH.
2. **Satisfaction Signals > raw watch time**: completion, replays, survey signals (go-viral.app 2026-03-14). MED.
3. **Explore/Exploit фазы**: explore-пакет на случайной выборке → exploit при прохождении порога (vidIQ 2025-12-29, цитирует Todd Sherman). HIGH.
4. **Порог здоровья канала**: VVSA ≥70%; 200 Shorts = стабильный рост (Nate Black / vidIQ). MED.
5. **Длина**: 11–20 сек даёт высшую медиану просмотров (quso.ai); 13с и 60с — sweet spots (Nate Black, directional). HIGH/MED.
- **Kill**: Inauthentic Content Policy (2025-07-15) — массовый шаблонный контент без человеческого слоя → демонетизация всего канала. HIGH.

### 1.2 VK Клипы
1. **First-3s критична**: смахнул на 3-й сек — алгоритм режет показ (ppc.world 2026-07-08 + dtf.ru 2026-02-25). HIGH.
2. **Реакции равномернее по дню после апдейта 2025**; качество контента превалирует над временем (LiveDune, 30 млн постов). HIGH.
3. **Тестовый посев 200–300 показов** на случайной выборке; ступенчатое расширение (zapuski.com 2026-08-24). MED.
4. **First-hour окно** решает дистрибуцию; **повторная дистрибуция через 24+ ч** возможна (fathersmm 2026-06-01; ppc.world LiveDune). MED/HIGH.
5. **Trend-hints при загрузке** (хештеги/треки из UI VK) — прямой relevance-сигнал, 0 ₽ (ppc.world, официальная фича). HIGH.
- **Kill**: AI-лицо без disclosure → понижающий коэффициент ×0.5 (внутренний playbook; первичный VK-источник = null). MED. Вотермарка TikTok → понижение рекомендаций. MED.

### 1.3 Instagram Reels *(только FYI — не launch-площадка, см. §4)*
1. **Watch time (total + replay rate)** — #1 ranking factor (Adam Mosseri, январь 2025). HIGH.
2. **Skip rate первых 3 сек** — первое измерение; канонический вес: skip rate > shares > likes > saves > reposts > comments (getreelyze). MED.
3. **DM shares (sends)** заменили saves как топ-сигнал 2026 (1kreach). MED.
4. **Субтитры** — ranking factor (Mosseri; 80% смотрят без звука). MED.
5. **Оригинальность**: ≥10 репостов/30 дней → исключение из рекомендаций (creatorflow 2026-08-24). MED.
- **Kill**: Meta = экстремистская организация в РФ; реклама запрещена; VPN-only аудитория. **HIGH (legal).**

### 1.4 TikTok *(carrier only — см. §4)*
1. **Completion ~70%** — барьер для выхода за пределы тестовой выборки (posteverywhere 2026-05-23). MED.
2. **Watch time первых секунд** — самый сильный сигнал (Hootsuite 2026-07-04). MED.
3. **Три семейства сигналов**: user interactions, video information, device/account (webtonic 2026-07-31, официальная документация). HIGH.
4. **Shares/saves > likes** (posteverywhere). MED.
5. **Follower-first testing 2026**: сначала на подписчиках, потом расширение (posteverywhere). MED.
- **Kill**: shadowban при повторных дублях/спам-действиях; восстановление 48–72ч пауза + 1 оригинал/день 5–7 дней (dicloak). MED.

### 1.5 Telegram *(нет алгоритмической ленты)*
1. **Лента хронологическая** — все подписчики видят все посты. Алгоритм работает в поиске, «Похожих каналах», Explore (palladium-smm, smm-marketing). HIGH/MED.
2. **ERR (Engagement Rate by Reach)** — ключевая метрика; норма 15–35%, <10% — проблема (smm-marketing). MED.
3. **Пересылки (репосты)** — самый сильный сигнал; эффективнее реакций в 3–5 раз (palladium-smm). MED.
4. **Порог критичности**: до 1000 подписчиков алгоритм не помогает; нужен стартовый буст (посевы/взаимопиар). MED.
5. **Взаимопиар** между каналами схожего размера — бесплатно; эффект от ~500+ подписчиков (ganiev-marketing). MED.
- **Kill**: накрутка ботов → теневой бан в поиске; ФАС с 2026-03 считает рекламу в TG нарушением (переходный период до конца 2026). HIGH/MED.

---

## 2. Механика первых часов / посев

| Площадка | Тестовый пакет | Критичное окно | Повторная дистрибуция | Confidence |
|---|---|---|---|---|
| YT Shorts | explore-выборка (сотни) | первые 48 часов | возможна спустя дни/недели (LOW) | HIGH (механика) / MED (окно) |
| VK Клипы | ~200–300 показов | первый час | возможна через 24+ ч (HIGH) | MED |
| TikTok | ~200–500 зрителей | первый час (15% ER = экспоненциальный рост) | возможна при тренде (LOW) | MED |
| IG Reels | маленький seed не-подписчикам | первый час | Trial Reels = официальный тест (HIGH) | MED/HIGH |
| Telegram | нет ленты | нет (ERR накапливается) | через пересылки, поиск | HIGH |

**Вывод:** для YT/VK/TT первый час критичен — публикация в активное окно аудитории + ответы на комментарии первые 30–60 минут. Для TG — накопление ERR через регулярность и пересылки.

---

## 3. Безопасный warm-up каналов (без накруток)

| Площадка | Тактика | Срок до 1k | Confidence |
|---|---|---|---|
| **YT Shorts** | 1 видео/нед → 6–18 мес; 2–3/нед → 3–8 мес; ежедневно → 1–4 мес. SEO-заголовки по запросам <100 символов (statzen 2026). | 3–8 мес при 2–3/нед | MED |
| **VK Клипы** | 3–5 клипов/нед первые 2 недели + 1–2 поста/день в ленту + ответы на комментарии. Клипы — самый доступный канал для новых групп (rbc.ru 2026). | 2–4 нед первые результаты, 2–3 мес стабильный рост | MED |
| **TikTok** | 1–3 видео/день; TikTok активно продвигает новые аккаунты (palladium-smm). | 1–3 мес (socialz 2026-03-09) | MED |
| **IG Reels** | Warm-up 7–14 дней: профиль, стабильное устройство, поведение в нише, первый Reel не раньше Day 7 (genviral, tokportal). | 8–16 нед при 4–7 Reels/нед | MED |
| **Telegram** | SEO названия + описание (255 симв., 3–5 ключевых) + 10–15 сильных постов ДО посевов; кросс-промо с 5–10 каналами (ganiev). | 3–6 мес органика, 1–2 мес с бюджетом 5–10К ₽/мес | MED |

**Anti-schemes (запрещено):** платные боты/накрутка (YouTube Fake Engagement Policy — termination; VK фильтрует); sub4sub/engagement pods; watermarked ре-аплоады; mass follow/unfollow; неофициальные API. Confidence: HIGH (официальные политики).

---

## 4. Fit-ранжирование для волны 1 (каналы из CHANNELS_READY_MAP_0610)

| # | Канал | Fit | Статус 07.10 | Действие |
|---|---|---|---|---|
| 1 | **VK Клипы** | **HIGH** | R (publication-ready, owner GO) | Week 1: 3 клипа/нед, trend-hints, плейлисты |
| 2 | **YouTube Shorts** | **HIGH** | R | Week 1: 3 клипа/нед, VVSA-метрика, SEO-заголовки |
| 3 | **Telegram ×3** | **MED** (hub) | R | Немедленно: нативные клипы + cross-links с VK/YT; взаимопиар с месяца 2 |
| 4 | **RuTube** | MED-HIGH | G (нужна проверка порога 5 000 views) | Week 2: старт с SEO-названиями, 24h velocity через TG |
| 5 | **Dzen** | LOW-MED | — | Только если marginal cost ≈ 0; funnel на TG/VK |
| 6 | **TikTok** | LOW (carrier) | R* (nickname fix после 08.10) | Только после отдельного GO владельца; VPN-риск |
| 7 | **Instagram** | **LOW (kill)** | X (legal) | Dormant; не launch-площадка |
| 8 | **Pinterest ×2** | out of scope | — | Card E |

**30-дневный лаунч-план (из GROWTH_SCHEMES_0610 §4):**
- **Week 1:** VK Клипы + YT Shorts only, 3 клипа/нед, native uploads, trend-hints VK, per-platform captions, cross-post в TG.
- **Week 2:** + RuTube с SEO-оптимизацией; 24h velocity через TG (не боты).
- **Week 3:** ревью VVSA (YT) и retention (VK); kill худшего формата, double лучшего; каденция сохраняется.
- **Week 4:** если клип прошёл 2-й тест-круг (>10x baseline), делать серию; драфт взаимопиар-листа TG на месяц 2.
- **Gate to month 2:** ≥1 клип с органической дистрибуцией за пределы seed-аудитории на VK или YT; иначе — rework форматов перед масштабированием до 11/нед.

---

## 5. Стоп-факторы / бан-риски (сводка)

| Риск | Площадка | Confidence | Источник |
|---|---|---|---|
| Inauthentic Content Policy (массовый шаблон) | YouTube | HIGH | support.google.com/youtube/answer/1311392, 2025-07-15 |
| Fake Engagement Policy (боты) | YouTube | HIGH | support.google.com/youtube/answer/3399767 |
| AI-лицо без disclosure | VK | MED | внутренний playbook; первичный VK = null |
| Вотермарка чужой платформы | VK, IG, TikTok | MED-HIGH | likelab.pro; Mosseri; TikTok FYF Standards |
| Репосты ≥10/30 дней | Instagram | MED | creatorflow 2026-08-24 |
| Shadowban (дубли, спам) | TikTok | MED | ru.dicloak.com |
| Накрутка ботов | Telegram | MED | smm-marketing.com.ua |
| ФАС по TG-рекламе | Telegram | MED | klerk.ru 2026-06-15 (переходный период до конца 2026) |
| Meta = экстремистская | Instagram | HIGH | companies.rbc.ru 2026-07-16; lenta.ru 2026-03-30 |
| Перезалив удалённого без изменений | VK, TikTok | LOW-MED | аналогия; dicloak для TT |

---

## 6. Частота и время публикаций (RU, МСК)

| Площадка | Частота (новый аккаунт) | Лучшее время | Confidence |
|---|---|---|---|
| VK Клипы | 1–2/день (полный конвейер); 2–3/нед минимум | будни 18:00–22:00; вс 20:00 (+35%) | HIGH (LiveDune 30 млн постов) |
| YT Shorts | 3–5/нед | будни 16:00–20:00 | MED (calcal.ru) |
| TikTok | 1–3/день | будни 18:00–22:00 | MED (calcal.ru) |
| IG Reels | 4–7/нед | сб 17:00–18:00; будни 18:00 | HIGH (LiveDune 3,4 млн Reels) |
| Telegram | 3–5/нед (экспертный) | вт–чт 09:00–11:00, 19:00–21:00 | MED (ganiev, palladium) |
| Pinterest | 5–10 пинов/нед | null (RU-специфика) | LOW |

---

## 7. Пробелы (null — не восполнять догадкой)

1. **Telegram native video / кружки / видеопосты**: механика дистрибуции видео внутри TG (не ссылки на внешние клипы) = null. Нет исследований 2025–2026 в каноне; web-search 08.10 пуст. План: мониторить через competitor-news-monitor при запуске TG-линии.
2. **Gaming-ниша hooks**: VIEWS_GROWTH_PLAYBOOK §4.1 даёт 7 шаблонов, но clipspeed reversal (scenario/POV слаб в gaming/general pool 0.57x) означает, что gaming-хуки требуют A/B-теста. Точные gaming-specific lift-цифры = null.
3. **YT/VK warm-up (не холодный старт, а именно «прогрев» перед активным постингом)**: данные только для IG (7–14 дней). Для YT/VK — null (предположительно не требуется, но не подтверждено).
4. **Pinterest RU**: частота/время = null; доступность у операторов нестабильна (prostotex 2026-07-02, HIGH как риск).
5. **Официальные пороги VK Клипы** (first-3s, дистрибуция): VK не публикует цифры = null.
6. **Официальный порог VVSA** = null (70% — отраслевой ориентир из Analytics).

---

## 8. Источники (ключевые, полный список в каноне)

| Источник | Дата | Confidence | Что даёт |
|---|---|---|---|
| ppc.world/articles/kak-rabotayut-algoritmy-vkontakte-v-2026-godu/ | 2026-07-08 | HIGH | VK сигналы, ссылки на vk.com/legal/recommendations |
| vidiq.com/blog/post/youtube-shorts-algorithm/ | 2025-12-29 | HIGH | Shorts explore/exploit, цитирует Todd Sherman |
| go-viral.app/blog/youtube-shorts-algorithm-2026/ | 2026-03-14 | MED | Satisfaction Signals, 74% non-subscriber views |
| quso.ai/research/video-retention-benchmarks | 2026-06-29 | HIGH | 508k постов, retention benchmarks |
| creatorflow.so/blog/instagram-algorithm-2026/ | 2026-08-24 | MED | IG originality, Mosseri signals |
| ganiev-marketing.ru/prodvizhenie-telegram-kanala/ | 2026 | MED | TG ERR, взаимопиар, холодный старт |
| klerk.ru/user/2646643/695747/ | 2026-06-15 | MED | TG посевы стоимость, ФАС флаг |
| LiveDune via ppc.world | 2025-12-18 | HIGH | VK время публикаций, 30 млн постов |
| LiveDune via likeni.ru | 2026-03-11 | HIGH | IG Reels время, 3,4 млн Reels |
| support.google.com/youtube/answer/1311392 | 2025-07-15 | HIGH | Inauthentic Content Policy |
| support.google.com/youtube/answer/3399767 | — | HIGH | Fake Engagement Policy |

---

## Handoff

- **Внедрение:** §1–§3 → skill video-direction (хуки, структура); §3 → qa-preflight (чек-лист); §4 → CLIPS_PRODUCTION_PLAN_0610 (G1–G5) как основание для Week 1–4; §5 → compliance-чек перед каждой публикацией.
- **Связь с каноном:** этот бриф не заменяет `PLATFORM_ALGORITHMS.md` (полная детализация с URL на каждый тезис) и `VIEWS_GROWTH_PLAYBOOK.md` (20 техник + хук-библиотека + A/B-план). Это executive summary для быстрого решения «куда и как постить в первые 30 дней».
- **Следующий шаг:** company → owner: GO на публикацию Week 1 (VK Клипы + YT Shorts, 3 клипа/нед, Wardogs-линия). Остальное — по гейту месяца 2.
- **Расходы:** 0 ₽, research-only. Финансовый scope: null (не применимо).

*Файл: `C:/Users/max/Desktop/all/ventures/docs/video/DISCOVERY_BRIEF_2026-10.md`*
