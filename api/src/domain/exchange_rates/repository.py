# Adaptado de OpenGravity: apps/bot/src/domain/exchange_rates/repository.py
"""Lecturas y escrituras de `exchange_rates` (solo `flush`)."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.enums import RateType
from src.domain.exchange_rates.db_models import ExchangeRateDB

BASE, TARGET = "USD", "VES"


class ExchangeRateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _pair(self, stmt):
        return stmt.where(ExchangeRateDB.base_currency == BASE, ExchangeRateDB.target_currency == TARGET)

    async def get_on(self, d: date, rate_type: RateType) -> ExchangeRateDB | None:
        stmt = self._pair(select(ExchangeRateDB)).where(ExchangeRateDB.date == d, ExchangeRateDB.rate_type == rate_type)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def latest_on_or_before(self, d: date) -> ExchangeRateDB | None:
        """La más reciente con fecha ≤ d, de cualquier tipo. A igual fecha, MANUAL gana a BCV."""
        stmt = (
            self._pair(select(ExchangeRateDB))
            .where(ExchangeRateDB.date <= d)
            .order_by(ExchangeRateDB.date.desc(), ExchangeRateDB.rate_type.desc(), ExchangeRateDB.fetched_at.desc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def add(self, row: ExchangeRateDB) -> ExchangeRateDB:
        self.session.add(row)
        await self.session.flush()
        return row
