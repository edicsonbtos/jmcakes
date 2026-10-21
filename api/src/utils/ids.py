"""Identificadores cuid2 para todas las tablas (02 §Convenciones)."""
from __future__ import annotations

from cuid2 import cuid_wrapper

_cuid = cuid_wrapper()


def new_id() -> str:
    """Un id nuevo (cuid2, 24 caracteres)."""
    return str(_cuid())
