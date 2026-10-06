# 08 — Contrato v1: endpoints, archivos, eventos e interfaces internas

FND declara **todos** estos endpoints, en el archivo de router indicado, con esquemas Pydantic (`ApiModel`, camelCase), roles y respuestas de error. Los cuerpos no implementados responden `501 NOT_IMPLEMENTED`. Así `contracts/openapi.json` está completo desde la Fase 0.

- Prefijo `/api/v1`, salvo `/api/health`.
- Roles: **P** público · **C** cliente · **A** admin · **K** producción (cocina) · **D** delivery.
- Dinero en string decimal. Fechas ISO con `Z`.
- Listas paginadas: `?cursor=&limit=` → `{items, nextCursor}`.
- Los campos de respuesta llevan el nombre de su columna en 02, en camelCase. Excepciones: los derivados `amountDue`, `amountDueVes`, `totalVes`, `priceVes`, `rate`, `imageUrl`, `hasPaymentInReview` e `isLate`.

## FND — `api/v1/auth.py`, `health.py`
| Ruta | Rol | Notas |
|---|---|---|
| `GET /api/health` | P | `{status, version, db}` (`SELECT 1`, timeout 5 s). |
| `POST /auth/register` | P | `{fullName, businessName?, segment?, phone, idDocument?, addressText, addressReference?, password}` → `{accessToken, refreshToken, user, customer}`. |
| `POST /auth/login` | P | `{phone, password}` → igual que register. Rate limit por IP + teléfono. |
| `POST /auth/refresh` | P | `{refreshToken}` → tokens nuevos (rotación). |
| `POST /auth/logout` | C A K D | Revoca el refresh. |
| `GET /auth/me` | C A K D | `{user, customer?}`. |
| `POST /auth/device-tokens` · `DELETE /auth/device-tokens/{token}` | C D | `{fcmToken, app}`. |
| `DELETE /auth/account` | C | Desactiva el usuario y anonimiza el perfil (`deletedAt`); conserva el registro contable. |

## B1
| Ruta | Archivo | Rol | Notas |
|---|---|---|---|
| `GET /catalog` | `catalog.py` | C A | `{rate: {date, value, rateType, isFallback} \| null, categories[{id, name, products[{id, name, description, unitLabel, price, priceVes \| null, minQty, isAvailable, imageUrl \| null}]}]}`. No falla si no hay tasa (`priceVes = null`). |
| `GET·POST /admin/categories` · `PATCH /admin/categories/{id}` | `catalog.py` | A | |
| `GET·POST /admin/products` · `GET·PATCH /admin/products/{id}` | `catalog.py` | A | Incluye `imageUrl`. |
| `POST /admin/products/bulk-price/preview` · `.../apply` | `catalog.py` | A | `{productIds?, categoryId?, mode: PERCENT\|AMOUNT, value, roundTo?}` → `{rows[{productId, name, oldPrice, newPrice}], previewToken}`. `apply` recibe `{previewToken}`. |
| `GET /admin/products/{id}/price-history` | `catalog.py` | A | |
| `POST /files` | `files.py` | C A | Multipart `{file, purpose}` (≤ 5 MB; jpeg/png/webp/pdf) → `{id, purpose, contentType, sizeBytes}`. Si no cumple: `422 FILE_INVALID`. PRODUCT_IMAGE solo A. |
| `GET /files/{id}/url` | `files.py` | C A | `{url, expiresAt}`. PRODUCT_IMAGE: C y A. PAYMENT_PROOF: su dueño y A. |
| `GET /files/{id}/local` | `files.py` | C A | Solo con `STORAGE_BACKEND=local`, con la misma autorización. |
| `GET·PATCH /me/profile` | `profile.py` | C | Dirección, referencia, contacto y segmento. No toca modo ni crédito. |
| `GET·POST /admin/customers` · `GET·PATCH /admin/customers/{id}` | `customers.py` | A | Filtros: `query`, `type`, `paymentMode`, `hasDebt`, `blocked`. Columnas `walletBalance`, `openDebt` y `overdueDebt` vía `FinanceQueries`. |
| `POST /admin/customers/{id}/credit` | `customers.py` | A | `{paymentMode, creditLimit, creditDays}`. |
| `POST /admin/customers/{id}/block` · `.../unblock` | `customers.py` | A | `block {reason}`: cancela los AWAITING vía `OrdersService.cancel_for_block`. |
| `GET·POST /admin/users` · `PATCH /admin/users/{id}` · `POST /admin/users/{id}/reset-password` | `users.py` | A | |
| `GET /settings/public` | `settings.py` | P | `{businessName, phone, whatsapp, address, openingTime, closingTime, minLeadMinutes, maxDaysAhead, deliveryFeeUsd, minPayWindowMinutes, minVersionCliente, minVersionDelivery}`. |
| `GET·PATCH /admin/settings` | `settings.py` | A | Por secciones: `business`, `orders`, `delivery`, `credit`, `payments`, `app`. |
| `GET /admin/audit` | `audit.py` | A | |

