# Adaptado de OpenGravity: apps/bot/src/domain/audit/service.py
"""`AuditService.log` real (08 §Interfaces). B-E1a agrega la consulta paginada en su repositorio."""
from __future__ import annotations

import enum
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.audit.db_models import AuditLogDB


def json_safe_payload(payload: Any) -> Any:
    """Normaliza a tipos que acepta una columna JSON. Los montos van como texto para no perder precisión."""
    if payload is None or isinstance(payload, (bool, int, str)):
        return payload
    if isinstance(payload, dict):
        return {str(k): json_safe_payload(v) for k, v in payload.items()}
    if isinstance(payload, (list, tuple, set)):
        return [json_safe_payload(v) for v in payload]
    if isinstance(payload, Decimal):
        return str(payload)
    if isinstance(payload, float):
        return str(Decimal(str(payload)))
    if isinstance(payload, (datetime, date, time)):
        return payload.isoformat()
    if isinstance(payload, enum.Enum):
        return json_safe_payload(payload.value)
    return str(payload)


class DefaultAuditService:
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
        row = AuditLogDB(
            actor_type="USER" if actor_id else "SYSTEM",
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            data_before=json_safe_payload(data_before),
            data_after=json_safe_payload(data_after),
            ip_address=ip_address,
        )
        session.add(row)
        await session.flush()
        return row


_instance = DefaultAuditService()


def get_audit_service() -> DefaultAuditService:
    """Fábrica (registro: `audit`)."""
    return _instance
