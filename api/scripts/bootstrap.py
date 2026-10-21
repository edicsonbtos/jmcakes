"""Arranque idempotente (07 §5). Corre en el `preDeployCommand` de Railway después de `alembic upgrade head`.

- Si hay `BOOTSTRAP_ADMIN_PHONE` y `BOOTSTRAP_ADMIN_PASSWORD` y no existe ningún ADMIN, lo crea con
  `mustChangePassword = true` (cambia la contraseña en el primer ingreso).
- Si `SEED_DEMO=1`, ejecuta `scripts/seed.py`. Falla si falta `SEED_PASSWORD`: nunca hay un valor por defecto.

Uso: `cd api && python -m scripts.bootstrap`
"""
from __future__ import annotations

import asyncio
import logging
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings, settings
from src.core.security import hash_password
from src.db.enums import UserRole
from src.domain.users.db_models import UserDB
from src.services import registry
from src.utils.phone import InvalidPhone, normalize_phone

logger = logging.getLogger("bootstrap")


class BootstrapError(RuntimeError):
    """Configuración de arranque inválida."""


def check_config(cfg: Settings) -> None:
    if cfg.SEED_DEMO and not cfg.SEED_PASSWORD:
        raise BootstrapError("SEED_DEMO=1 exige SEED_PASSWORD (no hay contraseña por defecto).")
    if bool(cfg.BOOTSTRAP_ADMIN_PHONE) != bool(cfg.BOOTSTRAP_ADMIN_PASSWORD):
        raise BootstrapError("BOOTSTRAP_ADMIN_PHONE y BOOTSTRAP_ADMIN_PASSWORD van juntas.")
    if cfg.BOOTSTRAP_ADMIN_PASSWORD and len(cfg.BOOTSTRAP_ADMIN_PASSWORD) < 8:
        raise BootstrapError("BOOTSTRAP_ADMIN_PASSWORD debe tener al menos 8 caracteres.")


async def ensure_admin(session: AsyncSession, cfg: Settings) -> UserDB | None:
    """Crea el primer ADMIN si no hay ninguno. Devuelve el admin creado o el existente más antiguo."""
    existing = (
        await session.execute(
            select(UserDB).where(UserDB.role == UserRole.ADMIN).order_by(UserDB.created_at, UserDB.id).limit(1)
        )
    ).scalar_one_or_none()
    if existing is not None or not cfg.BOOTSTRAP_ADMIN_PHONE:
        return existing
    try:
        phone = normalize_phone(cfg.BOOTSTRAP_ADMIN_PHONE)
    except InvalidPhone:
        raise BootstrapError("BOOTSTRAP_ADMIN_PHONE no es un teléfono válido.") from None
    admin = UserDB(
        role=UserRole.ADMIN,
        phone=phone,
        full_name="Administrador",
        password_hash=hash_password(cfg.BOOTSTRAP_ADMIN_PASSWORD),
        must_change_password=True,
    )
    session.add(admin)
    await session.flush()
    await registry.get("audit").log(session, action="bootstrap.admin_created", entity_type="user", entity_id=admin.id)
    logger.info("Administrador inicial creado (%s…)", phone[:6])
    return admin


async def run_bootstrap(session: AsyncSession, cfg: Settings = settings) -> dict:
    """Idempotente. Hace commit. Devuelve un resumen de lo hecho."""
    check_config(cfg)
    summary: dict = {"admin": None, "seed": None}
    admin = await ensure_admin(session, cfg)
    summary["admin"] = admin.id if admin else None
    if cfg.SEED_DEMO:
        from scripts.seed import run_seed

        summary["seed"] = await run_seed(session, cfg)
    await session.commit()
    return summary


async def _main() -> int:
    from src.core.logging import setup_logging
    from src.db.session import SessionLocal, dispose_engine

    setup_logging(settings.LOG_LEVEL)
    try:
        async with SessionLocal() as session:
            summary = await run_bootstrap(session)
        logger.info("Bootstrap listo: %s", summary)
        return 0
    except BootstrapError as exc:
        logger.error("Bootstrap: %s", exc)
        return 2
    finally:
        await dispose_engine()


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
