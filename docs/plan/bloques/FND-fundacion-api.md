# FND — Fundación de la API, base de datos y contrato

**Fase 0** (en paralelo con DSN) · rama `block/FND` · BD de pruebas `panaderia_test_fnd` · reutiliza OpenGravity según [06](../06-reutilizacion-opengravity.md), **saneando** lo que se copia.

## Objetivo
Dejar `api/` lista para que B1, B2 y B3 trabajen en paralelo sin tocar archivos compartidos, con `contracts/openapi.json` **completo** para W1, W2 y M.

## Alcance
1. **Entorno**
   - `scripts/dev-setup.sh` (raíz):
     - crea `.venv` con Python 3.11;
     - instala `api/requirements.txt` y `spec/requirements.txt`;
     - levanta Postgres (`service postgresql start`) y crea el rol `dev` si falta;
     - crea la base indicada en `$TEST_DATABASE_URL`.
   - `api/.python-version` = 3.11.
   - `api/requirements.txt` con versiones fijas: las de OpenGravity sin PTB, más `apscheduler`, `hypothesis`, `boto3`, `firebase-admin`, `python-multipart`, `cuid2`, `bcrypt`.
2. **Base técnica** (copiada y saneada, ver 06):
   - **Configuración y núcleo**:
     - `config.py`, `db/{base,session,models_registry}.py`;
     - `core/logging.py`, `utils/date_utils.py`, `api/limiter.py` (con `X-Forwarded-For`).
   - **`core/errors.py`**:
     - el catálogo **completo** de 03 §7 (enum `ErrorCode` con HTTP y texto);
     - `AppError(code, meta)`;
     - handlers: `IntegrityError` → 409 con mapa de restricción a `code`; `OperationalError` → 503; validación 422 en español.
   - **Esquemas y seguridad**:
     - `core/schemas.py::ApiModel` en camelCase;
     - `core/security.py` con JWT HS256, bcrypt y refresh.
   - **`main.py`**:
     - CORS;
     - lifespan con `jobs/runner.py`, que corre `AsyncIOScheduler(timezone=America/Caracas)` con `safe_job` y respeta `SCHEDULER_ENABLED`;
     - **todos los routers de 08 registrados**.
   - **Jobs ya registrados** con su horario y un `run(session)` vacío: `jobs/{bcv_sync,unpaid_auto_cancel,daily_closing}.py`. Los dueños solo completan `run`.
3. **Modelos y migración**
   - Todos los `db_models.py` de [02](../02-modelo-de-datos.md), con restricciones **nombradas** en los modelos: CHECKs, índice parcial `uq_payments_method_reference_live`, `uq_orders_customer_idem`, `uq_payments_customer_idem` y la secuencia `order_number_seq` desde 1001.
   - Una revisión Alembic inicial. `alembic/env.py` usa `DATABASE_URL_DIRECT` si existe.
4. **Auth completa:** register (crea un customer CASH), login con rate limit por IP + teléfono, refresh rotativo, logout, me, device-tokens y `DELETE /auth/account`. Dependencias `get_current_user`, `require_role(*roles)` y `get_current_customer`.
5. **Contrato completo**
   - Esquemas Pydantic de **todos** los endpoints de [08](../08-api-endpoints.md), en el archivo de router indicado ahí y con ejemplos realistas: productos venezolanos, dinero en string y fechas con `Z`.
   - Los ejemplos de `accessToken` son **JWT HS256 reales** firmados con `dev-mock-secret-no-usar-en-prod` (`role=ADMIN`, `exp` 2099), y el de `/auth/me` es coherente con ellos.
   - Componentes `EventEnvelope`, `OrderEventData`, `PaymentEventData`, `KitchenCard` y `DeliveryCard` exportados en el OpenAPI, sin campos de dinero en los de cocina y delivery (I-8).
   - Cada operación lleva `openapi_extra={"x-roles": [...]}`. `export_openapi.py --count` imprime el número de operaciones.
   - Endpoints no implementados → `AppError(NOT_IMPLEMENTED)` (501).
   - `api/scripts/export_openapi.py [--check]` → `contracts/openapi.json`.
   - `api/scripts/mock.sh`: Prism en `$MOCK_PORT`.
6. **Interfaces y fábricas** ([08](../08-api-endpoints.md) §Interfaces):
   - `services/interfaces.py` y `domain/*/interface.py` con los Protocol y DTO.
   - Cada fábrica en el archivo del implementador, con el stub descrito.
   - **Reales en FND:** `CustomersService`, `SettingsService`, `AuditService.log`, `RateService.rate_for` (03 §0) y `OrdersService.confirm_paid` (mínimo real). El stub de `MoneyService.checkout` sigue exactamente 08, incluido `expiresAt`.
   - Registro de fábricas `services/registry.py`: se resuelven en tiempo de llamada y las fixtures de prueba pueden sustituirlas.
