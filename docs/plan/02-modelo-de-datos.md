# 02 — Modelo de datos (v2, convenciones OpenGravity)

Lo implementa **FND** completo en la migración Alembic inicial. Los bloques siguientes **no crean tablas nuevas** salvo que lo pidan en su handoff (ver protocolo §4).

## Convenciones

- Tablas en `snake_case` minúscula. Columnas en **camelCase** (nombre físico como primer argumento de `Column`). Atributos Python en `snake_case`.
- `id` es `String` con cuid2. `createdAt` y `updatedAt` son `DateTime` naive UTC (`server_default=func.now()`).
- Dinero: `Numeric(14,2)` en **USD** salvo que la columna diga lo contrario (`amountLocal`, cuentas en VES). Tasa: `Numeric(14,4)`.
- Enums con `SQLEnum(X, name="X")`. Todas las FK llevan índice.
- `CHECK` en BD para las invariantes baratas: billetera ≥ 0, montos > 0, `paidAmount ≤ amount`.

## Identidad

| Tabla | Columnas clave |
|---|---|
| `users` | `id`, `role` (`UserRole`: ADMIN/PRODUCTION/DELIVERY/CUSTOMER), `phone` (único, E.164), `email` (null), `passwordHash` (bcrypt), `fullName`, `isActive`, `lastLoginAt` |
| `refresh_tokens` | `id`, `userId`, `tokenHash` (único), `expiresAt`, `revokedAt`, `deviceLabel` |
| `device_tokens` | `id`, `userId`, `fcmToken` (único), `app` (`cliente`/`delivery`), `lastSeenAt` |

## Clientes

**`customers`** — los crea el registro de la app (siempre `CASH`, sin aprobación) o el admin (con o sin usuario).

| Columna | Tipo | Notas |
|---|---|---|
| `userId` | String null único | null = cliente sin app (lo maneja solo el admin). |
| `type` | `CustomerType` RETAIL/WHOLESALE | Detal o mayorista. Por defecto WHOLESALE al registrarse en la app. |
| `segment` | `CustomerSegment` null | HOTDOG, BODEGA, CAFE_RESTAURANT, EVENTS, OTHER. |
| `businessName`, `contactName`, `phone`, `idDocument` | String | `idDocument` = RIF o cédula (opcional). |
| `addressText`, `addressReference` | String | Dirección de entrega en texto. |
| `paymentMode` | `PaymentMode` CASH/CREDIT | **Default CASH.** Solo el admin lo cambia (con auditoría). |
| `creditLimit` | Numeric default 0 | Solo aplica en CREDIT. |
| `creditDays` | Integer default `credit.defaultDays` | |
| `walletBalance` | Numeric default 0, **CHECK ≥ 0** | Caché del ledger; solo lo escribe `ledger.py`. |
| `isBlocked`, `blockedReason` | | Bloqueado = no puede pedir. |
| `notes` | | |

## Catálogo

| Tabla | Columnas clave |
|---|---|
| `categories` | `name`, `sortOrder`, `isActive` |
| `products` | `categoryId`, `name`, `description`, `unitLabel` (“unidad”, “bolsa x10”), `price` (USD), `minQty` (int ≥1), `imageFileId`, `isPublished`, `isAvailable` (agotado hoy), `sortOrder` |
| `price_history` | `productId`, `oldPrice`, `newPrice`, `changedBy`, `batchId` (cambio masivo), `createdAt` |

## Pedidos

**`orders`**

| Columna | Tipo | Notas |
|---|---|---|
| `number` | Integer único (secuencia `order_number_seq`, empieza en 1001) | Visible: **#1042**. |
| `customerId`, `createdByUserId` | | |
| `channel` | `OrderChannel` APP/BACKOFFICE | |
| `status` | `OrderStatus` | AWAITING_PAYMENT, CONFIRMED, PREPARING, READY, OUT_FOR_DELIVERY, DELIVERED, CANCELLED. |
| `paymentMode` | `PaymentMode` | Copia del modo del cliente al crear. |
| `paymentStatus` | `OrderPaymentStatus` | UNPAID, PARTIALLY_PAID, PAID, ON_CREDIT, REFUNDED. |
| `fulfillmentType` | `FulfillmentType` ASAP/SCHEDULED | “Lo quiero hoy” o programado. |
| `dueAt` | DateTime UTC | ASAP: el momento de la confirmación. SCHEDULED: fecha y hora elegidas. **Clave de orden en cocina.** |
| `subtotal`, `deliveryFee`, `total` | Numeric | `total = subtotal + deliveryFee`. |
| `paidFromWallet` | Numeric default 0 | Neto cobrado de la billetera (cargos − reembolsos). |
| `roundingAdjustment` | Numeric default 0 | Diferencia ≤ tolerancia perdonada al confirmar (ver flujos §3.4). |
| `deliveryAddressText`, `deliveryAddressReference`, `contactPhone` | | Copias al crear. |
| `notes` | | |
| `assignedDriverId` | String null | Se llena al pasar a READY. |
| `idempotencyKey` | String(64) único null | |
| `expiresAt` | DateTime null | Solo en AWAITING_PAYMENT; vencido → auto-cancelación. |
| `confirmedAt`, `preparingAt`, `readyAt`, `outForDeliveryAt`, `deliveredAt`, `cancelledAt` | DateTime | |
| `cancelReason`, `cancelledByUserId` | | |

