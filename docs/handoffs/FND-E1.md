# Handoff FND-E1 — Fundación de la API, base de datos y contrato (etapa E1)

Rama `block/FND-E1`. Ficha base FND recortada según `docs/plan/09` §E1. Base de pruebas
`panaderia_test_fnd` (+ `panaderia_migrations_fnd`, que crea y borra la prueba de migración) y puerto 8001.

## Hecho
- **Esquema completo de 02** en una sola revisión Alembic (`api/alembic/versions/0001_fnd_esquema_inicial.py`):
  las 24 tablas, incluidas las que E1 no usa todavía (pedidos, archivos, dispositivos y cierres), con:
  - enums nativos con nombre (`src/db/enums.py`);
  - restricciones nombradas por convención (`ck_<tabla>_<nombre>`, `uq_…`): `uq_users_phone`,
    `uq_orders_customer_idem`, `uq_payments_customer_idem`, `uq_idempotency_records_scope_key`,
    `ck_customers_wallet_nonneg`, `ck_receivables_paid_range`, `ck_cash_account_transactions_amount_sign`, etc.;
  - el índice único parcial `uq_payments_bank_account_reference_live` (libera la referencia solo en
    REJECTED o REVERSED + ENTRY_ERROR);
  - las secuencias `order_number_seq` (desde 1001), `wallet_movements_seq` y `cash_account_tx_seq`;
  - un índice para cada FK; fechas asignadas en Python (`utcnow()`), sin `func.now()`.
- **Base técnica:** `config.py` (sin `.env` bajo pytest), `db/{base,columns,enums,session,models_registry}.py`
  (engine perezoso, `timezone=UTC`, `prepare_threshold=None` con `-pooler`, `NullPool` en pruebas),
  `core/{errors,schemas,security,logging,examples}.py`, `utils/{date_utils,money,phone,ids}.py`,
  `api/limiter.py` (clave `X-Real-IP`, respaldo `client.host`).
- **`core/errors.py`:** el catálogo completo de 03 §7 (código, HTTP y texto, verificado contra el documento),
  `AppError(code, meta, detail)`, y handlers:
  - `IntegrityError` → 409 con el `code` de la restricción;
  - `OperationalError` → 503;
  - validación → 422 `VALIDATION_ERROR` con el detalle en español;
  - 404 y 405 en español; un error no controlado → 500 sin detalles técnicos.
- **Auth de E1** (`api/v1/auth.py`, `domain/auth/`):
  - login con teléfono normalizado a E.164 y límite de 5/min por `X-Real-IP` y 5/min por teléfono;
  - refresh rotativo con gracia de 60 s y `SELECT … FOR UPDATE` (dos refresh concurrentes funcionan);
  - logout (con `refreshToken` revoca esa sesión; sin cuerpo, todas);
  - `me` y `change-password` (revoca todas las sesiones, quita `mustChangePassword` y devuelve un par nuevo; queda auditado).
  - Dependencias `get_current_user`, `require_role(*roles)` y `access(*roles)`. Esta última pone las
    dependencias y los `x-roles` de cada operación en un solo lugar.
  - En E1 solo ADMIN inicia sesión. Con `mustChangePassword`, toda operación de admin responde
    `403 FORBIDDEN` con `meta.reason = MUST_CHANGE_PASSWORD`.
- **Contrato E1:** las **52 operaciones** del inventario de 09, cada una en su archivo de router (08), con
  esquemas `ApiModel` en camelCase, `x-roles`, respuestas de error y ejemplos realistas (dinero como
  string, fechas con `Z`, `accessToken` de ejemplo = JWT HS256 real con el secreto del mock, ADMIN, `exp` 2099).
  - Los cuerpos de las operaciones de B-E1a y B-E1b responden `501 NOT_IMPLEMENTED` con `meta.owner`
    hasta que su bloque los complete.
  - No hay ninguna ruta fuera del inventario de E1.
  - `contracts/openapi.json` está generado. Los errores de validación usan `ErrorOut`, no `HTTPValidationError`.
- **Interfaces de E1 congeladas** (`services/interfaces.py` + `domain/{customers,settings,audit,exchange_rates,finance}/interface.py`)
  y registro de fábricas resuelto en tiempo de llamada (`services/registry.py`, con `override` para pruebas):
  - reales: `CustomersService.get_for_update/get_by_user`, `SettingsService.get/update` (secciones de 02,
    caché de 30 s, sin commit), `AuditService.log` (sin commit) y `RateService.rate_for/rate_for_or_none`;
  - stubs: `MoneyService.open_balance` (no escribe; en pruebas, `money_double`) y
    `FinanceQueries.balances_for/debt_subquery` (ceros).
