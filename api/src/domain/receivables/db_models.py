"""Cuentas por cobrar y líneas de fiado (02 §Billetera y cuentas por cobrar)."""
from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, DateTime, Index, Numeric, String

from src.db.base import Base
from src.db.columns import MONEY, created_at, enum_col, fk, pk, updated_at
from src.db.enums import ReceivableSource, ReceivableStatus, ReceivableVoidReason


class ReceivableDB(Base):
    __tablename__ = "receivables"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="amount_nonneg"),
        CheckConstraint("status = 'VOID' OR amount > 0", name="amount_pos_unless_void"),
        CheckConstraint('"paidAmount" >= 0 AND "paidAmount" <= amount', name="paid_range"),
        CheckConstraint('"forgivenAmount" >= 0', name="forgiven_nonneg"),
        Index("ix_receivables_customer_id_status_due_at", "customerId", "status", "dueAt"),
    )

    id = pk()
    customer_id = fk("customerId", "customers.id", nullable=False, index=False)
    source = enum_col("source", ReceivableSource, nullable=False)
    # null = sistema. Quién fió o cargó el saldo anterior.
    created_by_user_id = fk("createdByUserId", "users.id")
    order_id = fk("orderId", "orders.id", unique=True, index=False)
    description = Column("description", String, nullable=True)
    amount = Column("amount", MONEY, nullable=False)
    paid_amount = Column("paidAmount", MONEY, nullable=False, default=0)
    forgiven_amount = Column("forgivenAmount", MONEY, nullable=False, default=0)
    status = enum_col("status", ReceivableStatus, nullable=False, default=ReceivableStatus.OPEN)
    issued_at = Column("issuedAt", DateTime, nullable=False)
    due_at = Column("dueAt", DateTime, nullable=False)
    void_reason = enum_col("voidReason", ReceivableVoidReason, nullable=True)
    voided_by = fk("voidedBy", "users.id")
    voided_at = Column("voidedAt", DateTime, nullable=True)
    note = Column("note", String, nullable=True)
    void_note = Column("voidNote", String, nullable=True)
    created_at = created_at()
    updated_at = updated_at()


class ReceivableItemDB(Base):
    """Líneas de un fiado. **Solo inserción**: anular un fiado no toca sus líneas."""

    __tablename__ = "receivable_items"
    __table_args__ = (
        CheckConstraint("qty > 0", name="qty_pos"),
        CheckConstraint('"unitPrice" > 0', name="unit_price_pos"),
        CheckConstraint('"lineTotal" >= 0', name="line_total_nonneg"),
    )

    id = pk()
    receivable_id = fk("receivableId", "receivables.id", nullable=False)
    # null = cargo libre ("Otro").
    product_id = fk("productId", "products.id")
    product_name = Column("productName", String, nullable=False)
    unit_label = Column("unitLabel", String, nullable=True)
    qty = Column("qty", Numeric(10, 3), nullable=False)
    unit_price = Column("unitPrice", MONEY, nullable=False)
    line_total = Column("lineTotal", MONEY, nullable=False)
    created_at = created_at()
