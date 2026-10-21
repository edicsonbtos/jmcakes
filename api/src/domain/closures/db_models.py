# Adaptado de OpenGravity: apps/bot/src/domain/closures/db_models.py
"""Cierre diario (02 §Operación). Una fila por día de Caracas; el job y sus endpoints llegan después de E1."""
from __future__ import annotations

from sqlalchemy import JSON, Column, Date, DateTime, Integer

from src.db.base import Base
from src.db.columns import MONEY, RATE, created_at, fk, pk, updated_at


class DailyClosingDB(Base):
    __tablename__ = "daily_closings"

    id = pk()
    closing_date = Column("closingDate", Date, nullable=False, unique=True)
    income_usd = Column("incomeUsd", MONEY, nullable=False, default=0)
    reversals_usd = Column("reversalsUsd", MONEY, nullable=False, default=0)
    payouts_usd = Column("payoutsUsd", MONEY, nullable=False, default=0)
    sales_usd = Column("salesUsd", MONEY, nullable=False, default=0)
    orders_count = Column("ordersCount", Integer, nullable=False, default=0)
    receivables_open_usd = Column("receivablesOpenUsd", MONEY, nullable=False, default=0)
    wallet_total_usd = Column("walletTotalUsd", MONEY, nullable=False, default=0)
    rate_value = Column("rateValue", RATE, nullable=True)
    # Métricas completas (por método, por cuenta, …).
    metrics_json = Column("metricsJson", JSON, nullable=False)
    pdf_file_id = fk("pdfFileId", "files.id")
    generated_at = Column("generatedAt", DateTime, nullable=False)
    created_at = created_at()
    updated_at = updated_at()
