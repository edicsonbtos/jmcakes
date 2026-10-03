# B2 — API: pedidos, producción, delivery y notificaciones

**Fase:** 1 (paralelo) · **Esfuerzo:** L · **Rama:** `block/B2-pedidos`

## Objetivo
Implementar el corazón operativo: **el pedido nace en la app, llega a cocina en tiempo real, pasa a “Listo”, se asigna solo al motorizado y se cierra como “Entregado”**, con notificaciones en cada paso.

## Entradas
- `main` con F0; `docs/handoffs/F0.md`; `03-flujos-de-negocio.md` §2, §4, §5.

## Alcance
1. **Servicio de transiciones** `orders.transition()` con la máquina de estados exacta de `03-flujos-de-negocio.md`, validación de rol por transición, `order_events`, marcas de tiempo, error `409 INVALID_TRANSITION`.
2. **Crear pedido** (cliente y admin): `Idempotency-Key`, precios vía `CatalogService.priceOrderLines`, crédito vía `FinanceService.assertCanPlaceOrder`, fecha de entrega con `cutoff_time` **[C-6]**, estado inicial según modo (`AWAITING_PAYMENT` o `CONFIRMED`), llamada a `FinanceService.onOrderConfirmed` dentro de la misma transacción.
3. **Implementar `OrdersService.confirmPaidOrder`** (lo llama B3 al aprobar pago de contado).
4. **Cancelación** con reglas por rol y `FinanceService.onOrderCancelled`.
5. **Edición de pedido por admin** antes de `READY` (cambiar cantidades/quitar líneas; recalcula y ajusta la CxC vía `FinanceService`) **[C-9]**.
6. **Cocina**: cola por fecha de entrega y estado; transiciones `PREPARING`, `READY`; endpoint **“totales a producir”** (suma por producto). Sin montos en las respuestas.
7. **Auto-asignación**: al pasar a `READY`, `assigned_driver_id = settings.delivery.default_driver_id`; si no hay motorizado configurado, el pedido queda `READY` sin asignar y se alerta al admin.
8. **Delivery**: “mis pedidos” (READY/OUT_FOR_DELIVERY/entregados hoy), transiciones `OUT_FOR_DELIVERY` (individual y múltiple) y `DELIVERED`. Incluye `amount_to_collect` si aplica **[C-4]**.
9. **Notificaciones** (implementar `Notifier`):
   - **SSE** `GET /v1/events`: canal por rol (cocina recibe `order.new`, `order.updated`, `order.cancelled`; admin recibe todo). Autenticación por token (query param de corta vida o cookie), *heartbeat* cada 25 s, `Last-Event-ID` para reanudar.
   - **FCM**: envío a `device_tokens` del usuario; limpieza de tokens inválidos; si no hay credenciales de Firebase, adaptador que solo registra en log.
   - Mensajes en español: “Nueva orden #1042 — Panadería El Trigal”, “Tu pedido #1042 va en camino”, etc.
10. **Listados admin**: filtros por estado, fecha, cliente, canal; detalle con bitácora.

## Fuera de alcance
Lógica de billetera/CxC (B3), catálogo (B1), interfaces.

## Carpetas propias
`api/src/modules/orders`, `api/src/modules/kitchen`, `api/src/modules/delivery`, `api/src/modules/notifications` y sus tests.

## Limitantes
- Consumir finanzas y catálogo **solo** por sus interfaces; mientras B1/B3 no estén fusionados, se prueba con los stubs de F0.
- Railway puede cortar conexiones largas: el SSE debe tolerar reconexiones (heartbeat + `Last-Event-ID`).
- Instancia única de API en v1: el bus de eventos puede ser en memoria. Dejar la interfaz lista para cambiar a `LISTEN/NOTIFY` de Postgres si se escalan réplicas.

## Oportunidades
- `LISTEN/NOTIFY` de Postgres hace el SSE robusto con varias réplicas sin agregar Redis.
- Tests de concurrencia: dos “Listo” simultáneos, doble envío de creación con la misma `Idempotency-Key`.

## Definición de terminado
- Tests: todas las transiciones válidas e inválidas por rol; idempotencia; auto-asignación; SSE recibe evento al crear pedido; push enviado al pasar a READY (mock de FCM).
- Test de contrato verde; desplegado en staging; handoff con secuencia `curl` de un pedido completo.

## Siguiente
Desbloquea datos reales en **W2** (cocina), **M2** (delivery), pedidos en **M1** y **W1**.

## Prompt para lanzar este bloque
```
Eres el agente del bloque B2 del proyecto JM Cakes (repo edicsonbtos/jmcakes).
Lee CLAUDE.md, docs/plan/ (especialmente 03-flujos-de-negocio.md),
docs/plan/bloques/B2-api-pedidos-produccion-delivery.md, docs/handoffs/F0.md y
docs/CUESTIONARIO.md. Implementa todo el alcance de B2 solo dentro de tus carpetas,
siguiendo docs/plan/05-protocolo-agentes.md (rama block/B2-pedidos, CI verde,
handoff docs/handoffs/B2.md, STATUS.md). Usa FinanceService y CatalogService
solo por sus interfaces: B1 y B3 los implementan en paralelo.
```
