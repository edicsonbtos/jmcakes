# 03 — Flujos de negocio (v2.1, tras la auditoría 1)

Reglas exactas para B2 (pedidos) y B3 (dinero).
- Cada flujo con dinero corre en **una sola transacción**: cliente bloqueado (`SELECT … FOR UPDATE` sobre `customers`) y escritura **solo** a través de `services/ledger.py`.
- `spec/money_model.py` implementa estas mismas reglas. Sus pruebas (`spec/test_money_model.py`) son la referencia de aceptación; ver [07](07-pruebas.md).
- `TOL = payments.roundingToleranceUsd` (0.01). `PAY_WINDOW = orders.minPayWindowMinutes` (30).

---

## 0. Tasa del día — una sola función
`rate_for(d)`, de **solo lectura**, sin HTTP y sin `commit`:
1. La tasa **MANUAL** de la fecha `d`.
2. Si no hay, la tasa **BCV** de `d` (la carga el job `bcv_sync` desde DolarAPI oficial, la única fuente externa de OpenGravity).
3. Si no hay, la **más reciente con fecha ≤ d de cualquier tipo**, con `isFallback = true`.
4. Si no existe ninguna: `409 RATE_UNAVAILABLE`.

Se usa **igual** para mostrar Bs (`d` = hoy en Caracas) y para convertir un pago (`d = paidOn`). La sincronización con DolarAPI (`sync_daily_rate`) solo ocurre en el job y en `POST /admin/rates/sync`, cada uno con su propia sesión. Nunca dentro de una transacción de dinero.

**Prohibido** (defectos de OpenGravity que no se copian):
- usar 1.0 como tasa de respaldo;
- reconvertir en el ledger un monto que ya viene convertido;
- `get_rate_at_date` solo para BCV;
- el caché por instancia.

Los Bs mostrados (`priceVes`, `totalVes`, `amountDueVes`) se calculan en el servidor con `ROUND_HALF_UP` a 2 decimales y **no se guardan**: se recalculan en cada consulta.

## 1. Clientes: registro, crédito y bloqueo
1. **Registro libre** desde la app: `users` (CUSTOMER) más `customers` con `paymentMode = CASH`, `type = WHOLESALE` y billetera 0. Puede pedir de inmediato.
2. **El admin habilita CREDIT** (límite y días) o vuelve a CASH. Siempre con auditoría; al habilitar crédito, push al cliente.
   - El **cambio de modo no altera pedidos existentes**: `orders.paymentMode` es una copia.
   - Un pedido CASH que espera pago sigue esperando. Si el cliente lo quiere a crédito, lo cancela y lo vuelve a crear.
   - La deuda existente se mantiene.
3. **Bloquear:**
   - Cancela todos los pedidos AWAITING_PAYMENT del cliente (§3.8, actor = admin, motivo “Cliente bloqueado”).
   - Los pagos en revisión siguen su curso y su dinero entra a la billetera.
   - `settle` **nunca confirma pedidos** de un cliente bloqueado, aunque sí paga sus CxC.
   - Un cliente bloqueado no puede pedir: `CUSTOMER_BLOCKED`.

## 2. Pedido: “Lo quiero hoy” o programado
Validaciones al crear o cotizar, todas del servidor (`MoneyService.assert_can_order` y B2):
- **Bloqueado:** `CUSTOMER_BLOCKED`.
- **Deuda vencida, cualquier modo:** si hay alguna CxC OPEN/PARTIAL con `dueAt + credit.blockOverdueDays < ahora` → `422 OVERDUE_DEBT`.
- **Cliente CASH con cualquier CxC abierta** (por reverso de pago, cargo manual o crédito anterior) → `422 OPEN_DEBT` con `meta.debt`. Primero paga la deuda (recarga o abono): un cliente de contado no acumula deuda.
- **Líneas:** producto publicado y disponible, `qty ≥ minQty`, precio del servidor. Errores `PRODUCT_UNAVAILABLE` y `BELOW_MIN_QTY` (con el producto en `meta`). Sin líneas: `EMPTY_ORDER`.
- **Tipo de entrega:**
  - `fulfillmentType = ASAP` → `dueAt = ahora`; se recalcula a la hora de confirmación.
  - `SCHEDULED` → el cliente envía `dueAt` (fecha+hora de Caracas). Debe cumplir `≥ ahora + orders.minLeadMinutes`, `≤ hoy + orders.maxDaysAhead` y hora entre `openingTime` y `closingTime`. Si no: `422 INVALID_SCHEDULE` con el motivo legible.
