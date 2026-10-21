"""Cuentas del negocio (08 §B3). Dueño: **B-E1b**. FND-E1 declara el contrato. Sin PATCH (08)."""
from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from src.core.errors import ErrorCode, error_responses, not_implemented
from src.core.schemas import Page
from src.db.enums import UserRole
from src.domain.auth.deps import access
from src.domain.cash_accounts.schemas import CashAccountCreate, CashAccountOut, CashAccountTransactionOut

OWNER = "B-E1b"
router = APIRouter(prefix="/admin/cash-accounts", tags=["cash-accounts"])
_A = access(UserRole.ADMIN)


@router.get(
    "",
    response_model=Page[CashAccountOut],
    summary="Cuentas del negocio con su saldo",
    responses=error_responses(ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN),
    **_A,
)
async def list_cash_accounts():
    not_implemented(OWNER)


@router.post(
    "",
    response_model=CashAccountOut,
    status_code=201,
    summary="Crear cuenta del negocio",
    responses=error_responses(ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN, ErrorCode.VALIDATION_ERROR),
    **_A,
)
async def create_cash_account(body: CashAccountCreate):
    not_implemented(OWNER)


@router.get(
    "/{id}/transactions",
    response_model=Page[CashAccountTransactionOut],
    summary="Movimientos de una cuenta del negocio (por seq)",
    responses=error_responses(ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN, ErrorCode.NOT_FOUND),
    **_A,
)
async def list_cash_account_transactions(
    id: str,
    from_: Annotated[date | None, Query(alias="from", description="Día de Caracas (incluido).")] = None,
    to: Annotated[date | None, Query(description="Día de Caracas (incluido).")] = None,
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
):
    not_implemented(OWNER)
