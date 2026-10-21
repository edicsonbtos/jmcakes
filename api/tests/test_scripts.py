"""`bootstrap` y `seed` (07 §5 y 09 §E1 — Datos): idempotentes y coherentes con las invariantes."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import func, select

from scripts.bootstrap import BootstrapError, check_config, run_bootstrap
from src.config import Settings
from src.core.security import verify_password
from src.db.enums import RateType, UserRole
from src.domain.cash_accounts.db_models import CashAccountDB
from src.domain.catalog.db_models import CategoryDB, ProductDB
from src.domain.customers.db_models import CustomerDB
from src.domain.exchange_rates.db_models import ExchangeRateDB
from src.domain.payment_methods.db_models import BankAccountDB, PaymentMethodDB
from src.domain.receivables.db_models import ReceivableDB, ReceivableItemDB
from src.domain.users.db_models import UserDB
from tests.helpers import assert_money_invariants

pytestmark = pytest.mark.asyncio


def cfg(**kw) -> Settings:
    base = dict(BOOTSTRAP_ADMIN_PHONE="", BOOTSTRAP_ADMIN_PASSWORD="", SEED_DEMO=False, SEED_PASSWORD="")
    return Settings(**{**base, **kw})


async def count(session, model) -> int:
    return (await session.execute(select(func.count()).select_from(model))).scalar()


async def test_seed_demo_sin_seed_password_falla():
    with pytest.raises(BootstrapError):
        check_config(cfg(SEED_DEMO=True))


async def test_bootstrap_crea_el_admin_con_cambio_de_clave_obligatorio_una_sola_vez(db_session):
    c = cfg(BOOTSTRAP_ADMIN_PHONE="0414-999.88.77", BOOTSTRAP_ADMIN_PASSWORD="Primera-clave-1")
    first = await run_bootstrap(db_session, c)
    second = await run_bootstrap(db_session, c)
    assert first["admin"] == second["admin"]
    admins = (await db_session.execute(select(UserDB).where(UserDB.role == UserRole.ADMIN))).scalars().all()
    assert len(admins) == 1
    admin = admins[0]
    assert admin.phone == "+584149998877" and admin.must_change_password is True
    assert verify_password("Primera-clave-1", admin.password_hash)


async def test_bootstrap_sin_variables_no_crea_nada(db_session):
    summary = await run_bootstrap(db_session, cfg())
    assert summary == {"admin": None, "seed": None}
    assert await count(db_session, UserDB) == 0


async def test_seed_de_e1_dos_veces_es_idempotente_y_cuadra(db_session, money_double):
    c = cfg(BOOTSTRAP_ADMIN_PHONE="+584149998877", BOOTSTRAP_ADMIN_PASSWORD="Primera-clave-1",
            SEED_DEMO=True, SEED_PASSWORD="Demo-clave-123")
    await run_bootstrap(db_session, c)
    snapshot = {m.__name__: await count(db_session, m) for m in (
        UserDB, CategoryDB, ProductDB, PaymentMethodDB, BankAccountDB, CashAccountDB, ExchangeRateDB,
        CustomerDB, ReceivableDB, ReceivableItemDB)}
    await run_bootstrap(db_session, c)
    again = {m.__name__: await count(db_session, m) for m in (
        UserDB, CategoryDB, ProductDB, PaymentMethodDB, BankAccountDB, CashAccountDB, ExchangeRateDB,
        CustomerDB, ReceivableDB, ReceivableItemDB)}
    assert snapshot == again
    assert snapshot == {
        "UserDB": 1, "CategoryDB": 3, "ProductDB": 12, "PaymentMethodDB": 4, "BankAccountDB": 4,
        "CashAccountDB": 3, "ExchangeRateDB": 2, "CustomerDB": 3, "ReceivableDB": 1, "ReceivableItemDB": 2,
    }

    products = (await db_session.execute(select(ProductDB))).scalars().all()
    assert all(p.price > 0 and p.retail_price and p.retail_price > p.price for p in products)
    caja = (await db_session.execute(select(BankAccountDB).where(BankAccountDB.account_label == "Caja"))).scalar_one()
    assert (await db_session.get(CashAccountDB, caja.cash_account_id)).name == "Caja USD"
    types = {r.rate_type for r in (await db_session.execute(select(ExchangeRateDB))).scalars()}
    assert types == {RateType.BCV, RateType.MANUAL}

    # Saldos anteriores vía MoneyService.open_balance (B-E1b): $50 de deuda y $10 a favor.
    assert sorted(call["amount"] for call in money_double.open_balance_calls) == [Decimal("-10.00"), Decimal("50.00")]
    fiado = (await db_session.execute(select(ReceivableDB))).scalar_one()
    items = (await db_session.execute(select(ReceivableItemDB))).scalars().all()
    assert fiado.amount == sum(i.line_total for i in items) and fiado.amount > 0
    await assert_money_invariants(db_session)


async def test_seed_sin_admin_del_bootstrap_crea_admin_demo_con_seed_password(db_session, money_double):
    await run_bootstrap(db_session, cfg(SEED_DEMO=True, SEED_PASSWORD="Demo-clave-123"))
    admin = (await db_session.execute(select(UserDB).where(UserDB.role == UserRole.ADMIN))).scalar_one()
    assert admin.phone == "+584120000001" and admin.must_change_password
    assert verify_password("Demo-clave-123", admin.password_hash)
