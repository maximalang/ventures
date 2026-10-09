# FACTORY_ECONOMICS_V2.py — воспроизводимая модель юнит-экономики контент-завода с МИКСОМ монетизации
# Карта F-MON2 (t_17058bf6), 23.09.2026. Роль: finance. Paid=0 (read-only расчёт).
# Запуск: python3 factory_econ_calc_v2.py  (python 3.8+, stdlib only)
#
# Отличие V2 от V1 (t_87aa5e43): добавлены потоки Boosty, TG Stars, CPA, YT long RPM, Интеграции
# по спецификации F_PILOT_PACKAGE.md §4 (микс >=3 потока/бренд, один поток <=60% net бренда).
#
# Каждая ставка — источник или явное ДОПУЩЕНИЕ. Источники:
# [MR]=MONEY_ROUTES.md (16.09.2026) · [TM]=THEMES_MATRIX.md · [V4]=VIDEO_STRATEGY_V4_DRAFT.md (20.09.2026)
# [ST]=MONETIZATION_STACKS.md (t_3b0621b9) · [AV]=AVATAR_TRACK.md · [D14]=MONETIZATION_EXECUTION_PLAN_D0_14.md
# [FP]=F_PILOT_PACKAGE.md (v2, 23.09.2026)

RUB_PER_USD = 92.0  # [V4 §6, модельный курс]

# --- Нетто-коэффициенты маршрутов (доля gross, доходящая до карты) ---
# [MR §5, расчёт на 100к gross, дата 16.09.2026; FP §4]
# ОБНОВЛЕНО 24.09.2026 картой F-MON3 (t_e5ae02e0) по delta MON-V7-B (DEEP_V7 §11) и MON-V7-D (WORKAROUNDS_D §6):
# НПД по доходам от физлиц/агентов = 4% (не 6%) [B3: письмо Минфина 03-11-11/74629, Т-Ж 2026, H].
NET = {
    "VK":         0.94,   # БЕЗ ИЗМЕНЕНИЙ. НПД 6% — VK-партнёрка, юр-контур [MR маршрут 2]
    "Klipni":     0.912,  # V3: 5% fee [K2] + НПД 4% [B3] (было 0.893 при НПД 6%) [D11, H]
    "Boosty":     0.821,  # V3: 11.7% комиссия [B1] + вывод 2.2%+20₽ [B3] + НПД 4% (было 0.883) [D11, H]
    "TrackB":     0.96,   # V3: НПД 4% на ₽-услуги физлицам [B3] (было 0.94 при НПД 6%) [D11, H]
    "Stars":      0.80,   # БЕЗ ИЗМЕНЕНИЙ. ~7-10% вывод + НДФЛ 13% (крипто != НПД) [MR маршрут 4, M]
    "CPA":        0.96,   # V3: НПД 4% [B3], erid авто биржей [C2] (было 0.94 ДОПУЩЕНИЕ). Всё ещё калибровка до 1-й выплаты [D11, M]
    "YT_RPM":     0.75,   # V3: середина канона 0.65-0.85 [D6 §6] (было 0.70). НЕ В БАЗЕ — триггер 250к просм/мес.
    "Integr":     0.91,   # V3: НПД 4%, erid обязателен (было 0.87; диапазон 0.87-0.96) [D11, M]
    "DareBay":    0.771,  # БЕЗ ИЗМЕНЕНИЙ. 10% вывод + 1.5% спред + НДФЛ 13% [MR маршрут 3] — крипто-цепочка
    "Stocks":     0.86,   # V3-НОВЫЙ (не в базе до М3): 0.94 EasyStaff x 0.96 НПД 4% [D6 §6]
}

# --- Ставки дохода (gross до комиссий/налога) ---
RATES = {
    "klipni_wardogs_rub_per_1k": 25.0,   # [D14 §1, кабинет; потолок 1500₽/ролик]
    "klipni_avg_rub_per_1k":     (30.0, 40.0),  # [TM стр.15: 300к просм ≈ 9-12к₽]
    "darebay_usd_per_1k":        (1.0, 2.0),    # [MR §2.2, H]
    "vk_rub_per_1k":             (20.0, 60.0),  # [MR §2.1, L-оценки; TM 15-70 по нишам]
    "vk_niche_fact_rub_per_1k":  (40.0, 55.0),  # [TM: образование/история]
    "yt_long_rpm_usd":           10.9,          # [FP §4: сон-серии $10.9 RPM]
    "stars_usd_per_star":        0.013,         # [MR §2.1: вывод $0.013/★]
}

