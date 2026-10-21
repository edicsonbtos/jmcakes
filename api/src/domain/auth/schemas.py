"""Esquemas de `auth.py` (08 §FND)."""
from __future__ import annotations

from pydantic import ConfigDict, Field

from src.core import examples as ex
from src.core.schemas import ApiModel, Money, UtcDateTime
from src.db.enums import CustomerType, PaymentMode, UserRole


class LoginIn(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": {"phone": "0414-123.45.67", "password": "Pan-dulce-2026"}})

    phone: str = Field(min_length=7, max_length=32, description="Teléfono como se escribe en Venezuela o en E.164.")
    password: str = Field(min_length=1, max_length=128)


class RefreshIn(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": {"refreshToken": ex.EXAMPLE_REFRESH_TOKEN}})

    refresh_token: str = Field(min_length=10, max_length=256)


class LogoutIn(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": {"refreshToken": ex.EXAMPLE_REFRESH_TOKEN}})

    refresh_token: str | None = Field(
        default=None, max_length=256, description="Si se envía, revoca esa sesión; si no, todas las del usuario."
    )


class ChangePasswordIn(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"currentPassword": "Temporal-1234", "newPassword": "Cachitos-de-jamon-7"}}
    )

    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class UserOut(ApiModel):
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


class MeCustomer(ApiModel):
    """Cliente ligado al usuario (solo usuarios CUSTOMER; desde E4)."""

    id: str
    type: CustomerType
    contact_name: str
    business_name: str | None = None
    phone: str | None = None
    payment_mode: PaymentMode
    wallet_balance: Money


class AuthTokens(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "accessToken": ex.EXAMPLE_ACCESS_TOKEN,
                "refreshToken": ex.EXAMPLE_REFRESH_TOKEN,
                "tokenType": "bearer",
                "expiresIn": 1800,
                "user": ex.EXAMPLE_ADMIN_USER,
                "customer": None,
            }
        }
    )

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Segundos de vida del access token.")
    user: UserOut
    customer: MeCustomer | None = None


class MeOut(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": {"user": ex.EXAMPLE_ADMIN_USER, "customer": None}})

    user: UserOut
    customer: MeCustomer | None = None


class HealthOut(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": {"status": "ok", "version": "0.1.0", "db": "ok"}})

    status: str
    version: str
    db: str
