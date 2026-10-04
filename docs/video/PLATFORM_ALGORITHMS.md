# PLATFORM_ALGORITHMS.md — Алгоритмы площадок волны 1 (VK Клипы, YouTube Shorts, TikTok, Instagram Reels, Telegram, Pinterest)

Статус: research deliverable для SPEC_I2, без публикаций. Дата среза: 2026-09-24. Формат: по каждой площадке 6 блоков, каждый тезис с URL + дата + confidence (HIGH/MED/LOW/null). Цифры без источника = null.

Confidence-шкала:
- HIGH — подтверждено официальной документацией платформы ИЛИ исследованием ≥30К единиц контента ИЛИ несколькими независимыми отраслевыми источниками за 2025–2026.
- MED — 1 независимое исследование / несколько отраслевых гайдов, без первичной документации.
- LOW — фольклор SMM-блогов, не подтверждено первичкой; помечается как ориентир для теста.

---

## 1. VK Клипы / VK Видео

### 1.1 Что ранжирует алгоритм 2025–2026
- Первые 3–5 секунд — критическая метрика: если человек смахнул на 3-й секунде, просмотр не засчитывается, и алгоритм получает сигнал ограничить показ. URL: https://ppc.world/articles/kak-rabotayut-algoritmy-vkontakte-v-2026-godu/, 2026-07-08; https://dtf.ru/howto/4808137-kak-uvelichit-prosmotry-vk-algoritmy-i-top-16-servisov, 2026-02-25. Confidence: HIGH (два независимых RU-источника).
- Алгоритм MMLM (multi-modal) VK учитывает: досмотр до конца (completion), повторный просмотр (loop), переход в профиль после просмотра, реакции, репосты, комментарии. URL: https://likelab.pro/blog/algoritmy-vk-klipy, 2026-06-08; https://fathersmm.ru/blog/vk-clips-guide, 2026-06-01. Confidence: MED.
- Реакции на посты после изменений 2025 распределяются равномернее в течение дня; качество контента превалирует над временем публикации. URL: https://ppc.world/news/luchshee-vremya-dlya-postinga-vkontakte-posle-izmeneniya-algoritmov-issledovanie-livedune/ (исследование 30 млн постов, сент-ноя 2025). Confidence: HIGH.

### 1.2 Механика посева
- Test-аудитория: новый клип получает стартовый пакет показов (порядка 200–300, ориентир из агентских кейсов) на случайной выборке; если first-3s и completion выше порога — охват расширяется ступенями. URL: https://zapuski.com/blog/algoritmy-vk-2026-rekomendacii.html, 2026-08-24 (кейс "застревали на 200-300"). Confidence: MED.
- First-hour окно: первый час после публикации решает, пойдёт ли клип в ленту рекомендаций. URL: https://fathersmm.ru/blog/vk-clips-guide, 2026-06-01. Confidence: MED.
- Повторная дистрибуция: возможен буст охвата через 24+ часов после публикации (новая лента ВК 2025). URL: https://ppc.world/news/luchshee-vremya-dlya-postinga-vkontakte-posle-izmeneniya-algoritmov-issledovanie-livedune/. Confidence: HIGH.

### 1.3 За что режет охваты
- AI-лицо в клипах → понижающий коэффициент охвата ×0.5 (из VIEWS_GROWTH_PLAYBOOK §VK: VK явно детектирует генерированные лица и понижает дистрибуцию). Confidence: MED (зафиксировано во внутреннем playbook, первичный VK-источник = null).
- Вотермарка чужой платформы (TikTok-лого на клипе) — понижение рекомендаций. URL: https://likelab.pro/blog/algoritmy-vk-klipy. Confidence: MED.
- Неоригинал/репосты без добавленной ценности — алгоритм не продвигает. URL: https://likelab.pro/blog/algoritmy-vk-klipy. Confidence: MED.
- Для VK-партнёрки (монетизации): кампанийные нарезки не считаются авторским контентом (внутреннее правило C MONETIZATION_EXECUTION_PLAN). Confidence: HIGH (внутреннее compliance-правило).

### 1.4 Холодный старт (первые 1k подписчиков)
- Алгоритм слабо доверяет аккаунтам без истории: новые профили получают пониженный стартовый охват. Тактика — накопление поведенческой истории + регулярные публикации. URL: https://palladium-smm.com/blog/vkontakte-klipy-prodvizhenie, 2026. Confidence: MED (предостережение: источник — SMM-панель, интерпретация с поправкой).
- Рабочий паттерн: 3–5 клипов в неделю первые 2 недели + 1–2 поста в день в ленту + активные ответы на комментарии. Первые результаты — 2–4 недели, стабильный органический рост — 2–3 месяца. URL: https://companies.rbc.ru/news/hE2ePBKNsK/prodvizhenie-gruppyi-v-vk-s-nulya-kak-nabrat-pervyih-1000-podpischikov/, 2026. Confidence: MED.
- VK Клипы — самый доступный канал органического охвата для новых групп: алгоритм активно показывает клипы не-подписчикам. URL: https://companies.rbc.ru/news/hE2ePBKNsK/. Confidence: MED.

