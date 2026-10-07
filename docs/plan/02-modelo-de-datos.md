# 02 — Modelo de datos (v2.3, convenciones OpenGravity)

FND implementa **todo** este modelo en la migración Alembic inicial. Los bloques siguientes no crean tablas; si una es indispensable, siguen el protocolo §4.

## Convenciones
- **Nombres:** tablas en `snake_case` minúscula; columnas en **camelCase** (nombre físico como primer argumento de `Column`); atributos Python en `snake_case`.
- **IDs y fechas:** `id` String (cuid2). `createdAt` y `updatedAt` `DateTime` naive UTC.
- **Dinero:** `Numeric(14,2)` en USD salvo que la columna indique otra moneda. Tasa: `Numeric(14,4)`.
- **Enums:** `SQLEnum(X, name="X")`.
- **Índices:** toda FK lleva índice.
- **Restricciones declaradas en los modelos** (`CheckConstraint`, `Index(..., postgresql_where=...)`, `Sequence`) **y** en la migración. Una prueba verifica que `alembic check` no propone cambios.
- **Nombres de restricciones estables** (`uq_…`, `ck_…`): el handler de `IntegrityError` mapea cada nombre a un `code` del catálogo de 03 §7.

## Identidad
| Tabla | Columnas clave |
|---|---|
| `users` | `role` (`UserRole`: ADMIN, PRODUCTION, DELIVERY, CUSTOMER), `phone` (`uq_users_phone` → `PHONE_TAKEN`, E.164), `email` (null), `passwordHash` (bcrypt), `fullName`, `isActive`, `mustChangePassword`, `lastLoginAt` |
| `refresh_tokens` | `userId`, `tokenHash` (único), `expiresAt`, `revokedAt`, `rotatedAt`, `replacedById`, `deviceLabel` (gracia de rotación de 60 s, 08) |
| `idempotency_records` | `scope` (p. ej. `admin.payout`), `key`, `requestHash`, `responseJson`, `createdAt`; único `(scope, key)`. Para operaciones de admin sin tabla propia con llave (cargos, ajustes, devoluciones). |
| `device_tokens` | `userId`, `app` (`cliente`/`delivery`/`admin-web`), `fcmToken` (único, null), `webPushSubscription` (JSON, null), `lastSeenAt` |

## Clientes — `customers`
| Columna | Notas |
|---|---|
| `userId` | null = cliente sin app; único. |
| `type` | `CustomerType` RETAIL / WHOLESALE. Por defecto WHOLESALE al registrarse. |
| `segment` | `CustomerSegment` null: HOTDOG, BODEGA, CAFE_RESTAURANT, EVENTS, OTHER. |
| `businessName`, `contactName`, `phone`, `idDocument` | |
| `addressText`, `addressReference` | |
| `paymentMode` | `PaymentMode` CASH / CREDIT. Default **CASH**. |
| `creditLimit` | Numeric ≥ 0, default 0. |
| `creditDays` | int, default `credit.defaultDays`. |
| `walletBalance` | Numeric default 0. **`ck_customers_wallet_nonneg`**: ≥ 0. Solo lo escribe el ledger. |
| `isBlocked`, `blockedReason`, `notes`, `deletedAt` | `deletedAt`: cuenta eliminada por el cliente (anonimizada). |

## Catálogo
| Tabla | Columnas clave |
|---|---|
| `categories` | `name`, `sortOrder`, `isActive` |
| `products` | `categoryId`, `name`, `description`, `unitLabel`, `price` (> 0), `minQty` (≥ 1), `imageFileId`, `isPublished`, `isAvailable`, `sortOrder` |
| `price_history` | `productId`, `oldPrice`, `newPrice`, `changedBy`, `batchId`, `createdAt` |

## Pedidos
**`orders`**

