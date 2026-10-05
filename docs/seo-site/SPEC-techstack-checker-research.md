# SPEC: Research — утилита «техстек-чекер» для SEO Utility Site (rev.1, 27.09.2026, author: company)

## Цель
Evidence-бриф для GO/NO-GO company по добавлению утилиты «проверка техстека
сайта» в SEO Utility Site. Владелец одобрил направление 27.09.2026 (пункт 3
разбора stackfull.lol); решение о постройке принимается ПОСЛЕ этого брифа.
Первичная метрика продукта: successful_organic_calculations_28d.

## Контекст (уже проверено company — не перепроверять)
- stackfull.lol: старт 25.09.2026, 27.09 пик 5,498 посетителей/день с одного
  ТГ-поста (данные их публичной stats-страницы) — доказательство виральности
  ниши; монетизация: спонсорские слоты $2,500/30 дней.
- У флота ЕСТЬ локальный сканер webstack-scanner (7 628 технологий, 0₽):
  C:/Users/max/Desktop/all/tools/capabilities/webstack-scanner/ACCESS.md.
- SEO Utility Site: репо C:/Users/max/Documents/seo-niche-research/mvp-peni-site,
  фаза pre-launch/local MVP, расчёты client-side и PII-free (CHARTER.md, STATE.md).

## Deliverable
Файл `C:/Users/max/Desktop/all/ventures/docs/seo-site/TECHSTACK_CHECKER_BRIEF.md`:
1. СПРОС: частотности RU+EN класса «технологии сайта / на чём сделан сайт /
   site technology checker / wappalyzer online / what website is built with» —
   каждое число ≥2 независимыми источниками (URL+дата). Сюда же: ТГ-виральность
   stackfull как qualitative-сигнал.
2. КОНКУРЕНТЫ: wappalyzer.com, builtwith.com, whatruns.io, similartech.com +
   RU-аналоги если есть: глубина free-tier, монетизация, сила домена/органики.
   Группировка A/B/C по независимо подтверждённой репутации (одному рейтингу
   не верить; проверять реферальные связи).
3. АРХИТЕКТУРА поставки с учётом CHARTER (client-side, PII-free, pre-launch):
   (a) статические SEO-страницы с ПРЕД-просканированными стеками топ-N
   компаний/доменов (данные генерит наш сканер батчем, 0₽);
   (b) server-side проверка по запросу (API route: хостинг, стоимость, abuse/
   rate-limit риски); (c) гибрид. Для каждой: стоимость ₽, трудоёмкость,
   SEO-потенциал, риски. GPL-нота: данные enthec/webappanalyzer GPL-3.0 —
   SaaS-использование допустимо, дистрибуция данных в продукте — оценить отдельно.
4. ЭКОНОМИКА: сценарии S/M/L (трафик→монетизация: реклама / lead-magnet для
   RR / платная глубина) с числами и допущениями; неизвестное = null с причиной.
5. РЕКОМЕНДАЦИЯ: GO/NO-GO + kill-критерий + один следующий измеримый шаг.

## Границы (запреты)
- Research-only: НЕТ правок кода mvp-peni-site, нет сборок, нет публикаций.
- НЕТ терминальных HTTP-проб живых эндпоинтов (fleet-policy гейтит live-вызовы
  в research-картах): только web_search/web_extract/публичные данные.
- НЕТ spend, регистраций аккаунтов, KYC.
- Числа без источника НЕ выдавать за факт: null + причина.

## Acceptance (evidence в комментарий карты)
- Файл брифа по указанному пути, все 5 секций заполнены.
- Каждое числовое утверждение: ≥2 источника (URL + дата доступа).
- RECOMMENDATION секция содержит явный GO или NO-GO + kill-критерий.
- В комментарии: путь + 5 строк (спрос-вердикт, разрыв конкурентов,
  рекомендованный вариант архитектуры, оценка стоимости, следующий шаг).

## Tool map
web_search, web_extract, read_file (CHARTER.md/STATE.md репо — только чтение),
write_file (только файл брифа). code_execution НЕдоступен. Артефакт писать
инкрементально (секция за секцией), не одним финальным куском.
