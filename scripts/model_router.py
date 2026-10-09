#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""model_router.py — автороутер флота «Рельсы v6.1» (ROUTES v6.1, карта t_d4ddabc1, ред. 08.10.2026; база v6.0 t_92cce51d, commit 20eb325).

Логика: задача → класс → упорядоченный список моделей → первый подходящий;
неудача/блок → шаг вправо (явный пер-картовый пин с причиной, лог — фаза C).
Только stdlib, 0 сети, 0 LLM, 0 pip. Единый источник правды: ROUTES/RULES/
PATTERNS/INVARIANTS внутри этого файла; внешних данных и фикстур нет.

Канон: ventures/docs/fleet-ops/model-routing-20261003/PROGRAM.md (v2.2),
SPEC-routing-matrix-router.md, SPEC-router-v4-hardening.md, fleet-doctrine SKILL.md (числа),
OPEN-QUESTIONS-20261004.md (директива владельца 04.10 — разбиение по классам сохранено;
GPT=мозг/DashScope=руки как запрет семьи ОТМЕНЁН директивой 07.10 вечер),
LADDER-PROVIDERS.md (T1/T2/T3, правила лестницы), PATTERNS-SOURCES-v2.md (PATTERNS v2 —
5 слоёв + источники на каждую модель, карта t_234de1e7; сверка 2026-10-04).
Bench-first канон v5.2: DIRECTIVE-bench-first-20261007-evening.md (в ветке, тот же
каталог; owner directive 07.10.2026 вечер) + program-level досье evidence:
docs/fleet-ops/model-routing-20261003/dossiers-v5/DOSSIER-A-v4-classes.md и
DOSSIER-B-v5-vision.md со снапшотами 07.10.2026 (program dir, в ветку не входят),
SPEC-routes-v5-bench-evidence.md (07.10.2026, program dir).

Дельты v5 (поверх v3.1, engine v4 → v5):
- bench-evidence порядок рельсов по классам: каждый ROUTES why цитирует ≥1 открытый
  бенч с источником и датой (структурная проверка);
- R5 restriction (defect #5 спеки v5): keyword-переклассификация срабатывает ТОЛЬКО
  при отсутствующем/неизвестном task_type; declared маркер никогда silently не
  флипается кросс-семейно (code + data-ключевые слова → остаётся code, сигнал в reason);
- R9 advisory split: mixed-карта (сигналы ≥2 семейств knowledge↔exec) → verdict несёт
  split-план subtask → class → first live rail; advisory only — исполнение декомпозиции
  у диспетчера/brain на нативных примитивах, параллельного execution-слоя нет;
- vision why: исправлена атрибуция PerceptionBench (defect #4 спеки, divergence D6);
- mode остаётся shadow (MODE константа в verdict; enforce — отдельное измеренное решение);

Дельты v5.1 (карта t_4e040c85; NO-GO QA t_835a9600 → binding DECISIONS t_28337b5a, 07.10.2026):
- §3 BLOCK-1: R1 fail-closed — author-exclusion review_nature (declared task_type=review ИЛИ
  финальный класс review) никогда не отменяется; пустой список → fail-closed degrade-вердикт
  PROFILE_DEFAULT с причиной «R1 author-exclusion: независимый кандидат недоступен — review
  деградирован в профильный дефолт, авторское review запрещено», rules_fired содержит R1;
- §3 BLOCK-2: declared review — маркер записи: protected-ключевое слово БЕЗ owner_facing НЕ
  флипает его в strategic (сигнал логируется); owner_facing=true может элеваировать (тогда
  R1 + astra-гвард на поднятом классе); ASTRA AUTO-SELECT GUARD: gpt-6-astra никогда не
  авто-выбирается ни в одном классе («astra — ручной пин; авто-выбор запрещён»);
- §3 BLOCK-3: _split_plan потребляет тот же availability-снимок; first_rail = первая живая
  рельса; все рельсы класса down → first_rail=PROFILE_DEFAULT + degrade-нота (parity с R7);
- §1 BLOCK-4: ladder-порядки СОХРАНЕНЫ (code/ops как в v5); V5_ADJACENCY_EXEMPT (тихий
  байпасс) удалён → явная запись ADJACENCY_RELAXATIONS {reason, authority, trigger};
  hard-клаузы (a) позиции 1-2 разные провайдеры, (b) ≤2 на провайдера, (c) ≥2 провайдеров —
  enforced selftest для всех не-DIVERSITY_EXEMPT классов;
- §2 BLOCK-5: vision = [gpt-6-luna, qwen-vl-max] (pyramid :46-48 + v10 «Взгляд=luna→qwen-vl»;
  смена только словом владельца/живым A/B); PerceptionBench 0.635=Qwen3.8 Max / 0.585=Kimi K3
  цитируется ТОЛЬКО как исправление атрибуции D6; телеметрия ≠ доказательство качества
  (vision/brief/creative why переформулированы); досье B = t_3e65166e (§4: t_47ba0f58 и
  t_597bb6a7 — phantom id, disposition t_28337b5a §4);
- сохранены: упорядоченные рельсы, rung advance на prior_run_failed (R4), availability
  skip до выбора (S1), degrade over invention (R7), review ≠ author_model (R1),
  PATTERNS на каждую рельсу ROUTES, паттерны traceable к vendor-докам.

Дельты v5.2 (карта t_c8f13333; binding owner directive 07.10.2026 вечер,
DIRECTIVE-bench-first-20261007-evening.md — аддендум к DECISIONS, лендится этим коммитом;
независимая QA t_c592f1c0 по базе 073e1b26 завершена ДО этой правки):
- BENCH-FIRST: иерархия «owner-канон выше бенчей» для ПОРЯДКОВ моделей отменена —
  порядок кандидатов чинят открытые бенчи и измеренные A/B; доверие: независимый
  прогон (HIGH) > vendor self-report (MED/LOW); vendor-число никогда не бьёт
  независимое; где независимых чисел нет — gap помечается, традицией не заполняется;
- флипы: code → sol#1 (TB4.0 58.2% HIGH > glm 41.8%); ops → deepseek-v4-flash#1
  (AutomationBench-AA 68.9% > glm 62%, оба независимые — ОТМЕНЕНО v5.3: 68.9% =
  DeepSeek V4.1 Flash ≠ допущенная 0731=54.0%, QA t_62e0e936 B1 → glm#1); data → qwen#1 (измеренный
  A/B 02.09: сохранение 3/3 vs kimi 0/3); research → glm#1 (hallucination 29.6%
  AA-Omniscience — лучший измеренный); brief/creative → qwen#1, kimi#2 (AA-Briefcase
  Elo: цитата «1640 > 1505 > luna 1299, снятие 24.09.2026» ОТЗВАНА v5.3.2 F2/G1 — нет
  сохранённого источника; сохранённая primary 07.10.2026: 1621 > 1501 > luna 1336,
  порядок тот же); review/strategic/vision — incumbent, gap-marked
  (нет открытого бенча класса / нет пары astra-vs-sol-6.1 / нет vision-бенча);
- R8 переписано: data-порядок теперь ЗАДАЁТСЯ измеренным A/B 02.09 (тест, не
  инструкция) — qwen №1; kimi-рельса на data сохраняет обязательный
  backup/no-destructive контракт;
- ASTRA AUTO-SELECT GUARD снят (директива: запрет «astra — только ручной пин» отменён
  как вкусовой); astra занимает место по измеренному качеству, но до A/B-прогона
  astra-vs-sol-6.1 она НЕ #1 нигде (evidence-gap, не запрет);
- статусы «D1/D3/D7 — ждём слова владельца» сняты: divergence D1/D2/D3/D7 RESOLVED
  этой директивой (таблица в ROUTES-V5-CHANGELOG.md); новых owner-question маркеров
  в ROUTES нет (структурная проверка);
- V10_HEADS-лок заменён на V52_HEADS (головы = bench-evidence таблица v5.2); owner
  v10 остаётся tie-breaker там, где независимых чисел нет (review/vision/strategic);
- hard-клауза (a) (первые две позиции — разные провайдеры) может быть покрыта явной
  записью ADJACENCY_RELAXATIONS с covers_clause_a=true {reason, authority, trigger} —
  только там, где evidence ставит две рельсы одного провайдера выше всех измеренных
  альтернатив (brief/creative: qwen 1621 > kimi 1501 > luna 1336 — сохранённая primary
  07.10.2026; цитата 24.09 «1640 > 1505 > 1299» отозвана v5.3.2, F2/G1);
- НЕ отменено (механика качества): R1 author-exclusion fail-closed, R6 детерминизм,
  R7 явный degrade, квота-гварды пулов (availability-слой — «кто жив»), S1, R4, R9,
  режим shadow, PATTERNS на каждую рельсу.

