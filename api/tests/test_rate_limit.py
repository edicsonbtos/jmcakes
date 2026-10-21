"""Límite de intentos del login: por `X-Real-IP` (nunca el primer `X-Forwarded-For`) y por teléfono."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio

LOGIN = "/api/v1/auth/login"


async def test_misma_ip_real_con_xff_distinto_en_cada_intento_el_sexto_da_429(client):
    for i in range(5):
        r = await client.post(
            LOGIN,
            json={"phone": f"+58414000000{i}", "password": "x"},
            headers={"X-Real-IP": "190.1.2.3", "X-Forwarded-For": f"10.0.0.{i}"},
        )
        assert r.status_code == 401, r.text
    r = await client.post(
        LOGIN, json={"phone": "+584140000009", "password": "x"},
        headers={"X-Real-IP": "190.1.2.3", "X-Forwarded-For": "10.0.0.99"},
    )
    assert r.status_code == 429
    assert r.json() == {"detail": "Demasiados intentos. Espera un minuto.", "code": "RATE_LIMITED", "meta": {}}


async def test_mismo_telefono_desde_ips_distintas_da_429(client):
    statuses = []
    for i in range(6):
        r = await client.post(LOGIN, json={"phone": "0414-555.00.00", "password": "x"}, headers={"X-Real-IP": f"190.9.9.{i}"})
        statuses.append(r.status_code)
    assert statuses[:5] == [401] * 5
    assert statuses[5] == 429


async def test_el_telefono_se_cuenta_normalizado(client):
    """Escribir el mismo número de formas distintas no evita el límite."""
    forms = ["04145550001", "0414-555.00.01", "+584145550001", "58 414 5550001", "414 5550001", "0414 555 0001"]
    statuses = [
        (await client.post(LOGIN, json={"phone": p, "password": "x"}, headers={"X-Real-IP": f"200.0.0.{i}"})).status_code
        for i, p in enumerate(forms)
    ]
    assert statuses[-1] == 429


async def test_ips_distintas_y_telefonos_distintos_no_se_limitan(client):
    for i in range(8):
        r = await client.post(
            LOGIN, json={"phone": f"+5841466600{i:02d}", "password": "x"}, headers={"X-Real-IP": f"201.0.0.{i}"}
        )
        assert r.status_code == 401
