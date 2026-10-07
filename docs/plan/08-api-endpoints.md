# 08 — Contrato v1: endpoints, eventos, push e interfaces internas (v2.2)

FND declara **todas** estas operaciones, cada una en el archivo de router indicado, con:
- esquemas Pydantic (`ApiModel`, camelCase);
- roles en `openapi_extra={"x-roles": [...]}`;
- respuestas de error.

Lo no implementado responde `501 NOT_IMPLEMENTED`. El **inventario** del final es la lista exacta de operaciones; `tests/test_contract_inventory.py` lo compara con el OpenAPI.

**Convenciones**

- Prefijo `/api/v1`, salvo `/api/health`.
- Roles: **P** público · **C** cliente · **A** admin · **K** producción · **D** delivery.
- **Dinero** como string decimal; **Bs** (`*Ves`) como `string | null`, en `null` cuando no hay tasa.
- **Tasa:** siempre `Rate{date, value, rateType, isFallback} | null`. **Ningún endpoint de pedidos, catálogo ni billetera falla por falta de tasa**; los Bs quedan en null.
- **Fechas** ISO con `Z`.
- **Listas:** `?cursor=&limit=` → `{items, nextCursor}`.
- **Nombres:** los campos que corresponden a una columna de 02 usan su nombre en camelCase. Los derivados se listan en cada endpoint.

## FND — `auth.py`, `health.py`
| Ruta | Rol | Notas |
|---|---|---|
| `GET /api/health` | P | `{status, version, db}`. |
| `POST /auth/register` | P | `{fullName, businessName?, segment?, phone, idDocument?, addressText, addressReference?, password}` → `{accessToken, refreshToken, user, customer}`. Teléfono repetido → `409 PHONE_TAKEN`. |
| `POST /auth/login` | P | `{phone, password}`. Límite por IP y teléfono → `429 RATE_LIMITED`. |
| `POST /auth/refresh` | P | `{refreshToken}` → par nuevo. **Gracia de 60 s**: un token rotado hace menos de `REFRESH_GRACE_SECONDS` todavía emite un par nuevo, lo que cubre la concurrencia y las respuestas perdidas. Pasado ese margen, `401 UNAUTHENTICATED`. |
| `POST /auth/logout` | C A K D | |
| `GET /auth/me` | C A K D | `{user, customer?}` |
| `POST /auth/device-tokens` · `DELETE /auth/device-tokens/{token}` | C D A | `{app: cliente\|delivery\|admin-web, fcmToken?, webPushSubscription?}` (admin-web = Web Push VAPID) |
| `DELETE /auth/account` | C | Anonimiza y desactiva; conserva la contabilidad. |

