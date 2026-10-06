"""Escenarios de aceptación (docs/plan/07-pruebas.md §2) + prueba de propiedades.

Correr:  python -m pytest spec -q
Q1 traduce estos mismos escenarios a pruebas HTTP contra la API real.
"""
from decimal import Decimal as D

import pytest
from hypothesis import given, settings, strategies as st

from money_model import OS, PS, RS, DomainError, Shop

DAY = 24 * 60


@pytest.fixture
def shop():
    return Shop()


def cash_customer_with_wallet(shop, amount):
    c = shop.register()
    p = shop.report_payment(c.id, amount, reference=f"R{c.id}-topup")
    shop.approve(p.id)
    return c


# --- E1: contado con billetera suficiente: entra a cocina sin intervención del admin
def test_e1_cash_wallet_covers_everything(shop):
    c = cash_customer_with_wallet(shop, "50.00")
    o = shop.create_order(c.id, "30.00", "k1")
    assert o.status == OS.CONFIRMED and o.payment_status == "PAID"
    assert c.wallet == D("20.00")
    assert ("order.confirmed", o.id) in shop.kitchen_events
    shop.check_invariants()


# --- E2: contado con billetera parcial: usa saldo, pide diferencia, entra al aprobar (D-4, D-5)
def test_e2_cash_partial_wallet_then_payment(shop):
    c = cash_customer_with_wallet(shop, "10.00")
    o = shop.create_order(c.id, "25.00", "k1")
    assert o.status == OS.AWAITING_PAYMENT and o.payment_status == "PARTIALLY_PAID"
    assert c.wallet == D("0.00") and shop.amount_due(o.id) == D("15.00")
    assert ("order.confirmed", o.id) not in shop.kitchen_events
    p = shop.report_payment(c.id, "15.00", reference="ABC", order_id=o.id)
    assert o.status == OS.AWAITING_PAYMENT          # reportar no mueve dinero
    shop.approve(p.id)
    assert o.status == OS.CONFIRMED and c.wallet == D("0.00")
    for s in (OS.READY, OS.OUT_FOR_DELIVERY, OS.DELIVERED):
        shop.transition(o.id, s)
    shop.check_invariants()


def test_e2b_overpayment_goes_to_wallet(shop):
    c = shop.register()
    o = shop.create_order(c.id, "12.00", "k1")
    p = shop.report_payment(c.id, "20.00", reference="X1", order_id=o.id)
    shop.approve(p.id)
    assert o.status == OS.CONFIRMED and c.wallet == D("8.00")
    shop.check_invariants()


def test_e2c_underpayment_keeps_waiting_with_smaller_due(shop):
    c = shop.register()
    o = shop.create_order(c.id, "12.00", "k1")
    shop.approve(shop.report_payment(c.id, "5.00", reference="U1", order_id=o.id).id)
    assert o.status == OS.AWAITING_PAYMENT and shop.amount_due(o.id) == D("7.00")
    shop.approve(shop.report_payment(c.id, "7.00", reference="U2", order_id=o.id).id)
    assert o.status == OS.CONFIRMED
    shop.check_invariants()


def test_e2d_rounding_tolerance_bs_conversion(shop):
    c = shop.register()
    o = shop.create_order(c.id, "10.00", "k1")
    shop.approve(shop.report_payment(c.id, "9.99", reference="R1", order_id=o.id).id)
    assert o.status == OS.CONFIRMED and o.rounding_adjustment == D("0.01")
    shop.check_invariants()


def test_rejected_payment_moves_no_money_and_reference_can_be_reused(shop):
    c = shop.register()
    o = shop.create_order(c.id, "10.00", "k1")
    p = shop.report_payment(c.id, "10.00", reference="SAME", order_id=o.id)
    with pytest.raises(DomainError) as e:
        shop.report_payment(c.id, "10.00", reference="SAME", order_id=o.id)
    assert e.value.code == "DUPLICATE_REFERENCE"
    shop.reject(p.id)
    assert c.wallet == D("0.00") and o.status == OS.AWAITING_PAYMENT
    p2 = shop.report_payment(c.id, "10.00", reference="SAME", order_id=o.id)
    shop.approve(p2.id)
    assert o.status == OS.CONFIRMED
    shop.check_invariants()


