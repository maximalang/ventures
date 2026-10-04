# FACTORY_ECONOMICS_V3.py — воспроизводимая модель юнит-экономики контент-завода
# Карта F-MON3 (t_e5ae02e0), 24.09.2026. Роль: finance. Paid=0 (read-only расчёт).
# Запуск: python factory_econ_calc_v3.py  (python 3.8+, stdlib only)
#
# Отличие V3 от V2 (t_17058bf6): применены delta-корректировки MON-V7-B (DEEP_V7 §11)
# и MON-V7-D (WORKAROUNDS_D §6):
#   * net-коэффициенты Klipni/Boosty/CPA/Integr пересчитаны (НПД 4% вместо 6%, точные комиссии)
#   * добавлены Kill-8 (стоки), Kill-9 (MCN задержки), Kill-10 (зарубежное юрлицо)
#   * YT MCN-поток НЕ в базовой ветке (триггер 250к просм/мес), смоделирован отдельным блоком
#   * стоки НЕ в базе до М3 (рекомендация DEEP_V7 §11) — отдельный триггерный расчёт
#   * UGC-брифы = расширение потока Klipni (внутри строки Klipni, антидвойной счёт)
#   * TG-интеграции (Epicstars от 1000 подп.) — активация потока Integr раньше Д60, помечено
#
# Каждая ставка — источник или явное ДОПУЩЕНИЕ. Источники V3:
# [D11]=MONETIZATION_DEEP_V7.md §11 (MON-V7-B, 24.09.2026)
# [D6]=MONETIZATION_WORKAROUNDS_D.md §6 (MON-V7-D, 24.09.2026)
# База V2: [MR]=MONEY_ROUTES.md · [FP]=F_PILOT_PACKAGE.md §4 · [V4]=VIDEO_STRATEGY_V4_DRAFT.md

RUB_PER_USD = 92.0  # [V4 §6, модельный курс — без изменений от V2]

# --- Нетто-коэффициенты маршрутов (доля gross, доходящая до карты) ---
# V3-значения: delta из [D11 таблица «Корректировки net-коэффициентов»] и [D6 §6]
NET = {
    "VK":         0.94,   # БЕЗ ИЗМЕНЕНИЙ (V2). НПД 6% — VK-партнёрка платит юр-контуром, ставка 6% [MR маршрут 2]
    "Klipni":     0.912,  # V2: 0.893 -> V3: 0.912. Комиссия 5% [D11/K2] + НПД 4% (доход от физлиц/агента) [D11/B3, H]
    "Boosty":     0.821,  # V2: 0.883 -> V3: 0.821. 11.7% комиссия [D11/B1] + вывод 2.2%+20руб [D11/B3] + НПД 4% [H]
    "TrackB":     0.96,   # V2: 0.94 -> V3: 0.96. НПД 4% (услуги физлицам) [D11/B3: письмо Минфина 03-11-11/74629, H]
    "Stars":      0.80,   # БЕЗ ИЗМЕНЕНИЙ (V2=[D11]: цепочка 60-85% до карты + НДФЛ 13%, крипто != НПД) [TG5, M]
    "CPA":        0.96,   # V2: 0.94 ДОПУЩЕНИЕ -> V3: 0.96. НПД 4% [D11/B3], erid авто биржей [D11/C2]. ВСЁ ЕЩЁ калибровка до 1-й выплаты (M)
    "YT_RPM":     0.75,   # V2: 0.70 -> V3: 0.75 середина диапазона 0.65-0.85 [D6 §6, канон]. НЕ В БАЗЕ — только триггерный блок.
    "Integr":     0.91,   # V2: 0.87 -> V3: 0.91 (диапазон 0.87-0.96). НПД 4%, erid обязателен [D11, M]
    "DareBay":    0.771,  # БЕЗ ИЗМЕНЕНИЙ (V2). 10% вывод + 1.5% спред + НДФЛ 13% [MR маршрут 3] — крипто-цепочка, НПД неприменим
    "Stocks":     0.86,   # НОВЫЙ поток V3. 0.94 посредник EasyStaff x 0.96 НПД 4% [D6 §6]. НЕ В БАЗЕ до М3 — триггерный блок.
}

