# Adaptado de OpenGravity: apps/bot/src/config.py
"""Configuración de la API (variables de entorno de docs/plan/01 §Variables).

- Bajo pytest **no** se lee `.env`: las pruebas fijan su entorno en `tests/conftest.py`.
- Toda variable nueva va también a `api/.env.example` (una prueba compara las claves).
"""
from __future__ import annotations

import logging
import sys
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Secreto que firma los JWT de ejemplo del contrato (modo mock). Nunca sirve en producción.
DEV_MOCK_JWT_SECRET = "dev-mock-secret-no-usar-en-prod"

_UNDER_PYTEST = "pytest" in sys.modules


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=None if _UNDER_PYTEST else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Base de datos
    DATABASE_URL: str = "postgresql+psycopg://dev:dev@127.0.0.1:5432/panaderia_dev"
    DATABASE_URL_DIRECT: str = ""
    TEST_DATABASE_URL: str = ""

    # Seguridad
    JWT_SECRET: str = ""
    ACCESS_TOKEN_TTL_SECONDS: int = 1800
    REFRESH_TOKEN_TTL_DAYS: int = 30
    REFRESH_GRACE_SECONDS: int = 60

    # Entorno
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000"
    LOG_LEVEL: str = "INFO"
    SCHEDULER_ENABLED: bool = False

    # Archivos (E4)
    STORAGE_BACKEND: str = "local"
    S3_ENDPOINT: str = ""
    S3_REGION: str = ""
    S3_BUCKET: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""

    # Notificaciones (E3–E4): vacías = solo log
    FCM_CREDENTIALS_JSON: str = ""
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_SUBJECT: str = ""

    # Tasa
    BCV_SOURCE_URL: str = "https://ve.dolarapi.com/v1/dolares/oficial"

    # Arranque y datos de demostración
    BOOTSTRAP_ADMIN_PHONE: str = ""
    BOOTSTRAP_ADMIN_PASSWORD: str = ""
    SEED_DEMO: bool = False
    SEED_PASSWORD: str = ""

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_test(self) -> bool:
        return self.ENVIRONMENT == "test"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def jwt_secret(self) -> str:
        """Secreto para firmar JWT. En producción es obligatorio y no puede ser el del mock."""
        if self.JWT_SECRET and (self.JWT_SECRET != DEV_MOCK_JWT_SECRET or not self.is_production):
            return self.JWT_SECRET
        if self.is_production:
            raise RuntimeError("JWT_SECRET es obligatorio en producción y no puede ser el secreto del mock.")
        return DEV_MOCK_JWT_SECRET


def normalize_db_url(url: str) -> str:
    """`postgres://` y `postgresql://` → `postgresql+psycopg://` (driver único, 01 §Stack)."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
