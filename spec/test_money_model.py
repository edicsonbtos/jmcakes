"""Escenarios de aceptación (docs/plan/07-pruebas.md §2) + prueba de propiedades.

Correr:  python -m pytest spec -q
Q1 traduce estos mismos escenarios a pruebas HTTP contra la API real.
"""
from decimal import Decimal as D

import pytest
from hypothesis import given, settings, strategies as st

import ast
import pathlib

from money_model import ERROR_CODES, OS, PS, RS, DomainError, Shop

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


# ---------------- v2.1: hallazgos de la auditoría 1 ----------------
def test_m2_reduce_awaiting_order_refund_is_collected_minus_new_total(shop):
    c = cash_customer_with_wallet(shop, "16.00")
    a = shop.create_order(c.id, "8.00", "a")          # pagado completo
    shop.adjust(c.id, "0.00" if False else "1.00")    # saldo 9
    b = shop.create_order(c.id, "10.00", "b")         # usa 9, falta 1
    a2 = shop.create_order(c.id, "20.00", "a2")       # sin saldo: espera 20
    shop.reduce_order(b.id, "9.00")                   # cobrado 9 = nuevo total → confirma, no devuelve nada
    assert b.status == OS.CONFIRMED and b.paid_from_wallet == D("9.00")
    assert a2.paid_from_wallet == D("0.00") and a.status == OS.CONFIRMED
    shop.check_invariants()


def test_m2_credit_reduction_can_void_receivable_at_zero(shop):
    c = cash_customer_with_wallet(shop, "10.00")
    shop.enable_credit(c.id, "100.00")
    o = shop.create_order(c.id, "30.00", "a")         # 10 billetera + 20 CxC
    shop.reduce_order(o.id, "8.00")                   # devuelve 2, CxC a 0 → VOID
    r = shop.receivables[o.receivable_id]
    assert r.status == RS.VOID and r.void_reason == "REDUCED"
    assert c.wallet == D("2.00") and o.payment_status == "PAID"
    shop.check_invariants()


def test_m4_cash_customer_with_reversal_debt_cannot_order(shop):
    c = shop.register()
    p = shop.report_payment(c.id, "100.00", reference="X")
    shop.approve(p.id)
    shop.create_order(c.id, "100.00", "a")
    shop.reverse(p.id)
    with pytest.raises(DomainError) as e:
        shop.create_order(c.id, "50.00", "b")
    assert e.value.code == "OPEN_DEBT"
    shop.approve(shop.report_payment(c.id, "100.00", reference="Y").id)   # paga la deuda
    assert shop.open_debt(c.id) == D("0.00")
    shop.create_order(c.id, "1.00", "c")
    shop.check_invariants()


def test_m4_overdue_debt_blocks_any_mode(shop):
    c = shop.register()
    shop.enable_credit(c.id, "50.00")
    shop.create_order(c.id, "10.00", "a")
    shop.set_cash(c.id)
    shop.now += 20 * DAY
    with pytest.raises(DomainError) as e:
        shop.create_order(c.id, "1.00", "b")
    assert e.value.code == "OVERDUE_DEBT"


def test_m5_scheduled_soon_keeps_minimum_pay_window(shop):
    c = shop.register()
    o = shop.create_order(c.id, "10.00", "a", due_at=shop.now + 60)   # programado justo al mínimo
    shop.now += 20
    assert shop.run_unpaid_auto_cancel() == [] and o.status == OS.AWAITING_PAYMENT
    shop.now += 15
    assert shop.run_unpaid_auto_cancel() == [o.id]


def test_m5_rejection_after_expiry_reopens_window(shop):
    c = shop.register()
    o = shop.create_order(c.id, "10.00", "a")
    p = shop.report_payment(c.id, "10.00", reference="R", order_id=o.id)
    shop.now += 2 * DAY                                # vencido, pero con pago en revisión
    assert shop.run_unpaid_auto_cancel() == []
    shop.reject(p.id)
    assert shop.run_unpaid_auto_cancel() == []         # tiene ventana mínima para otro pago
    shop.report_payment(c.id, "10.00", reference="R2", order_id=o.id)
    shop.check_invariants()


def test_m6_void_only_manual_and_forgive_order_debt(shop):
    c = shop.register()
    shop.enable_credit(c.id, "100.00")
    o = shop.create_order(c.id, "30.00", "a")
    shop.approve(shop.report_payment(c.id, "10.00", reference="T").id)
    with pytest.raises(DomainError) as e:
        shop.void_receivable(o.receivable_id)
    assert e.value.code == "RECEIVABLE_NOT_VOIDABLE"
    shop.forgive_receivable(o.receivable_id)
    r = shop.receivables[o.receivable_id]
    assert r.status == RS.PAID and r.forgiven == D("20.00") and o.payment_status == "PAID"
    with pytest.raises(DomainError):
        shop.reduce_order(o.id, "5.00")
    m = shop.manual_charge(c.id, "5.00")
    shop.void_receivable(m.id)
    assert shop.receivables[m.id].status == RS.VOID
    shop.check_invariants()


