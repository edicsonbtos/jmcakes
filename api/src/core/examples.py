"""Ejemplos del contrato (modo mock con Prism).

El `accessToken` de ejemplo es un JWT HS256 **real** firmado con el secreto del mock
(`dev-mock-secret-no-usar-en-prod`), `role=ADMIN` y `exp` en 2099, para que el proxy de la web
deje pasar en W-E1. Es determinista: `export_openapi --check` no cambia entre corridas.
"""
from __future__ import annotations

from datetime import datetime, timezone

import jwt

from src.config import DEV_MOCK_JWT_SECRET

EXAMPLE_ADMIN_ID = "u7k2m9p4q8r1s5t3v6w0x2y4"
EXAMPLE_ADMIN_PHONE = "+584141234567"
EXAMPLE_ADMIN_NAME = "María Fernández"
EXAMPLE_CUSTOMER_ID = "c3h8j2k5l9m1n4p7q0r6s2t8"
EXAMPLE_PRODUCT_ID = "p4d9f2g6h1j8k3l5m7n0q2r4"
EXAMPLE_CATEGORY_ID = "g2b7c4d9e1f6h3j8k5l0m2n4"
EXAMPLE_PAYMENT_ID = "y5a1b8c3d6e9f2g4h7j0k1l3"
EXAMPLE_RECEIVABLE_ID = "r6m2n8p4q1s7t3v9w5x0y2z4"
EXAMPLE_METHOD_ID = "m1q6r2s8t4v0w7x3y9z5a1b6"
EXAMPLE_BANK_ACCOUNT_ID = "b8c2d7e3f9g4h0j6k1l5m3n7"
EXAMPLE_CASH_ACCOUNT_ID = "k9l3m8n2p7q1r6s0t5v4w8x2"
EXAMPLE_TS = "2026-10-21T14:30:00.000Z"
EXAMPLE_DATE = "2026-10-21"

_IAT = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp())
_EXP = int(datetime(2099, 1, 1, tzinfo=timezone.utc).timestamp())

EXAMPLE_ACCESS_TOKEN = jwt.encode(
    {"sub": EXAMPLE_ADMIN_ID, "role": "ADMIN", "cid": None, "typ": "access", "iat": _IAT, "exp": _EXP},
    DEV_MOCK_JWT_SECRET,
    algorithm="HS256",
)
EXAMPLE_REFRESH_TOKEN = "Xq3v9LmT2pR7sK1wZ8yB4nC6dF0gH5jA-ejemplo-mock"

EXAMPLE_ADMIN_USER = {
    "id": EXAMPLE_ADMIN_ID,
    "role": "ADMIN",
    "phone": EXAMPLE_ADMIN_PHONE,
    "email": None,
    "fullName": EXAMPLE_ADMIN_NAME,
    "isActive": True,
    "mustChangePassword": False,
    "lastLoginAt": EXAMPLE_TS,
    "createdAt": "2026-10-01T12:00:00.000Z",
}

EXAMPLE_RATE = {"date": EXAMPLE_DATE, "value": "182.4500", "rateType": "BCV", "isFallback": False}
