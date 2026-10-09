# ROBOKASSA E2E STATUS
**Дата:** 2026-09-30  
**Карта:** t_f9b7859b  
**Статус:** Готов к тестовому платежу, ожидается подтверждение владельца

---

## 1. Статус доступа

| Компонент | Статус | Evidence |
|-----------|--------|----------|
| Код адаптера | ✅ Реализован | `apps/web/lib/paymentsRobokassa.ts` (493 строки) |
| Webhook route | ✅ Существует | `apps/web/app/api/billing/webhook/robokassa/route.ts` |
| Миграции БД | ✅ Применены | `20260804223000_robokassa_payment_integrity.sql`, `20260804225000_robokassa_refunds.sql` |
| Verify-скрипты | ✅ На месте | `verify-robokassa-site-criteria.mjs`, `verify-robokassa-billing.mjs` |
| Runbook | ✅ 215 строк, полный | `docs/robokassa-production-checklist.md` |
| Прод-сайт | ✅ Доступен | https://recruiter-radar.ru |

---

## 2. Готовность контура

### Реализовано в коде
- Платёжная форма: `PAYMENT_URL = auth.robokassa.ru/Merchant/Index.aspx`
- Подписи: MD5 / SHA-256 / SHA-384 / SHA-512
- Receipt НПД (СМЗ): формирование чека самозанятого
- Shp-параметры: `Shp_order_id`, `Shp_plan`
- Тестовый режим: `IsTest=1` при `ROBOKASSA_MODE=test`
- Webhook: `parseWebhook`, ожидание `ResultURL` (не доверяет browser-return в test-режиме)
- Синхронизация после возврата: `syncOrderAfterReturn`

### Требуется подтверждение владельца (без передачи значений)
- [ ] `ROBOKASSA_MODE=test` выставлен в prod-env
- [ ] Тест-магазин активен в кабинете Robokassa
- [ ] Робочеки СМЗ включены

---

## 3. Параметры тест-платежа

| Параметр | Значение |
|----------|----------|
| URL | https://recruiter-radar.ru/checkout?plan=pilot |
| Сумма | 990 ₽ |
| Период | 7 дней |
| Магазин | Тестовый (test password1/2) |
| Ожидаемый результат | Редирект на SuccessURL, webhook `OK{InvId}`, order→paid, чек СМЗ |

---

## 4. Что нужно от владельца (один запрос)

**Текст запроса (уже отправлен через owner_inbox):**

> Подтвердите, что в prod-env `ROBOKASSA_MODE=test` и тест-магазин активен в кабинете Robokassa — значения не присылайте.
>
> После подтверждения:
> 1. Открыть https://recruiter-radar.ru/checkout?plan=pilot
> 2. Нажать «Оплатить», пройти тестовую форму Robokassa (990 ₽)
> 3. Дождаться редиректа на SuccessURL
> 4. Сообщить флоту: email тест-аккаунта и примерное время оплаты
>
> Флот проверит: webhook получен, order→paid, доступ открыт, чек СМЗ сформирован.

---

## 5. После платежа — проверка e2e

- [ ] Webhook получен: `POST /api/billing/webhook/robokassa` → `OK{InvId}`
- [ ] Order status: `paid` в БД
- [ ] Доступ открыт: пользователь получил 7 дней
- [ ] Чек СМЗ: сформирован и отправлен
- [ ] Логи: нет ошибок в `payment_logs`

---

## 6. Риски и ограничения

| Риск | Митигейшн |
|------|-----------|
| Секреты не проверены флотом (policy) | Владелец подтверждает вручную |
| Тест-магазин не активен | Запрос владельцу перед платежом |
| Webhook не доходит | Проверить `ResultURL` в кабинете Robokassa |
| Чек СМЗ не формируется | Проверить `ROBOKASSA_RECEIPT_*` настройки |

---

## 7. История

- **2026-09-29:** Run 737 — автоблок по false-positive `.env.robokassa.example` (lexical classifier)
- **2026-09-30:** Unblock от company, курс скорректирован — секреты не читать, deliverable из evidence
- **2026-09-30:** ROBOKASSA_E2E_STATUS.md собран, owner_inbox-запрос отправлен

---

*Next: ожидание подтверждения владельца → тест-платёж → verify e2e*
