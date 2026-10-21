"""Datos de demostración de E1 (09 §E1 — Datos). Idempotente; solo con `SEED_DEMO=1` (staging).

- El admin del bootstrap (si no se configuró, uno de demostración `+584120000001` con `SEED_PASSWORD`).
- 3 categorías y 12 productos con precio mayor (`price`) y detal (`retailPrice`).
- Métodos de cobro: Pago móvil (Bs), Transferencia (Bs), Zelle (USD) y Efectivo USD, con la cuenta de
  cobro “Caja” ligada a la cuenta del negocio “Caja USD”.
- Tasa BCV y MANUAL de hoy.
- 3 clientes sin app: uno de detal con saldo anterior de $50, un mayorista con un fiado de 2 líneas y uno
  con $10 a favor. Los saldos anteriores pasan por `MoneyService.open_balance` (B-E1b).

Uso: `cd api && SEED_DEMO=1 SEED_PASSWORD=… python -m scripts.bootstrap`
"""
from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings, settings
from src.db.enums import (
    Currency,
    CustomerSegment,
    CustomerType,
    PaymentMethodType,
    RateType,
    ReceivableSource,
    ReceivableStatus,
)
from src.domain.cash_accounts.db_models import CashAccountDB
from src.domain.catalog.db_models import CategoryDB, ProductDB
from src.domain.customers.db_models import CustomerDB
from src.domain.exchange_rates.db_models import ExchangeRateDB
from src.domain.payment_methods.db_models import BankAccountDB, PaymentMethodDB
from src.domain.receivables.db_models import ReceivableDB, ReceivableItemDB
from src.services import registry
from src.utils.date_utils import end_of_day_caracas_utc, get_today_caracas, utcnow
from src.utils.money import q2

logger = logging.getLogger("seed")

D = Decimal

CATALOG: dict[str, list[tuple[str, str, str, str, int]]] = {
    # categoría: [(producto, unidad, precio mayor, precio detal, mínimo)]
    "Panes": [
        ("Pan canilla", "unidad", "0.80", "1.00", 10),
        ("Pan francés", "unidad", "0.25", "0.35", 20),
        ("Pan de sándwich", "bolsa", "2.20", "2.80", 2),
        ("Pan dulce", "unidad", "0.40", "0.55", 10),
    ],
    "Dulces": [
        ("Golfeado", "unidad", "1.10", "1.50", 6),
        ("Cachito dulce", "unidad", "0.90", "1.20", 6),
        ("Torta de pan", "porción", "1.30", "1.80", 4),
        ("Polvorosa", "unidad", "0.35", "0.50", 12),
    ],
    "Salados": [
        ("Cachito de jamón", "unidad", "1.20", "1.50", 6),
        ("Pan de jamón", "unidad", "9.00", "12.00", 1),
        ("Empanada de queso", "unidad", "0.95", "1.30", 6),
        ("Pastelito de carne", "unidad", "0.85", "1.10", 6),
    ],
}

# (cuenta del negocio, tipo, moneda)
CASH_ACCOUNTS = [("Banco Bs", "BANK", Currency.VES), ("Zelle", "ZELLE", Currency.USD), ("Caja USD", "CASH", Currency.USD)]

# (método, tipo, moneda, cuenta de cobro, cuenta del negocio, datos)
METHODS = [
    ("Pago móvil", PaymentMethodType.MOBILE_PAYMENT, Currency.VES, "Pago móvil Banesco", "Banco Bs",
     {"banco": "Banesco (0134)", "telefono": "0414-0000000", "cedula": "J-00000000-0"}),
    ("Transferencia", PaymentMethodType.BANK_TRANSFER, Currency.VES, "Banesco cuenta corriente", "Banco Bs",
     {"banco": "Banesco (0134)", "cuenta": "0134-0000-00-0000000000", "rif": "J-00000000-0"}),
    ("Zelle", PaymentMethodType.ZELLE, Currency.USD, "Zelle del negocio", "Zelle",
     {"correo": "pagos@ejemplo.com", "titular": "Panadería"}),
    ("Efectivo USD", PaymentMethodType.CASH, Currency.USD, "Caja", "Caja USD", {}),
]

DEMO_ADMIN_PHONE = "+584120000001"
DEMO_RATE_BCV = D("182.4500")
DEMO_RATE_MANUAL = D("183.0000")

CUSTOMERS = {
    "retail_debt": dict(contact_name="Carmen Pérez", phone="+584120000011", type=CustomerType.RETAIL,
                        notes="la del kiosko", segment=CustomerSegment.OTHER),
    "wholesale_fiado": dict(contact_name="José Rodríguez", business_name="Abasto La Esquina", phone="+584120000012",
                            type=CustomerType.WHOLESALE, segment=CustomerSegment.BODEGA),
    "credit": dict(contact_name="Luis Medina", business_name="Perros El Gocho", phone="+584120000013",
                   type=CustomerType.RETAIL, notes="el del carrito", segment=CustomerSegment.HOTDOG),
}


async def _one(session: AsyncSession, stmt):
    return (await session.execute(stmt)).scalars().first()


