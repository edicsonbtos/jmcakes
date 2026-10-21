"""Sesiones y dispositivos (02 §Identidad)."""
from __future__ import annotations

from sqlalchemy import JSON, Column, DateTime, String
from sqlalchemy import Enum as SQLEnum

from src.db.base import Base
from src.db.columns import created_at, fk, pk
from src.db.enums import DeviceApp


class RefreshTokenDB(Base):
    """Refresh rotativo con gracia de `REFRESH_GRACE_SECONDS` (08 §FND)."""

    __tablename__ = "refresh_tokens"

    id = pk()
    user_id = fk("userId", "users.id", nullable=False)
    token_hash = Column("tokenHash", String, nullable=False, unique=True)
    expires_at = Column("expiresAt", DateTime, nullable=False)
    revoked_at = Column("revokedAt", DateTime, nullable=True)
    rotated_at = Column("rotatedAt", DateTime, nullable=True)
    replaced_by_id = fk("replacedById", "refresh_tokens.id")
    device_label = Column("deviceLabel", String, nullable=True)
    created_at = created_at()


class DeviceTokenDB(Base):
    """Tokens de push (FCM) y suscripciones Web Push. Se usan desde E3–E4."""

    __tablename__ = "device_tokens"

    id = pk()
    user_id = fk("userId", "users.id", nullable=False)
    app = Column(
        "app",
        SQLEnum(DeviceApp, name="DeviceApp", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    fcm_token = Column("fcmToken", String, nullable=True, unique=True)
    web_push_subscription = Column("webPushSubscription", JSON, nullable=True)
    last_seen_at = Column("lastSeenAt", DateTime, nullable=True)
    created_at = created_at()
