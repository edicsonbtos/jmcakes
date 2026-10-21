"""Migraciones: upgrade → downgrade base → upgrade sobre una base aparte, `alembic check` y esquema de 02."""
from __future__ import annotations

import pytest
from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text

from src.config import normalize_db_url
from src.db.base import Base
import src.db.models_registry  # noqa: F401
from tests.conftest import TEST_DATABASE_URL, alembic_config, drop_database, ensure_database

TABLES_02 = {
    "users", "refresh_tokens", "idempotency_records", "device_tokens", "customers", "categories", "products",
    "price_history", "orders", "order_items", "order_events", "payment_methods", "bank_accounts", "payments",
    "wallet_movements", "receivables", "receivable_items", "cash_accounts", "cash_account_transactions",
    "exchange_rates", "app_settings", "audit_logs", "daily_closings", "files",
}

NAMED_CONSTRAINTS = {
    "uq_users_phone", "uq_orders_customer_idem", "uq_payments_customer_idem", "uq_idempotency_records_scope_key",
    "ck_customers_wallet_nonneg", "ck_receivables_paid_range", "ck_cash_account_transactions_amount_sign",
    "ck_wallet_movements_amount_nonzero", "ck_wallet_movements_adjustment_note",
}

MIGRATIONS_URL = TEST_DATABASE_URL.rsplit("/", 1)[0] + "/panaderia_migrations_fnd"


def _sync_url(url: str) -> str:
    return normalize_db_url(url)


def test_los_modelos_registran_todas_las_tablas_de_02():
    assert TABLES_02 <= set(Base.metadata.tables)


def test_una_sola_cabeza():
    script = ScriptDirectory.from_config(alembic_config(TEST_DATABASE_URL))
    assert len(script.get_heads()) == 1


def test_upgrade_downgrade_upgrade_en_base_aparte():
    drop_database(MIGRATIONS_URL)
    ensure_database(MIGRATIONS_URL)
    cfg = alembic_config(MIGRATIONS_URL)
    engine = create_engine(_sync_url(MIGRATIONS_URL))
    try:
        command.upgrade(cfg, "head")
        with engine.connect() as conn:
            assert TABLES_02 <= set(inspect(conn).get_table_names())
        command.downgrade(cfg, "base")
        with engine.connect() as conn:
            assert set(inspect(conn).get_table_names()) <= {"alembic_version"}
            types = conn.execute(text("SELECT typname FROM pg_type t JOIN pg_enum e ON e.enumtypid = t.oid")).all()
            assert types == []
            seqs = conn.execute(text("SELECT relname FROM pg_class WHERE relkind = 'S'")).scalars().all()
            assert seqs == []
        command.upgrade(cfg, "head")
        with engine.connect() as conn:
            assert TABLES_02 <= set(inspect(conn).get_table_names())
            assert conn.execute(text("SELECT nextval('order_number_seq')")).scalar() == 1001
    finally:
        engine.dispose()
        drop_database(MIGRATIONS_URL)


def test_alembic_check_sin_diferencias():
    command.check(alembic_config(TEST_DATABASE_URL))


@pytest.fixture
def sync_engine():
    engine = create_engine(_sync_url(TEST_DATABASE_URL))
    yield engine
    engine.dispose()


def test_restricciones_nombradas_existen(sync_engine):
    with sync_engine.connect() as conn:
        names = set(conn.execute(text("SELECT conname FROM pg_constraint")).scalars().all())
        indexes = set(conn.execute(text("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")).scalars().all())
    assert NAMED_CONSTRAINTS <= names, NAMED_CONSTRAINTS - names
    assert "uq_payments_bank_account_reference_live" in indexes


def test_toda_fk_tiene_indice(sync_engine):
    with sync_engine.connect() as conn:
        insp = inspect(conn)
        missing = []
        for table in TABLES_02:
            indexed = {tuple(ix["column_names"])[0] for ix in insp.get_indexes(table)}
            indexed |= {tuple(uc["column_names"])[0] for uc in insp.get_unique_constraints(table)}
            pk = insp.get_pk_constraint(table)["constrained_columns"]
            indexed |= {pk[0]} if pk else set()
            for fk in insp.get_foreign_keys(table):
                if fk["constrained_columns"][0] not in indexed:
                    missing.append((table, fk["constrained_columns"]))
    assert not missing, missing


def test_indice_parcial_libera_la_referencia_solo_en_rechazo_o_error_de_carga(sync_engine):
    with sync_engine.connect() as conn:
        definition = conn.execute(
            text("SELECT indexdef FROM pg_indexes WHERE indexname = 'uq_payments_bank_account_reference_live'")
        ).scalar_one()
    assert "UNIQUE" in definition
    assert "'REJECTED'" in definition and "'ENTRY_ERROR'" in definition
