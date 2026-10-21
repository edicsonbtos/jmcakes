"""Pagos del panel (08 §B3). Dueño: **B-E1b**. FND-E1 declara el contrato.

En E1 solo `reverse` (revertir un abono). Reportar, tomar, aprobar y rechazar llegan en E4.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header

from src.core.errors import ErrorCode, error_responses, not_implemented
from src.db.enums import UserRole
from src.domain.auth.deps import access
from src.domain.payments.schemas import PaymentActionOut, ReverseIn

OWNER = "B-E1b"
router = APIRouter(prefix="/admin/payments", tags=["payments"])


@router.post(
    "/{id}/reverse",
    response_model=PaymentActionOut,
    summary="Revertir un abono (BANK_RETURN o ENTRY_ERROR)",
    responses=error_responses(
        ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN, ErrorCode.NOT_FOUND, ErrorCode.PAYMENT_NOT_REVERSIBLE,
        ErrorCode.VALIDATION_ERROR,
    ),
    **access(UserRole.ADMIN),
)
async def reverse_payment(
    id: str,
    body: ReverseIn,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key", max_length=128)] = None,
):
    not_implemented(OWNER)
