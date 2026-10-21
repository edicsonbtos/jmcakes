# Adaptado de OpenGravity: apps/bot/src/api/auth/utils.py
"""Contraseñas (bcrypt), access JWT HS256 y refresh opacos (01 §Autenticación).

- Access: 30 min (`ACCESS_TOKEN_TTL_SECONDS`), claims `sub`, `role`, `cid`, `typ=access`, `iat`, `exp`.
- Refresh: 32 bytes aleatorios; en la base solo se guarda su sha256.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from src.config import settings

ALGORITHM = "HS256"


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(
    *, user_id: str, role: str, customer_id: str | None = None, now: datetime | None = None,
    ttl_seconds: int | None = None, secret: str | None = None,
) -> str:
    now = now or datetime.now(timezone.utc)
    ttl = settings.ACCESS_TOKEN_TTL_SECONDS if ttl_seconds is None else ttl_seconds
    payload = {
        "sub": user_id,
        "role": role,
        "cid": customer_id,
        "typ": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl)).timestamp()),
    }
    return jwt.encode(payload, secret or settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Claims del access o `None` si es inválido, venció o no es de tipo access."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM], options={"require": ["exp", "sub"]})
    except jwt.PyJWTError:
        return None
    if payload.get("typ") != "access":
        return None
    return payload


def new_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_temporary_password(length: int = 10) -> str:
    """Contraseña temporal legible (sin 0/O ni 1/l) para restablecer el acceso."""
    alphabet = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))
