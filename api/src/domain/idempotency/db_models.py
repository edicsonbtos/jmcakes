"""Registros de idempotencia de operaciones de admin sin tabla propia con llave (02 §Identidad).

Scopes: `admin.fiado`, `admin.manual_payment`, … y `admin.customer_import` (vista previa de la
importación: `key` = `previewToken`, vence a los 30 min de `createdAt`).
"""
from __future__ import annotations

from sqlalchemy import JSON, Column, String, UniqueConstraint

from src.db.base import Base
from src.db.columns import created_at, pk


class IdempotencyRecordDB(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (UniqueConstraint("scope", "key", name="uq_idempotency_records_scope_key"),)

    id = pk()
    scope = Column("scope", String, nullable=False)
    key = Column("key", String, nullable=False)
    request_hash = Column("requestHash", String, nullable=False)
    response_json = Column("responseJson", JSON, nullable=True)
    created_at = created_at()