| Columna | Notas |
|---|---|
| `number` | Integer único, secuencia `order_number_seq` desde 1001. |
| `customerId`, `createdByUserId` | |
| `channel` | APP / BACKOFFICE. |
| `status` | `OrderStatus`: AWAITING_PAYMENT, CONFIRMED, PREPARING, READY, OUT_FOR_DELIVERY, DELIVERED, CANCELLED. |
| `paymentMode` | Copia del modo del cliente al crear. |
| `paymentStatus` | `OrderPaymentStatus`: UNPAID, PARTIALLY_PAID, PAID, ON_CREDIT, REFUNDED (03 §3.5). |
| `fulfillmentType` | ASAP / SCHEDULED. |
| `dueAt` | UTC; clave de orden en cocina. |
| `subtotal`, `deliveryFee`, `total` | |
| `paidFromWallet` | Default 0. |
| `roundingAdjustment` | Default 0. |
| `deliveryAddressText`, `deliveryAddressReference`, `contactPhone`, `notes` | |
| `assignedDriverId` | Null. |
| `idempotencyKey` | `uq_orders_customer_idem` (`customerId`, `idempotencyKey`). |
| `requestHash` | sha256 del cuerpo, para detectar `IDEMPOTENCY_CONFLICT`. |
| `expiresAt` | |
| `confirmedAt`, `preparingAt`, `readyAt`, `outForDeliveryAt`, `deliveredAt`, `cancelledAt` | |
| `cancelReason`, `cancelledByUserId` | |

Índices: `(status, dueAt)`, `(customerId, createdAt)`, `(assignedDriverId, status)`, `(status, expiresAt)`.

| Tabla | Columnas clave |
|---|---|
| `order_items` | `orderId`, `productId`, `productName`, `unitLabel`, `unitPrice`, `qty`, `lineTotal` |
| `order_events` | `orderId`, `fromStatus`, `toStatus`, `actorUserId` (null = sistema), `note`, `createdAt` |

**Quién escribe qué en `orders`** (igual que en 08):
- **B3** (`MoneyService` y `ledger`): `paidFromWallet`, `roundingAdjustment`, `paymentStatus`, **`expiresAt`** y la CxC.
- **B2:** `status`, `*At`, `dueAt`, `assignedDriverId`, `order_events`, eventos y push. `confirm_paid` (B2, invocado por B3) limpia `expiresAt`.

## Pagos
**`payment_methods`** y **`bank_accounts`**: modelos de OpenGravity, con `bank_accounts.cashAccountId` (FK) agregado.

**`payments`** (base de estados reutilizada + columnas propias de la panadería)

| Columna | Notas |
|---|---|
| `customerId`, `createdByUserId` | |
| `idempotencyKey`, `requestHash` | `uq_payments_customer_idem` (`customerId`, `idempotencyKey`). |
| `purpose` | ORDER / WALLET_TOPUP / MANUAL. |
| `orderId` | null. |
| `paymentMethodId`, `bankAccountId` | |
| `amountLocal` | > 0. |
| `localCurrency` | USD / VES. |
| `bcvRateUsed` | Numeric(14,4) null. |
| `amountUsd` | > 0. |
| `reference`, `paidOn`, `senderName`, `proofFileId` | |
| `status` | PENDING_REVIEW, IN_REVIEW, APPROVED, REJECTED, REVERSED. |
| `reviewingAdminId`, `inReviewAt`, `approvedBy`, `approvedAt`, `rejectionReason`, `reversedBy`, `reversedAt`, `reversalReason` | |
| `correctedFrom` | JSON null: valores originales si el admin corrigió el monto o la tasa. |

**`uq_payments_bank_account_reference_live`**: único `(bankAccountId, reference)` `WHERE status <> 'REJECTED' AND reference IS NOT NULL`. La transferencia la identifican la cuenta destino y la referencia; solo un rechazo libera la referencia.

Prohibido el borrado físico de pagos.

## Billetera del cliente y cuentas por cobrar
**`wallet_movements`** — **solo inserción**; la escribe únicamente `services/ledger.py`.

| type (`WalletMovementType`) | Signo | Referencias |
|---|---|---|
| TOPUP_APPROVED | + | `paymentId` |
| ORDER_CHARGE | − | `orderId` |
| ORDER_REFUND | + | `orderId` (sin `receivableId`) |
| RECEIVABLE_SETTLEMENT | − | `receivableId` |
| RECEIVABLE_REFUND | + | `receivableId` (+ `orderId` si es de pedido) |
| PAYMENT_REVERSAL | − | `paymentId` |
| WALLET_PAYOUT | − | `cashAccountTransactionId` |
| ADJUSTMENT | ± | `note` obligatoria |