# --- Ставки дохода (gross до комиссий/налога) ---
RATES = {
    "klipni_wardogs_rub_per_1k": 25.0,   # [D14 §1, кабинет; частный случай 50-300 руб/1к [D11/K3]]
    "klipni_avg_rub_per_1k":     (30.0, 40.0),  # [TM стр.15]
    "darebay_usd_per_1k":        (1.0, 2.0),    # [MR §2.2, H]
    "vk_rub_per_1k":             (20.0, 60.0),  # [MR §2.1, L-оценки; TM 15-70 по нишам]
    "vk_niche_fact_rub_per_1k":  (40.0, 55.0),  # [TM: образование/история]
    "yt_long_rpm_usd":           10.9,          # [FP §4: сон-серии $10.9 RPM] — ДОПУЩЕНИЕ для нашей ниши, только триггерный блок
    "stars_usd_per_star":        0.013,         # [MR §2.1]
    "stocks_rub_per_file_month": (18.0, 46.0),  # [D11 §11: ~9-23к руб/мес при 500 файлах -> 18-46 руб/файл/мес, S1, M]
}

# --- Себестоимость (без изменений от V2) ---
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

# =====================================================================
# МИКС МОНЕТИЗАЦИИ ПО БРЕНДАМ (FP §4: >=3 потока/бренд, один поток <=60% net)
# Без изменений от V2 — delta не меняет структуру микса [D11 §11: правило >=3/<=60 не пересматривается]
# =====================================================================
BRAND_MIX = {
    "Wardogs": {"Klipni": 0.40, "Boosty": 0.25, "CPA": 0.20, "Stars": 0.15},
    "Facts":   {"VK": 0.45, "CPA": 0.30, "Boosty": 0.15, "Klipni": 0.10},
    "Psychology": {"VK": 0.40, "Boosty": 0.25, "TrackB": 0.20, "CPA": 0.15},
}
BRAND_SHARE = {"Wardogs": 3/11, "Facts": 4/11, "Psychology": 4/11}

