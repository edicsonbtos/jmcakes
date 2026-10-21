"""Esquemas de `users.py` (08 §B1). En E1, `POST /admin/users` solo crea administradores."""
from __future__ import annotations

from pydantic import ConfigDict, Field

from src.core import examples as ex
from src.core.schemas import ApiModel, UtcDateTime
from src.db.enums import UserRole


class AdminUser(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": ex.EXAMPLE_ADMIN_USER})

    id: str
    role: UserRole
    phone: str
    email: str | None = None
    full_name: str
    is_active: bool
    must_change_password: bool
    last_login_at: UtcDateTime | None = None
    created_at: UtcDateTime


class UserCreate(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"fullName": "Pedro González", "phone": "0412-765.43.21", "password": "Temporal-1234", "role": "ADMIN"}
        }
    )

    full_name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=7, max_length=32)
    email: str | None = Field(default=None, max_length=120)
    password: str = Field(min_length=8, max_length=128, description="Temporal: el usuario la cambia al entrar.")
    role: UserRole = Field(default=UserRole.ADMIN, description="En E1 solo ADMIN.")


class UserUpdate(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": {"fullName": "Pedro J. González", "isActive": False}})

    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = Field(default=None, min_length=7, max_length=32)
    email: str | None = Field(default=None, max_length=120)
    is_active: bool | None = None


class ResetPasswordIn(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": {"temporaryPassword": "Temporal-5678"}})

    temporary_password: str | None = Field(
        default=None, min_length=8, max_length=128, description="Si no se envía, la API genera una."
    )


class ResetPasswordOut(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": {"temporaryPassword": "Temporal-5678", "mustChangePassword": True}})

    temporary_password: str
    must_change_password: bool = True