## B1
| Ruta | Archivo | Rol | Notas |
|---|---|---|---|
| `GET /catalog` | `catalog.py` | C A | `{rate, categories[{id, name, products[{id, name, description, unitLabel, price, priceVes, minQty, isAvailable, imageUrl}]}]}` |
| `GET /admin/categories` · `POST /admin/categories` · `PATCH /admin/categories/{id}` | `catalog.py` | A | |
| `GET /admin/products` · `POST /admin/products` · `GET /admin/products/{id}` · `PATCH /admin/products/{id}` | `catalog.py` | A | Con `imageUrl`. |
| `POST /admin/products/bulk-price/preview` · `POST /admin/products/bulk-price/apply` | `catalog.py` | A | `{productIds?, categoryId?, mode: PERCENT\|AMOUNT, value, roundTo?}` → `{rows[{productId, name, oldPrice, newPrice}], previewToken}` · `apply {previewToken}`. Si el token venció o cambió el estado → `409 PRICE_PREVIEW_EXPIRED`. |
| `GET /admin/products/{id}/price-history` | `catalog.py` | A | |
| `POST /files` | `files.py` | C A | Multipart `{file, purpose}` → `{id, purpose, contentType, sizeBytes}`. Si no es válido → `422 FILE_INVALID`. PRODUCT_IMAGE solo A. |
| `GET /files/{id}/url` | `files.py` | C A | `{url, expiresAt}`. PAYMENT_PROOF: su dueño y A. |
| `GET /files/{id}/public` | `files.py` | P | Solo PRODUCT_IMAGE, ya convertida a WebP (máx. 800 px) y miniatura (`?size=thumb`, 320 px). URL estable `?v=<hash>` con `Cache-Control: public, max-age=31536000, immutable`. `imageUrl` del catálogo apunta aquí. |
| `GET /files/{id}/local` | `files.py` | P (firmada) | `?exp=&sig=` con `sig = HMAC(JWT_SECRET, id\|exp)` y TTL de 1 h; firma inválida o vencida → 403. Solo con `STORAGE_BACKEND=local`. Así `<img>` y Coil cargan sin Bearer. |
| `GET /me/profile` · `PATCH /me/profile` | `profile.py` | C | |
| `GET /admin/customers` · `POST /admin/customers` · `GET /admin/customers/{id}` · `PATCH /admin/customers/{id}` | `customers.py` | A | Filtros: `query`, `type`, `paymentMode`, `hasDebt`, `blocked`. Columnas `walletBalance`, `openDebt`, `overdueDebt` (de `FinanceQueries`). |
| `POST /admin/customers/{id}/credit` | `customers.py` | A | `{paymentMode, creditLimit, creditDays}` |
| `POST /admin/customers/{id}/block` · `POST /admin/customers/{id}/unblock` | `customers.py` | A | `block {reason}` |
| `GET /admin/users` · `POST /admin/users` · `PATCH /admin/users/{id}` · `POST /admin/users/{id}/reset-password` | `users.py` | A | `reset-password` también para CUSTOMER: contraseña temporal, revoca refresh, `mustChangePassword = true`. |
| `GET /settings/public` | `settings.py` | P | `{businessName, phone, whatsapp, address, openingTime, closingTime, minLeadMinutes, maxDaysAhead, deliveryFeeUsd, minPayWindowMinutes, minVersionCliente, minVersionDelivery}` |
| `GET /admin/settings` · `PATCH /admin/settings` | `settings.py` | A | Por secciones; si algo no es válido → `422 INVALID_SETTINGS`. |
| `GET /admin/audit` | `audit.py` | A | Filtros: `entity`, `entityId`, `actor`. |

## B2
| Ruta | Archivo | Rol | Notas |
|---|---|---|---|
| `POST /orders/quote` · `POST /admin/orders/quote` | `orders.py` | C · A | `{customerId (solo A), items[{productId, qty}], fulfillmentType, dueAt?}` → `{subtotal, deliveryFee, total, totalVes, rate, walletUsed, amountDue, amountDueVes, creditUsed, creditDueAt, creditAvailable, paymentMethods[]}`. Los campos `credit*` son null en CASH. |
| `POST /orders` · `POST /admin/orders` | `orders.py` | C · A | `Idempotency-Key`. `{customerId (solo A), items, fulfillmentType, dueAt?, notes?, deliveryAddressText?, deliveryAddressReference?}` → `OrderDetail` + `checkout{walletUsed, paymentMethods[]}`. |
| `GET /orders` · `GET /orders/{id}` | `orders.py` | C | Solo los propios → `OrderDetail`. |
| `POST /orders/{id}/cancel` | `orders.py` | C | Si ya estaba CANCELLED → 200 con `OrderDetail` (idempotente). |
| `GET /admin/orders` · `GET /admin/orders/{id}` | `orders.py` | A | Filtros: `status`, `date`, `customerId`, `channel`, `unassigned=true` → `AdminOrderDetail`. |
| `POST /admin/orders/{id}/cancel` · `POST /admin/orders/{id}/reduce` · `POST /admin/orders/{id}/transition` · `POST /admin/orders/{id}/assign-driver` | `orders.py` | A | `cancel {reason}` (idempotente) · `reduce {items[{orderItemId, qty}]}` (03 §3.9) · `transition {to}` · `assign-driver {driverUserId}`. |
| `GET /kitchen/board` | `kitchen.py` | K A | `{today: {new[], preparing[], ready[]}, scheduled[{date, orders[]}]}` de `KitchenCard`. |
| `POST /kitchen/orders/{id}/preparing` · `POST /kitchen/orders/{id}/ready` | `kitchen.py` | K A | |
| `GET /kitchen/production-totals` | `kitchen.py` | K A | `?date=` → `[{productId, name, unitLabel, qty}]` |
| `GET /delivery/orders` | `delivery.py` | D | `{ready[], outForDelivery[], deliveredTodayCount}` de `DeliveryCard` (asignados a mí o sin asignar). |
| `POST /delivery/orders/out-for-delivery` | `delivery.py` | D | `{orderIds[]}` → `{updated[], skipped[{orderId, reason: ALREADY_OUT\|NOT_READY\|CANCELLED\|ASSIGNED_TO_OTHER}]}` |
| `POST /delivery/orders/{id}/delivered` | `delivery.py` | D | Idempotente. |
| `POST /events/token` · `GET /events` | `events.py` | K A | SSE (§Eventos). |