## B2
| Ruta | Archivo | Rol | Notas |
|---|---|---|---|
| `POST /orders/quote` · `POST /admin/orders/quote` | `orders.py` | C · A | `{customerId (solo A), items[{productId, qty}], fulfillmentType, dueAt?}` → `{subtotal, deliveryFee, total, totalVes, rate, walletUsed, amountDue, amountDueVes, creditAvailable?, paymentMethods[]}`, o el error de validación. Sin efectos. |
| `POST /orders` · `POST /admin/orders` | `orders.py` | C · A | `Idempotency-Key`. Cuerpo: `{customerId (solo A), items, fulfillmentType, dueAt?, notes?, deliveryAddressText?, deliveryAddressReference?}` → `OrderDetail`. |
| `GET /orders` · `GET /orders/{id}` | `orders.py` | C | Solo los propios. |
| `POST /orders/{id}/cancel` | `orders.py` | C | |
| `GET /admin/orders` · `GET /admin/orders/{id}` | `orders.py` | A | Filtros: `status`, `date` (fecha Caracas de `dueAt`), `customerId`, `channel`. El detalle incluye `events[]`, `payments[]` y `receivable`. |
| `POST /admin/orders/{id}/cancel` · `.../reduce` · `.../transition` · `.../assign-driver` | `orders.py` | A | `cancel {reason}` · `reduce {items[{orderItemId, qty}]}` · `transition {to}` · `assign-driver {driverUserId}`. |
| `GET /kitchen/board` | `kitchen.py` | K A | `{today: {new[], preparing[], ready[]}, scheduled[{date, orders[]}]}` con `KitchenCard{id, number, customerName, fulfillmentType, dueAt, isLate, status, items[{name, unitLabel, qty}], notes}`. **Sin dinero.** |
| `POST /kitchen/orders/{id}/preparing` · `.../ready` | `kitchen.py` | K A | |
| `GET /kitchen/production-totals?date=` | `kitchen.py` | K A | `[{productId, name, unitLabel, qty}]`. |
| `GET /delivery/orders` | `delivery.py` | D | `{ready[], outForDelivery[], deliveredTodayCount}`. Incluye `assignedDriverId = yo` **o null**. `DeliveryCard{id, number, customerName, businessName, contactPhone, deliveryAddressText, deliveryAddressReference, dueAt, fulfillmentType, items[]}`, sin dinero. |
| `POST /delivery/orders/out-for-delivery` | `delivery.py` | D | `{orderIds[]}` → `{updated[], skipped[]}` (idempotente). |
| `POST /delivery/orders/{id}/delivered` | `delivery.py` | D | Idempotente si ya está DELIVERED por el mismo motorizado. |
| `POST /events/token` · `GET /events?token=&lastEventId=` | `events.py` | K A | SSE. |

