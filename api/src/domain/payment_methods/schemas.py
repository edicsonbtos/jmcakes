"""Esquemas de `payment_methods.py` (08 §B3). Sin borrado: se desactiva con `PATCH {isActive: false}`."""
from __future__ import annotations

from typing import Any

from pydantic import ConfigDict, Field

from src.core import examples as ex
from src.core.schemas import ApiModel, UtcDateTime
from src.db.enums import Currency, PaymentMethodType

_ACCOUNT_EXAMPLE = {
    "id": ex.EXAMPLE_BANK_ACCOUNT_ID,
    "paymentMethodId": ex.EXAMPLE_METHOD_ID,
    "accountLabel": "Banesco · 0414-1234567",
    "accountData": {"banco": "Banesco (0134)", "telefono": "0414-1234567", "cedula": "V-12.345.678"},
    "isDefault": True,
    "isActive": True,
    "cashAccountId": ex.EXAMPLE_CASH_ACCOUNT_ID,
    "createdAt": "2026-10-01T12:00:00.000Z",
    "updatedAt": "2026-10-01T12:00:00.000Z",
}


class BankAccountOut(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": _ACCOUNT_EXAMPLE})

    id: str
    payment_method_id: str
    account_label: str
    account_data: dict[str, Any] | None = None
    is_default: bool
    is_active: bool
    cash_account_id: str
    created_at: UtcDateTime
    updated_at: UtcDateTime


class AdminPaymentMethod(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": ex.EXAMPLE_METHOD_ID,
                "name": "Pago móvil",
                "type": "MOBILE_PAYMENT",
                "currency": "VES",
                "instructions": "Envía el pago móvil y anota la referencia.",
                "fields": {"banco": "Banesco (0134)", "telefono": "0414-1234567", "cedula": "V-12.345.678"},
                "isActive": True,
                "displayOrder": 1,
                "accounts": [_ACCOUNT_EXAMPLE],
                "createdAt": "2026-10-01T12:00:00.000Z",
                "updatedAt": "2026-10-01T12:00:00.000Z",
            }
        }
    )

    id: str
    name: str
    type: PaymentMethodType
    currency: Currency
    instructions: str | None = None
    fields: dict[str, Any] | None = None
    is_active: bool
    display_order: int
    accounts: list[BankAccountOut] = []
    created_at: UtcDateTime
    updated_at: UtcDateTime


class PaymentMethodCreate(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "Zelle", "type": "ZELLE", "currency": "USD", "displayOrder": 3}}
    )

    name: str = Field(min_length=1, max_length=60)
    type: PaymentMethodType
    currency: Currency
    instructions: str | None = Field(default=None, max_length=500)
    fields: dict[str, Any] | None = None
    is_active: bool = True
    display_order: int = 0


class PaymentMethodUpdate(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": {"isActive": False}})

    name: str | None = Field(default=None, min_length=1, max_length=60)
    instructions: str | None = Field(default=None, max_length=500)
    fields: dict[str, Any] | None = None
    is_active: bool | None = None
    display_order: int | None = None


class BankAccountCreate(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "paymentMethodId": ex.EXAMPLE_METHOD_ID,
                "accountLabel": "Banesco · 0414-1234567",
                "accountData": {"banco": "Banesco (0134)", "telefono": "0414-1234567"},
                "cashAccountId": ex.EXAMPLE_CASH_ACCOUNT_ID,
            }
        }
    )

    payment_method_id: str
    account_label: str = Field(min_length=1, max_length=80)
    account_data: dict[str, Any] | None = None
    is_default: bool = False
    is_active: bool = True
    cash_account_id: str


class BankAccountUpdate(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": {"isDefault": True}})

    account_label: str | None = Field(default=None, min_length=1, max_length=80)
    account_data: dict[str, Any] | None = None
    is_default: bool | None = None
    is_active: bool | None = None
    cash_account_id: str | None = None
