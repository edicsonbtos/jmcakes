"""El OpenAPI expone exactamente el inventario de la etapa (E1: 52 operaciones, docs/plan/09 §E1 — API).

Al pasar a E2 se cambia `STAGE_INVENTORY` hacia el de 08 (111 operaciones con todo).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from scripts.export_openapi import operations
from src.main import app

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "docs" / "plan"
E1_COUNT = 52


def parse_inventory(text: str, marker: str) -> set[tuple[str, str]]:
    """Expande `GET|POST /a/b|c` a operaciones (método, ruta), igual que `spec/test_plan_consistency.py`."""
    block = text[text.index(marker):].split("```")[1]
    ops: set[tuple[str, str]] = set()
    for part in re.split(r"\s·\s|\n", block):
        part = part.strip()
        if not part:
            continue
        methods, _, route = part.partition(" ")
        base, _, last = route.rpartition("/")
        for m in methods.split("|"):
            for leaf in last.split("|"):
                ops.add((m, f"{base}/{leaf}"))
    return ops


STAGE_INVENTORY = parse_inventory((PLAN / "09-etapas-admin-primero.md").read_text(encoding="utf-8"), "**Inventario E1**")
FULL_INVENTORY = parse_inventory((PLAN / "08-api-endpoints.md").read_text(encoding="utf-8"), "## Inventario")


def test_inventario_de_e1_tiene_52_operaciones_y_es_parte_del_de_08():
    assert len(STAGE_INVENTORY) == E1_COUNT
    assert STAGE_INVENTORY <= FULL_INVENTORY


def test_el_openapi_tiene_exactamente_el_inventario_de_e1():
    ops = set(operations(app.openapi()))
    assert ops - STAGE_INVENTORY == set(), "operaciones de más (no existen en E1)"
    assert STAGE_INVENTORY - ops == set(), "operaciones que faltan"


def test_export_openapi_count_imprime_52():
    out = subprocess.run(
        [sys.executable, "-m", "scripts.export_openapi", "--count"],
        cwd=ROOT / "api", capture_output=True, text=True, check=True,
    )
    assert out.stdout.strip() == str(E1_COUNT)


def test_contracts_openapi_json_esta_al_dia():
    """`export_openapi --check`: el contrato commiteado es el que genera la API."""
    out = subprocess.run(
        [sys.executable, "-m", "scripts.export_openapi", "--check"],
        cwd=ROOT / "api", capture_output=True, text=True,
    )
    assert out.returncode == 0, out.stderr


def test_ejemplo_de_access_token_es_un_jwt_admin_firmado_con_el_secreto_del_mock():
    import jwt

    from src.config import DEV_MOCK_JWT_SECRET

    spec = json.loads((ROOT / "contracts" / "openapi.json").read_text(encoding="utf-8"))
    example = spec["components"]["schemas"]["AuthTokens"]["example"]
    claims = jwt.decode(example["accessToken"], DEV_MOCK_JWT_SECRET, algorithms=["HS256"])
    assert claims["role"] == "ADMIN" and claims["exp"] >= 4070908800
    me = spec["components"]["schemas"]["MeOut"]["example"]
    assert me["user"]["id"] == claims["sub"] and me["user"]["role"] == "ADMIN"


def test_dinero_y_fechas_del_contrato_son_strings():
    spec = app.openapi()
    for name in ("AdminCustomer", "FiadoQuote", "ManualPaymentQuote", "DashboardSummary", "AdminProduct"):
        schema = spec["components"]["schemas"][name]
        for prop, sub in schema["properties"].items():
            variants = sub.get("anyOf", [sub])
            for v in variants:
                assert v.get("type") != "number", (name, prop)
    assert spec["components"]["schemas"]["AdminCustomer"]["properties"]["createdAt"]["format"] == "date-time"


def test_errores_de_validacion_usan_el_formato_propio():
    spec = json.dumps(app.openapi())
    assert "HTTPValidationError" not in spec
    assert '"ErrorOut"' in spec
