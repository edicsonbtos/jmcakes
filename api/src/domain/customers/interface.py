"""Interfaz congelada de clientes (08 §Interfaces). Real de FND."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.customers.db_models import CustomerDB


@runtime_checkable
class CustomersService(Protocol):
    async def get_for_update(self, session: AsyncSession, customer_id: str) -> CustomerDB:
        """`SELECT … FOR UPDATE` del cliente (todo flujo de dinero empieza aquí). No existe → `NOT_FOUND`."""
        ...

    async def get_by_user(self, session: AsyncSession, user_id: str) -> CustomerDB | None:
        """El cliente ligado a un usuario de la app, o `None`."""
        ...
