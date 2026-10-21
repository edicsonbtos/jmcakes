"""Arnés de pruebas de la API (docs/plan/bloques/FND §8 y Ajustes v2.3).

- `TEST_DATABASE_URL` es obligatorio y debe apuntar a un Postgres local (127.0.0.1, localhost o postgres).
  **Antes de importar `src.*`** se fija `DATABASE_URL = TEST_DATABASE_URL` y se borra `DATABASE_URL_DIRECT`.
- La base se crea si no existe y se migra con `alembic upgrade head` una vez por sesión (nunca `create_all`).
- Fixtures: `db_session` (savepoints, todo se deshace), `committed_db` (transacciones reales con TRUNCATE de
  **esta** base antes y después), `client` (httpx + ASGITransport), `make_user(role)`, `customer_cash`,
  `customer_credit`, `money_setup`, `money_double` y `settings_cache_clear` (autouse).
"""
from __future__ import annotations

import os
import sys
from urllib.parse import urlparse

import pytest

# ----------------------------------------------------------------------------- entorno (antes de src.*)
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "").strip()
if not TEST_DATABASE_URL:
    pytest.exit(
        "Falta TEST_DATABASE_URL (p. ej. postgresql+psycopg://dev:dev@127.0.0.1:5432/panaderia_test_fnd).",
        returncode=4,
    )
_parsed = urlparse(TEST_DATABASE_URL.replace("+psycopg", ""))
if _parsed.hostname not in {"127.0.0.1", "localhost", "postgres"}:
    pytest.exit(f"TEST_DATABASE_URL debe ser un Postgres local, no {_parsed.hostname!r}.", returncode=4)
if "src.config" in sys.modules:
    pytest.exit("src.config se importó antes que tests/conftest.py: el aislamiento de la base no es seguro.", returncode=4)

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.pop("DATABASE_URL_DIRECT", None)
os.environ["ENVIRONMENT"] = "test"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ.setdefault("JWT_SECRET", "secreto-solo-para-pruebas-locales")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

from collections.abc import AsyncIterator, Callable  # noqa: E402
from dataclasses import dataclass, field  # noqa: E402
from decimal import Decimal  # noqa: E402
from pathlib import Path  # noqa: E402

import httpx  # noqa: E402
import psycopg  # noqa: E402
import pytest_asyncio  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker  # noqa: E402

from src.api.limiter import reset_limits  # noqa: E402
from src.core.security import create_access_token, hash_password  # noqa: E402
from src.db.enums import Currency, CustomerType, PaymentMethodType, PaymentMode, UserRole  # noqa: E402
from src.db.session import build_engine, dispose_engine, get_db  # noqa: E402
from src.domain.cash_accounts.db_models import CashAccountDB  # noqa: E402
from src.domain.customers.db_models import CustomerDB  # noqa: E402
from src.domain.payment_methods.db_models import BankAccountDB, PaymentMethodDB  # noqa: E402
from src.domain.settings.service import clear_settings_cache  # noqa: E402
from src.domain.users.db_models import UserDB  # noqa: E402
from src.main import app  # noqa: E402
from src.services import registry  # noqa: E402

API_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORD = "Clave-de-prueba-123"
_DEFAULT_HASH = hash_password(DEFAULT_PASSWORD)  # bcrypt es lento: se calcula una vez


