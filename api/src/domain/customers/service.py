"""`CustomersService` real (08 §Interfaces). B-E1a agrega aquí el CRUD de clientes del panel."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import AppError, ErrorCode
from src.domain.customers.db_models import CustomerDB


class DefaultCustomersService:
    async def get_for_update(self, session: AsyncSession, customer_id: str) -> CustomerDB:
        stmt = select(CustomerDB).where(CustomerDB.id == customer_id).with_for_update()
        customer = (await session.execute(stmt)).scalar_one_or_none()
        if customer is None:
            raise AppError(ErrorCode.NOT_FOUND, {"entity": "customer", "id": customer_id})
        return customer

    async def get_by_user(self, session: AsyncSession, user_id: str) -> CustomerDB | None:
        stmt = select(CustomerDB).where(CustomerDB.user_id == user_id)
        return (await session.execute(stmt)).scalar_one_or_none()


_instance = DefaultCustomersService()


def get_customers_service() -> DefaultCustomersService:
    """Fábrica (registro: `customers`)."""
    return _instance
