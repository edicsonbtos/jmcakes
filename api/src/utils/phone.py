"""Teléfonos en E.164. Los venezolanos se aceptan como se escriben en el país.

Ejemplos: `0414-123.45.67`, `414 1234567`, `58 414 1234567` y `+58 414 123 4567` → `+584141234567`.
"""
from __future__ import annotations

import re

_NON_DIGITS = re.compile(r"\D")


class InvalidPhone(ValueError):
    """El texto no es un teléfono válido."""


def normalize_phone(raw: str) -> str:
    """Normaliza a E.164. Lanza `InvalidPhone` si no es un número válido."""
    if raw is None:
        raise InvalidPhone("Teléfono vacío")
    text = raw.strip()
    digits = _NON_DIGITS.sub("", text)
    if not digits:
        raise InvalidPhone("Teléfono vacío")
    if text.startswith("+") and not digits.startswith("58"):
        # Número extranjero ya en formato internacional.
        if 8 <= len(digits) <= 15:
            return "+" + digits
        raise InvalidPhone("Teléfono inválido")
    if digits.startswith("58") and len(digits) == 12:
        national = digits[2:]
    elif digits.startswith("0") and len(digits) == 11:
        national = digits[1:]
    elif len(digits) == 10:
        national = digits
    else:
        raise InvalidPhone("Teléfono inválido")
    if national[0] not in "24":
        raise InvalidPhone("Teléfono inválido")
    return "+58" + national


def phone_digits_query(raw: str) -> str:
    """Dígitos para buscar por teléfono: el “0” inicial equivale a “58” (08 §B1, filtro `query`)."""
    digits = _NON_DIGITS.sub("", raw or "")
    if digits.startswith("0"):
        return "58" + digits[1:]
    return digits
