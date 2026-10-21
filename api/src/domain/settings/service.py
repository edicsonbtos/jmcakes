"""`SettingsService` real (08 §Interfaces): `app_settings` por secciones con caché de 30 s.

El commit lo hace quien llama, para auditar en la misma transacción. B-E1a agrega aquí
validaciones (horas `HH:MM`, rangos…) sin cambiar las firmas.
"""
from __future__ import annotations

import time
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import AppError, ErrorCode, spanish_validation_message
from src.domain.settings.db_models import AppSettingDB
from src.domain.settings.interface import SECTIONS

CACHE_TTL_SECONDS = 30.0

_cache: dict[str, tuple[float, Any]] = {}


def clear_settings_cache() -> None:
    _cache.clear()


def _section_model(section: str):
    model = SECTIONS.get(section)
    if model is None:
        raise AppError(ErrorCode.INVALID_SETTINGS, {"section": section}, f"Configuración inválida: la sección “{section}” no existe.")
    return model


class DefaultSettingsService:
    async def get(self, session: AsyncSession, section: str) -> Any:
        model = _section_model(section)
        hit = _cache.get(section)
        if hit is not None and hit[0] > time.monotonic():
            return hit[1].model_copy()
        row = (await session.execute(select(AppSettingDB).where(AppSettingDB.section == section))).scalar_one_or_none()
        value = model.model_validate(row.data if row else {})
        _cache[section] = (time.monotonic() + CACHE_TTL_SECONDS, value)
        return value.model_copy()

    async def update(
        self, session: AsyncSession, section: str, data: dict[str, Any], actor_id: str | None = None
    ) -> Any:
        model = _section_model(section)
        row = (
            await session.execute(select(AppSettingDB).where(AppSettingDB.section == section).with_for_update())
        ).scalar_one_or_none()
        current = dict(row.data) if row else {}
        merged = {**model.model_validate(current).model_dump(mode="json"), **data}
        try:
            value = model.model_validate(merged)
        except ValidationError as exc:
            msg = "; ".join(spanish_validation_message(e) for e in exc.errors()[:3])
            raise AppError(ErrorCode.INVALID_SETTINGS, {"section": section}, f"Configuración inválida: {msg}.") from None
        stored = value.model_dump(mode="json")
        if row is None:
            session.add(AppSettingDB(section=section, data=stored, updated_by=actor_id))
        else:
            row.data = stored
            row.updated_by = actor_id
        await session.flush()
        _cache.pop(section, None)
        return value


_instance = DefaultSettingsService()


def get_settings_service() -> DefaultSettingsService:
    """Fábrica (registro: `settings`)."""
    return _instance
