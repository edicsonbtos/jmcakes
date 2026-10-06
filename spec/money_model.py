"""Modelo ejecutable de referencia de las reglas de dinero (docs/plan/03-flujos-de-negocio.md §1–§3).

No es código de producción: es la especificación probada. La API (bloques B2/B3) debe
comportarse igual que este modelo; los escenarios de spec/test_money_model.py se
reutilizan como pruebas de aceptación (B3 a nivel de services, Q1 por HTTP).

Todo en USD con Decimal a 2 decimales. Sin base de datos ni tasas: el tiempo es un
entero en minutos para simular vencimientos y la conversión Bs→USD ya viene resuelta
en `amount_usd` (la regla de tasa `rate_for(fecha)` está en 03 §3.3).

v2.1 (auditoría 1): reducción con fórmula `cobrado − nuevo total`, RECEIVABLE_REFUND,
WALLET_PAYOUT, condonar/anular CxC, OPEN_DEBT/OVERDUE_DEBT para todo modo, bloqueo de
cliente, ventana mínima de pago, referencia bloqueada también si REVERSED, paymentStatus
de pedidos a crédito que se pagan, catálogo de códigos de error.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from itertools import count

CENT = Decimal("0.01")
ZERO = Decimal("0.00")
DAY = 24 * 60

# Catálogo de códigos (03 §7). Toda DomainError del modelo debe estar aquí.
ERROR_CODES = {
    "CUSTOMER_BLOCKED", "OVERDUE_DEBT", "OPEN_DEBT", "CREDIT_LIMIT_EXCEEDED", "EMPTY_ORDER",
    "INVALID_TRANSITION", "ORDER_NOT_CANCELLABLE", "ONLY_REDUCTION", "ORDER_NOT_PAYABLE",
    "DUPLICATE_REFERENCE", "PAYMENT_NOT_REVIEWABLE", "PAYMENT_NOT_REVERSIBLE",
    "ADJUSTMENT_EXCEEDS_BALANCE", "PAYOUT_EXCEEDS_BALANCE", "RECEIVABLE_NOT_VOIDABLE",
    "INVALID_AMOUNT", "ORDER_NOT_REDUCIBLE",
}


def q(x) -> Decimal:
    return Decimal(x).quantize(CENT, rounding=ROUND_HALF_UP)


class DomainError(Exception):
    def __init__(self, code: str, **meta):
        assert code in ERROR_CODES, f"código fuera del catálogo: {code}"
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


# Pagos que bloquean su referencia (todo menos REJECTED) — índice único parcial de 02.
REFERENCE_LOCKING = {PS.PENDING_REVIEW, PS.IN_REVIEW, PS.APPROVED, PS.REVERSED}


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
    due_at: int
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
    forgiven: Decimal = ZERO
    status: RS = RS.OPEN
    void_reason: str | None = None


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
    """Estado completo + operaciones de 03 §1–§3."""

    KITCHEN_VISIBLE = {OS.CONFIRMED, OS.PREPARING, OS.READY}

    def __init__(self, tol: str = "0.01", unpaid_expiry: int = 24 * 60, block_overdue_days: int = 7,
                 min_lead: int = 60, min_pay_window: int = 30):
        self.tol = q(tol)
        self.unpaid_expiry = unpaid_expiry
        self.block_overdue_minutes = block_overdue_days * DAY
        self.min_lead = min_lead
        self.min_pay_window = min_pay_window
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

    # ---------- clientes (§1) ----------
    def register(self) -> Customer:
        c = Customer(id=next(self._ids))
        self.customers[c.id] = c
        return c

    def enable_credit(self, cid: int, limit: str, days: int = 7) -> None:
        """Cambio de modo: no altera pedidos existentes (orders.paymentMode es copia)."""
        c = self.customers[cid]
        c.mode, c.credit_limit, c.credit_days = Mode.CREDIT, q(limit), days

    def set_cash(self, cid: int) -> None:
        self.customers[cid].mode = Mode.CASH

    def block(self, cid: int) -> None:
        """§1: bloquear cancela los AWAITING_PAYMENT (con reembolso); los pagos en revisión siguen."""
        c = self.customers[cid]
        c.blocked = True
        for o in list(self.orders.values()):
            if o.customer_id == cid and o.status == OS.AWAITING_PAYMENT:
                self.cancel(o.id, by="admin")

    def unblock(self, cid: int) -> None:
        self.customers[cid].blocked = False

    def open_debt(self, cid: int) -> Decimal:
        return q(sum((r.amount - r.paid for r in self.receivables.values()
                      if r.customer_id == cid and r.status in (RS.OPEN, RS.PARTIAL)), ZERO))

    def _assert_can_order(self, c: Customer) -> None:
        """§2: bloqueo, deuda vencida (todo modo) y deuda abierta en CASH."""
        if c.blocked:
            raise DomainError("CUSTOMER_BLOCKED")
        open_recs = [r for r in self.receivables.values()
                     if r.customer_id == c.id and r.status in (RS.OPEN, RS.PARTIAL)]
        if any(r.due_at + self.block_overdue_minutes < self.now for r in open_recs):
            raise DomainError("OVERDUE_DEBT")
        if c.mode == Mode.CASH and open_recs:
            raise DomainError("OPEN_DEBT", debt=self.open_debt(c.id))

    # ---------- pedidos (§2–§3.2) ----------
    def create_order(self, cid: int, total: str, idem: str, due_at: int | None = None) -> Order:
        """due_at None = ASAP ("lo quiero hoy"); si no, minutos absolutos (programado)."""
        key = (cid, idem)
        if key in self._idem:
            return self.orders[self._idem[key]]
        c = self.customers[cid]
        self._assert_can_order(c)
        T = q(total)
        if T <= ZERO:
            raise DomainError("EMPTY_ORDER")
        use = min(c.wallet, T)
        rest = q(T - use)
        if c.mode == Mode.CREDIT:
            available = q(c.credit_limit - self.open_debt(cid))
            if rest > available:
                raise DomainError("CREDIT_LIMIT_EXCEEDED", available=available, required=rest, wallet=c.wallet)
        o = Order(id=next(self._ids), customer_id=cid, total=T, mode=c.mode, created_at=self.now,
                  due_at=self.now if due_at is None else due_at)
        self.orders[o.id] = o
        self._idem[key] = o.id
        if use > ZERO:
            self._charge_order(c, o, use)
        if c.mode == Mode.CREDIT:
            if rest > ZERO:
                r = Receivable(id=next(self._ids), customer_id=cid, amount=rest, issued_at=self.now,
                               due_at=o.due_at + c.credit_days * DAY, order_id=o.id)
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
                # §3.2 + ventana mínima de pago (auditoría M5)
                o.expires_at = max(self.now + self.min_pay_window,
                                   min(self.now + self.unpaid_expiry, o.due_at - self.min_lead))
        return o

    def amount_due(self, oid: int) -> Decimal:
        o = self.orders[oid]
        if o.status != OS.AWAITING_PAYMENT:
            return ZERO
        return q(o.total - o.paid_from_wallet - o.rounding_adjustment)

    def _charge_order(self, c: Customer, o: Order, amount: Decimal) -> None:
        self._move(c, "ORDER_CHARGE", -amount, order_id=o.id)
        o.paid_from_wallet = q(o.paid_from_wallet + amount)

    def _refund_order(self, c: Customer, o: Order, amount: Decimal) -> None:
        self._move(c, "ORDER_REFUND", amount, order_id=o.id)
        o.paid_from_wallet = q(o.paid_from_wallet - amount)

    def _confirm(self, o: Order) -> None:
        # (la API además recalcula dueAt de un ASAP a la hora de confirmación)
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
        """§3.8"""
        o = self.orders[oid]
        if by == "customer" and o.status not in (OS.AWAITING_PAYMENT, OS.CONFIRMED):
            raise DomainError("ORDER_NOT_CANCELLABLE")
        if o.status in (OS.DELIVERED, OS.CANCELLED):
            raise DomainError("ORDER_NOT_CANCELLABLE")
        c = self.customers[o.customer_id]
        was_visible = o.status in self.KITCHEN_VISIBLE
        refunded = False
        if o.paid_from_wallet > ZERO:
            self._refund_order(c, o, o.paid_from_wallet)
            refunded = True
        if o.receivable_id:
            r = self.receivables[o.receivable_id]
            if r.status != RS.VOID:
                if r.paid > ZERO:
                    self._move(c, "RECEIVABLE_REFUND", r.paid, receivable_id=r.id, order_id=o.id)
                    refunded = True
                r.status, r.void_reason = RS.VOID, "ORDER_CANCELLED"
        o.rounding_adjustment = ZERO
        o.status = OS.CANCELLED
        o.expires_at = None
        o.payment_status = "REFUNDED" if refunded else o.payment_status
        if was_visible:
            self.kitchen_events.append(("order.cancelled", o.id))
        self.settle(c.id)

    def reduce_order(self, oid: int, new_total: str) -> None:
        """§3.9: el admin reduce el pedido antes de READY (fórmula de auditoría M2)."""
        o = self.orders[oid]
        if o.status not in (OS.AWAITING_PAYMENT, OS.CONFIRMED, OS.PREPARING):
            raise DomainError("INVALID_TRANSITION")
        new_t = q(new_total)
        if not (ZERO < new_t <= o.total):
            raise DomainError("ONLY_REDUCTION")
        c = self.customers[o.customer_id]
        r = self.receivables[o.receivable_id] if o.receivable_id else None
        if r and r.forgiven > ZERO:
            raise DomainError("ORDER_NOT_REDUCIBLE")
        rec_paid = r.paid if r and r.status != RS.VOID else ZERO
        collected = q(o.paid_from_wallet + rec_paid + o.rounding_adjustment)
        refund = max(ZERO, q(collected - new_t))
        o.total = new_t
        o.rounding_adjustment = min(o.rounding_adjustment, new_t)
        # 1) CxC: bajar su monto hacia max(lo pagado, lo que el crédito aún debe cubrir)
        if r and r.status != RS.VOID:
            target = max(r.paid, q(new_t - o.paid_from_wallet - o.rounding_adjustment))
            r.amount = min(r.amount, max(target, ZERO))
            # 2) devolver primero lo pagado de la CxC
            back = min(refund, r.paid)
            if back > ZERO:
                r.paid = q(r.paid - back)
                r.amount = q(r.amount - back)
                self._move(c, "RECEIVABLE_REFUND", back, receivable_id=r.id, order_id=o.id)
                refund = q(refund - back)
            if r.amount == ZERO:
                r.status, r.void_reason = RS.VOID, "REDUCED"
            elif r.paid == r.amount:
                r.status = RS.PAID
            elif r.paid > ZERO:
                r.status = RS.PARTIAL
        # 3) luego lo cobrado de la billetera
        if refund > ZERO:
            back = min(refund, o.paid_from_wallet)
            self._refund_order(c, o, back)
            refund = q(refund - back)
        assert refund == ZERO
        if o.status == OS.AWAITING_PAYMENT and q(o.total - o.paid_from_wallet - o.rounding_adjustment) <= self.tol:
            o.rounding_adjustment = q(o.total - o.paid_from_wallet)
            o.payment_status = "PAID"
            self._confirm(o)
        self._sync_credit_payment_status(o)
        self.settle(c.id, priority=o.id)

    def _sync_credit_payment_status(self, o: Order) -> None:
        """Auditoría M12: un pedido a crédito cuya CxC quedó PAID/VOID se muestra PAID."""
        if o.receivable_id and o.status != OS.CANCELLED:
            r = self.receivables[o.receivable_id]
            o.payment_status = "ON_CREDIT" if r.status in (RS.OPEN, RS.PARTIAL) else "PAID"

    # ---------- pagos (§3.3–§3.7) ----------
    def report_payment(self, cid: int, amount_usd: str, reference: str, method: str = "PAGO_MOVIL",
                       order_id: int | None = None) -> Payment:
        if q(amount_usd) <= ZERO:
            raise DomainError("INVALID_AMOUNT")
        if any(p.method == method and p.reference == reference and p.status in REFERENCE_LOCKING
               for p in self.payments.values()):
            raise DomainError("DUPLICATE_REFERENCE")
        if order_id is not None:  # la API toma FOR UPDATE del pedido aquí (M10)
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
            if q(corrected_usd) <= ZERO:
                raise DomainError("INVALID_AMOUNT")
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
        if p.order_id is not None:  # §3.6: el cliente conserva una ventana para reportar otro
            o = self.orders[p.order_id]
            if o.status == OS.AWAITING_PAYMENT and o.expires_at is not None:
                o.expires_at = max(o.expires_at, self.now + self.min_pay_window)

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

    # ---------- operaciones manuales del admin ----------
    def adjust(self, cid: int, amount: str) -> None:
        c = self.customers[cid]
        a = q(amount)
        if a == ZERO:
            raise DomainError("INVALID_AMOUNT")
        if a < ZERO and -a > c.wallet:
            raise DomainError("ADJUSTMENT_EXCEEDS_BALANCE")
        self._move(c, "ADJUSTMENT", a)
        if a > ZERO:
            self.settle(cid)

    def payout(self, cid: int, amount: str) -> None:
        """§3.12: devolver saldo a favor en dinero (EXPENSE en cuenta del negocio)."""
        c = self.customers[cid]
        a = q(amount)
        if a <= ZERO:
            raise DomainError("INVALID_AMOUNT")
        if a > c.wallet:
            raise DomainError("PAYOUT_EXCEEDS_BALANCE")
        self._move(c, "WALLET_PAYOUT", -a)

    def manual_charge(self, cid: int, amount: str, due_in_days: int = 7) -> Receivable:
        if q(amount) <= ZERO:
            raise DomainError("INVALID_AMOUNT")
        r = Receivable(id=next(self._ids), customer_id=cid, amount=q(amount), issued_at=self.now,
                       due_at=self.now + due_in_days * DAY, source="MANUAL")
        self.receivables[r.id] = r
        self.settle(cid)
        return r

    def void_receivable(self, rid: int) -> None:
        """§3.11: solo MANUAL/PAYMENT_REVERSAL; devuelve lo pagado a la billetera."""
        r = self.receivables[rid]
        if r.source == "ORDER" or r.status == RS.VOID:
            raise DomainError("RECEIVABLE_NOT_VOIDABLE")
        c = self.customers[r.customer_id]
        if r.paid > ZERO:
            self._move(c, "RECEIVABLE_REFUND", r.paid, receivable_id=r.id)
        r.status, r.void_reason = RS.VOID, "VOIDED"
        self.settle(c.id)

    def forgive_receivable(self, rid: int) -> None:
        """§3.11: condonar el saldo pendiente sin devolver lo cobrado (cualquier source)."""
        r = self.receivables[rid]
        if r.status not in (RS.OPEN, RS.PARTIAL):
            raise DomainError("RECEIVABLE_NOT_VOIDABLE")
        r.forgiven = q(r.amount - r.paid)
        r.amount = r.paid
        if r.amount == ZERO:
            r.status, r.void_reason = RS.VOID, "FORGIVEN"
        else:
            r.status = RS.PAID
        for o in self.orders.values():
            if o.receivable_id == r.id:
                self._sync_credit_payment_status(o)

    # ---------- settle §3.5 ----------
    def settle(self, cid: int, priority: int | None = None) -> None:
        c = self.customers[cid]
        if not c.blocked:  # M9: nunca se confirman pedidos de un cliente bloqueado
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
            for o in self.orders.values():
                if o.receivable_id == r.id:
                    self._sync_credit_payment_status(o)

    # ---------- jobs ----------
    def run_unpaid_auto_cancel(self) -> list[int]:
        """§3.10 (la API usa FOR UPDATE SKIP LOCKED sobre orders)."""
        cancelled = []
        for o in list(self.orders.values()):
            if o.status == OS.AWAITING_PAYMENT and o.expires_at is not None and o.expires_at < self.now:
                in_review = any(p.order_id == o.id and p.status in (PS.PENDING_REVIEW, PS.IN_REVIEW)
                                for p in self.payments.values())
                if not in_review:
                    self.cancel(o.id, by="system")
                    cancelled.append(o.id)
        return cancelled

    # ---------- invariantes (02 §Invariantes, mismas fórmulas que el SQL) ----------
    def check_invariants(self) -> None:
        for c in self.customers.values():
            running = ZERO
            for m in c.movements:
                running = q(running + m.amount)
                assert m.balance_after == running, "I-1 balanceAfter"
                assert running >= ZERO, "I-1 negativo"
            assert running == c.wallet, "I-1 caché"

            def tot(t):
                return sum((m.amount for m in c.movements if m.type == t), ZERO)

            in_orders = sum((o.paid_from_wallet for o in self.orders.values()
                             if o.customer_id == c.id and o.status != OS.CANCELLED), ZERO)
            in_recs = sum((r.paid for r in self.receivables.values()
                           if r.customer_id == c.id and r.status != RS.VOID), ZERO)
            expected = q(tot("TOPUP_APPROVED") + tot("PAYMENT_REVERSAL") + tot("ADJUSTMENT")
                         + tot("WALLET_PAYOUT") - in_orders - in_recs)
            assert expected == c.wallet, "I-6 conservación"
        all_moves = [m for c in self.customers.values() for m in c.movements]
        for o in self.orders.values():
            charged = -sum((m.amount for m in all_moves if m.order_id == o.id
                            and m.type in ("ORDER_CHARGE", "ORDER_REFUND")), ZERO)
            assert charged == o.paid_from_wallet, "I-2"
            if o.status == OS.CANCELLED:
                assert o.paid_from_wallet == ZERO, "I-5"
                if o.receivable_id:
                    assert self.receivables[o.receivable_id].status == RS.VOID, "I-5 CxC"
            elif o.status != OS.AWAITING_PAYMENT:
                r = self.receivables[o.receivable_id] if o.receivable_id else None
                rec = ((r.amount if r.status != RS.VOID else ZERO) + r.forgiven) if r else ZERO
                assert q(o.paid_from_wallet + rec + o.rounding_adjustment) == o.total, "I-4"
                assert o.rounding_adjustment <= self.tol, "I-4 tolerancia"
            if o.receivable_id and o.status != OS.CANCELLED:
                r = self.receivables[o.receivable_id]
                want = "ON_CREDIT" if r.status in (RS.OPEN, RS.PARTIAL) else "PAID"
                assert o.payment_status == want, "M12 paymentStatus crédito"
        for r in self.receivables.values():
            assert ZERO <= r.paid <= r.amount or r.status == RS.VOID, "I-3 rango"
            if r.status != RS.VOID:
                settled = -sum((m.amount for m in all_moves
                                if m.receivable_id == r.id and m.type == "RECEIVABLE_SETTLEMENT"), ZERO)
                refunded = sum((m.amount for m in all_moves
                                if m.receivable_id == r.id and m.type == "RECEIVABLE_REFUND"), ZERO)
                assert q(settled - refunded) == r.paid, "I-3 igualdad"
                assert r.amount > ZERO, "I-3 monto"
        for o in self.orders.values():
            c = self.customers[o.customer_id]
            if c.blocked:
                assert o.status != OS.AWAITING_PAYMENT, "M9 bloqueado sin pedidos esperando pago"