# =====================================================================
# СЦЕНАРИИ М1/М3/М6 x 3 ветки — драйверы БЕЗ ИЗМЕНЕНИЙ от V2.
# Обоснование [D11 §11]: добавляемые потоки мелкие (<=20к руб/мес), сглаживают М1-М3,
# но не меняют М6; сценарии по существу не меняются. Меняются только net-коэффициенты.
# =====================================================================
SCEN = {
    "M1_conservative": dict(
        label="М1 консерв.", clips=10, views_per_clip=2000, vk_threshold=False,
        boosty_subs=0, boosty_avg_check=0, stars_donations_rub=0, cpa_revenue_rub=0,
        avatar_orders=0, integrations=0,
        note="Первый пакет. Только клиппинг Wardogs. Остальные потоки = 0 (нет аудитории)."),
    "M1_base": dict(
        label="М1 базовый", clips=20, views_per_clip=5000, vk_threshold=False,
        boosty_subs=5, boosty_avg_check=150, stars_donations_rub=500, cpa_revenue_rub=1000,
        avatar_orders=0, integrations=0,
        note="5 дней/нед. Минимальные Boosty/Stars/CPA — первые живые рубли помимо клиппинга."),
    "M1_aggressive": dict(
        label="М1 агресс.", clips=40, views_per_clip=10000, vk_threshold=False,
        boosty_subs=20, boosty_avg_check=200, stars_donations_rub=2000, cpa_revenue_rub=4000,
        avatar_orders=1, integrations=0,
        note="2 канала x 1 клип/день. Виральный клип. 1 заказ Track B."),
    "M3_conservative": dict(
        label="М3 консерв.", clips=60, views_per_clip=3000, vk_threshold=False,
        boosty_subs=15, boosty_avg_check=200, stars_donations_rub=1500, cpa_revenue_rub=3000,
        avatar_orders=0, integrations=0,
        series=20, series_views=2000, series_monetized=False,
        note="VK-порог не взят. Скромные донаты. Клиппинг медиана ниже F-нижней."),
    "M3_base": dict(
        label="М3 базовый", clips=60, views_per_clip=5000, vk_threshold=True,
        boosty_subs=50, boosty_avg_check=250, stars_donations_rub=5000, cpa_revenue_rub=10000,
        avatar_orders=2, integrations=0,
        series=30, series_views=8000, series_monetized=True, series_niche_rate="vk_niche_fact_rub_per_1k",
        note="VK-порог взят на 1 канале. Boosty растёт. CPA первые выплаты."),
    "M3_aggressive": dict(
        label="М3 агресс.", clips=90, views_per_clip=10000, vk_threshold=True,
        boosty_subs=120, boosty_avg_check=300, stars_donations_rub=12000, cpa_revenue_rub=25000,
        avatar_orders=5, integrations=1, integrations_rub=8000,
        series=40, series_views=15000, series_monetized=True, series_niche_rate="vk_niche_fact_rub_per_1k",
        note="3-4 канала, hook-ladder откалиброван. 5 заказов Track B. Первая интеграция."),
    "M6_conservative": dict(
        label="М6 консерв.", clips=90, views_per_clip=4000, vk_threshold=True,
        boosty_subs=80, boosty_avg_check=250, stars_donations_rub=5000, cpa_revenue_rub=8000,
        avatar_orders=1, integrations=0,
        series=40, series_views=5000, series_monetized=True, series_niche_rate="vk_rub_per_1k",
        note="Медленный рост. VK на нижней ставке 20-60 руб."),
    "M6_base": dict(
        label="М6 базовый", clips=120, views_per_clip=8000, vk_threshold=True,
        boosty_subs=200, boosty_avg_check=300, stars_donations_rub=15000, cpa_revenue_rub=30000,
        avatar_orders=5, integrations=2, integrations_rub=10000,
        series=60, series_views=10000, series_monetized=True, series_niche_rate="vk_niche_fact_rub_per_1k",
        note="4-5 каналов. ~1М просм/мес. 200 Boosty-подписчиков. 2 интеграции."),
    "M6_aggressive": dict(
        label="М6 агресс.", clips=180, views_per_clip=15000, vk_threshold=True,
        boosty_subs=500, boosty_avg_check=350, stars_donations_rub=40000, cpa_revenue_rub=80000,
        avatar_orders=10, integrations=4, integrations_rub=15000,
        series=80, series_views=20000, series_monetized=True, series_niche_rate="vk_niche_fact_rub_per_1k",
        note="5-6 каналов, 2 виральных. 500 Boosty-подписчиков. Track B ретейнер. 4 интеграции."),
}

AVATAR_PRICE = (4000.0, 7000.0)   # [V4 §2 Track B] — [D11 §Track B: рыночная середина 5-8к, наш чек конкурентен, не поднимать до 3 оплат]

