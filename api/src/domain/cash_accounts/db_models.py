# Adaptado de OpenGravity: apps/bot/src/domain/wallets/db_models.py
"""Cuentas del negocio (02 §Cuentas del negocio).

`amount` va **con signo** en la moneda de la cuenta (INCOME > 0, EXPENSE < 0, ADJUSTMENT ≠ 0)
y `balance += amount`. `seq` ordena los movimientos.
"""
from __future__ import annotations

from sqlalchemy import JSON, BigInteger, Boolean, CheckConstraint, Column, Index, Integer, Sequence, String

from src.db.base import Base
from src.db.columns import MONEY, created_at, enum_col, fk, pk, updated_at
from src.db.enums import CashTransactionType, Currency

CASH_ACCOUNT_TX_SEQ = Sequence("cash_account_tx_seq")


class CashAccountDB(Base):
    __tablename__ = "cash_accounts"

    id = pk()
    name = Column("name", String, nullable=False)
    account_type = Column("accountType", String, nullable=False)
    currency = enum_col("currency", Currency, nullable=False)
    balance = Column("balance", MONEY, nullable=False, default=0)
    is_active = Column("isActive", Boolean, nullable=False, default=True)
    display_order = Column("displayOrder", Integer, nullable=False, default=0)
    created_at = created_at()
    updated_at = updated_at()


class CashAccountTransactionDB(Base):
    __tablename__ = "cash_account_transactions"
    __table_args__ = (
        CheckConstraint(
            "(\"transactionType\" = 'INCOME' AND amount > 0) "
            "OR (\"transactionType\" = 'EXPENSE' AND amount < 0) "
            "OR (\"transactionType\" = 'ADJUSTMENT' AND amount <> 0)",
            name="amount_sign",
        ),
        Index("ix_cash_account_transactions_cash_account_id_seq", "cashAccountId", "seq"),
    )

    id = pk()
    seq = Column(
        "seq", BigInteger, CASH_ACCOUNT_TX_SEQ, nullable=False, unique=True,
        server_default=CASH_ACCOUNT_TX_SEQ.next_value(),
    )
    cash_account_id = fk("cashAccountId", "cash_accounts.id", nullable=False, index=False)
    transaction_type = enum_col("transactionType", CashTransactionType, nullable=False)
    amount = Column("amount", MONEY, nullable=False)
    balance_after = Column("balanceAfter", MONEY, nullable=False)
    # `payment` o `payout`.
    reference_type = Column("referenceType", String, nullable=True)
    reference_id = Column("referenceId", String, nullable=True)
    customer_id = fk("customerId", "customers.id")
    customer_name = Column("customerName", String, nullable=True)
    approved_by = fk("approvedBy", "users.id")
    notes = Column("notes", String, nullable=True)
    # `exchange_rate`, `amount_usd`, `amount_ves`.
    metadata_json = Column("metadata", JSON, nullable=True)
    created_at = created_at()
