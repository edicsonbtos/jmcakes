"""Ayudas de prueba compartidas.

`assert_money_invariants(session, tol)` ejecuta **literalmente** las consultas I-1…I-9 de
docs/plan/02 §Invariantes (I-8 no es SQL: se prueba sobre el OpenAPI). Cada consulta debe devolver
0 filas. Toda prueba de dinero termina llamándola.

Única adaptación (pedida como cambio a 02 en el handoff de FND-E1): en I-9 se compara
`o."paymentStatus"::text`, porque Postgres no tiene operador entre un enum nativo y el `text` que
devuelve el `CASE`. `I9_ENUM_CAST` la documenta y la prueba de copia literal la tiene en cuenta.
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Copiado literal de docs/plan/02-modelo-de-datos.md §Invariantes.
INVARIANTS_SQL = """
-- I-1a saldo guardado = suma del ledger, nunca negativo
SELECT c.id FROM customers c LEFT JOIN wallet_movements m ON m."customerId" = c.id
GROUP BY c.id, c."walletBalance"
HAVING c."walletBalance" <> COALESCE(SUM(m.amount),0) OR c."walletBalance" < 0;
-- I-1b balanceAfter correlativo por seq
SELECT id FROM (SELECT m.id, m."balanceAfter",
   SUM(m.amount) OVER (PARTITION BY m."customerId" ORDER BY m.seq) AS run FROM wallet_movements m) t
WHERE "balanceAfter" <> run OR run < 0;
-- I-2 paidFromWallet = −Σ(ORDER_CHARGE + ORDER_REFUND)
SELECT o.id FROM orders o LEFT JOIN wallet_movements m
  ON m."orderId" = o.id AND m.type IN ('ORDER_CHARGE','ORDER_REFUND')
GROUP BY o.id, o."paidFromWallet" HAVING o."paidFromWallet" <> -COALESCE(SUM(m.amount),0);
-- I-3 CxC viva: paidAmount = −Σ(RECEIVABLE_SETTLEMENT + RECEIVABLE_REFUND) y amount > 0
SELECT r.id FROM receivables r LEFT JOIN wallet_movements m
  ON m."receivableId" = r.id AND m.type IN ('RECEIVABLE_SETTLEMENT','RECEIVABLE_REFUND')
WHERE r.status <> 'VOID'
GROUP BY r.id, r."paidAmount", r.amount
HAVING r."paidAmount" <> -COALESCE(SUM(m.amount),0) OR r.amount <= 0;
-- I-4 pedido confirmado o posterior: total cubierto exactamente
SELECT o.id FROM orders o LEFT JOIN receivables r ON r."orderId" = o.id
WHERE o.status NOT IN ('AWAITING_PAYMENT','CANCELLED')
  AND (o.total <> o."paidFromWallet" + o."roundingAdjustment"
        + CASE WHEN r.id IS NULL THEN 0
               WHEN r.status = 'VOID' THEN r."forgivenAmount"
               ELSE r.amount + r."forgivenAmount" END
       OR o."roundingAdjustment" < 0 OR o."roundingAdjustment" > :tol);
-- I-5 pedido cancelado: nada cobrado y CxC anulada
SELECT o.id FROM orders o LEFT JOIN receivables r ON r."orderId" = o.id
WHERE o.status = 'CANCELLED' AND (o."paidFromWallet" <> 0 OR (r.id IS NOT NULL AND r.status <> 'VOID'));
-- I-6 conservación por cliente
SELECT c.id FROM customers c
WHERE c."walletBalance" <>
  COALESCE((SELECT SUM(amount) FROM wallet_movements m WHERE m."customerId" = c.id
            AND m.type IN ('TOPUP_APPROVED','PAYMENT_REVERSAL','ADJUSTMENT','WALLET_PAYOUT')),0)
  - COALESCE((SELECT SUM("paidFromWallet") FROM orders o WHERE o."customerId" = c.id AND o.status <> 'CANCELLED'),0)
  - COALESCE((SELECT SUM("paidAmount") FROM receivables r WHERE r."customerId" = c.id AND r.status <> 'VOID'),0);
-- I-7 cuentas del negocio (monto con signo) y balanceAfter por seq
SELECT a.id FROM cash_accounts a LEFT JOIN cash_account_transactions t ON t."cashAccountId" = a.id
GROUP BY a.id, a.balance HAVING a.balance <> COALESCE(SUM(t.amount),0);
SELECT id FROM (SELECT t.id, t."balanceAfter",
   SUM(t.amount) OVER (PARTITION BY t."cashAccountId" ORDER BY t.seq) AS run FROM cash_account_transactions t) x
WHERE "balanceAfter" <> run;
-- I-9 paymentStatus de pedidos a crédito
SELECT o.id FROM orders o JOIN receivables r ON r."orderId" = o.id
WHERE o.status <> 'CANCELLED'
  AND o."paymentStatus"::text <> CASE WHEN r.status IN ('OPEN','PARTIAL') THEN 'ON_CREDIT' ELSE 'PAID' END;
"""


#: (texto de 02, texto ejecutado): la única diferencia con la copia literal.
I9_ENUM_CAST = ('o."paymentStatus" <> CASE', 'o."paymentStatus"::text <> CASE')


def _split(sql: str) -> list[tuple[str, str]]:
    """[(nombre, consulta)] separando por `;`; el nombre es el último comentario `-- I-…` anterior."""
    out: list[tuple[str, str]] = []
    name = "?"
    for chunk in sql.split(";"):
        lines = [ln for ln in chunk.strip().splitlines()]
        body = []
        for ln in lines:
            if ln.strip().startswith("--"):
                name = ln.strip().lstrip("-").strip().split(" ")[0]
            else:
                body.append(ln)
        query = "\n".join(body).strip()
        if query:
            out.append((name, query))
    return out


INVARIANT_QUERIES = _split(INVARIANTS_SQL)


async def money_invariant_violations(session: AsyncSession, tol: Decimal = Decimal("0.01")) -> dict[str, list]:
    """{invariante: ids que la violan} (vacío si todo cuadra)."""
    await session.flush()
    bad: dict[str, list] = {}
    for name, query in INVARIANT_QUERIES:
        params = {"tol": tol} if ":tol" in query else {}
        rows = (await session.execute(text(query), params)).scalars().all()
        if rows:
            bad.setdefault(name, []).extend(rows)
    return bad


async def assert_money_invariants(session: AsyncSession, tol: Decimal = Decimal("0.01")) -> None:
    bad = await money_invariant_violations(session, tol)
    assert not bad, f"Invariantes de dinero violadas: {bad}"
