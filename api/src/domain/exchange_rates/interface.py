"""Interfaz congelada de la tasa (03 §0)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.enums import RateType


@dataclass(frozen=True)
class Rate:
    """Tasa usada para mostrar o convertir."""

    date: date
    value: Decimal
    rate_type: RateType
    is_fallback: bool


@runtime_checkable
class RateService(Protocol):
    async def rate_for(self, session: AsyncSession, d: date) -> Rate:
        """MANUAL de `d` > BCV de `d` > la más reciente con fecha ≤ `d` (`is_fallback=True`).
        Sin ninguna → `AppError(RATE_UNAVAILABLE)`. Solo lectura: sin HTTP y sin commit."""
        ...

    async def rate_for_or_none(self, session: AsyncSession, d: date) -> Rate | None:
        """Igual que `rate_for`, pero `None` si no hay tasa (para mostrar Bs en null)."""
        ...