### 1.5 Частота и время (RU)
- Оптимальная частота: 1–2 клипа/день при полном конвейере; при меньшей частоте (2–3 в неделю) рост замедляется. URL: https://palladium-smm.com/blog/vkontakte-klipy-prodvizhenie. Confidence: MED.
- Время: VK Клипы — будни 18:00–22:00 МСК, выходные 11:00–23:00; лучшие дни — чт–сб. URL: https://calcal.ru/vremya-publikaczii-smm (Mediascope 2025). Confidence: MED.
- Исследование LiveDune (30 млн постов, 2025): общий вечерний пик VK 16:00–21:00, лучший слот — воскресенье 20:00 (+35% к среднему). URL: https://ppc.world/news/luchshee-vremya-dlya-postinga-vkontakte-posle-izmeneniya-algoritmov-issledovanie-livedune/. Confidence: HIGH для постов; для Клипов переносится с оговоркой (LOW→MED).

### 1.6 Табу и бан-риски
- Публикация контента с вотермарками чужих площадок. Confidence: MED.
- AI-лица без соответствующего disclosure (риск понижающего коэффициента + репутационный). Confidence: MED.
- Накрутка ботов — VK хорошо фильтрует неживой трафик, бан возможен. URL: https://palladium-smm.com/blog/vkontakte-klipy-prodvizhenie. Confidence: MED.
- Перезалив удалённого видео без изменений — null (нет прямых данных по VK; по аналогии с другими платформами считать риском).

---

## 2. YouTube Shorts

### 2.1 Что ранжирует алгоритм 2025–2026
- VVSA (Viewed vs Swiped Away) — первичный сигнал: доля зрителей, которые выбрали смотреть, а не свайпнуть. Порог здоровья канала — VVSA ≥70%. URL: https://tubecreatorkit.com/guides/how-to-rank-youtube-shorts-in-2026/; https://www.tubeanalytics.net/blog/youtube-shorts-algorithm-2026. Confidence: HIGH (несколько отраслевых источников, метрика доступна в YouTube Analytics).
- Satisfaction Signals > сырой watch time: YouTube 2026 ранжирует по удовлетворённости (completion, replays, survey signals), а не только по времени. URL: https://www.go-viral.app/blog/youtube-shorts-algorithm-2026/. Confidence: MED.
- Дополнительные сигналы: watch time, replays (loop), completion rate, персонализация по истории просмотров, соответствие трендам. URL: https://www.tubeanalytics.net/blog/youtube-shorts-algorithm-2026. Confidence: MED.
- "1-second decision": решение зрителя принимается за первую секунду. URL: https://likes.io/blog/youtube-shorts-algorithm-2026. Confidence: MED.
- Внутренний playbook (VIEWS_GROWTH_PLAYBOOK) — stop rules: два клипа подряд с VVSA<50% или first-3s completion<60% → стоп серии, переписать frame 1. Confidence: HIGH (внутренний стандарт).

### 2.2 Механика посева
- Explore/Exploit фазы: новый ролик получает explore-пакет на случайной тестовой выборке, затем exploit (масштабирование) при прохождении порога. URL: https://www.go-viral.app/blog/youtube-shorts-algorithm-2026/. Confidence: MED.
- Первые 48 часов критичны для распределения; в этот период важно собрать органические реакции. URL: https://statzen.ru/blog/kak-nabrat-1000-podpischikov-youtube, 2026. Confidence: MED.
- Повторная дистрибуция: Shorts могут "оживать" спустя дни/недели, если меняется контекст запросов/трендов (внутренний playbook + отраслевые наблюдения). Confidence: LOW.

### 2.3 За что режет охваты
- **Inauthentic Content Policy (15.07.2025)** — переименованная "repetitious content": массовый, повторяющийся контент без оригинальности лишает монетизации НА УРОВНЕ КАНАЛА, не только отдельного видео. URL: https://support.google.com/youtube/answer/1311392?hl=en-gb, 2025-07-15; https://ppc.land/youtube-clarifies-inauthentic-content-policy-changes/, 2025-07-15. Confidence: HIGH (официальная политика).
- Кампанийные нарезки Klipni с баннером = рекламный контент: НЕ считаются нарушением сами по себе, но массовый шаблонный выпуск без человеческого слоя подпадает под inauthentic. Внутреннее правило: ручной выбор хука, контекста, вычитка. Confidence: HIGH (комбинация политики + внутренний стандарт).
- Вотермарка TikTok — YouTube официально понижает рекомендации роликов с чужими вотермарками. Confidence: MED (общепризнанный отраслевой факт, прямой URL на YouTube Help не получен в этом исследовании — null).
- Удаление и перезалив: YouTube явно не наказывает за удаление, но перезалив того же контента без изменений помечается как дубликат. Confidence: LOW.

