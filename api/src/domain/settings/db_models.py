"""Configuración por secciones (02 §Operación): una fila por sección con JSON validado por Pydantic."""
from __future__ import annotations

from sqlalchemy import JSON, Column, String

from src.db.base import Base
from src.db.columns import fk, pk, updated_at


class AppSettingDB(Base):
    __tablename__ = "app_settings"

    id = pk()
    # business, orders, delivery, credit, payments, app
    section = Column("section", String, nullable=False, unique=True)
    data = Column("data", JSON, nullable=False)
    updated_by = fk("updatedBy", "users.id")
    updated_at = updated_at()
