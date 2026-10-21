"""Clientes del panel (08 §B1 + §Agregados, 09 §E1). Dueño: **B-E1a**. FND-E1 declara el contrato.

- Las columnas de saldo vienen de `FinanceQueries` (B-E1b) y el saldo anterior de `MoneyService.open_balance`.
- Bloqueo y desbloqueo llegan después de E1.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Header, Query, UploadFile

from src.core.errors import ErrorCode, error_responses, not_implemented
from src.core.schemas import Page
from src.db.enums import CustomerType, PaymentMode, UserRole
from src.domain.auth.deps import access
from src.domain.customers.schemas import (
    AdminCustomer,
    CustomerCreate,
    CustomerCreditIn,
    CustomerUpdate,
    ImportApplyIn,
    ImportApplyOut,
    ImportPreview,
)

OWNER = "B-E1a"
router = APIRouter(prefix="/admin/customers", tags=["customers"])
_A = access(UserRole.ADMIN)
_ERR = error_responses(ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN, ErrorCode.VALIDATION_ERROR)
_ERR_ID = error_responses(ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN, ErrorCode.NOT_FOUND, ErrorCode.VALIDATION_ERROR)


@router.get("", response_model=Page[AdminCustomer], summary="Clientes con su saldo", responses=_ERR, **_A)
async def list_customers(
    query: Annotated[
        str | None,
        Query(max_length=80, description="Nombre, negocio, cédula/RIF o apodo (sin acentos ni mayúsculas); teléfono por dígitos."),
    ] = None,
    type: Annotated[CustomerType | None, Query()] = None,
    payment_mode: Annotated[PaymentMode | None, Query(alias="paymentMode")] = None,
    has_debt: Annotated[bool | None, Query(alias="hasDebt")] = None,
    overdue: Annotated[bool | None, Query()] = None,
    blocked: Annotated[bool | None, Query()] = None,
    sort: Annotated[str, Query(pattern="^(debt_desc|name)$")] = "debt_desc",
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
):
    not_implemented(OWNER)


@router.post("", response_model=AdminCustomer, status_code=201, summary="Nuevo cliente (con saldo anterior opcional)", responses=_ERR, **_A)
async def create_customer(body: CustomerCreate):
    not_implemented(OWNER)


@router.post(
    "/import/preview",
    response_model=ImportPreview,
    summary="Importar clientes por CSV: vista previa con errores por fila",
    responses=error_responses(ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN, ErrorCode.VALIDATION_ERROR),
    **_A,
)
async def import_preview(file: Annotated[UploadFile, File(description="CSV UTF-8 o Windows-1252, `,` o `;`, ≤ 1 MB.")]):
    not_implemented(OWNER)


@router.post(
    "/import/apply",
    response_model=ImportApplyOut,
    summary="Importar clientes por CSV: confirmar",
    responses=error_responses(
        ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN, ErrorCode.IMPORT_PREVIEW_EXPIRED, ErrorCode.VALIDATION_ERROR
    ),
    **_A,
)
async def import_apply(
    body: ImportApplyIn,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key", max_length=128)] = None,
):
    not_implemented(OWNER)


@router.get("/{id}", response_model=AdminCustomer, summary="Ficha del cliente", responses=_ERR_ID, **_A)
async def get_customer(id: str):
    not_implemented(OWNER)


@router.patch("/{id}", response_model=AdminCustomer, summary="Editar datos del cliente", responses=_ERR_ID, **_A)
async def update_customer(id: str, body: CustomerUpdate):
    not_implemented(OWNER)


@router.post("/{id}/credit", response_model=AdminCustomer, summary="Límite y días de crédito", responses=_ERR_ID, **_A)
async def update_credit(id: str, body: CustomerCreditIn):
    not_implemented(OWNER)
