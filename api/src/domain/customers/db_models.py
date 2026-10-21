"""Clientes (02 §Clientes). `walletBalance` solo lo escribe `services/ledger.py`."""
from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Index, Integer, String

from src.db.base import Base
from src.db.columns import MONEY, created_at, enum_col, fk, pk, updated_at
from src.db.enums import CustomerSegment, CustomerType, PaymentMode


class CustomerDB(Base):
    __tablename__ = "customers"
    __table_args__ = (
        CheckConstraint('"walletBalance" >= 0', name="wallet_nonneg"),
        CheckConstraint('"creditLimit" >= 0', name="credit_limit_nonneg"),
        CheckConstraint('"creditDays" >= 0', name="credit_days_nonneg"),
        Index("ix_customers_phone", "phone"),
    )

    id = pk()
    # null = cliente sin app. Único (el índice lo da la restricción única).
    user_id = fk("userId", "users.id", unique=True, index=False)
    type = enum_col("type", CustomerType, nullable=False)
    segment = enum_col("segment", CustomerSegment, nullable=True)
    business_name = Column("businessName", String, nullable=True)
    contact_name = Column("contactName", String, nullable=False)
    phone = Column("phone", String, nullable=True)
    id_document = Column("idDocument", String, nullable=True)
    address_text = Column("addressText", String, nullable=True)
    address_reference = Column("addressReference", String, nullable=True)
    payment_mode = enum_col("paymentMode", PaymentMode, nullable=False, default=PaymentMode.CASH)
    credit_limit = Column("creditLimit", MONEY, nullable=False, default=0)
    credit_days = Column("creditDays", Integer, nullable=False, default=7)
    wallet_balance = Column("walletBalance", MONEY, nullable=False, default=0)
    is_blocked = Column("isBlocked", Boolean, nullable=False, default=False)
    blocked_reason = Column("blockedReason", String, nullable=True)
    # Guarda el apodo ("la del kiosko") y es buscable.
    notes = Column("notes", String, nullable=True)
    deleted_at = Column("deletedAt", DateTime, nullable=True)
    created_at = created_at()
    updated_at = updated_at()
