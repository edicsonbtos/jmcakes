---
name: contabilidad-panaderia
description: Reglas de dinero de la panadería — billetera del cliente (ledger solo inserción), cuentas por cobrar, cuentas del negocio con monto con signo, tasa BCV con rate_for y conversión USD/VES. Úsala antes de tocar api/src/services/ledger.py, services/money.py, domain/{payments,wallet,receivables,cash_accounts,finance,exchange_rates,dashboard} o cualquier flujo que mueva dinero (fiado, abono, anular, revertir, saldo anterior).
---
# Adaptado de OpenGravity: .agents/skills/contabilidad-opengravity/SKILL.md

# Contabilidad de la panadería

La referencia ejecutable es `spec/money_model.py` (con `spec/test_money_model.py`). Las reglas
escritas están en `docs/plan/03-flujos-de-negocio.md` §0–§3.10b y §3.11–§3.13. **Si la API y el
modelo discrepan, manda el modelo.**

## Tres planos que no se mezclan
| | Billetera del cliente | Cuentas por cobrar (CxC) | Cuentas del negocio |
|---|---|---|---|
| Tablas | `customers.walletBalance` + `wallet_movements` | `receivables` + `receivable_items` | `cash_accounts` + `cash_account_transactions` |
| Moneda | USD | USD | La de la cuenta (USD o VES) |
| Signo | `amount ≠ 0` con signo; `balanceAfter ≥ 0` | `0 ≤ paidAmount ≤ amount` | `amount` **con signo** (INCOME > 0, EXPENSE < 0) |
| Orden | `seq` (`wallet_movements_seq`) | `dueAt ASC, issuedAt ASC` | `seq` (`cash_account_tx_seq`) |

- Saldo mostrado = `openDebt − walletBalance` (positivo = debe). Vencido = CxC OPEN/PARTIAL con `dueAt < ahora`.
- Los Bs (`*Ves`) se calculan en el servidor con `ROUND_HALF_UP` a 2 decimales y **no se guardan**.

## Quién escribe
- **Solo `services/ledger.py`** escribe `walletBalance`, `wallet_movements`, `cash_accounts.balance` y
  `cash_account_transactions`. Un service de dominio nunca asigna saldos.
- Todo flujo con dinero corre en **una transacción**: primero `CustomersService.get_for_update`
  (`SELECT … FOR UPDATE` del cliente), luego el ledger, al final `commit` en el service.
- `wallet_movements` es **solo inserción**; `createdAt` se asigna en Python (`utcnow()`), nunca
  `server_default=func.now()`.
- `settle` corre después de: aprobar un pago o abono, ajuste positivo, cualquier reembolso
  (anular, cancelar, reducir) y crear una CxC manual. Paga CxC por `dueAt ASC, issuedAt ASC`.

## Cuaderno (E1, 03 §3.10b)
- **Fiado:** CxC `MANUAL` con líneas; `lineTotal = round(qty × unitPrice, 2)` por línea; precio
  detal (`retailPrice ?? price`) para RETAIL y mayor (`price`) para WHOLESALE, editable por línea;
  sin `minQty` ni bloqueos; advertencia `CREDIT_LIMIT_EXCEEDED` solo si `creditLimit > 0`.
- **Saldo anterior:** `> 0` → CxC `OPENING_BALANCE`; `< 0` → `ADJUSTMENT(+)` con nota. Vía
  `MoneyService.open_balance` (interfaz congelada).
- **Abono:** pago `purpose = MANUAL` que nace APPROVED; `reference` obligatoria salvo efectivo; la
  `Idempotency-Key` se verifica **antes** que la referencia.
- **Anular:** solo MANUAL, OPENING_BALANCE o PAYMENT_REVERSAL; lo pagado vuelve con
  `RECEIVABLE_REFUND` y `settle` lo reaplica.
- **Revertir:** si no alcanza la billetera, CxC `PAYMENT_REVERSAL` con `dueAt = ahora`;
  `ENTRY_ERROR` libera la referencia, `BANK_RETURN` no (`uq_payments_bank_account_reference_live`).

## Moneda y tasa
- `RateService.rate_for(d)`: MANUAL de `d` > BCV de `d` > la más reciente ≤ `d` (`isFallback`) >
  `RATE_UNAVAILABLE`. Solo lectura: sin HTTP y sin commit. **Nunca** hay una tasa inventada.
- Pago en Bs: `amountUsd = round(amountLocal / bcvRateUsed, 2)` con `bcvRateUsed = rate_for(paidOn)`
  (el admin puede corregirla). Un monto ya convertido **no se reconvierte**.
- Cuenta del negocio VES: `+amountLocal` tal cual (cuadra con el banco); cuenta USD: `+amountUsd`.
  Metadata `{exchange_rate, amount_usd, amount_ves}`. Si la moneda del pago, del método y de la
  cuenta no coinciden → error, nunca conversión.

## Antes de dar por terminado
- Prueba con saldos **y** asientos, y al final `await assert_money_invariants(session)`
  (`api/tests/helpers.py`, SQL literal de 02 §Invariantes).
- Si tocaste conversión: un caso VES y uno USD.
- Concurrencia: dos operaciones del mismo cliente con `committed_db` sin romper invariantes.
- Pasa el agente `auditor-contable` sobre tu diff y pega el informe en el handoff.