- `total = Σ líneas + delivery.feeUsd`.
- **Idempotencia:** `Idempotency-Key` obligatorio, único por `(customerId, idempotencyKey)`.
  - La misma llave con el mismo contenido devuelve el mismo pedido (200).
  - Con otro contenido: `409 IDEMPOTENCY_CONFLICT`.
  - Ante un `IntegrityError` por carrera se relee el registro existente.

## 3. Dinero

### 3.1 Crear pedido — cliente CREDIT
```
usar = min(W, T);  resto = T − usar
disponible = creditLimit − deudaAbierta            # Σ(amount − paidAmount) de CxC OPEN/PARTIAL
resto > disponible → 422 CREDIT_LIMIT_EXCEEDED meta{available, required: resto, walletBalance: W}
usar > 0  → ORDER_CHARGE(−usar)
resto > 0 → CxC(source=ORDER, amount=resto, dueAt = fin del día Caracas de (fecha Caracas de dueAt + creditDays))
status = CONFIRMED; paymentStatus = PAID si resto = 0, si no ON_CREDIT
eventos order.created (admin) + order.confirmed (cocina) · push al cliente
```

### 3.2 Crear pedido — cliente CASH (D-4, D-5)
```
usar = min(W, T) → ORDER_CHARGE(−usar)                         # sin preguntar
falta = T − usar
falta ≤ TOL → roundingAdjustment = falta; CONFIRMED; PAID       # a cocina
si no      → AWAITING_PAYMENT; paymentStatus = PARTIALLY_PAID si usar > 0, si no UNPAID
             expiresAt = max(ahora + PAY_WINDOW, min(ahora + unpaidExpiryHours, dueAt − minLeadMinutes))
             evento order.created (admin)
```
`expiresAt` lo calcula B3 en `checkout`. Un ASAP siempre vence a `ahora + PAY_WINDOW`, porque `dueAt − minLead` ya pasó; `unpaidExpiryHours` solo pesa en programados lejanos.

Qué devuelve cada respuesta:
- **`checkout`** (al crear): `walletUsed` y `paymentMethods[]` con cuentas e **ids**.
- **`GET /orders/{id}`:** `paidFromWallet`, `amountDue`, `amountDueVes`, `rate` y `expiresAt`. Los métodos salen de `GET /payment-methods`.

La app muestra: “Usamos $X de tu billetera. Te falta pagar $Y (Bs Z) antes de las HH:MM”. Debajo, los datos para pagar y el formulario.

### 3.3 Reportar un pago (cliente)
Propósitos: `ORDER` (paga el faltante de un pedido) y `WALLET_TOPUP` (recarga).
1. `amountLocal > 0` (si no, `INVALID_AMOUNT`) y `paidOn ≤ hoy Caracas` (si no, `INVALID_PAID_ON`).
2. Coherencia de moneda: `localCurrency = payment_method.currency = cuenta del negocio de la bankAccount`.
3. Si es `ORDER`: **`SELECT … FOR UPDATE` del pedido**. El pedido debe ser del cliente y estar en AWAITING_PAYMENT; si no, `409 ORDER_NOT_PAYABLE`.
4. Conversión:
   - **VES:** `bcvRateUsed = rate_for(paidOn).value` y `amountUsd = round(amountLocal / bcvRateUsed, 2)`.
   - **USD:** `amountUsd = amountLocal`.
