"""Autenticación de E1: login, refresh rotativo con gracia (E15), logout, me y change-password (CU-11)."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from src.core.security import create_access_token, hash_token
from src.db.enums import UserRole
from src.domain.auth.db_models import RefreshTokenDB
from src.domain.users.db_models import UserDB
from src.utils.date_utils import utcnow
from tests.conftest import DEFAULT_PASSWORD

pytestmark = pytest.mark.asyncio

LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
ME = "/api/v1/auth/me"
LOGOUT = "/api/v1/auth/logout"
CHANGE = "/api/v1/auth/change-password"
ADMIN_ROUTE = "/api/v1/admin/customers"


async def login(client, phone: str, password: str = DEFAULT_PASSWORD, **headers):
    return await client.post(LOGIN, json={"phone": phone, "password": password}, headers=headers)


async def test_login_de_admin_devuelve_par_de_tokens_y_usuario(client, admin):
    r = await login(client, admin.user.phone)
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"accessToken", "refreshToken", "tokenType", "expiresIn", "user", "customer"}
    assert body["expiresIn"] == 1800 and body["tokenType"] == "bearer"
    assert body["user"]["role"] == "ADMIN" and body["user"]["mustChangePassword"] is False
    assert body["user"]["createdAt"].endswith("Z")
    me = await client.get(ME, headers={"Authorization": f"Bearer {body['accessToken']}"})
    assert me.status_code == 200 and me.json()["user"]["id"] == admin.id


async def test_login_acepta_el_telefono_como_se_escribe_en_venezuela(client, make_user):
    u = await make_user(UserRole.ADMIN, phone="+584141234567")
    for written in ("0414-123.45.67", "414 1234567", "+58 414 123 4567", "58 414 1234567"):
        r = await login(client, written)
        assert r.status_code == 200, (written, r.text)
        assert r.json()["user"]["id"] == u.id


async def test_login_con_clave_incorrecta_o_telefono_desconocido_da_invalid_credentials(client, admin):
    for phone, pwd in ((admin.user.phone, "otra-clave-123"), ("+584169999999", DEFAULT_PASSWORD), ("0000000", "x")):
        r = await login(client, phone, pwd)
        assert r.status_code == 401
        assert r.json() == {"detail": "Teléfono o contraseña incorrectos.", "code": "INVALID_CREDENTIALS", "meta": {}}


async def test_usuario_inactivo_no_inicia_sesion(client, make_user):
    u = await make_user(UserRole.ADMIN, is_active=False)
    r = await login(client, u.user.phone)
    assert r.status_code == 401 and r.json()["code"] == "INVALID_CREDENTIALS"


@pytest.mark.parametrize("role", [UserRole.CUSTOMER, UserRole.PRODUCTION, UserRole.DELIVERY])
async def test_en_e1_solo_el_admin_inicia_sesion(client, make_user, role):
    u = await make_user(role)
    r = await login(client, u.user.phone)
    assert r.status_code == 403 and r.json()["code"] == "FORBIDDEN"


async def test_login_actualiza_last_login_at(client, admin, db_session):
    assert admin.user.last_login_at is None
    assert (await login(client, admin.user.phone)).status_code == 200
    await db_session.refresh(admin.user)
    assert admin.user.last_login_at is not None


async def test_validacion_del_login_responde_en_espanol(client):
    r = await client.post(LOGIN, json={"phone": "04141234567"})
    assert r.status_code == 422
    body = r.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["detail"].startswith("Revisa los datos:") and "password" in body["detail"]


async def test_me_sin_token_o_con_token_invalido_da_401(client):
    for headers in ({}, {"Authorization": "Bearer no-es-un-jwt"}, {"Authorization": "Basic abc"}):
        r = await client.get(ME, headers=headers)
        assert r.status_code == 401
        assert r.json()["code"] == "UNAUTHENTICATED"
        assert r.json()["detail"] == "Tu sesión expiró. Inicia sesión de nuevo."


async def test_access_vencido_da_401(client, admin):
    expired = create_access_token(user_id=admin.id, role="ADMIN", now=datetime.now(timezone.utc) - timedelta(hours=2))
    r = await client.get(ME, headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401


async def test_access_con_rol_distinto_al_del_usuario_da_401(client, admin):
    forged = create_access_token(user_id=admin.id, role="CUSTOMER")
    assert (await client.get(ME, headers={"Authorization": f"Bearer {forged}"})).status_code == 401


# ----------------------------------------------------------------------------- refresh
async def test_refresh_rota_el_token_y_el_nuevo_sirve(client, admin, db_session):
    first = (await login(client, admin.user.phone)).json()
    r = await client.post(REFRESH, json={"refreshToken": first["refreshToken"]})
    assert r.status_code == 200, r.text
    second = r.json()
    assert second["refreshToken"] != first["refreshToken"]
    old = (await db_session.execute(select(RefreshTokenDB).where(RefreshTokenDB.token_hash == hash_token(first["refreshToken"])))).scalar_one()
    assert old.rotated_at is not None and old.replaced_by_id is not None
    r3 = await client.post(REFRESH, json={"refreshToken": second["refreshToken"]})
    assert r3.status_code == 200


async def test_refresh_dentro_de_la_gracia_emite_otro_par(client, admin):
    """E15: un reintento con el token ya rotado (respuesta perdida) todavía funciona dentro de 60 s."""
    first = (await login(client, admin.user.phone)).json()
    a = await client.post(REFRESH, json={"refreshToken": first["refreshToken"]})
    b = await client.post(REFRESH, json={"refreshToken": first["refreshToken"]})
    assert a.status_code == 200 and b.status_code == 200
    assert a.json()["refreshToken"] != b.json()["refreshToken"]


async def test_refresh_rotado_fuera_de_la_gracia_da_401(client, admin, db_session):
    first = (await login(client, admin.user.phone)).json()
    assert (await client.post(REFRESH, json={"refreshToken": first["refreshToken"]})).status_code == 200
    row = (await db_session.execute(select(RefreshTokenDB).where(RefreshTokenDB.token_hash == hash_token(first["refreshToken"])))).scalar_one()
    row.rotated_at = utcnow() - timedelta(seconds=61)
    await db_session.flush()
    r = await client.post(REFRESH, json={"refreshToken": first["refreshToken"]})
    assert r.status_code == 401 and r.json()["code"] == "UNAUTHENTICATED"


async def test_refresh_vencido_o_desconocido_da_401(client, admin, db_session):
    first = (await login(client, admin.user.phone)).json()
    row = (await db_session.execute(select(RefreshTokenDB).where(RefreshTokenDB.token_hash == hash_token(first["refreshToken"])))).scalar_one()
    row.expires_at = utcnow() - timedelta(seconds=1)
    await db_session.flush()
    assert (await client.post(REFRESH, json={"refreshToken": first["refreshToken"]})).status_code == 401
    assert (await client.post(REFRESH, json={"refreshToken": "token-que-no-existe-123"})).status_code == 401


@pytest.mark.committed
async def test_dos_refresh_concurrentes_con_el_mismo_token_funcionan(committed_db, committed_client):
    """E15: dos refresh simultáneos (sesiones reales) devuelven 200 los dos."""
    from src.core.security import hash_password

    async with committed_db() as s:
        user = UserDB(role=UserRole.ADMIN, phone="+584141110000", full_name="Admin", password_hash=hash_password(DEFAULT_PASSWORD))
        s.add(user)
        await s.commit()
    first = (await login(committed_client, "+584141110000")).json()
    results = await asyncio.gather(
        committed_client.post(REFRESH, json={"refreshToken": first["refreshToken"]}),
        committed_client.post(REFRESH, json={"refreshToken": first["refreshToken"]}),
    )
    assert [r.status_code for r in results] == [200, 200], [r.text for r in results]
    tokens = {r.json()["refreshToken"] for r in results}
    assert len(tokens) == 2
    for t in tokens:
        assert (await committed_client.post(REFRESH, json={"refreshToken": t})).status_code == 200


# ----------------------------------------------------------------------------- logout
async def test_logout_revoca_el_refresh_enviado(client, admin):
    tokens = (await login(client, admin.user.phone)).json()
    other = (await login(client, admin.user.phone)).json()
    auth = {"Authorization": f"Bearer {tokens['accessToken']}"}
    r = await client.post(LOGOUT, json={"refreshToken": tokens["refreshToken"]}, headers=auth)
    assert r.status_code == 204
    assert (await client.post(REFRESH, json={"refreshToken": tokens["refreshToken"]})).status_code == 401
    assert (await client.post(REFRESH, json={"refreshToken": other["refreshToken"]})).status_code == 200


async def test_logout_sin_cuerpo_revoca_todas_las_sesiones(client, admin):
    a = (await login(client, admin.user.phone)).json()
    b = (await login(client, admin.user.phone)).json()
    r = await client.post(LOGOUT, headers={"Authorization": f"Bearer {a['accessToken']}"})
    assert r.status_code == 204
    for t in (a, b):
        assert (await client.post(REFRESH, json={"refreshToken": t["refreshToken"]})).status_code == 401


async def test_logout_exige_sesion(client):
    assert (await client.post(LOGOUT)).status_code == 401


# ----------------------------------------------------------------------------- change-password (CU-11)
async def test_must_change_password_bloquea_las_rutas_de_admin_hasta_cambiarla(client, make_user):
    u = await make_user(UserRole.ADMIN, must_change_password=True, password="Temporal-1234")
    tokens = (await login(client, u.user.phone, "Temporal-1234")).json()
    assert tokens["user"]["mustChangePassword"] is True
    auth = {"Authorization": f"Bearer {tokens['accessToken']}"}

    me = await client.get(ME, headers=auth)
    assert me.status_code == 200 and me.json()["user"]["mustChangePassword"] is True

    blocked = await client.get(ADMIN_ROUTE, headers=auth)
    assert blocked.status_code == 403
    assert blocked.json()["code"] == "FORBIDDEN" and blocked.json()["meta"] == {"reason": "MUST_CHANGE_PASSWORD"}
    assert "cambiar tu contraseña" in blocked.json()["detail"]

    r = await client.post(CHANGE, json={"currentPassword": "Temporal-1234", "newPassword": "Nueva-clave-segura"}, headers=auth)
    assert r.status_code == 200, r.text
    fresh = r.json()
    assert fresh["user"]["mustChangePassword"] is False
    new_auth = {"Authorization": f"Bearer {fresh['accessToken']}"}
    assert (await client.get(ADMIN_ROUTE, headers=new_auth)).status_code not in (401, 403)
    # Las sesiones anteriores quedan revocadas; la nueva sirve.
    assert (await client.post(REFRESH, json={"refreshToken": tokens["refreshToken"]})).status_code == 401
    assert (await client.post(REFRESH, json={"refreshToken": fresh["refreshToken"]})).status_code == 200
    assert (await login(client, u.user.phone, "Nueva-clave-segura")).status_code == 200
    assert (await login(client, u.user.phone, "Temporal-1234")).status_code == 401


async def test_change_password_con_clave_actual_incorrecta_da_422(client, admin):
    r = await client.post(CHANGE, json={"currentPassword": "no-es-esta", "newPassword": "Nueva-clave-segura"}, headers=admin.headers)
    assert r.status_code == 422
    assert r.json() == {"detail": "La contraseña actual no es correcta.", "code": "INVALID_CURRENT_PASSWORD", "meta": {}}


async def test_change_password_exige_minimo_8_caracteres(client, admin):
    r = await client.post(CHANGE, json={"currentPassword": DEFAULT_PASSWORD, "newPassword": "corta"}, headers=admin.headers)
    assert r.status_code == 422 and r.json()["code"] == "VALIDATION_ERROR"
    assert "newPassword" in r.json()["detail"]


async def test_change_password_queda_auditado(client, admin, db_session):
    from src.domain.audit.db_models import AuditLogDB

    r = await client.post(CHANGE, json={"currentPassword": DEFAULT_PASSWORD, "newPassword": "Nueva-clave-segura"}, headers=admin.headers)
    assert r.status_code == 200
    logs = (await db_session.execute(select(AuditLogDB).where(AuditLogDB.entity_id == admin.id))).scalars().all()
    assert [log.action for log in logs] == ["auth.change_password"]
    assert logs[0].actor_type == "USER"
