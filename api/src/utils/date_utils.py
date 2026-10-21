# Adaptado de OpenGravity: apps/bot/src/utils/date_utils.py
"""Fechas de negocio de la panadería.

Reglas (CLAUDE.md §Tiempo):
- En la base de datos todo `DateTime` es **naive en UTC** (`to_utc_naive`, `utcnow`).
- El “día” se calcula en `America/Caracas` (`get_today_caracas`, `as_caracas_date`).
- Todo filtro por día usa `caracas_day_bounds_utc(d)`: intervalo semiabierto [inicio, inicioSiguiente).
- Nunca `.date()` sobre un UTC crudo.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

CARACAS_TZ = ZoneInfo("America/Caracas")


def utcnow() -> datetime:
    """Ahora en UTC naive, el formato de todas las columnas `DateTime`."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_now_caracas() -> datetime:
    """Ahora con zona de Caracas (aware)."""
    return datetime.now(CARACAS_TZ)


def get_today_caracas() -> date:
    """La fecha de hoy en Caracas."""
    return datetime.now(CARACAS_TZ).date()


def to_utc_naive(dt: datetime | None) -> datetime | None:
    """Convierte un datetime aware a UTC naive. Un naive de entrada ya es UTC y se conserva."""
    if dt is None or dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def as_caracas_date(dt: datetime | date | None) -> date | None:
    """Fecha de Caracas de un instante.

    - naive: se asume UTC (así viene de la base de datos);
    - aware: se convierte a Caracas;
    - `date`: se devuelve igual.
    """
    if dt is None:
        return None
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return dt
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(CARACAS_TZ).date()


def start_of_day_caracas(d: date) -> datetime:
    """00:00 de `d` en Caracas (aware)."""
    return datetime.combine(d, time.min, tzinfo=CARACAS_TZ)


def end_of_day_caracas(d: date) -> datetime:
    """23:59:59.999999 de `d` en Caracas (aware)."""
    return datetime.combine(d, time.max, tzinfo=CARACAS_TZ)


def caracas_day_bounds_utc(d: date) -> tuple[datetime, datetime]:
    """(inicio, inicioSiguiente) del día `d` de Caracas, en UTC naive. Semiabierto: `inicio <= x < fin`."""
    start = start_of_day_caracas(d)
    nxt = start_of_day_caracas(d + timedelta(days=1))
    return to_utc_naive(start), to_utc_naive(nxt)


def end_of_day_caracas_utc(d: date) -> datetime:
    """Fin del día `d` de Caracas en UTC naive (vencimientos de CxC: 03 §3.1 y §3.10b)."""
    return to_utc_naive(end_of_day_caracas(d))


def iso_z(dt: datetime) -> str:
    """ISO-8601 con `Z` para JSON. Un naive se interpreta como UTC."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.isoformat(timespec="milliseconds") + "Z"
