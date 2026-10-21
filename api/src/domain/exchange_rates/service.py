"""Tasa del día (03 §0): `rate_for(d)` de solo lectura y `sync_daily_rate` con sesión propia.

- `rate_for(d)`: MANUAL de `d` > BCV de `d` > la más reciente con fecha ≤ `d` (`isFallback`).
  Sin ninguna → `RATE_UNAVAILABLE`. Nunca hay una tasa de respaldo inventada. Sin HTTP ni commit.
- `sync_daily_rate(session)`: consulta DolarAPI e **inserta** la fila BCV de hoy (Caracas) solo si no
  existe; nunca la actualiza (las correcciones son MANUAL). La usan el job `bcv_sync` y
  `POST /admin/rates/sync`, cada uno con su propia sesión, nunca dentro de una transacción de dinero.
"""
from __future__ import annotations

import logging
from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.errors import AppError, ErrorCode
from src.db.enums import RateType
from src.domain.exchange_rates.db_models import ExchangeRateDB
from src.domain.exchange_rates.fetcher import BCVFetcher
from src.domain.exchange_rates.interface import Rate
from src.domain.exchange_rates.repository import ExchangeRateRepository
from src.utils.date_utils import get_today_caracas

logger = logging.getLogger(__name__)


def _to_rate(row: ExchangeRateDB, *, fallback: bool) -> Rate:
    return Rate(date=row.date, value=row.value, rate_type=RateType(row.rate_type), is_fallback=fallback)


class DefaultRateService:
    async def rate_for_or_none(self, session: AsyncSession, d: date) -> Rate | None:
        repo = ExchangeRateRepository(session)
        for rate_type in (RateType.MANUAL, RateType.BCV):
            row = await repo.get_on(d, rate_type)
            if row is not None:
                return _to_rate(row, fallback=False)
        row = await repo.latest_on_or_before(d)
        return _to_rate(row, fallback=True) if row is not None else None

    async def rate_for(self, session: AsyncSession, d: date) -> Rate:
        rate = await self.rate_for_or_none(session, d)
        if rate is None:
            raise AppError(ErrorCode.RATE_UNAVAILABLE, {"date": d.isoformat()})
        return rate


_instance = DefaultRateService()


def get_rate_service() -> DefaultRateService:
    """Fábrica (registro: `rates`)."""
    return _instance


async def sync_daily_rate(
    session: AsyncSession, fetcher: BCVFetcher | None = None, today: date | None = None
) -> tuple[ExchangeRateDB, bool]:
    """Inserta la fila BCV de hoy si falta. Devuelve (fila, creada). Lanza `BCVFetchError` si la fuente falla.

    Hace `commit` (es su propia sesión). Si otra corrida la insertó a la vez, devuelve la existente.
    """
    today = today or get_today_caracas()
    repo = ExchangeRateRepository(session)
    existing = await repo.get_on(today, RateType.BCV)
    if existing is not None:
        return existing, False
    result = await (fetcher or BCVFetcher(settings.BCV_SOURCE_URL)).fetch_usd_ves_rate()
    row = ExchangeRateDB(
        date=today,
        rate_type=RateType.BCV,
        value=result.value,
        source_url=result.source_url,
        fetched_at=result.fetched_at,
        metadata_json=result.metadata,
    )
    try:
        await repo.add(row)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        existing = await ExchangeRateRepository(session).get_on(today, RateType.BCV)
        if existing is None:
            raise
        return existing, False
    logger.info("Tasa BCV del %s registrada: %s", today.isoformat(), row.value)
    return row, True
