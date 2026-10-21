# Adaptado de OpenGravity: apps/bot/src/db/models_registry.py
"""Fuente única de registro de los modelos ORM en `Base.metadata`.

Lo importan `alembic/env.py`, `src/db/session.py` y las pruebas. Al agregar un dominio con
tablas, se agrega aquí su import; `tests/test_schema.py` falla si falta alguna tabla de 02.
"""
from src.db.base import Base  # noqa: F401

import src.domain.users.db_models  # noqa: F401,E402
import src.domain.auth.db_models  # noqa: F401,E402
import src.domain.idempotency.db_models  # noqa: F401,E402
import src.domain.customers.db_models  # noqa: F401,E402
import src.domain.files.db_models  # noqa: F401,E402
import src.domain.catalog.db_models  # noqa: F401,E402
import src.domain.orders.db_models  # noqa: F401,E402
import src.domain.cash_accounts.db_models  # noqa: F401,E402
import src.domain.payment_methods.db_models  # noqa: F401,E402
import src.domain.payments.db_models  # noqa: F401,E402
import src.domain.receivables.db_models  # noqa: F401,E402
import src.domain.wallet.db_models  # noqa: F401,E402
import src.domain.exchange_rates.db_models  # noqa: F401,E402
import src.domain.settings.db_models  # noqa: F401,E402
import src.domain.audit.db_models  # noqa: F401,E402
import src.domain.closures.db_models  # noqa: F401,E402

__all__ = ["Base"]
