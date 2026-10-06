# B3 — API de dinero: pagos, billetera, CxC, cuentas del negocio, tasa, dashboard y cierres

**Fase 1** · **Rama** `block/B3` · Endpoints: [08](../08-api-endpoints.md) §B3 · Reglas: [03](../03-flujos-de-negocio.md) §3 y §6 · Referencia ejecutable: `spec/money_model.py`

## Objetivo
Implementar el dinero con la exactitud de OpenGravity, de modo que cada escenario de `spec/test_money_model.py` se cumpla igual contra la API real.

## Alcance
1. **`services/ledger.py`**: el **único** que escribe saldos.
   - Patrón de OpenGravity: bloqueo `for_update`, `balanceAfter` y metadata USD/VES.
   - Métodos de billetera: `charge_order`, `refund_order`, `record_payment_approved`, `settle_receivable`, `reverse_payment` y `adjust`.
   - Métodos de cuentas del negocio: `cash_income` y `cash_expense`.
2. **`services/money.py`: implementar `MoneyService`** (03 §3.1, §3.2, §3.5, §3.8 y §3.9) y `settle()` con el orden exacto de obligaciones, más `FinanceQueries`.
3. **Pagos** (copiar y adaptar el dominio `payments` de OpenGravity):
   - Reportar, con:
     - idempotencia;
     - referencia única (índice parcial);
     - tasa de `paidOn` vía `ExchangeRateService.get_rate_at_date`;
     - `amountUsd = round(amountLocal / tasa, 2)`;
     - comprobante (`files`).
   - Revisar: `take` (IN_REVIEW), `approve` (03 §3.4, con correcciones auditadas), `reject` (con motivo) y `reverse` (03 §3.7).
   - Al aprobar: `settle` con prioridad al pedido del pago y `OrdersService.confirm_paid` para cada pedido que quede pagado.
   - Eventos `payment.reported` y `payment.updated`; push al cliente.
4. **Billetera y CxC**
   - `GET /me/wallet` y movimientos.
   - Admin: abono manual (pago APPROVED con `purpose = MANUAL`), cargos (CxC MANUAL), ajustes y anulación de CxC (devuelve lo pagado).
   - Estado de cuenta (JSON y CSV). Listado y antigüedad de CxC (0–7, 8–15, 16–30, +30).
5. **Métodos de pago y cuentas bancarias:** CRUD de OpenGravity más `GET /payment-methods` para la app. **Cuentas del negocio:** CRUD y transacciones.
6. **Tasa**
   - `GET /rates/today` y admin (`manual`, `sync`), con el `ExchangeRateService` de OpenGravity sin cambios de lógica.
   - Job `bcv_sync` a las 06:00 CCS.
   - Error `RATE_UNAVAILABLE` si no hay ninguna tasa.
7. **Dashboard** (03 §6) y **cierres**:
   - copiar `closures` de OpenGravity con métricas nuevas y su PDF (`reportlab`);
   - job `daily_closing` a las 23:50, idempotente;
   - export CSV.
8. **Auditor contable**: correr `.claude/agents/auditor-contable.md` (lo adapta FND) sobre el diff final y anexar el informe al handoff.

## No tocar
Transiciones de pedidos (B2), catálogo y clientes (B1), `db_models.py`, `main.py`.

## Pruebas exigidas
- **Portar los 18 escenarios de `spec/test_money_model.py`** a pruebas de API (HTTP y services) sobre Postgres, con `assert_money_invariants` después de cada uno.
- **Prueba de propiedades** (Hypothesis, ≥ 200 ejemplos) sobre los services con Postgres: secuencias aleatorias de pedir, reportar, aprobar, rechazar, cancelar y ajustar, con las invariantes I-1 a I-7 tras cada paso.
- **Concurrencia (E10):** dos aprobaciones simultáneas del mismo cliente en sesiones distintas, y aprobar mientras el cliente crea un pedido. Saldo correcto, sin pérdidas.
- **USD/VES:** pago en Bs con la tasa del día del pago, pago en USD y corrección de tasa del admin. La cuenta VES recibe `amountLocal` exacto.
- **Dashboard:** límites del día de Caracas (E11).
- Copiar y adaptar las pruebas de OpenGravity de `payments` (idempotencia, rechazo) y `exchange_rates`.

## Definición de terminado
Protocolo §6, más el informe del auditor contable sin hallazgos altos.
