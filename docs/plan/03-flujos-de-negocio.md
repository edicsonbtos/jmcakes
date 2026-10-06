# 03 — Flujos de negocio (v2)

Reglas exactas para B2 (pedidos) y B3 (dinero). Cada flujo con dinero se ejecuta **en una sola transacción**, con el cliente bloqueado (`SELECT … FOR UPDATE` sobre `customers`), y escribe **solo** a través de `services/ledger.py`. El modelo ejecutable `spec/money_model.py` implementa estas mismas reglas y sus pruebas (`spec/test_money_model.py`) son la referencia de aceptación (ver [07-pruebas](07-pruebas.md)).

Tolerancia `TOL = settings.payments.roundingToleranceUsd` (0.01).

---

## 1. Registro

1. El cliente se registra en la app con: nombre, nombre del negocio (opcional), tipo de negocio (perros calientes, bodega, cafetería/restaurante, eventos, otro), teléfono, cédula/RIF (opcional), dirección + referencia y contraseña.
2. Se crean `users` (CUSTOMER) y `customers` (`paymentMode = CASH`, `type = WHOLESALE`, billetera 0). **Sin aprobación**: entra directo y puede pedir.
3. El admin puede, en cualquier momento, habilitar **CREDIT** (límite y días), bloquear o editar. Todo queda en `audit_logs`. Push al cliente: “¡Tienes crédito disponible de $X!”.

## 2. Pedido: “Lo quiero hoy” o programado

Validaciones al crear (todas del servidor):
- Cliente activo y no bloqueado. Si es CREDIT, sin deuda vencida hace más de `credit.blockOverdueDays`. Si no: `422 OVERDUE_DEBT`.
- Líneas: producto publicado y disponible, `qty ≥ minQty`, precio **tomado del servidor**. Errores: `422 PRODUCT_UNAVAILABLE` o `422 BELOW_MIN_QTY`, con el producto en `meta`.
- `fulfillmentType = ASAP` → `dueAt = ahora` (se recalcula a la hora de confirmación).
- `fulfillmentType = SCHEDULED` → `dueAt` (fecha+hora de Caracas) con estas condiciones:
  - `≥ ahora + orders.minLeadMinutes`;
  - `≤ hoy + orders.maxDaysAhead`;
  - hora entre `openingTime` y `closingTime`.

  Si no cumple: `422 INVALID_SCHEDULE`, con el motivo legible.
- `total = Σ líneas + delivery.feeUsd`.
- `Idempotency-Key` obligatorio: si ya existe un pedido del mismo cliente con esa llave, se devuelve el mismo pedido (200), sin duplicar.

## 3. Cobro al crear el pedido

Sea `W` el saldo de la billetera y `T` el total.

### 3.1 Cliente CREDIT
```
usar      = min(W, T)
resto     = T − usar
disponible = creditLimit − deudaAbierta          # deudaAbierta = Σ(amount − paidAmount) de CxC OPEN/PARTIAL
si resto > disponible  → 422 CREDIT_LIMIT_EXCEEDED  meta{available, required: resto, walletBalance: W}
                         (nada se cobra; transacción revertida)
si usar > 0           → ledger.charge_order(usar)                 # ORDER_CHARGE
si resto > 0          → CxC(source=ORDER, amount=resto, dueAt = fin del día Caracas de (fecha de dueAt + creditDays))
status = CONFIRMED, paymentStatus = PAID si resto = 0, si no ON_CREDIT, confirmedAt = ahora
evento order.confirmed → cocina (sonido) · push al cliente “Pedido #N confirmado”
```

### 3.2 Cliente CASH (D-4, D-5)
```
usar = min(W, T)
si usar > 0 → ledger.charge_order(usar)          # “usa el saldo sin preguntar”
falta = T − usar
si falta ≤ TOL:
     roundingAdjustment = falta; status = CONFIRMED; paymentStatus = PAID   → cocina
si no:
     status = AWAITING_PAYMENT; paymentStatus = PARTIALLY_PAID si usar > 0, si no UNPAID
     expiresAt = ahora + unpaidExpiryHours   (programado: min(eso, dueAt − minLeadMinutes))
     la respuesta incluye: amountDue = falta (USD), amountDueVes = falta × tasa BCV de hoy (redondeado a 2),
     tasa usada y métodos de pago activos con sus cuentas (datos para pagar)
```
La app muestra en la misma pantalla: “Usamos $X de tu billetera. Te falta pagar $Y (Bs Z)”, los datos de pago y el formulario (método/cuenta, monto, referencia, fecha, titular y foto del comprobante).

