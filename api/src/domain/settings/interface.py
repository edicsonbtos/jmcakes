"""Interfaz congelada de configuración (08 §Interfaces) y las secciones de 02 §Claves de configuración.

Una fila por sección en `app_settings`. Lo que no esté guardado toma el default de aquí.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession


class _Section(BaseModel):
    model_config = ConfigDict(extra="ignore", validate_assignment=True)


class BusinessSettings(_Section):
    name: str = "Panadería"
    phone: str = ""
    whatsapp: str = ""
    address: str = ""


class OrdersSettings(_Section):
    openingTime: str = "06:00"  # noqa: N815  (las claves de 02 son camelCase)
    closingTime: str = "19:00"  # noqa: N815
    minLeadMinutes: int = Field(default=60, ge=0)  # noqa: N815
    maxDaysAhead: int = Field(default=30, ge=0)  # noqa: N815
    unpaidExpiryHours: int = Field(default=24, ge=1)  # noqa: N815
    minPayWindowMinutes: int = Field(default=30, ge=1)  # noqa: N815


class DeliverySettings(_Section):
    feeUsd: Decimal = Field(default=Decimal("0.00"), ge=0)  # noqa: N815
    driverUserId: str | None = None  # noqa: N815


class CreditSettings(_Section):
    defaultDays: int = Field(default=7, ge=0, le=365)  # noqa: N815
    blockOverdueDays: int = Field(default=7, ge=0, le=365)  # noqa: N815


class PaymentsSettings(_Section):
    roundingToleranceUsd: Decimal = Field(default=Decimal("0.01"), ge=0)  # noqa: N815


class AppVersionSettings(_Section):
    minVersionCliente: int = Field(default=1, ge=1)  # noqa: N815
    minVersionDelivery: int = Field(default=1, ge=1)  # noqa: N815


SECTIONS: dict[str, type[_Section]] = {
    "business": BusinessSettings,
    "orders": OrdersSettings,
    "delivery": DeliverySettings,
    "credit": CreditSettings,
    "payments": PaymentsSettings,
    "app": AppVersionSettings,
}


@runtime_checkable
class SettingsService(Protocol):
    async def get(self, session: AsyncSession, section: str) -> Any:
        """La sección como su modelo de `SECTIONS` (defaults para lo no guardado). Caché de 30 s."""
        ...

    async def update(
        self, session: AsyncSession, section: str, data: dict[str, Any], actor_id: str | None = None
    ) -> Any:
        """Valida y guarda los campos dados de la sección (merge), invalida la caché y devuelve la sección.
        Datos inválidos → `AppError(INVALID_SETTINGS)`. **No** hace commit: lo hace quien llama, junto con la
        auditoría."""
        ...
