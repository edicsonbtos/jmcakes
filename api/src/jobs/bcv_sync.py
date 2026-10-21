"""Job `bcv_sync` (06:00 Caracas): inserta la fila BCV del día si falta (03 §3.10). Dueño: B-E1b.

`sync_daily_rate` hace su propio commit; si la fuente falla, el job lo registra y `rate_for`
sigue respondiendo con la tasa más reciente (`isFallback`) o con la MANUAL del admin.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.exchange_rates.service import sync_daily_rate


async def run(session: AsyncSession) -> None:
    await sync_daily_rate(session)