def run(s):
    views_1k = s["clips"] * s["views_per_clip"] / 1000.0
    gross_by_stream = {}
    for brand, share in BRAND_SHARE.items():
        brand_views = views_1k * share
        for stream, stream_share in BRAND_MIX[brand].items():
            if stream == "VK" and not s.get("vk_threshold"):
                continue
            v = brand_views * stream_share
            if stream == "Klipni":
                g = v * RATES["klipni_wardogs_rub_per_1k"]
            elif stream == "VK":
                lo, hi = RATES["vk_rub_per_1k"]; g = v * ((lo + hi) / 2)
            elif stream == "DareBay":
                lo, hi = RATES["darebay_usd_per_1k"]; g = v * ((lo + hi) / 2) * RUB_PER_USD
            else:
                continue  # Boosty/Stars/CPA/TrackB/Integr — не по просмотрам
            gross_by_stream[stream] = gross_by_stream.get(stream, 0) + g

    series_gross = 0.0; sv_1k = 0.0
    if s.get("series_monetized") and s.get("series", 0) > 0:
        sv_1k = s["series"] * s["series_views"] / 1000.0
        lo, hi = RATES[s["series_niche_rate"]]
        series_gross = sv_1k * ((lo + hi) / 2)
        gross_by_stream["VK"] = gross_by_stream.get("VK", 0) + series_gross
    elif s.get("series", 0) > 0:
        sv_1k = s["series"] * s["series_views"] / 1000.0

    if s.get("boosty_subs", 0) * s.get("boosty_avg_check", 0):
        gross_by_stream["Boosty"] = gross_by_stream.get("Boosty", 0) + s["boosty_subs"] * s["boosty_avg_check"]
    if s.get("stars_donations_rub", 0):
        gross_by_stream["Stars"] = gross_by_stream.get("Stars", 0) + s["stars_donations_rub"]
    if s.get("cpa_revenue_rub", 0):
        gross_by_stream["CPA"] = gross_by_stream.get("CPA", 0) + s["cpa_revenue_rub"]
    av_lo, av_hi = AVATAR_PRICE
    if s.get("avatar_orders", 0):
        gross_by_stream["TrackB"] = gross_by_stream.get("TrackB", 0) + s["avatar_orders"] * ((av_lo + av_hi) / 2)
    if s.get("integrations", 0) * s.get("integrations_rub", 0):
        gross_by_stream["Integr"] = gross_by_stream.get("Integr", 0) + s["integrations"] * s["integrations_rub"]

    net_by_stream = {st: net(st, g) for st, g in gross_by_stream.items()}
    gross_total = sum(gross_by_stream.values()); net_total = sum(net_by_stream.values())
    shares = {st: (n / net_total * 100 if net_total else 0) for st, n in net_by_stream.items()}
    max_share = max(shares.values()) if shares else 0
    max_stream = max(shares, key=shares.get) if shares else None
    n_streams = len([v for v in net_by_stream.values() if v > 0])

    platforms_per_clip = 3
    c_lo, c_hi = COSTS["clip_master_labor_min"]; a_lo, a_hi = COSTS["clip_adapt_min"]
    clip_min = s["clips"] * ((c_lo + c_hi) / 2 + (platforms_per_clip - 1) * ((a_lo + a_hi) / 2))
    s_lo, s_hi = COSTS["series_labor_min"]
    series_min = s.get("series", 0) * (s_lo + s_hi) / 2
    avm_lo, avm_hi = COSTS["avatar_labor_min"]
    avatar_min = s.get("avatar_orders", 0) * (avm_lo + avm_hi) / 2
    labor_h = (clip_min + series_min + avatar_min) / 60.0
    cash = s.get("avatar_orders", 0) * (sum(COSTS["avatar_cash_prod"]) / 2) if s.get("avatar_orders") else 0.0

    return dict(label=s["label"], clips=s["clips"], series=s.get("series", 0),
        avatar_orders=s.get("avatar_orders", 0), total_views_1k=round(views_1k + sv_1k, 1),
        gross=round(gross_total), net=round(net_total), cash_cost=round(cash),
        labor_h=round(labor_h, 1), net_after_cash=round(net_total - cash),
        rub_per_hour=round((net_total - cash) / labor_h) if labor_h else None,
        n_streams=n_streams, max_share=round(max_share, 1), max_stream=max_stream,
        net_by_stream={k: round(v) for k, v in net_by_stream.items()},
        shares={k: round(v, 1) for k, v in shares.items()}, note=s["note"])

