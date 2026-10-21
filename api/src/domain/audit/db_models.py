# Adaptado de OpenGravity: apps/bot/src/domain/audit/db_models.py
"""Auditoría: quién hizo qué y cuándo."""
from __future__ import annotations

from sqlalchemy import JSON, Column, Index, String

from src.db.base import Base
from src.db.columns import created_at, fk, pk


class AuditLogDB(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_entity_type_entity_id", "entityType", "entityId"),
        Index("ix_audit_logs_created_at_id", "createdAt", "id"),
    )

    id = pk()
    # USER o SYSTEM.
    actor_type = Column("actorType", String, nullable=False)
    actor_id = fk("actorId", "users.id")
    action = Column("action", String, nullable=False)
    entity_type = Column("entityType", String, nullable=False)
    entity_id = Column("entityId", String, nullable=True)
    data_before = Column("dataBefore", JSON, nullable=True)
    data_after = Column("dataAfter", JSON, nullable=True)
    ip_address = Column("ipAddress", String, nullable=True)
    created_at = created_at()
