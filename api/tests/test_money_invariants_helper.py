"""`assert_money_invariants` copia literal el SQL de 02 y detecta descuadres."""
from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import text

from tests.helpers import (
    I9_ENUM_CAST,
    INVARIANT_QUERIES,
    INVARIANTS_SQL,
    assert_money_invariants,
    money_invariant_violations,
)

DOC02 = (Path(__file__).resolve().parents[2] / "docs" / "plan" / "02-modelo-de-datos.md").read_text(encoding="utf-8")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def test_el_sql_es_copia_literal_de_02():
    block = DOC02[DOC02.index("## Invariantes"):].split("```sql")[1].split("```")[0]
    assert _norm(block.replace(*I9_ENUM_CAST)) == _norm(INVARIANTS_SQL)
    names = [n for n, _ in INVARIANT_QUERIES]
    assert names == ["I-1a", "I-1b", "I-2", "I-3", "I-4", "I-5", "I-6", "I-7", "I-7", "I-9"]


@pytest.mark.asyncio
async def test_base_vacia_cumple_las_invariantes(db_session):
    await assert_money_invariants(db_session)


@pytest.mark.asyncio
async def test_detecta_billetera_sin_ledger(db_session, customer_cash):
    await db_session.execute(text('UPDATE customers SET "walletBalance" = 5 WHERE id = :id'), {"id": customer_cash.id})
    bad = await money_invariant_violations(db_session)
    assert customer_cash.id in bad["I-1a"] and customer_cash.id in bad["I-6"]
    with pytest.raises(AssertionError):
        await assert_money_invariants(db_session)


@pytest.mark.asyncio
async def test_pedido_a_credito_cuadra_y_un_payment_status_falso_se_detecta(db_session, customer_credit):
    """Ejercita I-2, I-4, I-5 e I-9 con tipos reales (enums nativos) sobre las tablas de pedidos de E1."""
    from src.db.enums import (
        FulfillmentType,
        OrderChannel,
        OrderPaymentStatus,
        OrderStatus,
        PaymentMode,
        ReceivableSource,
    )
    from src.domain.orders.db_models import OrderDB
    from src.domain.receivables.db_models import ReceivableDB
    from src.utils.date_utils import utcnow

    now = utcnow()
    order = OrderDB(customer_id=customer_credit.id, channel=OrderChannel.BACKOFFICE, status=OrderStatus.CONFIRMED,
                    payment_mode=PaymentMode.CREDIT, payment_status=OrderPaymentStatus.ON_CREDIT,
                    fulfillment_type=FulfillmentType.ASAP, due_at=now, subtotal=Decimal("10.00"),
                    delivery_fee=Decimal("0.00"), total=Decimal("10.00"))
    db_session.add(order)
    await db_session.flush()
    await db_session.refresh(order)
    assert order.number >= 1001
    db_session.add(ReceivableDB(customer_id=customer_credit.id, source=ReceivableSource.ORDER, order_id=order.id,
                                amount=Decimal("10.00"), issued_at=now, due_at=now))
    await db_session.flush()
    await assert_money_invariants(db_session)

    order.payment_status = OrderPaymentStatus.PAID
    await db_session.flush()
    assert order.id in (await money_invariant_violations(db_session))["I-9"]


@pytest.mark.asyncio
async def test_detecta_cuenta_del_negocio_descuadrada(db_session, money_setup):
    acc = money_setup.cash_accounts["Caja USD"]
    acc.balance = Decimal("3.00")
    await db_session.flush()
    bad = await money_invariant_violations(db_session)
    assert acc.id in bad["I-7"]