- **Tasa:** fetcher de DolarAPI que solo acepta JSON con `promedio` numérico > 0 (lee números como
  `Decimal`, guarda `fechaActualizacion` en metadata); `sync_daily_rate` inserta la BCV de hoy solo si falta.
- **Jobs:** `jobs/runner.py` con `AsyncIOScheduler(America/Caracas)`, `safe_job` y `SCHEDULER_ENABLED`;
  solo `bcv_sync` registrado (06:00), cuyo `run` llama a `sync_daily_rate`.
- **Scripts:** `scripts/export_openapi.py [--check|--count]`, `scripts/mock.sh` (Prism 5.16.0),
  `scripts/bootstrap.py` (admin con `mustChangePassword`; falla con `SEED_DEMO=1` sin `SEED_PASSWORD`) y
  `scripts/seed.py` con el seed de E1 de 09 §Datos (idempotente).
- **Pruebas** (arnés de FND §8): `pytest.ini` estricto con loop de sesión; conftest con el aislamiento de la
  base antes de importar `src.*`, `db_session`, `committed_db`, `client`, `committed_client`, `make_user`,
  `admin`, `customer_cash`, `customer_credit`, `money_setup`, `money_double`, `settings_cache_clear`
  (autouse) y reinicio de límites; `tests/helpers.py::assert_money_invariants` con el SQL de 02.
- **Infra:** `api/railway.toml` (Railpack, `preDeployCommand = "alembic upgrade head && python -m scripts.bootstrap"`,
  health `/api/health`, 1 réplica, us-east4), `api/.env.example`, `api/.python-version`,
  `.github/workflows/{api,contract,secrets}.yml`, `.gitleaks.toml`, `contracts/.spectral.yaml`,
  `scripts/dev-setup.sh`, `CLAUDE.md` §Comandos.
- **Skills y agente:** `.claude/skills/{contabilidad,migraciones-esquema,tests-api,cambios-quirurgicos,jobs-programados,panel-web}-panaderia/SKILL.md`
  y `.claude/agents/auditor-contable.md` (I-1…I-9). Escritos con las reglas de la panadería; no copian
  datos ni comentarios de producción de OpenGravity.

## Pruebas ejecutadas (comando → resultado)
Entorno: contenedor del agente, Python 3.11.15, PostgreSQL 16 local, rol `dev`.

```text
$ cd api && TEST_DATABASE_URL=postgresql+psycopg://dev:dev@127.0.0.1:5432/panaderia_test_fnd ../.venv/bin/python -m pytest -q
262 passed, 5 skipped in 28.02s
  (los 5 skipped son las 5 operaciones públicas en la prueba de “rol no permitido”: no tienen rol que rechazar)

$ cd api && ../.venv/bin/python -m scripts.export_openapi --check
contracts/openapi.json al día.

$ cd api && ../.venv/bin/python -m scripts.export_openapi --count
52

$ .venv/bin/python -m pytest spec -q
58 passed in 1.39s

$ npx --yes @stoplight/spectral-cli@6.16.3 lint contracts/openapi.json --ruleset contracts/.spectral.yaml --fail-severity error
No results with a severity of 'error' found!
  (verificado aparte que la regla camelCase falla con una propiedad snake_case)

$ gitleaks dir . --config .gitleaks.toml          (binario v8.28.0)
no leaks found

$ DATABASE_URL=…/panaderia_dev_fnd alembic upgrade head && python -m scripts.bootstrap   (dos veces, SEED_DEMO=1)
Bootstrap listo: {'admin': '…', 'seed': {'products': 12, 'customers': 3}}   (igual la segunda vez; 12 productos, 3 clientes, 1 usuario)

$ uvicorn src.main:app --port 8001   (SCHEDULER_ENABLED=true)
GET /api/health → {"status":"ok","version":"0.1.0","db":"ok"}; login del admin del bootstrap → par de tokens;
GET /admin/customers → 403 MUST_CHANGE_PASSWORD; change-password → 200; “Programador iniciado con 1 job(s)”.

$ MOCK_PORT=4019 api/scripts/mock.sh
Prism sirve el contrato; /admin/dashboard/summary y /auth/login devuelven los ejemplos.
```

Las pruebas incluyen (G1-E1):
- `test_migrations.py`:
  - upgrade → downgrade base → upgrade en `panaderia_migrations_fnd` (sin tablas, enums ni secuencias tras el downgrade);
  - `alembic check` sin diferencias y una sola cabeza;
  - restricciones nombradas, el índice parcial y un índice en toda FK.
