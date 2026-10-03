# 03 — Flujos de negocio

Reglas exactas que deben implementar los bloques B2 (pedidos) y B3 (finanzas). Lo marcado con **[C-n]** depende de la pregunta *n* del [cuestionario](../CUESTIONARIO.md); se implementa con el valor por defecto indicado hasta que se responda.

## 1. Registro y aprobación de clientes

1. El cliente descarga la app, se registra con: nombre, nombre del negocio, teléfono, cédula/RIF, dirección y referencia, contraseña.
2. Queda en estado `PENDING`. **[C-3]** Por defecto requiere aprobación del admin.
3. El admin, en la web, ve la bandeja “Clientes por aprobar”, revisa, y al aprobar define:
   - tipo (`WHOLESALE` por defecto),
   - **modo de cobro**: `CASH` (contado, por defecto para nuevos) o `CREDIT`,
   - si es crédito: límite y días de crédito.
4. El cliente recibe push “¡Tu cuenta fue aprobada!” y ya puede pedir.

El admin también puede crear clientes **sin app** (detal o mayorista) para llevar sus cuentas por cobrar desde el backoffice.

## 2. Máquina de estados del pedido

```
                ┌──────────────────── cancelar (admin / cliente) ────────────────────┐
                │                                                                     ▼
 [CASH] AWAITING_PAYMENT ──pago aprobado──▶ CONFIRMED ──▶ PREPARING ──▶ READY ──▶ OUT_FOR_DELIVERY ──▶ DELIVERED
 [CREDIT] ───────────────── chequeo de crédito OK ──▶ CONFIRMED                                         CANCELLED
```

| Transición | Quién | Efectos |
|---|---|---|
| crear → `AWAITING_PAYMENT` | Cliente CASH | Se le muestra el total y los datos para pagar. El pedido **no** llega a cocina todavía. **[C-4]** |
| crear → `CONFIRMED` | Cliente CREDIT con crédito disponible, o admin | Se crea la **cuenta por cobrar** (si CREDIT); se aplica billetera (FIFO). Evento SSE `order.new` a cocina + sonido. |
| `AWAITING_PAYMENT` → `CONFIRMED` | Sistema, al aprobar el pago del pedido | Igual que arriba. |
| `CONFIRMED` → `PREPARING` | Producción (opcional) | Push al cliente “Tu pedido está en preparación”. |
| `CONFIRMED`/`PREPARING` → `READY` | Producción | **Auto-asignación** a `settings.delivery.default_driver_id`. Push al motorizado “Nuevo pedido #1042 — Pedro Pérez — Av. …”. |
| `READY` → `OUT_FOR_DELIVERY` | Motorizado (“En camino”) | Push al cliente “Tu pedido va en camino”. |
| `OUT_FOR_DELIVERY` → `DELIVERED` | Motorizado (“Entregado”) | Push al cliente. Fecha de entrega fija el vencimiento de la factura **[C-7]**. |
| → `CANCELLED` | Cliente hasta `CONFIRMED` (antes de que cocina empiece); admin en cualquier estado previo a `DELIVERED` | Anula la cuenta por cobrar (`VOID`); lo ya aplicado desde la billetera **vuelve a la billetera** con un asiento `ADJUSTMENT`. Evento SSE `order.cancelled` a cocina. |

Reglas:
- Cada transición se valida en un único servicio `orders.transition(orderId, to, actor)` y se registra en `order_events`. Transición inválida → `409 INVALID_TRANSITION`.
- El motorizado no acepta ni rechaza: todo pedido `READY` es suyo.
- **Fecha de entrega [C-6]:** por defecto, pedidos creados antes de `orders.cutoff_time` son para hoy; después, para mañana. Cocina filtra por fecha.
- Pedido mínimo por producto (`min_qty`) y productos `is_available=false` se rechazan con error claro.
- Precios: se toman del servidor al crear (nunca del cliente) y se guardan como snapshot en `order_items`.

## 3. Billetera y cuentas por cobrar

Concepto acordado: el cliente **no** tiene billetera negativa. Tiene dos números:

- **Billetera** (saldo a favor, ≥ 0).
- **Deuda** (suma de cuentas por cobrar abiertas).

Cada vez que entra dinero a la billetera, el sistema **paga automáticamente** las deudas pendientes, de la más antigua a la más nueva (FIFO). Si sobra, queda como saldo a favor para el próximo pedido.

### Algoritmo `settle(customerId)` (B3) — corre dentro de una transacción

```
BEGIN
  SELECT * FROM customers WHERE id = :id FOR UPDATE        -- serializa por cliente
  saldo := customers.wallet_balance_cents
  FOR r IN receivables WHERE customer_id=:id AND status IN (OPEN, PARTIAL)
           ORDER BY issued_at ASC FOR UPDATE:
      EXIT WHEN saldo = 0
      aplicar := min(saldo, r.amount_cents - r.paid_cents)
      INSERT wallet_entries(type=APPLIED_TO_RECEIVABLE, amount=-aplicar, receivable_id=r.id, balance_after=saldo-aplicar)
      INSERT receivable_allocations(r.id, entry.id, aplicar)
      UPDATE receivables SET paid_cents += aplicar, status = PAID|PARTIAL
      saldo -= aplicar
  UPDATE customers SET wallet_balance_cents = saldo
COMMIT
```

