"""`FinanceQueries` (08 §Interfaces). **Stub de FND-E1: ceros**; B-E1b lo reemplaza con la implementación real.

Mientras tanto, la lista y la ficha de clientes muestran `walletBalance` real y deuda 0.
"""
from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import Numeric, Subquery, cast, literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.customers.db_models import CustomerDB
from src.domain.finance.interface import CustomerBalance

_ZERO = Decimal("0.00")


class StubFinanceQueries:
    async def balances_for(self, session: AsyncSession, customer_ids: Sequence[str]) -> dict[str, CustomerBalance]:
        ids = list(dict.fromkeys(customer_ids))
        if not ids:
            return {}
        rows = (await session.execute(select(CustomerDB.id).where(CustomerDB.id.in_(ids)))).scalars().all()
        return {cid: CustomerBalance(cid, _ZERO, _ZERO, _ZERO) for cid in rows}

    def debt_subquery(self) -> Subquery:
        zero = cast(literal(0), Numeric(14, 2))
        return select(
            CustomerDB.id.label("customerId"),
            zero.label("openDebt"),
            zero.label("overdueDebt"),
            zero.label("walletBalance"),
            zero.label("balance"),
        ).subquery("customer_debt")


_instance = StubFinanceQueries()


def get_finance_queries() -> StubFinanceQueries:
    """Fábrica (registro: `finance`)."""
    return _instance
