# Adaptado de OpenGravity: apps/bot/src/api/limiter.py
"""Límite de intentos (slowapi).

La clave es la cabecera **`X-Real-IP`** que pone el edge de Railway, con respaldo `client.host`.
Nunca el primer `X-Forwarded-For`, que lo controla el cliente. El límite por teléfono del login
se aplica dentro del handler con `limiter.limiter.hit` (`hit_login_phone`).
"""
from __future__ import annotations

from fastapi import Request
from limits import parse
from slowapi import Limiter

LOGIN_IP_LIMIT = "5/minute"
LOGIN_PHONE_LIMIT = "5/minute"
_login_ip_item = parse(LOGIN_IP_LIMIT)
_login_phone_item = parse(LOGIN_PHONE_LIMIT)


def client_ip(request: Request) -> str:
    real_ip = (request.headers.get("x-real-ip") or "").strip()
    if real_ip:
        return real_ip
    return request.client.host if request.client else "desconocido"


limiter = Limiter(key_func=client_ip, headers_enabled=False)


def hit_login_ip(request: Request) -> bool:
    """Cuenta un intento de login para la IP (`X-Real-IP`). `False` si superó el límite."""
    return limiter.limiter.hit(_login_ip_item, "login-ip", client_ip(request))


def hit_login_phone(phone: str) -> bool:
    """Cuenta un intento de login para ese teléfono. `False` si superó el límite."""
    return limiter.limiter.hit(_login_phone_item, "login-phone", phone)


def reset_limits() -> None:
    """Vacía los contadores (pruebas)."""
    limiter.reset()
