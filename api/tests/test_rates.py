"""Tasa del día (03 §0, E14 parte FND): `rate_for` y `sync_daily_rate`."""
from __future__ import annotations

import json
from datetime import date, timedelta
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import func, select

from src.core.errors import AppError, ErrorCode
from src.db.enums import RateType
from src.domain.exchange_rates.db_models import ExchangeRateDB
from src.domain.exchange_rates.fetcher import BCVFetcher, BCVFetchError
from src.domain.exchange_rates.service import get_rate_service, sync_daily_rate


D = date(2026, 10, 20)


async def add_rate(session, d: date, rate_type: RateType, value: str):
    session.add(ExchangeRateDB(date=d, rate_type=rate_type, value=Decimal(value)))
    await session.flush()


@pytest.mark.asyncio
async def test_manual_del_dia_manda_sobre_bcv(db_session):
    await add_rate(db_session, D, RateType.BCV, "180.0000")
    await add_rate(db_session, D, RateType.MANUAL, "181.5000")
    rate = await get_rate_service().rate_for(db_session, D)
    assert (rate.value, rate.rate_type, rate.is_fallback) == (Decimal("181.5000"), RateType.MANUAL, False)


@pytest.mark.asyncio
async def test_sin_manual_usa_la_bcv_del_dia(db_session):
    await add_rate(db_session, D - timedelta(days=1), RateType.MANUAL, "170.0000")
    await add_rate(db_session, D, RateType.BCV, "180.0000")
    rate = await get_rate_service().rate_for(db_session, D)
    assert (rate.value, rate.rate_type, rate.is_fallback) == (Decimal("180.0000"), RateType.BCV, False)


@pytest.mark.asyncio
async def test_sin_tasa_del_dia_usa_la_mas_reciente_anterior_como_respaldo(db_session):
    await add_rate(db_session, D - timedelta(days=5), RateType.BCV, "150.0000")
    await add_rate(db_session, D - timedelta(days=2), RateType.BCV, "160.0000")
    await add_rate(db_session, D - timedelta(days=2), RateType.MANUAL, "161.0000")
    await add_rate(db_session, D + timedelta(days=1), RateType.BCV, "999.0000")  # futura: no cuenta
    rate = await get_rate_service().rate_for(db_session, D)
    assert rate.date == D - timedelta(days=2)
    assert (rate.value, rate.rate_type, rate.is_fallback) == (Decimal("161.0000"), RateType.MANUAL, True)


@pytest.mark.asyncio
async def test_sin_ninguna_tasa_da_rate_unavailable(db_session):
    with pytest.raises(AppError) as info:
        await get_rate_service().rate_for(db_session, date(1990, 1, 1))
    assert info.value.code is ErrorCode.RATE_UNAVAILABLE
    assert await get_rate_service().rate_for_or_none(db_session, date(1990, 1, 1)) is None


@pytest.mark.asyncio
async def test_rate_for_no_hace_commit(db_session, monkeypatch):
    await add_rate(db_session, D, RateType.BCV, "180.0000")

    async def _no_commit(*a, **k):
        raise AssertionError("rate_for no debe hacer commit")

    monkeypatch.setattr(db_session, "commit", _no_commit)
    await get_rate_service().rate_for(db_session, D)


# ----------------------------------------------------------------------------- sync con DolarAPI
def _fetcher(handler) -> BCVFetcher:
    return BCVFetcher("https://ve.dolarapi.com/v1/dolares/oficial", transport=httpx.MockTransport(handler))


def _json(payload, status=200):
    return lambda request: httpx.Response(status, content=json.dumps(payload), headers={"content-type": "application/json"})


OFFICIAL = {"fuente": "oficial", "nombre": "Oficial", "compra": None, "venta": None, "promedio": 182.45,
            "fechaActualizacion": "2026-10-20T20:00:00.000Z"}


@pytest.mark.asyncio
async def test_sync_inserta_la_bcv_de_hoy_con_metadata(db_session):
    row, created = await sync_daily_rate(db_session, _fetcher(_json(OFFICIAL)), today=D)
    assert created and row.value == Decimal("182.4500") and row.rate_type == RateType.BCV
    assert row.metadata_json["fechaActualizacion"] == "2026-10-20T20:00:00.000Z"
    rate = await get_rate_service().rate_for(db_session, D)
    assert rate.value == Decimal("182.4500") and not rate.is_fallback


@pytest.mark.asyncio
async def test_sync_repetido_no_cambia_el_valor_de_hoy(db_session):
    await sync_daily_rate(db_session, _fetcher(_json(OFFICIAL)), today=D)
    row, created = await sync_daily_rate(db_session, _fetcher(_json({**OFFICIAL, "promedio": 190.1})), today=D)
    assert not created and row.value == Decimal("182.4500")
    count = (await db_session.execute(select(func.count()).select_from(ExchangeRateDB).where(ExchangeRateDB.date == D))).scalar()
    assert count == 1


@pytest.mark.asyncio
async def test_sync_por_la_tarde_no_altera_la_manual_del_dia(db_session):
    await add_rate(db_session, D, RateType.MANUAL, "185.0000")
    await sync_daily_rate(db_session, _fetcher(_json(OFFICIAL)), today=D)
    rate = await get_rate_service().rate_for(db_session, D)
    assert (rate.value, rate.rate_type) == (Decimal("185.0000"), RateType.MANUAL)


@pytest.mark.parametrize(
    "handler",
    [
        lambda r: httpx.Response(200, content="<html>Tasa 182,45</html>", headers={"content-type": "text/html"}),
        _json({**OFFICIAL, "promedio": "182,45"}),
        _json({**OFFICIAL, "promedio": 0}),
        _json({**OFFICIAL, "promedio": -3.2}),
        _json({"fuente": "oficial"}),
        _json([OFFICIAL]),
        _json(OFFICIAL, status=500),
        lambda r: httpx.Response(200, content="{no es json", headers={"content-type": "application/json"}),
    ],
    ids=["html", "texto", "cero", "negativo", "sin-promedio", "lista", "error-500", "json-roto"],
)
@pytest.mark.asyncio
async def test_respuesta_no_oficial_da_error_y_no_inserta_nada(db_session, handler):
    with pytest.raises(BCVFetchError):
        await sync_daily_rate(db_session, _fetcher(handler), today=D)
    count = (await db_session.execute(select(func.count()).select_from(ExchangeRateDB).where(ExchangeRateDB.date == D))).scalar()
    assert count == 0


@pytest.mark.asyncio
async def test_job_bcv_sync_usa_sync_daily_rate(db_session, monkeypatch):
    from src.jobs import bcv_sync

    calls = []

    async def fake(session):
        calls.append(session)
        return None, False

    monkeypatch.setattr(bcv_sync, "sync_daily_rate", fake)
    await bcv_sync.run(db_session)
    assert calls == [db_session]


def test_solo_bcv_sync_esta_registrado_a_las_6_de_caracas():
    from src.jobs.runner import JOBS, build_scheduler

    assert [name for name, _, _ in JOBS] == ["bcv_sync"]
    trigger = JOBS[0][2]
    assert str(trigger.timezone) == "America/Caracas"
    assert {f.name: str(f) for f in trigger.fields}["hour"] == "6"
    assert {f.name: str(f) for f in trigger.fields}["minute"] == "0"
    assert [j.id for j in build_scheduler().get_jobs()] == ["bcv_sync"]