Se llama:
1. al **aprobar un pago** (después de insertar `PAYMENT_IN`),
2. al **crear una cuenta por cobrar** (pedido a crédito confirmado o cargo manual),
3. al hacer un **ajuste manual** positivo.

### Chequeo de crédito al crear pedido (B3 expone, B2 consume)

```
deuda_abierta     = SUM(amount - paid) de receivables OPEN/PARTIAL
disponible        = credit_limit - deuda_abierta + wallet_balance
permitido si      total_pedido <= disponible
              y   no hay facturas vencidas hace más de settings.credit.block_if_overdue_days
              y   customer.is_active
```
Error: `422 CREDIT_LIMIT_EXCEEDED` con `details: { available_cents, required_cents }` para que la app muestre “Te faltan $X de crédito disponible. Recarga tu billetera.”

### Reporte de pagos desde la app

1. Cliente → “Recargar billetera” (crédito) o “Pagar pedido #1042” (contado).
2. Ingresa método, moneda, monto, referencia, fecha, y opcionalmente foto del comprobante.
3. Queda `PENDING`. **[C-5]** Por defecto **verificación manual** del admin (el admin confirma en su banco).
4. El admin aprueba (puede corregir monto/tasa) o rechaza con motivo.
5. Al aprobar: `PAYMENT_IN` a la billetera → `settle()` → si era pago de un pedido de contado y cubre el total, el pedido pasa a `CONFIRMED` y llega a cocina.
6. Push al cliente con el resultado.

Duplicados: `(method, reference)` es único; un segundo reporte con la misma referencia se rechaza con `409 DUPLICATE_REFERENCE`.

### Operaciones manuales del admin (backoffice)
- **Cargo manual** (p. ej. venta fiada en mostrador a un cliente detal): crea `receivable` `MANUAL` → `settle()`.
- **Abono manual** (cliente pagó en el local): crea `payment` ya `APPROVED` → `PAYMENT_IN` → `settle()`.
- **Ajuste** (corrección, positiva o negativa, con nota obligatoria). Negativo solo hasta dejar la billetera en 0.
- **Anular cuenta por cobrar** (con motivo): devuelve lo aplicado a la billetera.
- Todo queda en `audit_log`.

### Moneda **[C-1]**
Por defecto la moneda base es **USD**. Los pagos en bolívares se convierten con la tasa del día (`exchange_rates`) al aprobarse; el admin puede editar la tasa aplicada en ese pago antes de aprobar. La app muestra precios en USD y, debajo, el equivalente en Bs a la tasa del día.

## 4. Producción (cocina)

- Pantalla tipo tablero (kanban) para tablet: columnas **Nuevos · Preparando · Listos (hoy)**.
- Cada tarjeta: **#número**, **nombre del cliente / negocio**, hora, lista de productos con cantidades grandes, notas.
- Al llegar un pedido: alerta sonora repetida hasta que alguien toque la tarjeta, banner “Nueva orden — Pedro Pérez”.
- Botón principal grande: **Listo** (y opcional **Preparando**).
- Vista **“Total a producir”** por fecha: suma de cantidades por producto de todos los pedidos confirmados (útil para hornear en lote).
- Sin montos de dinero.
- Si se pierde la conexión SSE: reconexión automática + refresco completo; indicador visible “Sin conexión”.

## 5. Delivery (motorizado)

- Login una vez; sesión persistente.
- Lista **Mis pedidos**: pestañas **Por salir (READY)** y **En camino**; historial del día.
- Tarjeta: #número, cliente, **dirección + referencia**, teléfono (botón llamar / WhatsApp), items, **monto a cobrar** si es contado contra entrega **[C-4]**.
- Botones: **En camino** (puede marcar varios a la vez) y **Entregado** (con confirmación).
- Push con sonido por cada pedido nuevo asignado.
- Sin mapas ni rutas (botón opcional “Abrir en Google Maps” con la dirección en texto — costo cero).

## 6. Dashboard del administrador (día de Caracas)

| Indicador | Definición |
|---|---|
| **Ingresos del día** | Suma de pagos `APPROVED` con `reviewed_at` en el día, desglosado por método y moneda. |
| **Ventas del día** | Suma de `total_cents` de pedidos `CONFIRMED`+ creados en el día (excluye cancelados). |
| **Pedidos por estado** | Conteo en vivo (SSE). |
| **CxC total** | Deuda abierta total, separada en **detal** y **mayorista**, y en vigente / vencida. |
| **Top deudores** | Clientes con mayor deuda y antigüedad. |
| **Pagos por verificar** | Cantidad y monto pendiente. |
| **Productos más vendidos** | Hoy / 7 días / 30 días. |
| **Cierre del día** | Resumen imprimible/exportable (CSV). |
