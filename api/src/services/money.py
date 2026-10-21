"""`MoneyService` (08 §Interfaces). **Stub de FND-E1**; B-E1b lo reemplaza con la implementación real.

El stub no escribe dinero: solo deja constancia en el log. En las pruebas, la fixture `money_double`
lo sustituye por un doble que registra las llamadas.
"""
from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class StubMoneyService:
    async def open_balance(
        self,
        session: AsyncSession,
        customer_id: str,
        amount: Decimal,
        note: str | None,
        actor_id: str | None,
    ) -> None:
        logger.info("open_balance (stub) cliente=%s monto=%s", customer_id, amount)


_instance = StubMoneyService()


def get_money_service() -> StubMoneyService:
    """Fábrica (registro: `money`)."""
    return _instance
