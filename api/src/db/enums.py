"""Enums del modelo de datos (02). En la base: `SQLEnum(X, name="X")` con el nombre del miembro."""
from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    PRODUCTION = "PRODUCTION"
    DELIVERY = "DELIVERY"
    CUSTOMER = "CUSTOMER"


class CustomerType(str, enum.Enum):
    RETAIL = "RETAIL"
    WHOLESALE = "WHOLESALE"


class CustomerSegment(str, enum.Enum):
    HOTDOG = "HOTDOG"
    BODEGA = "BODEGA"
    CAFE_RESTAURANT = "CAFE_RESTAURANT"
    EVENTS = "EVENTS"
    OTHER = "OTHER"


class PaymentMode(str, enum.Enum):
    CASH = "CASH"
    CREDIT = "CREDIT"


class PriceType(str, enum.Enum):
    WHOLESALE = "WHOLESALE"
    RETAIL = "RETAIL"


class OrderChannel(str, enum.Enum):
    APP = "APP"
    BACKOFFICE = "BACKOFFICE"


class OrderStatus(str, enum.Enum):
    AWAITING_PAYMENT = "AWAITING_PAYMENT"
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    READY = "READY"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class OrderPaymentStatus(str, enum.Enum):
    UNPAID = "UNPAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    ON_CREDIT = "ON_CREDIT"
    REFUNDED = "REFUNDED"


class FulfillmentType(str, enum.Enum):
    ASAP = "ASAP"
    SCHEDULED = "SCHEDULED"


class Currency(str, enum.Enum):
    USD = "USD"
    VES = "VES"


class PaymentMethodType(str, enum.Enum):
    MOBILE_PAYMENT = "MOBILE_PAYMENT"
    BANK_TRANSFER = "BANK_TRANSFER"
    ZELLE = "ZELLE"
    CASH = "CASH"


class PaymentPurpose(str, enum.Enum):
    ORDER = "ORDER"
    WALLET_TOPUP = "WALLET_TOPUP"
    MANUAL = "MANUAL"


class PaymentStatus(str, enum.Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVERSED = "REVERSED"


class ReversalKind(str, enum.Enum):
    BANK_RETURN = "BANK_RETURN"
    ENTRY_ERROR = "ENTRY_ERROR"


class WalletMovementType(str, enum.Enum):
    TOPUP_APPROVED = "TOPUP_APPROVED"
    ORDER_CHARGE = "ORDER_CHARGE"
    ORDER_REFUND = "ORDER_REFUND"
    RECEIVABLE_SETTLEMENT = "RECEIVABLE_SETTLEMENT"
    RECEIVABLE_REFUND = "RECEIVABLE_REFUND"
    PAYMENT_REVERSAL = "PAYMENT_REVERSAL"
    WALLET_PAYOUT = "WALLET_PAYOUT"
    ADJUSTMENT = "ADJUSTMENT"


class ReceivableSource(str, enum.Enum):
    ORDER = "ORDER"
    MANUAL = "MANUAL"
    OPENING_BALANCE = "OPENING_BALANCE"
    PAYMENT_REVERSAL = "PAYMENT_REVERSAL"


class ReceivableStatus(str, enum.Enum):
    OPEN = "OPEN"
    PARTIAL = "PARTIAL"
    PAID = "PAID"
    VOID = "VOID"


class ReceivableVoidReason(str, enum.Enum):
    ORDER_CANCELLED = "ORDER_CANCELLED"
    REDUCED = "REDUCED"
    VOIDED = "VOIDED"
    FORGIVEN = "FORGIVEN"


class CashTransactionType(str, enum.Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    ADJUSTMENT = "ADJUSTMENT"


class RateType(str, enum.Enum):
    BCV = "BCV"
    MANUAL = "MANUAL"


class FilePurpose(str, enum.Enum):
    PRODUCT_IMAGE = "PRODUCT_IMAGE"
    PAYMENT_PROOF = "PAYMENT_PROOF"


class DeviceApp(str, enum.Enum):
    """App que registra el token. En la base se guarda el **valor** (`cliente`, `delivery`, `admin-web`)."""

    CLIENTE = "cliente"
    DELIVERY = "delivery"
    ADMIN_WEB = "admin-web"
