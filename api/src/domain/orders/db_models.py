"""Pedidos (02 §Pedidos). La tabla existe desde E1; sus endpoints y servicios llegan en E2.

Quién escribe qué: B3 (`MoneyService` y ledger) `paidFromWallet`, `roundingAdjustment`,
`paymentStatus`, `expiresAt` y la CxC; B2 el estado, los `*At`, `dueAt`, `assignedDriverId`
y `order_events`.
"""
from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, DateTime, Index, Integer, Sequence, String, UniqueConstraint

from src.db.base import Base
from src.db.columns import MONEY, created_at, enum_col, fk, pk, updated_at
from src.db.enums import FulfillmentType, OrderChannel, OrderPaymentStatus, OrderStatus, PaymentMode

ORDER_NUMBER_SEQ = Sequence("order_number_seq", start=1001)


class OrderDB(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("customerId", "idempotencyKey", name="uq_orders_customer_idem"),
        CheckConstraint("subtotal >= 0", name="subtotal_nonneg"),
        CheckConstraint('"deliveryFee" >= 0', name="delivery_fee_nonneg"),
        CheckConstraint("total >= 0", name="total_nonneg"),
        CheckConstraint('"paidFromWallet" >= 0', name="paid_from_wallet_nonneg"),
        CheckConstraint('"roundingAdjustment" >= 0', name="rounding_nonneg"),
        Index("ix_orders_status_due_at", "status", "dueAt"),
        Index("ix_orders_customer_id_created_at", "customerId", "createdAt"),
        Index("ix_orders_assigned_driver_id_status", "assignedDriverId", "status"),
        Index("ix_orders_status_expires_at", "status", "expiresAt"),
    )

    id = pk()
    number = Column(
        "number", Integer, ORDER_NUMBER_SEQ, nullable=False, unique=True, server_default=ORDER_NUMBER_SEQ.next_value()
    )
    # Índices cubiertos por los compuestos de arriba.
    customer_id = fk("customerId", "customers.id", nullable=False, index=False)
    created_by_user_id = fk("createdByUserId", "users.id")
    channel = enum_col("channel", OrderChannel, nullable=False)
    status = enum_col("status", OrderStatus, nullable=False)
    payment_mode = enum_col("paymentMode", PaymentMode, nullable=False)
    payment_status = enum_col("paymentStatus", OrderPaymentStatus, nullable=False)
    fulfillment_type = enum_col("fulfillmentType", FulfillmentType, nullable=False)
    due_at = Column("dueAt", DateTime, nullable=False)
    subtotal = Column("subtotal", MONEY, nullable=False)
    delivery_fee = Column("deliveryFee", MONEY, nullable=False, default=0)
    total = Column("total", MONEY, nullable=False)
    paid_from_wallet = Column("paidFromWallet", MONEY, nullable=False, default=0)
    rounding_adjustment = Column("roundingAdjustment", MONEY, nullable=False, default=0)
    delivery_address_text = Column("deliveryAddressText", String, nullable=True)
    delivery_address_reference = Column("deliveryAddressReference", String, nullable=True)
    contact_phone = Column("contactPhone", String, nullable=True)
    notes = Column("notes", String, nullable=True)
    assigned_driver_id = fk("assignedDriverId", "users.id", index=False)
    idempotency_key = Column("idempotencyKey", String, nullable=True)
    request_hash = Column("requestHash", String, nullable=True)
    expires_at = Column("expiresAt", DateTime, nullable=True)
    confirmed_at = Column("confirmedAt", DateTime, nullable=True)
    preparing_at = Column("preparingAt", DateTime, nullable=True)
    ready_at = Column("readyAt", DateTime, nullable=True)
    out_for_delivery_at = Column("outForDeliveryAt", DateTime, nullable=True)
    delivered_at = Column("deliveredAt", DateTime, nullable=True)
    cancelled_at = Column("cancelledAt", DateTime, nullable=True)
    cancel_reason = Column("cancelReason", String, nullable=True)
    cancelled_by_user_id = fk("cancelledByUserId", "users.id")
    created_at = created_at()
    updated_at = updated_at()


class OrderItemDB(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("qty >= 0", name="qty_nonneg"),
        CheckConstraint('"unitPrice" >= 0', name="unit_price_nonneg"),
        CheckConstraint('"lineTotal" >= 0', name="line_total_nonneg"),
    )

    id = pk()
    order_id = fk("orderId", "orders.id", nullable=False)
    product_id = fk("productId", "products.id", nullable=False)
    product_name = Column("productName", String, nullable=False)
    unit_label = Column("unitLabel", String, nullable=False)
    unit_price = Column("unitPrice", MONEY, nullable=False)
    qty = Column("qty", Integer, nullable=False)
    line_total = Column("lineTotal", MONEY, nullable=False)
    created_at = created_at()


class OrderEventDB(Base):
    __tablename__ = "order_events"

    id = pk()
    order_id = fk("orderId", "orders.id", nullable=False)
    from_status = enum_col("fromStatus", OrderStatus, nullable=True)
    to_status = enum_col("toStatus", OrderStatus, nullable=False)
    # null = sistema.
    actor_user_id = fk("actorUserId", "users.id")
    note = Column("note", String, nullable=True)
    created_at = created_at()
