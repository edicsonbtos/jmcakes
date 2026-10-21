# Adaptado de OpenGravity: apps/bot/src/db/session.py
"""Engine y sesiones (SQLAlchemy 2 async, driver único `postgresql+psycopg`).

- El engine es **perezoso**: se crea en el primer uso, así `export_openapi` importa la app sin conectarse.
- La conexión fija `timezone=UTC`; con el pooler de Neon (`-pooler`) se desactivan los prepared statements.
- En pruebas (`ENVIRONMENT=test`) se usa `NullPool`.
- Capas: el router valida y delega; el service hace commit/rollback; el repository solo `flush()`.
"""
from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import src.db.models_registry  # noqa: F401  (registra todos los modelos)
from src.config import normalize_db_url, settings

logger = logging.getLogger("db.session")

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def database_url() -> str:
    return normalize_db_url(settings.DATABASE_URL)


def build_engine(url: str | None = None, *, null_pool: bool | None = None) -> AsyncEngine:
    url = normalize_db_url(url or database_url())
    connect_args: dict = {"options": "-c timezone=UTC"}
    if "-pooler" in url:
        connect_args["prepare_threshold"] = None
    use_null = settings.is_test if null_pool is None else null_pool
    if use_null:
        return create_async_engine(url, poolclass=NullPool, connect_args=connect_args)
    return create_async_engine(
        url, pool_size=5, max_overflow=10, pool_pre_ping=True, pool_recycle=300, connect_args=connect_args
    )


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = build_engine()
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(get_engine(), class_=AsyncSession, expire_on_commit=False)
    return _sessionmaker


def SessionLocal() -> AsyncSession:  # noqa: N802  (nombre histórico del patrón)
    """Sesión nueva para jobs, scripts y servicios con sesión propia."""
    return get_sessionmaker()()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia de FastAPI: una sesión por request; rollback si algo falla."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None