- `test_contract_inventory.py`:
  - inventario E1 = 52 ⊆ 08;
  - el OpenAPI tiene exactamente esas operaciones;
  - `--count` = 52 y `--check`;
  - el JWT de ejemplo y el dinero como string.
- `test_authz_matrix.py`: con cada `x-roles`, sin token → 401; rol no permitido → 401/403; admin con
  `mustChangePassword` → 403 en todas las operaciones de admin.
- `test_auth.py`: login, formatos de teléfono, inactivo, solo ADMIN, refresh, gracia y vencido, **dos
  refresh concurrentes con `committed_db` (E15)**, logout, change-password y auditoría (CU-11).
- `test_rate_limit.py`: mismo `X-Real-IP` con XFF distinto → el sexto intento da 429; mismo teléfono
  desde IPs distintas → 429; el teléfono se cuenta normalizado.
- `test_rates.py`:
  - `rate_for`: MANUAL > BCV > la más reciente ≤ d; RATE_UNAVAILABLE; sin commit;
  - sync: inserta una vez; un sync repetido no cambia el valor; la MANUAL manda;
  - HTML, texto, cero, negativo, JSON roto o error 500 → error sin insertar;
  - horario del job.
- `test_factories.py`: las fábricas son importables y cumplen su Protocol, más los stubs y `money_double`.
- `test_errors.py`: el catálogo es igual a 03 §7 (HTTP y texto) ⊇ `spec.ERROR_CODES`; `IntegrityError`
  real → 409 `PHONE_TAKEN`; 503, 500, 404, 501 y float → 422.
- `test_scripts.py`: bootstrap y seed corridos dos veces dan el mismo resultado y cumplen las invariantes.
- `test_config.py`: `.env.example` = claves de `Settings`; el engine usa `TEST_DATABASE_URL`; día de
  Caracas (22:30 VET); redondeo; E.164.
- `test_money_invariants_helper.py`: el SQL es copia de 02; detecta descuadres; un pedido a crédito
  ejercita I-2, I-4, I-5 e I-9.

**Solo en CI** (no corrieron en GitHub Actions desde aquí; los agentes no publican):
- `api.yml`, `contract.yml` y `secrets.yml`. Sus comandos sí se ejecutaron en local con el mismo
  resultado, salvo el escaneo de **historial** de gitleaks: el sandbox del agente no permite
  `gitleaks git`, así que solo corrió `gitleaks dir`.
- No aplica Playwright ni Android.

## Endpoints / pantallas entregados
| Archivo (dueño) | Operaciones | Estado |
|---|---|---|
| `health.py`, `auth.py` (FND-E1) | `GET /api/health`; `POST /auth/login\|refresh\|logout\|change-password`; `GET /auth/me` | **Implementadas** |
| `catalog.py` (B-E1a) | categorías (3), productos (4), `bulk-price/preview\|apply`, `price-history` | Contrato; 501 hasta B-E1a |
| `customers.py` (B-E1a) | `GET\|POST /admin/customers`, `GET\|PATCH /{id}`, `/{id}/credit`, `import/preview\|apply` | Contrato; 501 |
| `users.py`, `settings.py`, `audit.py` (B-E1a) | usuarios (4), `settings/public`, `GET\|PATCH /admin/settings`, `GET /admin/audit` | Contrato; 501 |
| `rates.py`, `payment_methods.py`, `cash_accounts.py` (B-E1b) | tasa (4), métodos (3), cuentas bancarias (3), cuentas del negocio (3) | Contrato; 501 |
| `admin_money.py`, `payments.py`, `dashboard.py` (B-E1b) | `fiado/quote`, `fiado`, `manual-payment/quote`, `manual-payment`, `receivables/{id}/void`, `statement`, `payments/{id}/reverse`, `dashboard/summary` | Contrato; 501 |

Total: **52**, verificado por `test_contract_inventory.py`.

## Cambios a archivos compartidos (aditivos)
- `CLAUDE.md` §Comandos: comandos reales (solo esa sección).
- `.gitleaks.toml` en la raíz (lo pide FND, Ajustes v2.3), con una lista blanca solo para los valores de
  ejemplo públicos (secreto del mock, refresh de ejemplo, contraseñas y tokens de vista previa de ejemplo).
- `contracts/.spectral.yaml`: reglas de Spectral (camelCase en propiedades y parámetros, `x-roles` obligatorio).
- `spec/requirements.txt` con versiones fijas (`pytest==9.0.3`, `hypothesis==6.140.2`).