def test_cancel_awaiting_refunds_partial_wallet(shop):
    c = cash_customer_with_wallet(shop, "10.00")
    o = shop.create_order(c.id, "25.00", "k1")
    shop.cancel(o.id, by="customer")
    assert o.status == OS.CANCELLED and c.wallet == D("10.00") and o.payment_status == "REFUNDED"
    shop.check_invariants()


def test_customer_cannot_cancel_once_preparing(shop):
    c = cash_customer_with_wallet(shop, "10.00")
    o = shop.create_order(c.id, "5.00", "k1")
    shop.transition(o.id, OS.PREPARING)
    with pytest.raises(DomainError):
        shop.cancel(o.id, by="customer")
    shop.cancel(o.id, by="admin")
    assert ("order.cancelled", o.id) in shop.kitchen_events and c.wallet == D("10.00")
    shop.check_invariants()


def test_auto_cancel_skips_orders_with_payment_in_review(shop):
    c = shop.register()
    o1 = shop.create_order(c.id, "10.00", "a")
    o2 = shop.create_order(c.id, "10.00", "b")
    shop.report_payment(c.id, "10.00", reference="P", order_id=o2.id)
    shop.now += 2 * DAY
    assert shop.run_unpaid_auto_cancel() == [o1.id]
    assert o2.status == OS.AWAITING_PAYMENT
    shop.check_invariants()


def test_late_approval_after_cancel_money_stays_in_wallet(shop):
    c = shop.register()
    o = shop.create_order(c.id, "10.00", "a")
    p = shop.report_payment(c.id, "10.00", reference="P", order_id=o.id)
    shop.cancel(o.id)
    shop.approve(p.id)
    assert c.wallet == D("10.00")
    shop.check_invariants()


def test_idempotent_order_creation(shop):
    c = cash_customer_with_wallet(shop, "10.00")
    o1 = shop.create_order(c.id, "5.00", "same-key")
    o2 = shop.create_order(c.id, "5.00", "same-key")
    assert o1 is o2 and c.wallet == D("5.00")


# --- E3: crédito: confirmado al instante, deuda, recarga salda FIFO y sobra a favor
def test_e3_credit_flow(shop):
    c = shop.register()
    shop.enable_credit(c.id, "100.00")
    o1 = shop.create_order(c.id, "60.00", "a")
    assert o1.status == OS.CONFIRMED and o1.payment_status == "ON_CREDIT"
    with pytest.raises(DomainError) as e:
        shop.create_order(c.id, "50.00", "b")
    assert e.value.code == "CREDIT_LIMIT_EXCEEDED" and e.value.meta["available"] == D("40.00")
    shop.approve(shop.report_payment(c.id, "40.00", reference="T1").id)
    assert shop.open_debt(c.id) == D("20.00") and c.wallet == D("0.00")
    o3 = shop.create_order(c.id, "50.00", "c")
    assert o3.status == OS.CONFIRMED and shop.open_debt(c.id) == D("70.00")
    shop.approve(shop.report_payment(c.id, "100.00", reference="T2").id)
    assert shop.open_debt(c.id) == D("0.00") and c.wallet == D("30.00")
    o4 = shop.create_order(c.id, "20.00", "d")
    assert o4.payment_status == "PAID" and c.wallet == D("10.00")
    shop.check_invariants()


def test_credit_overdue_blocks_new_orders(shop):
    c = shop.register()
    shop.enable_credit(c.id, "100.00", days=7)
    shop.create_order(c.id, "10.00", "a")
    shop.now += 15 * DAY
    with pytest.raises(DomainError) as e:
        shop.create_order(c.id, "1.00", "b")
    assert e.value.code == "OVERDUE_DEBT"


def test_credit_cancel_voids_receivable_and_refunds_paid_part(shop):
    c = shop.register()
    shop.enable_credit(c.id, "100.00")
    o = shop.create_order(c.id, "30.00", "a")
    shop.approve(shop.report_payment(c.id, "10.00", reference="T").id)
    assert shop.receivables[o.receivable_id].paid == D("10.00")
    shop.cancel(o.id)
    assert shop.receivables[o.receivable_id].status == RS.VOID and c.wallet == D("10.00")
    shop.check_invariants()


