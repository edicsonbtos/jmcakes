"""Login, refresh rotativo con gracia, logout y cambio de contraseña (01 §Autenticación, 08 §FND).

En E1 solo el rol ADMIN inicia sesión (`LOGIN_ROLES`); `register`, `device-tokens` y
`DELETE /auth/account` llegan en E4. Este service hace el commit de cada operación.
"""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.errors import AppError, ErrorCode
from src.core.security import create_access_token, hash_password, hash_token, new_refresh_token, verify_password
from src.db.enums import UserRole
from src.domain.auth.db_models import RefreshTokenDB
from src.domain.auth.schemas import AuthTokens, MeCustomer, MeOut, UserOut
from src.domain.users.db_models import UserDB
from src.services import registry
from src.utils.date_utils import utcnow
from src.utils.phone import InvalidPhone, normalize_phone

#: Roles que pueden iniciar sesión en la etapa actual (09 §E1 — API, notas de `auth`).
LOGIN_ROLES = frozenset({UserRole.ADMIN})

# Hash de una contraseña cualquiera: igualamos el tiempo de respuesta cuando el teléfono no existe.
_DUMMY_HASH = hash_password("contrasena-de-relleno-para-tiempo-constante")


async def _customer_out(session: AsyncSession, user: UserDB) -> MeCustomer | None:
    if UserRole(user.role) != UserRole.CUSTOMER:
        return None
    customer = await registry.get("customers").get_by_user(session, user.id)
    return MeCustomer.model_validate(customer) if customer else None


async def issue_tokens(session: AsyncSession, user: UserDB, device_label: str | None = None) -> AuthTokens:
    """Crea un refresh nuevo (solo `flush`) y firma el access."""
    tokens, _ = await _issue(session, user, device_label)
    return tokens


async def _issue(session: AsyncSession, user: UserDB, device_label: str | None) -> tuple[AuthTokens, str]:
    plain = new_refresh_token()
    now = utcnow()
    row = RefreshTokenDB(
        user_id=user.id,
        token_hash=hash_token(plain),
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS),
        device_label=device_label,
    )
    session.add(row)
    await session.flush()
    customer = await _customer_out(session, user)
    access = create_access_token(user_id=user.id, role=UserRole(user.role).value, customer_id=customer.id if customer else None)
    tokens = AuthTokens(
        access_token=access,
        refresh_token=plain,
        expires_in=settings.ACCESS_TOKEN_TTL_SECONDS,
        user=UserOut.model_validate(user),
        customer=customer,
    )
    return tokens, row.id


async def login(session: AsyncSession, phone: str, password: str) -> AuthTokens:
    try:
        normalized = normalize_phone(phone)
    except InvalidPhone:
        verify_password(password, _DUMMY_HASH)
        raise AppError(ErrorCode.INVALID_CREDENTIALS) from None
    user = (await session.execute(select(UserDB).where(UserDB.phone == normalized))).scalar_one_or_none()
    if user is None:
        verify_password(password, _DUMMY_HASH)
        raise AppError(ErrorCode.INVALID_CREDENTIALS)
    if not verify_password(password, user.password_hash) or not user.is_active:
        raise AppError(ErrorCode.INVALID_CREDENTIALS)
    if UserRole(user.role) not in LOGIN_ROLES:
        raise AppError(ErrorCode.FORBIDDEN, {"reason": "ROLE_NOT_ENABLED"})
    user.last_login_at = utcnow()
    tokens = await issue_tokens(session, user)
    await session.commit()
    return tokens


async def refresh(session: AsyncSession, refresh_token: str) -> AuthTokens:
    """Rota el refresh. Un token rotado hace menos de `REFRESH_GRACE_SECONDS` todavía emite un par nuevo
    (refresh concurrentes o respuesta perdida); pasado ese margen, `401 UNAUTHENTICATED`."""
    now = utcnow()
    row = (
        await session.execute(
            select(RefreshTokenDB).where(RefreshTokenDB.token_hash == hash_token(refresh_token)).with_for_update()
        )
    ).scalar_one_or_none()
    if row is None or row.revoked_at is not None or row.expires_at <= now:
        raise AppError(ErrorCode.UNAUTHENTICATED)
    if row.rotated_at is not None and (now - row.rotated_at).total_seconds() > settings.REFRESH_GRACE_SECONDS:
        raise AppError(ErrorCode.UNAUTHENTICATED)
    user = await session.get(UserDB, row.user_id)
    if user is None or not user.is_active:
        raise AppError(ErrorCode.UNAUTHENTICATED)
    tokens, new_row_id = await _issue(session, user, row.device_label)
    if row.rotated_at is None:
        row.rotated_at = now
        row.replaced_by_id = new_row_id
    await session.commit()
    return tokens


async def logout(session: AsyncSession, user: UserDB, refresh_token: str | None) -> None:
    stmt = update(RefreshTokenDB).where(RefreshTokenDB.user_id == user.id, RefreshTokenDB.revoked_at.is_(None))
    if refresh_token:
        stmt = stmt.where(RefreshTokenDB.token_hash == hash_token(refresh_token))
    await session.execute(stmt.values(revoked_at=utcnow()))
    await session.commit()


async def me(session: AsyncSession, user: UserDB) -> MeOut:
    return MeOut(user=UserOut.model_validate(user), customer=await _customer_out(session, user))


async def change_password(session: AsyncSession, user: UserDB, current: str, new: str) -> AuthTokens:
    """Cambia la contraseña, quita `mustChangePassword`, revoca todas las sesiones y devuelve un par nuevo."""
    if not verify_password(current, user.password_hash):
        raise AppError(ErrorCode.INVALID_CURRENT_PASSWORD)
    user.password_hash = hash_password(new)
    user.must_change_password = False
    await session.execute(
        update(RefreshTokenDB)
        .where(RefreshTokenDB.user_id == user.id, RefreshTokenDB.revoked_at.is_(None))
        .values(revoked_at=utcnow())
    )
    tokens = await issue_tokens(session, user)
    await registry.get("audit").log(
        session, action="auth.change_password", entity_type="user", entity_id=user.id, actor_id=user.id
    )
    await session.commit()
    return tokens
