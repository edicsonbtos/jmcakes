"""Esquemas de `audit.py` (08 §B1)."""
from __future__ import annotations

from typing import Any

from pydantic import ConfigDict

from src.core import examples as ex
from src.core.schemas import ApiModel, UtcDateTime


class AuditLogOut(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "a4b9c3d8e2f7g1h6j0k5l4m9",
                "actorType": "USER",
                "actorId": ex.EXAMPLE_ADMIN_ID,
                "actorName": ex.EXAMPLE_ADMIN_NAME,
                "action": "customer.credit",
                "entityType": "customer",
                "entityId": ex.EXAMPLE_CUSTOMER_ID,
                "dataBefore": {"creditLimit": "0.00", "creditDays": 7},
                "dataAfter": {"creditLimit": "100.00", "creditDays": 15},
                "createdAt": ex.EXAMPLE_TS,
            }
        }
    )

    id: str
    actor_type: str
    actor_id: str | None = None
    actor_name: str | None = None
    action: str
    entity_type: str
    entity_id: str | None = None
    data_before: dict[str, Any] | None = None
    data_after: dict[str, Any] | None = None
    created_at: UtcDateTime
