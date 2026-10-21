"""Esquemas de abonos y reversos del panel (08 §B3 + §Agregados, 03 §3.4, §3.7 y §3.10b).

En E1 un abono es un pago `purpose = MANUAL` que nace APPROVED. `orderId` llega con E2.
"""
from __future__ import annotations

from typing import Any

from pydantic import ConfigDict, Field

from src.core import examples as ex
from src.core.schemas import ApiModel, IsoDate, Money, Rate4, RateOut, UtcDateTime
from src.db.enums import Currency, PaymentPurpose, PaymentStatus, ReversalKind


class ManualPaymentIn(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "paymentMethodId": ex.EXAMPLE_METHOD_ID,
                "bankAccountId": ex.EXAMPLE_BANK_ACCOUNT_ID,
                "localCurrency": "VES",
                "amountLocal": "1824.50",
                "paidOn": ex.EXAMPLE_DATE,
                "reference": "004512",
                "note": "Abono del martes",
            }
        }
    )

    payment_method_id: str
    bank_account_id: str
    local_currency: Currency
    amount_local: Money = Field(description="> 0, en la moneda del método.")
    paid_on: IsoDate = Field(description="Día del pago (Caracas); no puede ser futuro.")
    bcv_rate_used: Rate4 | None = Field(default=None, description="Solo VES: corrige la tasa de `paidOn`.")
    reference: str | None = Field(default=None, max_length=60, description="Obligatoria salvo en métodos de efectivo.")
    note: str | None = Field(default=None, max_length=300)


class AdminPayment(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": ex.EXAMPLE_PAYMENT_ID,
                "customerId": ex.EXAMPLE_CUSTOMER_ID,
                "purpose": "MANUAL",
                "paymentMethodId": ex.EXAMPLE_METHOD_ID,
                "bankAccountId": ex.EXAMPLE_BANK_ACCOUNT_ID,
                "amountLocal": "1824.50",
                "localCurrency": "VES",
                "bcvRateUsed": "182.4500",
                "amountUsd": "10.00",
                "reference": "004512",
                "paidOn": ex.EXAMPLE_DATE,
                "senderName": None,
                "status": "APPROVED",
                "approvedBy": ex.EXAMPLE_ADMIN_ID,
                "approvedAt": ex.EXAMPLE_TS,
                "reversedBy": None,
                "reversedAt": None,
                "reversalReason": None,
                "reversalKind": None,
                "correctedFrom": None,
                "createdByUserId": ex.EXAMPLE_ADMIN_ID,
                "createdAt": ex.EXAMPLE_TS,
            }
        }
    )

    id: str
    customer_id: str
    purpose: PaymentPurpose
    payment_method_id: str
    bank_account_id: str
    amount_local: Money
    local_currency: Currency
    bcv_rate_used: Rate4 | None = None
    amount_usd: Money
    reference: str | None = None
    paid_on: IsoDate
    sender_name: str | None = None
    status: PaymentStatus
    approved_by: str | None = None
    approved_at: UtcDateTime | None = None
    reversed_by: str | None = None
    reversed_at: UtcDateTime | None = None
    reversal_reason: str | None = None
    reversal_kind: ReversalKind | None = None
    corrected_from: dict[str, Any] | None = None
    created_by_user_id: str | None = None
    created_at: UtcDateTime


class ManualPaymentQuote(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amountUsd": "10.00",
                "rate": {"date": ex.EXAMPLE_DATE, "value": "182.4500", "rateType": "BCV", "isFallback": False},
                "balanceBefore": "35.50",
                "balanceAfter": "25.50",
            }
        }
    )

    amount_usd: Money
    rate: RateOut | None = Field(default=None, description="null en abonos en USD.")
    balance_before: Money
    balance_after: Money


class PaymentActionOut(ApiModel):
    """Respuesta de abonar o revertir: el pago y el saldo resultante del cliente."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"payment": AdminPayment.model_config["json_schema_extra"]["example"], "balance": "25.50", "balanceVes": "4652.48"}
        }
    )

    payment: AdminPayment
    balance: Money
    balance_ves: Money | None = None


class ReverseIn(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": {"reason": "Lo cargué al cliente equivocado", "kind": "ENTRY_ERROR"}})

    reason: str = Field(min_length=3, max_length=300)
    kind: ReversalKind = Field(description="BANK_RETURN: el banco lo devolvió · ENTRY_ERROR: error de carga (libera la referencia).")
