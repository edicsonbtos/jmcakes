"""Esquemas de `customers.py` (08 §B1 + §Agregados, 09 §E1).

`walletBalance` es la columna; `openDebt`, `overdueDebt`, `balance` (= openDebt − walletBalance,
positivo = debe) y `balanceVes` son derivados de `FinanceQueries` y de `rate_for(hoy)`.
"""
from __future__ import annotations

from typing import Any

from pydantic import ConfigDict, Field

from src.core import examples as ex
from src.core.schemas import ApiModel, Money, UtcDateTime
from src.db.enums import CustomerSegment, CustomerType, PaymentMode

_CUSTOMER_EXAMPLE = {
    "id": ex.EXAMPLE_CUSTOMER_ID,
    "userId": None,
    "type": "WHOLESALE",
    "segment": "BODEGA",
    "businessName": "Abasto La Esquina",
    "contactName": "José Rodríguez",
    "phone": "+584242223344",
    "idDocument": "V-14.567.890",
    "addressText": "Av. Baralt, Catia, Caracas",
    "addressReference": "Frente a la panadería vieja",
    "paymentMode": "CASH",
    "creditLimit": "0.00",
    "creditDays": 7,
    "walletBalance": "0.00",
    "openDebt": "35.50",
    "overdueDebt": "0.00",
    "balance": "35.50",
    "balanceVes": "6476.98",
    "isBlocked": False,
    "blockedReason": None,
    "notes": "el del abasto de la esquina",
    "createdAt": "2026-10-01T12:00:00.000Z",
    "updatedAt": ex.EXAMPLE_TS,
}


class AdminCustomer(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": _CUSTOMER_EXAMPLE})

    id: str
    user_id: str | None = None
    type: CustomerType
    segment: CustomerSegment | None = None
    business_name: str | None = None
    contact_name: str
    phone: str | None = None
    id_document: str | None = None
    address_text: str | None = None
    address_reference: str | None = None
    payment_mode: PaymentMode
    credit_limit: Money
    credit_days: int
    wallet_balance: Money
    open_debt: Money
    overdue_debt: Money
    balance: Money
    balance_ves: Money | None = None
    is_blocked: bool
    blocked_reason: str | None = None
    notes: str | None = None
    created_at: UtcDateTime
    updated_at: UtcDateTime


class CustomerCreate(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "RETAIL",
                "contactName": "Carmen Pérez",
                "phone": "0414-555.12.34",
                "notes": "la del kiosko",
                "openingBalance": "50.00",
                "openingNote": "Deuda del cuaderno",
            }
        }
    )

    type: CustomerType = Field(description="Obligatorio: decide el precio del fiado (detal o mayor).")
    segment: CustomerSegment | None = None
    business_name: str | None = Field(default=None, max_length=120)
    contact_name: str = Field(min_length=1, max_length=120)
    phone: str | None = Field(default=None, max_length=32, description="Se normaliza a E.164.")
    id_document: str | None = Field(default=None, max_length=32)
    address_text: str | None = Field(default=None, max_length=300)
    address_reference: str | None = Field(default=None, max_length=300)
    notes: str | None = Field(default=None, max_length=500, description="Apodo u observaciones; es buscable.")
    credit_limit: Money | None = Field(default=None, description="≥ 0; por defecto 0 (sin advertencia).")
    credit_days: int | None = Field(default=None, ge=0, le=365, description="Por defecto `credit.defaultDays`.")
    opening_balance: Money | None = Field(default=None, description="> 0 = deuda; < 0 = saldo a favor (03 §3.10b).")
    opening_note: str | None = Field(default=None, max_length=300)


class CustomerUpdate(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": {"businessName": "Kiosko Carmen", "notes": "la del kiosko"}})

    type: CustomerType | None = None
    segment: CustomerSegment | None = None
    business_name: str | None = Field(default=None, max_length=120)
    contact_name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = Field(default=None, max_length=32)
    id_document: str | None = Field(default=None, max_length=32)
    address_text: str | None = Field(default=None, max_length=300)
    address_reference: str | None = Field(default=None, max_length=300)
    notes: str | None = Field(default=None, max_length=500)


class CustomerCreditIn(ApiModel):
    """En E1 solo se guardan `creditLimit` y `creditDays` (`paymentMode` queda CASH)."""

    model_config = ConfigDict(json_schema_extra={"example": {"creditLimit": "100.00", "creditDays": 15}})

    payment_mode: PaymentMode | None = None
    credit_limit: Money
    credit_days: int = Field(ge=0, le=365)


class ImportRow(ApiModel):
    line: int
    data: dict[str, Any]
    errors: list[str]


class ImportPreview(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rows": [
                    {
                        "line": 2,
                        "data": {"contactName": "Luis Medina", "phone": "+584121112233", "type": "RETAIL", "openingBalance": "12.50", "notes": "el del carrito"},
                        "errors": [],
                    },
                    {
                        "line": 3,
                        "data": {"contactName": "", "phone": "0412", "type": "RETAIL", "openingBalance": "0.00"},
                        "errors": ["Falta el nombre", "Teléfono inválido"],
                    },
                ],
                "validCount": 1,
                "errorCount": 1,
                "totalDebt": "12.50",
                "previewToken": "imp_7c2e9a1f4b8d3e6a",
            }
        }
    )

    rows: list[ImportRow]
    valid_count: int
    error_count: int
    total_debt: Money
    preview_token: str


class ImportApplyIn(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": {"previewToken": "imp_7c2e9a1f4b8d3e6a"}})

    preview_token: str = Field(min_length=1)


class ImportSkipped(ApiModel):
    line: int
    reason: str


class ImportApplyOut(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"created": 1, "skipped": [{"line": 3, "reason": "Falta el nombre"}]}}
    )

    created: int
    skipped: list[ImportSkipped]
