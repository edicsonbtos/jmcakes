"""`/api/health` y reglas del arnés: las carpetas de prueba de cada bloque no pueden quedar vacías."""
from __future__ import annotations

from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
BLOCK_DIRS = ("b1", "b2", "b3")


@pytest.mark.asyncio
async def test_health_responde_ok_con_la_base(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["db"] == "ok" and body["version"]


def test_carpetas_de_bloque_existentes_recogen_pruebas(request):
    """Si `tests/b1/`, `tests/b2/` o `tests/b3/` existen, deben recoger al menos una prueba."""
    collected = {Path(str(item.fspath)).resolve() for item in request.session.items}
    for name in BLOCK_DIRS:
        folder = TESTS / name
        if folder.is_dir():
            assert any(folder in p.parents for p in collected), f"tests/{name}/ existe y no recoge pruebas"
