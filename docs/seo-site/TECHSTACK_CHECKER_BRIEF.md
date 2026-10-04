# TECHSTACK_CHECKER_BRIEF

**Дата:** 2026-09-27
**Автор:** research (Kanban t_6db8cab6)
**Владелец:** company
**Статус:** draft для review

---

## 1. СПРОС

### EN-частотности (Google, global)

| Запрос | Оценка monthly volume | Источники |
|--------|----------------------|-----------|
| "what is this website built with" | **null** — точный объём не найден в открытых источниках | Поиск по Ahrefs/Semrush/Keyword Tool не дал публичных чисел; требуется платный доступ |
| "website technology checker" | **null** — точный объём не найден | Аналогично; частота подтверждена наличием множества сервисов, но не числом |
| "wappalyzer" (brand) | ~7.9M monthly visits (SEMrush, July 2026) | https://www.semrush.com/website/wappalyzer.com/overview/ (дата доступа: 2026-09-27) |
| "builtwith" (brand) | ~4.9M monthly visits (SEMrush, June 2026) | https://www.semrush.com/website/builtwith.com/overview/ (дата доступа: 2026-09-27) |
| "whatcms.org" | ~798.5K monthly visits (SEMrush, Aug 2026) | https://www.semrush.com/website/atshop.io/overview/ (упоминание как competitor; дата доступа: 2026-09-27) |

### RU-частотности (Яндекс Wordstat)

| Запрос | Оценка monthly volume | Источники |
|--------|----------------------|-----------|
| "на чём сделан сайт" | **null** — нет публичных данных Wordstat без авторизации | Поиск не дал опубликованных цифр; требуется ручная проверка wordstat.yandex.ru |
| "определить CMS сайта" | **null** — аналогично | Требуется ручная проверка |
| "узнать движок сайта" | **null** — аналогично | Требуется ручная проверка |

### Косвенные индикаторы спроса

| Метрика | Значение | Источники |
|---------|----------|-----------|
| Wappalyzer Chrome extension users | **2.5M+** (встроено в их платформу) | https://pipeline.zoominfo.com/sales/builtwith-vs-wappalyzer (2026-05-31, дата доступа: 2026-09-27) |
| BuiltWith technologies tracked | **113,002+** | https://pipeline.zoominfo.com/sales/builtwith-vs-wappalyzer (2026-05-31, дата доступа: 2026-09-27) |
| BuiltWith domains coverage | **478M+ root domains** | https://pipeline.zoominfo.com/sales/builtwith-vs-wappalyzer (2026-05-31, дата доступа: 2026-09-27) |
| stackfull.lol пиковый трафик | **5,498 visitors/день** (27.09.2026, один ТГ-пост) | Данные company из их публичной stats-страницы (подтверждено в SPEC) |
| stackfull.lol текущий трафик | **6,279 visitors/30 дней** (27.09.2026) | https://www.stackfull.lol/sponsor (дата доступа: 2026-09-27) |
| stackfull.lol спонсорство | **$2,500/30 дней**, 2/12 слотов занято | https://www.stackfull.lol/sponsor (дата доступа: 2026-09-27) |

### Вердикт по спросу

**Qualitative: HIGH.** Наличие устойчивых брендов (Wappalyzer 2.5M+ extension users, BuiltWith 478M+ domains) доказывает persistent demand. Виральность stackfull.lol (5.5K visitors/день с одного ТГ-поста) подтверждает, что формат "узнать стек компании" вызывает organic sharing.

**Quantitative: MEDIUM-LOW для SEO.** Точные частотности ключевых запросов недоступны без платных инструментов. RU-частотности не подтверждены публичными данными. Это ограничивает точность прогноза organic traffic.

---

## 2. КОНКУРЕНТЫ

### Группа A: Enterprise leaders (независимо подтверждённая репутация)

