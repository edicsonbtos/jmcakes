"""Registro de fábricas (08 §Interfaces): las implementaciones se resuelven **en tiempo de llamada**.

- En servicios: `registry.get("money").open_balance(...)`.
- En routers: `Depends(registry.dep("money"))` o las dependencias `get_*` de abajo.
- En pruebas: `with registry.override("money", doble): ...` (las fixtures de `tests/conftest.py` lo usan).

Nunca se importa una instancia por valor: así cada bloque cambia su implementación sin tocar a quien la usa.
"""
from __future__ import annotations

import importlib
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

FACTORIES: dict[str, str] = {
    "customers": "src.domain.customers.service:get_customers_service",
    "settings": "src.domain.settings.service:get_settings_service",
    "audit": "src.domain.audit.service:get_audit_service",
    "rates": "src.domain.exchange_rates.service:get_rate_service",
    "finance": "src.domain.finance.queries:get_finance_queries",
    "money": "src.services.money:get_money_service",
}

_overrides: dict[str, Any] = {}


def factory(name: str) -> Callable[[], Any]:
    try:
        target = FACTORIES[name]
    except KeyError:
        raise KeyError(f"Fábrica desconocida: {name}") from None
    module, _, attr = target.partition(":")
    return getattr(importlib.import_module(module), attr)


def get(name: str) -> Any:
    if name in _overrides:
        return _overrides[name]
    return factory(name)()


@contextmanager
def override(name: str, impl: Any) -> Iterator[Any]:
    if name not in FACTORIES:
        raise KeyError(f"Fábrica desconocida: {name}")
    previous = _overrides.get(name, _MISSING)
    _overrides[name] = impl
    try:
        yield impl
    finally:
        if previous is _MISSING:
            _overrides.pop(name, None)
        else:
            _overrides[name] = previous


_MISSING = object()


def dep(name: str) -> Callable[[], Any]:
    """Dependencia de FastAPI que resuelve la fábrica en cada request."""

    def _resolve() -> Any:
        return get(name)

    _resolve.__name__ = f"get_{name}"
    return _resolve


# Dependencias con nombre, para usar en `Depends(...)`.
get_customers = dep("customers")
get_settings_service = dep("settings")
get_audit = dep("audit")
get_rates = dep("rates")
get_finance = dep("finance")
get_money = dep("money")
