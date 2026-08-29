# Sprint-H1 Field Validation Tracker — GPT Estate Manager

Карточка: t_e56b725d (родитель t_f3573ec1, вердикт NEEDS-EVIDENCE 2026-08-29).
Открыт: 2026-08-29. Статус: ДЕНЬ 0 — инфраструктура готова, поле НЕ активно (ждёт user-approval на outreach).
Правило: строки заполняются только реальными наблюдениями; «нет данных» — валидное значение. Выдуманные цифры запрещены.

## 1. Таблица гейтов GO (факт vs план)

| Гейт | План (источник) | Факт на 2026-08-29 | Доказательство (path/URL) | Статус |
|---|---|---|---|---|
| G1. Интервью: ≥10 проблемных, из них ≥3 с подтверждением боли на сегмент | 5×S1 + 5×S2 + 5×S3 (product doc §interview plan) | 0 проведено; 0 записано | venture-lab/sprint-H1-interviews-2026-08-29.csv (пуст) | NOT STARTED — блокер: outreach требует user-approval |
| G2. Предзаказы/LOI: ≥3 | aggregate §0 | 0 | venture-lab/sprint-H1-signals-2026-08-29.csv | NOT STARTED — зависит от G1/лендинга |
| G3. Consented GPT portfolio inventory scan: ≥50 completed distinct scans ИЛИ ≥30 регистраций (счётчики раздельные, не комбинируются) | aggregate §4 тест 4 + протокол: venture-lab/sprint-H1-g3-portfolio-scan-protocol-2026-08-29.md | 0 completed scans; 0 регистраций (день 0; seed-строки scans-CSV — примеры протокола §5, не полевые данные) | venture-lab/sprint-H1-scans-2026-08-29.csv (регистр сканов) + venture-lab/sprint-H1-signals-2026-08-29.csv (регистрации) | METHOD DEFINED — сбор не начинается до approvals B1–B4; лендинг-плечо (≥30 регистраций) дополнительно требует B2 |
| G4. S2: 3 agency discovery-call, ≥1 LOI | aggregate §4 тест 5 | 0 | venture-lab/sprint-H1-signals-2026-08-29.csv | NOT STARTED — блокер: outreach требует user-approval |

## 2. Kill-критерии (мониторинг, еженедельно до вердикта)

| Kill | Порог срабатывания | Проверка 2026-08-29 | Статус |
|---|---|---|---|
| K1. OpenAI шипит нативную GPT→Skills конвертацию | shipped = п. «конвертация» в release notes/help center ИЛИ рабочий «migrate/convert» в продукте (проверка E4 в реальном аккаунте) | НЕ сработал. Release notes (openai.com/products/release-notes, help.openai.com/6825453) — упоминаний нет; help center GPTs (8554407) — нет; btibor91 — только leak 2025-12-20 + закрытие создания 16.08. CONTRADICTION: сторонний блог (aiautomationglobal.com) утверждает, что one-click migrate уже есть, без первоисточника, классифицирован LOW/unverified | NO KILL. Риск эскалировал: OFFICIAL ROADMAP CONFIRMED (см. §4) |
| K2. <30% интервью с подтверждением боли | после ≥5 интервью доля подтверждений <30% | нет данных (0 интервью) | NOT TRIGGERED — insufficient data |
| K3. Прямой конкурент-автоматизация экспорта в S2 | продукт автоматизирует export агентствам | первый pass 2026-08-29 (web_search): прямой конкурент не найден; SERP-кластер — конвертеры (gpt2skill, миграционные гайды), не inventory/audit-автоматизация для агентств. Один поиск — слабое доказательство для негативного claim'а | NO KILL (прелюминарно; повторить проверку на неделе 1) |

## 3. Матрица блокеров

