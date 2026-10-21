"""Auditoría (08 §B1). Dueño: **B-E1a**. FND-E1 declara el contrato."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from src.core.errors import ErrorCode, error_responses, not_implemented
from src.core.schemas import Page
from src.db.enums import UserRole
from src.domain.audit.schemas import AuditLogOut
from src.domain.auth.deps import access

OWNER = "B-E1a"
router = APIRouter(prefix="/admin", tags=["audit"])


@router.get(
    "/audit",
    response_model=Page[AuditLogOut],
    summary="Registro de auditoría",
    responses=error_responses(ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN, ErrorCode.VALIDATION_ERROR),
    **access(UserRole.ADMIN),
)
async def list_audit(
    entity: Annotated[str | None, Query(max_length=60)] = None,
    entity_id: Annotated[str | None, Query(alias="entityId", max_length=60)] = None,
    actor: Annotated[str | None, Query(max_length=60, description="Id del usuario que actuó.")] = None,
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
):
    not_implemented(OWNER)