Índices: `(status, dueAt)`, `(customerId, createdAt)`, `(assignedDriverId, status)`.

| Tabla | Columnas clave |
|---|---|
| `order_items` | `orderId`, `productId`, `productName`, `unitLabel`, `unitPrice`, `qty`, `lineTotal` (copias del momento de la compra) |
| `order_events` | `orderId`, `fromStatus`, `toStatus`, `actorUserId` (null = sistema), `note`, `createdAt` |

## Pagos (modelo de OpenGravity adaptado)

**`payment_methods`** y **`bank_accounts`** — se copian de OpenGravity. Se agrega `bank_accounts.cashAccountId`, la cuenta del negocio donde entra el dinero. Son los “datos de pago” que ve el cliente.

**`payments`**

| Columna | Tipo | Notas |
|---|---|---|
| `idempotencyKey` | String(64) único | |
| `customerId` | | |
| `purpose` | `PaymentPurpose` ORDER/WALLET_TOPUP/MANUAL | MANUAL = abono que registra el admin. |
| `orderId` | null | Pedido al que el cliente destina el pago (prioridad al aplicar). |
| `paymentMethodId`, `bankAccountId` | | |
| `amountLocal`, `localCurrency` (USD/VES) | Numeric, String | Lo que el cliente pagó, en su moneda. |
| `bcvRateUsed` | Numeric(14,4) null | Tasa del día del pago (`paidOn`). Solo en VES. |
| `amountUsd` | Numeric | `amountLocal` en USD, o `round(amountLocal / bcvRateUsed, 2)` en VES. El admin puede corregirlo al aprobar. |
| `reference` | String | Número de referencia bancaria. |
| `paidOn` | Date | Fecha del pago según el cliente. |
| `senderName` | null | Titular que pagó (como OpenGravity). |
| `proofFileId` | null | Comprobante (`files`). |
| `status` | `PaymentStatus` | PENDING_REVIEW, IN_REVIEW, APPROVED, REJECTED, REVERSED. |
| `reviewingAdminId`, `inReviewAt` | | “Tomar” un pago para revisarlo. |
| `approvedBy`, `approvedAt`, `rejectionReason`, `reversedBy`, `reversedAt`, `reversalReason` | | |

Índice único **parcial**: `(paymentMethodId, reference)` donde `status IN ('PENDING_REVIEW','IN_REVIEW','APPROVED')`. Una referencia rechazada se puede volver a reportar.

## Billetera del cliente y cuentas por cobrar

**`wallet_movements`** — ledger **solo inserción**; lo escribe únicamente `services/ledger.py`.

| Columna | Notas |
|---|---|
| `customerId` | |
| `type` (`WalletMovementType`) | TOPUP_APPROVED (+), ORDER_CHARGE (−), RECEIVABLE_SETTLEMENT (−), ORDER_REFUND (+), PAYMENT_REVERSAL (−), ADJUSTMENT (±). |
| `amount` | Con signo; nunca 0. |
| `balanceAfter` | Saldo de la billetera tras el asiento. |
| `paymentId`, `orderId`, `receivableId` | Referencias según el tipo. |
| `createdByUserId` | null = sistema. |
| `note` | Obligatoria en ADJUSTMENT. |

**`receivables`** — cuentas por cobrar.

| Columna | Notas |
|---|---|
| `customerId` | |
| `source` (`ReceivableSource`) | ORDER (resto a crédito de un pedido), MANUAL (fiado de mostrador o cargo del admin), PAYMENT_REVERSAL (pago revertido sin saldo). |
| `orderId` | Único, null. |
| `description` | |
| `amount`, `paidAmount` | `CHECK 0 ≤ paidAmount ≤ amount`. |
| `status` (`ReceivableStatus`) | OPEN, PARTIAL, PAID, VOID. |
| `issuedAt`, `dueAt` | |
| `voidReason`, `voidedBy`, `voidedAt` | |

