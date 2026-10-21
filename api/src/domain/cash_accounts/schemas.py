"""Esquemas de `cash_accounts.py` (08 §B3). Montos en la moneda de la cuenta, con signo."""
from __future__ import annotations

from typing import Any

from pydantic import ConfigDict, Field

from src.core import examples as ex
from src.core.schemas import ApiModel, Money, UtcDateTime
from src.db.enums import CashTransactionType, Currency


class CashAccountOut(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": ex.EXAMPLE_CASH_ACCOUNT_ID,
                "name": "Banco Bs",
                "accountType": "BANK",
                "currency": "VES",
                "balance": "18245.00",
                "balanceUsd": "100.00",
                "isActive": True,
                "displayOrder": 1,
                "createdAt": "2026-10-01T12:00:00.000Z",
                "updatedAt": ex.EXAMPLE_TS,
            }
        }
    )

    id: str
    name: str
    account_type: str
    currency: Currency
    balance: Money
    balance_usd: Money | None = Field(default=None, description="Equivalente en USD a la tasa de hoy (null sin tasa).")
    is_active: bool
    display_order: int
    created_at: UtcDateTime
    updated_at: UtcDateTime


class CashAccountCreate(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "Caja USD", "accountType": "CASH", "currency": "USD", "displayOrder": 3}}
    )

    name: str = Field(min_length=1, max_length=60)
    account_type: str = Field(min_length=1, max_length=30, description="BANK, CASH, ZELLE…")
    currency: Currency
    display_order: int = 0


class CashAccountTransactionOut(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "t2v7w1x6y0z5a9b4c8d3e7f1",
                "seq": 42,
                "transactionType": "INCOME",
                "amount": "1824.50",
                "balanceAfter": "18245.00",
                "referenceType": "payment",
                "referenceId": ex.EXAMPLE_PAYMENT_ID,
                "customerId": ex.EXAMPLE_CUSTOMER_ID,
                "customerName": "José Rodríguez",
                "approvedBy": ex.EXAMPLE_ADMIN_ID,
                "notes": None,
                "metadata": {"exchange_rate": "182.4500", "amount_usd": "10.00", "amount_ves": "1824.50"},
                "createdAt": ex.EXAMPLE_TS,
            }
        }
    )

    id: str
    seq: int
    transaction_type: CashTransactionType
    amount: Money
    balance_after: Money
    reference_type: str | None = None
    reference_id: str | None = None
    customer_id: str | None = None
    customer_name: str | None = None
    approved_by: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: UtcDateTime
