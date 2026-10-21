"""Usuarios internos (08 §B1). Dueño: **B-E1a**. FND-E1 declara el contrato. En E1 solo ADMIN."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from src.core.errors import ErrorCode, error_responses, not_implemented
from src.core.schemas import Page
from src.db.enums import UserRole
from src.domain.auth.deps import access
from src.domain.users.schemas import AdminUser, ResetPasswordIn, ResetPasswordOut, UserCreate, UserUpdate

OWNER = "B-E1a"
router = APIRouter(prefix="/admin/users", tags=["users"])
_A = access(UserRole.ADMIN)
_ERR = error_responses(ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN, ErrorCode.VALIDATION_ERROR)
_ERR_ID = error_responses(ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN, ErrorCode.NOT_FOUND, ErrorCode.VALIDATION_ERROR)


@router.get("", response_model=Page[AdminUser], summary="Administradores", responses=_ERR, **_A)
async def list_users(
    role: Annotated[UserRole | None, Query()] = None,
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
):
    not_implemented(OWNER)


@router.post(
    "",
    response_model=AdminUser,
    status_code=201,
    summary="Crear administrador",
    responses=error_responses(
        ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN, ErrorCode.PHONE_TAKEN, ErrorCode.VALIDATION_ERROR
    ),
    **_A,
)
async def create_user(body: UserCreate):
    not_implemented(OWNER)


@router.patch("/{id}", response_model=AdminUser, summary="Editar o desactivar usuario", responses=_ERR_ID, **_A)
async def update_user(id: str, body: UserUpdate):
    not_implemented(OWNER)


@router.post(
    "/{id}/reset-password",
    response_model=ResetPasswordOut,
    summary="Restablecer la contraseña (temporal, revoca sesiones, mustChangePassword)",
    responses=_ERR_ID,
    **_A,
)
async def reset_password(id: str, body: ResetPasswordIn | None = None):
    not_implemented(OWNER)
