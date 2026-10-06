"""Modelo ejecutable de referencia de las reglas de dinero (docs/plan/03-flujos-de-negocio.md §3).

No es código de producción: es la especificación probada. La API (bloque B3/B2) debe
comportarse igual que este modelo; los escenarios de spec/test_money_model.py se
reutilizan como pruebas de aceptación contra la API real (bloque Q1).

Todo en USD con Decimal a 2 decimales. Sin base de datos, sin fechas reales: el tiempo
es un entero (minutos) para poder simular vencimientos.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from itertools import count

CENT = Decimal("0.01")
ZERO = Decimal("0.00")


def q(x) -> Decimal:
    return Decimal(x).quantize(CENT, rounding=ROUND_HALF_UP)


class DomainError(Exception):
    def __init__(self, code: str, **meta):
        super().__init__(code)
        self.code = code
        self.meta = meta


class Mode(str, Enum):
    CASH = "CASH"
    CREDIT = "CREDIT"


class OS(str, Enum):  # OrderStatus
    AWAITING_PAYMENT = "AWAITING_PAYMENT"
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    READY = "READY"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class PS(str, Enum):  # PaymentStatus (OpenGravity)
    PENDING_REVIEW = "PENDING_REVIEW"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVERSED = "REVERSED"


class RS(str, Enum):  # ReceivableStatus
    OPEN = "OPEN"
    PARTIAL = "PARTIAL"
    PAID = "PAID"
    VOID = "VOID"


@dataclass
class Movement:
    type: str
    amount: Decimal
    balance_after: Decimal
    order_id: int | None = None
    receivable_id: int | None = None
    payment_id: int | None = None


@dataclass
class Customer:
    id: int
    mode: Mode = Mode.CASH
    credit_limit: Decimal = ZERO
    credit_days: int = 7
    wallet: Decimal = ZERO
    blocked: bool = False
    movements: list[Movement] = field(default_factory=list)


@dataclass
class Order:
    id: int
    customer_id: int
    total: Decimal
    mode: Mode
    created_at: int
    status: OS = OS.AWAITING_PAYMENT
    paid_from_wallet: Decimal = ZERO
    rounding_adjustment: Decimal = ZERO
    receivable_id: int | None = None
    expires_at: int | None = None
    payment_status: str = "UNPAID"


@dataclass
class Receivable:
    id: int
    customer_id: int
    amount: Decimal
    issued_at: int
    due_at: int
    source: str = "ORDER"
    order_id: int | None = None
    paid: Decimal = ZERO
    status: RS = RS.OPEN


@dataclass
class Payment:
    id: int
    customer_id: int
    amount_usd: Decimal
    method: str
    reference: str
    order_id: int | None = None
    status: PS = PS.PENDING_REVIEW


class Shop:
    """Estado completo + operaciones del flujo §3."""

    KITCHEN_VISIBLE = {OS.CONFIRMED, OS.PREPARING, OS.READY}

    def __init__(self, tol: str = "0.01", unpaid_expiry: int = 24 * 60, block_overdue_days: int = 7):
        self.tol = q(tol)
        self.unpaid_expiry = unpaid_expiry
        self.block_overdue_minutes = block_overdue_days * 24 * 60
        self.now = 0
        self.customers: dict[int, Customer] = {}
        self.orders: dict[int, Order] = {}
        self.receivables: dict[int, Receivable] = {}
        self.payments: dict[int, Payment] = {}
        self.kitchen_events: list[tuple[str, int]] = []
        self._ids = count(1)
        self._idem: dict[tuple[int, str], int] = {}

    # ---------- ledger (único que toca el saldo) ----------
    def _move(self, c: Customer, type_: str, amount: Decimal, **refs) -> None:
        amount = q(amount)
        if amount == ZERO:
            return
        new = q(c.wallet + amount)
        if new < ZERO:
            raise AssertionError(f"billetera negativa: {type_} {amount} sobre {c.wallet}")
        c.wallet = new
        c.movements.append(Movement(type_, amount, new, **refs))

    # ---------- clientes ----------
    def register(self) -> Customer:
        c = Customer(id=next(self._ids))
        self.customers[c.id] = c
        return c

    def enable_credit(self, cid: int, limit: str, days: int = 7) -> None:
        c = self.customers[cid]
        c.mode, c.credit_limit, c.credit_days = Mode.CREDIT, q(limit), days

    def open_debt(self, cid: int) -> Decimal:
        return q(sum((r.amount - r.paid for r in self.receivables.values()
                      if r.customer_id == cid and r.status in (RS.OPEN, RS.PARTIAL)), ZERO))

    def _has_blocking_overdue(self, cid: int) -> bool:
        return any(r.customer_id == cid and r.status in (RS.OPEN, RS.PARTIAL)
                   and r.due_at + self.block_overdue_minutes < self.now
                   for r in self.receivables.values())

    # ---------- pedidos ----------
    def create_order(self, cid: int, total: str, idem: str) -> Order:
        key = (cid, idem)
        if key in self._idem:
            return self.orders[self._idem[key]]
        c = self.customers[cid]
        if c.blocked:
            raise DomainError("CUSTOMER_BLOCKED")
        T = q(total)
        if T <= ZERO:
            raise DomainError("EMPTY_ORDER")
        if c.mode == Mode.CREDIT and self._has_blocking_overdue(cid):
            raise DomainError("OVERDUE_DEBT")
        use = min(c.wallet, T)
        rest = q(T - use)
        if c.mode == Mode.CREDIT:
            available = q(c.credit_limit - self.open_debt(cid))
            if rest > available:
                raise DomainError("CREDIT_LIMIT_EXCEEDED", available=available, required=rest, wallet=c.wallet)
        o = Order(id=next(self._ids), customer_id=cid, total=T, mode=c.mode, created_at=self.now)
        self.orders[o.id] = o
        self._idem[key] = o.id
        if use > ZERO:
            self._charge_order(c, o, use)
        if c.mode == Mode.CREDIT:
            if rest > ZERO:
                r = Receivable(id=next(self._ids), customer_id=cid, amount=rest, issued_at=self.now,
                               due_at=self.now + c.credit_days * 24 * 60, order_id=o.id)
                self.receivables[r.id] = r
                o.receivable_id = r.id
                o.payment_status = "ON_CREDIT"
            else:
                o.payment_status = "PAID"
            self._confirm(o)
        else:
            missing = q(T - o.paid_from_wallet)
            if missing <= self.tol:
                o.rounding_adjustment = missing
                o.payment_status = "PAID"
                self._confirm(o)
            else:
                o.status = OS.AWAITING_PAYMENT
                o.payment_status = "PARTIALLY_PAID" if o.paid_from_wallet > ZERO else "UNPAID"
                o.expires_at = self.now + self.unpaid_expiry
        return o

    def amount_due(self, oid: int) -> Decimal:
        o = self.orders[oid]
        if o.status != OS.AWAITING_PAYMENT:
            return ZERO
        return q(o.total - o.paid_from_wallet - o.rounding_adjustment)

    def _charge_order(self, c: Customer, o: Order, amount: Decimal) -> None:
        self._move(c, "ORDER_CHARGE", -amount, order_id=o.id)
        o.paid_from_wallet = q(o.paid_from_wallet + amount)

    def _confirm(self, o: Order) -> None:
        o.status = OS.CONFIRMED
        o.expires_at = None
        self.kitchen_events.append(("order.confirmed", o.id))

    def transition(self, oid: int, to: OS) -> None:
        o = self.orders[oid]
        allowed = {
            OS.CONFIRMED: {OS.PREPARING, OS.READY},
            OS.PREPARING: {OS.READY},
            OS.READY: {OS.OUT_FOR_DELIVERY},
            OS.OUT_FOR_DELIVERY: {OS.DELIVERED},
        }
        if to not in allowed.get(o.status, set()):
            raise DomainError("INVALID_TRANSITION", frm=o.status, to=to)
        o.status = to

    def cancel(self, oid: int, by: str = "admin") -> None:
        o = self.orders[oid]
        if by == "customer" and o.status not in (OS.AWAITING_PAYMENT, OS.CONFIRMED):
            raise DomainError("ORDER_NOT_CANCELLABLE")
        if o.status in (OS.DELIVERED, OS.CANCELLED):
            raise DomainError("ORDER_NOT_CANCELLABLE")
        c = self.customers[o.customer_id]
        was_visible = o.status in self.KITCHEN_VISIBLE
        refunded = False
        if o.paid_from_wallet > ZERO:
            self._move(c, "ORDER_REFUND", o.paid_from_wallet, order_id=o.id)
            o.paid_from_wallet = ZERO
            refunded = True
        if o.receivable_id:
            r = self.receivables[o.receivable_id]
            if r.paid > ZERO:
                self._move(c, "ORDER_REFUND", r.paid, receivable_id=r.id, order_id=o.id)
                refunded = True
            r.status = RS.VOID
        o.rounding_adjustment = ZERO
        o.status = OS.CANCELLED
        o.expires_at = None
        o.payment_status = "REFUNDED" if refunded else o.payment_status
        if was_visible:
            self.kitchen_events.append(("order.cancelled", o.id))
        self.settle(c.id)

    def reduce_order(self, oid: int, new_total: str) -> None:
        """§3.9: el admin reduce el pedido antes de READY."""
        o = self.orders[oid]
        if o.status not in (OS.AWAITING_PAYMENT, OS.CONFIRMED, OS.PREPARING):
            raise DomainError("INVALID_TRANSITION")
        new_t = q(new_total)
        if not (ZERO < new_t <= o.total):
            raise DomainError("ONLY_REDUCTION")
        c = self.customers[o.customer_id]
        excess = q(o.total - new_t)
        o.total = new_t
        if o.receivable_id:
            r = self.receivables[o.receivable_id]
            cut = min(excess, q(r.amount - r.paid))
            r.amount = q(r.amount - cut)
            excess = q(excess - cut)
            if r.amount == r.paid:
                r.status = RS.PAID
            # si aún sobra y la CxC tenía pagos, se baja lo pagado de la CxC y se devuelve
            if excess > ZERO and r.paid > ZERO:
                back = min(excess, r.paid)
                r.paid = q(r.paid - back)
                r.amount = q(r.amount - back)
                self._move(c, "ORDER_REFUND", back, receivable_id=r.id, order_id=o.id)
                excess = q(excess - back)
        if excess > ZERO and o.paid_from_wallet > ZERO:
            back = min(excess, o.paid_from_wallet)
            o.paid_from_wallet = q(o.paid_from_wallet - back)
            self._move(c, "ORDER_REFUND", back, order_id=o.id)
            excess = q(excess - back)
        if o.status == OS.AWAITING_PAYMENT and self.amount_due(oid) <= self.tol:
            o.rounding_adjustment = q(o.total - o.paid_from_wallet)
            o.payment_status = "PAID"
            self._confirm(o)
        self.settle(c.id)

    # ---------- pagos ----------
    def report_payment(self, cid: int, amount_usd: str, reference: str, method: str = "PAGO_MOVIL",
                       order_id: int | None = None) -> Payment:
        live = {PS.PENDING_REVIEW, PS.IN_REVIEW, PS.APPROVED}
        if any(p.method == method and p.reference == reference and p.status in live
               for p in self.payments.values()):
            raise DomainError("DUPLICATE_REFERENCE")
        if order_id is not None:
            o = self.orders[order_id]
            if o.customer_id != cid or o.status != OS.AWAITING_PAYMENT:
                raise DomainError("ORDER_NOT_PAYABLE")
        p = Payment(id=next(self._ids), customer_id=cid, amount_usd=q(amount_usd), method=method,
                    reference=reference, order_id=order_id)
        self.payments[p.id] = p
        return p

    def approve(self, pid: int, corrected_usd: str | None = None) -> None:
        p = self.payments[pid]
        if p.status not in (PS.PENDING_REVIEW, PS.IN_REVIEW):
            raise DomainError("PAYMENT_NOT_REVIEWABLE")
        if corrected_usd is not None:
            p.amount_usd = q(corrected_usd)
        c = self.customers[p.customer_id]
        self._move(c, "TOPUP_APPROVED", p.amount_usd, payment_id=p.id)
        p.status = PS.APPROVED
        self.settle(c.id, priority=p.order_id)

    def reject(self, pid: int) -> None:
        p = self.payments[pid]
        if p.status not in (PS.PENDING_REVIEW, PS.IN_REVIEW):
            raise DomainError("PAYMENT_NOT_REVIEWABLE")
        p.status = PS.REJECTED

    def reverse(self, pid: int) -> None:
        p = self.payments[pid]
        if p.status != PS.APPROVED:
            raise DomainError("PAYMENT_NOT_REVERSIBLE")
        c = self.customers[p.customer_id]
        take = min(c.wallet, p.amount_usd)
        self._move(c, "PAYMENT_REVERSAL", -take, payment_id=p.id)
        short = q(p.amount_usd - take)
        if short > ZERO:
            r = Receivable(id=next(self._ids), customer_id=c.id, amount=short, issued_at=self.now,
                           due_at=self.now, source="PAYMENT_REVERSAL")
            self.receivables[r.id] = r
        p.status = PS.REVERSED

    def adjust(self, cid: int, amount: str) -> None:
        c = self.customers[cid]
        a = q(amount)
        if a < ZERO and -a > c.wallet:
            raise DomainError("ADJUSTMENT_EXCEEDS_BALANCE")
        self._move(c, "ADJUSTMENT", a)
        if a > ZERO:
            self.settle(cid)

    def manual_charge(self, cid: int, amount: str, due_in_days: int = 7) -> Receivable:
        r = Receivable(id=next(self._ids), customer_id=cid, amount=q(amount), issued_at=self.now,
                       due_at=self.now + due_in_days * 24 * 60, source="MANUAL")
        self.receivables[r.id] = r
        self.settle(cid)
        return r

    # ---------- settle §3.5 ----------
    def settle(self, cid: int, priority: int | None = None) -> None:
        c = self.customers[cid]
        awaiting = sorted((o for o in self.orders.values()
                           if o.customer_id == cid and o.status == OS.AWAITING_PAYMENT),
                          key=lambda o: (o.id != priority, o.created_at, o.id))
        for o in awaiting:
            if c.wallet <= ZERO:
                break
            missing = q(o.total - o.paid_from_wallet - o.rounding_adjustment)
            take = min(c.wallet, missing)
            self._charge_order(c, o, take)
            left = q(missing - take)
            if left <= self.tol:
                o.rounding_adjustment = q(o.rounding_adjustment + left)
                o.payment_status = "PAID"
                self._confirm(o)
            else:
                o.payment_status = "PARTIALLY_PAID"
        recs = sorted((r for r in self.receivables.values()
                       if r.customer_id == cid and r.status in (RS.OPEN, RS.PARTIAL)),
                      key=lambda r: (r.due_at, r.issued_at, r.id))
        for r in recs:
            if c.wallet <= ZERO:
                break
            take = min(c.wallet, q(r.amount - r.paid))
            self._move(c, "RECEIVABLE_SETTLEMENT", -take, receivable_id=r.id)
            r.paid = q(r.paid + take)
            r.status = RS.PAID if r.paid == r.amount else RS.PARTIAL

    # ---------- jobs ----------
    def run_unpaid_auto_cancel(self) -> list[int]:
        cancelled = []
        for o in list(self.orders.values()):
            if o.status == OS.AWAITING_PAYMENT and o.expires_at is not None and o.expires_at < self.now:
                in_review = any(p.order_id == o.id and p.status in (PS.PENDING_REVIEW, PS.IN_REVIEW)
                                for p in self.payments.values())
                if not in_review:
                    self.cancel(o.id, by="system")
                    cancelled.append(o.id)
        return cancelled

    # ---------- invariantes (docs/plan/02 §Invariantes) ----------
    def check_invariants(self) -> None:
        for c in self.customers.values():
            running = ZERO
            for m in c.movements:
                running = q(running + m.amount)
                assert m.balance_after == running, "I-1 balanceAfter"
                assert running >= ZERO, "I-1 negativo"
            assert running == c.wallet, "I-1 caché"
            approved = sum((m.amount for m in c.movements if m.type == "TOPUP_APPROVED"), ZERO)
            reversals = sum((m.amount for m in c.movements if m.type == "PAYMENT_REVERSAL"), ZERO)
            adjustments = sum((m.amount for m in c.movements if m.type == "ADJUSTMENT"), ZERO)
            in_orders = sum((o.paid_from_wallet for o in self.orders.values()
                             if o.customer_id == c.id and o.status != OS.CANCELLED), ZERO)
            in_recs = sum((r.paid for r in self.receivables.values()
                           if r.customer_id == c.id and r.status != RS.VOID), ZERO)
            assert q(approved + reversals + adjustments - in_orders - in_recs) == c.wallet, "I-6 conservación"
        for o in self.orders.values():
            charged = -sum((m.amount for c in self.customers.values() for m in c.movements
                            if m.order_id == o.id and m.receivable_id is None), ZERO)
            if o.status == OS.CANCELLED:
                assert o.paid_from_wallet == ZERO, "I-5"
                assert charged == ZERO, "I-2 cancelado"
                if o.receivable_id:
                    assert self.receivables[o.receivable_id].status == RS.VOID, "I-5 CxC"
            else:
                assert charged == o.paid_from_wallet, "I-2"
                if o.status != OS.AWAITING_PAYMENT:
                    rec = self.receivables[o.receivable_id].amount if o.receivable_id else ZERO
                    assert q(o.paid_from_wallet + rec + o.rounding_adjustment) == o.total, "I-4"
                    assert o.rounding_adjustment <= self.tol, "I-4 tolerancia"
        for r in self.receivables.values():
            assert ZERO <= r.paid <= r.amount, "I-3 rango"