## Dependencias nuevas pedidas
Ninguna fuera de la lista de 06. `api/requirements.txt`, todas con `==`:
- fastapi 0.135.3, starlette 1.0.0, uvicorn 0.42.0, SQLAlchemy 2.0.48, psycopg[binary] 3.3.3,
  alembic 1.16.5, pydantic 2.12.5, pydantic-settings 2.13.1, python-dotenv 1.2.2;
- slowapi 0.1.9, limits 5.8.0, httpx 0.28.1, bcrypt 5.0.0, cuid2 2.0.1, APScheduler 3.11.2,
  reportlab 4.4.10, python-multipart 0.0.24, tzdata 2026.1, Pillow 12.2.0;
- PyJWT 2.10.1, boto3 1.40.30, firebase-admin 7.1.0, pywebpush 2.0.3;
- pytest 9.0.3, pytest-asyncio 1.3.0, hypothesis 6.140.2.

## Decisiones por defecto tomadas
1. **Login de otros roles en E1:** si la contraseña es correcta pero el rol no es ADMIN → `403 FORBIDDEN`
   (`meta.reason = ROLE_NOT_ENABLED`). Los roles habilitados están en `domain/auth/service.py::LOGIN_ROLES`.
   Un usuario inactivo → `401 INVALID_CREDENTIALS`.
2. **`mustChangePassword`** se aplica también en la API, no solo en `proxy.ts`. Las operaciones de admin
   responden `403 FORBIDDEN`, con `meta.reason = MUST_CHANGE_PASSWORD` y el texto “Debes cambiar tu
   contraseña antes de continuar.”. `me`, `logout` y `change-password` siguen permitidas.
3. **`logout`** responde 204. Con `{refreshToken}` revoca esa sesión; sin cuerpo, todas.
   **Respuesta de login, refresh y change-password:** `{accessToken, refreshToken, tokenType, expiresIn, user, customer}`.
4. **Límites:** 5 intentos por minuto por IP y 5 por teléfono. Para la clave del teléfono se usa el número normalizado.
5. **`IntegrityError` sin código mapeado** → 409 `VALIDATION_ERROR` (“Revisa los datos: ya existe un registro igual o falta
   uno relacionado.”). Solo se mapean las únicas que el usuario puede violar (`CONSTRAINT_CODES`). Un error
   no controlado → 500 con `code = SERVICE_UNAVAILABLE` y el texto del catálogo.
6. **Enums:**
   - viven en `src/db/enums.py`;
   - `PaymentMethodType` es `MOBILE_PAYMENT | BANK_TRANSFER | ZELLE | CASH` (CASH = efectivo, sin referencia);
   - `idempotency_records` está en `domain/idempotency/db_models.py`, y `refresh_tokens` y `device_tokens` en `domain/auth/db_models.py`.
7. **Recortes de E1 en el contrato:**
   - sin `imageUrl` ni `imageFileId` en productos (E1 sin fotos);
   - sin `orderId` en el abono (llega con E2);
   - `GET /settings/public` con la forma completa de 08;
   - `POST /admin/customers/{id}/credit` acepta `paymentMode` opcional (B-E1a lo deja en CASH);
   - `dashboard/summary` solo con los campos de 09.
8. **`Idempotency-Key`:** obligatoria en `fiado` y `manual-payment` (08). Opcional en `void`, `reverse` e
   `import/apply`, porque la web la envía en esos reintentos (09 §Requisitos de uso).
9. **Estado de cuenta:** `format=json` devuelve `StatementOut`, `csv` devuelve `text/csv` y `whatsapp` devuelve `text/plain`.
10. **Listas:** todas devuelven `{items, nextCursor}`, también las cortas (categorías, métodos, cuentas). En el
    contrato, el nombre de cada página es `<Modelo>Page`.
11. **Seed de E1:**
    - Los saldos anteriores ($50 de deuda y $10 a favor) pasan por `MoneyService.open_balance`. Con el
      stub de FND no escriben nada; con el de B-E1b, sí.
    - El fiado de 2 líneas del mayorista se inserta como CxC `MANUAL` con sus `receivable_items` (cliente
      sin saldo a favor, así que no hay nada que liquidar ni ninguna billetera que mover). Así no hace
      falta una interfaz de fiado que 09 no congela.
    - Si no hay admin del bootstrap, el seed crea uno de demostración (`+584120000001`) con `SEED_PASSWORD`
      y `mustChangePassword`.
    - Tasas de demostración: BCV 182.4500 y MANUAL 183.0000.