### 3.3 Reportar un pago (cliente)
Propósitos: `ORDER` (paga el faltante de un pedido) o `WALLET_TOPUP` (recarga).
1. Si es `ORDER`: el pedido es del cliente y está en AWAITING_PAYMENT.
2. VES: `bcvRateUsed = tasa de paidOn` (`ExchangeRateService.get_rate_at_date`, lógica de OpenGravity) y `amountUsd = round(amountLocal / bcvRateUsed, 2)`. USD: `amountUsd = amountLocal`.
3. Referencia única entre pagos vivos: si se repite, `409 DUPLICATE_REFERENCE`.
4. `status = PENDING_REVIEW`. El pedido muestra “Pago en revisión”. Evento `payment.reported` → admin (contador y sonido).
5. **No se mueve dinero** hasta que el admin apruebe.

### 3.4 Aprobar un pago (admin) — corazón del sistema
```
lock payment FOR UPDATE; exigir status ∈ {PENDING_REVIEW, IN_REVIEW}   (si no → 409 PAYMENT_NOT_REVIEWABLE)
aplicar correcciones del admin (amountUsd o bcvRateUsed) → audit_logs
lock customer FOR UPDATE
ledger.record_payment_approved(payment):
     wallet  + amountUsd                                   (TOPUP_APPROVED)
     cash_account(bank_account.cashAccountId) INCOME en su moneda
         (si la cuenta es VES: amountLocal tal cual — regla de OpenGravity; si es USD: amountUsd)
status = APPROVED, approvedBy, approvedAt
settle(customer, prioridad = payment.orderId)
push al cliente: “Pago aprobado: +$X” (+ “Tu pedido #N entró a producción” si se confirmó)
```

### 3.5 `settle(customer, prioridad)` — uso automático de la billetera
Con el cliente bloqueado:
```
obligaciones, en este orden:
  1. el pedido prioridad, si está AWAITING_PAYMENT
  2. los demás pedidos AWAITING_PAYMENT del cliente, por createdAt ASC
  3. CxC OPEN/PARTIAL por dueAt ASC, issuedAt ASC
para cada obligación, mientras W > 0:
  pedido:   falta = total − paidFromWallet − roundingAdjustment
            cobrar = min(W, falta) → ORDER_CHARGE
            si falta − cobrar ≤ TOL → roundingAdjustment += (falta − cobrar); confirmar pedido (→ CONFIRMED, cocina)
            si no → paymentStatus = PARTIALLY_PAID (sigue esperando el resto)
  CxC:      aplicar = min(W, amount − paidAmount) → RECEIVABLE_SETTLEMENT; status PAID o PARTIAL
```
`settle` corre después de: aprobar un pago, abono manual del admin, ajuste positivo, reembolso por cancelación o edición, y creación de una CxC manual.

**Al confirmar un pedido** que estaba en AWAITING_PAYMENT:
- `dueAt` de un ASAP se recalcula a la hora de confirmación, para que no aparezca “atrasado” en cocina.
- Si el pedido programado **ya pasó su hora**, igual entra a cocina, marcado **“Atrasado”**.

### 3.6 Rechazar un pago (admin)
Pasa a `REJECTED` con motivo obligatorio. No se mueve dinero. Push: “Pago rechazado: <motivo>”. El pedido sigue en AWAITING_PAYMENT y el cliente puede reportar otro pago hasta `expiresAt`.

### 3.7 Revertir un pago aprobado (admin, p. ej. transferencia devuelta)
```
lock customer
si W ≥ amountUsd → PAYMENT_REVERSAL(−amountUsd)
si no            → PAYMENT_REVERSAL(−W) y CxC(source=PAYMENT_REVERSAL, amount = amountUsd − W, dueAt = hoy)
cash_account EXPENSE espejo del INCOME; status = REVERSED; audit_logs
```
Los pedidos ya confirmados **no** se cancelan solos; el admin decide.

### 3.8 Cancelar un pedido
- **Cliente:** solo en AWAITING_PAYMENT o CONFIRMED (antes de PREPARING).
- **Admin:** en cualquier estado antes de DELIVERED, con motivo.
- **Sistema:** job de vencimiento (§3.10).

```
lock customer
reembolso = paidFromWallet            → ORDER_REFUND(+reembolso); paidFromWallet = 0
CxC del pedido: si paidAmount > 0 → ORDER_REFUND(+paidAmount, receivableId); status = VOID
roundingAdjustment = 0; status = CANCELLED; paymentStatus = REFUNDED si hubo reembolso
settle(customer)                      # el saldo devuelto paga otras obligaciones, como cualquier saldo
evento order.cancelled → cocina (si estaba visible) · push al cliente
```
Si hay pagos **en revisión** de ese pedido, siguen su curso: al aprobarse, el dinero entra a la billetera y paga otras obligaciones o queda a favor. Nunca se pierde dinero.