### 2.4 Холодный старт (первые 1k)
- Алгоритм не знает, кому показывать видео нового канала: первые 10–20 видео тестируются на выборках в сотни людей. URL: https://statzen.ru/blog/kak-nabrat-1000-podpischikov-youtube. Confidence: MED.
- Поиск — главный источник трафика для нулевого канала: SEO-заголовки по запросам < 100 символов, ключевой запрос в первые 100 символов описания. URL: https://statzen.ru/blog/kak-nabrat-1000-podpischikov-youtube. Confidence: MED.
- Скорость роста (статистика по нишам): 1 видео/мес → 2–4 года до 1k; 1/нед → 6–18 мес; 2–3/нед → 3–8 мес; ежедневно → 1–4 мес. URL: https://statzen.ru/blog/kak-nabrat-1000-podpischikov-youtube. Confidence: MED (обобщение, не конкретное исследование).
- Для Shorts на новом канале: VVSA ≥70% на первых роликах важнее подписок — алгоритм начинает воспринимать канал как "активный" после первой 1000 + 4000 часов просмотра (монетизационный порог). URL: https://statzen.ru/blog/kak-nabrat-1000-podpischikov-youtube. Confidence: HIGH для порога, MED для тактики.

### 2.5 Частота и время (RU)
- Частота для Shorts: 3–5 в неделю (calcal.ru), 1–2 в неделю для длинных видео. URL: https://calcal.ru/vremya-publikaczii-smm. Confidence: MED.
- Пик RU-аудитории YouTube: будни 16:00–20:00 МСК, выходные 10:00–14:00 и 16:00–22:00; лучшие дни — чт–сб. URL: https://calcal.ru/vremya-publikaczii-smm (Mediascope 2025). Confidence: MED.
- Суточная аудитория YouTube в РФ в 2025 упала до DAU 21 млн (с 42 млн в 2024), MAU 67–82 млн; среднее время 17 мин/день (-67%). URL: https://ppc.world/articles/auditoriya-devyati-krupneyshih-socsetey-v-rossii-v-2024-godu-issledovaniya-i-cifry/, 2026-02-16. Confidence: HIGH (Mediascope/Brand Analytics). Интерпретация: Shorts остаются главным выгодополучателем перехода аудитории Instagram*, но объём внимания в РФ сжимается.

### 2.6 Табу и бан-риски
- Inauthentic Content Policy — риск потери монетизации всего канала. Confidence: HIGH.
- Массовый AI-slop без человеческого слоя — прямой риск под политику 15.07.2025. Confidence: HIGH.
- Кликбейт-несоответствие хука payoff — накапливаемый негатив satisfaction signals. Confidence: MED.
- Для кампаний Klipni: публикация без required disclosure/erid-маркировки = юридический риск, не алгоритмический. Confidence: HIGH (внутренний compliance).

---

## 3. TikTok