# --- Себестоимость ---
COSTS = {
    "clip_master_cash": 0.0,
    "clip_master_labor_min": (5, 15),
    "clip_adapt_min": (12, 20),
    "series_cash": 0.0,
    "series_labor_min": (20, 40),
    "avatar_cash_free": 0.0,
    "avatar_cash_prod": (20, 45),
    "avatar_labor_min": (10, 20),
}
LABOR_RATE_RUB_H = 500.0  # [ДОП] внутренняя оценка часа ручного слоя

def net(route, gross):
    return gross * NET[route]

def rng(v):
    return (v, v) if isinstance(v, (int, float)) else v

# =====================================================================
# МИКС МОНЕТИЗАЦИИ ПО БРЕНДАМ (FP §4: >=3 потока/бренд, один поток <=60% net)
# =====================================================================
# Три бренда F_PILOT: Wardogs (RP-гейминг), Facts (evergreen), Psychology (evergreen)
# Каждому бренду присвоен микс из 8 потоков [FP §4, ранжирование по net и юр-чистоте]

BRAND_MIX = {
    "Wardogs": {
        # RP-гейминг: клиппинг ядро, донаты с фан-базы, CPA гейминг-офферы
        "Klipni":  0.40,   # быстрые деньги с дня 1
        "Boosty":  0.25,   # донат-мост RP-фанатов
        "CPA":     0.20,   # гейминг-офферы в описаниях
        "Stars":   0.15,   # TG-канал как дистрибуция
        # VK-серии не планируются в М1-М3 (ниша чистый клиппинг)
    },
    "Facts": {
        # Evergreen: VK-партнёрка ядро (оригинальный контент), CPA фин/edtech, Boosty
        "VK":      0.45,   # после порога (Д60-90) — в М1 0
        "CPA":     0.30,   # финпродукты/edtech — высокий CPM ниши
        "Boosty":  0.15,   # подписки/донаты
        "Klipni":  0.10,   # клиппинг-дополнение
    },
    "Psychology": {
        # Evergreen: VK-партнёрка + Track B услуги (психологическая ниша подходит для аватар-консультаций)
        "VK":      0.40,   # после порога
        "Boosty":  0.25,   # платное сообщество (класс 12 F)
        "TrackB":  0.20,   # аватар-услуги (психолог-аватар)
        "CPA":     0.15,   # edtech/психология-курсы
    },
}

# Доля каждого бренда в общем объёме клипов [FP §1: Wardogs 3, facts 4, psychology 4 из 11 мастеров]
BRAND_SHARE = {"Wardogs": 3/11, "Facts": 4/11, "Psychology": 4/11}

# =====================================================================
# СЦЕНАРИИ: М1/М3/М6 × 3 ветки
# Драйверы V1 + новые потоки (Boosty подписки, Stars донаты, CPA, Track B)
# =====================================================================

