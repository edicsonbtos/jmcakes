# Adaptado de OpenGravity: apps/bot/src/api/auth/deps.py
"""Dependencias de autenticación y autorización.

- `get_current_user`: Bearer JWT válido y usuario activo; si no, `401 UNAUTHENTICATED`.
- `require_role(*roles)`: además, el rol; si no, `403 FORBIDDEN`. Con `mustChangePassword` responde
  `403 FORBIDDEN` (`meta.reason = MUST_CHANGE_PASSWORD`) hasta que el usuario llame a `change-password`.
- `access(*roles)`: dependencias + `x-roles` de una operación en un solo lugar, para que el contrato y
  la autorización no se separen (`tests/test_authz_matrix.py` lo verifica).
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import AppError, ErrorCode
from src.core.security import decode_access_token
from src.db.enums import UserRole
from src.db.session import get_db
from src.domain.users.db_models import UserDB

PUBLIC = "PUBLIC"
ALL_ROLES = (UserRole.CUSTOMER, UserRole.ADMIN, UserRole.PRODUCTION, UserRole.DELIVERY)

_bearer = HTTPBearer(auto_error=False, description="Access token JWT (30 min).")

MUST_CHANGE_PASSWORD_DETAIL = "Debes cambiar tu contraseña antes de continuar."


async def get_current_user_allow_password_change(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserDB:
    """Usuario autenticado, aunque deba cambiar la contraseña (para `me`, `logout` y `change-password`)."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(ErrorCode.UNAUTHENTICATED)
    claims = decode_access_token(credentials.credentials)
    if claims is None:
        raise AppError(ErrorCode.UNAUTHENTICATED)
    user = await session.get(UserDB, claims["sub"])
    if user is None or not user.is_active or user.role != claims.get("role"):
        raise AppError(ErrorCode.UNAUTHENTICATED)
    return user


async def get_current_user(
    user: Annotated[UserDB, Depends(get_current_user_allow_password_change)],
) -> UserDB:
    """Usuario autenticado que ya no tiene contraseña temporal."""
    if user.must_change_password:
        raise AppError(ErrorCode.FORBIDDEN, {"reason": "MUST_CHANGE_PASSWORD"}, MUST_CHANGE_PASSWORD_DETAIL)
    return user


def require_role(*roles: UserRole):
    allowed = {UserRole(r) for r in roles}

    async def _require(user: Annotated[UserDB, Depends(get_current_user)]) -> UserDB:
        if UserRole(user.role) not in allowed:
            raise AppError(ErrorCode.FORBIDDEN)
        return user

    _require.__name__ = "require_" + "_".join(sorted(r.value.lower() for r in allowed))
    return _require


def access(*roles: UserRole | str, allow_password_change: bool = False) -> dict[str, Any]:
    """`**access(UserRole.ADMIN)` en el decorador de la ruta: dependencias y `x-roles`.

    `access(PUBLIC)` → sin autenticación. Con `allow_password_change=True` se acepta un usuario con
    `mustChangePassword` (solo las operaciones de `auth` que lo necesitan).
    """
    if roles == (PUBLIC,):
        return {"openapi_extra": {"x-roles": [PUBLIC]}}
    role_set = tuple(UserRole(r) for r in roles)
    if allow_password_change:
        if set(role_set) != set(ALL_ROLES):
            raise ValueError("allow_password_change solo aplica a operaciones de cualquier rol autenticado")
        deps = [Depends(get_current_user_allow_password_change)]
    else:
        deps = [Depends(require_role(*role_set))]
    return {"dependencies": deps, "openapi_extra": {"x-roles": [r.value for r in role_set]}}


CurrentUser = Annotated[UserDB, Depends(get_current_user)]
CurrentUserAllowPasswordChange = Annotated[UserDB, Depends(get_current_user_allow_password_change)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