def test_m7_payout_returns_wallet_money(shop):
    c = cash_customer_with_wallet(shop, "12.00")
    with pytest.raises(DomainError):
        shop.payout(c.id, "12.01")
    shop.payout(c.id, "12.00")
    assert c.wallet == D("0.00") and c.movements[-1].type == "WALLET_PAYOUT"
    shop.check_invariants()


def test_m8_reversed_reference_stays_locked(shop):
    c = shop.register()
    p = shop.report_payment(c.id, "10.00", reference="FAKE")
    shop.approve(p.id)
    shop.reverse(p.id)
    with pytest.raises(DomainError) as e:
        shop.report_payment(c.id, "10.00", reference="FAKE")
    assert e.value.code == "DUPLICATE_REFERENCE"


def test_m9_blocking_cancels_awaiting_and_settle_never_confirms(shop):
    c = cash_customer_with_wallet(shop, "4.00")
    o = shop.create_order(c.id, "10.00", "a")
    p = shop.report_payment(c.id, "6.00", reference="P", order_id=o.id)
    shop.block(c.id)
    assert o.status == OS.CANCELLED and c.wallet == D("4.00")
    shop.approve(p.id)                                 # el pago en revisión sigue su curso
    assert c.wallet == D("10.00")
    with pytest.raises(DomainError):
        shop.create_order(c.id, "1.00", "b")
    shop.check_invariants()


def test_m12_credit_order_shows_paid_when_receivable_paid(shop):
    c = shop.register()
    shop.enable_credit(c.id, "50.00")
    o = shop.create_order(c.id, "20.00", "a")
    assert o.payment_status == "ON_CREDIT"
    shop.approve(shop.report_payment(c.id, "20.00", reference="T").id)
    assert o.payment_status == "PAID"
    shop.check_invariants()


def test_m11_every_model_error_code_is_in_catalog():
    src = pathlib.Path(__file__).with_name("money_model.py").read_text()
    raised = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "DomainError":
            raised.add(node.args[0].value)
    assert raised <= ERROR_CODES, raised - ERROR_CODES
    catalog = pathlib.Path(__file__).parents[1].joinpath("docs/plan/03-flujos-de-negocio.md").read_text()
    missing = {c for c in ERROR_CODES if f"`{c}`" not in catalog}
    assert not missing, f"códigos sin documentar en 03 §7: {missing}"


# ---------------- v2.2: hallazgos de la auditoría 2 ----------------
def test_r2_underpaid_approval_after_expiry_reopens_window(shop):
    c = shop.register()
    o = shop.create_order(c.id, "12.00", "a")
    p = shop.report_payment(c.id, "5.00", reference="R", order_id=o.id)
    shop.now += 2 * DAY
    shop.approve(p.id)
    assert o.status == OS.AWAITING_PAYMENT and shop.amount_due(o.id) == D("7.00")
    shop.now += 10
    assert shop.run_unpaid_auto_cancel() == []        # tiene ventana para pagar la diferencia
    shop.check_invariants()


def test_r2_cash_with_reversal_debt_pays_debt_before_order(shop):
    c = shop.register()
    o = shop.create_order(c.id, "12.00", "a")
    p = shop.report_payment(c.id, "5.00", reference="R1", order_id=o.id)
    shop.approve(p.id)
    shop.reverse(p.id)                                # deuda 5 (el saldo ya estaba en el pedido)
    assert shop.open_debt(c.id) == D("5.00")
    shop.approve(shop.report_payment(c.id, "7.00", reference="R2", order_id=o.id).id)
    assert shop.open_debt(c.id) == D("0.00")          # primero salda la deuda
    assert o.status == OS.AWAITING_PAYMENT            # el pedido aún no se confirma
    shop.check_invariants()


def test_r2_reference_unique_per_bank_account(shop):
    c = shop.register()
    shop.report_payment(c.id, "5.00", reference="X", method="PAGO_MOVIL", bank_account="B1")
    with pytest.raises(DomainError):
        shop.report_payment(c.id, "5.00", reference="X", method="TRANSFERENCIA", bank_account="B1")
    shop.report_payment(c.id, "5.00", reference="X", method="PAGO_MOVIL", bank_account="B2")


# --- Propiedades: cualquier secuencia de operaciones respeta las invariantes
OPS = st.lists(st.tuples(
    st.sampled_from(["order", "sched", "pay", "pay_order", "approve", "reject", "cancel", "advance",
                     "reverse", "adjust", "reduce", "charge", "time", "credit", "cash", "block",
                     "unblock", "payout", "void", "forgive"]),
    st.integers(min_value=0, max_value=50),
    st.integers(min_value=1, max_value=9000),
), max_size=60)


@settings(max_examples=500, deadline=None)
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
            elif op == "sched":
                shop.create_order(c.id, amount, f"k{seq}", due_at=shop.now + 60 + cents)
            elif op == "cash":
                shop.set_cash(c.id)
            elif op == "block":
                shop.block(c.id)
            elif op == "unblock":
                shop.unblock(c.id)
            elif op == "payout":
                shop.payout(c.id, amount)
            elif op in ("void", "forgive") and shop.receivables:
                recs = list(shop.receivables.values())
                r = recs[i % len(recs)]
                (shop.void_receivable if op == "void" else shop.forgive_receivable)(r.id)
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