**`OrderDetail`** (cliente y admin): `id, number, status, paymentMode, paymentStatus, fulfillmentType, dueAt, isLate, items[], subtotal, deliveryFee, total, totalVes, paidFromWallet, roundingAdjustment, amountDue, amountDueVes, rate, expiresAt, hasPaymentInReview, deliveryAddressText, deliveryAddressReference, notes, createdAt, confirmedAt, readyAt, outForDeliveryAt, deliveredAt, cancelledAt, cancelReason`.
- `amountDue` y `amountDueVes` vienen de `MoneyService.amount_due`; no se calculan en B2.
- Al crear, la respuesta agrega `checkout{walletUsed, paymentMethods[]}`.

### Eventos SSE (FND exporta estos esquemas como componentes del OpenAPI)
`EventEnvelope{id: int, type, at, data}`:

| type | Destino | data |
|---|---|---|
| `order.created` | A | `OrderEventData` |
| `order.confirmed` · `order.updated` · `order.cancelled` | K A | `OrderEventData{orderId, number, status, fulfillmentType, dueAt, isLate, customerName}`, **sin montos** |
| `payment.reported` · `payment.updated` | A | `PaymentEventData{paymentId, status, customerName, amountUsd}` |
| `heartbeat` · `reset` | todos | `{}` |

## B3
| Ruta | Archivo | Rol | Notas |
|---|---|---|---|
| `GET /rates/today` | `rates.py` | P | `{date, value, rateType, isFallback}` o `409 RATE_UNAVAILABLE`. |
| `GET /admin/rates` · `POST /admin/rates/manual` · `POST /admin/rates/sync` | `rates.py` | A | `manual {date, value}`. |
| `GET /payment-methods` | `payment_methods.py` | C A | `[{id, name, type, currency, instructions, fields, accounts[{id, label, data, isDefault}]}]`: **todas** las cuentas activas, con `id`. |
| `GET·POST·PATCH /admin/payment-methods` · `/admin/bank-accounts` | `payment_methods.py` | A | `bank-accounts` incluye `cashAccountId`. |
| `POST /payments` | `payments.py` | C | `Idempotency-Key`. `{purpose: ORDER\|WALLET_TOPUP, orderId?, paymentMethodId, bankAccountId, localCurrency, amountLocal, reference, paidOn, senderName?, proofFileId?}`. |
| `GET /payments` · `GET /payments/{id}` | `payments.py` | C | Propios, con estado y `rejectionReason`. |
| `GET /admin/payments` · `GET /admin/payments/{id}` | `payments.py` | A | Filtros: `status`, `date`, `customerId`. El detalle incluye `proofUrl`, `order` y `customer`. |
| `GET /admin/payments/pending-count` | `payments.py` | A | `{count, totalUsd}`. |
| `POST /admin/payments/{id}/take` · `.../approve` · `.../reject` · `.../reverse` | `payments.py` | A | `approve {amountUsd?, bcvRateUsed?, note?}` · `reject {reason}` · `reverse {reason}`. |
| `GET /me/wallet` · `GET /me/wallet/movements` | `wallet.py` | C | `{walletBalance, openDebt, overdueDebt, paymentMode, creditLimit, creditAvailable, receivables[]}` y movimientos paginados. |
| `POST /admin/customers/{id}/manual-payment` | `admin_money.py` | A | `Idempotency-Key`. `{orderId?, paymentMethodId, bankAccountId, localCurrency, amountLocal, paidOn, reference?, note?}` → pago APPROVED (MANUAL) + `settle` con prioridad al pedido. |
| `POST /admin/customers/{id}/charges` | `admin_money.py` | A | `{amount, description, dueDate}` → CxC MANUAL. |
| `POST /admin/customers/{id}/adjustments` | `admin_money.py` | A | `{amount (±), note}`. |
| `POST /admin/customers/{id}/payouts` | `admin_money.py` | A | `{amount, cashAccountId, note}` (03 §3.12). |
| `GET /admin/customers/{id}/statement?from&to&format=json\|csv` | `admin_money.py` | A | |
| `GET /admin/receivables` · `GET /admin/receivables/aging` | `admin_money.py` | A | |
| `POST /admin/receivables/{id}/void` · `.../forgive` | `admin_money.py` | A | `{reason}` (03 §3.11). |
| `GET·POST /admin/cash-accounts` · `GET /admin/cash-accounts/{id}/transactions` | `cash_accounts.py` | A | |
| `GET /admin/dashboard/summary?date=` · `GET /admin/dashboard/top-products?range=` | `dashboard.py` | A | |
| `GET /admin/closures` · `GET /admin/closures/{date}` · `.../pdf` · `POST /admin/closures/{date}/run` | `closures.py` | A | |
| `GET /admin/export/{payments\|receivables\|orders}.csv?from&to` | `export.py` | A | |