**Esquemas** (derivados en *cursiva*)
- `KitchenCard` = `DeliveryCard` base, **sin dinero**:
  - campos: `{id, number, status, customerName, businessName, fulfillmentType, dueAt, *isLate*, assignedDriverId, items[{name, unitLabel, qty}], notes}`;
  - `DeliveryCard` agrega `contactPhone`, `deliveryAddressText` y `deliveryAddressReference`.
- `OrderDetail` (cliente):
  - identificación y estado: `{id, number, status, paymentMode, paymentStatus, fulfillmentType, dueAt, *isLate*, items[]}`;
  - montos: `{subtotal, deliveryFee, total, *totalVes*, paidFromWallet, roundingAdjustment, *amountDue*, *amountDueVes*, *rate*}`;
  - pago: `{expiresAt, *hasPaymentInReview*, *receivable{amount, paidAmount, forgivenAmount, status, dueAt}|null*}`;
  - entrega: `{deliveryAddressText, deliveryAddressReference, notes}`;
  - marcas de tiempo: `{createdAt, confirmedAt, preparingAt, readyAt, outForDeliveryAt, deliveredAt, cancelledAt, cancelReason}`.
- `amountDue` y `amountDueVes` valen **0** salvo en AWAITING_PAYMENT. Vienen de `MoneyService.amount_due`.
- `AdminOrderDetail` = `OrderDetail` + `{customerId, *customerName*, businessName, channel, assignedDriverId, contactPhone, createdByUserId, *events[]*, *payments[]*}`.

## B3
| Ruta | Archivo | Rol | Notas |
|---|---|---|---|
| `GET /rates/today` | `rates.py` | P | `Rate`, o `409 RATE_UNAVAILABLE`. |
| `GET /admin/rates` · `POST /admin/rates/manual` · `POST /admin/rates/sync` | `rates.py` | A | `manual {date, value}` |
| `GET /payment-methods` | `payment_methods.py` | C A | `[{id, name, type, currency, instructions, fields, accounts[{id, label, data, isDefault}]}]` (todas las cuentas activas). |
| `GET /admin/payment-methods` · `POST /admin/payment-methods` · `PATCH /admin/payment-methods/{id}` | `payment_methods.py` | A | El PATCH incluye `isActive` y `displayOrder` (no hay DELETE). |
| `GET /admin/bank-accounts` · `POST /admin/bank-accounts` · `PATCH /admin/bank-accounts/{id}` | `payment_methods.py` | A | Con `cashAccountId`. |
| `POST /payments` | `payments.py` | C | `Idempotency-Key`. `{purpose: ORDER\|WALLET_TOPUP, orderId?, paymentMethodId, bankAccountId, localCurrency, amountLocal, reference, paidOn, senderName?, proofFileId?}`. Si la cuenta no corresponde al método o la moneda → `422 PAYMENT_ACCOUNT_MISMATCH`. |
| `GET /payments` · `GET /payments/{id}` | `payments.py` | C | Propios. |
| `GET /admin/payments` · `GET /admin/payments/{id}` | `payments.py` | A | Filtros: `status`, `date`, `customerId`. Detalle con `*proofUrl*`, `order` y `customer`. |
| `GET /admin/payments/pending-count` | `payments.py` | A | `{count, totalUsd}` |
| `POST /admin/payments/{id}/take` · `.../approve` · `.../reject` · `.../reverse` | `payments.py` | A | `approve {amountLocal?, bcvRateUsed?, note?}` (03 §3.4) · `reject {reason}` · `reverse {reason}` |
| `GET /me/wallet` · `GET /me/wallet/movements` | `wallet.py` | C | `{walletBalance, *walletBalanceVes*, openDebt, *openDebtVes*, overdueDebt, *overdueDebtVes*, rate, paymentMode, creditLimit, creditAvailable, receivables[]}`. Movimientos ordenados por `seq`. |
| `POST /admin/customers/{id}/manual-payment` | `admin_money.py` | A | `Idempotency-Key`. `{orderId?, paymentMethodId, bankAccountId, localCurrency, amountLocal, paidOn, reference?, note?}` |
| `POST /admin/customers/{id}/charges` · `.../adjustments` · `.../payouts` | `admin_money.py` | A | **`Idempotency-Key`**. `charges {amount, description, dueDate}` · `adjustments {amount, note}` · `payouts {amount, cashAccountId, note}` |
| `GET /admin/customers/{id}/statement` | `admin_money.py` | A | `?from&to&format=json\|csv` |
| `GET /admin/receivables` · `GET /admin/receivables/aging` · `POST /admin/receivables/{id}/void` · `POST /admin/receivables/{id}/forgive` | `admin_money.py` | A | `{reason}` |
| `GET /admin/cash-accounts` · `POST /admin/cash-accounts` · `GET /admin/cash-accounts/{id}/transactions` | `cash_accounts.py` | A | |
| `GET /admin/dashboard/summary` · `GET /admin/dashboard/top-products` | `dashboard.py` | A | `summary?date=` incluye `readyUnassignedCount` (03 §6). |
| `GET /admin/closures` · `GET /admin/closures/{date}` · `GET /admin/closures/{date}/pdf` · `POST /admin/closures/{date}/run` | `closures.py` | A | |
| `GET /admin/export/{kind}` | `export.py` | A | `kind ∈ {payments, receivables, orders}`, `?from&to&format=csv` |