5. **Referencia única por cuenta destino** (`bankAccountId` + `reference`) entre pagos no rechazados: cubre PENDING_REVIEW, IN_REVIEW, APPROVED y **REVERSED**. Si se repite: `409 DUPLICATE_REFERENCE`.
6. Comprobante: `proofFileId` debe ser un archivo `PAYMENT_PROOF` del mismo usuario (`FileService.assert_owned`).
7. `status = PENDING_REVIEW`. El pedido muestra `hasPaymentInReview`. Evento `payment.reported` al admin.
8. **No se mueve dinero.** Idempotencia igual que en los pedidos.

### 3.4 Aprobar un pago (admin)
```
lock payment FOR UPDATE; status ∈ {PENDING_REVIEW, IN_REVIEW} si no 409 PAYMENT_NOT_REVIEWABLE
correcciones opcionales del admin: amountLocal (> 0, en la moneda del pago) y/o bcvRateUsed (> 0, solo VES)
   → amountUsd = round(amountLocal / bcvRateUsed, 2) si VES, amountUsd = amountLocal si USD
   → correctedFrom guarda {amountLocal, bcvRateUsed, amountUsd} originales; audit_logs
lock customer FOR UPDATE
ledger.record_payment_approved:
   wallet + amountUsd                                     (TOPUP_APPROVED)
   cash_account(bank_account.cashAccountId) INCOME:
       cuenta VES → +amountLocal tal cual (cuadra con el banco) · cuenta USD → +amountUsd
       metadata {exchange_rate, amount_usd, amount_ves}
status = APPROVED, approvedBy, approvedAt
settle(customer, prioridad = payment.orderId)
si payment.orderId sigue AWAITING_PAYMENT → expiresAt = max(expiresAt, ahora + PAY_WINDOW)
push PAYMENT_APPROVED: “Pago aprobado: +$X” (+ “Tu pedido #N entró a producción”, o “te falta $Y; tienes hasta HH:MM”)
```

### 3.5 `settle(customer, prioridad)`
Con el cliente bloqueado. El orden de las obligaciones es:
```
cliente CREDIT, o CASH sin deuda:                 cliente CASH con CxC abierta (reverso, fiado, crédito anterior):
1. el pedido prioridad (si AWAITING_PAYMENT)       1. CxC OPEN/PARTIAL por dueAt ASC, issuedAt ASC
2. otros AWAITING_PAYMENT, createdAt ASC           2. el pedido prioridad
3. CxC por dueAt ASC, issuedAt ASC                 3. otros AWAITING_PAYMENT
(los pedidos se omiten si el cliente está bloqueado, §1)
```
Un cliente de contado **salda su deuda antes** de que se confirme cualquier pedido suyo. Así no se premia un pago revertido.
Para cada obligación, mientras W > 0:
- **Pedido:**
  - `falta = total − paidFromWallet − roundingAdjustment` y `cobrar = min(W, falta)` → `ORDER_CHARGE`.
  - Si `falta − cobrar ≤ TOL` → `roundingAdjustment += resto` y se confirma: `OrdersService.confirm_paid`, que lleva el pedido a CONFIRMED, recalcula `dueAt` si es ASAP, limpia `expiresAt` y emite `order.confirmed`.
  - Si no → `PARTIALLY_PAID`.
- **CxC:**
  - `aplicar = min(W, amount − paidAmount)` → `RECEIVABLE_SETTLEMENT`; la CxC queda en PAID o PARTIAL.
  - Si la CxC es de un pedido y quedó PAID, el pedido pasa a `paymentStatus = PAID`. Vuelve a ON_CREDIT si la CxC se reabre.

`settle` corre después de:
- aprobar un pago o un abono manual;
- un ajuste positivo;
- cualquier reembolso (cancelación, reducción, anulación);
- crear una CxC manual.

Un programado que se confirma después de su hora entra a cocina marcado **“Atrasado”**.

### 3.6 Rechazar un pago
- `REJECTED` con motivo obligatorio. No mueve dinero.
- Si el pago era de un pedido AWAITING_PAYMENT: `expiresAt = max(expiresAt, ahora + PAY_WINDOW)`, para que el cliente tenga tiempo de reportar otro.
- Push: “Pago rechazado: <motivo>. Tienes hasta las HH:MM para reportar otro.”

