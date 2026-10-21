"""Esquemas del cuaderno: fiado, anular y estado de cuenta (08 §B3 + §Agregados, 03 §3.10b)."""
from __future__ import annotations

import enum

from pydantic import ConfigDict, Field

from src.core import examples as ex
from src.core.schemas import ApiModel, IsoDate, Money, Qty3, RateOut, UtcDateTime
from src.db.enums import CustomerType, ReceivableSource, ReceivableStatus, ReceivableVoidReason


class FiadoLineIn(ApiModel):
    """Línea de catálogo (`productId`) o cargo libre “Otro” (sin `productId`: `name` y `unitPrice` obligatorios)."""

    product_id: str | None = None
    name: str | None = Field(default=None, max_length=120)
    qty: Qty3 = Field(description="> 0, hasta 3 decimales.")
    unit_price: Money | None = Field(default=None, description="Si se omite, sale del catálogo según el tipo del cliente.")


class FiadoIn(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {"productId": ex.EXAMPLE_PRODUCT_ID, "qty": "20"},
                    {"name": "Bolsa de hielo", "qty": "1", "unitPrice": "2.00"},
                ],
                "note": "Para el kiosko",
                "dueDate": "2026-10-28",
            }
        }
    )

    items: list[FiadoLineIn] = Field(description="Sin líneas → `EMPTY_ORDER`.")
    note: str | None = Field(default=None, max_length=300)
    due_date: IsoDate | None = Field(default=None, description="Si se omite: hoy + `creditDays` del cliente.")


class FiadoLineOut(ApiModel):
    product_id: str | None = None
    product_name: str
    unit_label: str | None = None
    qty: Qty3
    unit_price: Money
    line_total: Money


class CreditWarning(ApiModel):
    """Advertencia sin bloqueo (03 §3.10b): `code = CREDIT_LIMIT_EXCEEDED`, `meta{limit, openDebt}`."""

    code: str
    detail: str
    meta: dict[str, str]


_LINES_EXAMPLE = [
    {"productId": ex.EXAMPLE_PRODUCT_ID, "productName": "Pan canilla", "unitLabel": "unidad", "qty": "20", "unitPrice": "1.00", "lineTotal": "20.00"},
    {"productId": None, "productName": "Bolsa de hielo", "unitLabel": None, "qty": "1", "unitPrice": "2.00", "lineTotal": "2.00"},
]


class FiadoQuote(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": _LINES_EXAMPLE,
                "total": "22.00",
                "totalVes": "4013.90",
                "balanceBefore": "13.50",
                "balanceAfter": "35.50",
                "warning": None,
            }
        }
    )

    items: list[FiadoLineOut]
    total: Money
    total_ves: Money | None = None
    balance_before: Money
    balance_after: Money
    warning: CreditWarning | None = None


class ReceivableOut(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": ex.EXAMPLE_RECEIVABLE_ID,
                "customerId": ex.EXAMPLE_CUSTOMER_ID,
                "source": "MANUAL",
                "description": "Fiado",
                "amount": "22.00",
                "paidAmount": "0.00",
                "forgivenAmount": "0.00",
                "status": "OPEN",
                "issuedAt": ex.EXAMPLE_TS,
                "dueAt": "2026-10-29T03:59:59.999Z",
                "voidReason": None,
                "voidedBy": None,
                "voidedAt": None,
                "voidNote": None,
                "note": "Para el kiosko",
                "createdByUserId": ex.EXAMPLE_ADMIN_ID,
                "createdAt": ex.EXAMPLE_TS,
            }
        }
    )

    id: str
    customer_id: str
    source: ReceivableSource
    description: str | None = None
    amount: Money
    paid_amount: Money
    forgiven_amount: Money
    status: ReceivableStatus
    issued_at: UtcDateTime
    due_at: UtcDateTime
    void_reason: ReceivableVoidReason | None = None
    voided_by: str | None = None
    voided_at: UtcDateTime | None = None
    void_note: str | None = None
    note: str | None = None
    created_by_user_id: str | None = None
    created_at: UtcDateTime


class FiadoOut(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "receivable": ReceivableOut.model_config["json_schema_extra"]["example"],
                "items": _LINES_EXAMPLE,
                "balance": "35.50",
                "balanceVes": "6476.98",
                "warning": None,
            }
        }
    )

    receivable: ReceivableOut
    items: list[FiadoLineOut]
    balance: Money
    balance_ves: Money | None = None
    warning: CreditWarning | None = None


class VoidIn(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": {"reason": "Se anotó dos veces"}})

    reason: str = Field(min_length=3, max_length=300)


class ReceivableActionOut(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "receivable": {**ReceivableOut.model_config["json_schema_extra"]["example"], "status": "VOID", "voidReason": "VOIDED", "amount": "0.00"},
                "balance": "13.50",
                "balanceVes": "2463.08",
            }
        }
    )

    receivable: ReceivableOut
    balance: Money
    balance_ves: Money | None = None


# --------------------------------------------------------------------------- estado de cuenta
class StatementKind(str, enum.Enum):
    SALDO_ANTERIOR = "SALDO_ANTERIOR"
    FIADO = "FIADO"
    ABONO = "ABONO"
    REVERSO = "REVERSO"
    ANULACION = "ANULACION"
    CONDONACION = "CONDONACION"
    AJUSTE = "AJUSTE"
    DEVOLUCION = "DEVOLUCION"


class StatementCustomer(ApiModel):
    id: str
    contact_name: str
    business_name: str | None = None
    phone: str | None = None
    type: CustomerType


class StatementRow(ApiModel):
    seq: int
    at: UtcDateTime
    kind: StatementKind
    description: str
    amount: Money = Field(description="Efecto en el saldo: + sube la deuda, − la baja (03 §3.10b).")
    balance_after: Money
    actor_name: str | None = None
    receivable_id: str | None = None
    payment_id: str | None = None
    items: list[FiadoLineOut] | None = None


class StatementOut(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "customer": {"id": ex.EXAMPLE_CUSTOMER_ID, "contactName": "José Rodríguez", "businessName": "Abasto La Esquina", "phone": "+584242223344", "type": "WHOLESALE"},
                "from": "2026-10-01",
                "to": ex.EXAMPLE_DATE,
                "openingBalance": "0.00",
                "rows": [
                    {"seq": 1, "at": "2026-10-05T13:00:00.000Z", "kind": "SALDO_ANTERIOR", "description": "Saldo anterior", "amount": "13.50", "balanceAfter": "13.50", "actorName": ex.EXAMPLE_ADMIN_NAME, "receivableId": "r1a2b3c4d5e6f7g8h9j0k1l2", "paymentId": None, "items": None},
                    {"seq": 2, "at": ex.EXAMPLE_TS, "kind": "FIADO", "description": "Fiado: Pan canilla ×20, Bolsa de hielo ×1", "amount": "22.00", "balanceAfter": "35.50", "actorName": ex.EXAMPLE_ADMIN_NAME, "receivableId": ex.EXAMPLE_RECEIVABLE_ID, "paymentId": None, "items": _LINES_EXAMPLE},
                ],
                "closingBalance": "35.50",
                "closingBalanceVes": "6476.98",
                "rate": ex.EXAMPLE_RATE,
            }
        }
    )

    customer: StatementCustomer
    from_: IsoDate | None = Field(default=None, alias="from")
    to: IsoDate | None = None
    opening_balance: Money
    rows: list[StatementRow]
    closing_balance: Money
    closing_balance_ves: Money | None = None
    rate: RateOut | None = None
