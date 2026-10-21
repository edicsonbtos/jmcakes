# Adaptado de OpenGravity: apps/bot/src/domain/exchange_rates/db_models.py
"""Tasas USD/VES (02 §Operación). La fila BCV de un día se inserta una sola vez; las correcciones son MANUAL."""
from __future__ import annotations

from sqlalchemy import JSON, CheckConstraint, Column, Date, DateTime, String, UniqueConstraint

from src.db.base import Base
from src.db.columns import RATE, created_at, enum_col, pk
from src.db.enums import RateType
from src.utils.date_utils import utcnow


class ExchangeRateDB(Base):
    __tablename__ = "exchange_rates"
    __table_args__ = (
        UniqueConstraint(
            "date", "baseCurrency", "targetCurrency", "rateType", name="uq_exchange_rates_date_pair_type"
        ),
        CheckConstraint("value > 0", name="value_pos"),
    )

    id = pk()
    date = Column("date", Date, nullable=False, index=True)
    base_currency = Column("baseCurrency", String, nullable=False, default="USD")
    target_currency = Column("targetCurrency", String, nullable=False, default="VES")
    rate_type = enum_col("rateType", RateType, nullable=False)
    value = Column("value", RATE, nullable=False)
    source_url = Column("sourceUrl", String, nullable=True)
    fetched_at = Column("fetchedAt", DateTime, nullable=False, default=utcnow)
    metadata_json = Column("metadata", JSON, nullable=True)
    created_at = created_at()