## Eventos SSE
- `POST /events/token` → `{token, expiresAt}` (60 s, un solo uso).
- `GET /events?token=&lastEventId=` (también acepta la cabecera `Last-Event-ID`).

**Formato exacto del stream**
```
id: <envelope.id>
event: <type>
data: <EventEnvelope JSON>

: hb                       ← heartbeat cada 20 s (comentario: sin id ni event)

event: reset               ← sin id; el cliente recarga todo
data: {}
```
`EventEnvelope{id: int, type, at, data}`. FND lo exporta en el OpenAPI junto con `OrderEventData` y `PaymentEventData`.

| type | Destino | Cuándo | data |
|---|---|---|---|
| `order.created` | A | Al crear. | `OrderEventData` |
| `order.confirmed` | K A | Al confirmar. | `OrderEventData` |
| `order.updated` | K* A | **En toda transición de estado**, en `reduce` y en `assign-driver`. | `OrderEventData` |
| `order.cancelled` | K* A | Al cancelar. | `OrderEventData` |
| `payment.reported` · `payment.updated` | A | | `PaymentEventData{paymentId, status, customerName, amountUsd}` |

- **K\*:** cocina solo recibe eventos de pedidos cuyo estado **anterior o nuevo** sea CONFIRMED, PREPARING o READY.
- `OrderEventData` = los campos de `KitchenCard`, sin dinero. W2 actualiza la tarjeta (upsert) con `data` y la quita si `status` sale de esos tres estados.
- `useEventStream` registra un listener por tipo y uno para `reset`.

## Push (FCM) — `data` con todos los valores como string
| `type` | Destinatario | Título / cuerpo | `data` |
|---|---|---|---|
| `ORDER_CONFIRMED` | cliente | “Tu pedido #N entró a producción” | `orderId` |
| `ORDER_OUT_FOR_DELIVERY` | cliente | “Tu pedido #N va en camino” | `orderId` |
| `ORDER_DELIVERED` | cliente | “Tu pedido #N fue entregado” | `orderId` |
| `ORDER_CANCELLED` | cliente | “Tu pedido #N fue cancelado: <motivo>” | `orderId` |
| `PAYMENT_APPROVED` | cliente | “Pago aprobado: +$X” (+ “te falta $Y, tienes hasta HH:MM” si aplica) | `paymentId`, `orderId?` |
| `PAYMENT_REJECTED` | cliente | “Pago rechazado: <motivo>. Tienes hasta HH:MM” | `paymentId`, `orderId?` |
| `CREDIT_ENABLED` | cliente | “Tienes crédito disponible de $X” | — |
| `PAYMENT_REPORTED` | admin (Web Push) | “Pago por verificar: $X de <cliente>” | `paymentId` |
| `READY_UNASSIGNED` | admin (Web Push) | “Pedido #N listo sin motorizado” | `orderId` |
| `DELIVERY_ASSIGNED` | motorizado | “Nuevo pedido #N para <cliente>” | `orderId` |

