# Adaptado de OpenGravity: apps/bot/src/domain/exchange_rates/fetcher.py
"""Lector de la tasa oficial de DolarAPI (`BCV_SOURCE_URL`).

Solo acepta la respuesta JSON oficial con un `promedio` numérico mayor que cero. Cualquier otra
cosa (HTML, texto, número inválido) es `BCVFetchError`: nunca se adivina una tasa.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from src.utils.date_utils import utcnow
from src.utils.money import q4

logger = logging.getLogger(__name__)


class BCVFetchError(Exception):
    """La fuente no devolvió una tasa oficial válida."""


@dataclass(frozen=True)
class BCVRateResult:
    value: Decimal
    source_url: str
    fetched_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


def parse_official_payload(payload: Any) -> tuple[Decimal, dict[str, Any]]:
    """`{"promedio": 182.45, "fechaActualizacion": "…", …}` → (valor, metadata)."""
    if not isinstance(payload, dict):
        raise BCVFetchError("La respuesta no es un objeto JSON.")
    raw = payload.get("promedio")
    if isinstance(raw, bool) or not isinstance(raw, (int, Decimal)):
        raise BCVFetchError("La respuesta no trae un `promedio` numérico.")
    try:
        value = q4(Decimal(raw))
    except InvalidOperation:
        raise BCVFetchError("El `promedio` no es un número válido.") from None
    if not value.is_finite() or value <= 0:
        raise BCVFetchError("El `promedio` debe ser mayor que cero.")
    meta = {k: payload.get(k) for k in ("fuente", "nombre", "fechaActualizacion") if payload.get(k) is not None}
    return value, meta


class BCVFetcher:
    def __init__(
        self, source_url: str, timeout_seconds: float = 8.0, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        self.source_url = source_url
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    async def fetch_usd_ves_rate(self) -> BCVRateResult:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, transport=self.transport) as client:
                response = await client.get(self.source_url, headers={"Accept": "application/json"})
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise BCVFetchError(f"No se pudo consultar la fuente de la tasa: {exc.__class__.__name__}") from exc
        content_type = response.headers.get("content-type", "")
        if "json" not in content_type:
            raise BCVFetchError("La fuente no respondió JSON.")
        try:
            # Los números se leen como Decimal: nunca pasan por float.
            payload = json.loads(response.text, parse_float=Decimal, parse_int=Decimal)
        except ValueError:
            raise BCVFetchError("La fuente respondió un JSON inválido.") from None
        value, meta = parse_official_payload(payload)
        return BCVRateResult(value=value, source_url=self.source_url, fetched_at=utcnow(), metadata=meta)
