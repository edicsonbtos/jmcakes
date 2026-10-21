"""Usuarios (02 §Identidad)."""
from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, String

from src.db.base import Base
from src.db.columns import created_at, enum_col, pk, updated_at
from src.db.enums import UserRole


class UserDB(Base):
    __tablename__ = "users"

    id = pk()
    role = enum_col("role", UserRole, nullable=False)
    # `uq_users_phone` → PHONE_TAKEN. E.164.
    phone = Column("phone", String, nullable=False, unique=True)
    email = Column("email", String, nullable=True)
    password_hash = Column("passwordHash", String, nullable=False)
    full_name = Column("fullName", String, nullable=False)
    is_active = Column("isActive", Boolean, nullable=False, default=True)
    must_change_password = Column("mustChangePassword", Boolean, nullable=False, default=False)
    last_login_at = Column("lastLoginAt", DateTime, nullable=True)
    created_at = created_at()
    updated_at = updated_at()
