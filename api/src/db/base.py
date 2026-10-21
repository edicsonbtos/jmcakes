# Adaptado de OpenGravity: apps/bot/src/db/base.py
"""Base declarativa única de los modelos ORM.

`metadata` usa una convención de nombres para que toda restricción tenga un nombre
estable (02 §Convenciones): el handler de `IntegrityError` mapea esos nombres a `code`.
"""
from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
