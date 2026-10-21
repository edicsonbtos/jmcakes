"""Configuración y aislamiento: variables de `.env.example`, base de pruebas y utilidades de tiempo y dinero."""
from __future__ import annotations

import re
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from src.config import Settings, normalize_db_url, settings
from src.db.session import get_engine
from src.utils.date_utils import as_caracas_date, caracas_day_bounds_utc, end_of_day_caracas_utc, iso_z
from src.utils.money import q2, to_ves
from src.utils.phone import InvalidPhone, normalize_phone, phone_digits_query
from tests.conftest import TEST_DATABASE_URL

API = Path(__file__).resolve().parents[1]


def test_env_example_tiene_exactamente_las_claves_de_settings():
    text = (API / ".env.example").read_text(encoding="utf-8")
    keys = set(re.findall(r"^([A-Z][A-Z0-9_]+)=", text, re.M))
    assert keys == set(Settings.model_fields)


def test_la_api_usa_la_base_de_pruebas():
    assert str(get_engine().url.render_as_string(hide_password=False)) == normalize_db_url(TEST_DATABASE_URL)
    assert settings.DATABASE_URL_DIRECT == "" and settings.SCHEDULER_ENABLED is False


def test_bajo_pytest_no_se_lee_dotenv():
    assert Settings.model_config["env_file"] is None


def test_jwt_secret_del_mock_no_sirve_en_produccion():
    prod = Settings(ENVIRONMENT="production", JWT_SECRET="dev-mock-secret-no-usar-en-prod")
    with pytest.raises(RuntimeError):
        _ = prod.jwt_secret
    with pytest.raises(RuntimeError):
        _ = Settings(ENVIRONMENT="production", JWT_SECRET="").jwt_secret
    assert Settings(ENVIRONMENT="production", JWT_SECRET="otro-secreto-largo").jwt_secret == "otro-secreto-largo"


def test_normaliza_url_al_driver_psycopg():
    assert normalize_db_url("postgres://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert normalize_db_url("postgresql://u:p@h/db") == "postgresql+psycopg://u:p@h/db"


def test_dia_de_caracas_y_limites_en_utc():
    # 22:30 VET del 20/10 = 02:30 UTC del 21/10 → cuenta el 20/10.
    assert as_caracas_date(datetime(2026, 10, 21, 2, 30)) == date(2026, 10, 20)
    start, end = caracas_day_bounds_utc(date(2026, 10, 20))
    assert (start, end) == (datetime(2026, 10, 20, 4, 0), datetime(2026, 10, 21, 4, 0))
    assert end_of_day_caracas_utc(date(2026, 10, 20)) == datetime(2026, 10, 21, 3, 59, 59, 999999)
    assert iso_z(datetime(2026, 10, 21, 2, 30)) == "2026-10-21T02:30:00.000Z"
    assert iso_z(datetime(2026, 10, 21, 2, 30, tzinfo=timezone.utc)) == "2026-10-21T02:30:00.000Z"


def test_dinero_redondea_half_up_y_bs_en_null_sin_tasa():
    assert q2("0.125") == Decimal("0.13") and q2("2.675") == Decimal("2.68")
    assert to_ves(Decimal("10.00"), Decimal("182.4550")) == Decimal("1824.55")
    assert to_ves(Decimal("10.00"), None) is None


@pytest.mark.parametrize(
    "raw,expected",
    [("0414-123.45.67", "+584141234567"), ("414 1234567", "+584141234567"), ("+58 414 123 4567", "+584141234567"),
     ("58-412-7654321", "+584127654321"), ("0212-5551234", "+582125551234"), ("+1 305 555 0100", "+13055550100")],
)
def test_telefono_a_e164(raw, expected):
    assert normalize_phone(raw) == expected


@pytest.mark.parametrize("raw", ["", "0414", "12345", "0914-1234567", "abc"])
def test_telefono_invalido(raw):
    with pytest.raises(InvalidPhone):
        normalize_phone(raw)


def test_busqueda_por_digitos_trata_el_cero_inicial_como_58():
    assert phone_digits_query("0414-12") == "5841412"
    assert phone_digits_query("+58 414") == "58414"
