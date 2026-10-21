"""Dinero con `Decimal` (CLAUDE.md §Dinero). Nunca `float`.

- USD a 2 decimales con `ROUND_HALF_UP`.
- Tasas a 4 decimales.
- Los Bs mostrados se calculan aquí y no se guardan (03 §0).
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
RATE_QUANT = Decimal("0.0001")
ZERO = Decimal("0.00")


def q2(value: Decimal | int | str) -> Decimal:
    """Redondea a 2 decimales con `ROUND_HALF_UP`."""
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def q4(value: Decimal | int | str) -> Decimal:
    """Redondea una tasa a 4 decimales con `ROUND_HALF_UP`."""
    return Decimal(value).quantize(RATE_QUANT, rounding=ROUND_HALF_UP)


def to_ves(amount_usd: Decimal | None, rate_value: Decimal | None) -> Decimal | None:
    """USD → Bs a la tasa dada; `None` si falta el monto o la tasa (los `*Ves` quedan en null, 08)."""
    if amount_usd is None or rate_value is None:
        return None
    return q2(Decimal(amount_usd) * Decimal(rate_value))


def ves_to_usd(amount_ves: Decimal, rate_value: Decimal) -> Decimal:
    """Bs → USD: `round(amountLocal / bcvRateUsed, 2)` (03 §3.3)."""
    return q2(Decimal(amount_ves) / Decimal(rate_value))