# =====================================================================
# ВЫВОД: базовые сценарии V3
# =====================================================================
print("=" * 124)
print("FACTORY_ECONOMICS_V3 (F-MON3, t_e5ae02e0) — база с delta-коэффициентами MON-V7-B/D")
print("=" * 124)
print(f"{'сценарий':<14} {'кл':>3} {'сер':>3} {'зак':>3} {'просм,к':>8} {'gross₽':>8} {'net₽':>8} {'cash':>5} {'часы':>6} {'₽/ч':>6} {'N_потоков':>9} {'max_доля%':>9} {'max_поток':>8}")
print("-" * 124)
results = {}
for k in SCEN:
    r = run(SCEN[k]); results[k] = r
    print(f"{r['label']:<14} {r['clips']:>3} {r['series']:>3} {r['avatar_orders']:>3} {r['total_views_1k']:>8} {r['gross']:>8} {r['net']:>8} {r['cash_cost']:>5} {r['labor_h']:>6} {r['rub_per_hour']:>6} {r['n_streams']:>9} {r['max_share']:>9} {str(r['max_stream']):>8}")

# --- Сравнение V2 vs V3 (те же сценарии, старые коэффициенты) ---
NET_V2 = {"VK": 0.94, "Klipni": 0.893, "Boosty": 0.883, "TrackB": 0.94, "Stars": 0.80,
          "CPA": 0.94, "YT_RPM": 0.70, "Integr": 0.87, "DareBay": 0.771}
def run_with_net(s, net_table):
    global NET
    saved = NET; NET = net_table
    try:
        return run(s)
    finally:
        NET = saved

print("\n=== DELTA V2 -> V3 (те же драйверы сценариев, только коэффициенты) ===")
print(f"{'сценарий':<14} {'net_V2':>9} {'net_V3':>9} {'Δ₽':>8} {'Δ%':>6}")
for k in SCEN:
    r2 = run_with_net(SCEN[k], NET_V2); r3 = results[k]
    d = r3['net'] - r2['net']; pct = (d / r2['net'] * 100) if r2['net'] else 0
    print(f"{r3['label']:<14} {r2['net']:>9} {r3['net']:>9} {d:>+8} {pct:>+6.1f}")

print("\n=== ДЕТАЛИЗАЦИЯ ПО ПОТОКАМ V3 (net ₽ / доля %) ===")
for k in SCEN:
    r = results[k]
    print(f"\n{r['label']} ({r['note']}):")
    for st in sorted(r['net_by_stream'], key=r['net_by_stream'].get, reverse=True):
        n = r['net_by_stream'][st]; sh = r['shares'][st]
        flag = " <<< >60%!" if sh > 60 else ""
        print(f"  {st:>10}: {n:>8}₽  ({sh:>5.1f}%){flag}")
    if r['n_streams'] < 3:
        print(f"  *** НАРУШЕНИЕ FP-правила: только {r['n_streams']} потока (нужно >=3)")

# =====================================================================
# ОТДЕЛЬНЫЙ ТРИГГЕРНЫЙ БЛОК (НЕ входит в базу): YT MCN + Стоки
# [D6 §6]: YT MCN = null до триггера 250к просм/мес; стоки не в базе до М3 [D11 §11]
# =====================================================================
print("\n" + "=" * 124)
print("ТРИГГЕРНЫЙ БЛОК (НЕ в базе М1-М6): YT MCN при 250к+ просм/мес + Стоки при М3+")
print("=" * 124)
print("YT MCN: net-коэффициент канон 0.65-0.85 [D6 §6]; RPM $10.9 [FP §4, ДОПУЩЕНИЕ для ниши]; курс 92₽/$ [V4 §6]")
print(f"{'YT просм/мес':>14} {'gross$':>8} {'gross₽':>9} {'net@0.65':>9} {'net@0.75':>9} {'net@0.85':>9}")
for views in (250_000, 500_000, 1_000_000, 4_300_000):
    gross_usd = views / 1000 * RATES["yt_long_rpm_usd"]
    gross_rub = gross_usd * RUB_PER_USD
    print(f"{views:>14,} {gross_usd:>8.0f} {gross_rub:>9.0f} {gross_rub*0.65:>9.0f} {gross_rub*0.75:>9.0f} {gross_rub*0.85:>9.0f}")
