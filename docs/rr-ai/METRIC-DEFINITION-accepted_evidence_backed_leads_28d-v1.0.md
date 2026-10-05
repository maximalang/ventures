# METRIC DEFINITION — accepted_evidence_backed_leads_28d (operational v1.0, ADOPTED)

Статус: ПРИНЯТО company-решением (карта t_0a65e710, 02.10.2026) ДО любой instrumentation — требование SPEC 2.0 §7.1 выполнено.
Источник канона имени: C:/Users/max/Desktop/all/ventures/PORTFOLIO.md L17-20 — имя первичной метрики НЕ меняется этим решением.
Источник формулировки: SPEC 2.0 §7.1 (hash 65f28c45b4ce43aa5004613386ed2515aaf8db9a10a6267963df3d411e408067) — provisional-предложение product принято company как операционное определение v1.0 со следующими уточнениями. Файл SPEC НЕ изменён (QA hash-якорь сохранён); снятие «provisional»-пометки в §7.1 — будущая авторская docs-ревизия отдельной lane.
Проверка конфликта единиц (§7.1: «если действующий канон использует другую единицу — company явно разрешает конфликт ДО изменений»): канон PORTFOLIO.md задаёт только имя; dashboard 7/30d-счётчики (apps/web/lib/dashboard-data.ts L93-129) — status proxy, не конкурирующее определение. Конфликт НЕ обнаружен (зафиксировано QA-ревью t_a5071b8b §5 и этим решением).

## 1. Единица и событие (acceptance)
Один счёт = ПЕРВЫЙ реальный ручной transition пользователя в feedback_status ∈ {contacted, replied, meeting, won} по уникальной паре (workspace_id, org_id). Последующие переходы той же пары (replied→meeting→won) счёт не добавляют. Строка кандидата/профиля — НЕ единица; COUNT кандидатов ≠ число уникальных принятых компаний.

## 2. Acceptance timestamp и окно
t_accept = серверный UTC-таймстамп первого квалифицирующего ручного перехода (событийное время действия, не created_at кандидата, не время отчёта). Окно = rolling 28 дней [T−28d, T] на момент запроса; публикуемые отчёты фиксируют конец периода T и метку периода. Переход, случившийся вне окна, в счёт окна не входит.

## 3. Evidence snapshot (as-of acceptance)
На t_accept evidence-пакет лида ОБЯЗАН содержать: source ref (URL/ID + published/observed time), проверенное непросроченное evidence (validUntil > t_accept по действующему deterministic-гейту), provenance, и прохождение действующих на t_accept deterministic gate + contact policy. Снимок хранится неизменяемо/версионно; replay воспроизводит evidence AS-OF acceptance (позднейшие изменения/истечения задним числом счёт не отменяют и не создают).

## 4. Dedup
Повторные кандидаты/профили/переходы одной компании в том же workspace не создают новый outcome в том же 28-дневном окне. Откат статуса и повторный accept в том же окне — считается только первый квалифицирующий t_accept. Новый accept той же пары (workspace_id, org_id) может дать счёт в более позднем окне лишь если предшествующий t_accept вышел за границы этого окна. Tenancy изолирована: одна компания, принятая в двух разных workspace = два счёта (разные единицы).

## 5. Исключения (не считаются никогда)
test/synthetic/internal/bot accounts; mock feedback; auto-accepted (не ручной UI-action) переходы; acceptance без evidence-снимка либо с отсутствующим/просроченным/невалидным на t_accept evidence; summary view; AI call; draft copy; research/study-решения (P0 study plans ≠ accepted leads — 20 планов эксперимента не дают ни одного счёта); действия по suppressed/policy-restricted записям; записи без workspace-tenancy атрибуции. Отсутствующее наблюдение = null с причиной, НЕ 0.

## 6. Policy gate и обязательные тесты до канонической отчётности
Считаются только acceptances, соответствующие действующим на t_accept deterministic gate + contact policy (corporate path, no_personal, suppression respected). Любая instrumentation lane, публикующая метрику, ОБЯЗАНА пройти независимый query/replay test-suite: повторы (dedup), границы 28d-окна, tenancy-изоляция, expiry evidence, first-accept timestamp, null-vs-0. До PASS этого suite число публикуется только как «proxy», не как accepted_evidence_backed_leads_28d.

## 7. Proxy-дисциплина
Существующие dashboard accepted-счётчики (7/30d по contacted/replied/meeting/won на строках digest_candidates) остаются status proxy: не подписывать и не отчитывать их как accepted_evidence_backed_leads_28d до выполнения §6.

## 8. Cost-ratio (указатель)
cost_per_verified_accepted_lead — по SPEC 2.0 §6: подтверждённый incremental AI cost за явно указанный период / соответствующие уникальные evidence-backed accepted leads того же периода. cost или denominator неизвестны → null с причиной; нулевой denominator → undefined, НЕ «0 ₽ за лид»; неизвестный usage.total_tokens ≠ 0. На дату принятия: LLM-стоимость не возникала (0 реальных вызовов), baseline метрики = null (БД не читалась в re-spec фазе).

## Приёмка и границы решения
Принял: company (t_0a65e710), 02.10.2026. Решение операционное, не портфельное: имя канона PORTFOLIO.md не изменено; изменение самой формулы в будущем — только явным новым company-решением с тем же протоколом (конфликт-чек → определение → replay-тесты). Финансовый scope принятия: 0 RUB cash; instrumentation — будущая code lane (T3-тип по SPEC §9) c собственными gate-цепочками.
