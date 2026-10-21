"""`GET /api/health` (P): `{status, version, db}`. Lo usa el healthcheck de Railway."""
from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.db.session import SessionLocal
from src.domain.auth.deps import PUBLIC, access
from src.domain.auth.schemas import HealthOut
from src.version import VERSION

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get(
    "/api/health",
    response_model=HealthOut,
    summary="Estado de la API y de la base de datos",
    responses={503: {"model": HealthOut, "description": "La base de datos no responde."}},
    **access(PUBLIC),
)
async def health():
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return HealthOut(status="ok", version=VERSION, db="ok")
    except Exception as exc:  # noqa: BLE001  (el healthcheck nunca lanza)
        logger.error("Healthcheck: la base no responde (%s)", exc.__class__.__name__)
        body = HealthOut(status="degraded", version=VERSION, db="error").model_dump(by_alias=True)
        return JSONResponse(status_code=503, content=body)