### 3.7 Revertir un pago aprobado (transferencia devuelta o falsa)
```
lock customer
W ≥ amountUsd → PAYMENT_REVERSAL(−amountUsd)
si no         → PAYMENT_REVERSAL(−W) + CxC(source=PAYMENT_REVERSAL, amount = amountUsd − W, dueAt = ahora)
cash_account EXPENSE espejo del INCOME (mismo monto y moneda); status = REVERSED; audit_logs
```
La referencia queda bloqueada para siempre. Los pedidos ya confirmados **no** se cancelan solos; la deuda creada bloquea nuevos pedidos (§2: `OPEN_DEBT` u `OVERDUE_DEBT`).

### 3.8 Cancelar un pedido
- **Quién puede:**
  - El cliente, solo en AWAITING_PAYMENT o CONFIRMED.
  - El admin, en cualquier estado antes de DELIVERED, con motivo.
  - El sistema, por el job de vencimiento o al bloquear al cliente.
- Si no se puede: `409 ORDER_NOT_CANCELLABLE`.
```
lock order + customer
paidFromWallet > 0 → ORDER_REFUND(+paidFromWallet); paidFromWallet = 0
CxC del pedido (si no VOID): paidAmount > 0 → RECEIVABLE_REFUND(+paidAmount); status = VOID (voidReason ORDER_CANCELLED)
roundingAdjustment = 0; status = CANCELLED; paymentStatus = REFUNDED si hubo reembolso
settle(customer) · order.cancelled → cocina (si estaba visible) · push
```
Los pagos en revisión de ese pedido siguen su curso. Al aprobarse, el dinero entra a la billetera y paga otras obligaciones o queda a favor.

### 3.9 Reducir un pedido (admin, antes de READY, por faltante en cocina)
```
si su CxC tiene forgiven > 0 → 409 ORDER_NOT_REDUCIBLE
por línea: 0 ≤ qtyNueva ≤ qtyActual y al menos una línea con qty > 0; si no 422 ONLY_REDUCTION
nuevoTotal = Σ líneas + deliveryFee (el envío no se reduce; las líneas en 0 se conservan con qty 0)
cobrado = paidFromWallet + CxC.paidAmount + roundingAdjustment
devolver = max(0, cobrado − nuevoTotal)
CxC.amount = min(CxC.amount, max(CxC.paidAmount, nuevoTotal − paidFromWallet − roundingAdjustment))
de "devolver": primero RECEIVABLE_REFUND (baja paidAmount y amount de la CxC), luego ORDER_REFUND (baja paidFromWallet)
CxC.amount = 0 → VOID (voidReason REDUCED)
si sigue AWAITING_PAYMENT y total − paidFromWallet − roundingAdjustment ≤ TOL → confirmar
settle(customer, prioridad = pedido) · order_events + audit_logs · evento order.updated
```

### 3.10 Jobs
Todos con `safe_job`, sesión propia y zona `America/Caracas`.

| Job | Cuándo | Qué hace |
|---|---|---|
| `bcv_sync` | 06:00 | `sync_daily_rate()`: upsert de la fila BCV del día. |
| `unpaid_auto_cancel` | cada 10 min | Toma `orders` AWAITING_PAYMENT con `expiresAt < ahora` usando **`FOR UPDATE SKIP LOCKED`**. Cancela los que no tengan pagos PENDING_REVIEW o IN_REVIEW (§3.8, actor sistema). Idempotente. |
| `daily_closing` | **00:05**, para el **día anterior** | Métricas del día de Caracas (por `approvedAt` y `confirmedAt` en SQL) + PDF. Upsert por fecha. Se reprocesa con `POST /admin/closures/{date}/run`. |

### 3.11 Anular o condonar una CxC (admin)
- **Anular:** solo las CxC de source **MANUAL** o **PAYMENT_REVERSAL**. Las de un pedido se anulan cancelando el pedido (§3.8); si no, `409 RECEIVABLE_NOT_VOIDABLE`. Lo pagado vuelve con `RECEIVABLE_REFUND`; luego `VOID` (VOIDED) y `settle`.
- **Condonar** (cualquier source, OPEN o PARTIAL):
  - `forgivenAmount = amount − paidAmount` y `amount = paidAmount`;
  - queda PAID, o VOID (FORGIVEN) si no se había pagado nada;
  - no devuelve lo cobrado;
  - auditoría con motivo.