12. **`bcv_sync.run`** llama a `sync_daily_rate` (real de FND); B-E1b es dueño del archivo y puede ampliarlo.
13. **`SettingsService`:** las firmas llevan `session` (`get(session, section)` y `update(session, section, data, actor_id)`).
    Todas las fábricas de 08 son stateless y reciben la sesión como primer argumento.

## Pendiente / diferido
- Por diseño de E1, sin stubs ni rutas: `register`, `device-tokens`, `DELETE /auth/account`,
  `get_current_customer`, los jobs `unpaid_auto_cancel` y `daily_closing`, `nixpacks.toml` (Railpack lo
  reemplaza, Ajustes v2.3), las interfaces de pedidos, eventos, push y archivos, y las fixtures
  `event_spy`, `push_spy` y `orders_double`. Llegan con E2–E4.
- CI en GitHub Actions: los workflows están escritos y sus comandos corren en local; el orquestador los
  verá en verde o en rojo al publicar.

## Solicitudes de cambio (rompen compatibilidad)
1. **docs/plan/02 §Invariantes, I-9:** en Postgres, el SQL literal falla
   (`operator does not exist: "OrderPaymentStatus" <> text`), porque `paymentStatus` es un enum nativo y el
   `CASE` devuelve `text`. Propuesta: `o."paymentStatus"::text <> CASE …`.
   - `tests/helpers.py` ya usa esa forma (constante `I9_ENUM_CAST`), y la prueba de copia literal la tiene en cuenta.
   - Sugiero actualizar 02 y `.claude/agents/auditor-contable.md` si se cita el SQL.
2. **Documentación incoherente:**
   - Las fichas `FND`, `B1` y `B3` dicen “inventario (51 operaciones)” en su encabezado, pero 09, 07 y 08 dicen 52.
   - La ficha FND nombra el índice `uq_payments_method_reference_live`, y 02 lo llama
     `uq_payments_bank_account_reference_live` (se usó el de 02).
   - Solo afecta a los documentos.

## Para el siguiente bloque
- **Todos:**
  - corran `scripts/dev-setup.sh` con su `TEST_DATABASE_URL` y lean `.claude/skills/tests-api-panaderia`;
  - la actorización va en el decorador con `**access(UserRole.ADMIN)`, que ya está puesto. Para el actor,
    agreguen `user: CurrentUser` (`domain/auth/deps.py`) y `session: DbSession`;
  - los cuerpos `not_implemented(OWNER)` se reemplazan por la implementación;
  - pueden **ampliar** su `schemas.py` y su router sin quitar campos.
- **B-E1a:**
  - `CustomersService` y `AuditService.log` ya son reales;
  - `SettingsService.update` valida con los modelos de `domain/settings/interface.py::SECTIONS`. Agreguen
    validaciones (HH:MM, etc.) sin cambiar la firma;
  - para el saldo anterior usen `registry.get("money").open_balance(...)` y prueben con `money_double`;
  - para la deuda, `registry.get("finance").debt_subquery()`, que es un stub con ceros. Para probar el
    filtro y el orden, usen `registry.override("finance", doble)`;
  - `utils/phone.py` tiene `normalize_phone` y `phone_digits_query` (el “0” equivale a “58”);
  - la importación guarda la vista previa en `idempotency_records` (scope `admin.customer_import`).
- **B-E1b:**
  - reemplacen `services/money.py` (`open_balance`) y `domain/finance/queries.py` manteniendo las
    fábricas `get_money_service` y `get_finance_queries`, y los Protocol;
  - `RateService.rate_for` y `sync_daily_rate` ya son reales; `POST /admin/rates/sync` debe usar una sesión propia;
  - `assert_money_invariants` está en `tests/helpers.py`, y `money_setup` crea los 4 métodos con sus cuentas;
  - antes de entregar, pasen `auditor-contable`.
- **W-E1 / orquestador:**
  - corran `cd web && npm run gen:api` con este `contracts/openapi.json`;
  - para el mock, `MOCK_PORT=4011 api/scripts/mock.sh`. El `accessToken` de ejemplo pasa el `proxy.ts`
    con `JWT_SECRET=dev-mock-secret-no-usar-en-prod`;
  - la web recibe `403` con `meta.reason = MUST_CHANGE_PASSWORD` si no se cambió la contraseña.
- **Q-E1:** el `preDeployCommand` de Railway ya corre `alembic upgrade head && python -m scripts.bootstrap`.
  En staging: `SEED_DEMO=1` con `SEED_PASSWORD`, y `BOOTSTRAP_ADMIN_PHONE` y `BOOTSTRAP_ADMIN_PASSWORD` del dueño.
