# B2 — API: pedidos, agenda, cocina, delivery, eventos y push

**Fase 1** · rama `block/B2` · BD `panaderia_test_b2` · [08](../08-api-endpoints.md) §B2 · reglas [03](../03-flujos-de-negocio.md) §1–§2, §3.8–§3.10, §4–§5

## Objetivo
El pedido nace en la app (“lo quiero hoy” o programado). Llega a cocina en tiempo real solo cuando está pagado o va a crédito, pasa a Listo, el motorizado lo saca y se cierra como Entregado, con eventos y push en cada paso.

## Alcance
1. **Crear y cotizar** (`/orders`, `/admin/orders`, `/orders/quote`, `/admin/orders/quote`):
   - Validación de agenda con `dueAt` (03 §2).
   - `CatalogService.price_lines`.
   - `MoneyService.assert_can_order` y luego `checkout` o `quote`. **B2 no calcula dinero.**
   - Idempotencia por cliente + `requestHash` (con relectura ante `IntegrityError`).
   - Evento `order.created` (A) y `order.confirmed` si el pedido nace confirmado.
2. **`OrderDetail`** con los campos de 08; `amountDue`, `amountDueVes`, `rate` y `expiresAt` vienen de `MoneyService.amount_due`.
3. **Máquina de estados:** `orders.transition()` con validación por rol, `order_events`, marcas de tiempo y `INVALID_TRANSITION`.
   - **Implementar `OrdersService.confirm_paid`:** completa el mínimo de FND, con recálculo de `dueAt` ASAP y push al cliente.
   - **Implementar `OrdersService.cancel_for_block`.**
4. **Cancelar** (cliente, admin y sistema): 03 §3.8, `MoneyService.on_order_cancelled`, `order.cancelled` y push.
5. **Reducir** (admin): 03 §3.9, vía `MoneyService.on_order_reduced`, y `order.updated`.
6. **Job `unpaid_auto_cancel`:** `FOR UPDATE SKIP LOCKED`. No cancela si hay pagos en revisión. Idempotente.
7. **Cocina:** `board` (Hoy y Programados, `KitchenCard` **sin dinero**), `preparing`, `ready`, `production-totals`.
   - Al pasar a READY: asignación a `delivery.driverUserId` (o null) y push al motorizado.
   - **No hay push a cocina:** se entera por SSE.
8. **Delivery:**
   - `GET /delivery/orders` incluye los asignados a mí **o sin asignar**.
   - `out-for-delivery` asigna a quien los saca y responde `{updated, skipped[{orderId, reason}]}` con razón `ALREADY_OUT`, `NOT_READY`, `CANCELLED` o `ASSIGNED_TO_OTHER`.
   - `cancel` sobre un pedido ya cancelado → 200 (idempotente).
   - `delivered` es idempotente.
   - Push al cliente.
   - `assign-driver` (admin).
9. **Eventos:**
   - `EventBus` en memoria con `publish_after_commit` (hook `after_commit`), el sobre `EventEnvelope` y el **formato exacto del stream** de 08.
   - `order.updated` se emite en **toda** transición, en `reduce` y en `assign-driver`. Cocina recibe solo lo que entra o sale de CONFIRMED, PREPARING o READY. `OrderEventData` = campos de `KitchenCard`.
   - `POST /events/token` (60 s, un solo uso).
   - `GET /events?token&lastEventId`, también con la cabecera `Last-Event-ID`.
   - Filtro por rol (K nunca recibe `payment.*`), heartbeat de 20 s y buffer de 200 eventos.
   - Evento `reset` si no se puede reanudar.
   - Cabeceras `no-cache` y `X-Accel-Buffering: no`.
10. **Push:** `PushSender` (FCM si hay `FCM_CREDENTIALS_JSON`; si no, Log). Limpia los tokens inválidos. Tipos, textos y claves de `data` según la tabla §Push de 08.
11. Listados de admin con cursor y detalle con bitácora.

## No tocar
`services/{ledger,money}.py`, los dominios de dinero, catálogo y clientes, `db_models.py`, `interface.py`, `main.py`, `jobs/runner.py`.

## Pruebas exigidas
Todas en `api/tests/b2/`, con los dobles de FND (`event_spy`, `push_spy`, `money_double`) cuando el comportamiento ajeno importe.
- Todas las transiciones válidas e inválidas por rol.
- Agenda: límites, horario, día de Caracas a las 23:30 y E4 con el reloj simulado.
- Idempotencia, incluido el conflicto.
- JSON de cocina y delivery **sin campos de dinero** (verificado sobre el esquema).
- READY sin motorizado → se configura → el motorizado lo ve y lo saca.
- Idempotencia de delivery.
- Job E7, incluida la carrera con un reporte de pago: dos sesiones; `SKIP LOCKED` respeta el pedido bloqueado.
- **SSE a nivel de `EventBus` y del generador** (sin stream HTTP infinito):
  - commit → evento, rollback → nada;
  - filtro por rol;
  - reanudación por `lastEventId`;
  - `reset`;
  - el **texto emitido** coincide con el formato de 08;
  - OUT_FOR_DELIVERY emite `order.updated` a cocina; un pedido AWAITING reducido no llega a cocina.
- Push con el adaptador falso.
- Flujo ASAP completo con los stubs de B3.