7. **Dominios que FND deja funcionando:**
   - `exchange_rates`: modelo, repositorio, fetcher, `rate_for` y `sync_daily_rate` (sin endpoints);
   - `audit`: servicio;
   - `settings`: `app_settings` por secciones con caché, sin endpoints.
8. **Pruebas** (diseño obligatorio; **no** copiar el conftest de OpenGravity):
   - **Configuración:**
     - `pytest.ini`: `asyncio_mode = strict`, `asyncio_default_fixture_loop_scope = session` y `asyncio_default_test_loop_scope = session`.
     - `TEST_DATABASE_URL` obligatorio (si falta, `pytest.exit`). El conftest crea la base si no existe y corre `alembic upgrade head` una vez por sesión. Engine con `NullPool`. `SCHEDULER_ENABLED=false`.
   - **Fixtures:**
     - `db_session` con `join_transaction_mode="create_savepoint"`;
     - `committed_db`: TRUNCATE … RESTART IDENTITY CASCADE de **su** base (excepto `alembic_version`) antes y después;
     - `client` (httpx con ASGITransport);
     - `make_user(role)` con su token; `customer_cash`, `customer_credit`, `money_setup` (métodos, cuentas bancarias y cuentas del negocio).
   - **`tests/helpers.py`:** `assert_money_invariants(session)` con el SQL **literal** de 02 (I-1…I-9).
   - **`tests/test_authz_matrix.py`:** lee los roles de `x-roles` de cada operación del OpenAPI y verifica que cada rol no permitido recibe 401/403 en **todas** las operaciones. Nadie más lo edita. Los casos de propiedad (cliente A contra B) van en `tests/bX/test_authz_bX.py` de cada bloque.
   - **`pytest.ini`:** `testpaths = tests`. Una prueba falla si `tests/b1/`, `tests/b2/` o `tests/b3/` existen y recogen 0 pruebas.
   - **Dobles inyectables** (08 §Interfaces): `event_spy`, `push_spy`, `orders_double`, `money_double` y `settings_cache_clear` (autouse).
   - **`tests/test_contract_inventory.py`:** compara (método, ruta) del OpenAPI con el inventario de 08 (104 operaciones).
   - **Refresh:** dos refresh concurrentes y un reintento dentro de la gracia de 60 s (E15).
   - **Pruebas propias:**
     - auth;
     - rate limit con distintos `X-Forwarded-For`;
     - migración upgrade → downgrade base → upgrade sobre `panaderia_migrations_fnd` (la crea y la borra la prueba);
     - `alembic check` sin diferencias;
     - `export_openapi --check`;
     - `rate_for` (MANUAL > BCV > última ≤ d; RATE_UNAVAILABLE; sin commit);
     - las fábricas importables y sus stubs;
     - `core/errors.py` ⊇ `spec.ERROR_CODES`;
     - `IntegrityError` → 409 con `code`;
     - `bootstrap` y `seed` corridos dos veces.
9. **Scripts:**
   - `api/scripts/bootstrap.py` y `api/scripts/seed.py` (07 §5).
   - `api/railway.toml`: `startCommand`, `numReplicas = 1`, `preDeployCommand = "alembic upgrade head && python -m scripts.bootstrap"`, `healthcheckPath = "/api/health"`, `healthcheckTimeout = 120`.
   - `api/nixpacks.toml` nuevo (Python 3.11).
   - `api/.env.example` con todas las variables de 01.
10. **CI:**
    - `.github/workflows/api.yml`: Python 3.11, servicio `postgres:16`, `pip install`, `pytest -q` (con `TEST_DATABASE_URL`), `export_openapi --check` y `pytest spec -q`.
    - `contract.yml`: Spectral con `casing: camel`.
    - `secrets.yml`: gitleaks.
11. **Skills y agente:** `.claude/skills/{contabilidad,migraciones-esquema,tests-api,cambios-quirurgicos,jobs-programados,panel-web}-panaderia/SKILL.md` adaptadas y saneadas, más `.claude/agents/auditor-contable.md` con las invariantes I-1…I-9.
12. `CLAUDE.md` §Comandos con los comandos reales.

## No tocar
`web/`, `android/`, `DESIGN.md`, `docs/design/`.

## Limitantes
- Sin salida a Neon:5432; se usa Postgres local.
- Nada de lógica de B1, B2 ni B3 más allá de los stubs indicados.

## Compuerta G1 (parte FND)
Todo el §8 en verde, con la salida pegada en el handoff, incluido `test_contract_inventory` (104 operaciones).