## Interfaces internas

**Dónde vive cada pieza:**
- **Protocolos y DTO compartidos** están en módulos **congelados** de FND: `api/src/services/interfaces.py` y `api/src/domain/<x>/interface.py`.
- **Implementación:** cada bloque escribe la suya en sus propios archivos y la expone con una **fábrica**. Los consumidores solo importan la fábrica y el Protocol.
- **Stubs:** FND deja cada fábrica devolviendo un stub con el comportamiento indicado.

| Protocol (archivo congelado) | Fábrica (archivo del implementador) | Implementa | Consume | Stub de FND |
|---|---|---|---|---|
| `CatalogService.price_lines(session, lines) -> list[PricedLine]` | `domain/catalog/service.py::get_catalog_service` | B1 | B2 | Toma el precio del producto; valida que exista. |
| `CustomersService.get_for_update / get_by_user` | `domain/customers/service.py::get_customers_service` | FND (**real**, trivial) | B2 B3 | — |
| `FileService.assert_owned(session, file_id, user_id, purpose) -> FileDB` · `signed_get_url(file) -> str` | `domain/files/service.py::get_file_service` | B1 | B3 | Revisa dueño y propósito en la tabla; la URL es `/api/v1/files/{id}/local`. |
| `MoneyService.assert_can_order · checkout · quote · amount_due · on_order_cancelled · on_order_reduced` | `services/money.py::get_money_service` | B3 | B2 | `assert_can_order`: solo `isBlocked`. `checkout`: CREDIT confirma (PAID); CASH queda AWAITING (UNPAID) sin mover dinero; `paymentMethods` leídos de la tabla. `quote`: igual sin escribir. `amount_due`: `total − paidFromWallet − roundingAdjustment`, con Bs según `rate_for(hoy)` si existe. `on_*`: no-op. |
| `FinanceQueries.balances_for(session, ids) -> dict[str, CustomerBalance]` | `domain/finance/queries.py::get_finance_queries` | B3 | B1 | `walletBalance` de la fila; deuda 0. |
| `OrdersService.confirm_paid(session, order, actor_id)` · `cancel_for_block(session, customer_id, actor_id)` | `domain/orders/service.py::get_orders_service` | B2 | B3 B1 | `confirm_paid` **real mínimo**: CONFIRMED, `confirmedAt`, `expiresAt = None`, `dueAt = now` si es ASAP, `order_events` y `publish_after_commit(order.confirmed)`. `cancel_for_block`: no-op. |
| `RateService.rate_for(session, d) -> Rate` | `domain/exchange_rates/service.py::get_rate_service` | FND (**real**, 03 §0) | B1 B2 B3 | — |
| `EventBus.publish_after_commit(session, event)` | `services/events.py::get_event_bus` | B2 | B1 B3 | Lista en memoria inspeccionable. |
| `PushSender.send_to_user(session, user_id, title, body, data)` | `services/push.py::get_push_sender` | B2 | B1 B3 | Log + lista inspeccionable. |

Los DTO `PricedLine`, `CheckoutResult` (`status, paymentStatus, walletUsed, amountDue, amountDueVes, rate, paymentMethods[]`), `QuoteResult`, `DueResult`, `CustomerBalance`, `Rate` y `DomainEvent` viven en `services/interfaces.py`, que está congelado. Cambiarlos requiere una “Solicitud de cambio”.
