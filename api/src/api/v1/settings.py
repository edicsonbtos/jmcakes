"""Configuración (08 §B1). Dueño: **B-E1a**. FND-E1 declara el contrato.

`/settings/public` alimenta el nombre del negocio en la barra superior (09 §E1).
"""
from __future__ import annotations

from fastapi import APIRouter

from src.core.errors import ErrorCode, error_responses, not_implemented
from src.db.enums import UserRole
from src.domain.auth.deps import PUBLIC, access
from src.domain.settings.schemas import AdminSettings, AdminSettingsPatch, PublicSettings

OWNER = "B-E1a"
router = APIRouter(tags=["settings"])
_A = access(UserRole.ADMIN)


@router.get("/settings/public", response_model=PublicSettings, summary="Datos públicos del negocio", **access(PUBLIC))
async def public_settings():
    not_implemented(OWNER)


@router.get(
    "/admin/settings",
    response_model=AdminSettings,
    summary="Configuración (negocio y crédito)",
    responses=error_responses(ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN),
    **_A,
)
async def get_admin_settings():
    not_implemented(OWNER)


@router.patch(
    "/admin/settings",
    response_model=AdminSettings,
    summary="Editar configuración por secciones",
    responses=error_responses(
        ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN, ErrorCode.INVALID_SETTINGS, ErrorCode.VALIDATION_ERROR
    ),
    **_A,
)
async def patch_admin_settings(body: AdminSettingsPatch):
    not_implemented(OWNER)