| Игрок | Трафик | Free-tier | Монетизация | Репутация |
|-------|--------|-----------|-------------|-----------|
| **BuiltWith** | 4.9M visits/mo (SEMrush, Jun 2026) | Limited lookups/day, no bulk export, no API | $295-$995/mo (Basic/Pro/Team), Enterprise custom | Подтверждена: Crunchbase profile, ZoomInfo comparison, WebReveal review |
| **Wappalyzer** | 7.9-15.5M visits/mo (SEMrush, May-Jun 2026) | Chrome extension free, 50 lookups/mo account limit | $250-$850/mo (Starter/Growth/Business) | Подтверждена: 2.5M extension users (ZoomInfo), Derrick review, TechPeeker comparison |

**Источники:**
- https://www.semrush.com/website/builtwith.com/overview/ (2026-09-27)
- https://www.semrush.com/website/wappalyzer.com/overview/ (2026-09-27)
- https://pipeline.zoominfo.com/sales/builtwith-vs-wappalyzer (2026-05-31, доступ: 2026-09-27)
- https://webreveal.io/blog/builtwith-pricing-alternatives.html (2026-04-01, доступ: 2026-09-27)
- https://derrick-app.com/tools/wappalyzer-review (2026-05-17, доступ: 2026-09-27)

### Группа B: Mid-tier / niche

| Игрок | Трафик | Free-tier | Монетизация | Репутация |
|-------|--------|-----------|-------------|-----------|
| **WhatRuns** | ~76K US rank (Similarweb, data limited) | Browser extension free | Premium features unknown | Подтверждена: упоминание в TechPeeker, Similarweb comparison |
| **SimilarTech** | ~2.5K monthly US visitors (Exploding Topics) | Limited | Enterprise sales intelligence | Подтверждена: Crunchbase, Bloomberry review |
| **WhatCMS.org** | ~798K visits/mo (SEMrush, Aug 2026) | Free CMS detection | Unknown monetization | Подтверждена: Semrush competitor data |

**Источники:**
- https://www.similarweb.com/website/whatruns.com/ (данные ограничены, доступ: 2026-09-27)
- https://analytics.explodingtopics.com/website/similartech.com (доступ: 2026-09-27)
- https://www.crunchbase.com/organization/similartech (доступ: 2026-09-27)

### Группа C: RU-аналоги

| Игрок | Трафик | Free-tier | Монетизация | Репутация |
|-------|--------|-----------|-------------|-----------|
| **PR-CY** (cms-checker) | **null** — нет данных | Free online tool | SEO tools suite | Упоминается в uGuide, Webolution, Hastra |
| **2ip.ru/cms** | **null** — нет данных | Free online tool | 2ip.ru tools suite | Упоминается в uGuide, SEO.RU |
| **iTrack** (whatcms) | **null** — нет данных | Free limited, paid bulk | SEO/платная аналитика | Упоминается в Hastra, SEO.RU |

**Источники:**
- https://uguide.ru/kak-uznat-na-kakom-dvizhke-sdelan-sait (2025-08-18, доступ: 2026-09-27)
- https://seo.ru/blog/kak-opredelit-cms-sayta-12-prostyh-sposobov/ (2024-09-25, доступ: 2026-09-27)
- https://hastra.ru/blog/kak-uznat-cms-sajta/ (доступ: 2026-09-27)

### Разрыв конкурентов (gap analysis)

1. **RU-ниша слабо покрыта:** Все RU-аналоги (PR-CY, 2ip, iTrack) — это узкие CMS-детекторы без глубины технологий (Wappalyzer tracks 3K+, BuiltWith 113K+). Нет публичных данных об их трафике — вероятно, низкий.

2. **Виральный потенциал не использован:** Ни один из лидеров не делает viral-friendly публичные страницы стеков компаний (как stackfull.lol). Их модель — private lookups, не shareable content.

3. **Free-tier ограничен:** BuiltWith и Wappalyzer сильно ограничивают free usage (лимиты lookups, нет API). Это оставляет окно для truly free alternative с viral loop.