### 3.12 Devolver saldo a favor en dinero (admin)
- Validaciones: `0 < monto ≤ walletBalance`; si no, `PAYOUT_EXCEEDS_BALANCE` o `INVALID_AMOUNT`.
- Movimientos: `WALLET_PAYOUT(−monto)` y `cash_account EXPENSE` en la cuenta elegida. Si es VES: `monto × rate_for(hoy)`, con metadata.
- Auditoría.

### 3.13 Ajuste manual
- `ADJUSTMENT(±monto)`, con nota obligatoria.
- Un ajuste negativo solo procede hasta dejar la billetera en 0; si no, `ADJUSTMENT_EXCEEDS_BALANCE`.
- Un ajuste positivo dispara `settle`.

## 4. Producción (cocina)
- **Qué ve:** solo pedidos CONFIRMED, PREPARING y READY, **sin montos** (esquema propio).
- **Hoy:** pedidos con fecha Caracas de `dueAt` ≤ hoy, en Nuevos · Preparando · Listos, ordenados por `dueAt`. Cada tarjeta muestra la hora grande, el chip “Para ya” o “Programado 3:00 pm”, y “Atrasado” si `dueAt < ahora`.
- **Programados:** pedidos de fechas futuras, agrupados por día con la **fecha en grande**. Se pueden empezar antes.
- **Total a producir** por fecha.
- **Llegada** (`order.confirmed`): sonido repetido y la tarjeta resaltada hasta tocarla.
- **Listo:**
  - El pedido se asigna a `delivery.driverUserId` y sale un push al motorizado.
  - Si no hay motorizado configurado, queda READY con `assignedDriverId = null` y se emite el evento `order.updated` para que el admin vea la alerta.

## 5. Delivery (un solo motorizado)
- `GET /delivery/orders` devuelve los READY con `assignedDriverId = yo` **o null**. Al marcarlos “En camino”, se asignan a quien los saca.
- El admin puede reasignar: `POST /admin/orders/{id}/assign-driver`.
- **Idempotencia** ante la mala señal:
  - `delivered` sobre un pedido ya DELIVERED por el mismo motorizado → 200 con el pedido;
  - `out-for-delivery` ignora los que ya están en camino y responde `{updated[], skipped[]}`.
- Tarjeta: #N, cliente, dirección + referencia, teléfono, productos y hora programada. Sin montos.

## 6. Dashboard (día de Caracas, en SQL)
| Indicador | Definición |
|---|---|
| Ingresos del día | Pagos con status **APPROVED o REVERSED** y `approvedAt` en el día de Caracas, convertido a UTC naive. Un reverso posterior **no** cambia el ingreso del día ya cerrado. Total USD, desglose por método y por cuenta (Bs exactos en cuentas VES). |
| Reversos y devoluciones del día | Pagos REVERSED con `reversedAt` en el día, y `WALLET_PAYOUT` del día, en líneas propias. |
| Ventas del día | Σ `total` de pedidos con `confirmedAt` en el día, no cancelados. |
| Pedidos por estado | En vivo, incluido `readyUnassignedCount` (READY sin motorizado). |
| Pagos por verificar | Cantidad y Σ `amountUsd` en PENDING_REVIEW o IN_REVIEW (`GET /admin/payments/pending-count`). |
| CxC | Total abierto, detal vs mayorista, vigente vs vencida, antigüedad 0–7 / 8–15 / 16–30 / +30, top deudores. |
| Saldo a favor de clientes | Σ `walletBalance`. |
| Cuentas del negocio | Saldo de cada cuenta en su moneda, más el equivalente USD a `rate_for(día)`. |
| Productos más vendidos | Hoy / 7 / 30 días. |
| Cierre diario | `daily_closings` + PDF. |

## 7. Catálogo de errores
`code` → HTTP · texto para el usuario (en español de Venezuela; el cliente lo muestra tal cual).