SCEN = {
    # ---------- МЕСЯЦ 1 ----------
    "M1_conservative": dict(
        label="М1 консерв.",
        clips=10, views_per_clip=2000,   # kill-floor D14
        # М1: VK-порог не взят, поэтому VK-потоки заменяются на пропорциональный рост других
        vk_threshold=False,
        boosty_subs=0, boosty_avg_check=0,     # ДОПУЩЕНИЕ: нет аудитории → 0 подписок
        stars_donations_rub=0,                  # ДОПУЩЕНИЕ: нет TG-аудитории
        cpa_revenue_rub=0,                      # ДОПУЩЕНИЕ: нет кликов без охвата
        avatar_orders=0,
        integrations=0,
        note="Первый пакет. Только клиппинг Wardogs. Остальные потоки = 0 (нет аудитории)."),

    "M1_base": dict(
        label="М1 базовый",
        clips=20, views_per_clip=5000,
        vk_threshold=False,
        boosty_subs=5, boosty_avg_check=150,    # ДОПУЩЕНИЕ: 5 ранних подписчиков × 150₽ [ST стек 5 нижняя граница]
        stars_donations_rub=500,                # ДОПУЩЕНИЕ: первые донаты TG
        cpa_revenue_rub=1000,                   # ДОПУЩЕНИЕ: первые переходы (LOW conf)
        avatar_orders=0,
        integrations=0,
        note="5 дней/нед. Минимальные Boosty/Stars/CPA — первые живые рубли помимо клиппинга."),

    "M1_aggressive": dict(
        label="М1 агресс.",
        clips=40, views_per_clip=10000,
        vk_threshold=False,
        boosty_subs=20, boosty_avg_check=200,   # ДОПУЩЕНИЕ: виральный клип привёл 20 подписок
        stars_donations_rub=2000,               # ДОПУЩЕНИЕ: активные донаты с виральности
        cpa_revenue_rub=4000,                   # ДОПУЩЕНИЕ: 40 клипов с CPA-ссылками
        avatar_orders=1,
        integrations=0,
        note="2 канала × 1 клип/день. Виральный клип. 1 заказ Track B."),

    # ---------- МЕСЯЦ 3 ----------
    "M3_conservative": dict(
        label="М3 консерв.",
        clips=60, views_per_clip=3000,
        vk_threshold=False,                     # порог не взят
        boosty_subs=15, boosty_avg_check=200,
        stars_donations_rub=1500,
        cpa_revenue_rub=3000,
        avatar_orders=0,
        integrations=0,
        series=20, series_views=2000, series_monetized=False,
        note="VK-порог не взят. Скромные донаты. Клиппинг медиана ниже F-нижней."),

    "M3_base": dict(
        label="М3 базовый",
        clips=60, views_per_clip=5000,
        vk_threshold=True,                      # VK взят на 1-2 каналах Facts/Psychology
        boosty_subs=50, boosty_avg_check=250,
        stars_donations_rub=5000,
        cpa_revenue_rub=10000,
        avatar_orders=2,
        integrations=0,
        series=30, series_views=8000, series_monetized=True, series_niche_rate="vk_niche_fact_rub_per_1k",
        note="VK-порог взят на 1 канале. Boosty растёт. CPA первые выплаты."),

    "M3_aggressive": dict(
        label="М3 агресс.",
        clips=90, views_per_clip=10000,
        vk_threshold=True,
        boosty_subs=120, boosty_avg_check=300,
        stars_donations_rub=12000,
        cpa_revenue_rub=25000,
        avatar_orders=5,
        integrations=1, integrations_rub=8000,   # ДОПУЩЕНИЕ: первая спонсорская вставка
        series=40, series_views=15000, series_monetized=True, series_niche_rate="vk_niche_fact_rub_per_1k",
        note="3-4 канала, hook-ladder откалиброван. 5 заказов Track B. Первая интеграция."),

    # ---------- МЕСЯЦ 6 ----------
    "M6_conservative": dict(
        label="М6 консерв.",
        clips=90, views_per_clip=4000,
        vk_threshold=True,
        boosty_subs=80, boosty_avg_check=250,
        stars_donations_rub=5000,
        cpa_revenue_rub=8000,
        avatar_orders=1,
        integrations=0,
        series=40, series_views=5000, series_monetized=True, series_niche_rate="vk_rub_per_1k",
        note="Медленный рост. VK на нижней ставке 20-60₽."),

    "M6_base": dict(
        label="М6 базовый",
        clips=120, views_per_clip=8000,
        vk_threshold=True,
        boosty_subs=200, boosty_avg_check=300,
        stars_donations_rub=15000,
        cpa_revenue_rub=30000,
        avatar_orders=5,
        integrations=2, integrations_rub=10000,
        series=60, series_views=10000, series_monetized=True, series_niche_rate="vk_niche_fact_rub_per_1k",
        note="4-5 каналов. ~1М просм/мес. 200 Boosty-подписчиков. 2 интеграции."),

    "M6_aggressive": dict(
        label="М6 агресс.",
        clips=180, views_per_clip=15000,
        vk_threshold=True,
        boosty_subs=500, boosty_avg_check=350,
        stars_donations_rub=40000,
        cpa_revenue_rub=80000,
        avatar_orders=10,
        integrations=4, integrations_rub=15000,
        series=80, series_views=20000, series_monetized=True, series_niche_rate="vk_niche_fact_rub_per_1k",
        note="5-6 каналов, 2 виральных. 500 Boosty-подписчиков. Track B ретейнер. 4 интеграции."),
}

AVATAR_PRICE = (4000.0, 7000.0)   # [V4 §2 Track B]
AVATAR_NET = 0.94