print("Примечание: 4.3М просм/мес = М6 агрессивный уровень V3 (справочно). Kill-9: 2 мес задержки выплат -> разрыв.")

print("\nСТОКИ (EasyStaff 6% посредник, net 0.86 [D6 §6]): ставка 18-46 ₽/файл/мес [D11 §11 от 9-23к при 500 файлах]")
print(f"{'файлов':>8} {'gross₽/мес low':>15} {'gross₽/мес high':>16} {'net₽/мес low':>13} {'net₽/мес high':>14}")
lo, hi = RATES["stocks_rub_per_file_month"]
for files in (100, 300, 500, 1000):
    gl, gh = files * lo, files * hi
    print(f"{files:>8} {gl:>15.0f} {gh:>16.0f} {gl*NET['Stocks']:>13.0f} {gh*NET['Stocks']:>14.0f}")
print("Примечание: маржинальная стоимость ~0 (переиспользование артов завода). Kill-8: <$25 баланс на Д90 -> стоп.")

# =====================================================================
# KILL-КРИТЕРИИ V3 (1-7 из V2 без изменений + 8-10 новые)
# =====================================================================
print("\n=== KILL-КРИТЕРИИ V3 (канон после F-MON3) ===")
kills = [
    ("Kill-1", "Медиана подтверждённых просмотров клипа < 2 000 при 30+ клипах -> контент-пивот (Д30)", "V2"),
    ("Kill-2", "Доход/час < 500 ₽/ч при 50+ часах ручного слоя -> стоп ручных форматов (Д30)", "V2"),
    ("Kill-3", "Любой поток > 60% net бренда на Д30 -> ребаланс микса до Д45 (сигнал)", "V2"),
    ("Kill-4", "Track B: нет >=3 запросов / 1 оплаты за 2 нед оффера -> оффер отключается", "V2"),
    ("Kill-5", "Boosty: < 10 платящих подписчиков суммарно на Д60 -> пересмотр платного слоя", "V2"),
    ("Kill-6", "CPA: 0 подтверждённых выплат при 100+ кликах на Д30 -> замена офферов", "V2"),
    ("Kill-7", "Д30 = М1 консерв. (только Klipni, 1 поток) -> микс-гипотеза не подтверждена", "V2"),
    ("Kill-8", "СТОКИ: баланс < $25 на Д90 после старта контрибьютинга -> стоп потока", "V3 [D11 §11]"),
    ("Kill-9", "YT MCN: 2 месяца задержки выплат -> разрыв договора / смена сети / отказ от потока", "V3 [D6 §6]"),
    ("Kill-10", "Зарубежное юрлицо: владелец не дал решения за 30 дней -> закрыть вопрос, 0 ₽-модель", "V3 [D6 §6]"),
]
for name, text, src in kills:
    print(f"  {name:<8} [{src:<12}] {text}")

print("\n=== ЧУВСТВИТЕЛЬНОСТЬ М3_base V3: net₽/мес vs просмотров/клип ===")
base = dict(SCEN["M3_base"])
for v in (1000, 2000, 5000, 10000, 20000, 30000):
    base["views_per_clip"] = v; r = run(base)
    print(f"  {v:>6}/клип -> {r['total_views_1k']:>7}к просм -> net {r['net']:>7}₽ (после cash {r['net_after_cash']:>7}₽) · {r['n_streams']} потоков · max доля {r['max_share']}%")

print("\n=== ЧУВСТВИТЕЛЬНОСТЬ М3_base V3: net₽/мес vs число Boosty-подписчиков ===")
base = dict(SCEN["M3_base"])
for subs in (0, 20, 50, 100, 200, 300):
    base["boosty_subs"] = subs; r = run(base)
    print(f"  {subs:>4} подписчиков -> net {r['net']:>7}₽ · Boosty доля {r['shares'].get('Boosty', 0):.1f}%")