def test_reduce_credit_order(shop):
    c = shop.register()
    shop.enable_credit(c.id, "100.00")
    o = shop.create_order(c.id, "30.00", "a")
    shop.approve(shop.report_payment(c.id, "25.00", reference="T").id)
    shop.reduce_order(o.id, "20.00")
    assert shop.receivables[o.receivable_id].amount == D("20.00")
    assert c.wallet == D("5.00")
    shop.check_invariants()


def test_reduce_cash_awaiting_order_can_confirm_it(shop):
    c = cash_customer_with_wallet(shop, "8.00")
    o = shop.create_order(c.id, "10.00", "a")
    shop.reduce_order(o.id, "8.00")
    assert o.status == OS.CONFIRMED
    shop.check_invariants()


def test_reversal_without_balance_creates_debt(shop):
    c = shop.register()
    p = shop.report_payment(c.id, "20.00", reference="T")
    shop.approve(p.id)
    shop.create_order(c.id, "15.00", "a")
    shop.reverse(p.id)
    assert c.wallet == D("0.00") and shop.open_debt(c.id) == D("15.00")
    shop.check_invariants()


def test_manual_charge_paid_from_wallet(shop):
    c = cash_customer_with_wallet(shop, "5.00")
    r = shop.manual_charge(c.id, "8.00")
    assert r.status == RS.PARTIAL and c.wallet == D("0.00")
    shop.check_invariants()


# --- Propiedades: cualquier secuencia de operaciones respeta las invariantes
OPS = st.lists(st.tuples(
    st.sampled_from(["order", "pay", "pay_order", "approve", "reject", "cancel", "advance",
                     "reverse", "adjust", "reduce", "charge", "time", "credit"]),
    st.integers(min_value=0, max_value=50),
    st.integers(min_value=1, max_value=9000),
), max_size=60)


@settings(max_examples=400, deadline=None)
@given(OPS)
def test_property_invariants_hold(ops):
    shop = Shop()
    custs = [shop.register() for _ in range(3)]
    seq = 0
    for op, i, cents in ops:
        seq += 1
        amount = str(D(cents) / 100)
        c = custs[i % len(custs)]
        orders = [o for o in shop.orders.values()]
        pays = [p for p in shop.payments.values()]
        try:
            if op == "order":
                shop.create_order(c.id, amount, f"k{seq}")
            elif op == "credit":
                shop.enable_credit(c.id, str(D(cents) / 10))
            elif op == "pay":
                shop.report_payment(c.id, amount, reference=f"r{seq}")
            elif op == "pay_order" and orders:
                o = orders[i % len(orders)]
                shop.report_payment(o.customer_id, amount, reference=f"r{seq}", order_id=o.id)
            elif op == "approve" and pays:
                shop.approve(pays[i % len(pays)].id)
            elif op == "reject" and pays:
                shop.reject(pays[i % len(pays)].id)
            elif op == "reverse" and pays:
                shop.reverse(pays[i % len(pays)].id)
            elif op == "cancel" and orders:
                shop.cancel(orders[i % len(orders)].id, by="customer" if i % 2 else "admin")
            elif op == "advance" and orders:
                o = orders[i % len(orders)]
                nxt = {OS.CONFIRMED: OS.PREPARING, OS.PREPARING: OS.READY, OS.READY: OS.OUT_FOR_DELIVERY,
                       OS.OUT_FOR_DELIVERY: OS.DELIVERED}.get(o.status)
                if nxt:
                    shop.transition(o.id, nxt)
            elif op == "reduce" and orders:
                o = orders[i % len(orders)]
                shop.reduce_order(o.id, str(max(D("0.01"), (o.total * D(i % 10 + 1) / 10).quantize(D("0.01")))))
            elif op == "adjust":
                shop.adjust(c.id, amount if i % 2 else "-" + amount)
            elif op == "charge":
                shop.manual_charge(c.id, amount)
            elif op == "time":
                shop.now += cents
                shop.run_unpaid_auto_cancel()
        except DomainError:
            pass
        shop.check_invariants()
