"""Interfaces internas congeladas de E1 (08 §Interfaces) y sus DTO.

Reglas:
- Cada implementación vive en el archivo de su bloque y se obtiene por **fábrica**, resuelta en
  tiempo de llamada: `Depends(get_x)` en routers y `services.registry.get("x")` en servicios.
- Las firmas no cambian; los cambios aditivos se declaran en el handoff.
- Las interfaces de pedidos, eventos, push y archivos llegan con E2–E4.

| Nombre en el registro | Protocol | Fábrica | Implementa |
|---|---|---|---|
| `customers` | `CustomersService` | `domain/customers/service.py` | FND (real) |
| `settings`  | `SettingsService`  | `domain/settings/service.py`  | FND (real) |
| `audit`     | `AuditService`     | `domain/audit/service.py`     | FND (real) |
| `rates`     | `RateService`      | `domain/exchange_rates/service.py` | FND (real) |
| `finance`   | `FinanceQueries`   | `domain/finance/queries.py`   | B-E1b (stub de FND: ceros) |
| `money`     | `MoneyService`     | `services/money.py`           | B-E1b (stub de FND: no escribe) |
"""
from __future__ import annotations

from decimal import Decimal
from typing import Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.audit.interface import AuditService
from src.domain.customers.interface import CustomersService
from src.domain.exchange_rates.interface import Rate, RateService
from src.domain.finance.interface import CustomerBalance, FinanceQueries
from src.domain.settings.interface import SettingsService


@runtime_checkable
class MoneyService(Protocol):
    """Dinero (B-E1b). En E1 solo se congela `open_balance`; el resto de 08 llega con E2."""

    async def open_balance(
        self,
        session: AsyncSession,
        customer_id: str,
        amount: Decimal,
        note: str | None,
        actor_id: str | None,
    ) -> None:
        """Saldo anterior (03 §3.10b): CxC `OPENING_BALANCE` si `amount > 0`, `ADJUSTMENT(+|amount|)` si
        `amount < 0` (nota “Saldo a favor anterior”), y luego `settle`. `amount == 0` no hace nada.
        No hace commit: lo hace quien llama, en su misma transacción."""
        ...


__all__ = [
    "AuditService",
    "CustomerBalance",
    "CustomersService",
    "FinanceQueries",
    "MoneyService",
    "Rate",
    "RateService",
    "SettingsService",
]