Дельты v5.3 (карта t_6f4c4809; bounded repair по NO-GO QA t_62e0e936, 07.10.2026):
- B1 (HIGH): ops-порядок исправлен → glm-5.3 №1 (AutomationBench-AA 62%,
  artificialanalysis.ai, live 07.10.2026, HIGH) → qwen3.8-max №2 (канон Round-2 02.09;
  публичного AutomationBench-AA числа нет — gap) → deepseek-v4-flash №3 (хвост SUPERSEDED
  v5.3.1 correction #1: flash №2 измеренная 54.0% → qwen №3 явный GAP-MARK). Причина:
  цитата v5.2 «flash №1 — 68.9%» относится к DeepSeek V4.1 Flash (рельса НЕ допущена
  LADDER); допущенная рельса deepseek-v4-flash-0731 = 54.0% по цитированному
  AA-сравнению в той же статье (traictory.com, 15.09.2026) < glm 62% — winner-claim
  снят; соседняя пара qwen→flash (обе custom) покрыта ADJACENCY_RELAXATIONS;
- B2 (HIGH): R1 author-exclusion распространён на advisory split — review-записи
  плана исключают author_model; author-only → first_rail=PROFILE_DEFAULT + R7-shaped
  маркер (parity с fail-closed вердиктом основного пути); +2 selftest-фикстуры;
- B3 (MEDIUM): vision why — честная формулировка gap: опубликованное покрытие ЕСТЬ
  (AA-MMMU-Pro, benchlm.ai, снапшот 07.10.2026: gpt-6.1-sol 86.0% #3, gpt-6-luna
  79.7% #21), но точной пары luna-vs-qwen-vl-max оно НЕ покрывает → ранжирование =
  прямой флот A/B (VISION-SLOT-PROOF-20261007.md, t_432cd7ef: luna 10/10 vs
  qwen-vl-max 9/10); rank flip отсутствует;
- неизменно: code sol→glm→kimi→qwen; data qwen→glm→kimi; research glm→qwen→kimi;
  brief/creative qwen→kimi→luna→terra; review/strategic/vision incumbents; механика
  R1/R6/R7/S1/R4/R9, квота-гварды, mode=shadow, PATTERNS; новых model id нет.

Дельты v5.3.1 (карта t_d633425f; COMPANY CONTRACT CORRECTION #1 — binding, комментарий
t_6f4c4809 07.10.2026 22:34 MSK; correction приземлилась через 51 с после финиша run 164
(v5.3 commit 1dd29d7) → v5.3-head никогда не соответствовал финальному контракту
(missed window); QA t_46db399a WITHHELD + company re-anchor на новый head):
- BENCH-FIRST ops-хвост: финальный порядок glm-5.3 №1 (62%, AA AutomationBench 15.09,
  HIGH) → deepseek-v4-flash №2 (54%, AA 15.09 same lane; live family id
  deepseek-v4-flash-0731; MED) → qwen3.8-max №3 с явным GAP-MARK (нет AA AutomationBench
  числа; Round-2 canon 02.09 = tie-break only; не может outrank измеренный скор;
  A/B pending). Основание: измеренные рельсы ранжируются по скорам; gap-marked filler
  идёт за ними — иначе bench-first декоративен. Порядок v5.3 (glm→qwen→flash) SUPERSEDED
  (порядок v5.3.1 glm→flash→qwen в свою очередь SUPERSEDED v5.3.2 revision #2 — см. ниже);
- головы классов не изменились (ops head glm-5.3); heads-таблица = V531_HEADS (строка v5.3.1
  добавлена: хвост ops переставлен bench-first);
- движок — data-only ревизия: механика R1/R6/R7/S1/R4/R9, квота-гварды, mode=shadow,
  PATTERNS не затронуты; новых model id нет; прочие классы без изменений.

Дельты v5.3.2 (карта t_adc86747; COMPANY CONTRACT REVISION #2 — binding, company decision
t_9c87c344 комментарий 08.10.2026 + owner word; QA t_46db399a run 3012 подтвердил
BLOCK-1/BLOCK-2 по сохранённой primary evidence 07.10.2026; company re-anchor QA на новый head):
- BENCH-FIRST ops: полный список = три измеренные HIGH рельсы одной лаборатории AA
  (AutomationBench, сохранённые compare-снапшоты 07.10.2026, sha256 10aed5ac… /
  c9742f0c…): zai/glm-5.3 №1 (62%) → custom/kimi-k3 №2 (58%) → custom/qwen3.8-max №3
  (56%). Порядок v5.3.1 glm→flash→qwen SUPERSEDED;
- deepseek-v4-flash исключён из ops-списка: измерен (54% — свежий live-снапшот
  public-aa-tool-118533 08.10.2026, sha256 9529723e…, same-generation primary:
  qwen 56 > flash 54), но измерен НИЖЕ всех трёх; две custom-рельсы уже на позициях
  2-3 → max-two-custom лимит не оставляет ему слота. Остаётся доступным per-card пином
  (PATTERNS §8 PATTERNS-SOURCES-v2 сохранён без изменений);
- GAP-MARK qwen v5.3.1 ОТЗВАН: «Not publicly available» досье A устарел — сохранённая
  primary 07.10.2026 содержит публичные AA AutomationBench числа и для qwen (56), и для
  kimi (58); Round-2 canon 02.09 остаётся tie-break only;
- F2/G1: цитата AA-Briefcase v1.1 Elo «1640 > 1505 > 1299 (снятие 24.09.2026)» ОТЗВАНА —
  сохранённого источника нет (тот же режим, что 68.9%); в ROUTES why и ADJACENCY
  reasons (brief/creative/research/data) заменена сохранённой primary 07.10.2026:
  qwen 1621 > kimi 1501 > luna 1336 (совпадает с текущими публичными строками AA).
  Порядки brief/creative/research/data БЕЗ изменений (qwen > kimi > luna) — ранг-флипа
  нет, чисто source-ремедиация;
- ADJACENCY_RELAXATIONS["ops"]: пара flash→qwen ⇒ kimi→qwen (обе custom, позиции 2-3);
  authority = COMPANY CONTRACT REVISION #2 (t_9c87c344) + сохранённые AA-снапшоты
  07.10.2026; trigger = новая независимо измеренная не-custom ops-рельса ИЛИ live A/B
  kimi-vs-qwen на ops ИЛИ новый снапшот AA AutomationBench, меняющий порядок трёх;
- V531_HEADS → V532_HEADS: головы БЕЗ изменений (code sol, data qwen, research glm,
  ops glm, review glm, vision luna); добавлена строка v5.3.2 (ops-список = три
  измеренные рельсы bench-first);
- движок — data-only ревизия: механика R1/R6/R7/S1/R4/R9, квота-гварды, mode=shadow,
  PATTERNS не затронуты; новых model id нет (kimi-k3 уже в пуле/PATTERNS); прочие
  классы без изменений.
Дельты v6.0 (карта t_92cce51d; ROUTES-V6-FASTPATH-20261008.md — owner-ordered fast path 08.10.2026;
ТРАНСКРИПЦИЯ подписанной политики, не новый дизайн):
- Rev 4 §6 (OWNER-DIRECTIVE-review-economy-20261007.md, binding): тиры в ROUTES —
  TIER_POLICY: масса (ops/code/research/review) = tier-1 ТОЛЬКО не-GPT; Plus
  (gpt-6.1-sol/gpt-6-astra) = tier-2 ТОЧЕЧНО (глубокий дизайн, high-risk гейты,
  финальный acceptance) — per-card pin, не по умолчанию; brain-профили
  (product/video-director) сохраняют sol-дефолт как tier-2; gpt-free
  (luna/terra) = tier-Q — допустимы только при существующих ledger/caps/stop-loss,
  до их введения в массе запрещены (burn/churn);
- review: [glm-5.3, sol, qwen] ⇒ [glm-5.3, qwen3.8-max, kimi-k3] — sol ИЗЪЯТ из
  массовой цепи (tier-2); порядок не-GPT — bench-first по РЕЛЕВАНТНОМУ классу бенчу:
  review-бенч t_3d503c82 (08.10.2026, 9 frozen QA-кейсов, deterministic scoring):
  glm удержан №1 по прямой рекомендации бенча (НЕ переключать до фикса 240s
  timeout-pathology, NEEDS-EVIDENCE); qwen №2 (precision 3/3 на отвеченных,
  0 false-approve — response-rate 14% = serving-pathology, не качество); kimi №3
  (50% accuracy + 3 dangerous false-approves на том же бенче); новая запись
  ADJACENCY_RELAXATIONS["review"] (пара qwen→kimi, обе custom);
- code: [sol, glm, kimi, qwen] ⇒ [glm-5.3, kimi-k3, qwen3.8-max] — sol ИЗЪЯТ из
  массовой цепи (tier-2 per-card pin; TB4.0 58.2% HIGH сохранён как tier-2
  evidence); порядок tier-1 — измеренный: DeepSWE glm 69±3 / kimi 69±5 / qwen 57±3;
- ops/research — уже tier-1 не-GPT (без изменений); data/brief/creative/vision/
  strategic — без изменений (не классы массы; brief/creative rungs luna/terra —
  tier-Q существующие измеренные позиции, НЕ масса; расширение tier-Q — только
  после ledger/caps/stop-loss);
- FALLBACK-GOVERNANCE (interim, до механизмов M14–M17): деградационный рельс — в том
  же тире или ниже, НИКОГДА выше (инцидент 08.10: резервная цепь qa rung
  openai-codex залипала сессии на Plus-sol = 57% расхода пула/сутки); read-only
  аудит цепей всех 12 профилей — в ROUTES-V6-CHANGELOG.md §FALLBACK-GOVERNANCE
  (нарушения: finance, tech, ux; latent: company nested; qa исправлен 08.10);
- закрытие дефектов: B1–B3 (QA t_62e0e936, v5.2 BLOCK) и NO-GO v5.3 (QA t_46db399a
  run3512 F1) — закрыты предшествующими repair-коммитами (1dd29d7, 6c4db72) и
  задокументированы в ROUTES-V6-CHANGELOG.md со ссылками; v6 наследует исправленное
  состояние без изменений ops/data/research/brief/creative/vision/strategic;
- незыблемо: R1 (reviewer ≠ модель автора, fail-closed), R6 (детерминизм), R7 (явный
  degrade, решение выдаётся всегда), квота-гварды пулов; один консолидированный
  QA-гейт; re-review delta-scoped. Движок — data-only ревизия: логика classify/
  _split_plan идентична v5.3.2; новых model id нет; mode=shadow.
Дельты v6.1 (карта t_d4ddabc1; OWNER-DIRECTIVE-fallback-matrix-20261008.md — binding
owner fallback matrix 08.10.2026 evening; ТРАНСКРИПЦИЯ, не новый дизайн; data-only):
- gpt-6-luna (провайдер gpt-free) — ФИНАЛЬНЫЙ аварийный ранг деградации в классах
  review/code/ops/research/brief/creative (после существующих не-GPT рельс). Матрица:
  «АВАРИЙНЫЙ финальный ранг всех цепей (R7: решение выдаётся всегда)»; аварийный,
  НЕ массовый — mass_gpt_ban и caps-pending статус tier-Q сохранены (массовая
  маршрутизация на gpt-free без ledger/caps запрещена).
- brief/creative: terra поднята на позицию 3 (gap-ранг; «не выше середины» сохранено —
  3 из 4), luna перенесена в финальный аварийный ранг и ре-провайдерена
  openai-codex → gpt-free (матрица 08.10: openai-codex = ТОЛЬКО sol/astra tier-2 pin;
  luna обслуживается пулом gpt-free n=4). Owner-канон для аварийного ранга выше
  bench-first порядка (Elo luna 1336 сохранён как tier-Q evidence в why).
- QA-классы (exact-head review/acceptance) и QA-цепь профиля qa — НЕ затронуты
  (политика 08.10 R1: GPT-free QA-цепь); классы data/vision/strategic — вне scope
  (без изменений; vision luna остаётся openai-codex — известный residual,
  ре-провайдеринг vision — отдельной картой).
- Ноль рангов openai-codex (sol/astra) в деградации — подтверждено структурной
  проверкой (sol/astra ⊆ strategic, tier-2 pin-класс).
- Живые цепи 12 профилей УЖЕ приведены company к этой матрице (hermes config set,
  08.10.2026 ~17:0x MSK) — таблица догоняет реальность (shadow-режим неизменён).
- Поведенческая дельта selftest: сценарии «все T1-рельсы down» в 6 классах теперь
  завершаются на gpt-6-luna (gpt-free), а не на PROFILE_DEFAULT; R7 degrade в
  профильный дефолт наступает только при недоступности и gpt-free. R1
  author-exclusion сильнее аварийного ранга: author=gpt-6-luna на review →
  fail-closed degrade (кейс в selftest).
- движок — data-only ревизия: логика classify/_split_plan идентична v6.0; новых
  model id нет; mode=shadow; активация таблицы — за native engine (t_aa908ed4
  M14–M17) + QA (t_46db399a).
CLI: --card file.json [--status s.json] | --selftest | --print-rules | --patterns [MODEL]
"""
import argparse
import hashlib
import json
import re
import sys

VERSION = "6.2.0"  # v6.2: repair QA t_23bf8397 F1–F3 (карта t_fa3611e4, SPEC-v62-f1f3-repair-20261008): rationale-vs-order в ADJACENCY_RELAXATIONS.code, честная формулировка terra в review.why, регрессионный структурный кейс rationale-vs-order; порядки/тиры НЕ менялись; база v6.1 t_d4ddabc1 (8940aa5)
ROUTES_VERSION = "v6.2"  # версия таблицы ROUTES (карта t_fa3611e4: repair F1–F3, data-only — списки идентичны v6.1)
ROUTER_VERSION = "v6.2"  # версия движка (v6.2: data-only ревизия — логика движка идентична v6.1/v6.0/v5.3.2)
MODE = "shadow"  # enforce — отдельное измеренное решение владельца; в этом изменении не флипается (SPEC v5 bans)

if hasattr(sys.stdout, "reconfigure"):  # Windows: стабильный UTF-8 вывод
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# --- Константы лестницы (LADDER-PROVIDERS.md 03.10.2026 + директива владельца 04.10) ---
T1_PROVIDERS = ("custom", "zai", "openai-codex")  # T1 — стабильное ядро; T2 (agentrouter/TypeSafe/OpenRouter) и T3 в ROUTES никогда
# terra-ступень (scope b карты t_91e8ce45): только при положительной каталог-верификации.
# Верификация t_4e47fef0 (operations, done 05.10.2026): проба 2026-10-05T18:30:50Z,
# GET chatgpt.com/backend-api/codex/models?client_version=99.0.0 — HTTP 200 на обеих
# строках пула (a2662b, 8a052d), точная id-строка "gpt-5.6-terra" присутствует в каталоге.
# Телеметрия 30д: 0 вызовов → качество для классов НЕ доказано → terra экономичная ступень
# не выше середины списка (LADDER правило 1); повышение — только по shadow-данным.
TERRA_CATALOG_VERIFIED = True
TERRA_ALLOWED_CLASSES = ("brief", "creative")
DIVERSITY_EXEMPT = ("strategic",)  # канон: brain-рельса owner-facing, только ручной пин (sol+astra — оба openai-codex)
# v5.1 (disposition t_28337b5a §1, 07.10.2026): V5_ADJACENCY_EXEMPT (тихий байпасс) УДАЛЁН.
# Замена — явная запись-релаксация: соседние одно-провайдерные пары допустимы ТОЛЬКО с записью
# {pairs, reason, authority, trigger}; hard-клаузы (a)(b)(c) проверяются selftest для каждого
# не-DIVERSITY_EXEMPT класса (см. _structural_checks); релаксация снимается по триггеру.
# v5.2 (директива 07.10.2026 evening): опциональный флаг covers_clause_a — запись покрывает
# клаузу (a) «позиции 1-2 разных провайдера», только когда evidence ставит две рельсы одного
# провайдера выше всех измеренных альтернатив (brief/creative: qwen 1621 > kimi 1501 >
# luna 1336 — сохранённая primary 07.10.2026; цитата 24.09 «1640 > 1505 > 1299» отозвана
# v5.3.2, F2/G1 — нет сохранённого источника).
ADJACENCY_RELAXATIONS = {
    "code": {
        "pairs": [["custom/kimi-k3", "custom/qwen3.8-max"]],
        "reason": "v6.2 (repair QA t_23bf8397 F1 — rationale соответствует фактическому списку): code = glm#1 (DeepSWE 69±3 HIGH 22.09.2026, TB 41.8% HIGH) → kimi#2 (DeepSWE 69±5 HIGH; TB н/д — gap) → qwen#3 (DeepSWE 57±3, TB 27.0% HIGH) → gpt-6-luna#4 (R7 финальный аварийный ранг v6.1, класс не измерен); соседняя пара kimi→qwen = позиции 2-3, обе custom — в пуле одна измеренная не-custom рельса code (zai-голова), полное чередование невозможно без непроверенных рельс. SUPERSEDED-история v6.0 (НЕ текущий порядок): sol лидировал по TB4.0 58.2% (HIGH, tbench.ai live 07.10.2026) и был головой code до Rev 4 §6 — изъят из массовой code-цепи в tier-2 per-card pin (OWNER-DIRECTIVE-review-economy-20261007.md + OWNER-DIRECTIVE-fallback-matrix-20261008)",
        "authority": "owner directive bench-first 07.10.2026 evening (DIRECTIVE-bench-first-20261007-evening.md, в ветке); dossier A snapshots 07.10.2026",
        "trigger": "новая независимо измеренная не-custom рельса code ИЛИ live A/B по паре kimi/qwen на code",
    },
    "research": {
        "pairs": [["custom/qwen3.8-max", "custom/kimi-k3"]],
        "reason": "bench-first v5.2: research = glm#1 (hallucination 29.6% AA-Omniscience via benchlm.ai 07.10.2026 — лучший измеренный пула) → qwen#2 (AA-Briefcase Elo 1621 > kimi 1501 — сохранённый снапшот 07.10.2026; цитата 24.09 «1640 > 1505» отозвана v5.3.2 F2/G1 — нет сохранённого источника) → kimi#3 (vendor BrowseComp 91.2/DeepSearchQA 95.0 LOW не ранжирует выше независимых); позиции 2-3 обе custom — второй измеренной не-custom рельсы research нет (gap досье A: независимых BrowseComp/DeepSearchQA прогонов нет ни у одной рельсы пула)",
        "authority": "owner directive bench-first 07.10.2026 evening; dossier A snapshots 07.10.2026",
        "trigger": "независимый research-suite прогон (BrowseComp/DeepSearchQA/SimpleQA) по ≥2 рельсам пула ИЛИ новая измеренная не-custom рельса research",
    },
    "ops": {
        "pairs": [["custom/kimi-k3", "custom/qwen3.8-max"]],
        "reason": "v5.3.2 (COMPANY CONTRACT REVISION #2, карта t_adc86747, company decision t_9c87c344): ops = glm#1 (AutomationBench-AA 62%, сохранённый снапшот artificialanalysis.ai 07.10.2026, HIGH) → kimi#2 (58%, тот же прогон AA, HIGH) → qwen#3 (56%, тот же прогон AA, HIGH) — все три измерены одной лабораторией; позиции 2-3 обе custom: две лучшие после glm измеренные рельсы класса обе custom (deepseek-v4-flash измерен — 54%, свежий снапшот 08.10.2026 — но ниже всех трёх, max-two-custom лимит не оставляет ему слота, per-card pin); не-custom место в списке одно (zai/glm-5.3, голова), codex-рельсей класса нет — полное чередование невозможно без непроверенных/неизмеренных рельсей",
        "authority": "COMPANY CONTRACT REVISION #2 (company decision t_9c87c344, комментарий 08.10.2026 + owner word, binding) — enforced картой t_adc86747; сохранённые AA-снапшоты 07.10.2026 (aa-compare-glm53-vs-qwen38max sha256 10aed5ac…, aa-compare-kimi-k3-vs-qwen38max sha256 c9742f0c…, dossiers-v5/snapshots)",
        "trigger": "новая независимо измеренная не-custom ops-рельса ИЛИ live A/B kimi-vs-qwen на ops ИЛИ новый снапшот AA AutomationBench, меняющий порядок трёх",
    },
    "brief": {
        "pairs": [["custom/qwen3.8-max", "custom/kimi-k3"]],
        "covers_clause_a": True,
        "reason": "bench-first v5.2 (числа — v5.3.2 source-ремедиация F2/G1): AA-Briefcase v1.1 Elo (artificialanalysis.ai, сохранённые снапшоты 07.10.2026, sha256 29aa7dc7… / c9742f0c…): qwen 1621 > kimi 1501 > luna 1336 — две лучшие измеренные рельсы класса обе custom; первая измеренная не-custom рельса (luna 1336) ниже обеих, постановка выше kimi была бы заполнением структурой вместо evidence. Цитата «снятие 24.09.2026: 1640 > 1505 > 1299» ОТЗВАНА (v5.3.2): сохранённого источника нет; сохранённая primary совпадает с текущими публичными строками AA — порядок не меняется. v6.1 (OWNER-DIRECTIVE-fallback-matrix-20261008.md, binding): пара luna→terra расформирована — terra поднята на позицию 3 (gap, не выше середины — 3 из 4), luna ре-провайдерена openai-codex → gpt-free и перенесена в финальный аварийный ранг (позиция 4); соседняя пара terra(oc)→luna(gpt-free) — разные провайдеры, релаксации не требует; owner-канон для аварийного ранга выше bench-first порядка",
        "authority": "owner directive bench-first 07.10.2026 evening (бенчи решают порядок кандидатов) + OWNER-DIRECTIVE-fallback-matrix-20261008.md (аварийный финальный ранг, binding)",
        "trigger": "новый снапшот AA-Briefcase с не-custom рельсой ≥1501 ИЛИ live A/B brief-класса ИЛИ первое измерение terra ИЛИ отзыв/замена аварийного ранга матрицы 08.10",
    },
    "creative": {
        "pairs": [["custom/qwen3.8-max", "custom/kimi-k3"]],
        "covers_clause_a": True,
        "reason": "bench-first v5.2 (числа — v5.3.2 source-ремедиация F2/G1): тот же AA-Briefcase v1.1 Elo (artificialanalysis.ai, сохранённые снапшоты 07.10.2026): qwen 1621 > kimi 1501 > luna 1336 (цитата «снятие 24.09.2026: 1640 > 1505 > 1299» отозвана v5.3.2 — нет сохранённого источника); luna-экономика ($/task) — не quality-аргумент (директива: скорость/цена ≠ качество). v6.1 (OWNER-DIRECTIVE-fallback-matrix-20261008.md, binding): пара luna→terra расформирована — terra поднята на позицию 3 (gap, не выше середины), luna ре-провайдерена openai-codex → gpt-free и перенесена в финальный аварийный ранг (позиция 4); соседняя пара terra(oc)→luna(gpt-free) — разные провайдеры, релаксации не требует",
        "authority": "owner directive bench-first 07.10.2026 evening + OWNER-DIRECTIVE-fallback-matrix-20261008.md (аварийный финальный ранг, binding)",
        "trigger": "новый снапшот AA-Briefcase с не-custom рельсой ≥1501 ИЛИ live A/B creative-класса ИЛИ первое измерение terra ИЛИ отзыв/замена аварийного ранга матрицы 08.10",
    },
    "review": {
        "pairs": [["custom/qwen3.8-max", "custom/kimi-k3"]],
        "reason": "v6 (Rev 4 §6, карта t_92cce51d): review масса = tier-1 не-GPT [glm-5.3, qwen3.8-max, kimi-k3]; позиции 2-3 обе custom — qwen3.8-max №2 по review-бенчу t_3d503c82 (08.10.2026, 9 frozen QA-кейсов: precision 3/3 на отвеченных, 0 false-approve, 0 false-request-changes; response-rate 14% — 240s serving timeout-pathology, не качество) и kimi-k3 №3 (50% accuracy + 3 dangerous false-approves на том же бенче → ниже qwen на классе review; общее AA AutomationBench kimi 58 > qwen 56 — ops-класс, не отменяет классовый review-бенч: bench-first = релевантный бенч класса); не-custom tier-1 рельса класса одна (zai/glm-5.3, голова); Plus (sol) в массовой review-цепи запрещён (Rev 4 §6); v6.1 (OWNER-DIRECTIVE-fallback-matrix-20261008.md, binding): gpt-free/gpt-6-luna допущена ФИНАЛЬНЫМ аварийным рангом (позиция 4, после kimi) — аварийный, НЕ массовый (caps-pending tier-Q сохранён); измеренных не-custom альтернатив паре нет",
        "authority": "OWNER-DIRECTIVE-review-economy-20261007.md Rev 4 §6 (binding) + измеренный review-бенч t_3d503c82 (done 08.10.2026, BENCH-REPORT.md) + ROUTES-V6-FASTPATH-20261008.md (owner-ordered fast path)",
        "trigger": "re-run review-бенча после фикса 240s timeout-pathology (ok_rate ≥80% на модель) ИЛИ новая измеренная не-custom review-рельса ИЛИ введение ledger/caps/stop-loss для tier-Q (gpt-free) — тогда пересмотр позиций 2-3",
    },
}
# --- v6.0: TIER_POLICY — транскрипция Rev 4 §6 (OWNER-DIRECTIVE-review-economy-20261007.md, binding) ---
# Тиры review-класса и массовой маршрутизации; enforcement — структурные проверки
# selftest (масса = только не-GPT) + per-card pin дисциплина диспетчера.
TIER_POLICY = {
    "version": "rev4-6",
    "authority": "OWNER-DIRECTIVE-review-economy-20261007.md Rev 4 §6 (binding) + DIRECTIVE-bench-first-20261007-evening.md + ROUTES-V6-FASTPATH-20261008.md (owner-ordered fast path 08.10.2026)",
    "mass_classes": ["ops", "code", "research", "review"],
    "mass_gpt_ban": True,  # ни один класс массы не маршрутизирует в Plus/gpt-free без caps
    # v6.1 (карта t_d4ddabc1): вырезка матрицы 08.10 — luna(gpt-free) финальным аварийным
    # рангом НЕ отменяет mass_gpt_ban (аварийный ≠ массовый; caps-pending tier-Q сохранён)
    "v61_emergency_final_rank": {"model": "gpt-6-luna", "provider": "gpt-free",
                                 "classes": ["review", "code", "ops", "research", "brief", "creative"],
                                 "scope": "ФИНАЛЬНЫЙ аварийный ранг деградации (после не-GPT рельс): R7 — решение выдаётся всегда; аварийный, НЕ массовый — mass_gpt_ban и caps-pending tier-Q сохранены; QA-классы exact-head review/acceptance и QA-цепь профиля qa НЕ затронуты (GPT-free политика 08.10, R1)",
                                 "authority": "OWNER-DIRECTIVE-fallback-matrix-20261008.md (binding, owner fallback matrix 08.10.2026 evening); живые цепи 12 профилей применены company 08.10 (config set ~17:0x MSK) — таблица догоняет реальность"},
    "tiers": {
        "tier-1": {"scope": "масса — ТОЛЬКО не-GPT", "providers": ["zai", "custom"]},
        "tier-Q": {"scope": "gpt-free (luna/terra) — рутина, влияющая на качество; допустим ТОЛЬКО при существующих ledger/caps/stop-loss; до их введения масса НЕ маршрутизируется (burn/churn запрещён)",
                   "models": ["gpt-6-luna", "gpt-5.6-terra"], "status": "caps-pending"},
        "tier-2": {"scope": "Plus (sol/astra) — точечно: глубокий дизайн, high-risk гейты, финальный acceptance; per-card pin, не по умолчанию; brain-профили (product/video-director) сохраняют sol-дефолт",
                   "models": ["gpt-6.1-sol", "gpt-6-astra"], "access": "per-card pin / brain-profile default"},
    },
    "fallback_governance": "деградационный рельс — В ТОМ ЖЕ ТИРЕ или ниже, НИКОГДА выше (инцидент 08.10: резервная цепь qa rung openai-codex залипала сессии на Plus-sol = 57% расхода пула/сутки); read-only аудит цепей профилей — ROUTES-V6-CHANGELOG.md §FALLBACK-GOVERNANCE; правки чужих цепей — отдельными картами; v6.1 (матрица 08.10): финальный ранг дешёвых цепей = gpt-6-luna (gpt-free) аварийный; ноль рангов openai-codex (sol/astra) в fallback — sol/astra только tier-2 pin-класс",
    "qa_gate": "один консолидированный QA-гейт; re-review delta-scoped",
}
DEGRADE_MODEL = "PROFILE_DEFAULT"  # R7: все рельсы класса недоступны → дефолт профиля (LADDER правило 6)
DEGRADE_PROVIDER = "profile-default"

# --- v6.0 heads = Rev 4 §6 tier-economy (карта t_92cce51d, ROUTES-V6-FASTPATH-20261008.md,
# owner-ordered fast path 08.10.2026; база = v5.3.2 bench-evidence таблица) ---
# Масса (ops/code/research/review) = tier-1 ТОЛЬКО не-GPT; sol изъят из code/review
# массовых цепей (tier-2 per-card pin); порядки не-GPT — bench-first по релевантному
# классу бенчу (code: DeepSWE; review: флот review-бенч t_3d503c82; ops: AA AutomationBench
# сохранённая primary 07.10.2026 — revision #2).
V6_HEADS = {"code": "zai/glm-5.3",                # v6: масса tier-1 не-GPT (Rev 4 §6); DeepSWE 69±3 HIGH (22.09.2026); sol → tier-2 per-card pin (TB4.0 58.2% HIGH сохранён как tier-2 evidence)
            "data": "custom/qwen3.8-max",         # измеренный A/B 02.09: сохранение 3/3 vs kimi 0/3 (тест, не инструкция)
            "research": "zai/glm-5.3",            # hallucination 29.6% AA-Omniscience (benchlm.ai 07.10.2026) — лучший измеренный
            "ops": "zai/glm-5.3",                 # AutomationBench-AA 62% (сохранённый снапшот 07.10.2026, HIGH) > kimi 58% > qwen 56% (revision #2)
            "review": "zai/glm-5.3",              # incumbent: review-бенч t_3d503c82 (08.10.2026) — НЕ переключать до фикса timeout-pathology (NEEDS-EVIDENCE); R1 — механика
            "vision": "openai-codex/gpt-6-luna"}  # incumbent: точной пары luna-vs-qwen-vl-max в открытых бенчах нет → флот A/B 10:9

# --- Источники open-bench цитат для структурной проверки why (SPEC v5 acceptance) ---
BENCH_SOURCES = ("tbench.ai", "deepswe.datacurve.ai", "artificialanalysis.ai", "llm-stats.com",
                 "benchlm.ai", "kimi.ai/blog", "z.ai/blog", "swebench.com", "aider.chat",
                 "arxiv.org", "traictory.com", "vellum.ai")
BENCH_DATE_RE = re.compile(r"(20\d\d|\d{2}\.\d{2}\.20\d\d)")
# v5.2 (директива 07.10.2026 evening): owner-question маркеры в ROUTES запрещены —
# порядок чинят тесты/бенчи, не ожидание owner-слова (D1/D3/D7 RESOLVED).
OWNER_WORD_MARKERS = ("pending owner word", "словом владельца", "слова владельца", "ждём слова")

# --- ROUTES v5: 9 классов; порядок списка = предпочтение; why = ≥1 open-bench число с источником+датой ---
ROUTES = {
    "code": {
        "models": ["zai/glm-5.3", "custom/kimi-k3", "custom/qwen3.8-max", "gpt-free/gpt-6-luna"],
        "why": "v6 (Rev 4 §6 — масса ТОЛЬКО не-GPT; карта t_92cce51d): glm-5.3 №1 — лучшая измеренная не-GPT рельса класса: DeepSWE v1.1 69%±3 (deepswe.datacurve.ai, upd. 22.09.2026, HIGH) + TB 4.0 41.8% (tbench.ai, live 07.10.2026, HIGH); kimi-k3 №2 — DeepSWE 69%±5 (HIGH, паритет с glm в пределах ошибки; TB н/д — gap); qwen3.8-max №3 — DeepSWE 57%±3, TB 4.0 27.0% (HIGH). Соседняя пара kimi→qwen (обе custom) записана в ADJACENCY_RELAXATIONS; hard-клаузы (a)(b)(c) выполняются. gpt-6.1-sol ИЗЪЯТ из массовой code-цепи: TB 4.0 58.2% (tbench.ai, 07.10.2026, HIGH) измерен лучшим на классе, но Rev 4 §6 (binding, OWNER-DIRECTIVE-review-economy-20261007.md) — Plus-квота только для tier-2 «качество» (глубокий дизайн, high-risk гейты, финальный acceptance): sol доступен per-card пином (точечно, не по умолчанию), brain-профили (product/video-director) сохраняют sol-дефолт как tier-2. astra в code не входит: нет пары astra-vs-sol-6.1 (evidence-gap) + capacity-гвард; пересмотр по live A/B. Divergence D1 RESOLVED (порядок — измеренный; v6: масса — tier-1 по Rev 4 §6). v6.1 (OWNER-DIRECTIVE-fallback-matrix-20261008.md, binding): gpt-6-luna (провайдер gpt-free) — ФИНАЛЬНЫЙ аварийный ранг после tier-1 не-GPT рельс (R7: решение выдаётся всегда); аварийный, не массовый — mass_gpt_ban и caps-pending tier-Q сохранены; живые цепи 12 профилей уже приведены company к матрице (config set 08.10.2026) — таблица догоняет реальность",
    },
    "data": {
        "models": ["custom/qwen3.8-max", "zai/glm-5.3", "custom/kimi-k3"],
        "why": "bench-first v5.2 (директива 07.10.2026 evening): qwen3.8-max №1 — измеренный флот-A/B 02.09: сохранение данных 3/3 при конфликтных инструкциях vs kimi 0/3 (тест, не инструкция; флот-канон) + высший AA-Briefcase v1.1 Elo пула 1621 (artificialanalysis.ai, сохранённый снапшот 07.10.2026; цитата «1640, снятие 24.09.2026» отозвана v5.3.2 F2/G1 — нет сохранённого источника); glm-5.3 №2 — TB 4.0 41.8% (tbench.ai, live 07.10.2026, HIGH) + hallucination rate 29.6% (AA-Omniscience via benchlm.ai, 07.10.2026) — аккуратность на data-классе; kimi-k3 №3 — R8: data-loss измерен (0/3, A/B 02.09) → каждая data-задача на kimi-рельсе обязана нести backup/no-destructive контракт (паттерн kimi-k3); вендорское TB2.1 88.3 (kimi.ai/blog/kimi-k3, LOW self-report) как независимый факт не используется (divergence D4). Divergence D2 RESOLVED директивой: измеренный A/B задаёт порядок",
    },
    "research": {
        "models": ["zai/glm-5.3", "custom/qwen3.8-max", "custom/kimi-k3", "gpt-free/gpt-6-luna"],
        "why": "bench-first v5.2 (директива 07.10.2026 evening): glm-5.3 №1 — лучшая измеренная аккуратность пула: hallucination rate 29.6% (AA-Omniscience via benchlm.ai, 07.10.2026) + DeepSWE v1.1 69%±3 (deepswe.datacurve.ai, 22.09.2026, HIGH) + TB 4.0 41.8% (tbench.ai, 07.10.2026, HIGH); qwen3.8-max №2 — AA-Briefcase v1.1 Elo 1621 (artificialanalysis.ai, сохранённый снапшот 07.10.2026) > kimi 1501, owner-canon hallucination 40% < kimi ~47.6-51% (LOW); цитата 24.09.2026 «1640 > 1505» отозвана v5.3.2 (F2/G1 — нет сохранённого источника); kimi-k3 №3 — vendor BrowseComp 91.2 / DeepSearchQA 95.0 F1 (kimi.ai/blog/kimi-k3, LOW self-report) не ранжирует выше независимых чисел (директива: vendor-число никогда не бьёт независимое); паттерн строго требует источник/URL на каждое число. GAP: независимых прогонов BrowseComp/DeepSearchQA нет ни у одной рельсы пула (досье A §4, 07.10.2026) — пересмотр по первому независимому research-suite прогону. Соседняя пара qwen→kimi (обе custom) записана в ADJACENCY_RELAXATIONS. v6.1 (OWNER-DIRECTIVE-fallback-matrix-20261008.md, binding): gpt-6-luna (провайдер gpt-free) — ФИНАЛЬНЫЙ аварийный ранг после tier-1 не-GPT рельс (R7: решение выдаётся всегда); аварийный, не массовый — mass_gpt_ban сохранён; живые цепи 12 профилей уже приведены company к матрице (config set 08.10.2026) — таблица догоняет реальность",
    },
    "ops": {
        "models": ["zai/glm-5.3", "custom/kimi-k3", "custom/qwen3.8-max", "gpt-free/gpt-6-luna"],
        "why": "bench-first v5.3.2 (COMPANY CONTRACT REVISION #2 — binding, company decision t_9c87c344 комментарий 08.10.2026 + owner word; карта t_adc86747; QA t_46db399a run 3012 BLOCK-1/BLOCK-2 по сохранённой primary 07.10.2026): glm-5.3 №1 — AutomationBench-AA 62% (artificialanalysis.ai, live 07.10.2026, HIGH независимый) — лучший измеренный пула на ops-классе; kimi-k3 №2 — AutomationBench-AA 58% (сохранённый compare-снапшот artificialanalysis.ai 07.10.2026 «Qwen3.8 Max (0902) vs Kimi K3 (Max)», sha256 c9742f0c…, HIGH); qwen3.8-max №3 — AutomationBench-AA 56% (сохранённые compare-снапшоты 07.10.2026: glm-vs-qwen sha256 10aed5ac…, kimi-vs-qwen sha256 c9742f0c…; свежий live-снапшот 08.10.2026 flash-vs-qwen sha256 9529723e…: qwen 56 > flash 54, same-generation primary) — все три измерены одной лабораторией AA (HIGH). deepseek-v4-flash исключён из ops-списка: измерен (54% AutomationBench-AA, свежий live-снапшот public-aa-tool-118533 08.10.2026, HIGH) — НИЖЕ всех трёх; две custom-рельсы уже на позициях 2-3 → max-two-custom лимит не оставляет ему слота; остаётся доступным per-card пином (PATTERNS §8 PATTERNS-SOURCES-v2 сохранён; DashScope live-verified id семейства deepseek-v4-flash-0731, fleet-doctrine inventory 04.10.2026). Порядок v5.3.1 glm→flash→qwen SUPERSEDED ревизией #2. GAP-MARK qwen v5.3.1 ОТЗВАН: «Not publicly available» досье A устарел — сохранённая primary 07.10.2026 содержит публичные AA AutomationBench числа и для qwen (56), и для kimi (58); Round-2 canon 02.09 (hands, измеренный флот-A/B) остаётся tie-break only и не outrank-ит измеренные скоры. СНЯТАЯ ЦИТАТА v5.2: «flash №1 — AutomationBench-AA 68.9%» — число принадлежит DeepSeek V4.1 Flash (рельса не допущена, нет в ROUTES/PATTERNS); winner-claim отозван (QA t_62e0e936 B1). kimi-k3 возвращён в ops (v5.3.2): вывод v5.2 «независимых ops-чисел kimi нет» устарел — независимое AA-число 58% найдено в сохранённой primary 07.10.2026; vendor AutomationBench v1.0.6 glm 48.2 / kimi 46.7 / qwen 39.8 (z.ai/blog/glm-5.3, 14.08.2026, LOW) как самостоятельный факт не используется (divergence D4), направление совпадает с независимым AA (glm > kimi > qwen). Divergence D3 RE-RESOLVED v5.3.2: glm 62% > kimi 58% > qwen 56% > flash-0731 54% → glm №1. Соседняя пара kimi→qwen (обе custom, позиции 2-3) записана в ADJACENCY_RELAXATIONS {reason, authority, trigger}; hard-клаузы (a)(b)(c) выполняются (zai→custom→custom). v6.1 (OWNER-DIRECTIVE-fallback-matrix-20261008.md, binding): gpt-6-luna (провайдер gpt-free) — ФИНАЛЬНЫЙ аварийный ранг после tier-1 не-GPT рельс (R7: решение выдаётся всегда); аварийный, не массовый — mass_gpt_ban сохранён; живые цепи 12 профилей уже приведены company к матрице (config set 08.10.2026) — таблица догоняет реальность",
    },
    "review": {
        "models": ["zai/glm-5.3", "custom/qwen3.8-max", "custom/kimi-k3", "gpt-free/gpt-6-luna"],
        "why": "v6 (Rev 4 §6 — масса ТОЛЬКО не-GPT; Plus и gpt-free в массовой review-цепи ЗАПРЕЩЕНЫ; карта t_92cce51d): glm-5.3 №1 — incumbent, удержан по прямой рекомендации измеренного review-бенча t_3d503c82 (08.10.2026, 9 frozen QA-кейсов флота, deterministic scoring против ground truth: НЕ переключать QA-lane до фикса 240s timeout-pathology — NEEDS-EVIDENCE) + DeepSWE v1.1 69%±3 (deepswe.datacurve.ai, 22.09.2026, HIGH) + hallucination rate 29.6% (AA-Omniscience via benchlm.ai, 07.10.2026); qwen3.8-max №2 — лучшая точность бенча на отвеченных (3/3 = 100%, 0 false-approve, 0 false-request-changes; response-rate 14% = serving timeout-pathology, не качество) + AA AutomationBench 56% (artificialanalysis.ai, сохранённый снапшот 07.10.2026, HIGH); kimi-k3 №3 — 50% accuracy с 3 dangerous false-approves на том же review-бенче (t_3d503c82, 08.10.2026) → ниже qwen на классе review (классовый бенч важнее общего ops-класса AA AutomationBench 58%; bench-first = релевантный бенч класса). Соседняя пара qwen→kimi (обе custom) записана в ADJACENCY_RELAXATIONS. gpt-6.1-sol ИЗЪЯТ из массовой цепи: Rev 4 §6 — Plus = tier-2 точечно (глубокий дизайн, high-risk гейты, финальный acceptance), per-card pin. tier-Q gpt-free (luna/terra): допустимы только при существующих ledger/caps/stop-loss — до их введения в review-массе запрещены (burn/churn; на бенче luna 20% + 3 false request_changes, terra 75% при n=4 — кандидаты tier-Q после введения caps). R1: author_model исключается из списка, опустошение → fail-closed degrade (механика качества, неизменна). terra не входит — единственное измерение 75% при sub-quorum n=4 не принято как классовое (not measured); порядок glm→qwen→kimi требует rerun бенча t_3d503c82 на свежих данных при n≥12. v6.1 (OWNER-DIRECTIVE-fallback-matrix-20261008.md, binding): gpt-6-luna (провайдер gpt-free) добавлена ФИНАЛЬНЫМ аварийным рангом после kimi-k3 — аварийный, НЕ массовый: tier-Q caps-pending и запрет массовой маршрутизации на gpt-free сохранены (масса = позиции 1-3, tier-1 не-GPT); R1 author-exclusion сильнее аварийного ранга (author=luna → исключается, fail-closed degrade); QA-цепь профиля qa и exact-head review/acceptance остаются GPT-free (политика 08.10) и не затронуты; живые цепи 12 профилей уже приведены company к матрице (config set 08.10.2026) — таблица догоняет реальность",
    },
    "strategic": {
        "models": ["openai-codex/gpt-6.1-sol", "openai-codex/gpt-6-astra"],
        "why": "bench-first v5.2: owner-facing/портфель/protected — sol №1 (TB 4.0 58.2% — tbench.ai, live 07.10.2026, HIGH; DeepSWE 75.2% @ high — vendor-анонс 29.09.2026, vellum.ai/blog/gpt-6-1-sol-benchmarks-explained, MED); astra №2 — DeepSWE v1.1 74%±3 (deepswe.datacurve.ai, 22.09.2026, HIGH), TB 4.0 58.2% (tbench.ai, 07.10.2026, HIGH), TB 2.1 87.4% (tbench.ai, 07.10.2026, HIGH). GAP: пары astra-vs-sol-6.1 в открытых тестах нет (TB4.0 паритет 58.2=58.2) → astra НЕ #1 до A/B (директива 07.10.2026 evening — evidence-gap, не запрет); auto-select guard снят той же директивой: astra авто-выбираема как №2 при недоступности sol (S1); capacity-нота: astra token-expensive → точечные пакеты (флот-канон, квота-гвард — не вкусовой запрет). Класс ручной (DIVERSITY_EXEMPT): оба кандидата openai-codex, отказ провайдера эскалируется",
    },
    "vision": {
        "models": ["openai-codex/gpt-6-luna", "custom/qwen-vl-max"],
        "why": "bench-first v5.3 (repair QA t_62e0e936 B3, карта t_6f4c4809): порядок СОХРАНЁН — luna №1, qwen-vl-max №2 (incumbent). Опубликованное покрытие ЕСТЬ, но НЕ для точной пары: AA-MMMU-Pro (benchlm.ai/benchmarks/aammmupro, снапшот 07.10.2026, независимый прогон AA): gpt-6.1-sol 86.0% (#3), gpt-6-luna 79.7% (#21) — luna покрыта, qwen-vl-max на борде отсутствует → прямого опубликованного сравнения пары luna-vs-qwen-vl-max НЕТ (comparative gap сохраняется; формулировка v5.2 «ни одна vision-рельса не покрыта опубликованным бенчем» была неверна — исправлена). Ранжирование пары — прямой флот A/B: VISION-SLOT-PROOF-20261007.md (t_432cd7ef, live-вызовы 07.10.2026 через production vision path): luna 10/10 vs qwen-vl-max 9/10 на 10-страничном scan/handwriting корпусе (обе ловушки скрытого текстового слоя выдержаны обеими рельсами; hw1 miss qwen воспроизведён дважды) → luna-first измерением, не традицией. Rank flip по MMMU-Pro НЕ делается: 79.7% luna не сравнимо напрямую с отсутствующей строкой qwen-vl-max; qwen3.8-max 82.3% (#4) — текстовая флагманская рельса, не vision-слот. PerceptionBench (arxiv.org/abs/2607.24957, fetched 07.10.2026): НИ qwen-vl-max, НИ luna не входят; числа 0.635=Qwen3.8 Max / 0.585=Kimi K3 — текстовые рельсы, self-reported LOW (llm-stats.com/benchmarks/perceptionbench, «Last updated October 7, 2026») — цитируются ТОЛЬКО как исправление атрибуции D6, не как доказательство качества vision-рельсей. LADDER правило 4 сохраняет допуск рельс (только qwen-vl-max и luna). qwen-vl-max — backup без reasoning_effort (инвариант №3)",
    },
    "brief": {
        "models": ["custom/qwen3.8-max", "custom/kimi-k3", "openai-codex/gpt-5.6-terra", "gpt-free/gpt-6-luna"],
        "why": "bench-first v5.2 (директива 07.10.2026 evening; числа — v5.3.2 source-ремедиация F2/G1): порядок фиксирует AA-Briefcase v1.1 Elo (artificialanalysis.ai, сохранённые снапшоты 07.10.2026, sha256 29aa7dc7… / c9742f0c…): qwen3.8-max №1 — 1621 (высший пула) + жёсткий формат вывода (A/B 02.09: данные 3/3, флот-канон); kimi-k3 №2 — 1501; gpt-5.6-terra №3 — GAP: измерений класса нет (каталог-верификация t_4e47fef0 05.10.2026 — только доступность; 0 вызовов 30д ≠ доказательство качества) → не выше середины (LADDER правило 1: позиция 3 из 4); gpt-6-luna №4 — ФИНАЛЬНЫЙ аварийный ранг v6.1 (OWNER-DIRECTIVE-fallback-matrix-20261008.md, binding): ре-провайдерена openai-codex → gpt-free (матрица 08.10: openai-codex = только sol/astra tier-2 pin; luna обслуживается пулом gpt-free n=4); owner-канон для аварийного ранга выше bench-first порядка — Elo luna 1336 (измерен ниже kimi; none/low effort — developers.openai.com) сохранён как tier-Q evidence, аварийный ранг НЕ массовая маршрутизация (R7: решение выдаётся всегда; caps-pending tier-Q сохранён). Цитата «снятие 24.09.2026: 1640 > 1505 > 1299» ОТЗВАНА (v5.3.2, QA t_46db399a run 3012 F2/G1): сохранённого источника нет; сохранённая primary 07.10.2026 совпадает с текущими публичными строками AA — порядок не меняется (чисто source-ремедиация). Пара qwen→kimi (обе custom, позиции 1-2) покрыта ADJACENCY_RELAXATIONS с covers_clause_a: Elo ставит обе выше любой измеренной не-custom рельсы. Divergence D7 RESOLVED директивой (Elo-таблица задаёт порядок)",
    },
    "creative": {
        "models": ["custom/qwen3.8-max", "custom/kimi-k3", "openai-codex/gpt-5.6-terra", "gpt-free/gpt-6-luna"],
        "why": "bench-first v5.2 (директива 07.10.2026 evening; числа — v5.3.2 source-ремедиация F2/G1): design/ux/video-продакшн — порядок по AA-Briefcase v1.1 Elo (artificialanalysis.ai, сохранённые снапшоты 07.10.2026): qwen3.8-max №1 — 1621 (высший пула) + визуальный вход (alibabacloud.com model-studio); kimi-k3 №2 — 1501 + визуальный вход (platform.kimi.ai); gpt-5.6-terra №3 — GAP: измерений класса нет (каталог-верификация t_4e47fef0 05.10.2026 — только доступность) → не выше середины (позиция 3 из 4); gpt-6-luna №4 — ФИНАЛЬНЫЙ аварийный ранг v6.1 (OWNER-DIRECTIVE-fallback-matrix-20261008.md, binding): ре-провайдерена openai-codex → gpt-free (матрица 08.10: openai-codex = только sol/astra tier-2 pin; luna обслуживается пулом gpt-free n=4); owner-канон для аварийного ранга выше bench-first порядка — Elo luna 1336 (измерен ниже kimi; luna-экономика $/task — не quality-аргумент, директива: скорость/цена ≠ качество) сохранён как tier-Q evidence, аварийный ранг НЕ массовая маршрутизация (R7: решение выдаётся всегда). Цитата «снятие 24.09.2026: 1640 > 1505 > 1299» отозвана v5.3.2 (нет сохранённого источника, F2/G1) — порядок не меняется. Пара qwen→kimi (обе custom, позиции 1-2) покрыта ADJACENCY_RELAXATIONS с covers_clause_a (та же Elo-таблица). bench-coverage brief/creative — scope досье B (t_3e65166e)",
    },
}

# --- PATTERNS v2 (карта t_234de1e7): 5 слоёв на каждую модель — как брифовать /
# требовать строго / страховка / анти-паттерн / канонические настройки + строка
# «источники» (traceability к цитате; сверка 2026-10-04). Источник правды слоя:
# docs/fleet-ops/model-routing-20261003/PATTERNS-SOURCES-v2.md
# (sha256 76e68e7c3cd536d5129746491bd209f8f3d6d6dd4591522fbb65e93d0206ab33).
# Формат строки совместим с hook v1.2.36+ (decision["pattern"] — строка целиком).
PATTERNS_VERSION = "v2"
PATTERNS_SOURCE_DOC = "PATTERNS-SOURCES-v2.md (сверка 2026-10-04, sha256 76e68e7c…)"
PATTERNS_V2_LAYERS = ("как брифовать:", "требовать строго:", "страховка:",
                      "анти-паттерн", "канонические настройки:", "источники:")
PATTERNS = {
    "kimi-k3": (
        "как брифовать: точное ТЗ, один deliverable, без параллельных веток («Write Clear Instructions — the less the model has to guess» — platform.kimi.ai); роль — system prompt; разделители (тройные кавычки/XML-теги/заголовки); JSON — конкретный пример вывода в промпте + response_format json_object.\n"
        "требовать строго: источники на каждый факт; числа только с URL; выдуманные данные запрещены (флот-канон). multi-turn: полный messages list as-is, включая reasoning_content и tool_calls (platform.kimi.ai). data-класс: backup/снимок ДО любой записи — R8 data-loss exception (измеренный A/B 02.09: kimi 0/3 vs qwen 3/3; с v5.2 этот тест задаёт data-порядок — qwen №1, kimi-рельса несёт контракт).\n"
        "страховка: деструктивные файловые операции только после diff/backup (флот-канон); JSON без response_format — проверка на malformed (trailing commas, лишний текст).\n"
        "анти-паттерн: конфликтные инструкции по формату — при конфликте удаляет данные (0/3, A/B 02.09, флот-канон); thinking.type для k3 — ошибка (reserved for k2.x), только reasoning_effort.\n"
        "канонические настройки: reasoning_effort low/high/max (default max, top-level); thinking не передавать; response_format json_object; контекст 1M; cache-hit ~10% от цены cache-miss.\n"
        "источники: platform.kimi.ai/docs/guide/prompt-best-practice; use-thinking-models.md; use-reasoning-effort.md; use-json-mode-feature-of-kimi-api.md; engage-in-multi-turn-conversations-using-kimi-api.md; context-caching.md (сверка 2026-10-04)."),
    "qwen3.8-max": (
        "как брифовать: жёсткий формат вывода (JSON/схема), поля перечислены по порядку («the more specific your task description… the more likely the LLM's performance will meet your expectations» — alibabacloud.com); system message для роли и ограничений.\n"
        "требовать строго: запрет уничтожения данных — при конфликте сохранить значение в восстановимой форме (флот-канон, A/B 02.09: qwen сохраняет 3/3); краткость, без прозы после JSON (флот-канон).\n"
        "страховка: readback/валидация вывода по схеме (флот-канон).\n"
        "анти-паттерн: факты без проверки цитированием (галлюцинации 40%, флот-канон); «творческие» задания без жёсткого формата (флот-канон).\n"
        "канонические настройки: system message optional but recommended; temperature/top_p/top_k для 3.8-max не документированы → default; vision: single/multiple image_url + text.\n"
        "источники: alibabacloud.com/help/en/model-studio/text-generation; prompt-engineering-guide (сверка 2026-10-04)."),
    "glm-5.3": (
        "как брифовать: ревью по пунктам с номерами, каждый пункт — критерий (флот-канон); thinking принудителен — не просить «не думать», а задавать effort под задачу («Disabling thinking is no longer supported» — docs.z.ai).\n"
        "требовать строго: вердикт структурирован по пунктам PASS/FAIL с цитатами; FAIL → нумерованные дефекты, не чинить (флот-канон); interleaved thinking: thinking-блоки preserved и возвращаются вместе с tool results (docs.z.ai).\n"
        "страховка: на main/deploy — второй независимый вердикт (dual verdict 03.09, флот-канон); reasoning_content не переупорядочивать/не редактировать — деградация качества и кэш-хитов (docs.z.ai).\n"
        "анти-паттерн: размытое «всё выглядит хорошо» без пунктов и evidence (флот-канон); попытка отключить thinking — API вернёт ошибку или проигнорирует (docs.z.ai).\n"
        "канонические настройки: thinking forced (нельзя отключить); effort low/high/max; clear_thinking:false = Preserved Thinking (default Coding Plan); structured output JSON поддерживается.\n"
        "источники: docs.z.ai/guides/llm/glm-5.3; docs.z.ai/guides/capabilities/thinking-mode; z.ai/blog/glm-5.3 (сверка 2026-10-04)."),
    "gpt-6.1-sol": (
        "как брифовать: короткий ясный текст, только суть; финишная линия в каждой задаче (флот-канон); «precise instructions that explicitly provide the logic and data required to complete the task» (developers.openai.com).\n"
        "требовать строго: решение + обоснование в 3–5 предложениях (флот-канон); без «think hard» — глубина только через reasoning_effort; none/minimal не поддерживаются (developers.openai.com).\n"
        "страховка: сверять поле model в usage — флагованный ответ тихо даунгрейдит модель (флот-канон).\n"
        "анти-паттерн: длинные многоуровневые брифы (флот-канон); хаотичная смена правил mid-turn — API поддерживает контролируемый steering через WebSocket, но это не смена ТЗ (уточнение v2, developers.openai.com).\n"
        "канонические настройки: reasoning.effort low/medium(default)/high/xhigh/max; none и minimal NOT supported; async tool calling (async:true); Responses API для tools, Chat Completions для простых запросов.\n"
        "источники: developers.openai.com/api/docs/guides/latest-model; prompt-engineering; reasoning-best-practices; openai.com/index/introducing-gpt-6-sol-and-luna (сверка 2026-10-04)."),
    "gpt-6-astra": (
        "как брифовать: только узкий пакет — один вопрос/одно решение (флот-канон); «precise instructions that explicitly provide the logic and data» (developers.openai.com).\n"
        "требовать строго: ответ в формате пакета, без развернутых исследований (флот-канон).\n"
        "страховка: нужно глубокое исследование — передать классу research (kimi-k3, флот-канон); при жёстком SLA — Fast/Ultrafast режимы («All GPT-6 Astra users also have access to Fast mode and the new Ultrafast mode» — openai.com, добавлено в v2).\n"
        "анти-паттерн: портфельные исследования и длинный анализ (флот-канон).\n"
        "канонические настройки: reasoning.effort low/medium(default)/high/xhigh/max; Fast и Ultrafast mode доступны всем пользователям astra; async tool calling.\n"
        "источники: developers.openai.com/api/docs/guides/latest-model; prompt-engineering; openai.com/index/practical-guide-building-gpt-6 (сверка 2026-10-04)."),
    "qwen-vl-max": (
        "как брифовать: одно изображение на вопрос; вопрос конкретный — что прочитать/описать (флот-канон); официально поддержаны single и multiple image inputs (alibabacloud.com).\n"
        "требовать строго: без параметра reasoning_effort (инвариант №3, флот-канон); ответ в запрошенном формате; Function Calling не поддерживается, Structured Outputs поддерживается (alibabacloud.com).\n"
        "страховка: критичное распознавание — перепроверка второй моделью (gpt-6-luna, флот-канон).\n"
        "анти-паттерн: любая настройка effort (флот-канон); коллажи/несколько изображений — официально multi-image поддерживается, ограничение флот-канона по качеству распознавания (смягчено в v2).\n"
        "канонические настройки: input text+image+video; Function Calling Unsupported; Structured Outputs Supported; контекст 129K input / 8K output / 131K total.\n"
        "источники: alibabacloud.com/help/en/model-studio/vision; help.aliyun.com/en/model-studio/qwen-vl-max (сверка 2026-10-04)."),
    "gpt-6-luna": (
        "как брифовать: массовые простые просмотры — пачка однотипных изображений, low/none effort («Fastest and most cost-effective. Strong performance for focused, high-volume tasks» — developers.openai.com); творческие брифы — короткий ясный пакет (флот-канон).\n"
        "требовать строго: короткий единообразный ответ на каждый элемент (флот-канон).\n"
        "страховка: сложный/сомнительный кадр — эскалация на qwen-vl-max (флот-канон); для массовых просмотров reasoning_effort:none — «GPT-6 Sol and GPT-6 Luna do support the none reasoning effort» (developers.openai.com, добавлено в v2).\n"
        "анти-паттерн: детальный анализ одного изображения; портфельные исследования (флот-канон).\n"
        "канонические настройки: reasoning.effort none/low/medium/high — none поддерживается (в отличие от sol/astra).\n"
        "источники: developers.openai.com/api/docs/guides/latest-model; openai.com/index/introducing-gpt-6-sol-and-luna (сверка 2026-10-04)."),
    "gpt-5.6-terra": (
        "как брифовать: короткий ясный текст, только суть, один deliverable — экономичная ступень (GPT-семейство: precise instructions — developers.openai.com/api/docs/guides/prompt-engineering).\n"
        "требовать строго: результат + краткое обоснование; глубина только через reasoning_effort; сверять поле model в usage (тихий даунгрейд — флот-канон).\n"
        "страховка: качество для класса не доказано (телеметрия 30д: 0 вызовов; каталог-верификация t_4e47fef0 05.10.2026 — HTTP 200 обе строки пула) → результат критичного класса через независимую QA.\n"
        "анти-паттерн: постановка на первые две позиции класса; портфельные исследования и длинный анализ. Источник: только флот-канон (в вендорном корпусе PATTERNS-SOURCES-v2 terra отсутствует — §12 вопрос #1) + гайды GPT-семейства.\n"
        "канонические настройки: вендорных настроек для terra нет (§12 вопрос #1); по гайдам GPT-семейства глубиной управляет reasoning_effort (developers.openai.com).\n"
        "источники: только флот-канон + developers.openai.com/api/docs/guides/prompt-engineering (GPT-семейство); каталог-верификация t_4e47fef0 05.10.2026 (сверка 2026-10-04)."),
    "deepseek-v4-flash": (
        "как брифовать: чёткий system + user prompt; для JSON — слово «json» в промпте + пример формата + response_format json_object («Include the word 'json'… and provide an example of the desired JSON format» — api-docs.deepseek.com); reasoning → thinking enabled, скорость → disabled.\n"
        "требовать строго: в thinking mode reasoning_content не передавать в следующий turn — только content (api-docs.deepseek.com); max_tokens достаточный, чтобы JSON не truncated.\n"
        "страховка: проверять content на пустоту (известная issue: «the API may occasionally return empty content»); для FIM — base_url=https://api.deepseek.com/beta.\n"
        "анти-паттерн: logprobs/top_logprobs в thinking mode — ошибка; ожидать детерминизма от temperature — в thinking mode параметры игнорируются (api-docs.deepseek.com).\n"
        "канонические настройки: model deepseek-flash (legacy deepseek-v4-flash); thinking enabled/disabled; reasoning_effort high только при thinking; temperature/top_p/presence_penalty/frequency_penalty в thinking mode игнорируются; max_tokens 32K default / 64K max; контекст 1M, output 384K; кэш по умолчанию, хит ~10%.\n"
        "источники: api-docs.deepseek.com/guides/thinking_mode; json_mode; function_calling; kv_cache; chat_prefix_completion; fim_completion; quick_start/pricing (сверка 2026-10-04)."),
}

RULES_SHA = hashlib.sha1(json.dumps({"ROUTES": ROUTES, "PATTERNS": PATTERNS}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:12]  # D2: отпечаток правил — sha1 канонического дампа, [:12]; детерминизм между прогонами

# --- Жёсткие правила: применяются до выбора; при коллизии побеждает старший номер (R3 > R2) ---
RULES = [
    ("R1", "review_nature (declared task_type=review ИЛИ финальный класс review) → author_model исключается из итогового списка класса (инвариант №2: проверяющий на чужой модели); v5.1 (disposition t_28337b5a §3): исключение НИКОГДА не отменяется — пустой список → fail-closed degrade в PROFILE_DEFAULT с явной причиной «авторское review запрещено»; авторская рельса не выбирается ни при каком статусе."),
    ("R2", "owner_facing=true или protected (main/deploy/publish в title/body) → класс strategic."),
    ("R3", "needs_vision=true → класс vision (способность выше тира: R3 перекрывает R2)."),
    ("R4", "prior_run_failed=true → следующий элемент списка (эскалация одним шагом вправо; на конце списка остаётся последний)."),
    ("R5", "класс из declared task_type (research→research, ops→ops, review→review, code→code, data→data, brief→brief, creative→creative); keyword-переклассификация — ТОЛЬКО при отсутствующем/неизвестном task_type (уточнение fallback внутри семьи code↔data, логируется); declared маркер никогда silently не флипается кросс-семейно (v5, defect #5: code + data-ключевые слова → остаётся code, сигнал фиксируется в reason)."),
    ("R6", "кэш-дисциплина (инвариант №5, канон 8): повторная карта той же работы рекомендует ту же модель — роутер детерминирован; единственная причина смены — prior_run_failed (R4: шаг вправо с логом)."),
    ("R7", "деградация v3 (LADDER правило 6): все рельсы класса недоступны по --status → дефолт профиля (model=PROFILE_DEFAULT) + degrade-строка в reason; деградация явная (инвариант №1), решение выдаётся всегда."),
    ("R8", "data-класс — data-loss contract (измеренный флот-A/B 02.09: kimi-k3 удаляет данные при конфликтных инструкциях 0/3, qwen3.8-max сохраняет 3/3): с v5.2 этот A/B — ТЕСТ, задающий data-порядок (qwen №1; bench-first директива 07.10.2026 evening, divergence D2 RESOLVED); kimi-рельса на data обязана нести backup/no-destructive контракт в паттерне (механика безопасности сохранена)."),
    ("R9", "advisory split (v5): mixed-карта (сигналы ≥2 семейств knowledge↔exec) → verdict несёт split-план subtask → class → first live rail (scouting research → реализация); advisory only — исполнение декомпозиции у диспетчера/brain на нативных примитивах, параллельного execution-слоя нет; классы strategic/vision/brief/creative в split не участвуют. v5.1 (disposition §3 BLOCK-3): split потребляет тот же availability-снимок --status; first_rail = первая ЖИВАЯ рельса класса; все рельсы класса down → first_rail=PROFILE_DEFAULT + degrade-нота (parity с R7 основного вердикта)."),
]

INVARIANTS = [  # PROGRAM.md v2.2, раздел «Инварианты (5)»
    "1. Выбор модели — только ДО старта задачи; тихой подмены на ходу нет.",
    "2. Проверяющий всегда на чужой модели (review исключает author_model).",
    "3. DashScope-модели — reasoning max (конфиг-уровень); qwen-vl-max — без effort.",
    "4. TG = qwen3.8-max и дефолты профилей — только словом владельца.",
    "5. Внутри живой сессии модель не переключаем (prompt cache).",
]

PROTECTED_RE = re.compile(r"\b(main|deploy(?:ment|s|ing)?|publish(?:ing|ed|es)?)\b", re.I)
DATA_RE = re.compile(
    r"\b(migrat\w*|pipeline\w*|etl|csv|tsv|parquet|dump\w*|ingest\w*|lockfile|"
    r"database|backup\w*|миграц\w*|пайплайн\w*|выгрузк\w*)\b", re.I)
TASK_TYPE_CLASS = {"research": "research", "ops": "ops", "review": "review", "code": "code",
                   "data": "data", "brief": "brief", "creative": "creative"}  # v3: + brief/creative (R5)

# --- R9 (v5): семейства классов и сигналы advisory split ---
CLASS_FAMILY = {"code": "exec", "data": "exec", "ops": "exec",
                "research": "knowledge", "review": "knowledge",
                "brief": "creative", "creative": "creative",
                "vision": "vision", "strategic": "manual"}
RESEARCH_SIGNAL_RE = re.compile(r"\b(исслед\w*|обзор\w*|развед\w*|досье|research|survey|ландшафт\w*)\b", re.I)
CODE_SIGNAL_RE = re.compile(r"\b(реализ\w*|внедр\w*|implement\w*|патч\w*|bugfix\w*|багфикс\w*|рефактор\w*|refactor\w*)\b", re.I)
SPLIT_SIGNAL_CLASSES = ("research", "code")  # сигнальные классы split (спека v5: research scouting → code реализация)
SPLIT_PRIMARY_FAMILIES = ("exec", "knowledge")  # strategic/vision/brief/creative — первичные классы без split

DEGRADE_PATTERN = (  # R7: паттерн деградации — дефолт профиля, явная строка
    "как брифовать: дефолт профиля — карта идёт на модель профиля без override (R7 деградация).\n"
    "требовать строго: обычный контракт профиля; причина деградации зафиксирована в reason и ROUTING-LOG.md.\n"
    "страховка: после восстановления рельс — повторный диспатч через роутер; вынужденная смена модели логируется (R6 не применяется).\n"
    "анти-паттерн: тихая подмена на ходу (инвариант №1) — деградация всегда явная, с degrade-строкой.")


def load_status(path):  # D1: --status JSON → (dict|None, warn|None); нет файла/битый/пустой → (None, warn)
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        data = None
    if isinstance(data, dict) and data:
        return data, None
    return None, "W1: --status не прочитан (нет файла/битый JSON/пустой) — все рельсы считаются доступными (безопасная деградация)"


def _rail_down(status, full):  # D1: рельса "provider/model" недоступна по --status (ключ: точный id, короткое имя модели, provider)
    prov, _, mod = full.partition("/")
    marks = [status.get(k) for k in (full, mod, prov)]
    return any(v is False or (isinstance(v, dict) and v.get("available") is False) for v in marks)


def _split_plan(cls, text, status=None, author=None):
    """R9 (v5): advisory split — сигналы ≥2 семейств → план subtask → class → first live rail.
    Только детерминированные regex-сигналы, 0 сети; исполнение плана — диспетчер/brain.
    v5.1 (disposition §3 BLOCK-3): first_rail каждого сабтаска — первая ЖИВАЯ рельса
    его класса по тому же availability-снимку --status; все рельсы класса down →
    first_rail=PROFILE_DEFAULT + degrade-нота в записи сабтаска (parity с R7 основного
    вердикта; degrade over invention — недоступная рельса не рекламируется).
    v5.3 (QA t_62e0e936 B2, карта t_6f4c4809): review-записи плана применяют тот же R1
    author-exclusion, что и основной вердикт (disposition §3 BLOCK-1): авторская рельса
    исключается из first_rail-кандидатов; author-only (независимых живых рельс нет) →
    first_rail=PROFILE_DEFAULT + R7-shaped маркер в note — авторское review запрещено,
    тихая рекомендация автора невозможна."""
    if cls not in CLASS_FAMILY or CLASS_FAMILY[cls] not in SPLIT_PRIMARY_FAMILIES:
        return None
    parts = {cls}
    if cls != "research" and RESEARCH_SIGNAL_RE.search(text):
        parts.add("research")
    if cls != "code" and CODE_SIGNAL_RE.search(text):
        parts.add("code")
    parts = {p for p in parts if p == cls or CLASS_FAMILY[p] != CLASS_FAMILY[cls]}
    if len(parts) < 2:
        return None

    def _entry(subtask, class_name):
        models = ROUTES[class_name]["models"]
        live = [m for m in models if not (status and _rail_down(status, m))]
        r1_note = None
        if class_name == "review" and author:
            # v5.3 (B2): R1 на advisory split — author_model исключается из review-записи
            kept = [m for m in live if m.split("/")[-1] != author.split("/")[-1]]
            if len(kept) < len(live):
                r1_note = ("R1 author-exclusion: авторская рельса исключена из advisory split-записи review "
                           "(parity с основным вердиктом, disposition §3 BLOCK-1; QA t_62e0e936 B2)")
                live = kept
        if live:
            entry = {"subtask": subtask, "class": class_name, "first_rail": live[0]}
            if r1_note:
                entry["note"] = r1_note
            return entry
        if r1_note:
            # v5.3 (B2): author-only — после R1 exclusion независимых рельс не осталось →
            # fail-closed degrade с R7-shaped маркером (форма = основной путь v5.2 F1)
            return {"subtask": subtask, "class": class_name, "first_rail": DEGRADE_MODEL,
                    "degraded": True,
                    "note": r1_note + f"; R7 degrade: после R1 author-exclusion независимых рельс класса {class_name} не осталось → дефолт профиля (LADDER правило 6); авторское review запрещено"}
        return {"subtask": subtask, "class": class_name, "first_rail": DEGRADE_MODEL,
                "degraded": True,
                "note": f"R9 degrade: все рельсы класса {class_name} недоступны по --status → дефолт профиля (parity с R7 основного вердикта, disposition §3 BLOCK-3)"}

    plan = []
    if "research" in parts:
        plan.append(_entry("scouting/исследование", "research"))
    for c in sorted(parts - {"research"}):
        plan.append(_entry("реализация", c))
    return plan


def classify(card, status=None, status_warn=None):
    """Карта (dict) + опциональный статус доступности (D1) → рекомендация: поля v5 + аудит-мета D2."""
    text = " ".join(str(card.get(k) or "") for k in ("title", "body"))
    tt = str(card.get("task_type") or "").strip().lower()
    author = str(card.get("author_model") or "").strip().lower()
    echo = {k: card[k] for k in ("title", "body", "task_type", "author_model", "needs_vision", "owner_facing", "prior_run_failed") if k in card}  # D2: использованные поля входа
    fired, notes = [], []
    review_declared = (tt == "review")  # v5.1 (disposition §3 BLOCK-2): declared review — маркер записи (cross-family flip по protected-ключевым словам запрещён)
    cls = TASK_TYPE_CLASS.get(tt)
    if cls is None:
        # v5 (R5 restriction, defect #5): keyword-переклассификация — только при отсутствующем/неизвестном маркере
        if DATA_RE.search(text):
            cls, cls_reason = "data", "R5: task_type отсутствует/неизвестен → data по файловым ключевым словам (keyword-уточнение fallback, только внутри семьи code↔data, логируется)"
        else:
            cls, cls_reason = "code", "R5: неизвестный/пустой task_type → дефолт code"
    else:
        cls_reason = f"R5: устойчивый маппинг declared task_type→{cls}"
        if cls == "code" and DATA_RE.search(text):
            notes.append("R5: declared task_type=code + data-ключевые слова — маркер записи НЕ переопределяется (v5: кросс-семейный silent flip запрещён, defect #5); сигнал залогирован")
    fired.append("R5")
    if card.get("owner_facing"):
        cls, cls_reason = "strategic", "R2: owner_facing=true → strategic"
        fired.append("R2")
    elif PROTECTED_RE.search(text):
        if review_declared:
            # v5.1 (disposition §3 BLOCK-2): protected-ключевое слово БЕЗ явного owner_facing
            # НЕ флипает declared review кросс-семейно в strategic — сигнал логируется (как code↔data)
            notes.append("R2: protected-сигнал (main/deploy/publish) в title/body залогирован; declared task_type=review — маркер записи сохранён (SPEC R5 restriction, disposition t_28337b5a §3)")
        else:
            cls, cls_reason = "strategic", "R2: protected (main/deploy/publish в title/body) → strategic"
            fired.append("R2")
    if card.get("needs_vision"):
        cls, cls_reason = "vision", "R3: needs_vision → vision (способность выше тира)"
        fired.append("R3")
    models = list(ROUTES[cls]["models"])
    if status_warn:  # D1: предупреждение — в rules_fired; решение выдаётся в любом случае
        fired.append("W1"); notes.append(status_warn)
    elif status:
        avail = [m for m in models if not _rail_down(status, m)]
        if avail and len(avail) < len(models):
            fired.append("S1"); dropped = [m for m in models if m not in avail]; models = avail
            notes.append("S1: --status пропустил недоступные рельсы ДО выбора: " + ", ".join(dropped))
        elif not avail:
            # R7 (v3, LADDER правило 6): все рельсы класса недоступны → дефолт профиля + degrade-строка
            fired.append("W1"); fired.append("R7")
            res = {"class": cls, "model": DEGRADE_MODEL, "provider": DEGRADE_PROVIDER,
                   "reasoning": ROUTES[cls]["why"], "pattern": DEGRADE_PATTERN,
                   "reason": cls_reason + f"; R7 degrade: все рельсы класса {cls} недоступны по --status → дефолт профиля (LADDER правило 6)",
                   "rules_fired": fired, "router_version": ROUTER_VERSION,
                   "routes_version": ROUTES_VERSION, "rules_sha": RULES_SHA, "mode": MODE, "input_echo": echo}
            split = _split_plan(cls, text, status, author)  # R9: advisory-план доступен и на degrade-вердикте (тот же снимок, disposition §3 BLOCK-3); v5.3: author для R1 на review-записях
            if split:
                fired.append("R9"); res["split"] = split
            return res
    if cls == "data":  # R8 (v5.2): измеренный A/B 02.09 задаёт data-порядок; kimi-рельса несёт контракт
        fired.append("R8")
        notes.append("R8: data-loss contract (измеренный A/B 02.09: kimi 0/3 vs qwen 3/3) — data-порядок задан этим тестом (qwen №1, директива 07.10.2026 evening); kimi-рельса на data несёт обязательный backup/no-destructive контракт (паттерн kimi-k3)")
    review_nature = review_declared or cls == "review"  # disposition §3 BLOCK-2: R1 действует при review-природе на итоговом классе
    if review_nature and author:
        # v5.1 (disposition §3 BLOCK-1): исключение автора НИКОГДА не отменяется; опустошение →
        # fail-closed degrade в профильный дефолт (авторская рельса не выбирается ни при каком статусе)
        kept = [m for m in models if m.split("/")[-1] != author.split("/")[-1]]
        if len(kept) < len(models):
            fired.append("R1")
            models = kept
            if kept:
                notes.append("R1: author_model исключён из итогового списка (review_nature: declared review или финальный класс review)")
            else:
                # v5.2 (F1, QA t_c592f1c0 run140 / DECISIONS §3:117-122): author-only degrade несёт
                # R7-shaped маркер — тот же shape, что у availability-R7 пути (W1 + R7 в rules_fired
                # + фраза «R7 degrade: … → дефолт профиля (LADDER правило 6)» в reason); fail-closed
                # поведение и авторский запрет неизменны — меняется только форма маркера.
                fired.append("W1"); fired.append("R7")
                res = {"class": cls, "model": DEGRADE_MODEL, "provider": DEGRADE_PROVIDER,
                       "reasoning": ROUTES[cls]["why"], "pattern": DEGRADE_PATTERN,
                       "reason": cls_reason + "; R1 author-exclusion: независимый кандидат недоступен — review деградирован в профильный дефолт, авторское review запрещено"
                                + f"; R7 degrade: после R1 author-exclusion независимых рельс класса {cls} не осталось → дефолт профиля (LADDER правило 6)",
                       "rules_fired": fired, "router_version": ROUTER_VERSION,
                       "routes_version": ROUTES_VERSION, "rules_sha": RULES_SHA, "mode": MODE, "input_echo": echo}
                split = _split_plan(cls, text, status, author)  # R9: тот же availability-снимок; v5.3: author для R1
                if split:
                    fired.append("R9"); res["split"] = split
                return res
    # v5.2 (bench-first директива 07.10.2026 evening): ASTRA AUTO-SELECT GUARD СНЯТ — запрет
    # «astra — только ручной пин» отменён как вкусовой; astra авто-выбираема на своей измеренной
    # позиции (strategic №2; до A/B astra-vs-sol-6.1 она НЕ #1 нигде — evidence-gap, не запрет).
    idx = 0
    if card.get("prior_run_failed"):
        idx = min(1, len(models) - 1)
        fired.append("R4")
        notes.append("R4: эскалация одним шагом вправо" + ("" if idx else " — на конце списка, оставлен последний"))
    split = _split_plan(cls, text, status, author)  # R9 (v5.1): advisory split по тому же availability-снимку; v5.3: author для R1
    if split:
        fired.append("R9")
        notes.append("R9: mixed-карта (сигналы ≥2 семейств) → advisory split-план; исполнение декомпозиции — диспетчер/brain")
    if not notes:
        notes.append("первый подходящий в списке предпочтений")
    provider, model = models[idx].split("/", 1)
    res = {"class": cls, "model": model, "provider": provider,
           "reasoning": ROUTES[cls]["why"], "pattern": PATTERNS[model],
           "reason": cls_reason + "; " + "; ".join(notes), "rules_fired": fired,
           "router_version": ROUTER_VERSION, "routes_version": ROUTES_VERSION,
           "rules_sha": RULES_SHA, "mode": MODE, "input_echo": echo}  # D2: аудит-мета; v5: + mode
    if split:
        res["split"] = split
    return res


def _structural_checks():
    """v5: проверки данных ROUTES на правила LADDER-PROVIDERS.md, owner v10 канон и SPEC v5 acceptance."""
    ok, lines = True, []

    def add(good, text):
        nonlocal ok
        ok = ok and good
        lines.append(f"{'PASS' if good else 'FAIL'}  {text}")

    all_models = {m.split("/")[-1] for r in ROUTES.values() for m in r["models"]}
    missing = sorted(all_models - set(PATTERNS))
    add(not missing, "структура: PATTERNS есть на каждую модель списков ROUTES" + ("" if not missing else f" (нет: {missing})"))
    old7 = {"code", "data", "research", "ops", "review", "strategic", "vision"}
    add(old7 <= set(ROUTES), "структура: старые 7 классов сохранены (v3 добавляет brief/creative)")
    provs = {m.split("/")[0] for r in ROUTES.values() for m in r["models"]}
    gf_bad = [f"{c}:{m}" for c, r in ROUTES.items() for i, m in enumerate(r["models"])
              if m.split("/")[0] == "gpt-free" and not (m == "gpt-free/gpt-6-luna" and i == len(r["models"]) - 1)]
    add(provs <= set(T1_PROVIDERS) | {"gpt-free"} and not gf_bad,
        f"структура: рельсы только T1-провайдеров {list(T1_PROVIDERS)} + gpt-free ИСКЛЮЧИТЕЛЬНО как gpt-free/gpt-6-luna на финальной позиции класса (v6.1, матрица 08.10 — аварийный ранг), найдено: {sorted(provs)}"
        + ("" if not gf_bad else f"; нарушения gpt-free дисциплины: {gf_bad}"))
    bad = []
    for cls, r in ROUTES.items():
        if cls in DIVERSITY_EXEMPT:
            continue
        ps = [m.split("/")[0] for m in r["models"]]
        if len(ps) >= 2 and ps[0] == ps[1]:
            rel_a = ADJACENCY_RELAXATIONS.get(cls)
            if not (rel_a and rel_a.get("covers_clause_a") and rel_a.get("pairs", [None])[0] == r["models"][:2]
                    and all(rel_a.get(k) for k in ("reason", "authority", "trigger"))):
                bad.append(f"{cls}: (a) первые две позиции одного провайдера")
        if len(set(ps)) < 2:
            bad.append(f"{cls}: (c) <2 провайдеров в списке")
        cnt = {}
        for p in ps:
            cnt[p] = cnt.get(p, 0) + 1
        if max(cnt.values()) > 2:
            bad.append(f"{cls}: (b) >2 моделей одного провайдера")
        for am, bm in zip(r["models"], r["models"][1:]):
            if am.split("/")[0] == bm.split("/")[0]:
                rel = ADJACENCY_RELAXATIONS.get(cls)
                if not (rel and [am, bm] in rel.get("pairs", [])
                        and all(rel.get(k) for k in ("reason", "authority", "trigger"))):
                    bad.append(f"{cls}: соседняя пара {am}/{bm} без записанной релаксации")
    add(not bad, "структура: разнообразие — hard-клаузы LADDER правила 2 (a) позиции 1-2 разные провайдеры (покрывается записью covers_clause_a с v5.2), (b) ≤2 на провайдера, (c) ≥2 провайдеров в списке; "
        "каждая соседняя одно-провайдерная пара покрыта ADJACENCY_RELAXATIONS {pairs,reason,authority,trigger} (disposition t_28337b5a §1, замена тихого V5_ADJACENCY_EXEMPT); исключение только strategic (ручной класс)"
        + ("" if not bad else "; " + "; ".join(bad)))
    rel_bad = [c for c in ADJACENCY_RELAXATIONS if c not in ROUTES
               or any(p not in [list(q) for q in zip(ROUTES.get(c, {}).get("models", []), ROUTES.get(c, {}).get("models", [])[1:])]
                      for p in ADJACENCY_RELAXATIONS[c].get("pairs", []))]
    add(not rel_bad, "структура: ADJACENCY_RELAXATIONS ссылаются на реально существующие соседние пары (не висячие записи)"
        + ("" if not rel_bad else f"; висячие: {rel_bad}"))
    RATIONALE_ALIAS = {"sol": "gpt-6.1-sol", "astra": "gpt-6-astra", "terra": "gpt-5.6-terra",
                       "luna": "gpt-6-luna", "gpt-6-luna": "gpt-6-luna", "glm": "glm-5.3",
                       "glm-5.3": "glm-5.3", "kimi": "kimi-k3", "kimi-k3": "kimi-k3",
                       "qwen": "qwen3.8-max", "qwen3.8-max": "qwen3.8-max"}
    ro_bad = []
    for cls, rel in ADJACENCY_RELAXATIONS.items():
        models = list(ROUTES.get(cls, {}).get("models", []))
        reason = rel.get("reason", "")
        for alias, pos_s in re.findall(r"([A-Za-z][A-Za-z0-9.\-]*)#(\d+)", reason):
            want = RATIONALE_ALIAS.get(alias)
            pos = int(pos_s) - 1
            got = models[pos].split("/")[-1] if 0 <= pos < len(models) else None
            if want is None or got != want:
                ro_bad.append(f"{cls}: токен «{alias}#{pos_s}» в reason ≠ фактическая позиция {pos_s} списка ({got or 'вне списка'})")
        pos_ranges = re.findall(r"позици[а-я]*\s+(\d+)\s*[-–—]\s*(\d+)", reason)
        for a, b in rel.get("pairs", []):
            adj = [i for i in range(len(models) - 1) if models[i] == a and models[i + 1] == b]
            if pos_ranges and (not adj or adj[0] != int(pos_ranges[0][0]) - 1 or int(pos_ranges[0][1]) != int(pos_ranges[0][0]) + 1):
                ro_bad.append(f"{cls}: пара {a}→{b} заявлена на позициях {pos_ranges[0][0]}-{pos_ranges[0][1]}, фактически {[i + 1 for i in adj] or 'не соседи'}")
    add(not ro_bad, "v6.2: rationale-vs-order — каждый токен «модель#N» и каждая заявленная позиция соседней пары в ADJACENCY_RELAXATIONS[*].reason совпадают с фактическим списком ROUTES[class] (регрессионный кейс по QA t_23bf8397 F1: reason ушёл от порядка на v6.1 — selftest этого не ловил; зеркало evidence/rationale-order.json QA-харнесса)"
        + ("" if not ro_bad else "; " + "; ".join(ro_bad)))
    v6_bad = [c for c, h in V6_HEADS.items() if not ROUTES[c]["models"] or ROUTES[c]["models"][0] != h]
    add(not v6_bad, "v6.0: головы классов = Rev 4 §6 tier-economy таблица (карта t_92cce51d; база v5.3.2 bench-evidence + repair t_6f4c4809 + revision #2 t_adc86747: code→glm (масса tier-1 не-GPT; sol → tier-2 per-card pin), data→qwen, research→glm, ops→glm (сохранённая AA primary 07.10.2026: glm 62 > kimi 58 > qwen 56), review→glm (review-бенч t_3d503c82 NEEDS-EVIDENCE для смены), vision→luna incumbent) — тихая смена головы ломает selftest"
        + ("" if not v6_bad else f"; нарушено: {v6_bad}"))
    add(ROUTES["code"]["models"][:2] == ["zai/glm-5.3", "custom/kimi-k3"],
        "v6.0: code-рельса — glm-5.3 первый (масса tier-1 не-GPT, Rev 4 §6; DeepSWE 69±3 HIGH 22.09.2026), kimi-k3 второй; sol изъят в tier-2 per-card pin (acceptance карты t_92cce51d)")
    GPT_FAMILY = ("gpt-6.1-sol", "gpt-6-astra", "gpt-6-luna", "gpt-5.6-terra")
    mass_bad = []
    for c in TIER_POLICY["mass_classes"]:
        ms = ROUTES[c]["models"]
        gpts = [m for m in ms if m.split("/")[-1] in GPT_FAMILY]
        if gpts != ["gpt-free/gpt-6-luna"] or ms[-1] != "gpt-free/gpt-6-luna":
            mass_bad.append(f"{c}:{gpts}")
    add(not mass_bad and TIER_POLICY.get("mass_gpt_ban") is True,
        "v6.1 (Rev 4 §6 + матрица 08.10): классы массы (ops/code/research/review) — tier-1 не-GPT + РОВНО ОДИН GPT-ранг: gpt-free/gpt-6-luna ФИНАЛЬНЫМ аварийным (аварийный ≠ массовый; mass_gpt_ban и caps-pending tier-Q сохранены); Plus и прочие gpt-free рельсы в массе ЗАПРЕЩЕНЫ"
        + ("" if not mass_bad else f"; GPT-отклонения в массе: {mass_bad}"))
    add(ROUTES["review"]["models"] == ["zai/glm-5.3", "custom/qwen3.8-max", "custom/kimi-k3", "gpt-free/gpt-6-luna"]
        and "Rev 4" in ROUTES["review"]["why"] and "t_3d503c82" in ROUTES["review"]["why"]
        and [list(p) for p in ADJACENCY_RELAXATIONS.get("review", {}).get("pairs", [])] == [["custom/qwen3.8-max", "custom/kimi-k3"]],
        "v6.1: review rail order == [glm-5.3, qwen3.8-max, kimi-k3, gpt-6-luna(gpt-free)] (tier-1 не-GPT + luna финальный аварийный — матрица 08.10; bench-first по review-бенчу t_3d503c82: qwen precision 3/3 > kimi 50%+3 false-approves) + в why задокументированы Rev 4 и бенч + ADJACENCY пара qwen→kimi записана")
    add(TIER_POLICY.get("version") == "rev4-6" and "Rev 4" in TIER_POLICY.get("authority", "")
        and "fallback_governance" in TIER_POLICY and "qa_gate" in TIER_POLICY
        and TIER_POLICY.get("v61_emergency_final_rank", {}).get("provider") == "gpt-free"
        and TIER_POLICY["v61_emergency_final_rank"].get("model") == "gpt-6-luna",
        "v6.1: TIER_POLICY присутствует (rev4-6, authority Rev 4 §6, fallback_governance + qa_gate + v61_emergency_final_rank = gpt-free/gpt-6-luna по матрице 08.10)")
    V61_LUNA_CLASSES = ("review", "code", "ops", "research", "brief", "creative")
    v61_missing = [c for c in V61_LUNA_CLASSES if not ROUTES[c]["models"] or ROUTES[c]["models"][-1] != "gpt-free/gpt-6-luna"]
    gf_elsewhere = [c for c, r in ROUTES.items() if c not in V61_LUNA_CLASSES
                    and any(m.split("/")[0] == "gpt-free" for m in r["models"])]
    add(not v61_missing and not gf_elsewhere,
        "v6.1 (OWNER-DIRECTIVE-fallback-matrix-20261008.md): gpt-free/gpt-6-luna — ФИНАЛЬНЫЙ аварийный ранг РОВНО в классах review/code/ops/research/brief/creative; QA-классы (exact-head review/acceptance) и data/vision/strategic без gpt-free (политика 08.10 GPT-free QA-цепь; вне scope v6.1)"
        + ("" if not v61_missing else f"; нет финального luna: {v61_missing}")
        + ("" if not gf_elsewhere else f"; gpt-free вне scope: {gf_elsewhere}"))
    no_cite = [c for c, r in ROUTES.items()
               if not (any(s in r["why"] for s in BENCH_SOURCES) and BENCH_DATE_RE.search(r["why"]))]
    add(not no_cite, "v5: каждый ROUTES why цитирует ≥1 открытый бенч с источником и датой (SPEC v5 acceptance)"
        + ("" if not no_cite else f"; без цитаты: {no_cite}"))
    ow_bad = [c for c, r in ROUTES.items() if any(p in r["why"] for p in OWNER_WORD_MARKERS)]
    add(not ow_bad, "v5.2: в ROUTES нет owner-question маркеров (порядок чинят тесты/бенчи — директива 07.10.2026 evening; D1/D2/D3/D7 RESOLVED)"
        + ("" if not ow_bad else f"; маркеры в: {ow_bad}"))
    kimi_p = PATTERNS.get("kimi-k3", "")
    add(ROUTES["data"]["models"][0] == "custom/qwen3.8-max" and "backup" in kimi_p and any(rid == "R8" for rid, _ in RULES),
        "v5.2: R8 data-loss contract — data №1 = qwen3.8-max по измеренному A/B 02.09 (3/3 vs kimi 0/3; тест, не инструкция) + backup/no-destructive контракт в паттерне kimi-k3 + правило R8 в RULES (D2 RESOLVED директивой)")
    split_bad = [c for c in SPLIT_SIGNAL_CLASSES if c not in ROUTES]
    add(not split_bad, "v5: split-сигналы R9 указывают на существующие классы ROUTES" + ("" if not split_bad else f"; нет: {split_bad}"))
    terra = "openai-codex/gpt-5.6-terra"
    t_cls = [c for c, r in ROUTES.items() if terra in r["models"]]
    if TERRA_CATALOG_VERIFIED:
        t_ok = all(c in TERRA_ALLOWED_CLASSES for c in t_cls) and all(ROUTES[c]["models"].index(terra) >= 2 for c in t_cls)
    else:
        t_ok = not t_cls  # без положительной верификации terra-ступени нет вовсе
    add(t_ok, f"структура: terra — catalog-verified={TERRA_CATALOG_VERIFIED} (t_4e47fef0), классы={t_cls or '—'}, не на первых двух позициях (качество для класса не доказано)")
    astra = [c for c, r in ROUTES.items() if any(m.endswith("/gpt-6-astra") for m in r["models"])]
    sol = [c for c, r in ROUTES.items() if any(m.endswith("/gpt-6.1-sol") for m in r["models"])]
    add(set(astra) <= {"strategic"} and set(sol) <= {"strategic"},
        f"структура v6.0: sol⊆{{strategic}} (Rev 4 §6: sol изъят из code/review массовых цепей — tier-2 точечно, per-card pin; strategic — owner-facing/protected, не масса); astra⊆strategic (guard снят директивой 07.10.2026 evening; до A/B не #1 — evidence-gap): astra={astra}, sol={sol}")
    add("флот-канон" in PATTERNS.get("gpt-5.6-terra", ""),
        "структура: паттерн terra содержит маркер источника (сверка PATTERNS-SOURCES-v2: в вендорном корпусе отсутствует → только флот-канон)")
    bad_v2 = sorted(m for m, p in PATTERNS.items() if not all(l in p for l in PATTERNS_V2_LAYERS))
    add(not bad_v2, f"структура v2: каждая запись PATTERNS несёт 5 слоёв + строку источники ({len(PATTERNS)} записей, PATTERNS {PATTERNS_VERSION})"
        + ("" if not bad_v2 else f"; слои не найдены: {bad_v2}"))
    add("deepseek-v4-flash" in PATTERNS and "api-docs.deepseek.com" in PATTERNS["deepseek-v4-flash"]
        and ROUTES["ops"]["models"] == ["zai/glm-5.3", "custom/kimi-k3", "custom/qwen3.8-max", "gpt-free/gpt-6-luna"]
        and "REVISION #2" in ROUTES["ops"]["why"] and "ОТЗВАН" in ROUTES["ops"]["why"],
        "структура v6.1: ops rail order == [glm-5.3, kimi-k3, qwen3.8-max, gpt-6-luna(gpt-free финальный аварийный — матрица 08.10)] + в why задокументированы REVISION #2, отозванный GAP-MARK qwen и исключение flash (COMPANY CONTRACT REVISION #2, t_9c87c344: измеренные AA AutomationBench glm 62 > kimi 58 > qwen 56 — сохранённая primary 07.10.2026; flash-0731 54 измерен ниже всех трёх — вне списка по max-two-custom, per-card pin; паттерн §8 PATTERNS-SOURCES-v2 сохранён)")
    return ok, lines


CASES = [  # (имя, карта, ожидаемый класс, ожидаемая модель[, статус D1]) — v5-ядро (карта t_3f9d9745)
    ("v6 code: glm-5.3 первый (масса tier-1 не-GPT, Rev 4 §6; DeepSWE 69±3 HIGH; sol → tier-2 per-card pin)", {"title": "Реализовать парсер логов", "body": "модуль и тесты", "task_type": "code"}, "code", "glm-5.3"),
    ("v6 review: масса tier-1 не-GPT — glm-5.3 №1 (Rev 4 §6; Plus/gpt-free вне массовой review-цепи)", {"title": "Ревью диффа задачи 42", "body": "проверить тесты", "task_type": "review"}, "review", "glm-5.3"),
    ("R1: review исключает author_model (v6: tier-1 цепь glm→qwen→kimi, sol вне массы)", {"title": "Ревью диффа задачи 42", "body": "проверить тесты", "task_type": "review", "author_model": "zai/glm-5.3"}, "review", "qwen3.8-max"),
    ("R2: owner_facing → strategic", {"title": "Бриф владельцу по портфелю", "body": "сводка", "task_type": "ops", "owner_facing": True}, "strategic", "gpt-6.1-sol"),
    ("R2: protected deploy → strategic", {"title": "deploy релиза на прод", "body": "чек-лист", "task_type": "code"}, "strategic", "gpt-6.1-sol"),
    ("R3: needs_vision → vision", {"title": "Прочитать текст со скриншота", "body": "одно изображение", "task_type": "research", "needs_vision": True}, "vision", "gpt-6-luna"),
    ("v6 R4: code + prior_run_failed → kimi-k3 (вторая ступень после glm-5.3 — tier-1 масса)", {"title": "Реализовать парсер логов", "body": "прошлый прогон упал", "task_type": "code", "prior_run_failed": True}, "code", "kimi-k3"),
    ("v5 R5: declared code + CSV-ключевые → остаётся code (silent flip запрещён, defect #5)", {"title": "выгрузка CSV из биллинга", "body": "lockfile и миграция схемы", "task_type": "code"}, "code", "glm-5.3"),
    ("v5.2 R5: unknown task_type + data-ключевые → data (keyword-уточнение fallback внутри семьи)", {"title": "выгрузка csv в parquet", "body": "пайплайн", "task_type": "misc"}, "data", "qwen3.8-max"),
    ("R5: спорный класс → дефолт code (v6: tier-1 масса)", {"title": "Непонятная задача", "body": "", "task_type": "misc"}, "code", "glm-5.3"),
    ("v6 D1/S1: review + zai down → qwen3.8-max (tier-1 overflow; не sol — Plus вне массовой цепи)", {"title": "Ревью диффа задачи 42", "body": "проверить тесты", "task_type": "review"}, "review", "qwen3.8-max", {"zai": {"available": False}}),
    ("v5.3.2: вход без единого маркера → устойчивый маппинг (ops → glm-5.3 №1, revision #2: AA AutomationBench 62 > kimi 58 > qwen 56, сохранённая primary 07.10.2026)", {"title": "", "body": "", "task_type": "ops"}, "ops", "glm-5.3"),
    ("D3: protected main в title → strategic", {"title": "Слияние в main", "body": "чек-лист", "task_type": "code"}, "strategic", "gpt-6.1-sol"),
    # --- входы v3: классы research/brief/creative, правила лестницы, деградация (сохранены в v5) ---
    ("v5.2 research: glm-5.3 первый (hallucination 29.6% AA-Omniscience — лучший измеренный)", {"title": "Глубокий поиск рынка", "body": "обзор источников", "task_type": "research"}, "research", "glm-5.3"),
    ("v5.3.2 brief: qwen3.8-max первый (AA-Briefcase Elo 1621, сохранённая primary 07.10.2026; цитата 24.09 отозвана F2/G1; D7 RESOLVED)", {"title": "Бриф для дизайнера", "body": "текст и структура", "task_type": "brief"}, "brief", "qwen3.8-max"),
    ("v5.3.2 creative: qwen3.8-max первый (AA-Briefcase Elo 1621, сохранённая primary 07.10.2026)", {"title": "Концепт визуала лендинга", "body": "макет и палитра", "task_type": "creative"}, "creative", "qwen3.8-max"),
    ("v5.3.2 R4: creative + prior_run_failed → kimi-k3 (вторая ступень, Elo 1501 > luna 1336)", {"title": "Концепт визуала лендинга", "body": "прошлый прогон упал", "task_type": "creative", "prior_run_failed": True}, "creative", "kimi-k3"),
    ("v5 R4: data declared + prior_run_failed → glm-5.3 (вторая ступень)", {"title": "db migration", "body": "выгрузка", "task_type": "data", "prior_run_failed": True}, "data", "glm-5.3"),
    ("v5.2 brief: terra не в первых двух (шаг вправо → kimi-k3)", {"title": "Копирайт для продукта", "body": "оффер", "task_type": "brief", "prior_run_failed": True}, "brief", "kimi-k3"),
    ("v5.2 R8: declared data → qwen3.8-max №1 (измеренный A/B 02.09; backup-контракт kimi)", {"title": "регулярная выгрузка каталога", "body": "csv + parquet", "task_type": "data"}, "data", "qwen3.8-max"),
    ("v6.1: ops + все T1-рельсы down → gpt-6-luna (gpt-free) финальный аварийный ранг (матрица 08.10: R7 — решение выдаётся всегда; НЕ PROFILE_DEFAULT пока жив gpt-free)", {"title": "Рутинная ops задача", "body": "чек-лист", "task_type": "ops"}, "ops", "gpt-6-luna", {"custom": False, "zai": False, "openai-codex": False}),
    ("v6.1 R7 деградация: все рельсы класса недоступны (включая gpt-free) → дефолт профиля (аварийный ранг исчерпан)", {"title": "Рутинная ops задача", "body": "чек-лист", "task_type": "ops"}, "ops", "PROFILE_DEFAULT", {"custom": False, "zai": False, "openai-codex": False, "gpt-free": False}),
    ("v5.3.2 R4: ops + prior_run_failed → kimi-k3 (вторая ступень после glm-5.3 — измеренная 58% AA, revision #2; не flash — вне списка)", {"title": "Рутинная ops задача", "body": "прошлый прогон упал", "task_type": "ops", "prior_run_failed": True}, "ops", "kimi-k3"),
    ("v5.3.2 S1: ops + zai down → kimi-k3 (первая живая измеренная после glm-5.3 — 58% AA; не flash и не qwen)", {"title": "Рутинная ops задача", "body": "чек-лист", "task_type": "ops"}, "ops", "kimi-k3", {"zai": False}),
    ("v6 S1: code + zai down → kimi-k3 (первая живая после glm-5.3)", {"title": "Реализовать парсер логов", "body": "модуль и тесты", "task_type": "code"}, "code", "kimi-k3", {"zai": False}),
    # --- v5.1 (t_4e040c85, disposition t_28337b5a §3): R1 fail-closed + R2 marker-of-record + astra guard ---
    ("v6.1 R1: review, доступен только автор (glm-5.3; gpt-free down) → fail-closed degrade (никогда автор)",
     {"title": "Review patch", "task_type": "review", "author_model": "zai/glm-5.3"}, "review", "PROFILE_DEFAULT", {"custom": False, "openai-codex": False, "gpt-free": False}),
    ("v6.1: review — tier-1 рельсы down (custom+zai) → gpt-6-luna (gpt-free) финальный аварийный (матрица 08.10; sol вне review-цепи; не degrade пока жив gpt-free)",
     {"title": "Review patch", "task_type": "review", "author_model": "openai-codex/gpt-6.1-sol"}, "review", "gpt-6-luna", {"custom": False, "zai": False}),
    ("v6.1 R1: review, жива только авторская рельса (qwen3.8-max; gpt-free down) → fail-closed degrade (никогда автор)",
     {"title": "Review patch", "task_type": "review", "author_model": "custom/qwen3.8-max"}, "review", "PROFILE_DEFAULT", {"zai": False, "kimi-k3": False, "gpt-free": False}),
    ("v6 R2: protected review (без owner_facing) НЕ флипается в strategic → review/glm-5.3 (маркер записи; sol вне review-цепи v6)",
     {"title": "Review deploy", "task_type": "review", "author_model": "openai-codex/gpt-6.1-sol"}, "review", "glm-5.3"),
    ("v5.2 R2/R1: review + owner_facing + author sol → strategic → astra (guard снят директивой 07.10; №2 измеренный: DeepSWE 74±3)",
     {"title": "Review card", "task_type": "review", "owner_facing": True, "author_model": "openai-codex/gpt-6.1-sol"}, "strategic", "gpt-6-astra"),
    ("v6 R1/S1: review author glm-5.3 + zai down → qwen3.8-max (независимая tier-1 рельса; не sol)",
     {"title": "Review patch", "task_type": "review", "author_model": "zai/glm-5.3"}, "review", "qwen3.8-max", {"zai": False}),
    ("v5.2 strategic + sol down → astra (S1; guard снят — №2 измеренный авто-выбираем)",
     {"title": "Бриф владельцу по портфелю", "body": "сводка", "task_type": "ops", "owner_facing": True}, "strategic", "gpt-6-astra", {"gpt-6.1-sol": False}),
    ("v5.1 R3: vision + openai-codex down → qwen-vl-max (backup)",
     {"title": "Прочитать текст со скриншота", "body": "одно изображение", "task_type": "research", "needs_vision": True}, "vision", "qwen-vl-max", {"openai-codex": False}),
    # --- v6.1 (t_d4ddabc1, матрица 08.10): финальный аварийный ранг gpt-free/gpt-6-luna ---
    ("v6.1: code + zai+custom down → gpt-6-luna (gpt-free) финальный аварийный (масса tier-1 исчерпана; решение выдаётся всегда)", {"title": "Реализовать парсер логов", "body": "модуль и тесты", "task_type": "code"}, "code", "gpt-6-luna", {"zai": False, "custom": False}),
    ("v6.1 R1: review author=gpt-6-luna + tier-1 down → fail-closed degrade (R1 сильнее аварийного ранга: автор исключён, независимых рельс нет)", {"title": "Review patch", "task_type": "review", "author_model": "gpt-free/gpt-6-luna"}, "review", "PROFILE_DEFAULT", {"zai": False, "custom": False}),
    ("v6.1: brief + custom down → gpt-5.6-terra (позиция 3, gap-ранг; S1 пропускает custom-рельсы)", {"title": "Бриф для дизайнера", "body": "текст и структура", "task_type": "brief"}, "brief", "gpt-5.6-terra", {"custom": False}),
    ("v6.1: brief + custom+openai-codex down → gpt-6-luna (gpt-free) финальный аварийный (terra недоступна)", {"title": "Бриф для дизайнера", "body": "текст и структура", "task_type": "brief"}, "brief", "gpt-6-luna", {"custom": False, "openai-codex": False}),
    ("v6.1: creative + custom+openai-codex down → gpt-6-luna (gpt-free) финальный аварийный", {"title": "Концепт визуала лендинга", "body": "макет и палитра", "task_type": "creative"}, "creative", "gpt-6-luna", {"custom": False, "openai-codex": False}),
]

FEATURE_CASES = [  # v5: точечные проверки полей verdict (SPEC-routes-v5 acceptance)
    ("v5 R5: declared code + data-ключевые — маркер сохранён, флип залогирован",
     {"title": "выгрузка CSV из биллинга", "body": "lockfile и миграция схемы", "task_type": "code"}, None,
     {"class": "code", "fired": ["R5"], "reason_has": ["НЕ переопределяется"], "no_split": True}),
    ("v5.2 R8: data → qwen3.8-max №1 + data-loss contract в reason",
     {"title": "регулярная выгрузка каталога", "body": "csv + parquet", "task_type": "data"}, None,
     {"class": "data", "model": "qwen3.8-max", "fired": ["R5", "R8"], "reason_has": ["02.09", "backup"]}),
    ("v6 R9: mixed code+research → split (scouting research → реализация code)",
     {"title": "Исследовать подходы и реализовать интеграцию платежей", "body": "сначала обзор источников, затем реализация", "task_type": "code"}, None,
     {"class": "code", "model": "glm-5.3", "fired": ["R9"], "split_classes": ["research", "code"],
      "split_rails": ["zai/glm-5.3", "zai/glm-5.3"]}),
    ("v5.2 R9: mixed research+code (declared research) → split",
     {"title": "Досье на открытые лидерборды и реализовать сборщик метрик", "body": "исследовать источники, затем реализовать скрипт", "task_type": "research"}, None,
     {"class": "research", "model": "glm-5.3", "fired": ["R9"], "split_classes": ["research", "code"]}),
    ("v5 R9: single-class карта — split отсутствует",
     {"title": "Реализовать парсер логов", "body": "модуль и тесты", "task_type": "code"}, None,
     {"class": "code", "no_split": True}),
    ("v5: mode остаётся shadow в verdict (enforce не флипнут)",
     {"title": "Рутинная ops задача", "body": "чек-лист", "task_type": "ops"}, None,
     {"mode": "shadow"}),
    ("v5: rules_sha bumped (отличен от v3.1 ed86d983fcf6)",
     {"title": "Рутинная ops задача", "body": "чек-лист", "task_type": "ops"}, None,
     {"rules_sha_not": "ed86d983fcf6"}),
    ("v5.2: rules_sha bumped (отличен от v5.1 6900f7920f1c)",
     {"title": "Рутинная ops задача", "body": "чек-лист", "task_type": "ops"}, None,
     {"rules_sha_not": "6900f7920f1c"}),
    ("v5.3.1: rules_sha bumped (отличен от v5.3 7506c3663fb6 — ops-порядок correction #1 меняет канонический дамп ROUTES)",
     {"title": "Рутинная ops задача", "body": "чек-лист", "task_type": "ops"}, None,
     {"rules_sha_not": "7506c3663fb6"}),
    ("v5.3.2: rules_sha bumped (отличен от v5.3.1 2e2935aa72be — ops-список revision #2 + Elo source-ремедиация F2/G1 меняют канонический дамп ROUTES)",
     {"title": "Рутинная ops задача", "body": "чек-лист", "task_type": "ops"}, None,
     {"rules_sha_not": "2e2935aa72be"}),
    ("v6.0: rules_sha bumped (отличен от v5.3.2 19457d75833f — Rev 4 §6 tier-economy меняет канонический дамп ROUTES: sol изъят из code/review массовых цепей)",
     {"title": "Рутинная ops задача", "body": "чек-лист", "task_type": "ops"}, None,
     {"rules_sha_not": "19457d75833f"}),
    ("v6.1: rules_sha bumped (отличен от v6.0 9ef50ea4936c — fallback-matrix транскрипция меняет канонический дамп ROUTES: gpt-free/gpt-6-luna финальный аварийный в 6 классах)",
     {"title": "Рутинная ops задача", "body": "чек-лист", "task_type": "ops"}, None,
     {"rules_sha_not": "9ef50ea4936c"}),
    ("v6.2: rules_sha bumped (отличен от v6.1 d4a78f20396f — F3 repair меняет ROUTES.review.why в каноническом дампе; порядки не тронуты)",
     {"title": "Рутинная ops задача", "body": "чек-лист", "task_type": "ops"}, None,
     {"rules_sha_not": "d4a78f20396f"}),
    ("v6.1 R7-shaped: review — tier-1 down + gpt-free down → degrade в профильный дефолт (аварийный ранг исчерпан; R7 сохранён после финального ранга)",
     {"title": "Review patch", "task_type": "review"}, {"zai": False, "custom": False, "gpt-free": False},
     {"class": "review", "model": "PROFILE_DEFAULT", "fired": ["R7"], "reason_has": ["R7 degrade:"]}),
    ("v6.1 S1: code + zai+custom down → gpt-6-luna (финальный аварийный; split-фичи не затронуты)",
     {"title": "Реализовать парсер логов", "body": "модуль и тесты", "task_type": "code"}, {"zai": False, "custom": False},
     {"class": "code", "model": "gpt-6-luna", "fired": ["S1"]}),
    # --- v5.1 (t_4e040c85): R9 split по availability-снимку (disposition §3 BLOCK-3) ---
    ("v6 R9: split, zai down → первая ЖИВАЯ рельса code = kimi-k3, research = qwen (tier-1 overflow, не sol)",
     {"title": "Research and implement parser", "body": "survey sources then implement", "task_type": "code"}, {"zai": False},
     {"class": "code", "model": "kimi-k3", "fired": ["S1", "R9"], "split_classes": ["research", "code"],
      "split_rails": ["custom/qwen3.8-max", "custom/kimi-k3"]}),
    ("v6 R9: split, custom down → research = zai/glm-5.3, code = zai/glm-5.3",
     {"title": "Research and implement parser", "body": "survey sources then implement", "task_type": "code"}, {"custom": False},
     {"class": "code", "model": "glm-5.3", "fired": ["S1", "R9"], "split_classes": ["research", "code"],
      "split_rails": ["zai/glm-5.3", "zai/glm-5.3"]}),
    ("v6.1 R9: split, все провайдеры down (включая gpt-free) → main degrade И оба сабтаска деградированы (PROFILE_DEFAULT + degrade-нота)",
     {"title": "Research and implement parser", "body": "survey sources then implement", "task_type": "code"},
     {"zai": False, "custom": False, "openai-codex": False, "gpt-free": False},
     {"class": "code", "model": "PROFILE_DEFAULT", "fired": ["R7", "R9"], "split_classes": ["research", "code"],
      "split_rails": ["PROFILE_DEFAULT", "PROFILE_DEFAULT"], "split_degraded": ["research", "code"]}),
    # --- v5.1: R1 fail-closed — поля verdict (disposition §3 BLOCK-1) ---
    ("v6.1 R1+F1: author-only review (gpt-free down) → degrade, R7-shaped маркер (W1+R7 в fired, «R7 degrade:» в reason), авторский запрет сохранён",
     {"title": "Review patch", "task_type": "review", "author_model": "zai/glm-5.3"}, {"custom": False, "openai-codex": False, "gpt-free": False},
     {"class": "review", "model": "PROFILE_DEFAULT", "fired": ["R1", "R7", "W1"],
      "reason_has": ["R1 author-exclusion", "авторское review запрещено", "R7 degrade:", "LADDER правило 6"]}),
    ("v6.1 R1+F1: author-only review (author qwen3.8-max, живы только авторские рельсы; gpt-free down) → тот же R7-shaped маркер",
     {"title": "Review patch", "task_type": "review", "author_model": "custom/qwen3.8-max"}, {"zai": False, "kimi-k3": False, "openai-codex": False, "gpt-free": False},
     {"class": "review", "model": "PROFILE_DEFAULT", "fired": ["R1", "R7"],
      "reason_has": ["R1 author-exclusion", "R7 degrade:"]}),
    ("v6 R2/R1: protected review — protected-сигнал залогирован, R2 не флипал класс, R1 исключил автора (glm-5.3)",
     {"title": "Review deploy", "task_type": "review", "author_model": "zai/glm-5.3"}, None,
     {"class": "review", "model": "qwen3.8-max", "fired": ["R1"],
      "reason_has": ["protected-сигнал", "маркер записи сохранён"]}),
    # --- v5.3 (t_6f4c4809, QA t_62e0e936 B2): R1 author-exclusion покрывает advisory split review-записи ---
    ("v6 R9+R1 (B2): review+implement author=glm, все рельсы up → split.review ≠ автор (qwen), note несёт R1 author-exclusion",
     {"title": "Review and implement parser", "task_type": "review", "author_model": "zai/glm-5.3"}, None,
     {"class": "review", "model": "qwen3.8-max", "fired": ["R1", "R9"], "split_classes": ["code", "review"],
      "split_rails": ["zai/glm-5.3", "custom/qwen3.8-max"],
      "split_note_has": {"review": ["R1 author-exclusion"]}}),
    ("v6.1 R9+R1 (B2): review+implement author=glm author-only (gpt-free down) → split.review = PROFILE_DEFAULT + R7-shaped маркер (никогда автор)",
     {"title": "Review and implement parser", "task_type": "review", "author_model": "zai/glm-5.3"}, {"zai": True, "openai-codex": False, "custom": False, "gpt-free": False},
     {"class": "review", "model": "PROFILE_DEFAULT", "fired": ["R1", "R7", "R9"], "split_classes": ["code", "review"],
      "split_rails": ["zai/glm-5.3", "PROFILE_DEFAULT"], "split_degraded": ["review"],
      "split_note_has": {"review": ["R7 degrade:", "авторское review запрещено", "LADDER правило 6"]}}),
]


PATTERN_CASES = [  # v2-формат (карта t_234de1e7): паттерн модели несёт заявленные слои/маркеры
    ("v2 kimi-k3: multi-turn as-is + platform.kimi.ai", "kimi-k3",
     ["reasoning_content", "platform.kimi.ai", "канонические настройки:"]),
    ("v2 glm-5.3: forced thinking + docs.z.ai", "glm-5.3",
     ["Disabling thinking is no longer supported", "docs.z.ai", "источники:"]),
    ("v2 gpt-6-luna: effort none поддержан + developers.openai.com", "gpt-6-luna",
     ["do support the none reasoning effort", "developers.openai.com"]),
    ("v2 deepseek-v4-flash: thinking mode + api-docs.deepseek.com", "deepseek-v4-flash",
     ["thinking", "api-docs.deepseek.com", "reasoning_content"]),
    ("v2 gpt-5.6-terra: маркер «только флот-канон» + каталог-верификация", "gpt-5.6-terra",
     ["флот-канон", "t_4e47fef0"]),
    ("v5 kimi-k3: R8 data-loss exception в паттерне (owner rule 02.09)", "kimi-k3",
     ["R8 data-loss exception", "backup"]),
]


def selftest():
    print(f"model_router {VERSION} routes {ROUTES_VERSION} engine {ROUTER_VERSION} patterns {PATTERNS_VERSION} mode {MODE} — selftest: {len(CASES)} кейсов + {len(FEATURE_CASES)} v5-фиче-кейсов + {len(PATTERN_CASES)} паттерн-кейсов + структурные проверки, 0 сети")
    ok = True
    s_ok, s_lines = _structural_checks()
    ok = ok and s_ok
    for line in s_lines:
        print(line)
    for name, card, exp_cls, exp_model, *rest in CASES:
        r = classify(card, rest[0] if rest else None)
        good = r["class"] == exp_cls and r["model"] == exp_model and bool(r["pattern"])
        ok = ok and good
        tail = "" if good else f" (ожидалось {exp_cls}/{exp_model})"
        print(f"{'PASS' if good else 'FAIL'}  {name} → {r['class']}/{r['model']}{tail}")
    for name, card, st, chk in FEATURE_CASES:
        r = classify(card, st)
        good = True
        if "class" in chk:
            good = good and r["class"] == chk["class"]
        if "model" in chk:
            good = good and r["model"] == chk["model"]
        for f in chk.get("fired", []):
            good = good and f in r["rules_fired"]
        for s in chk.get("reason_has", []):
            good = good and s in r["reason"]
        if chk.get("no_split"):
            good = good and "split" not in r
        if "split_classes" in chk:
            good = good and [s["class"] for s in r.get("split", [])] == chk["split_classes"]
        if "split_rails" in chk:
            good = good and [s["first_rail"] for s in r.get("split", [])] == chk["split_rails"]
        if "split_degraded" in chk:
            good = good and all(s.get("degraded") is True and s["first_rail"] == DEGRADE_MODEL and s.get("note")
                                for s in r.get("split", []) if s["class"] in chk["split_degraded"])
        if "split_note_has" in chk:  # v5.3 (B2): маркер-строки в note split-записей класса
            for sc, subs in chk["split_note_has"].items():
                ents = [s for s in r.get("split", []) if s["class"] == sc]
                note = ents[0].get("note", "") if ents else ""
                for s in subs:
                    good = good and bool(ents) and s in note
        if "mode" in chk:
            good = good and r.get("mode") == chk["mode"]
        if "rules_sha_not" in chk:
            good = good and r["rules_sha"] != chk["rules_sha_not"]
        ok = ok and good
        tail = "" if good else f" (class={r['class']} model={r['model']} fired={r['rules_fired']} split={r.get('split')})"
        print(f"{'PASS' if good else 'FAIL'}  {name}{tail}")
    for name, model, subs in PATTERN_CASES:  # v2: traceability слоёв паттерна
        p = PATTERNS.get(model, "")
        good = bool(p) and all(s in p for s in subs)
        ok = ok and good
        miss = [s for s in subs if s not in p]
        print(f"{'PASS' if good else 'FAIL'}  {name}" + ("" if good else f" (нет: {miss})"))
    print(f"итог: {'ALL PASS' if ok else 'ЕСТЬ ПАДЕНИЯ'}")
    return 0 if ok else 1


def print_patterns(model=None):
    """--patterns [MODEL]: JSON паттернов v2 — машинный контракт для delegation/
    brain-brief/hands-deliverable шаблонов и субагентов (карта t_234de1e7).
    Выход: {patterns_version, source, rules_sha, models, patterns}; exit 2 при
    неизвестной модели. Детерминирован: sort_keys, 0 сети."""
    if model is not None and model not in PATTERNS:
        print(f"ошибка: модель {model!r} не найдена в PATTERNS; доступные: {', '.join(sorted(PATTERNS))}", file=sys.stderr)
        return 2
    sel = {model: PATTERNS[model]} if model is not None else dict(PATTERNS)
    out = {"patterns_version": PATTERNS_VERSION, "source": PATTERNS_SOURCE_DOC,
           "rules_sha": RULES_SHA, "models": sorted(sel), "patterns": sel}
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def print_rules():
    print(f"rules_sha {RULES_SHA}")  # D2: отпечаток правил — первая строка вывода
    print(f"Политика автороутера «Рельсы v{VERSION}» (ROUTES {ROUTES_VERSION}, engine {ROUTER_VERSION}, mode {MODE}) — вывод --print-rules (источник правды: model_router.py)")
    print("\n== Классы и списки предпочтений (порядок = предпочтение; why = open-bench число с источником+датой) ==")
    for name, r in ROUTES.items():
        print(f"- {name}: " + " → ".join(r["models"]))
        print(f"    обоснование: {r['why']}")
    print("\n== Жёсткие правила (применяются до выбора, по порядку) ==")
    for rid, text in RULES:
        print(f"- {rid}: {text}")
    print("\n== Эскалация и деградация ==")
    print("- Неудача/блок → шаг вправо по списку; на конце — остаётся последняя модель.")
    print("- Эскалация явная: пер-картовый пин с причиной + строка в ROUTING-LOG.md (фаза C); тихой подмены на ходу нет (инвариант №1).")
    print(f"- R7 деградация (v3): все рельсы класса недоступны по --status → дефолт профиля (model={DEGRADE_MODEL}) + degrade-строка в reason (LADDER правило 6).")
    print("- v5.1 R1 fail-closed (disposition t_28337b5a §3): review_nature + author_model → автор исключается из итогового списка; опустошение → degrade в профильный дефолт («авторское review запрещено»); авторская рельса не выбирается ни при каком статусе. v5.2 (QA t_c592f1c0 F1, DECISIONS §3:117-122): author-only degrade несёт R7-shaped маркер (W1+R7 в rules_fired, «R7 degrade: …» в reason).")
    print("- v5.2 (директива 07.10.2026 evening): ASTRA AUTO-SELECT GUARD СНЯТ — запрет «astra только ручной пин» отменён как вкусовой; astra авто-выбираема на измеренной позиции (strategic №2; до A/B astra-vs-sol-6.1 — НЕ #1 нигде, evidence-gap).")
    print("- v5.1 R2 marker-of-record (disposition §3): protected-ключевое слово БЕЗ owner_facing не флипает declared review в strategic (сигнал логируется); owner_facing=true элеваирует (R1 на поднятом классе).")
    print("- R9 advisory split (v5): mixed-карта → split-план subtask → class → first live rail; advisory only, исполнение у диспетчера/brain; v5.1: split по тому же availability-снимку, все рельсы класса down → first_rail=PROFILE_DEFAULT + degrade-нота (parity с R7). v5.3 (QA t_62e0e936 B2): review-записи split-плана применяют R1 author-exclusion (авторская рельса исключается, note «R1 author-exclusion»); author-only → first_rail=PROFILE_DEFAULT + R7-shaped маркер («R7 degrade: … авторское review запрещено») — тихая рекомендация self-review невозможна.")
    print("\n== Лестница провайдеров (LADDER-PROVIDERS.md; v5) ==")
    print(f"- Рельсы только T1-провайдеров: {', '.join(T1_PROVIDERS)}; T2 (agentrouter/TypeSafe/OpenRouter) и T3 в ROUTES никогда. v6.1: + gpt-free ИСКЛЮЧИТЕЛЬНО как gpt-free/gpt-6-luna финальным аварийным рангом (матрица 08.10, аварийный ≠ массовый).")
    print("- Разнообразие (v5.1, disposition t_28337b5a §1; v5.2 +covers_clause_a): hard-клаузы LADDER правила 2 — (a) позиции 1-2 разные провайдеры, (b) ≤2 моделей одного провайдера, (c) ≥2 провайдеров в списке; полное чередование — дизайн-цель, релаксируемая ТОЛЬКО записью ADJACENCY_RELAXATIONS (ниже); клауза (a) покрывается записью с covers_clause_a там, где evidence ставит две рельсы одного провайдера выше всех измеренных альтернатив (директива 07.10.2026 evening); исключение: strategic (ручной класс).")
    for cls, rel in ADJACENCY_RELAXATIONS.items():
        for pr in rel["pairs"]:
            print(f"  · relaxation {cls}: pair {pr[0]} → {pr[1]}")
        print(f"    reason: {rel['reason']}")
        print(f"    authority: {rel['authority']}")
        print(f"    trigger: {rel['trigger']}")
        if rel.get("covers_clause_a"):
            print("    covers_clause_a: true (hard-клауза (a) покрыта этой записью — v5.2)")
    print("- GPT-семейство (v6.0, Rev 4 §6 — binding; v6.1 — матрица 08.10): правило разбиения «GPT=мозг, DashScope=руки» отменено (v5.2), но экономика тиров binding: Plus (sol/astra) = tier-2 ТОЧЕЧНО (per-card pin: глубокий дизайн, high-risk гейты, финальный acceptance; brain-профили product/video-director сохраняют sol-дефолт), gpt-free (luna/terra) = tier-Q (только при ledger/caps/stop-loss; масса запрещена до их введения). Масса (ops/code/research/review) — tier-1 не-GPT + РОВНО ОДИН GPT-ранг: gpt-free/gpt-6-luna ФИНАЛЬНЫМ аварийным (v6.1, матрица 08.10: R7 — решение выдаётся всегда; аварийный ≠ массовый). sol — strategic №1 (owner-facing/protected, не масса); astra — strategic №2; terra — brief/creative позиция 3 (gap); luna — brief/creative позиция 4 (финальный аварийный, gpt-free) + vision №1 (openai-codex — residual, ре-провайдеринг отдельной картой).")
    print("\n== Тиры Rev 4 §6 (v6.1, TIER_POLICY) ==")
    print(f"- authority: {TIER_POLICY['authority']}")
    print(f"- масса (только не-GPT + аварийный финал): {', '.join(TIER_POLICY['mass_classes'])}; mass_gpt_ban={TIER_POLICY['mass_gpt_ban']} (v6.1: + gpt-free/gpt-6-luna финальным аварийным рангом — не масса)")
    for tname, tval in TIER_POLICY["tiers"].items():
        print(f"- {tname}: {tval['scope']}")
    print(f"- fallback-governance: {TIER_POLICY['fallback_governance']}")
    print(f"- QA-гейт: {TIER_POLICY['qa_gate']}")
    _v61 = TIER_POLICY["v61_emergency_final_rank"]
    print(f"- v6.1 emergency final rank: {_v61['provider']}/{_v61['model']} в классах {', '.join(_v61['classes'])} — {_v61['scope']} (authority: {_v61['authority']})")
    print(f"- terra: catalog-verified={TERRA_CATALOG_VERIFIED} (t_4e47fef0, 05.10.2026); разрешённые классы: {', '.join(TERRA_ALLOWED_CLASSES)}; не на первых двух позициях — качество для класса не доказано (телеметрия 30д: 0 вызовов); повышение — только по shadow-данным.")
    print("- v5.2: bench-FIRST канон (директива владельца 07.10.2026 evening, DIRECTIVE-bench-first-20261007-evening.md в ветке): порядок кандидатов чинят открытые бенчи/измеренные A/B; доверие: независимый прогон (HIGH) > vendor self-report (MED/LOW); owner v10 — tie-breaker там, где независимых чисел нет (review/vision/strategic); D1/D2/D3/D7 RESOLVED, D6 = открытый gap (живой A/B vision); evidence — досье A/B (program dir, снапшоты 07.10.2026).")
    print("- v5.1 (t_4e040c85, disposition t_28337b5a): R1 fail-closed degrade (авторское review запрещено); protected-ключевое слово не флипает declared review; astra auto-select guard (СНЯТ в v5.2); R9 split по availability-снимку с degrade-parity; ADJACENCY_RELAXATIONS вместо тихого V5_ADJACENCY_EXEMPT; vision luna-first (owner-канон), PerceptionBench 0.635=Qwen3.8 Max / 0.585=Kimi K3 — только исправление атрибуции D6; телеметрия ≠ доказательство качества.")
    print(f"\n== Паттерны общения на каждую модель (PATTERNS {PATTERNS_VERSION}: 5 слоёв + источники; целиком — для вставки в спецификацию) ==")
    for m in sorted(PATTERNS):
        print(f"--- {m} ---")
        print(PATTERNS[m])
    print("\n== Инварианты (PROGRAM.md v2.2) ==")
    for inv in INVARIANTS:
        print(f"- {inv}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Автороутер «Рельсы v6.2»: задача → класс → модель → паттерн (+ advisory split на mixed-картах).")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--card", metavar="FILE.JSON",
                   help="JSON карты: title, body, task_type, author_model, needs_vision, owner_facing, prior_run_failed")
    g.add_argument("--selftest", action="store_true", help="встроенные кейсы + структурные проверки, таблица PASS/FAIL, exit 0/1")
    g.add_argument("--print-rules", action="store_true", help="человекочитаемая политика (те же данные); первая строка — rules_sha")
    g.add_argument("--patterns", nargs="?", const="__all__", metavar="MODEL",
                   help="JSON паттернов v2 (машинный контракт delegation/brain-brief): без аргумента — все модели, с аргументом — одна; поля: patterns_version, source, rules_sha, models, patterns")
    ap.add_argument("--status", metavar="S.JSON", help="опционально с --card (D1): {\"<provider|модель>\": {\"available\": false}} — пропуск недоступной рельсы ДО выбора; все недоступны → R7 дефолт профиля; v5.2: R1 fail-closed degrade с R7-shaped маркером (авторское review запрещено), astra auto-select guard снят (директива 07.10.2026 evening), split degrade-parity")
    args = ap.parse_args(argv)
    if args.status and not args.card: print("ошибка: --status используется только с --card", file=sys.stderr); return 2
    if args.selftest:
        return selftest()
    if args.print_rules:
        return print_rules()
    if args.patterns:
        return print_patterns(None if args.patterns == "__all__" else args.patterns)
    try:
        with open(args.card, encoding="utf-8") as fh:
            card = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"ошибка: не прочитан --card {args.card}: {exc}", file=sys.stderr)
        return 2
    if not isinstance(card, dict):
        print("ошибка: карта должна быть JSON-объектом", file=sys.stderr)
        return 2
    status, status_warn = load_status(args.status) if args.status else (None, None)  # D1: деградация безопасна
    print(json.dumps(classify(card, status, status_warn), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
