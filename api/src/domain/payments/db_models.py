# Adaptado de OpenGravity: apps/bot/src/domain/payments/db_models.py
"""Pagos (02 §Pagos): base de estados + columnas de la panadería. Prohibido el borrado físico.

`uq_payments_bank_account_reference_live`: la transferencia la identifican la cuenta destino y la
referencia; solo un rechazo o un reverso por error de carga (`ENTRY_ERROR`) liberan la referencia.
"""
from __future__ import annotations

from sqlalchemy import JSON, CheckConstraint, Column, Date, DateTime, Index, String, UniqueConstraint, text

from src.db.base import Base
from src.db.columns import MONEY, RATE, created_at, enum_col, fk, pk, updated_at
from src.db.enums import Currency, PaymentPurpose, PaymentStatus, ReversalKind


class PaymentDB(Base):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("customerId", "idempotencyKey", name="uq_payments_customer_idem"),
        CheckConstraint('"amountLocal" > 0', name="amount_local_pos"),
        CheckConstraint('"amountUsd" > 0', name="amount_usd_pos"),
        CheckConstraint('"bcvRateUsed" IS NULL OR "bcvRateUsed" > 0', name="bcv_rate_pos"),
        Index(
            "uq_payments_bank_account_reference_live",
            "bankAccountId",
            "reference",
            unique=True,
            postgresql_where=text(
                "status <> 'REJECTED' AND reference IS NOT NULL "
                "AND NOT (status = 'REVERSED' AND \"reversalKind\" = 'ENTRY_ERROR')"
            ),
        ),
        Index("ix_payments_customer_id_created_at", "customerId", "createdAt"),
        Index("ix_payments_status_created_at", "status", "createdAt"),
        Index("ix_payments_approved_at", "approvedAt"),
        Index("ix_payments_reversed_at", "reversedAt"),
    )

    id = pk()
    customer_id = fk("customerId", "customers.id", nullable=False, index=False)
    created_by_user_id = fk("createdByUserId", "users.id")
    idempotency_key = Column("idempotencyKey", String, nullable=True)
    request_hash = Column("requestHash", String, nullable=True)
    purpose = enum_col("purpose", PaymentPurpose, nullable=False)
    order_id = fk("orderId", "orders.id")
    payment_method_id = fk("paymentMethodId", "payment_methods.id", nullable=False)
    bank_account_id = fk("bankAccountId", "bank_accounts.id", nullable=False)
    amount_local = Column("amountLocal", MONEY, nullable=False)
    local_currency = enum_col("localCurrency", Currency, nullable=False)
    bcv_rate_used = Column("bcvRateUsed", RATE, nullable=True)
    amount_usd = Column("amountUsd", MONEY, nullable=False)
    reference = Column("reference", String, nullable=True)
    paid_on = Column("paidOn", Date, nullable=False)
    sender_name = Column("senderName", String, nullable=True)
    proof_file_id = fk("proofFileId", "files.id")
    status = enum_col("status", PaymentStatus, nullable=False, default=PaymentStatus.PENDING_REVIEW)
    reviewing_admin_id = fk("reviewingAdminId", "users.id")
    in_review_at = Column("inReviewAt", DateTime, nullable=True)
    approved_by = fk("approvedBy", "users.id")
    approved_at = Column("approvedAt", DateTime, nullable=True)
    rejection_reason = Column("rejectionReason", String, nullable=True)
    reversed_by = fk("reversedBy", "users.id")
    reversed_at = Column("reversedAt", DateTime, nullable=True)
    reversal_reason = Column("reversalReason", String, nullable=True)
    reversal_kind = enum_col("reversalKind", ReversalKind, nullable=True)
    # Valores originales si el admin corrigió el monto o la tasa (03 §3.4).
    corrected_from = Column("correctedFrom", JSON, nullable=True)
    created_at = created_at()
    updated_at = updated_at()
