"""Autenticación (08 §FND). En E1: login, refresh, logout, me y change-password; solo ADMIN inicia sesión.

`register`, `device-tokens` y `DELETE /auth/account` llegan en E4.
"""
from __future__ import annotations

from fastapi import APIRouter, Request, Response, status

from src.api.limiter import hit_login_ip, hit_login_phone
from src.core.errors import AppError, ErrorCode, error_responses
from src.domain.auth import service
from src.domain.auth.deps import ALL_ROLES, PUBLIC, CurrentUserAllowPasswordChange, DbSession, access
from src.domain.auth.schemas import AuthTokens, ChangePasswordIn, LoginIn, LogoutIn, MeOut, RefreshIn
from src.utils.phone import InvalidPhone, normalize_phone

router = APIRouter(prefix="/auth", tags=["auth"])

_ANY = access(*ALL_ROLES, allow_password_change=True)


@router.post(
    "/login",
    response_model=AuthTokens,
    summary="Iniciar sesión con teléfono y contraseña",
    responses=error_responses(
        ErrorCode.INVALID_CREDENTIALS, ErrorCode.FORBIDDEN, ErrorCode.RATE_LIMITED, ErrorCode.VALIDATION_ERROR
    ),
    **access(PUBLIC),
)
async def login(body: LoginIn, request: Request, session: DbSession) -> AuthTokens:
    if not hit_login_ip(request):
        raise AppError(ErrorCode.RATE_LIMITED)
    try:
        phone_key = normalize_phone(body.phone)
    except InvalidPhone:
        phone_key = body.phone.strip()
    if not hit_login_phone(phone_key):
        raise AppError(ErrorCode.RATE_LIMITED)
    return await service.login(session, body.phone, body.password)


@router.post(
    "/refresh",
    response_model=AuthTokens,
    summary="Rotar el refresh token y obtener un par nuevo",
    responses=error_responses(ErrorCode.UNAUTHENTICATED, ErrorCode.VALIDATION_ERROR),
    **access(PUBLIC),
)
async def refresh(body: RefreshIn, session: DbSession) -> AuthTokens:
    return await service.refresh(session, body.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Cerrar sesión (revoca el refresh enviado o todos)",
    responses=error_responses(ErrorCode.UNAUTHENTICATED),
    **_ANY,
)
async def logout(user: CurrentUserAllowPasswordChange, session: DbSession, body: LogoutIn | None = None) -> Response:
    await service.logout(session, user, body.refresh_token if body else None)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me",
    response_model=MeOut,
    summary="Usuario de la sesión (incluye mustChangePassword)",
    responses=error_responses(ErrorCode.UNAUTHENTICATED),
    **_ANY,
)
async def me(user: CurrentUserAllowPasswordChange, session: DbSession) -> MeOut:
    return await service.me(session, user)


@router.post(
    "/change-password",
    response_model=AuthTokens,
    summary="Cambiar la contraseña (obligatorio si mustChangePassword)",
    responses=error_responses(
        ErrorCode.UNAUTHENTICATED, ErrorCode.INVALID_CURRENT_PASSWORD, ErrorCode.VALIDATION_ERROR
    ),
    **_ANY,
)
async def change_password(
    body: ChangePasswordIn, user: CurrentUserAllowPasswordChange, session: DbSession
) -> AuthTokens:
    return await service.change_password(session, user, body.current_password, body.new_password)
