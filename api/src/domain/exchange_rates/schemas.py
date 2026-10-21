"""Esquemas de `rates.py` (08 §B3)."""
from __future__ import annotations

from typing import Any

from pydantic import ConfigDict

from src.core import examples as ex
from src.core.schemas import ApiModel, IsoDate, Rate4, UtcDateTime
from src.db.enums import RateType

_ROW_EXAMPLE = {
    "id": "x3y8z2a7b1c6d0e5f9g4h8j2",
    "date": ex.EXAMPLE_DATE,
    "rateType": "BCV",
    "value": "182.4500",
    "sourceUrl": "https://ve.dolarapi.com/v1/dolares/oficial",
    "fetchedAt": "2026-10-21T10:00:05.000Z",
    "createdAt": "2026-10-21T10:00:05.000Z",
}


class ExchangeRateOut(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": _ROW_EXAMPLE})

    id: str
    date: IsoDate
    rate_type: RateType
    value: Rate4
    source_url: str | None = None
    fetched_at: UtcDateTime
    created_at: UtcDateTime


class ManualRateIn(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": {"date": ex.EXAMPLE_DATE, "value": "183.1000"}})

    date: IsoDate
    value: Rate4


class RateSyncOut(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": {"created": True, "rate": _ROW_EXAMPLE}})

    created: bool
    rate: ExchangeRateOut


def rate_example() -> dict[str, Any]:
    return dict(ex.EXAMPLE_RATE)
