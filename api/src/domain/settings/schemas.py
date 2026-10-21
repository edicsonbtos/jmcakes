"""Esquemas de `settings.py` (08 §B1). En E1 el panel solo edita `business` y `credit`."""
from __future__ import annotations

from pydantic import ConfigDict, Field

from src.core.schemas import ApiModel, Money


class PublicSettings(ApiModel):
    """`GET /settings/public` (forma exacta de 08)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "businessName": "Panadería",
                "phone": "+582125551234",
                "whatsapp": "+584141234567",
                "address": "Av. Sucre, Catia, Caracas",
                "openingTime": "06:00",
                "closingTime": "19:00",
                "minLeadMinutes": 60,
                "maxDaysAhead": 30,
                "deliveryFeeUsd": "0.00",
                "minPayWindowMinutes": 30,
                "minVersionCliente": 1,
                "minVersionDelivery": 1,
            }
        }
    )

    business_name: str
    phone: str
    whatsapp: str
    address: str
    opening_time: str
    closing_time: str
    min_lead_minutes: int
    max_days_ahead: int
    delivery_fee_usd: Money
    min_pay_window_minutes: int
    min_version_cliente: int
    min_version_delivery: int


class BusinessSection(ApiModel):
    name: str
    phone: str
    whatsapp: str
    address: str


class CreditSection(ApiModel):
    default_days: int
    block_overdue_days: int


class AdminSettings(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "business": {"name": "Panadería", "phone": "+582125551234", "whatsapp": "+584141234567", "address": "Av. Sucre, Catia, Caracas"},
                "credit": {"defaultDays": 7, "blockOverdueDays": 7},
            }
        }
    )

    business: BusinessSection
    credit: CreditSection


class BusinessSectionPatch(ApiModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    phone: str | None = Field(default=None, max_length=32)
    whatsapp: str | None = Field(default=None, max_length=32)
    address: str | None = Field(default=None, max_length=300)


class CreditSectionPatch(ApiModel):
    default_days: int | None = Field(default=None, ge=0, le=365)
    block_overdue_days: int | None = Field(default=None, ge=0, le=365)


class AdminSettingsPatch(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": {"business": {"name": "Panadería La Canilla"}, "credit": {"defaultDays": 15}}})

    business: BusinessSectionPatch | None = None
    credit: CreditSectionPatch | None = None