## Cuentas del negocio (reutiliza `wallets` de OpenGravity con otro nombre)

| Tabla | Columnas clave |
|---|---|
| `cash_accounts` | `name` (“Banesco Bs”, “Zelle”, “Efectivo USD”), `accountType`, `currency` USD/VES, `balance`, `isActive`, `displayOrder` |
| `cash_account_transactions` | `cashAccountId`, `transactionType` (INCOME/EXPENSE/ADJUSTMENT), `amount` (en la moneda de la cuenta), `balanceAfter`, `referenceType`/`referenceId` (`payment`), `customerId`, `customerName`, `approvedBy`, `notes`, `metadata` (`exchange_rate`, `amount_usd`, `amount_ves`) |

## Operación

| Tabla | Origen | Notas |
|---|---|---|
| `exchange_rates` | **OpenGravity, tal cual** | `date`, `baseCurrency`, `targetCurrency`, `rateType` (BCV/MANUAL), `value`, `sourceUrl`, `fetchedAt`. |
| `settings` | OpenGravity (clave–valor tipado + caché) | Claves abajo. |
| `audit_logs` | OpenGravity | Precio, crédito, aprobación/rechazo/reverso de pagos, ajustes, anulaciones, bloqueos. |
| `daily_closings` | OpenGravity (`closures`), métricas adaptadas | Una fila por día de Caracas; PDF. |
| `files` | Nuevo | `key`, `contentType`, `sizeBytes`, `purpose` (PRODUCT_IMAGE/PAYMENT_PROOF), `ownerUserId`. |

### Claves de `settings` (con su valor por defecto)

| Clave | Default | Uso |
|---|---|---|
| `business.name` | “Panadería” | Nombre visible en todas las superficies. |
| `business.phone` / `business.whatsapp` / `business.address` | vacío | |
| `orders.openingTime` / `orders.closingTime` | 06:00 / 19:00 | Ventana válida para `dueAt` de los programados. |
| `orders.minLeadMinutes` | 60 | Mínimo entre ahora y la hora programada. |
| `orders.maxDaysAhead` | 30 | Máximo de días para programar. |
| `orders.unpaidExpiryHours` | 24 | Vencimiento de AWAITING_PAYMENT (para programados: el menor entre esto y `dueAt − minLeadMinutes`). |
| `delivery.feeUsd` | 0.00 | Costo de envío. |
| `delivery.driverUserId` | null | El único motorizado. |
| `credit.defaultDays` | 7 | |
| `credit.blockOverdueDays` | 7 | Bloquea pedidos si hay deuda vencida hace más de N días. |
| `payments.roundingToleranceUsd` | 0.01 | Diferencia por redondeo Bs↔USD que se perdona. |
| `rates.manualOverride` | — | Lo maneja `exchange_rates` (tipo MANUAL), como en OpenGravity. |

## Invariantes (se prueban; ver [07-pruebas](07-pruebas.md))

1. **I-1** `customers.walletBalance = Σ wallet_movements.amount ≥ 0`, y cada `balanceAfter` es correcto en secuencia.
2. **I-2** `orders.paidFromWallet = −Σ(ORDER_CHARGE del pedido) − Σ(ORDER_REFUND del pedido)` (los cargos son negativos y los reembolsos positivos).
3. **I-3** `receivables.paidAmount = −Σ(RECEIVABLE_SETTLEMENT de esa CxC)`. Al anular (VOID), lo pagado se devuelve a la billetera con un `ORDER_REFUND` que referencia la CxC y `paidAmount` queda como dato histórico.
4. **I-4** Para todo pedido que no esté cancelado y haya pasado de AWAITING_PAYMENT: `total = paidFromWallet + amount de su CxC (si CREDIT) + roundingAdjustment`.
5. **I-5** Pedido CANCELLED: `paidFromWallet = 0` y su CxC en VOID.
6. **I-6** Conservación del dinero, por cliente: `walletBalance = Σ pagos aprobados − Σ reversos (lo debitado de billetera) + Σ ajustes (con signo) − Σ paidFromWallet (pedidos no cancelados) − Σ paidAmount (CxC no anuladas)`.
7. **I-7** `cash_accounts.balance = Σ cash_account_transactions.amount`.
8. **I-8** Un pedido solo es visible para cocina en CONFIRMED, PREPARING o READY.