M navega según `type`. B1, B2 y B3 prueban el envío con `push_spy`.

## Interfaces internas
**Reglas**
- Los Protocol y DTO viven en módulos **congelados**: `services/interfaces.py` y `domain/<x>/interface.py`.
- Cada implementación vive en los archivos de su bloque y se expone por **fábrica**. La fábrica se resuelve **en tiempo de llamada**: `Depends(get_x)` en routers y `services.registry.get("x")` en servicios. Nunca se importa la instancia por valor.
- FND deja en `api/tests/conftest.py` las fixtures `event_spy`, `push_spy`, `orders_double`, `money_double` y `settings_cache_clear` (autouse). Cada una sustituye la fábrica por un doble inspeccionable durante la prueba.
- **Las pruebas de B1, B2 y B3 afirman sobre esos dobles o sobre su propia implementación, nunca sobre el comportamiento del stub por defecto.**

| Protocol | Fábrica (archivo del implementador) | Implementa | Consume | Stub de FND |
|---|---|---|---|---|
| `CatalogService.price_lines` | `domain/catalog/service.py` | B1 | B2 | Precio del producto. |
| `CustomersService.get_for_update / get_by_user` | `domain/customers/service.py` | FND (real) | B2 B3 | — |
| `SettingsService.get(section) / update(section, data)` (invalida la caché) | `domain/settings/service.py` | FND (real); B1 agrega validación sin cambiar la firma | B1 B2 B3 | — |
| `AuditService.log(...)` | `domain/audit/service.py` | FND (real); B1 agrega la consulta paginada | todos | — |
| `FileService.assert_owned / signed_get_url` | `domain/files/service.py` | B1 | B3 | Revisa dueño y propósito; URL local **firmada**. |
| `RateService.rate_for(d)` | `domain/exchange_rates/service.py` | FND (real) | B1 B2 B3 | — |
| `MoneyService.assert_can_order · checkout · quote · amount_due · on_order_cancelled · on_order_reduced` | `services/money.py` | B3 | B2 | Ver abajo. |
| `FinanceQueries.balances_for` | `domain/finance/queries.py` | B3 | B1 | `walletBalance` y deuda 0. |
| `OrdersService.confirm_paid · cancel_for_block` | `domain/orders/service.py` | B2 | B3 B1 | `confirm_paid` real mínimo (CONFIRMED, `confirmedAt`, `expiresAt = None`, `dueAt` ASAP, `order_events`, evento). `cancel_for_block` no-op. |
| `EventBus.publish_after_commit` | `services/events.py` | B2 | B1 B3 | Lista en memoria. |
| `PushSender.send_to_user` | `services/push.py` | B2 | B1 B3 | Log + lista. |

**Stub de `MoneyService`**, coherente con 03 para que las pruebas de B2 no cambien en G2:
- `assert_can_order`: `CUSTOMER_BLOCKED`.
- `checkout`:
  - CREDIT: CONFIRMED; `paymentStatus` es PAID si W ≥ T y ON_CREDIT si no; `CREDIT_LIMIT_EXCEEDED` si el resto supera `creditLimit`; sin asientos.
  - CASH: AWAITING_PAYMENT, `paymentStatus = UNPAID`, **`expiresAt` con la fórmula de 03 §3.2**.
  - `paymentMethods` leídos de la tabla.
- `quote`: lo mismo, sin escribir.
- `amount_due`: 0 si el pedido no está en AWAITING_PAYMENT; si está, `total − paidFromWallet − roundingAdjustment`, con Bs según `rate_for(hoy)` o null.
- `on_*`: no-op.

**Propiedad de columnas de `orders`**
- B3 (vía `MoneyService` y el ledger): `paidFromWallet`, `roundingAdjustment`, `paymentStatus`, **`expiresAt`** (lo calcula en `checkout` y lo extiende al rechazar o al aprobar un pago insuficiente) y la CxC.
- B2: `status`, `*At`, `dueAt`, `assignedDriverId`, `order_events`, eventos y push. `confirm_paid` limpia `expiresAt`, y el job solo la lee.

