"""Catálogo de errores (03 §7) y handlers: IntegrityError → 409 con `code`, OperationalError → 503, 404/422 en español."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from money_model import ERROR_CODES
from sqlalchemy.exc import IntegrityError, OperationalError

from src.core.errors import CONSTRAINT_CODES, AppError, ErrorCode, integrity_error_handler, register_error_handlers
from src.db.enums import UserRole
from src.domain.users.db_models import UserDB

DOC03 = (Path(__file__).resolve().parents[2] / "docs" / "plan" / "03-flujos-de-negocio.md").read_text(encoding="utf-8")
CATALOG_03 = dict(
    (code, (int(status), textual))
    for code, status, textual in re.findall(
        r"^\| `([A-Z_]+)` \| (\d{3}) \| (.+?) \|$", DOC03[DOC03.index("## 7. Catálogo de errores"):], re.M
    )
)


def test_errors_py_contiene_todos_los_codigos_del_modelo():
    assert ERROR_CODES <= {c.value for c in ErrorCode}


def test_errors_py_es_el_catalogo_de_03_con_su_http_y_su_texto():
    assert {c.value for c in ErrorCode} == set(CATALOG_03)
    for code in ErrorCode:
        status, textual = CATALOG_03[code.value]
        assert code.http == status, code
        assert code.text == textual, code


def test_todo_codigo_de_restriccion_esta_en_el_catalogo():
    assert all(isinstance(c, ErrorCode) for c in CONSTRAINT_CODES.values())


@pytest.mark.asyncio
async def test_integrity_error_por_telefono_repetido_es_409_phone_taken(db_session):
    db_session.add(UserDB(role=UserRole.ADMIN, phone="+584147770000", full_name="A", password_hash="x"))
    await db_session.flush()
    nested = await db_session.begin_nested()
    db_session.add(UserDB(role=UserRole.ADMIN, phone="+584147770000", full_name="B", password_hash="x"))
    with pytest.raises(IntegrityError) as info:
        await db_session.flush()
    await nested.rollback()
    response = await integrity_error_handler(None, info.value)  # type: ignore[arg-type]
    assert response.status_code == 409
    body = json.loads(response.body)
    assert body["code"] == "PHONE_TAKEN" and body["meta"]["constraint"] == "uq_users_phone"
    assert body["detail"].startswith("Ese teléfono ya está registrado")


def _app_raising(exc: Exception) -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/boom")
    async def boom():
        raise exc

    return app


@pytest.mark.asyncio
async def test_integrity_error_sin_codigo_mapeado_es_409_en_espanol():
    class Diag:
        constraint_name = "fk_algo"

    class Orig(Exception):
        diag = Diag()

    app = _app_raising(IntegrityError("INSERT …", {}, Orig()))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/boom")
    assert r.status_code == 409
    assert r.json()["code"] == "VALIDATION_ERROR" and r.json()["detail"].startswith("Revisa los datos")


@pytest.mark.asyncio
async def test_operational_error_es_503():
    app = _app_raising(OperationalError("SELECT 1", {}, Exception("conexión rechazada")))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/boom")
    assert r.status_code == 503
    assert r.json() == {"detail": "Servicio no disponible. Intenta de nuevo.", "code": "SERVICE_UNAVAILABLE", "meta": {}}


@pytest.mark.asyncio
async def test_app_error_lleva_detail_code_y_meta():
    app = _app_raising(AppError(ErrorCode.OPEN_DEBT, {"debt": "12.50"}, "Tienes una deuda pendiente de $12.50. Págala para hacer nuevos pedidos."))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/boom")
    assert r.status_code == 422
    assert r.json() == {
        "detail": "Tienes una deuda pendiente de $12.50. Págala para hacer nuevos pedidos.",
        "code": "OPEN_DEBT",
        "meta": {"debt": "12.50"},
    }


@pytest.mark.asyncio
async def test_error_no_controlado_es_500_sin_detalles_tecnicos():
    app = _app_raising(RuntimeError("detalle interno"))
    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://t") as c:
        r = await c.get("/boom")
    assert r.status_code == 500
    assert "detalle interno" not in r.text


@pytest.mark.asyncio
async def test_ruta_inexistente_es_404_en_espanol(client):
    r = await client.get("/api/v1/no-existe")
    assert r.status_code == 404
    assert r.json() == {"detail": "No encontramos lo que buscas.", "code": "NOT_FOUND", "meta": {}}


@pytest.mark.asyncio
async def test_operacion_declarada_por_fnd_para_otro_bloque_responde_501(client, admin):
    r = await client.get("/api/v1/admin/customers", headers=admin.headers)
    assert r.status_code == 501
    assert r.json() == {"detail": "Aún no disponible.", "code": "NOT_IMPLEMENTED", "meta": {"owner": "B-E1a"}}


@pytest.mark.asyncio
async def test_dinero_como_float_se_rechaza_en_espanol(client, admin):
    r = await client.post(
        "/api/v1/admin/products",
        json={"categoryId": "x", "name": "Pan", "unitLabel": "unidad", "price": 1.5},
        headers=admin.headers,
    )
    assert r.status_code == 422
    assert r.json()["code"] == "VALIDATION_ERROR"
    assert "texto decimal" in r.json()["detail"]