### 3.1 Что ранжирует алгоритм 2025–2026
- Completion rate — барьер 2026 ~70% (для коротких роликов) для выхода за пределы тестовой выборки. URL: https://posteverywhere.ai/blog/how-the-tiktok-algorithm-works, 2026-05-23; https://www.socialync.io/blog/tiktok-algorithm-2026-what-works-now, 2026-07-06. Confidence: MED (отраслевые гайды, не первичная документация).
- Watch time в первые секунды — самый сильный сигнал (Hootsuite 2026). URL: https://blog.hootsuite.com/tiktok-algorithm/, 2026-07-04. Confidence: MED.
- Три семейства сигналов по документации TikTok: user interactions, video information, device/account settings (последнее — минимальный вес). Follower count и прошлые хиты — НЕ прямой фактор ранжирования. URL: https://www.webtonic.io/blog/tiktok-algorithm, 2026-07-31. Confidence: HIGH (ссылается на официальную документацию TikTok).
- Shares и saves весят выше likes в 2026. URL: https://posteverywhere.ai/blog/how-the-tiktok-algorithm-works. Confidence: MED.
- Niche relevance > broad reach (например #BookTok): глубина в нише важнее ширины. URL: https://blog.hootsuite.com/tiktok-algorithm/. Confidence: MED.
- Follower-first testing: 2026 алгоритм сначала тестирует на подписчиках, потом расширяет. URL: https://posteverywhere.ai/blog/how-the-tiktok-algorithm-works. Confidence: MED.

### 3.2 Механика посева
- Test pool → expansion: если completion ≥~35% И хотя бы один engagement-сигнал (shares/saves/deep comments) ≥~1.5% от зрителей, ролик переходит в expansion pool 5k–10k зрителей. URL: https://likes.io/blog/tiktok-algorithm-2026. Confidence: MED.
- First hour test window: первая реакция подписчиков в первый час определяет дальнейшую дистрибуцию. URL: https://www.socialync.io/blog/tiktok-algorithm-2026-what-works-now. Confidence: MED.
- Повторные волны: TikTok может рециркулировать ролик спустя дни/недели, если тренд/аудио набирает обороты. Confidence: LOW.

### 3.3 За что режет охваты
- Повторная публикация почти дублирующихся клипов, ежедневное использование одного и того же крючка, низкое изменение в монтаже → снижает право на рекомендации. URL: https://ru.dicloak.com/blog-detail/tiktok-shadowbanned-how-to-confirm-it-recover-reach-and-prevent-it. Confidence: MED.
- Репосты с вотермарками и скопированные озвучки мешают охвату. URL: ru.dicloak.com (там же). Confidence: MED.
- Удаление и повторная загрузка того же видео = сигнал нарушения, может усугубить shadowban. URL: https://ru.dicloak.com/blog-detail/cracking-the-code-the-ultimate-guide-to-the-tiktok-shadowban-in-2026. Confidence: MED.
- Спам-действия (поды вовлечённости, массовые подписки/отписки, автолайки) — прямой риск shadowban. URL: ru.dicloak.com. Confidence: MED.
- Видео 15–35 сек — рабочая длина для восстановления охвата; строго 3–5 нишевых хэштегов, без мешанины. URL: ru.dicloak.com. Confidence: MED.

### 3.4 Холодный старт (первые 1k)
- 1–3 видео/день на старте; TikTok активно продвигает новые аккаунты. URL: https://palladium-smm.com/blog/pervye-1000-podpischikov. Confidence: MED (SMM-источник).
- Большинство авторов достигают 1k за 1–3 месяца при 1–3 публикациях/день. URL: https://socialz.ai/blog/how-to-get-1000-followers-on-tiktok, 2026-03-09. Confidence: MED.
- Cold start типичен для всех платформ: первые 72 часа алгоритм решает, показывать ли дальше; ключевые сигналы — completion, rewatches, saves, shares, profile visits, follow-through. URL: https://1kreach.com/blog/cold-start-problem-first-1000-followers-2026, 2026. Confidence: MED.
- Для РФ-контура: TikTok в РФ ограничен, требуется иностранный регион аккаунта + VPN (внутреннее решение MONETIZATION_EXECUTION_PLAN — TikTok только после отдельного GO владельца). Confidence: HIGH.

### 3.5 Частота и время (RU)
- Оптимум 1–3 видео/день (алгоритм любит частоту). URL: https://calcal.ru/vremya-publikaczii-smm. Confidence: MED.
- Пик RU-аудитории: будни 18:00–22:00 МСК, выходные 11:00–14:00 и 19:00–23:00; лучшие дни пт–вс. URL: https://calcal.ru/vremya-publikaczii-smm. Confidence: MED.
- Дополнительно (для зарубежного контура): TikTok вознаграждает раннюю скорость — публикация при пробуждении аудитории. URL: https://tareno.co/ru/best-time-to-post, 2026. Confidence: MED.
- Важно: MAU TikTok в РФ 2025 ~65 млн, DAU ~33 млн (больше YouTube). URL: https://ppc.world/articles/auditoriya-devyati-krupneyshih-socsetey-v-rossii-v-2024-godu/. Confidence: HIGH.

### 3.6 Табу и бан-риски
- Shadowban — временный (несколько дней — недели), восстановление через удаление нарушающего контента + пауза 48–72ч + 1 оригинальное видео/день 5–7 дней. URL: ru.dicloak.com. Confidence: MED.
- Массовый кросс-постинг одного и того же файла на много аккаунтов без вариации — сигнал фермы. URL: https://www.tokportal.com/learn/low-instagram-reels-reach-new-account (по аналогии с IG). Confidence: MED.
- Контент, нарушающий Community Guidelines — риск перманентного бана после повторных нарушений. Confidence: HIGH (официальные правила TikTok).
- Для нашего контура: erid-контент в TikTok допустим на разрешённых Klipni-площадках; VPN-стабильность и регион аккаунта — отдельный риск-фактор блокировки аккаунта. Confidence: HIGH (внутренний compliance).

---

## 4. Instagram Reels

### 4.1 Что ранжирует алгоритм 2025–2026
- Watch time (total seconds watched + replay rate) — #1 ranking factor, подтверждено Adam Mosseri (январь 2025, подтверждено в 2026). URL: https://www.dataslayer.ai/blog/instagram-algorithm-2025-complete-guide-for-marketers, 2026-06-29. Confidence: HIGH (слова Mosseri).
- Completion rate: ролик, досмотренный до конца 1000 людьми, получит большую дистрибуцию, чем просмотренный частично. URL: https://reshmashaji.com/blog-instagram-reels-algorithm-2026/, 2026-06-08. Confidence: MED.
- DM shares (sends) заменили saves как топ-сигнал для Reels в 2026. URL: https://1kreach.com/blog/cold-start-problem-first-1000-followers-2026. Confidence: MED.
- Skip rate первых 3 секунд — первое, что меряет алгоритм; канонический порядок весов: skip rate > shares > likes > saves > reposts > comments. URL: https://getreelyze.com/guides/grow-instagram-from-zero-with-reels. Confidence: MED.
- Captions/субтитры: большинство смотрят без звука; Mosseri публично назвал субтитры ranking factor. URL: https://orangemonke.com/blogs/instagram-algorithm/, 2026-07-16. Confidence: MED.
- Оригинальный контент получает на 40–60% больше дистрибуции, чем репосты; ≥10 репостов за 30 дней → исключение из рекомендаций. URL: https://creatorflow.so/blog/instagram-algorithm-2026/, 2026-08-24. Confidence: MED.

### 4.2 Механика посева
- Reels показываются НЕ-подписчикам по умолчанию: главный канал роста новых аккаунтов. URL: https://getreelyze.com/guides/grow-instagram-from-zero-with-reels. Confidence: HIGH (логика продукта, повторяется в нескольких источниках).
- Test pool: новый аккаунт получает маленькую начальную аудиторию; при сильных сигналах (watch time, replays, saves, shares, profile actions) дистрибуция расширяется. URL: https://www.tokportal.com/learn/low-instagram-reels-reach-new-account. Confidence: MED.
- Longer Reels (до 3 мин) теперь достигают не-подписчиков. URL: https://creatorflow.so/blog/instagram-algorithm-2026/. Confidence: MED.

### 4.3 За что режет охваты
- Репосты (≥10 за 30 дней) → исключение из рекомендаций. URL: creatorflow.so. Confidence: MED.
- Вотермарка TikTok — известный триггер понижения Reels. Confidence: MED (общепризнанно, точный URL на Instagram Help не получен — null).
- Mass-upload одного и того же ассета через несколько аккаунтов без вариации — сигнал фермы. URL: tokportal.com. Confidence: MED.
- Редактирование подписи после публикации на новом аккаунте — алгоритм воспринимает подозрительно. URL: https://www.genviral.io/blog/warm-up-instagram-account. Confidence: MED.
- Планировщики вместо нативного постинга на раннем этапе — слабый сигнал, повышает риск action block. URL: genviral.io. Confidence: MED.
- erid/рекламный контент — внутреннее правило E: не публикуется в Instagram вообще. Confidence: HIGH (внутренний compliance).

### 4.4 Холодный старт (первые 1k)
- Warm-up 7–14 дней обязателен перед активным постингом: полный профиль, стабильное устройство, поведение в нише (смотреть/сохранять Reels своей тематики), постепенный рост объёма. URL: https://www.tokportal.com/learn/instagram-account-warming-strategy-2026; https://www.genviral.io/blog/warm-up-instagram-account. Confidence: MED.
- 7-day cycle (Genviral): день 1 профиль+просмотр, день 7 — первый Reel; до этого — фото/Stories, никаких Reels раньше Day 7. URL: genviral.io. Confidence: MED.
- 4–7 Reels в неделю в первые 60–90 дней в одной узкой нише. URL: getreelyze.com. Confidence: MED.
- Типичный срок до 1k подписчиков с нуля: 8–16 недель при 4–7 Reels/неделю; нелинейный рост (первые 100 — самые медленные). URL: getreelyze.com. Confidence: MED.
- Breakout pattern: один Reel, пересекший 10k–50k не-подписных просмотров, может дать +несколько сотен подписчиков за раз. URL: getreelyze.com. Confidence: MED.
- Хэштеги: до 5 нишевых; больше — снижение охвата. URL: getreelyze.com. Confidence: MED.

### 4.5 Частота и время (RU)
- Исследование LiveDune (3,4 млн Reels в 62К аккаунтах, 2025): лучший слот — суббота 17:00–18:00; будни пик ~18:00 (85–89% от субботнего максимума); худшее — 06:00 (~60%), антирекорд — понедельник 06:00 (55%). После 20:00 — спад, к полуночи 65–70%. URL: https://www.likeni.ru/events/v-kakoe-vremya-luchshe-publikovat-reels-issledovanie-livedune/, 2026-03-11. Confidence: HIGH (большая выборка).
- Instagram* RU-аудитория 2025: 19 млн активных авторов, 51,5 млн публикаций/мес. URL: ppc.world (Brand Analytics). Confidence: HIGH. Примечание: Mediascope с 2025 не включает Instagram* в популярные соцсети РФ — оценка аудитории требует осторожности.
- Частота: 3–4 Reels в неделю + 1 пост в ленту + 3–5 Stories/день. URL: palladium-smm.com/blog/pervye-1000-podpischikov. Confidence: MED.

### 4.6 Табу и бан-риски
- Action block для новых аккаунтов — главный риск (Genviral: топ-1 причина — постинг Reels до Day 7). Confidence: MED.
- Создание аккаунта на домашнем Wi-Fi вместо мобильной сети — триггер для флага. URL: genviral.io. Confidence: MED.
- Bio link до ~Day 30 на холодном аккаунте — риск. URL: genviral.io. Confidence: MED.
- Ранняя интеграция Threads до прогрева — риск. URL: genviral.io. Confidence: MED.
- Массовые действия (>150 действий/день в первый месяц) — спам-флаг. URL: genviral.io. Confidence: MED.
- Для нашего контура: Instagram* признана экстремистской в РФ, erid-контент не публикуется (правило E), требуется отдельное решение владельца. Confidence: HIGH.

---

## 5. Telegram

### 5.1 Что ранжирует "алгоритм" 2025–2026
- Принципиально: у Telegram НЕТ алгоритмической ленты — лента подписок хронологическая. Все подписчики видят все посты. URL: https://www.smm-marketing.com.ua/blog/algoritmy-telegram-2026-kak-oni-rabotaut-i-chto-realno-vliyaet-na-prodvizhenie. Confidence: HIGH.
- Алгоритм работает в трёх местах: (1) поиск внутри мессенджера (SEO-логика: название/описание с ключевыми словами), (2) рекомендации "Похожие каналы" (Similar channels), (3) раздел Explore ("Что интересного"). URL: https://palladium-smm.com/blog/kak-rabotaet-algoritm-telegram; ganiev-marketing.ru. Confidence: MED.
- Ключевые метрики ранжирования в поиске: скорость роста подписчиков, ERR (Engagement Rate by Reach = просмотры/подписчики), частота публикаций. URL: https://ganiev-marketing.ru/prodvizhenie-telegram-kanala/. Confidence: MED.
- ERR норма для здорового канала: 15–35%; <10% — проблема (контент или боты); >40% — очень хорошо. URL: smm-marketing.com.ua. Confidence: MED.
- Пересылки (репосты) — самый сильный сигнал: увеличивают охват в 3–5 раз эффективнее реакций. URL: palladium-smm.com. Confidence: MED.

### 5.2 Механика посева
- "Похожие каналы" — бесплатный органический трафик: Telegram рекомендует канал при подписке на похожий. Влияет: тематическая близость, ERR, стабильность роста, отсутствие жалоб. URL: smm-marketing.com.ua. Confidence: MED.
- Explore ("Что интересного"): для попадания нужна модерация (нет спама/нарушений) + минимум 100–500 подписчиков. Новые каналы получают временный буст первые 30 дней. URL: palladium-smm.com. Confidence: MED.
- Снежный ком: чем быстрее растёт канал, тем больше органических подписчиков получает через рекомендации. URL: palladium-smm.com. Confidence: MED.

### 5.3 За что режет охваты
- Накрутка ботов: резкий скачок подписчиков без активности → теневой бан в поиске. URL: smm-marketing.com.ua. Confidence: MED.
- История массовых жалоб — снижение ранжирования. URL: smm-marketing.com.ua. Confidence: MED.
- Непоследовательный постинг (неделя тишины → 10 постов за день) — снижение охвата следующих постов. URL: palladium-smm.com. Confidence: MED.
- Слишком частый постинг → пользователи мьютят канал → падение ERR. URL: ganiev-marketing.ru. Confidence: MED.

### 5.4 Холодный старт (первые 1k)
- Порог критичности: до 1000 подписчиков алгоритм практически не помогает; нужен стартовый буст (посевы или взаимопиар). URL: palladium-smm.com. Confidence: MED.
- Средняя стоимость подписчика: посевы 30–120 ₽, Telegram Ads 40–200 ₽. URL: ganiev-marketing.ru. Confidence: MED.
- Органический путь до 1k без бюджета: 3–6 месяцев (кросс-промо, SEO, внешние площадки). С бюджетом 5–10К ₽/мес — 1–2 месяца. URL: ganiev-marketing.ru. Confidence: MED.
- Подготовка ДО продвижения: SEO-оптимизация названия (главный ключевой запрос) + описание (255 символов, 3–5 ключевых слов) + 10–15 сильных постов до запуска посевов. URL: ganiev-marketing.ru; dzen.ru/a/ak-S7cpc2E9VEQh-. Confidence: MED.
- Рабочие бесплатные тактики: кросс-промо с 5–10 каналами схожей тематики, экспертные комментарии в тематических группах, контент-публикации на внешних площадках (30–40% подписчиков у ganiev_marketing именно так). URL: ganiev-marketing.ru. Confidence: MED (кейс одного канала).

### 5.5 Частота и время (RU)
- Оптимальная частота: 3–5 постов в неделю для экспертного канала; 1–3 в день для новостных; ежедневные посты — только при высоком качестве, иначе мьют. URL: ganiev-marketing.ru; palladium-smm.com. Confidence: MED.
- Лучшее время: B2B вторник–четверг 09:00–11:00 и 19:00–21:00 МСК; общий пик 07:00–09:00 и 18:00–22:00 МСК (+30–50% просмотров против непикового). URL: ganiev-marketing.ru; palladium-smm.com. Confidence: MED.
- Calcal: Telegram будни 10:00–12:00 и 19:00–22:00; выходные 11:00–15:00 и 20:00–23:00; лучшие дни — вт–ср. URL: calcal.ru. Confidence: MED.

### 5.6 Табу и бан-риски
- Накрутка ботов = теневой бан поиска. Confidence: MED.
- Спам-действия (инвайт-флуд, массовые реакции) — риск ограничений. Confidence: MED.
- Публикация контента, провоцирующего массовые жалобы. Confidence: MED.
- Для нашего контура: Telegram — основной безрисковый канал RU; erid-маркировка для рекламных постов обязательна по закону. Confidence: HIGH (legal).

---

## 6. Pinterest

### 6.1 Что ранжирует алгоритм 2025–2026
- 4 главных сигнала: quality, engagement, relevance, freshness. URL: https://sproutsocial.com/insights/pinterest-algorithm/, 2026-05-13. Confidence: MED.
- Fresh pins: новые пины получают начальный буст при быстром engagement; "fresh" — это и новый контент, и обновлённые titles/descriptions/boards существующих. URL: https://www.outfy.com/blog/pinterest-algorithm/, 2026-04-29. Confidence: MED.
- Entity recognition: аккаунты, последовательно покрывающие одну тему, набирают авторитет; смешанные сигналы режут охват. URL: outfy.com. Confidence: MED.
- Video и Idea Pins критичны для SEO-видимости 2026; алгоритм приоритизирует новые оригинальные изображения над репинами. URL: https://rankmypin.com/blog/pinterest-seo-explained/, 2026-02-03. Confidence: MED.
- Ранняя дистрибуция новых пинов + фокус на video/multi-page. URL: https://rankmypin.com/blog/pinterest-algorithm/, 2026-02-15. Confidence: MED.

### 6.2 Механика посева
- Freshness boost: каждая вариация пина считается fresh → дистрибуция; стратегия — несколько пинов на один контент, распределённых по времени. URL: https://seosherpa.com/pinterest-seo/, 2026-05-25. Confidence: MED.
- Pinterest — это поисковая система: пины индексируются и приносят трафик месяцами/годами (в отличие от ленточных платформ). Это базовое свойство продукта. Confidence: HIGH.
- Для РФ: связка Pinterest + Яндекс Дзен усиливает эффект: Pinterest даёт "быстрые ссылки" для Яндекса. URL: https://dzen.ru/a/ac-D4IlxU3miNuWa, 2026-04-08. Confidence: LOW (один источник, нужна проверка).

### 6.3 За что режет охваты
- Смешанные тематики (аккаунт обо всём) — entity recognition не работает, охват падает. URL: outfy.com. Confidence: MED.
- Репины вместо свежих пинов — приоритет у оригиналов. URL: rankmypin.com. Confidence: MED.
- Спам-паттерны (массовые дубли пинов) — стандартный антиспам. Confidence: LOW (нет свежего источника в этом исследовании).

### 6.4 Холодный старт (первые 1k)
- Специфичных данных по РФ-холодному старту Pinterest = null (пробел). Общая логика: нишевой аккаунт + регулярные свежие пины 5–10/неделю + SEO-оптимизация (keywords в title/description). Confidence: LOW.
- Для нашего контура: Pinterest — воронка/трафик для Facts/Psychology брендов, не первичная платформа (CHANNELS_WAVE1: 2 аккаунта Pinterest зарегистрированы 2026-09-23/24).

### 6.5 Частота и время (RU)
- Доступность в РФ 2026: Pinterest официально НЕ заблокирован РКН, но пользователи сообщают о замедлении/недоступности у отдельных операторов. URL: https://prostotex.org/blog/pinterest-v-rossii-2026, 2026-07-02. Confidence: HIGH (важный риск-фактор).
- RU-сегмент Pinterest вырос на 40% после блокировок других визуальных сетей. URL: https://dzen.ru/a/ac-D4IlxU3miNuWa. Confidence: LOW (один источник).
- Конкретные часы/частота для RU-аудитории Pinterest = null (пробел, требуется отдельное исследование).
- Общая рекомендация (не RU-специфика): 1–2 пина/день или 5–10/неделю, распределённо. Confidence: LOW.

### 6.6 Табу и бан-риски
- Техническая недоступность для части RU-пользователей — главный риск канала (не контентный). Confidence: HIGH.
- Для нашего контура: Pinterest НЕ входит в Klipni-площадки, это отдельный тракт органического трафика. Confidence: HIGH (внутренний compliance).

---

## Сводная таблица: пороги и первичные метрики по площадкам

| Площадка | Главная метрика | Порог здоровья | First-hour критичность | Частота/день (новый аккаунт) | RU-пик (МСК) |
|---|---|---|---|---|---|
| VK Клипы | first-3s + completion | completion ≥50% | HIGH | 1–2 клипа | 18–22 будни |
| YouTube Shorts | VVSA | ≥70% | MED (48ч окно) | 3–5/неделю | 16–20 будни |
| TikTok | completion + shares/saves | completion ~70% | HIGH (1ч test) | 1–3 | 18–22 будни |
| Instagram Reels | watch time + DM sends | skip rate минимум | HIGH (1ч) | 4–7/неделю | сб 17–18; будни 18:00 |
| Telegram | ERR + пересылки | ERR ≥15% | нет (нет ленты) | 3–5/неделю | 07–09, 18–22 |
| Pinterest | freshness + engagement | — | LOW | 5–10 пинов/неделю | null |

## Главные пробелы (null, требуют отдельного исследования)
1. VK Клипы: официальный first-3s/порог дистрибуции от VK Team = null (использованы агентские данные).
2. TikTok: официальные числовые пороги completion для expansion pool = null (только отраслевые оценки ~70%).
3. Pinterest: RU-специфика частоты и времени = null.
4. Instagram: официальный список табу из Instagram Help = null (использованы слова Mosseri через прессу).
5. YouTube: официальный порог VVSA = null (70% — отраслевой ориентир, доступен в Analytics).
6. Telegram: размер стартового буста новых каналов в Explore = null (только "100–500 подписчиков").

## Источники (полный список)
- https://ppc.world/articles/kak-rabotayut-algoritmy-vkontakte-v-2026-godu/ (2026-07-08)
- https://dtf.ru/howto/4808137-kak-uvelichit-prosmotry-vk-algoritmy-i-top-16-servisov (2026-02-25)
- https://likelab.pro/blog/algoritmy-vk-klipy (2026-06-08)
- https://fathersmm.ru/blog/vk-clips-guide (2026-06-01)
- https://zapuski.com/blog/algoritmy-vk-2026-rekomendacii.html (2026-08-24)
- https://ppc.world/news/luchshee-vremya-dlya-postinga-vkontakte-posle-izmeneniya-algoritmov-issledovanie-livedune/ (2025)
- https://companies.rbc.ru/news/hE2ePBKNsK/prodvizhenie-gruppyi-v-vk-s-nulya-kak-nabrat-pervyih-1000-podpischikov/ (2026)
- https://palladium-smm.com/blog/vkontakte-klipy-prodvizhenie (2026)
- https://palladium-smm.com/blog/pervye-1000-podpischikov (2026)
- https://palladium-smm.com/blog/kak-rabotaet-algoritm-telegram (2026)
- https://palladium-smm.com/blog/kak-raskrutit-akkaunt-s-nulya (2026)
- https://tubecreatorkit.com/guides/how-to-rank-youtube-shorts-in-2026/
- https://www.tubeanalytics.net/blog/youtube-shorts-algorithm-2026
- https://www.go-viral.app/blog/youtube-shorts-algorithm-2026/
- https://metricool.com/youtube-shorts-algorithm/
- https://likes.io/blog/youtube-shorts-algorithm-2026
- https://statzen.ru/blog/kak-nabrat-1000-podpischikov-youtube (2026)
- https://support.google.com/youtube/answer/1311392?hl=en-gb (2025-07-15)
- https://ppc.land/youtube-clarifies-inauthentic-content-policy-changes/ (2025-07-15)
- https://www.subsub.io/blog/youtube-inauthentic-content-policy-2025
- https://posteverywhere.ai/blog/how-the-tiktok-algorithm-works (2026-05-23)
- https://www.socialync.io/blog/tiktok-algorithm-2026-what-works-now (2026-07-06)
- https://blog.hootsuite.com/tiktok-algorithm/ (2026-07-04)
- https://www.webtonic.io/blog/tiktok-algorithm (2026-07-31)
- https://likes.io/blog/tiktok-algorithm-2026
- https://socialz.ai/blog/how-to-get-1000-followers-on-tiktok (2026-03-09)
- https://ru.dicloak.com/blog-detail/cracking-the-code-the-ultimate-guide-to-the-tiktok-shadowban-in-2026
- https://ru.dicloak.com/blog-detail/tiktok-shadowbanned-how-to-confirm-it-recover-reach-and-prevent-it
- https://www.dataslayer.ai/blog/instagram-algorithm-2025-complete-guide-for-marketers (2026-06-29)
- https://reshmashaji.com/blog-instagram-reels-algorithm-2026/ (2026-06-08)
- https://creatorflow.so/blog/instagram-algorithm-2026/ (2026-08-24)
- https://blog.hootsuite.com/instagram-algorithm/ (2026-07-15)
- https://orangemonke.com/blogs/instagram-algorithm/ (2026-07-16)
- https://www.tokportal.com/learn/low-instagram-reels-reach-new-account
- https://www.tokportal.com/learn/instagram-account-warming-strategy-2026
- https://www.genviral.io/blog/warm-up-instagram-account
- https://getreelyze.com/guides/grow-instagram-from-zero-with-reels
- https://1kreach.com/blog/cold-start-problem-first-1000-followers-2026
- https://www.likeni.ru/events/v-kakoe-vremya-luchshe-publikovat-reels-issledovanie-livedune/ (2026-03-11)
- https://ganiev-marketing.ru/prodvizhenie-telegram-kanala/
- https://www.smm-marketing.com.ua/blog/algoritmy-telegram-2026-kak-oni-rabotaut-i-chto-realno-vliyaet-na-prodvizhenie
- https://viarum.ru/prodvizhenie-v-telegram-strategii-instrumenty-i-realnye-primery/
- https://dzen.ru/a/ak-S7cpc2E9VEQh- (2026-07-09)
- https://www.outfy.com/blog/pinterest-algorithm/ (2026-04-29)
- https://rankmypin.com/blog/pinterest-seo-explained/ (2026-02-03)
- https://rankmypin.com/blog/pinterest-algorithm/ (2026-02-15)
- https://sproutsocial.com/insights/pinterest-algorithm/ (2026-05-13)
- https://seosherpa.com/pinterest-seo/ (2026-05-25)
- https://prostotex.org/blog/pinterest-v-rossii-2026 (2026-07-02)
- https://contentmagiablog.ru/2026/04/03/pinterest-dlya-biznesa-v-rossii-v-2026-rabotayet-li-on/
- https://dzen.ru/a/ac-D4IlxU3miNuWa (2026-04-08)
- https://ppc.world/articles/auditoriya-devyati-krupneyshih-socsetey-v-rossii-v-2024-godu-issledovaniya-i-cifry/ (2026-02-16)
- https://calcal.ru/vremya-publikaczii-smm
- https://tareno.co/ru/best-time-to-post
- https://monty.fast/ru/blog/kak-chasto-postit-reels/ (2026-07-20)
- https://spikereel.com/blog/ru/tiktok-vs-reels-vs-shorts-2026 (2026-04-26)
- https://shortzly.com/blog/short-form-video-posting-frequency (2026-06-22)
- https://www.kapwing.com/resources/short-form-video-statistics-tiktok-reels-and-shorts-by-the-numbers-in-2026/ (2026-07-08)
- https://postplanify.com/blog/short-form-video-statistics-2026 (2026-04-25)
- https://earnifyhub.com/creator-economy/first-1000-subscribers-platform-guide-2026 (2026-04-09)
- Внутренние: VIEWS_GROWTH_PLAYBOOK.md, PLATFORMS_MATRIX.md, PLATFORM_RANKING.md, MONETIZATION_EXECUTION_PLAN_D0_14.md, CHANNELS_WAVE1.md