### 3.9 Editar un pedido (admin, antes de READY) — solo reducir (faltante en cocina)
- Se pueden reducir cantidades o quitar líneas. Se recalculan `subtotal` y `total`.
- Lo cobrado de más se devuelve en este orden:
  1. Pedido CREDIT: primero se reduce el `amount` de la CxC (sin bajar de su `paidAmount`).
  2. El exceso que quede se devuelve con `ORDER_REFUND` y se reduce `paidFromWallet`.
- Luego corre `settle`. Todo queda en `order_events` y `audit_logs`.

### 3.10 Jobs
| Job | Hora (CCS) | Qué hace | Idempotencia |
|---|---|---|---|
| `bcv_sync` | 06:00 | `ExchangeRateService.sync_daily_rate()` (OpenGravity) | upsert por fecha |
| `unpaid_auto_cancel` | cada 10 min | Cancela pedidos AWAITING_PAYMENT con `expiresAt < ahora` **y sin pagos en revisión** (§3.8, actor = sistema). | Revisa el estado bajo bloqueo. |
| `daily_closing` | 23:50 | Métricas del día y PDF (`closures` de OpenGravity) | upsert por fecha |

## 4. Producción (cocina)

- Ve solo los pedidos **CONFIRMED, PREPARING y READY**, sin montos.
- **Hoy:** pedidos con `fecha Caracas(dueAt) ≤ hoy`. Columnas **Nuevos · Preparando · Listos**, ordenadas por `dueAt`. Cada tarjeta muestra:
  - la **hora** grande;
  - el chip **“Para ya”** (ASAP) o **“Programado 3:00 pm”**;
  - **“Atrasado”** si `dueAt < ahora`.
- **Programados:** pedidos confirmados con fecha futura, agrupados por día con la **fecha en grande** (“JUEVES 9 OCT”) y la hora en cada tarjeta. Se pueden empezar antes.
- **Total a producir:** por fecha, suma de cantidades por producto.
- Llegada de un pedido (`order.confirmed`): sonido repetido y tarjeta resaltada hasta tocarla.
- Transiciones: CONFIRMED → PREPARING (opcional) y → READY. Al pasar a READY se asigna a `delivery.driverUserId` y sale un push al motorizado. Si no hay motorizado configurado, queda READY sin asignar y el admin ve una alerta.

## 5. Delivery
- Lista **Por salir** (READY asignados), ordenada por `dueAt` y con la hora visible.
- Lista **En camino** y contador de “entregados hoy”.
- Tarjeta: #N, cliente/negocio, dirección + referencia, teléfono (Llamar / WhatsApp), productos y hora programada.
- Acciones:
  - **En camino:** individual o varios a la vez → push al cliente.
  - **Entregado:** con confirmación → push al cliente.
- Sin montos a cobrar: todo está pagado o a crédito.

## 6. Dashboard (día de Caracas)
| Indicador | Definición |
|---|---|
| Ingresos del día | Pagos APPROVED con `approvedAt` en el día: total USD, desglose por método y por cuenta (con su monto en Bs). |
| Ventas del día | Σ `total` de pedidos con `confirmedAt` en el día (excluye cancelados). |
| Pedidos por estado | En vivo (SSE). |
| Pagos por verificar | Cantidad y Σ `amountUsd` en PENDING_REVIEW/IN_REVIEW. |
| CxC | Total abierto, detal vs mayorista, vigente vs vencida, antigüedad 0–7 / 8–15 / 16–30 / +30, top deudores. |
| Saldo a favor de clientes | Σ `walletBalance` (dinero de clientes en custodia). |
| Productos más vendidos | Hoy / 7 / 30 días. |
| Cierre diario | `daily_closings` + PDF (patrón OpenGravity), consultable por fecha. |

## 7. Catálogo de errores (`code` → texto para el usuario)
`INVALID_CREDENTIALS`, `CUSTOMER_BLOCKED`, `OVERDUE_DEBT`, `CREDIT_LIMIT_EXCEEDED`, `PRODUCT_UNAVAILABLE`, `BELOW_MIN_QTY`, `INVALID_SCHEDULE`, `INVALID_TRANSITION`, `ORDER_NOT_CANCELLABLE`, `DUPLICATE_REFERENCE`, `PAYMENT_NOT_REVIEWABLE`, `RATE_UNAVAILABLE`, `IDEMPOTENCY_CONFLICT` (misma llave con otro contenido), `NOT_FOUND`, `FORBIDDEN`. El texto en español lo define el backend y el cliente lo muestra tal cual.
