# B3 — API: billetera, cuentas por cobrar, pagos y dashboard

**Fase:** 1 (paralelo) · **Esfuerzo:** L · **Rama:** `block/B3-finanzas`

## Objetivo
Llevar el dinero con exactitud contable: **billetera ≥ 0, cuentas por cobrar por pedido, pagos reportados y verificados, aplicación automática FIFO**, y los indicadores del dashboard del día en hora de Caracas.

## Entradas
- `main` con F0; `docs/handoffs/F0.md`; `03-flujos-de-negocio.md` §3 y §6.

## Alcance
1. **Implementar `FinanceService`**: `assertCanPlaceOrder`, `onOrderConfirmed`, `onOrderCancelled`, `onOrderDelivered`, exactamente como en `03-flujos-de-negocio.md`.
2. **`settle(customerId)`** con bloqueo `FOR UPDATE` por cliente, ledger solo-inserción, `receivable_allocations`, invariante de saldo.
3. **Pagos (cliente)**: reportar pago (método, moneda, monto, referencia, fecha, comprobante opcional vía URL prefirmada), `Idempotency-Key`, unicidad `(method, reference)`, listar mis pagos y su estado.
4. **Pagos (admin)**: bandeja de pendientes, aprobar (con edición de monto/tasa), rechazar con motivo. Al aprobar: `PAYMENT_IN` → `settle()` → si es pago de pedido de contado y lo cubre, `OrdersService.confirmPaidOrder`. Push al cliente con el resultado.
5. **Operaciones manuales**: cargo manual, abono manual, ajuste (+/−, nota obligatoria), anular CxC. Todo a `audit_log`.
6. **Estado de cuenta**: por cliente (movimientos de billetera, facturas abiertas/pagadas, antigüedad) — para el cliente (propio) y para el admin (cualquiera). Exportable CSV.
7. **CxC global**: total por tipo de cliente (detal/mayorista), vigente vs. vencida (por `due_at`), antigüedad 0-7 / 8-15 / 16-30 / +30 días, top deudores.
8. **Tasa de cambio**: CRUD de la tasa del día; conversión en pagos VES **[C-1][C-2]**.
9. **Dashboard** (`03-flujos-de-negocio.md` §6): ingresos del día por método/moneda, ventas del día, pedidos por estado, pagos por verificar, top productos (hoy/7/30), **cierre del día** CSV. Todo con `businessDate` de Caracas.
10. Exponer a B1 una consulta de deuda por cliente para el listado de clientes.

## Fuera de alcance
Transiciones de pedidos (B2), catálogo (B1), interfaces.

## Carpetas propias
`api/src/modules/finance`, `api/src/modules/dashboard` y sus tests.

## Limitantes
- **Nunca** actualizar `wallet_balance_cents` fuera de `settle()`/funciones del ledger.
- **Nunca** usar `float`/`number` para dinero en BD; `bigint` y librería de decimales para conversiones.
- Consumir pedidos solo vía `OrdersService`.

## Oportunidades
- **Tests de propiedades** (fast-check): para cualquier secuencia de pagos, pedidos y cancelaciones, `wallet = Σ ledger ≥ 0` y `Σ asignaciones = Σ pagado de facturas`.
- Test de concurrencia: dos aprobaciones de pago simultáneas para el mismo cliente.
- Vistas SQL materializables para el dashboard si crece el volumen.

## Definición de terminado
- Tests unitarios + propiedades + concurrencia verdes.
- Escenario documentado en el handoff: cliente crédito con límite $100 pide $60, pide $50 (rechazado), reporta $40 → aprobado → deuda $20, pide $50 → OK.
- Desplegado en staging.

## Siguiente
Desbloquea **W1** (finanzas y dashboard) y la billetera de **M1**.

## Prompt para lanzar este bloque
```
Eres el agente del bloque B3 del proyecto JM Cakes (repo edicsonbtos/jmcakes).
Lee CLAUDE.md, docs/plan/ (especialmente 03-flujos-de-negocio.md §3 y §6),
docs/plan/bloques/B3-api-finanzas-dashboard.md, docs/handoffs/F0.md y
docs/CUESTIONARIO.md. Implementa todo el alcance de B3 solo dentro de tus carpetas,
siguiendo docs/plan/05-protocolo-agentes.md (rama block/B3-finanzas, CI verde,
handoff docs/handoffs/B3.md, STATUS.md). El dinero es un ledger: escribe tests de
propiedades y de concurrencia. B2 implementa OrdersService en paralelo.
```
