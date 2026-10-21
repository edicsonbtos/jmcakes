# Adaptado de OpenGravity: apps/bot/src/domain/payment_methods/db_models.py
"""Métodos de cobro y sus cuentas (02 §Pagos). Sin borrado: se desactivan con `isActive = false`.

`bank_accounts.cashAccountId` liga cada cuenta de cobro con la cuenta del negocio donde entra el dinero.
"""
from __future__ import annotations

from sqlalchemy import JSON, Boolean, Column, Integer, String

from src.db.base import Base
from src.db.columns import created_at, enum_col, fk, pk, updated_at
from src.db.enums import Currency, PaymentMethodType


class PaymentMethodDB(Base):
    __tablename__ = "payment_methods"

    id = pk()
    name = Column("name", String, nullable=False)
    type = enum_col("type", PaymentMethodType, nullable=False)
    currency = enum_col("currency", Currency, nullable=False)
    is_active = Column("isActive", Boolean, nullable=False, default=True)
    display_order = Column("displayOrder", Integer, nullable=False, default=0)
    # Campos que el cliente ve para pagar (banco, teléfono, cédula…), como JSON.
    fields = Column("fields", JSON, nullable=True)
    instructions = Column("instructions", String, nullable=True)
    created_at = created_at()
    updated_at = updated_at()


class BankAccountDB(Base):
    __tablename__ = "bank_accounts"

    id = pk()
    payment_method_id = fk("paymentMethodId", "payment_methods.id", nullable=False)
    account_label = Column("accountLabel", String, nullable=False)
    account_data = Column("accountData", JSON, nullable=True)
    is_default = Column("isDefault", Boolean, nullable=False, default=False)
    is_active = Column("isActive", Boolean, nullable=False, default=True)
    cash_account_id = fk("cashAccountId", "cash_accounts.id", nullable=False)
    created_at = created_at()
    updated_at = updated_at()
