"""Fábricas de 08 §Interfaces (E1): importables, cumplen su Protocol y los stubs hacen lo descrito."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import func, select

from src.core.errors import AppError, ErrorCode
from src.domain.audit.db_models import AuditLogDB
from src.domain.receivables.db_models import ReceivableDB
from src.domain.wallet.db_models import WalletMovementDB
from src.services import interfaces, registry
from tests.helpers import assert_money_invariants

PROTOCOLS = {
    "customers": interfaces.CustomersService,
    "settings": interfaces.SettingsService,
    "audit": interfaces.AuditService,
    "rates": interfaces.RateService,
    "finance": interfaces.FinanceQueries,
    "money": interfaces.MoneyService,
}


def test_todas_las_fabricas_de_e1_estan_registradas():
    assert set(registry.FACTORIES) == set(PROTOCOLS)


@pytest.mark.parametrize("name", sorted(PROTOCOLS))
def test_cada_fabrica_es_importable_y_cumple_su_protocol(name):
    impl = registry.get(name)
    assert isinstance(impl, PROTOCOLS[name]), name


def test_override_sustituye_y_restaura():
    original = registry.get("money")
    double = object()
    with registry.override("money", double):
        assert registry.get("money") is double
    assert registry.get("money") is original
    with pytest.raises(KeyError):
        registry.get("orders")  # las interfaces de pedidos llegan en E2


@pytest.mark.asyncio
async def test_customers_get_for_update_y_get_by_user(db_session, customer_cash):
    svc = registry.get("customers")
    assert (await svc.get_for_update(db_session, customer_cash.id)).id == customer_cash.id
    assert await svc.get_by_user(db_session, "no-existe") is None
    with pytest.raises(AppError) as info:
        await svc.get_for_update(db_session, "no-existe")
    assert info.value.code is ErrorCode.NOT_FOUND


@pytest.mark.asyncio
async def test_audit_log_agrega_fila_sin_commit_y_serializa_dinero(db_session, admin):
    row = await registry.get("audit").log(
        db_session, action="prueba.accion", entity_type="customer", entity_id="c1", actor_id=admin.id,
        data_before={"creditLimit": Decimal("0.00")}, data_after={"creditLimit": Decimal("100.00")},
    )
    assert row.id and row.actor_type == "USER" and row.data_after == {"creditLimit": "100.00"}
    system = await registry.get("audit").log(db_session, action="job.algo", entity_type="system")
    assert system.actor_type == "SYSTEM"


@pytest.mark.asyncio
async def test_settings_get_devuelve_defaults_de_02_y_update_valida(db_session):
    svc = registry.get("settings")
    business = await svc.get(db_session, "business")
    credit = await svc.get(db_session, "credit")
    assert business.name == "Panadería" and credit.defaultDays == 7 and credit.blockOverdueDays == 7
    assert (await svc.get(db_session, "payments")).roundingToleranceUsd == Decimal("0.01")
    assert (await svc.get(db_session, "orders")).openingTime == "06:00"

    updated = await svc.update(db_session, "credit", {"defaultDays": 15})
    assert updated.defaultDays == 15 and updated.blockOverdueDays == 7
    assert (await svc.get(db_session, "credit")).defaultDays == 15  # la caché se invalidó

    with pytest.raises(AppError) as info:
        await svc.update(db_session, "credit", {"defaultDays": -1})
    assert info.value.code is ErrorCode.INVALID_SETTINGS and info.value.detail.startswith("Configuración inválida:")
    with pytest.raises(AppError):
        await svc.get(db_session, "no-existe")


@pytest.mark.asyncio
async def test_settings_caché_se_respeta_y_se_limpia(db_session):
    from src.domain.settings.db_models import AppSettingDB
    from src.domain.settings.service import clear_settings_cache

    svc = registry.get("settings")
    assert (await svc.get(db_session, "business")).name == "Panadería"
    db_session.add(AppSettingDB(section="business", data={"name": "Otro nombre"}))
    await db_session.flush()
    assert (await svc.get(db_session, "business")).name == "Panadería"  # caché de 30 s
    clear_settings_cache()
    assert (await svc.get(db_session, "business")).name == "Otro nombre"


@pytest.mark.asyncio
async def test_stub_de_finance_devuelve_ceros(db_session, customer_cash, customer_credit):
    fq = registry.get("finance")
    balances = await fq.balances_for(db_session, [customer_cash.id, customer_credit.id, "desconocido"])
    assert set(balances) == {customer_cash.id, customer_credit.id}
    b = balances[customer_cash.id]
    assert (b.wallet_balance, b.open_debt, b.overdue_debt, b.balance) == (Decimal("0"),) * 4
    sub = fq.debt_subquery()
    assert {"customerId", "openDebt", "overdueDebt", "walletBalance", "balance"} <= set(sub.c.keys())
    rows = (await db_session.execute(select(sub).where(sub.c.customerId == customer_cash.id))).all()
    assert len(rows) == 1 and rows[0].openDebt == 0


@pytest.mark.asyncio
async def test_stub_de_money_open_balance_no_escribe_dinero(db_session, customer_cash):
    await registry.get("money").open_balance(db_session, customer_cash.id, Decimal("50.00"), "Saldo anterior", None)
    for model in (ReceivableDB, WalletMovementDB):
        assert (await db_session.execute(select(func.count()).select_from(model))).scalar() == 0
    await assert_money_invariants(db_session)


@pytest.mark.asyncio
async def test_money_double_registra_open_balance(db_session, customer_cash, money_double):
    await registry.get("money").open_balance(db_session, customer_cash.id, Decimal("-10.00"), "A favor", "u1")
    assert money_double.open_balance_calls == [
        {"customer_id": customer_cash.id, "amount": Decimal("-10.00"), "note": "A favor", "actor_id": "u1"}
    ]


@pytest.mark.asyncio
async def test_audit_no_hace_commit(db_session, monkeypatch):
    async def _no_commit(*a, **k):
        raise AssertionError("AuditService.log no debe hacer commit")

    monkeypatch.setattr(db_session, "commit", _no_commit)
    await registry.get("audit").log(db_session, action="x", entity_type="y")
    assert (await db_session.execute(select(func.count()).select_from(AuditLogDB))).scalar() >= 1
