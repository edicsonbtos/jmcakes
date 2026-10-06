# B2 — API: pedidos, agenda, cocina, delivery, eventos y push

**Fase 1** · **Rama** `block/B2` · Endpoints: [08](../08-api-endpoints.md) §B2 · Reglas: [03](../03-flujos-de-negocio.md) §2, §3.8–3.10, §4, §5

## Objetivo
Que el pedido nazca en la app (“lo quiero hoy” o programado), llegue a cocina en tiempo real solo cuando esté pagado o a crédito, pase a “Listo”, se asigne solo al motorizado y se cierre como “Entregado”, con notificaciones en cada paso.

## Alcance
1. **Crear pedido** (`POST /orders` y `POST /admin/orders`), en una sola transacción:
   - **Idempotencia:** la misma `Idempotency-Key` del mismo cliente devuelve el mismo pedido. Con distinto contenido → `409 IDEMPOTENCY_CONFLICT`.
   - **Validación de agenda** (03 §2) con settings y `date_utils` de Caracas: ASAP o SCHEDULED, `minLeadMinutes`, `maxDaysAhead` y horario.
   - **Precios** con `CatalogService.price_lines`; `total = subtotal + delivery.feeUsd`.
   - **Cobro:** `MoneyService.assert_can_order` y luego `MoneyService.checkout` (B3). B2 **no calcula dinero**: usa el `CheckoutResult` (estado, `paymentStatus`, `walletUsed`, `amountDue`, `amountDueVes`, tasa).
   - **Respuesta:** `OrderDetail` + `checkout`, con métodos de pago (vía `payment_methods`) si hay monto por pagar.
2. **`POST /orders/quote`:** igual a crear pero sin escribir (rollback o cálculo puro vía `MoneyService.quote`).
3. **Máquina de estados**
   - `orders.transition()` con la tabla de 03, validada por rol, más `order_events`, marcas de tiempo y `409 INVALID_TRANSITION`.
   - **Implementar `OrdersService.confirm_paid`:** AWAITING_PAYMENT → CONFIRMED. Recalcula `dueAt` si es ASAP, limpia `expiresAt` y emite `order.confirmed`. Lo usa B3 al aprobar un pago.
4. **Cancelación** (cliente y admin): reglas de 03 §3.8, `MoneyService.on_order_cancelled`, evento y push.
5. **Reducción (admin):** solo reducir, antes de READY, con `MoneyService.on_order_reduced`.
6. **Job `unpaid_auto_cancel`**, cada 10 min con `_safe_job`:
   - cancela por vencimiento si no hay pagos en revisión;
   - es idempotente;
   - opera bajo bloqueo de fila.
7. **Cocina**
   - `GET /kitchen/board`: Hoy (fecha Caracas de `dueAt` ≤ hoy, dividido en Nuevos, Preparando y Listos) y Programados, agrupados por fecha. **Sin ningún campo de dinero** (un esquema propio, no el `OrderDetail`).
   - Las tarjetas llevan `isAsap`, `dueAt`, `isLate`, ítems, notas y cliente.
   - `preparing` y `ready`; al pasar a ready se auto-asigna a `delivery.driverUserId` y se envía push.
   - `production-totals` por fecha.
8. **Delivery**
   - `GET /delivery/orders`: solo los asignados al motorizado.
   - `out-for-delivery` (en lote) y `delivered`, cada uno con push al cliente.
9. **Eventos**
   - `EventBus` en memoria con `publish_after_commit`.
   - `POST /events/token` (60 s, un solo uso) y `GET /events` (SSE): filtrado por rol (cocina no recibe `payment.*`), heartbeat cada 20 s, `Last-Event-ID` con un buffer circular de los últimos 200 eventos.
10. **Push**
    - `PushSender` con dos adaptadores: FCM, vía `FCM_CREDENTIALS_JSON`, y Log, por defecto.
    - Borra los tokens inválidos.
    - Textos de push en español:
      - cocina: “Nueva orden #1042 — Perros El Gordo”;
      - motorizado: “Nuevo pedido #1042 para Perros El Gordo”;
      - cliente: “Tu pedido #1042 va en camino”.
11. Listados de admin con filtros, cursor y detalle con bitácora y pagos.

## No tocar
`services/ledger.py`, `services/money.py`, dominios de dinero (B3), catálogo y clientes (B1), `db_models.py`, `main.py`.

## Pruebas exigidas
- Todas las transiciones válidas e inválidas por rol.
- Agenda: límites, horario y cambio de día en Caracas (pedido a las 23:30 VET).
- Idempotencia, incluido el conflicto.
- Cocina:
  - nunca recibe montos (inspeccionar el JSON del tablero);
  - un pedido programado a +3 días aparece en Programados y, con el reloj simulado ese día, aparece en Hoy (E4).
- Auto-asignación.
- Job de auto-cancelación: E7, más idempotencia corriéndolo dos veces.
- SSE: recibe `order.confirmed` tras el commit y **no** lo recibe si hay rollback.
- Push con el adaptador falso.
- Con los stubs de B3, el flujo completo ASAP de crear → … → entregado.

## Definición de terminado
Protocolo §6. El handoff incluye la secuencia `curl` de un pedido completo.