DTO congelados en `services/interfaces.py`:
- `PricedLine`;
- `CheckoutResult{status, paymentStatus, walletUsed, amountDue, amountDueVes, rate, expiresAt, creditUsed, creditDueAt, paymentMethods[]}`;
- `QuoteResult`;
- `DueResult{amountDue, amountDueVes, rate, expiresAt}`;
- `CustomerBalance`, `Rate`, `DomainEvent`.

## Inventario (método + ruta; `test_contract_inventory.py` lo compara con el OpenAPI)
```
GET /api/health
POST /api/v1/auth/register|login|refresh|logout · GET /api/v1/auth/me · POST /api/v1/auth/device-tokens · DELETE /api/v1/auth/device-tokens/{token} · DELETE /api/v1/auth/account
GET /api/v1/catalog
GET|POST /api/v1/admin/categories · PATCH /api/v1/admin/categories/{id}
GET|POST /api/v1/admin/products · GET|PATCH /api/v1/admin/products/{id} · POST /api/v1/admin/products/bulk-price/preview · POST /api/v1/admin/products/bulk-price/apply · GET /api/v1/admin/products/{id}/price-history
POST /api/v1/files · GET /api/v1/files/{id}/url · GET /api/v1/files/{id}/local · GET /api/v1/files/{id}/public
GET|PATCH /api/v1/me/profile
GET|POST /api/v1/admin/customers · GET|PATCH /api/v1/admin/customers/{id} · POST /api/v1/admin/customers/{id}/credit|block|unblock
GET|POST /api/v1/admin/users · PATCH /api/v1/admin/users/{id} · POST /api/v1/admin/users/{id}/reset-password
GET /api/v1/settings/public · GET|PATCH /api/v1/admin/settings · GET /api/v1/admin/audit
POST /api/v1/orders/quote · POST /api/v1/admin/orders/quote · POST /api/v1/orders · POST /api/v1/admin/orders
GET /api/v1/orders · GET /api/v1/orders/{id} · POST /api/v1/orders/{id}/cancel
GET /api/v1/admin/orders · GET /api/v1/admin/orders/{id} · POST /api/v1/admin/orders/{id}/cancel|reduce|transition|assign-driver
GET /api/v1/kitchen/board · POST /api/v1/kitchen/orders/{id}/preparing|ready · GET /api/v1/kitchen/production-totals
GET /api/v1/delivery/orders · POST /api/v1/delivery/orders/out-for-delivery · POST /api/v1/delivery/orders/{id}/delivered
POST /api/v1/events/token · GET /api/v1/events
GET /api/v1/rates/today · GET /api/v1/admin/rates · POST /api/v1/admin/rates/manual|sync
GET /api/v1/payment-methods · GET|POST /api/v1/admin/payment-methods · PATCH /api/v1/admin/payment-methods/{id} · GET|POST /api/v1/admin/bank-accounts · PATCH /api/v1/admin/bank-accounts/{id}
POST /api/v1/payments · GET /api/v1/payments · GET /api/v1/payments/{id}
GET /api/v1/admin/payments · GET /api/v1/admin/payments/pending-count · GET /api/v1/admin/payments/{id} · POST /api/v1/admin/payments/{id}/take|approve|reject|reverse
GET /api/v1/me/wallet · GET /api/v1/me/wallet/movements
POST /api/v1/admin/customers/{id}/manual-payment|charges|adjustments|payouts · GET /api/v1/admin/customers/{id}/statement
GET /api/v1/admin/receivables · GET /api/v1/admin/receivables/aging · POST /api/v1/admin/receivables/{id}/void|forgive
GET|POST /api/v1/admin/cash-accounts · GET /api/v1/admin/cash-accounts/{id}/transactions
GET /api/v1/admin/dashboard/summary · GET /api/v1/admin/dashboard/top-products
GET /api/v1/admin/closures · GET /api/v1/admin/closures/{date} · GET /api/v1/admin/closures/{date}/pdf · POST /api/v1/admin/closures/{date}/run
GET /api/v1/admin/export/{kind}
```
`a|b` sobre la misma ruta base significa una operación por variante. Total: **105 operaciones**. FND las cuenta con `export_openapi.py --count`.