Otras columnas:
- **`seq`** BigInteger: secuencia `wallet_movements_seq`, única. Es el **orden canónico** del ledger para invariantes, estado de cuenta y cursor; `id` (cuid2) y `createdAt` no sirven para ordenar.
- `amount` (≠ 0), `balanceAfter`, `createdByUserId`, `cashAccountTransactionId` (en WALLET_PAYOUT).
- `createdAt`, asignado en Python con `to_utc_naive(utcnow())`. **No** usar `server_default=func.now()`, que en Postgres repite la hora de inicio de la transacción.

**`receivables`**

| Columna | Notas |
|---|---|
| `customerId`, `source` | `source`: ORDER / MANUAL / PAYMENT_REVERSAL. |
| `orderId` | Único, null. |
| `description` | |
| `amount` | **≥ 0**; 0 solo en VOID. |
| `paidAmount` | `ck_receivables_paid_range`: `0 ≤ paidAmount ≤ amount`. |
| `forgivenAmount` | Default 0. |
| `status` | OPEN, PARTIAL, PAID, VOID. |
| `issuedAt`, `dueAt` | |
| `voidReason` | ORDER_CANCELLED, REDUCED, VOIDED, FORGIVEN. |
| `voidedBy`, `voidedAt`, `note` | |

## Cuentas del negocio (las `wallets` de OpenGravity, renombradas)
| Tabla | Columnas clave |
|---|---|
| `cash_accounts` | `name`, `accountType`, `currency` (USD/VES), `balance`, `isActive`, `displayOrder` |
| `cash_account_transactions` | **`seq`** (`cash_account_tx_seq`), `cashAccountId`, `transactionType` (INCOME/EXPENSE/ADJUSTMENT), **`amount` CON SIGNO** en la moneda de la cuenta (INCOME > 0, EXPENSE < 0, ADJUSTMENT ≠ 0), `balanceAfter`, `referenceType`/`referenceId` (`payment`, `payout`), `customerId`, `customerName`, `approvedBy`, `notes`, `metadata` (`exchange_rate`, `amount_usd`, `amount_ves`) |

Se cambia respecto de OpenGravity: allí el monto era siempre positivo y el signo salía del tipo. Aquí es con signo, `balance += amount`, con una CHECK por tipo.

## Operación
| Tabla | Origen | Notas |
|---|---|---|
| `exchange_rates` | OpenGravity (modelo) | `date`, `baseCurrency`, `targetCurrency`, `rateType` (BCV/MANUAL), `value`, `sourceUrl`, `fetchedAt`. La lógica de lectura se reescribe: `rate_for(d)`, ver 03 §0. |
| `app_settings` | Nuevo, inspirado en `ConfigService` de OpenGravity | Una fila por sección (`business`, `orders`, `delivery`, `credit`, `payments`, `app`) con JSON validado por Pydantic. Caché de 30 s. El `commit` lo hace quien llama, para auditar en la misma transacción. |
| `audit_logs` | OpenGravity | |
| `daily_closings` | OpenGravity `closures` | Métricas nuevas. |
| `files` | Nuevo | `key`, `contentType`, `sizeBytes`, `purpose` (PRODUCT_IMAGE/PAYMENT_PROOF), `ownerUserId`, `createdAt`. |

### Claves de configuración (sección.clave = default)
| Clave | Default |
|---|---|
| `business.name` | “Panadería” |
| `business.phone` · `business.whatsapp` · `business.address` | “” |
| `orders.openingTime` · `orders.closingTime` | “06:00” · “19:00” |
| `orders.minLeadMinutes` | 60 |
| `orders.maxDaysAhead` | 30 |
| `orders.unpaidExpiryHours` | 24 |
| `orders.minPayWindowMinutes` | 30 |
| `delivery.feeUsd` | 0.00 |
| `delivery.driverUserId` | null |
| `credit.defaultDays` | 7 |
| `credit.blockOverdueDays` | 7 |
| `payments.roundingToleranceUsd` | 0.01 |
| `app.minVersionCliente` · `app.minVersionDelivery` | 1 · 1 (versionCode) |

## Invariantes
FND las copia **literalmente** en `api/tests/helpers.py::assert_money_invariants(session, tol)`. Cada consulta debe devolver **0 filas**.

`spec/money_model.py::check_invariants` implementa las mismas fórmulas. Excepciones: I-7 (el modelo no tiene cuentas del negocio) e I-8 (es una prueba de esquema/HTTP de FND y E12, no una consulta).

