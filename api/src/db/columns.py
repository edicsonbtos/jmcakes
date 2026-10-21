"""Columnas comunes (02 §Convenciones): id cuid2, fechas naive UTC asignadas en Python y dinero."""
from __future__ import annotations

import enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Numeric, String

from src.utils.date_utils import utcnow
from src.utils.ids import new_id

MONEY = Numeric(14, 2)
RATE = Numeric(14, 4)


def pk() -> Column:
    return Column("id", String, primary_key=True, default=new_id)


def created_at() -> Column:
    # Asignado en Python: `func.now()` repite la hora de inicio de la transacción (02).
    return Column("createdAt", DateTime, nullable=False, default=utcnow)


def updated_at() -> Column:
    return Column("updatedAt", DateTime, nullable=False, default=utcnow, onupdate=utcnow)


def enum_col(name: str, enum_cls: type[enum.Enum], **kw) -> Column:
    return Column(name, SQLEnum(enum_cls, name=enum_cls.__name__), **kw)


def fk(name: str, target: str, *, nullable: bool = True, index: bool = True, **kw) -> Column:
    """FK a `<tabla>.id` con índice (toda FK lleva índice)."""
    return Column(name, String, ForeignKey(target), nullable=nullable, index=index, **kw)