def alembic_config(url: str) -> Config:
    cfg = Config(str(API_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.attributes["configure_logger"] = False
    return cfg


def _admin_dsn(url: str) -> tuple[str, str]:
    """(DSN libpq a la base `postgres`, nombre de la base de pruebas)."""
    p = urlparse(url.replace("postgresql+psycopg://", "postgresql://"))
    name = p.path.lstrip("/")
    return p._replace(path="/postgres").geturl(), name


def ensure_database(url: str) -> None:
    dsn, name = _admin_dsn(url)
    with psycopg.connect(dsn, autocommit=True) as conn:
        exists = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone()
        if not exists:
            conn.execute(f'CREATE DATABASE "{name}"')


def drop_database(url: str) -> None:
    dsn, name = _admin_dsn(url)
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


@pytest.fixture(scope="session", autouse=True)
def _migrated_database() -> None:
    ensure_database(TEST_DATABASE_URL)
    command.upgrade(alembic_config(TEST_DATABASE_URL), "head")


@pytest_asyncio.fixture(scope="session")
async def engine(_migrated_database) -> AsyncIterator[AsyncEngine]:
    eng = build_engine(TEST_DATABASE_URL, null_pool=True)
    yield eng
    await eng.dispose()
    await dispose_engine()


# ----------------------------------------------------------------------------- sesiones
@pytest_asyncio.fixture
async def db_session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Sesión dentro de una transacción externa que se deshace al final; los `commit` son savepoints."""
    async with engine.connect() as conn:
        outer = await conn.begin()
        session = AsyncSession(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)
        try:
            yield session
        finally:
            await session.close()
            if outer.is_active:
                await outer.rollback()


async def truncate_all(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        tables = (
            await conn.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename <> 'alembic_version'")
            )
        ).scalars().all()
        if tables:
            joined = ", ".join(f'"{t}"' for t in tables)
            await conn.execute(text(f"TRUNCATE {joined} RESTART IDENTITY CASCADE"))


@pytest_asyncio.fixture
async def committed_db(engine: AsyncEngine) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Fábrica de sesiones con commits reales (concurrencia, `after_commit`). Vacía su base antes y después."""
    await truncate_all(engine)
    try:
        yield async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    finally:
        await truncate_all(engine)


# ----------------------------------------------------------------------------- cliente HTTP
@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[httpx.AsyncClient]:
    """Cliente contra la app; cada request usa `db_session` (todo se deshace al terminar)."""

    async def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def committed_client(committed_db) -> AsyncIterator[httpx.AsyncClient]:
    """Cliente contra la app con sesiones reales por request (usar junto con `committed_db`)."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ----------------------------------------------------------------------------- autouse
@pytest.fixture(autouse=True)
def settings_cache_clear():
    clear_settings_cache()
    yield
    clear_settings_cache()


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    reset_limits()
    yield
    reset_limits()


# ----------------------------------------------------------------------------- fábricas
@dataclass
class AuthUser:
    user: UserDB
    token: str
    password: str

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    @property
    def id(self) -> str:
        return self.user.id


_phone_seq = iter(range(1, 10_000_000))


def next_phone() -> str:
    return f"+58412{next(_phone_seq):07d}"


@pytest_asyncio.fixture
async def make_user(db_session: AsyncSession) -> Callable:
    """`await make_user(UserRole.ADMIN, must_change_password=False)` → `AuthUser` con su token."""

    async def _make(
        role: UserRole = UserRole.ADMIN,
        *,
        must_change_password: bool = False,
        is_active: bool = True,
        phone: str | None = None,
        password: str = DEFAULT_PASSWORD,
        full_name: str | None = None,
    ) -> AuthUser:
        user = UserDB(
            role=role,
            phone=phone or next_phone(),
            full_name=full_name or f"Usuario {role.value.title()}",
            password_hash=_DEFAULT_HASH if password == DEFAULT_PASSWORD else hash_password(password),
            must_change_password=must_change_password,
            is_active=is_active,
        )
        db_session.add(user)
        await db_session.flush()
        return AuthUser(user=user, token=create_access_token(user_id=user.id, role=role.value), password=password)

    return _make


@pytest_asyncio.fixture
async def admin(make_user) -> AuthUser:
    return await make_user(UserRole.ADMIN, full_name="Admin de pruebas")


@pytest_asyncio.fixture
async def customer_cash(db_session: AsyncSession) -> CustomerDB:
    c = CustomerDB(type=CustomerType.RETAIL, contact_name="Cliente Contado", phone=next_phone(),
                   payment_mode=PaymentMode.CASH, credit_days=7)
    db_session.add(c)
    await db_session.flush()
    return c


@pytest_asyncio.fixture
async def customer_credit(db_session: AsyncSession) -> CustomerDB:
    c = CustomerDB(type=CustomerType.WHOLESALE, contact_name="Cliente Crédito", business_name="Bodega Crédito",
                   phone=next_phone(), payment_mode=PaymentMode.CREDIT, credit_limit=Decimal("100.00"), credit_days=7)
    db_session.add(c)
    await db_session.flush()
    return c


@dataclass
class MoneySetup:
    cash_accounts: dict[str, CashAccountDB]
    methods: dict[str, PaymentMethodDB]
    bank_accounts: dict[str, BankAccountDB]


@pytest_asyncio.fixture
async def money_setup(db_session: AsyncSession) -> MoneySetup:
    """Pago móvil y transferencia (Bs, cuenta “Banco Bs”), Zelle (USD) y Efectivo USD (cuenta “Caja”)."""
    cash = {
        "Banco Bs": CashAccountDB(name="Banco Bs", account_type="BANK", currency=Currency.VES),
        "Zelle": CashAccountDB(name="Zelle", account_type="ZELLE", currency=Currency.USD),
        "Caja USD": CashAccountDB(name="Caja USD", account_type="CASH", currency=Currency.USD),
    }
    db_session.add_all(cash.values())
    await db_session.flush()
    spec = [
        ("Pago móvil", PaymentMethodType.MOBILE_PAYMENT, Currency.VES, "Pago móvil", "Banco Bs"),
        ("Transferencia", PaymentMethodType.BANK_TRANSFER, Currency.VES, "Cuenta corriente", "Banco Bs"),
        ("Zelle", PaymentMethodType.ZELLE, Currency.USD, "Zelle", "Zelle"),
        ("Efectivo USD", PaymentMethodType.CASH, Currency.USD, "Caja", "Caja USD"),
    ]
    methods, accounts = {}, {}
    for i, (name, kind, cur, label, cash_name) in enumerate(spec, start=1):
        m = PaymentMethodDB(name=name, type=kind, currency=cur, display_order=i)
        db_session.add(m)
        await db_session.flush()
        a = BankAccountDB(payment_method_id=m.id, account_label=label, cash_account_id=cash[cash_name].id, is_default=True)
        db_session.add(a)
        await db_session.flush()
        methods[name], accounts[name] = m, a
    return MoneySetup(cash_accounts=cash, methods=methods, bank_accounts=accounts)


# ----------------------------------------------------------------------------- dobles inyectables
@dataclass
class MoneyDouble:
    """Doble de `MoneyService` (08 §Interfaces): registra las llamadas a `open_balance`."""

    open_balance_calls: list[dict] = field(default_factory=list)

    async def open_balance(self, session, customer_id, amount, note, actor_id) -> None:
        self.open_balance_calls.append(
            {"customer_id": customer_id, "amount": Decimal(amount), "note": note, "actor_id": actor_id}
        )


@pytest.fixture
def money_double():
    double = MoneyDouble()
    with registry.override("money", double):
        yield double