| Блокер | Гейты | Требует | Обходного пути нет? |
|---|---|---|---|
| B1. Email-sequence 7 писем S1/S2 | G1(часть)/G2/G4 | user-approval по APPROVALS.md до отправки первого касания | нет |
| B2. Промо-лендинг + email-захват | G2/G3 | user-approval: публикация + плейсмент. $0-варианты не верифицированы (Netlify/Vercel free tier), часть требует FPA или валидного email | нет; уточнить у userа разрешённые $0-плейсменты |
| B3. WCMS-метод не определён | G3 | RESOLVED 2026-08-29 (карточка t_9b0bda2c): метрика переименована в «consented GPT portfolio inventory scan», метод и правила счёта — venture-lab/sprint-H1-g3-portfolio-scan-protocol-2026-08-29.md; аббревиатура WCMS не расшифрована (первичного артефакта нет, гадание запрещено). Остаточный блокер: продвижение скана = outreach → approval B1/B2 | да, для остаточного (approval обязателен) |
| B4. Reddit/форум-кейсы (посты) | G1 (recruiting)/G3 (трафик) | публикация = outreach → approval | нет |

Ни один из 4 гейтов не может начать набор фактов без разблокировки B1–B4. Автономная работа (kill-мониторинг, консьюмер-контекст, документация спринта) продолжается.

## 4. Kill-фактор S07: официальный статус (обновление 2026-08-29)

- OpenAI Academy «Skills» (academy.openai.com/public/clubs/work-users-ynjqu/resources/skills, last updated 2026-08-27): «After that time, we'll offer options for both users and admins to convert GPTs into skills when they're better suited for repeatable workflows» — официальное подтверждение намерения. Снапшот: evidence-discovery2-H1/e23_academy_skills_conversion.txt.
- Release notes за август 2026: конвертации нет. Снапшот: evidence-discovery2-H1/e24_release_notes_kill1_check.txt.
- Вывод: kill-фактор перешёл из «вероятностного» в «официально заявленный роадмап без даты». Тайминг беты Skills неизвестен; при шипе конвертации — kill срабатывает, возврат в discovery.

## 5. Гипотезы спринта (falsifiable)

| ID | Гипотеза | Проверка | Falsifier |
|---|---|---|---|
| SH1 | ≥30% из 10+ проблемных интервью подтвердят боль «потеря/миграция портфеля GPT» | интервью по product doc | если после ≥5 интервью <30% подтверждений — kill K2 |
| SH2 | ≥3 из 15 интервью дадут предзаказ/LOI при оффере $29–49 solo / $99–199 год agency | оффер в конце интервью/письма | 0 из 15 → G2 провален |
| SH3 | Free-скан даёт visitor→scan ≥20% и scan→email ≥25% | лендинг-аналитика после approval | недобор обеих в первые 2 недели → канал не работает |
| SH4 | Consented portfolio-scan достижим ($0, 2–3 дня труда) | метод: venture-lab/sprint-H1-g3-portfolio-scan-protocol-2026-08-29.md; пилот — при открытии поля | если ручной consent-сбор не даёт 50 completed scans за спринт ИЛИ требуется платный API → G3 пересматривается; automated extraction (скрейпинг UI, неофициальные API) запрещён ToS [S21] и обходом не является |

## 6. Чекпойнты

- 2026-08-29: день 0. Инфраструктура, kill-проверка №1, регистрация блокеров. Полевые цифры: 0/0/0.
- 2026-08-29 (t_9b0bda2c): метод G3 определён — протокол «consented GPT portfolio inventory scan» (venture-lab/sprint-H1-g3-portfolio-scan-protocol-2026-08-29.md) + raw-регистр venture-lab/sprint-H1-scans-2026-08-29.csv с seed-примерами EX1–EX5 (примеры протокола §5, НЕ полевые данные). Блокер B3 закрыт (метод); счётчики сканов и регистраций раздельны (≥50 OR ≥30, комбинирование запрещено). Полевые цифры G3 остаются 0/0 — сбор данных ждёт approvals B1–B4.
- Неделя 1 (план): kill-проверка №2; повторная S2-конкурентная проверка; при approval — старт outreach.
- Вердикт (план): карточка агрегации результатов спринта принимает GO/NO-GO по гейтам §0 aggregate.

## 7. Ограничения

- Все полевые каналы (email, посты, лендинг, скан-продвижение) стоят в очереди на user-approval — см. матрицу блокеров. Без approval факт-значения гейтов не двигаются; это соответствует APPROVALS.md и не является срывом спринта.
- Проверки kill-фактора выполнены на открытых источниках; проверка в реальном аккаунте ChatGPT (E4-style) — рекомендация для недели 1.
