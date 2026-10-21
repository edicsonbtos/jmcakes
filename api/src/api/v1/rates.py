"""Tasa BCV del día (08 §B3, 03 §0). Dueño: **B-E1b**. FND-E1 declara el contrato.

`RateService.rate_for` y `sync_daily_rate` (en `domain/exchange_rates/service.py`) ya son reales.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import ConfigDict

from src.core.errors import ErrorCode, error_responses, not_implemented
from src.core.schemas import Page, RateOut
from src.db.enums import UserRole
from src.domain.auth.deps import PUBLIC, access
from src.domain.exchange_rates.schemas import ExchangeRateOut, ManualRateIn, RateSyncOut, rate_example

OWNER = "B-E1b"
router = APIRouter(tags=["rates"])
_A = access(UserRole.ADMIN)


class TodayRateOut(RateOut):
    model_config = ConfigDict(json_schema_extra={"example": rate_example()})


@router.get(
    "/rates/today",
    response_model=TodayRateOut,
    summary="Tasa de hoy (Caracas)",
    responses=error_responses(ErrorCode.RATE_UNAVAILABLE),
    **access(PUBLIC),
)
async def rates_today():
    not_implemented(OWNER)


@router.get(
    "/admin/rates",
    response_model=Page[ExchangeRateOut],
    summary="Historial de tasas",
    responses=error_responses(ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN),
    **_A,
)
async def list_rates(
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 60,
):
    not_implemented(OWNER)


@router.post(
    "/admin/rates/manual",
    response_model=ExchangeRateOut,
    summary="Fijar la tasa a mano (manda sobre la BCV de ese día)",
    responses=error_responses(ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN, ErrorCode.VALIDATION_ERROR),
    **_A,
)
async def set_manual_rate(body: ManualRateIn):
    not_implemented(OWNER)


@router.post(
    "/admin/rates/sync",
    response_model=RateSyncOut,
    summary="Sincronizar la tasa BCV de hoy desde la fuente oficial",
    responses=error_responses(ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN, ErrorCode.SERVICE_UNAVAILABLE),
    **_A,
)
async def sync_rate():
    not_implemented(OWNER)