def run(s):
    views_1k = s["clips"] * s["views_per_clip"] / 1000.0

    # Распределяем просмотры по брендам, у каждого свой микс
    gross_by_stream = {}
    for brand, share in BRAND_SHARE.items():
        brand_views = views_1k * share
        mix = BRAND_MIX[brand]
        for stream, stream_share in mix.items():
            if stream == "VK" and not s.get("vk_threshold"):
                continue  # порог не взят — поток не работает
            v = brand_views * stream_share
            if stream == "Klipni":
                g = v * RATES["klipni_wardogs_rub_per_1k"]
            elif stream == "VK":
                lo, hi = RATES["vk_rub_per_1k"]
                g = v * ((lo + hi) / 2)
            elif stream == "DareBay":
                lo, hi = RATES["darebay_usd_per_1k"]
                g = v * ((lo + hi) / 2) * RUB_PER_USD
            else:
                continue  # Boosty/Stars/CPA/TrackB/Integr — не по просмотрам
            gross_by_stream[stream] = gross_by_stream.get(stream, 0) + g

    # VK-серии (отдельный слой, только если порог взят)
    series_gross = 0.0
    sv_1k = 0.0
    if s.get("series_monetized") and s.get("series", 0) > 0:
        sv_1k = s["series"] * s["series_views"] / 1000.0
        lo, hi = RATES[s["series_niche_rate"]]
        series_gross = sv_1k * ((lo + hi) / 2)
        gross_by_stream["VK"] = gross_by_stream.get("VK", 0) + series_gross
    elif s.get("series", 0) > 0:
        sv_1k = s["series"] * s["series_views"] / 1000.0

    # Потоки, не привязанные к просмотрам (gross)
    boosty_gross = s.get("boosty_subs", 0) * s.get("boosty_avg_check", 0)
    if boosty_gross:
        gross_by_stream["Boosty"] = gross_by_stream.get("Boosty", 0) + boosty_gross

    stars_gross = s.get("stars_donations_rub", 0)
    if stars_gross:
        gross_by_stream["Stars"] = gross_by_stream.get("Stars", 0) + stars_gross

    cpa_gross = s.get("cpa_revenue_rub", 0)
    if cpa_gross:
        gross_by_stream["CPA"] = gross_by_stream.get("CPA", 0) + cpa_gross

    av_lo, av_hi = AVATAR_PRICE
    avatar_gross = s.get("avatar_orders", 0) * ((av_lo + av_hi) / 2)
    if avatar_gross:
        gross_by_stream["TrackB"] = gross_by_stream.get("TrackB", 0) + avatar_gross

    integr_gross = s.get("integrations", 0) * s.get("integrations_rub", 0)
    if integr_gross:
        gross_by_stream["Integr"] = gross_by_stream.get("Integr", 0) + integr_gross

    # Net по каждому потоку
    net_by_stream = {}
    for stream, g in gross_by_stream.items():
        net_by_stream[stream] = net(stream, g)

    gross_total = sum(gross_by_stream.values())
    net_total = sum(net_by_stream.values())

    # Доли потоков в net (проверка правила <=60%)
    shares = {st: (n / net_total * 100 if net_total else 0) for st, n in net_by_stream.items()}
    max_share = max(shares.values()) if shares else 0
    max_stream = max(shares, key=shares.get) if shares else None
    n_streams = len([s2 for s2 in net_by_stream.values() if s2 > 0])

    # Трудоёмкость
    platforms_per_clip = 3
    c_lo, c_hi = COSTS["clip_master_labor_min"]
    a_lo, a_hi = COSTS["clip_adapt_min"]
    clip_min = s["clips"] * ((c_lo + c_hi) / 2 + (platforms_per_clip - 1) * ((a_lo + a_hi) / 2))
    s_lo, s_hi = COSTS["series_labor_min"]
    series_min = s.get("series", 0) * (s_lo + s_hi) / 2
    avm_lo, avm_hi = COSTS["avatar_labor_min"]
    avatar_min = s.get("avatar_orders", 0) * (avm_lo + avm_hi) / 2
    labor_h = (clip_min + series_min + avatar_min) / 60.0

    cash = s.get("avatar_orders", 0) * (sum(COSTS["avatar_cash_prod"]) / 2) if s.get("avatar_orders") else 0.0

    return dict(
        label=s["label"], clips=s["clips"], series=s.get("series", 0),
        avatar_orders=s.get("avatar_orders", 0),
        total_views_1k=round(views_1k + sv_1k, 1),
        gross=round(gross_total), net=round(net_total),
        cash_cost=round(cash), labor_h=round(labor_h, 1),
        net_after_cash=round(net_total - cash),
        rub_per_hour=round((net_total - cash) / labor_h) if labor_h else None,
        n_streams=n_streams,
        max_share=round(max_share, 1), max_stream=max_stream,
        net_by_stream={k: round(v) for k, v in net_by_stream.items()},
        shares={k: round(v, 1) for k, v in shares.items()},
        note=s["note"],
    )