```sql
-- I-1a saldo guardado = suma del ledger, nunca negativo
SELECT c.id FROM customers c LEFT JOIN wallet_movements m ON m."customerId" = c.id
GROUP BY c.id, c."walletBalance"
HAVING c."walletBalance" <> COALESCE(SUM(m.amount),0) OR c."walletBalance" < 0;
-- I-1b balanceAfter correlativo por seq
SELECT id FROM (SELECT m.id, m."balanceAfter",
   SUM(m.amount) OVER (PARTITION BY m."customerId" ORDER BY m.seq) AS run FROM wallet_movements m) t
WHERE "balanceAfter" <> run OR run < 0;
-- I-2 paidFromWallet = −Σ(ORDER_CHARGE + ORDER_REFUND)
SELECT o.id FROM orders o LEFT JOIN wallet_movements m
  ON m."orderId" = o.id AND m.type IN ('ORDER_CHARGE','ORDER_REFUND')
GROUP BY o.id, o."paidFromWallet" HAVING o."paidFromWallet" <> -COALESCE(SUM(m.amount),0);
-- I-3 CxC viva: paidAmount = −Σ(RECEIVABLE_SETTLEMENT + RECEIVABLE_REFUND) y amount > 0
SELECT r.id FROM receivables r LEFT JOIN wallet_movements m
  ON m."receivableId" = r.id AND m.type IN ('RECEIVABLE_SETTLEMENT','RECEIVABLE_REFUND')
WHERE r.status <> 'VOID'
GROUP BY r.id, r."paidAmount", r.amount
HAVING r."paidAmount" <> -COALESCE(SUM(m.amount),0) OR r.amount <= 0;
-- I-4 pedido confirmado o posterior: total cubierto exactamente
SELECT o.id FROM orders o LEFT JOIN receivables r ON r."orderId" = o.id
WHERE o.status NOT IN ('AWAITING_PAYMENT','CANCELLED')
  AND (o.total <> o."paidFromWallet" + o."roundingAdjustment"
        + CASE WHEN r.id IS NULL THEN 0
               WHEN r.status = 'VOID' THEN r."forgivenAmount"
               ELSE r.amount + r."forgivenAmount" END
       OR o."roundingAdjustment" < 0 OR o."roundingAdjustment" > :tol);
-- I-5 pedido cancelado: nada cobrado y CxC anulada
SELECT o.id FROM orders o LEFT JOIN receivables r ON r."orderId" = o.id
WHERE o.status = 'CANCELLED' AND (o."paidFromWallet" <> 0 OR (r.id IS NOT NULL AND r.status <> 'VOID'));
-- I-6 conservación por cliente
SELECT c.id FROM customers c
WHERE c."walletBalance" <>
  COALESCE((SELECT SUM(amount) FROM wallet_movements m WHERE m."customerId" = c.id
            AND m.type IN ('TOPUP_APPROVED','PAYMENT_REVERSAL','ADJUSTMENT','WALLET_PAYOUT')),0)
  - COALESCE((SELECT SUM("paidFromWallet") FROM orders o WHERE o."customerId" = c.id AND o.status <> 'CANCELLED'),0)
  - COALESCE((SELECT SUM("paidAmount") FROM receivables r WHERE r."customerId" = c.id AND r.status <> 'VOID'),0);
-- I-7 cuentas del negocio (monto con signo) y balanceAfter por seq
SELECT a.id FROM cash_accounts a LEFT JOIN cash_account_transactions t ON t."cashAccountId" = a.id
GROUP BY a.id, a.balance HAVING a.balance <> COALESCE(SUM(t.amount),0);
SELECT id FROM (SELECT t.id, t."balanceAfter",
   SUM(t.amount) OVER (PARTITION BY t."cashAccountId" ORDER BY t.seq) AS run FROM cash_account_transactions t) x
WHERE "balanceAfter" <> run;
-- I-9 paymentStatus de pedidos a crédito
SELECT o.id FROM orders o JOIN receivables r ON r."orderId" = o.id
WHERE o.status <> 'CANCELLED'
  AND o."paymentStatus" <> CASE WHEN r.status IN ('OPEN','PARTIAL') THEN 'ON_CREDIT' ELSE 'PAID' END;
```
**I-8 (no es SQL):** cocina y delivery solo ven CONFIRMED, PREPARING o READY, y sus esquemas no tienen campos de dinero. FND lo prueba sobre el OpenAPI (`KitchenCard`, `DeliveryCard`, `OrderEventData`).
