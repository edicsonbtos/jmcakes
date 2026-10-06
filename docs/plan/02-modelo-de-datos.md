# 02 — Modelo de datos (v2.1, convenciones OpenGravity)

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
| `users` | `role` (`UserRole`: ADMIN, PRODUCTION, DELIVERY, CUSTOMER), `phone` (único, E.164), `email` (null), `passwordHash` (bcrypt), `fullName`, `isActive`, `lastLoginAt` |
| `refresh_tokens` | `userId`, `tokenHash` (único), `expiresAt`, `revokedAt`, `deviceLabel` |
| `device_tokens` | `userId`, `fcmToken` (único), `app` (`cliente`/`delivery`), `lastSeenAt` |

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

**Quién escribe qué en `orders`:**
- **B3** (`MoneyService` y `ledger`): `paidFromWallet`, `roundingAdjustment`, `paymentStatus` y la CxC.
- **B2:** todo lo demás (`status`, `*At`, `expiresAt`, `dueAt`, `assignedDriverId`, `order_events`), además de eventos y push.
- La confirmación por pago la ejecuta B2 (`OrdersService.confirm_paid`), invocada por B3.

## Pagos
**`payment_methods`** y **`bank_accounts`**: modelos de OpenGravity, con `bank_accounts.cashAccountId` (FK) agregado.

**`payments`** (en OpenGravity no existían `reference`, `paidOn`, método, cuenta ni reverso: es **código nuevo** sobre su base)

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

**`uq_payments_method_reference_live`**: único `(paymentMethodId, reference)` `WHERE status <> 'REJECTED'`. Solo un rechazo libera la referencia.

Prohibido el borrado físico de pagos: no se copia el `DELETE /payments/{id}` de OpenGravity.

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

Otras columnas: `amount` (≠ 0), `balanceAfter`, `createdByUserId`, `createdAt`.

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
| `cash_account_transactions` | `cashAccountId`, `transactionType` (INCOME/EXPENSE/ADJUSTMENT), **`amount` CON SIGNO** en la moneda de la cuenta (INCOME > 0, EXPENSE < 0, ADJUSTMENT ≠ 0), `balanceAfter`, `referenceType`/`referenceId` (`payment`, `payout`), `customerId`, `customerName`, `approvedBy`, `notes`, `metadata` (`exchange_rate`, `amount_usd`, `amount_ves`) |

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
FND las escribe tal cual en `api/tests/helpers.py::assert_money_invariants(session)`; `spec/money_model.py::check_invariants` usa las mismas fórmulas.

```sql
-- I-1 saldo = suma del ledger y nunca negativo (balanceAfter correlativo: verificado en Python ordenando por createdAt, id)
SELECT c.id FROM customers c LEFT JOIN wallet_movements m ON m."customerId" = c.id
GROUP BY c.id, c."walletBalance" HAVING c."walletBalance" <> COALESCE(SUM(m.amount),0) OR c."walletBalance" < 0;

-- I-2 paidFromWallet = −Σ(ORDER_CHARGE + ORDER_REFUND) del pedido (excluye reembolsos de CxC)
SELECT o.id FROM orders o LEFT JOIN wallet_movements m
  ON m."orderId" = o.id AND m.type IN ('ORDER_CHARGE','ORDER_REFUND')
GROUP BY o.id, o."paidFromWallet" HAVING o."paidFromWallet" <> -COALESCE(SUM(m.amount),0);

-- I-3 CxC viva: paidAmount = −Σ RECEIVABLE_SETTLEMENT − Σ RECEIVABLE_REFUND ; amount > 0
SELECT r.id FROM receivables r LEFT JOIN wallet_movements m
  ON m."receivableId" = r.id AND m.type IN ('RECEIVABLE_SETTLEMENT','RECEIVABLE_REFUND')
WHERE r.status <> 'VOID'
GROUP BY r.id, r."paidAmount", r.amount
HAVING r."paidAmount" <> -COALESCE(SUM(m.amount),0) OR r.amount <= 0;

-- I-4 pedido confirmado o posterior, no cancelado: total = paidFromWallet + (CxC.amount si no VOID) + CxC.forgivenAmount + roundingAdjustment ; roundingAdjustment ≤ tolerancia
-- I-5 pedido CANCELLED: paidFromWallet = 0 y su CxC VOID
-- I-6 por cliente: walletBalance = Σ(TOPUP_APPROVED + PAYMENT_REVERSAL + ADJUSTMENT + WALLET_PAYOUT)
--                                  − Σ paidFromWallet (pedidos no cancelados) − Σ paidAmount (CxC no VOID)
-- I-7 cash_accounts.balance = Σ cash_account_transactions.amount (con signo)
-- I-8 cocina solo ve CONFIRMED/PREPARING/READY y sus respuestas no tienen campos de dinero
-- I-9 pedido a crédito no cancelado: paymentStatus = ON_CREDIT si su CxC está OPEN/PARTIAL; si no, PAID
```