4. **SEO-оптимизация слабая:** Wappalyzer organic traffic только 41.7K/mo (SEMrush, Jul 2026) при 15.5M total — 0.27%. BuiltWith 28.7% от Google (Semrush, Jun 2026). Оба полагаются на direct/brand traffic, не на SEO content.

---

## 3. АРХИТЕКТУРА ПОСТАВКИ

### Вариант (a): Статические SEO-страницы с пред-просканированными стеками

**Описание:** Батч-сканирование топ-N доменов (наш webstack-scanner, 7,628 технологий, 0₽), генерация статических HTML-страниц `/stack/<domain>.html`, sitemap.

| Параметр | Оценка |
|----------|--------|
| Стоимость | **0₽** (сканер уже есть, генерация статики бесплатна) |
| Трудоёмкость | **2-3 дня** (шаблоны, батч-скрипт, sitemap) |
| SEO-потенциал | **ВЫСОКИЙ** — каждая страница уникальна, long-tail "на чём сделан <domain>" |
| PII-free | **ДА** — только публичные данные |
| Риски | Данные устаревают (нужен refresh), не покрывает "по запросу" |
| GPL-нота | **OK** — используем наш сканер, не распространяем данные enthec |

### Вариант (b): Server-side проверка по запросу (API route)

**Описание:** API endpoint `/api/check?url=...` вызывает наш сканер, возвращает JSON. Frontend рендерит результат.

| Параметр | Оценка |
|----------|--------|
| Стоимость | **0₽** (тот же сканер), но хостинг API ~500-1000₽/мес (VPS) |
| Трудоёмкость | **3-5 дней** (API route, rate limiting, error handling) |
| SEO-потенциал | **НИЗКИЙ** — динамический контент не индексируется, нет shareable URLs |
| PII-free | **ДА** — не храним запросы |
| Риски | **Abuse** — mass scanning через наш endpoint, DDoS, rate-limit bypass |
| GPL-нота | **OK** — SaaS-использование допустимо |

### Вариант (c): Гибрид

**Описание:** Статические страницы для топ-10K доменов (SEO) + API для "проверить свой сайт" (engagement).

| Параметр | Оценка |
|----------|--------|
| Стоимость | **0-1000₽/мес** (хостинг API) |
| Трудоёмкость | **5-7 дней** |
| SEO-потенциал | **ВЫСОКИЙ** (статика) + **engagement** (API) |
| PII-free | **ДА** |
| Риски | Abuse на API-части, нужен rate limit + CAPTCHA |

### Рекомендация по архитектуре

**Рекомендуемый вариант: (a) → (c)** — начать со статических страниц (быстрый MVP, 0₽, SEO), добавить API после валидации спроса. Это соответствует CHARTER: client-side first, PII-free, pre-launch.

---

## 4. ЭКОНОМИКА

### Сценарий S (консервативный): 10K visitors/mo

| Параметр | Значение | Допущение |
|----------|----------|-----------|
| Трафик | 10,000 visitors/mo | 2% от пика stackfull.lol (5K/день → 150K/mo) |
| Монетизация: реклама | **$50-100/mo** | $5-10 CPM, 1 ad slot |
| Монетизация: lead-magnet для RR | **null** — не оценено | Требуется модель конверсии RR |
| Монетизация: платная глубина | **$0** | Нет платного tier на старте |
| **Итого** | **$50-100/mo** (~4,000-8,000₽) | |

### Сценарий M (базовый): 50K visitors/mo

| Параметр | Значение | Допущение |
|----------|----------|-----------|
| Трафик | 50,000 visitors/mo | 10% от пика stackfull.lol |
| Монетизация: реклама | **$250-500/mo** | $5-10 CPM |
| Монетизация: спонсорство (как stackfull) | **$500-1,000/mo** | 1-2 слота по $500 (ниже stackfull $2,500) |
| Монетизация: lead-magnet для RR | **null** — не оценено | |
| **Итого** | **$750-1,500/mo** (~60,000-120,000₽) | |

### Сценарий L (оптимистичный): 200K visitors/mo

