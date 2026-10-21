"""Interfaz congelada de las consultas de saldo (08 §Interfaces). Implementa B-E1b; consume B-E1a."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, runtime_checkable

from sqlalchemy import Subquery
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class CustomerBalance:
    """Saldo de un cliente (03 §3.10b). `balance = openDebt − walletBalance` (positivo = debe)."""

    customer_id: str
    wallet_balance: Decimal
    open_debt: Decimal
    overdue_debt: Decimal

    @property
    def balance(self) -> Decimal:
        return self.open_debt - self.wallet_balance


@runtime_checkable
class FinanceQueries(Protocol):
    async def balances_for(self, session: AsyncSession, customer_ids: Sequence[str]) -> dict[str, CustomerBalance]:
        """Saldo de cada cliente pedido (todos presentes en el resultado; los desconocidos se omiten).
        `openDebt` = Σ(amount − paidAmount) de CxC OPEN/PARTIAL; `overdueDebt` = las de `dueAt < ahora`."""
        ...

    def debt_subquery(self) -> Subquery:
        """*Selectable* con columnas `customerId`, `openDebt`, `overdueDebt`, `walletBalance` y `balance`,
        una fila por cliente, para unir al listado y filtrar u ordenar por deuda."""
        ...
