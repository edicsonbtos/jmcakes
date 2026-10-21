"""Base de los esquemas de la API (01 §Convenciones).

- `ApiModel`: JSON en camelCase (`alias_generator=to_camel`), acepta snake_case al construir y lee
  atributos de los modelos ORM.
- `Money` (USD, 2 decimales) y `Rate4` (tasa, 4 decimales): **string decimal** en JSON. Se rechaza `float`.
- `UtcDateTime`: ISO-8601 con `Z`. Los naive se interpretan como UTC (así vienen de la base).
- Listas: `Page[T]` = `{items, nextCursor}`.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated, Any, Generic, TypeVar

from pydantic import BaseModel, BeforeValidator, ConfigDict, PlainSerializer, WithJsonSchema
from pydantic.alias_generators import to_camel

from src.db.enums import RateType
from src.utils.date_utils import iso_z, to_utc_naive
from src.utils.money import q2, q4


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        use_enum_values=False,
        ser_json_timedelta="iso8601",
    )


# --------------------------------------------------------------------------- dinero
def _parse_decimal(value: Any, places: int) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError("debe enviarse como texto decimal, por ejemplo \"12.50\"")
    if isinstance(value, Decimal):
        d = value
    elif isinstance(value, int):
        d = Decimal(value)
    elif isinstance(value, str):
        text = value.strip()
        try:
            d = Decimal(text)
        except InvalidOperation:
            raise ValueError("debe ser un monto decimal, por ejemplo \"12.50\"") from None
    else:
        raise ValueError("debe ser un monto decimal, por ejemplo \"12.50\"")
    if not d.is_finite():
        raise ValueError("debe ser un monto decimal finito")
    exponent = d.as_tuple().exponent
    if isinstance(exponent, int) and -exponent > places:
        raise ValueError(f"admite como máximo {places} decimales")
    return d


def _money_in(value: Any) -> Decimal:
    return q2(_parse_decimal(value, 2))


def _rate_in(value: Any) -> Decimal:
    return q4(_parse_decimal(value, 4))


def _qty_in(value: Any) -> Decimal:
    return _parse_decimal(value, 3).quantize(Decimal("0.001"))


Money = Annotated[
    Decimal,
    BeforeValidator(_money_in),
    PlainSerializer(lambda d: str(q2(d)), return_type=str, when_used="json"),
    WithJsonSchema({"type": "string", "format": "decimal", "pattern": r"^-?\d+(\.\d{1,2})?$", "example": "12.50"}),
]
"""Monto en USD (o en la moneda indicada), string decimal con 2 decimales."""

Rate4 = Annotated[
    Decimal,
    BeforeValidator(_rate_in),
    PlainSerializer(lambda d: str(q4(d)), return_type=str, when_used="json"),
    WithJsonSchema({"type": "string", "format": "decimal", "pattern": r"^\d+(\.\d{1,4})?$", "example": "182.4500"}),
]
"""Tasa Bs/USD, string decimal con 4 decimales."""

Qty3 = Annotated[
    Decimal,
    BeforeValidator(_qty_in),
    PlainSerializer(lambda d: format(d.normalize(), "f"), return_type=str, when_used="json"),
    WithJsonSchema({"type": "string", "format": "decimal", "pattern": r"^\d+(\.\d{1,3})?$", "example": "2"}),
]
"""Cantidad con hasta 3 decimales (productos por kg), string decimal."""


# --------------------------------------------------------------------------- fechas
def _dt_in(value: Any) -> Any:
    if isinstance(value, datetime):
        return to_utc_naive(value)
    if isinstance(value, str):
        text = value.strip().replace("Z", "+00:00")
        try:
            return to_utc_naive(datetime.fromisoformat(text))
        except ValueError:
            raise ValueError("debe ser una fecha y hora ISO, por ejemplo 2026-10-21T14:30:00Z") from None
    return value


UtcDateTime = Annotated[
    datetime,
    BeforeValidator(_dt_in),
    PlainSerializer(lambda d: iso_z(d), return_type=str, when_used="json"),
    WithJsonSchema({"type": "string", "format": "date-time", "example": "2026-10-21T14:30:00.000Z"}),
]

IsoDate = Annotated[date, WithJsonSchema({"type": "string", "format": "date", "example": "2026-10-21"})]


# --------------------------------------------------------------------------- comunes
T = TypeVar("T")


class Page(ApiModel, Generic[T]):
    """Lista paginada por cursor: `?cursor=&limit=` → `{items, nextCursor}`."""

    items: list[T]
    next_cursor: str | None = None

    @classmethod
    def model_parametrized_name(cls, params: tuple[type[Any], ...]) -> str:
        return f"{params[0].__name__}Page"


class RateOut(ApiModel):
    """`Rate{date, value, rateType, isFallback}` (08 §Convenciones)."""

    date: IsoDate
    value: Rate4
    rate_type: RateType
    is_fallback: bool
