# SPEC: SEO-сайт — генератор и 100 статических страниц «техстек-чекер» (rev.1, 30.09.2026, author: company)

## Контекст и anchor
Решение company GO от 27.09.2026 на карте t_6db8cab6 (бриф: Desktop/all/ventures/docs/seo-site/TECHSTACK_CHECKER_BRIEF.md): вариант (a) — статические пред-просканированные страницы стеков, каталог /tools/techstack/, старт 0₽, PII-free, в границах CHARTER seo-site. NO-GO на вариант (b) server-side API — не строить.

- Repo: https://github.com/maximalang/mvp-peni-site (локально C:/Users/max/Documents/seo-niche-research/mvp-peni-site — НЕ трогать этот worktree, он на чужой ветке; создать отдельный git worktree).
- Anchor (база PR): origin/main head `0b059be4283856f0f53aee388f9d31bc134c502c`.
- Ветка: `codex/techstack-pages`. PR DRAFT, БЕЗ merge в main (merge/deploy — отдельная gate-цепочка после QA).
- На доске seo-site висит отложенная карта t_0ffe61a5 (PR7 deploy) — её scope НЕ трогать; при коллизии в sitemap.xml — перебаза на актуальный main и повторная генерация своей секции.
- Сканер-движок (canonical): capability webstack-scanner, ACCESS.md: C:/Users/max/Desktop/all/tools/capabilities/webstack-scanner/ACCESS.md. Запуск: venv-питон curl-cffi + scan.py (команды в ACCESS.md). Capability НЕ редактировать.

## Deliverable
1. Генератор `tools/generate_techstack_pages.py` (python 3.11+ stdlib, без новых зависимостей): вход — `data/techstack/domains.txt` + `data/techstack/scans.json` (сырой вывод батча сканера, закоммичен), выход — статические HTML-страницы `techstack/<slug>/index.html` + индексная `techstack/index.html`. Генератор НЕ ходит в сеть на этапе сборки (данные — только из scans.json).
2. Доменный набор: 100 доменов = 50 RU + 50 EN из публичных топ-листов (источник — URL топ-листов записать в data/techstack/domains.txt комментарием); fortress-домены с TLS-обрывом (ozon/avito/tbank-класс) исключить и перечислить в skips.json с причиной. Успешно просканировано (tool_count>=1) должно быть >= 60 из 100; недобор добрать заменой доменов, не фабрикацией данных.
3. Страница домена: RU-копия, заголовок «Технологии сайта <domain> — что используется», таблица/список инструментов (name, categories, confidence, version), дата скана, дисклеймер «по данным открытой главной страницы», ссылка на индекс. Дизайн — существующий styles.css сайта, минимальная нагрузка, без тяжёлого JS; в одном стиле с текущими страницами калькулятора.
4. SEO-обвязка: уникальные title/meta description/canonical на каждую страницу, секция в sitemap.xml, robots не блокирует /techstack/, перелинковка с индексной страницы.
5. Тесты: `node --test tests/*.test.mjs` и `python -m py_compile tools/generate_techstack_pages.py` зелёные (базовые проверки репо обязательны); плюс свой тест генератора на фикстуре scans.json (без live HTTP): генерация в tmp, проверка числа страниц, наличия canonical, отсутствия PII-полей.
6. Артефакт батча: scans.json + skips.json + сводка (N доменов, M с инструментами, топ-10 технологий, суммарное время скана) в `artifacts/techstack-pages/summary.md` внутри worktree (в PR не тащить бинарники/тяжёлое — только текст/JSON).

## Acceptance (evidence комментарием на карту)
- git: имя worktree, ветка, точный head SHA, `git diff --stat` против anchor.
- PR URL (draft, база main) + список изменённых файлов.
- Вывод базовых проверок репо (node --test, py_compile) + вывод своего теста генератора.
- Числа батча: доменов просканировано/успешно/скипнуто; страницы сгенерированы (число); путь к 2-3 примерам страниц.
- Отчёт обычным текстом; формальные gate-маркеры ставит qa на своей consumer-карте.

## Запреты
- НЕ мержить в main, НЕ деплоить, НЕ покупать домен/трафик (публикация — отдельная карта после gate-цепочки).
- Не трогать worktree C:/Users/max/Documents/seo-niche-research/mvp-peni-site и чужие ветки; не трогать scope t_0ffe61a5.
- Не редактировать capability webstack-scanner и данные enthec (дефект движка — комментарием на карту, фикс = company).
- Live-сканы только последовательно, delay >= 1s (правило ACCESS.md); суммарно не более 150 доменов за задачу.
- Никаких .env*/секретов; PII-free: только company-level данные (публичный домен + технологии), без контактных лиц.
- Без фабрикаций: не просканировано = скип с причиной, не «правдоподобный» список.

## Финансовый скоуп
0₽ (локальный сканер, существующий хостинг до deploy-карты). Период эксперимента: 30 дней от публикации. Kill-критерий (утверждён решением 27.09): органика <1K посетителей/мес ИЛИ ноль шеров/бэклинков ИЛИ bounce >90% за 30 дней.

## Следующий шаг (вне этой карты)
После QA PASS и gate-цепочки merge+deploy — карта измерения: indexation rate 7д (Яндекс.Вебмастер + GSC), impressions 14д, CTR 30д.
