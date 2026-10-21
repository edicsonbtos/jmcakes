"""Matriz de autorización (E12 / CU-11). **Solo FND la edita.**

Lee los roles de `x-roles` de cada operación del OpenAPI y verifica que:
- sin token, toda operación no pública responde 401;
- cada rol no permitido recibe 401/403 en **todas** las operaciones;
- un ADMIN con `mustChangePassword` recibe 403 en toda operación de admin;
- los roles permitidos pasan la autorización (no reciben 401/403).
Los casos de propiedad (cliente A contra B) van en `tests/bX/test_authz_bX.py`.
"""
from __future__ import annotations

import re

import pytest

from src.db.enums import UserRole
from src.main import app

METHODS = ("get", "post", "patch", "put", "delete")
ROLES = [r for r in UserRole]


def _operations():
    spec = app.openapi()
    for path, item in spec["paths"].items():
        for method, op in item.items():
            if method in METHODS:
                yield method.upper(), path, op["x-roles"]


OPERATIONS = sorted(_operations())


def _concrete(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "x0x0x0x0x0x0x0x0x0x0x0x0", path)


async def _call(client, method: str, path: str, headers: dict | None = None):
    return await client.request(method, _concrete(path), headers=headers or {})


def test_toda_operacion_declara_x_roles():
    for method, path, roles in OPERATIONS:
        assert roles, (method, path)
        assert set(roles) <= {"PUBLIC", *[r.value for r in ROLES]}, (method, path, roles)
        if path.startswith("/api/v1/admin/"):
            assert roles == ["ADMIN"], (method, path, roles)


@pytest.mark.asyncio
@pytest.mark.parametrize("method,path,roles", OPERATIONS, ids=[f"{m} {p}" for m, p, _ in OPERATIONS])
async def test_sin_token_responde_401_salvo_lo_publico(client, method, path, roles):
    r = await _call(client, method, path)
    if roles == ["PUBLIC"]:
        assert r.status_code not in (401, 403), r.text
    else:
        assert r.status_code == 401, r.text
        assert r.json()["code"] == "UNAUTHENTICATED"


@pytest.mark.asyncio
@pytest.mark.parametrize("method,path,roles", OPERATIONS, ids=[f"{m} {p}" for m, p, _ in OPERATIONS])
async def test_cada_rol_no_permitido_recibe_401_o_403(client, make_user, method, path, roles):
    if roles == ["PUBLIC"]:
        pytest.skip("operación pública")
    for role in ROLES:
        user = await make_user(role)
        r = await _call(client, method, path, user.headers)
        if role.value in roles:
            assert r.status_code not in (401, 403), (role, r.text)
        else:
            assert r.status_code in (401, 403), (role, r.status_code, r.text)
            assert r.json()["code"] in ("UNAUTHENTICATED", "FORBIDDEN")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,path,roles",
    [op for op in OPERATIONS if op[2] == ["ADMIN"]],
    ids=[f"{m} {p}" for m, p, r in OPERATIONS if r == ["ADMIN"]],
)
async def test_admin_con_must_change_password_recibe_403(client, make_user, method, path, roles):
    user = await make_user(UserRole.ADMIN, must_change_password=True)
    r = await _call(client, method, path, user.headers)
    assert r.status_code == 403, r.text
    assert r.json()["meta"] == {"reason": "MUST_CHANGE_PASSWORD"}
