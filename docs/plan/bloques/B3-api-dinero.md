# B3 — API de dinero: pagos, billetera, CxC, cuentas, tasa, dashboard y cierres

**Fase 1** · rama `block/B3` · BD `panaderia_test_b3` · [08](../08-api-endpoints.md) §B3 · reglas [03](../03-flujos-de-negocio.md) §0, §3 y §6 · referencia ejecutable `spec/money_model.py`

## Objetivo
Implementar el dinero con la exactitud de OpenGravity, **sin sus defectos** (06), de modo que cada escenario de `spec/` se cumpla igual en la API.

## Alcance
1. **`services/ledger.py`** (el único que escribe saldos): `charge_order`, `refund_order`, `record_payment_approved`, `settle_receivable`, `refund_receivable`, `reverse_payment`, `payout` y `adjust`, más `cash_income`, `cash_expense` y `cash_adjust` con el **monto con signo**.
   - Bloqueo `FOR UPDATE` y `balanceAfter`.
   - La moneda del pago, la del método y la de la cuenta deben coincidir; si no, error. **Nunca** se reconvierte ni se usa una tasa de respaldo de 1.0.
2. **`services/money.py`:** `MoneyService` completo (`assert_can_order` con CUSTOMER_BLOCKED, OVERDUE_DEBT de cualquier modo y OPEN_DEBT en CASH; `checkout`, `quote`, `amount_due`, `on_order_cancelled`, `on_order_reduced`) y `settle()` (03 §3.5, sin confirmar pedidos de clientes bloqueados). Más `FinanceQueries`.
3. **Pagos**, código nuevo sobre la base de OpenGravity:
   - Reportar con: `FOR UPDATE` del pedido; validación de `paidOn`; moneda; `rate_for(paidOn)`; referencia única (incluye REVERSED); `FileService.assert_owned` del comprobante; idempotencia por cliente + `requestHash`.
   - `take`, `approve` (con correcciones auditadas en `correctedFrom`), `reject` (extiende `expiresAt`), `reverse` (03 §3.7).
   - Al aprobar: `settle` con prioridad y `OrdersService.confirm_paid` para los pedidos que se completen.
   - Eventos `payment.*` y push.
   - `GET /payments/{id}` y `GET /admin/payments/pending-count`.
4. **Admin de dinero** (`admin_money.py`): abono manual (pago APPROVED MANUAL con `orderId` opcional), cargos, ajustes, **devoluciones** (03 §3.12), **anular y condonar** CxC (03 §3.11), estado de cuenta (JSON y CSV), CxC y antigüedad.
5. **Métodos de pago y cuentas bancarias** (`/payment-methods` con todas las cuentas y su `id`; CRUD admin con `cashAccountId`) y **cuentas del negocio**.
6. **Tasa:** endpoints `rates` (lectura con `rate_for`; `manual`; `sync` con su propia sesión). Job `bcv_sync`.
7. **Dashboard** (03 §6) y **cierres** (OpenGravity `closures` corregido): SQL por los límites del día de Caracas, sin `.date()` sobre UTC, sin carga total en memoria, sin commit interno, cuentas VES en su moneda. Job `daily_closing`, PDF y export CSV.
8. **Auditor contable** (`.claude/agents/auditor-contable.md`) sobre el diff final; el informe va al handoff.

## No tocar
Transiciones de pedidos (B2), catálogo y clientes (B1), `db_models.py`, `interface.py`, `main.py`, `jobs/runner.py`.

## Pruebas exigidas
- **Portar los 29 escenarios de `spec/test_money_model.py`** a pruebas de **services** sobre Postgres, con `assert_money_invariants` tras cada una. Los pedidos se crean con `tests/b3_orders_helper.py`: inserta `OrderDB` con los modelos congelados y llama a `checkout`, `on_order_cancelled` y `on_order_reduced` como lo haría B2.
- **Por HTTP** solo los endpoints de B3: pagos, billetera, `admin_money`, métodos de pago, tasa, dashboard y cierres.
- **Propiedades** (Hypothesis, ≥ 200 ejemplos) sobre los services con Postgres e invariantes I-1…I-9.
- **E10:** dos aprobaciones en sesiones reales (`committed_db`) y `checkout` en paralelo con `approve`.
- **USD/VES (E14):** pago en Bs con la tasa de `paidOn`; los Bs exactos mostrados confirman el pedido; corrección de tasa; cuenta VES con `amountLocal` exacto; RATE_UNAVAILABLE sin commit parcial.
- **E11:** pago aprobado a las 22:30 VET en el día correcto del dashboard y del cierre.
- Copiar y adaptar las pruebas de OpenGravity de `payments` y `exchange_rates` que apliquen, renombradas por comportamiento.
