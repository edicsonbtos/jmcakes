"""Billetera del cliente (02 §Billetera). **Solo inserción**; la escribe únicamente `services/ledger.py`.

`seq` es el orden canónico del ledger (invariantes, estado de cuenta y cursor).
"""
from __future__ import annotations

from sqlalchemy import BigInteger, CheckConstraint, Column, Index, Sequence, String

from src.db.base import Base
from src.db.columns import MONEY, created_at, enum_col, fk, pk
from src.db.enums import WalletMovementType

WALLET_MOVEMENTS_SEQ = Sequence("wallet_movements_seq")


class WalletMovementDB(Base):
    __tablename__ = "wallet_movements"
    __table_args__ = (
        CheckConstraint("amount <> 0", name="amount_nonzero"),
        CheckConstraint('"balanceAfter" >= 0', name="balance_after_nonneg"),
        CheckConstraint("type <> 'ADJUSTMENT' OR note IS NOT NULL", name="adjustment_note"),
        Index("ix_wallet_movements_customer_id_seq", "customerId", "seq"),
    )

    id = pk()
    seq = Column(
        "seq", BigInteger, WALLET_MOVEMENTS_SEQ, nullable=False, unique=True,
        server_default=WALLET_MOVEMENTS_SEQ.next_value(),
    )
    customer_id = fk("customerId", "customers.id", nullable=False, index=False)
    type = enum_col("type", WalletMovementType, nullable=False)
    amount = Column("amount", MONEY, nullable=False)
    balance_after = Column("balanceAfter", MONEY, nullable=False)
    order_id = fk("orderId", "orders.id")
    receivable_id = fk("receivableId", "receivables.id")
    payment_id = fk("paymentId", "payments.id")
    cash_account_transaction_id = fk("cashAccountTransactionId", "cash_account_transactions.id")
    note = Column("note", String, nullable=True)
    created_by_user_id = fk("createdByUserId", "users.id")
    created_at = created_at()