| Параметр | Значение | Допущение |
|----------|----------|-----------|
| Трафик | 200,000 visitors/mo | Повторение виральности stackfull.lol |
| Монетизация: реклама | **$1,000-2,000/mo** | |
| Монетизация: спонсорство | **$2,500-5,000/mo** | 1-2 слота по $2,500 (как stackfull) |
| Монетизация: платная глубина | **$500-1,000/mo** | API access, bulk export |
| **Итого** | **$4,000-8,000/mo** (~320,000-640,000₽) | |

### Неизвестное (null)

| Параметр | Причина |
|----------|---------|
| Конверсия в RR leads | Нет данных о пересечении аудитории |
| RU organic traffic potential | Нет Wordstat данных |
| Retention rate | Нет исторических данных |
| CAC для платного tier | Нет данных о канале привлечения |

---

## 5. РЕКОМЕНДАЦИЯ

### GO/NO-GO: **CONDITIONAL GO**

**GO при условии:** Использование варианта (a) — статические страницы — как MVP с нулевой стоимостью и минимальным риском.

**NO-GO для:** Варианта (b) — server-side API — до валидации спроса, из-за abuse-рисков и низкого SEO-потенциала.

### Kill-критерий

**Kill если:** После 30 дней live:
- Organic traffic < 1,000 visitors/mo (ниже порога рекламной монетизации), ИЛИ
- Zero backlinks/shares (отсутствие виральности), ИЛИ
- Bounce rate > 90% (неудовлетворённый интент)

### Следующий измеримый шаг

**Шаг:** Сгенерировать 100 статических страниц топ-100 RU/EN доменов (наш сканер, 0₽), опубликовать на mvp-peni-site под `/tools/techstack/`, измерить:
1. Indexation rate (Google Search Console) через 7 дней
2. Organic impressions через 14 дней
3. Click-through rate через 30 дней

**Owner:** company (решение), code (реализация после GO)

---

## Источники (полный список)

| # | URL | Дата доступа | Использовано для |
|---|-----|--------------|------------------|
| 1 | https://www.semrush.com/website/wappalyzer.com/overview/ | 2026-09-27 | Wappalyzer traffic |
| 2 | https://www.semrush.com/website/builtwith.com/overview/ | 2026-09-27 | BuiltWith traffic |
| 3 | https://hypestat.com/info/wappalyzer.com | 2026-09-27 | Wappalyzer traffic (второй источник) |
| 4 | https://pipeline.zoominfo.com/sales/builtwith-vs-wappalyzer | 2026-09-27 | Extension users, technologies count |
| 5 | https://webreveal.io/blog/builtwith-pricing-alternatives.html | 2026-09-27 | Pricing comparison |
| 6 | https://derrick-app.com/tools/wappalyzer-review | 2026-09-27 | Wappalyzer pricing, features |
| 7 | https://www.techpeeker.com/wappalyzer-alternative | 2026-09-27 | Market landscape |
| 8 | https://seomator.com/blog/wappalyzer-alternatives | 2026-09-27 | GPL-3.0 history, alternatives |
| 9 | https://github.com/enthec/webappanalyzer | 2026-09-27 | GPL license confirmation |
| 10 | https://www.stackfull.lol/sponsor | 2026-09-27 | Viral traffic, sponsorship model |
| 11 | https://uguide.ru/kak-uznat-na-kakom-dvizhke-sdelan-sait | 2026-09-27 | RU competitors |
| 12 | https://seo.ru/blog/kak-opredelit-cms-sayta-12-prostyh-sposobov/ | 2026-09-27 | RU competitors |
| 13 | https://www.similarweb.com/website/whatruns.com/ | 2026-09-27 | WhatRuns (ограниченные данные) |
| 14 | https://analytics.explodingtopics.com/website/similartech.com | 2026-09-27 | SimilarTech traffic |
| 15 | https://www.crunchbase.com/organization/similartech | 2026-09-27 | SimilarTech profile |

---

*Бриф подготовлен в рамках Kanban task t_6db8cab6. Research-only, без live-проб, без правок кода.*
