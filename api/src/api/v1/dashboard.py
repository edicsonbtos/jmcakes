"""Inicio del panel (09 §E1 — Inicio, día de Caracas). Dueño: **B-E1b**. FND-E1 declara el contrato."""
from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from src.core.errors import ErrorCode, error_responses, not_implemented
from src.db.enums import UserRole
from src.domain.auth.deps import access
from src.domain.dashboard.schemas import DashboardSummary

OWNER = "B-E1b"
router = APIRouter(prefix="/admin/dashboard", tags=["dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummary,
    summary="Totales del día: por cobrar, abonos, fiado, vencidos y top deudores",
    responses=error_responses(ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN, ErrorCode.VALIDATION_ERROR),
    **access(UserRole.ADMIN),
)
async def summary(date_: Annotated[date | None, Query(alias="date", description="Día de Caracas; por defecto hoy.")] = None):
    not_implemented(OWNER)
