"""Interfaz congelada de auditoría (08 §Interfaces). Real de FND; B-E1a agrega la consulta paginada."""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.audit.db_models import AuditLogDB


@runtime_checkable
class AuditService(Protocol):
    async def log(
        self,
        session: AsyncSession,
        *,
        action: str,
        entity_type: str,
        entity_id: str | None = None,
        actor_id: str | None = None,
        data_before: dict[str, Any] | None = None,
        data_after: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AuditLogDB:
        """Agrega una fila a `audit_logs` en la transacción de quien llama (solo `flush`, sin commit).
        `actor_id = None` → actor SYSTEM. Los `Decimal`, fechas y enums se guardan como texto."""
        ...
