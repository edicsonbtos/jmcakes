# Adaptado de OpenGravity: apps/bot/alembic/env.py
"""Entorno de Alembic.

Precedencia de la URL: la fijada por quien llama (`Config.set_main_option("sqlalchemy.url")`)
> `DATABASE_URL_DIRECT` (Neon sin `-pooler`) > `DATABASE_URL`. Las migraciones usan un engine
síncrono con el mismo driver `psycopg`.
"""
from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import normalize_db_url  # noqa: E402
from src.db.base import Base  # noqa: E402
import src.db.models_registry  # noqa: F401,E402

config = context.config
if config.config_file_name is not None and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def resolve_url() -> str:
    url = config.get_main_option("sqlalchemy.url") or ""
    if not url:
        url = os.environ.get("DATABASE_URL_DIRECT") or os.environ.get("DATABASE_URL") or ""
    if not url:
        raise RuntimeError("Falta la URL de la base: DATABASE_URL_DIRECT o DATABASE_URL.")
    return normalize_db_url(url)


def run_migrations_offline() -> None:
    context.configure(
        url=resolve_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(
        resolve_url(), poolclass=pool.NullPool, connect_args={"options": "-c timezone=UTC"}
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