| code | HTTP | Texto |
|---|---|---|
| `INVALID_CREDENTIALS` | 401 | Teléfono o contraseña incorrectos. |
| `FORBIDDEN` | 403 | No tienes permiso para esta acción. |
| `NOT_FOUND` | 404 | No encontramos lo que buscas. |
| `CUSTOMER_BLOCKED` | 403 | Tu cuenta está bloqueada. Escríbenos por WhatsApp. |
| `OVERDUE_DEBT` | 422 | Tienes una deuda vencida. Págala para hacer nuevos pedidos. |
| `OPEN_DEBT` | 422 | Tienes una deuda pendiente de $X. Págala para hacer nuevos pedidos. |
| `CREDIT_LIMIT_EXCEEDED` | 422 | Tu crédito disponible es $X y este pedido necesita $Y. Recarga tu billetera. |
| `EMPTY_ORDER` | 422 | Agrega al menos un producto. |
| `PRODUCT_UNAVAILABLE` | 422 | “<producto>” no está disponible ahora. |
| `BELOW_MIN_QTY` | 422 | “<producto>” se vende desde N unidades. |
| `INVALID_SCHEDULE` | 422 | Esa fecha u hora no está disponible: <motivo>. |
| `INVALID_TRANSITION` | 409 | El pedido ya cambió de estado. Actualiza la pantalla. |
| `ORDER_NOT_CANCELLABLE` | 409 | Este pedido ya no se puede cancelar. |
| `ONLY_REDUCTION` | 422 | Solo se puede reducir el pedido. |
| `ORDER_NOT_REDUCIBLE` | 409 | Este pedido tiene deuda condonada y no se puede modificar. |
| `ORDER_NOT_PAYABLE` | 409 | Este pedido ya no está esperando pago. |
| `DUPLICATE_REFERENCE` | 409 | Esa referencia ya fue reportada. |
| `INVALID_PAID_ON` | 422 | La fecha del pago no puede ser futura. |
| `INVALID_AMOUNT` | 422 | El monto debe ser mayor que cero. |
| `PAYMENT_NOT_REVIEWABLE` | 409 | Este pago ya fue revisado. |
| `PAYMENT_NOT_REVERSIBLE` | 409 | Solo se puede revertir un pago aprobado. |
| `ADJUSTMENT_EXCEEDS_BALANCE` | 422 | El ajuste supera el saldo de la billetera. |
| `PAYOUT_EXCEEDS_BALANCE` | 422 | La devolución supera el saldo a favor. |
| `RECEIVABLE_NOT_VOIDABLE` | 409 | Esta deuda no se puede anular; cancela el pedido o condónala. |
| `RATE_UNAVAILABLE` | 409 | No hay tasa del día. El administrador debe cargarla. |
| `IDEMPOTENCY_CONFLICT` | 409 | Esta solicitud ya se envió con otros datos. |
| `FILE_INVALID` | 422 | El archivo debe ser una imagen o PDF de hasta 5 MB. |
| `PAYMENT_ACCOUNT_MISMATCH` | 422 | La cuenta elegida no corresponde a ese método o moneda. |
| `PRICE_PREVIEW_EXPIRED` | 409 | La vista previa venció o los precios cambiaron. Genera una nueva. |
| `PHONE_TAKEN` | 409 | Ese teléfono ya está registrado. Inicia sesión. |
| `RATE_LIMITED` | 429 | Demasiados intentos. Espera un minuto. |
| `UNAUTHENTICATED` | 401 | Tu sesión expiró. Inicia sesión de nuevo. |
| `VALIDATION_ERROR` | 422 | Revisa los datos: <detalle>. |
| `INVALID_SETTINGS` | 422 | Configuración inválida: <detalle>. |
| `SERVICE_UNAVAILABLE` | 503 | Servicio no disponible. Intenta de nuevo. |
| `NOT_IMPLEMENTED` | 501 | Aún no disponible. |

El catálogo vive en `api/src/core/errors.py` (enum, HTTP y texto). Una prueba de la API verifica que contiene todos los códigos de `spec/money_model.py::ERROR_CODES`, y `spec` verifica que todos están en esta tabla.
