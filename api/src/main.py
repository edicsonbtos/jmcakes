"""Aplicación FastAPI de la panadería.

- CORS desde `CORS_ORIGINS`.
- Lifespan: programador de jobs (`SCHEDULER_ENABLED`) y cierre del engine.
- Registra **todos** los routers del inventario de la etapa (09 §E1 — API: 52 operaciones).
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.limiter import limiter
from src.api.v1 import (
    admin_money,
    audit,
    auth,
    cash_accounts,
    catalog,
    customers,
    dashboard,
    health,
    payment_methods,
    payments,
    rates,
    settings as settings_router,
    users,
)
from src.config import settings
from src.core.errors import register_error_handlers
from src.core.logging import setup_logging
from src.db.session import dispose_engine
from src.jobs.runner import start_scheduler, stop_scheduler
from src.version import VERSION

API_PREFIX = "/api/v1"

#: Routers bajo `/api/v1`, en el orden en que aparecen en el contrato.
V1_ROUTERS = [
    auth.router,
    catalog.router,
    customers.router,
    users.router,
    settings_router.router,
    audit.router,
    rates.router,
    payment_methods.router,
    cash_accounts.router,
    admin_money.router,
    payments.router,
    dashboard.router,
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()
        await dispose_engine()


_RENAMED_SCHEMAS = {"Body_import_preview_api_v1_admin_customers_import_preview_post": "CustomerImportUpload"}


def _replace_refs(node, old: str, new: str):
    if isinstance(node, dict):
        return {k: (new if k == "$ref" and v == old else _replace_refs(v, old, new)) for k, v in node.items()}
    if isinstance(node, list):
        return [_replace_refs(v, old, new) for v in node]
    return node


def build_openapi(app: FastAPI) -> dict:
    """OpenAPI con los errores de validación en el formato propio `{detail, code, meta}` y nombres estables."""
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi

    schema = get_openapi(
        title=app.title, version=app.version, description=app.description, routes=app.routes, servers=app.servers
    )
    prefix = "#/components/schemas/"
    schema = _replace_refs(schema, prefix + "HTTPValidationError", prefix + "ErrorOut")
    components = schema["components"]["schemas"]
    for name in ("HTTPValidationError", "ValidationError"):
        components.pop(name, None)
    renames = dict(_RENAMED_SCHEMAS)
    for name in list(components):
        if name.startswith("Page_") and name.endswith("_"):
            renames[name] = name[len("Page_"):-1] + "Page"
    for old, new in renames.items():
        if old in components:
            components[new] = components.pop(old)
            components[new]["title"] = new
            schema = _replace_refs(schema, prefix + old, prefix + new)
            components = schema["components"]["schemas"]
    for path in schema.get("paths", {}).values():
        for op in path.values():
            resp = op.get("responses", {}).get("422")
            if resp and resp.get("description") == "Validation Error":
                resp["description"] = "`VALIDATION_ERROR`: Revisa los datos: <detalle>."
    app.openapi_schema = schema
    return schema


def create_app() -> FastAPI:
    setup_logging(settings.LOG_LEVEL)
    app = FastAPI(
        title="API de la panadería",
        version=VERSION,
        description=(
            "Contrato v1 (etapa E1: web del administrador y cuaderno de clientes). "
            "Dinero como string decimal en USD; Bs en `*Ves` (null sin tasa); fechas ISO-8601 con `Z`. "
            "Errores: `{detail, code, meta}` con `detail` en español."
        ),
        lifespan=lifespan,
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url=None,
    )
    app.state.limiter = limiter
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "Last-Event-ID"],
    )
    register_error_handlers(app)
    app.include_router(health.router)
    for router in V1_ROUTERS:
        app.include_router(router, prefix=API_PREFIX)
    app.openapi = lambda: build_openapi(app)  # type: ignore[method-assign]
    return app


app = create_app()
