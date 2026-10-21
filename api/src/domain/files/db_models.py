"""Archivos subidos (02 §Operación). Se usan desde E4."""
from __future__ import annotations

from sqlalchemy import Column, Integer, String

from src.db.base import Base
from src.db.columns import created_at, enum_col, fk, pk
from src.db.enums import FilePurpose


class FileDB(Base):
    __tablename__ = "files"

    id = pk()
    key = Column("key", String, nullable=False, unique=True)
    content_type = Column("contentType", String, nullable=False)
    size_bytes = Column("sizeBytes", Integer, nullable=False)
    purpose = enum_col("purpose", FilePurpose, nullable=False)
    owner_user_id = fk("ownerUserId", "users.id")
    created_at = created_at()
