"""Cuaderno del panel: fiado, abono, anular y estado de cuenta (08 §B3 + §Agregados, 03 §3.10b).

Dueño: **B-E1b**. FND-E1 declara el contrato. `Idempotency-Key` obligatorio en fiado y abono
(scopes `admin.fiado` y `admin.manual_payment` en `idempotency_records`). Cargos, ajustes,
devoluciones y condonar llegan después de E1.
"""
from __future__ import annotations

import enum
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Header, Query

from src.core.errors import ErrorCode, error_responses, not_implemented
from src.db.enums import UserRole
from src.domain.auth.deps import access
from src.domain.payments.schemas import ManualPaymentIn, ManualPaymentQuote, PaymentActionOut
from src.domain.receivables.schemas import (
    FiadoIn,
    FiadoOut,
    FiadoQuote,
    ReceivableActionOut,
    StatementOut,
    VoidIn,
)

OWNER = "B-E1b"
router = APIRouter(prefix="/admin", tags=["admin-money"])
_A = access(UserRole.ADMIN)
_AUTH = (ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN, ErrorCode.NOT_FOUND)

IdemKeyRequired = Annotated[
    str, Header(alias="Idempotency-Key", min_length=8, max_length=128, description="Se crea al abrir el formulario y se reutiliza en los reintentos.")
]
IdemKeyOptional = Annotated[str | None, Header(alias="Idempotency-Key", max_length=128)]


class StatementFormat(str, enum.Enum):
    json = "json"
    csv = "csv"
    whatsapp = "whatsapp"


@router.post(
    "/customers/{id}/fiado/quote",
    response_model=FiadoQuote,
    summary="Cotizar un fiado sin escribir (total en vivo)",
    responses=error_responses(*_AUTH, ErrorCode.EMPTY_ORDER, ErrorCode.INVALID_AMOUNT, ErrorCode.VALIDATION_ERROR),
    **_A,
)
async def fiado_quote(id: str, body: FiadoIn):
    not_implemented(OWNER)


@router.post(
    "/customers/{id}/fiado",
    response_model=FiadoOut,
    status_code=201,
    summary="Fiar productos (CxC MANUAL con líneas)",
    responses=error_responses(
        *_AUTH, ErrorCode.EMPTY_ORDER, ErrorCode.INVALID_AMOUNT, ErrorCode.IDEMPOTENCY_CONFLICT, ErrorCode.VALIDATION_ERROR
    ),
    **_A,
)
async def fiado(id: str, body: FiadoIn, idempotency_key: IdemKeyRequired):
    not_implemented(OWNER)


@router.post(
    "/customers/{id}/manual-payment/quote",
    response_model=ManualPaymentQuote,
    summary="Cotizar un abono sin escribir (para confirmar)",
    responses=error_responses(
        *_AUTH, ErrorCode.RATE_UNAVAILABLE, ErrorCode.INVALID_AMOUNT, ErrorCode.INVALID_PAID_ON,
        ErrorCode.PAYMENT_ACCOUNT_MISMATCH, ErrorCode.VALIDATION_ERROR,
    ),
    **_A,
)
async def manual_payment_quote(id: str, body: ManualPaymentIn):
    not_implemented(OWNER)


@router.post(
    "/customers/{id}/manual-payment",
    response_model=PaymentActionOut,
    status_code=201,
    summary="Registrar un abono (pago MANUAL aprobado)",
    responses=error_responses(
        *_AUTH, ErrorCode.RATE_UNAVAILABLE, ErrorCode.INVALID_AMOUNT, ErrorCode.INVALID_PAID_ON,
        ErrorCode.PAYMENT_ACCOUNT_MISMATCH, ErrorCode.DUPLICATE_REFERENCE, ErrorCode.IDEMPOTENCY_CONFLICT,
        ErrorCode.VALIDATION_ERROR,
    ),
    **_A,
)
async def manual_payment(id: str, body: ManualPaymentIn, idempotency_key: IdemKeyRequired):
    not_implemented(OWNER)


@router.post(
    "/receivables/{id}/void",
    response_model=ReceivableActionOut,
    summary="Anular un fiado o un saldo anterior (lo abonado se reaplica)",
    responses=error_responses(*_AUTH, ErrorCode.RECEIVABLE_NOT_VOIDABLE, ErrorCode.VALIDATION_ERROR),
    **_A,
)
async def void_receivable(id: str, body: VoidIn, idempotency_key: IdemKeyOptional = None):
    not_implemented(OWNER)


@router.get(
    "/customers/{id}/statement",
    response_model=StatementOut,
    summary="Estado de cuenta (JSON, CSV o texto para WhatsApp)",
    responses={
        **error_responses(*_AUTH, ErrorCode.VALIDATION_ERROR),
        200: {
            "description": "`format=json` → StatementOut · `csv` → text/csv · `whatsapp` → text/plain (≤ 1500 caracteres).",
            "content": {
                "text/csv": {"schema": {"type": "string"}, "example": "fecha,concepto,monto,saldo\n2026-10-21,Fiado,22.00,35.50\n"},
                "text/plain": {"schema": {"type": "string"}, "example": "Panadería\nJosé Rodríguez\nDebe $35.50 (Bs 6476.98 a tasa BCV del 21/10)"},
            },
        },
    },
    **_A,
)
async def statement(
    id: str,
    from_: Annotated[date | None, Query(alias="from", description="Día de Caracas (incluido).")] = None,
    to: Annotated[date | None, Query(description="Día de Caracas (incluido).")] = None,
    format: Annotated[StatementFormat, Query()] = StatementFormat.json,
):
    not_implemented(OWNER)