# =====================================================================
# ВЫВОД
# =====================================================================
print(f"{'сценарий':<14} {'кл':>3} {'сер':>3} {'зак':>3} {'просм,к':>8} {'gross₽':>8} {'net₽':>8} {'cash':>5} {'часы':>6} {'₽/ч':>6} {'N_потоков':>9} {'max_доля%':>9} {'max_поток':>8}")
print("-" * 120)
results = {}
for k in SCEN:
    r = run(SCEN[k])
    results[k] = r
    print(f"{r['label']:<14} {r['clips']:>3} {r['series']:>3} {r['avatar_orders']:>3} {r['total_views_1k']:>8} {r['gross']:>8} {r['net']:>8} {r['cash_cost']:>5} {r['labor_h']:>6} {r['rub_per_hour']:>6} {r['n_streams']:>9} {r['max_share']:>9} {str(r['max_stream']):>8}")

print("\n=== ДЕТАЛИЗАЦИЯ ПО ПОТОКАМ (net ₽ / доля %) ===")
for k in SCEN:
    r = results[k]
    print(f"\n{r['label']} ({r['note']}):")
    for st in sorted(r['net_by_stream'], key=r['net_by_stream'].get, reverse=True):
        n = r['net_by_stream'][st]
        sh = r['shares'][st]
        flag = " <<< >60%!" if sh > 60 else ""
        print(f"  {st:>10}: {n:>8}₽  ({sh:>5.1f}%){flag}")
    if r['n_streams'] < 3:
        print(f"  *** НАРУШЕНИЕ FP-правила: только {r['n_streams']} потока (нужно >=3)")

print("\n=== ЧУВСТВИТЕЛЬНОСТЬ М3_base: net₽/мес vs просмотров/клип ===")
base = dict(SCEN["M3_base"])
for v in (1000, 2000, 5000, 10000, 20000, 30000):
    base["views_per_clip"] = v
    r = run(base)
    print(f"  {v:>6}/клип → {r['total_views_1k']:>7}к просм → net {r['net']:>7}₽ (после cash {r['net_after_cash']:>7}₽) · {r['n_streams']} потоков · max доля {r['max_share']}%")

print("\n=== KILL-КРИТЕРИИ V3 (F-MON3, t_e5ae02e0): канон 1-7 из V2 + 8-10 новые ===")
for name, text in [
    ("Kill-8",  "СТОКИ: баланс < $25 на Д90 после старта контрибьютинга -> стоп потока [D11 §11]"),
    ("Kill-9",  "YT MCN: 2 месяца задержки выплат -> разрыв договора / смена сети / отказ от потока [D6 §6]"),
    ("Kill-10", "Зарубежное юрлицо: владелец не дал решения за 30 дней -> закрыть вопрос, 0 ₽-модель [D6 §6]"),
]:
    print(f"  {name:<8} {text}")
print("  (Kill-1..Kill-7 — без изменений, см. FACTORY_ECONOMICS_V2.md §6)")

print("\n=== ЧУВСТВИТЕЛЬНОСТЬ М3_base: net₽/мес vs число Boosty-подписчиков ===")
base = dict(SCEN["M3_base"])
for subs in (0, 20, 50, 100, 200, 300):
    base["boosty_subs"] = subs
    r = run(base)
    print(f"  {subs:>4} подписчиков → net {r['net']:>7}₽ · Boosty доля {r['shares'].get('Boosty', 0):.1f}%")

print("\n=== СРАВНЕНИЕ V1 vs V2 (только Klipni+VK+DareBay vs микс 8 потоков) ===")
# V1 М1 базовый: 2232₽, М3 базовый: 32224₽, М6 базовый: 90578₽
v1 = {"M1_base": 2232, "M3_base": 32224, "M6_base": 90578}
for k in ("M1_base", "M3_base", "M6_base"):
    v2 = results[k]['net']
    delta = v2 - v1[k]
    pct = (delta / v1[k] * 100) if v1[k] else 0
    print(f"  {k}: V1={v1[k]:>7}₽ → V2={v2:>7}₽ (Δ {delta:+7}₽, {pct:+.0f}%)")
