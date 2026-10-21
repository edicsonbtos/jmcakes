"""Métodos de cobro y cuentas bancarias del panel (08 §B3). Dueño: **B-E1b**. FND-E1 declara el contrato.

En E1 solo las rutas de admin; `GET /payment-methods` (cliente) llega en E4.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from src.core.errors import ErrorCode, error_responses, not_implemented
from src.core.schemas import Page
from src.db.enums import UserRole
from src.domain.auth.deps import access
from src.domain.payment_methods.schemas import (
    AdminPaymentMethod,
    BankAccountCreate,
    BankAccountOut,
    BankAccountUpdate,
    PaymentMethodCreate,
    PaymentMethodUpdate,
)

OWNER = "B-E1b"
router = APIRouter(prefix="/admin", tags=["payment-methods"])
_A = access(UserRole.ADMIN)
_ERR = error_responses(ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN, ErrorCode.VALIDATION_ERROR)
_ERR_ID = error_responses(ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN, ErrorCode.NOT_FOUND, ErrorCode.VALIDATION_ERROR)


@router.get("/payment-methods", response_model=Page[AdminPaymentMethod], summary="Métodos de cobro con sus cuentas", responses=_ERR, **_A)
async def list_payment_methods(include_inactive: Annotated[bool, Query(alias="includeInactive")] = True):
    not_implemented(OWNER)


@router.post("/payment-methods", response_model=AdminPaymentMethod, status_code=201, summary="Crear método de cobro", responses=_ERR, **_A)
async def create_payment_method(body: PaymentMethodCreate):
    not_implemented(OWNER)


@router.patch("/payment-methods/{id}", response_model=AdminPaymentMethod, summary="Editar, ordenar o desactivar método", responses=_ERR_ID, **_A)
async def update_payment_method(id: str, body: PaymentMethodUpdate):
    not_implemented(OWNER)


@router.get("/bank-accounts", response_model=Page[BankAccountOut], summary="Cuentas de cobro", responses=_ERR, **_A)
async def list_bank_accounts(payment_method_id: Annotated[str | None, Query(alias="paymentMethodId")] = None):
    not_implemented(OWNER)


@router.post(
    "/bank-accounts",
    response_model=BankAccountOut,
    status_code=201,
    summary="Crear cuenta de cobro ligada a una cuenta del negocio",
    responses=error_responses(
        ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN, ErrorCode.PAYMENT_ACCOUNT_MISMATCH, ErrorCode.VALIDATION_ERROR
    ),
    **_A,
)
async def create_bank_account(body: BankAccountCreate):
    not_implemented(OWNER)


@router.patch("/bank-accounts/{id}", response_model=BankAccountOut, summary="Editar o desactivar cuenta de cobro", responses=_ERR_ID, **_A)
async def update_bank_account(id: str, body: BankAccountUpdate):
    not_implemented(OWNER)