async def seed_catalog(session: AsyncSession) -> dict[str, ProductDB]:
    products: dict[str, ProductDB] = {}
    for order, (cat_name, items) in enumerate(CATALOG.items(), start=1):
        cat = await _one(session, select(CategoryDB).where(CategoryDB.name == cat_name))
        if cat is None:
            cat = CategoryDB(name=cat_name, sort_order=order)
            session.add(cat)
            await session.flush()
        for p_order, (name, unit, price, retail, min_qty) in enumerate(items, start=1):
            prod = await _one(session, select(ProductDB).where(ProductDB.name == name))
            if prod is None:
                prod = ProductDB(category_id=cat.id, name=name, unit_label=unit, price=D(price),
                                 retail_price=D(retail), min_qty=min_qty, sort_order=p_order)
                session.add(prod)
                await session.flush()
            products[name] = prod
    return products


async def seed_payment_methods(session: AsyncSession) -> None:
    cash: dict[str, CashAccountDB] = {}
    for order, (name, kind, currency) in enumerate(CASH_ACCOUNTS, start=1):
        acc = await _one(session, select(CashAccountDB).where(CashAccountDB.name == name))
        if acc is None:
            acc = CashAccountDB(name=name, account_type=kind, currency=currency, display_order=order)
            session.add(acc)
            await session.flush()
        cash[name] = acc
    for order, (name, kind, currency, label, cash_name, data) in enumerate(METHODS, start=1):
        method = await _one(session, select(PaymentMethodDB).where(PaymentMethodDB.name == name))
        if method is None:
            method = PaymentMethodDB(name=name, type=kind, currency=currency, display_order=order, fields=data)
            session.add(method)
            await session.flush()
        account = await _one(
            session,
            select(BankAccountDB).where(BankAccountDB.payment_method_id == method.id, BankAccountDB.account_label == label),
        )
        if account is None:
            session.add(BankAccountDB(payment_method_id=method.id, account_label=label, account_data=data,
                                      is_default=True, cash_account_id=cash[cash_name].id))
            await session.flush()


async def seed_rates(session: AsyncSession) -> None:
    today = get_today_caracas()
    for rate_type, value in ((RateType.BCV, DEMO_RATE_BCV), (RateType.MANUAL, DEMO_RATE_MANUAL)):
        row = await _one(
            session, select(ExchangeRateDB).where(ExchangeRateDB.date == today, ExchangeRateDB.rate_type == rate_type)
        )
        if row is None:
            session.add(ExchangeRateDB(date=today, rate_type=rate_type, value=value, source_url="seed",
                                       metadata_json={"demo": True}))
            await session.flush()


async def _customer(session: AsyncSession, data: dict, credit_days: int) -> tuple[CustomerDB, bool]:
    existing = await _one(session, select(CustomerDB).where(CustomerDB.phone == data["phone"]))
    if existing is not None:
        return existing, False
    customer = CustomerDB(credit_days=credit_days, **data)
    session.add(customer)
    await session.flush()
    return customer, True


async def seed_customers(session: AsyncSession, products: dict[str, ProductDB], actor_id: str | None) -> None:
    credit = await registry.get("settings").get(session, "credit")
    money = registry.get("money")

    c, created = await _customer(session, CUSTOMERS["retail_debt"], credit.defaultDays)
    if created:
        await money.open_balance(session, c.id, D("50.00"), "Deuda del cuaderno", actor_id)

    c, created = await _customer(session, CUSTOMERS["credit"], credit.defaultDays)
    if created:
        await money.open_balance(session, c.id, D("-10.00"), "Saldo a favor anterior", actor_id)

    c, created = await _customer(session, CUSTOMERS["wholesale_fiado"], credit.defaultDays)
    if created:
        # Fiado de 2 líneas a precio mayor. El cliente no tiene saldo a favor, así que no hay nada que
        # liquidar (03 §3.10b): solo se registra la CxC MANUAL con sus líneas; no se mueve ninguna billetera.
        lines = [(products["Pan canilla"], D("20")), (products["Cachito de jamón"], D("12"))]
        now = utcnow()
        items = [
            ReceivableItemDB(product_id=p.id, product_name=p.name, unit_label=p.unit_label, qty=qty,
                             unit_price=p.price, line_total=q2(qty * p.price))
            for p, qty in lines
        ]
        amount = sum((i.line_total for i in items), D("0.00"))
        rec = ReceivableDB(
            customer_id=c.id, source=ReceivableSource.MANUAL, created_by_user_id=actor_id, description="Fiado",
            amount=amount, paid_amount=D("0.00"), status=ReceivableStatus.OPEN, issued_at=now,
            due_at=end_of_day_caracas_utc(get_today_caracas() + timedelta(days=c.credit_days)),
        )
        session.add(rec)
        await session.flush()
        for item in items:
            item.receivable_id = rec.id
            session.add(item)
        await session.flush()


async def run_seed(session: AsyncSession, cfg: Settings = settings) -> dict:
    """Idempotente; no hace commit (lo hace `run_bootstrap`)."""
    from scripts.bootstrap import ensure_admin

    admin = await ensure_admin(session, cfg)
    if admin is None:
        # Sin admin del bootstrap: un admin de demostración con `SEED_PASSWORD` (cambia la clave al entrar).
        admin = await ensure_admin(
            session,
            cfg.model_copy(update={"BOOTSTRAP_ADMIN_PHONE": DEMO_ADMIN_PHONE, "BOOTSTRAP_ADMIN_PASSWORD": cfg.SEED_PASSWORD}),
        )
    products = await seed_catalog(session)
    await seed_payment_methods(session)
    await seed_rates(session)
    await seed_customers(session, products, admin.id if admin else None)
    logger.info("Datos de demostración listos")
    return {"products": len(products), "customers": len(CUSTOMERS)}
