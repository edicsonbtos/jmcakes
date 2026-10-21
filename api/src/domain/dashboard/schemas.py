"""Inicio de E1 (`GET /admin/dashboard/summary`, 09 §E1 — Inicio). Solo los campos de E1; E2 agrega."""
from __future__ import annotations

from pydantic import ConfigDict

from src.core import examples as ex
from src.core.schemas import ApiModel, Money
from src.db.enums import Currency


class ReceivablesSummary(ApiModel):
    total: Money
    retail: Money
    wholesale: Money
    overdue: Money


class PaymentsByMethod(ApiModel):
    payment_method_id: str
    name: str
    currency: Currency
    total_local: Money
    total_usd: Money


class PaymentsToday(ApiModel):
    total_usd: Money
    by_method: list[PaymentsByMethod]


class CountTotal(ApiModel):
    count: int
    total_usd: Money


class TopDebtor(ApiModel):
    customer_id: str
    name: str
    balance: Money
    overdue_debt: Money


class DashboardSummary(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "receivables": {"total": "412.50", "retail": "120.00", "wholesale": "292.50", "overdue": "48.00"},
                "walletTotal": "15.00",
                "paymentsToday": {
                    "totalUsd": "60.00",
                    "byMethod": [
                        {"paymentMethodId": ex.EXAMPLE_METHOD_ID, "name": "Pago móvil", "currency": "VES", "totalLocal": "7298.00", "totalUsd": "40.00"},
                        {"paymentMethodId": "z1y2x3w4v5t6s7r8q9p0n1m2", "name": "Efectivo USD", "currency": "USD", "totalLocal": "20.00", "totalUsd": "20.00"},
                    ],
                },
                "reversalsToday": {"count": 0, "totalUsd": "0.00"},
                "fiadoToday": {"count": 3, "totalUsd": "54.00"},
                "overdueCustomersCount": 2,
                "topDebtors": [{"customerId": ex.EXAMPLE_CUSTOMER_ID, "name": "Abasto La Esquina", "balance": "35.50", "overdueDebt": "0.00"}],
            }
        }
    )

    receivables: ReceivablesSummary
    wallet_total: Money
    payments_today: PaymentsToday
    reversals_today: CountTotal
    fiado_today: CountTotal
    overdue_customers_count: int
    top_debtors: list[TopDebtor]
