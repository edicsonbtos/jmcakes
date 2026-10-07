# 01 — Arquitectura y stack (v2.1)

## Vista general
```
App Android Cliente ─┐  HTTPS · Bearer JWT    ┌──────────── Railway · proyecto "jmcakes" · 1 réplica ─────────┐
App Android Delivery ┼──────────────────────▶ │ api  FastAPI + SQLAlchemy 2 async (psycopg 3) + Alembic        │──▶ Neon Postgres "jmcakes"
                     │                        │      REST /api/v1 (OpenAPI generado, JSON camelCase)          │    (pooler: app · directa: Alembic)
Navegador ───────────┘  cookies httpOnly      │      SSE /api/v1/events · APScheduler (TZ Caracas)            │──▶ FCM (opcional)
 /admin  · /cocina  ───────────────────────▶  │ web  Next.js 16 + Tailwind 4                                   │──▶ Railway Bucket (archivos)
                                              └────────────────────────────────────────────────────────────────┘
```

## Stack
| Capa | Elección |
|---|---|
| API | Python **3.11** (fijado en `api/.python-version` y CI), FastAPI, SQLAlchemy 2.0 async, **driver único `postgresql+psycopg`** (asyncpg prohibido), Pydantic v2. |
| Migraciones | Alembic. **`alembic/env.py` usa `DATABASE_URL_DIRECT`** (Neon sin `-pooler`) si existe. Railway: `preDeployCommand = "alembic upgrade head && python -m scripts.bootstrap"`. |
| Conexión app | `DATABASE_URL` (Neon **-pooler**); si el host contiene `-pooler` → `connect_args={"prepare_threshold": None}` (PgBouncer transaccional). |
| Proceso | `python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT --workers 1 --proxy-headers --forwarded-allow-ips='*'` · `numReplicas = 1` (scheduler y bus de eventos en memoria). |
| Jobs | APScheduler `AsyncIOScheduler(timezone="America/Caracas")` en el lifespan; envoltorio `safe_job(name, fn)` (sesión propia, commit/rollback, log). `SCHEDULER_ENABLED=false` en tests, E2E y CI. |
| Rate limit | slowapi con `key_func` = primer `X-Forwarded-For` (respaldo `client.host`); login limitado por **IP + teléfono**. |
| Tests API | pytest + pytest-asyncio (strict, loop de sesión) + **Postgres 16 real** (local o servicio de CI), **una base por agente** (`panaderia_test_<id>`), esquema por `alembic upgrade head` (nunca `create_all`). |
| Contrato | OpenAPI generado por FastAPI → `contracts/openapi.json` (`api/scripts/export_openapi.py`, `--check` en CI). Mock: Prism. |
| Web | Next.js 16.2.2, React 19.2.4, Tailwind 4, Vitest; Playwright **se ejecuta en GitHub Actions** (el contenedor no puede descargar navegadores). |
| Android | Kotlin 2 · Compose · Material 3 · Hilt · Retrofit/OkHttp · kotlinx.serialization · DataStore · Coil · FCM. `:core:network` y `:core:data` como **módulos JVM puros** (prueban en local); `:core:designsystem`, `:app-cliente`, `:app-delivery` Android (compilan en GitHub Actions). |
| Archivos | Subida **a través de la API** (`POST /api/v1/files`, multipart ≤ 5 MB, tipo validado en servidor) → Railway Bucket (S3) o almacenamiento local en dev/test. Lectura por URL GET prefirmada (TTL 1 h). Sin CORS de bucket. |
| Diseño | Impeccable → `PRODUCT.md`, `DESIGN.md`, `docs/design/tokens.json`. |

## Estructura del repositorio
```
jmcakes/
├─ PRODUCT.md · DESIGN.md · CLAUDE.md · README.md
├─ contracts/openapi.json                    # generado
├─ scripts/dev-setup.sh                      # venv + deps + Postgres local + base del agente
├─ spec/  (money_model.py, test_money_model.py, requirements.txt)
├─ api/
│  ├─ .python-version · requirements.txt · pytest.ini · alembic.ini · alembic/ · railway.toml · nixpacks.toml · .env.example
│  ├─ scripts/ (export_openapi.py, mock.sh, seed.py, bootstrap.py)
│  ├─ src/
│  │  ├─ main.py · config.py
│  │  ├─ core/   (errors.py: catálogo 03 §7 + handlers · schemas.py: ApiModel camelCase · security.py · logging.py)
│  │  ├─ db/     (base.py · session.py · models_registry.py)
│  │  ├─ utils/date_utils.py
│  │  ├─ domain/<x>/ (db_models · schemas · repository · service · interface.py)
│  │  │    auth users customers catalog files settings orders kitchen delivery
│  │  │    payments payment_methods wallet receivables cash_accounts finance exchange_rates
│  │  │    audit closures dashboard
│  │  ├─ api/v1/<archivo>.py              # ver 08 (columna Archivo)
│  │  ├─ services/ (interfaces.py · ledger.py · money.py · events.py · push.py)
│  │  └─ jobs/ (runner.py · bcv_sync.py · unpaid_auto_cancel.py · daily_closing.py)
│  └─ tests/
├─ web/ (src/app/(admin) · src/app/(cocina) · src/app/login · src/app/api/auth · src/components/{ui,layout,admin,cocina} · src/lib · e2e/ · public/)
├─ android/ (core/designsystem · core/network · core/data · app-cliente · app-delivery · gradle wrapper)
├─ e2e/run_scenarios.py
├─ docs/ (plan · design · handoffs · CUESTIONARIO.md)
└─ .github/workflows/ (api.yml · contract.yml · web.yml · android.yml · e2e.yml · release-android.yml · secrets.yml [gitleaks])
```

## Convenciones (obligatorias)
1. **Capas** OpenGravity: router valida y delega; service orquesta y hace commit/rollback; repository `flush()`.
2. **JSON en camelCase**: todo esquema hereda de `core/schemas.py::ApiModel` (`alias_generator=to_camel, populate_by_name=True, from_attributes=True`). Los campos de respuesta usan el nombre de la columna (02) en camelCase. Regla Spectral `casing: camel` en CI.
3. **Dinero**: `Decimal`/`Numeric(14,2)`; JSON string decimal; Android `BigDecimal`. Escritura de saldos solo en `services/ledger.py` con `FOR UPDATE` y `balanceAfter`. Bs mostrados calculados en servidor (03 §0).
4. **Fechas**: UTC naive en BD (`to_utc_naive`); día de negocio Caracas (`get_today_caracas`, `as_caracas_date`, `start_of_day_caracas`, `end_of_day_caracas`); en JSON ISO-8601 con `Z`.
5. **BD**: tablas snake_case, columnas camelCase, IDs cuid2, enums con `name=`, registro único `models_registry.py`, restricciones nombradas.
6. **Errores**: `AppError(code)` → `{detail, code, meta}`; `IntegrityError` → 409 con `code` según la restricción; `OperationalError` → 503; 422 de validación en español. Nada en inglés hacia el usuario.
7. **Idempotencia**: `Idempotency-Key` obligatorio en `POST /orders`, `POST /admin/orders`, `POST /payments`, `POST /admin/customers/{id}/manual-payment`; único por cliente + `requestHash`.
8. **Web**: cliente delgado (no calcula dinero ni estados), `cache: 'no-store'` en vistas operativas, `timeZone: "America/Caracas"`, filtros/paginación del servidor.
9. **Repositorio público**: nada de secretos, datos de clientes, ni comentarios/pruebas que citen incidentes, montos o nombres de producción de OpenGravity (ver 06 §Reglas). `gitleaks` en CI.

## Autenticación
- `users.role` ∈ {ADMIN, PRODUCTION, DELIVERY, CUSTOMER}; login por teléfono + contraseña (bcrypt).
- Access JWT HS256 **30 min** (`sub`, `role`, `cid`) · refresh rotativo 30 días (hash en `refresh_tokens`), con **gracia de 60 s** (`REFRESH_GRACE_SECONDS`) para refresh concurrentes o respuestas perdidas. La ruta web `/api/auth/refresh` serializa las llamadas por cookie, y el `Authenticator` de Android está sincronizado.
- **Web** (corrige el patrón de OpenGravity, que no tenía refresh):
  - Server Action de login guarda **`authToken` y `refreshToken`** en cookies httpOnly, SameSite=Lax, path `/`.
  - `src/app/api/auth/refresh/route.ts` llama `POST /api/v1/auth/refresh` y rota ambas cookies.
  - `src/proxy.ts`: si el access venció y hay `refreshToken` → redirige a `/api/auth/refresh?next=…`; verifica rol por ruta (`/admin/**` ADMIN; `/cocina/**` PRODUCTION|ADMIN). Sin `console.log`.
  - `src/app/api/auth/token/route.ts` (solo mismo origen) entrega al JS un access **fresco** (refresca si quedan < 5 min) para llamadas `Bearer` a la API y para pedir token de SSE. No se copia `set-token` de OpenGravity.
  - `client-api`: ante 401 llama `/api/auth/refresh` una vez y reintenta; si falla → `/login`.
- **Android**: Bearer + interceptor de refresh (OkHttp `Authenticator`).
- **Modo mock** (Prism): los `example` de `accessToken` son JWT HS256 reales firmados con `JWT_SECRET=dev-mock-secret-no-usar-en-prod`, `role=ADMIN`, `exp` 2099, para que el proxy deje pasar en W1/W2.

## Tiempo real (SSE)
- `POST /api/v1/events/token` (Bearer, K/A) → token de 60 s y un solo uso.
- `GET /api/v1/events?token=…&lastEventId=<n>` (también acepta cabecera `Last-Event-ID`); cabeceras `Cache-Control: no-cache`, `X-Accel-Buffering: no`, sin compresión; heartbeat 20 s; buffer de 200 eventos; si no puede reanudar emite `event: reset`.
- Cliente (`useEventStream`): en `onerror` → `close()`, backoff 1/2/5/10 s, token nuevo, reabre con `lastEventId`; en `reset` recarga todo.
- Sobre de evento `{id, type, at, data}` (08 §Eventos). Publicación **después del commit**.

## Variables de entorno (FND copia a `api/.env.example`, DSN a `web/.env.example`)
| Servicio | Variable | Notas |
|---|---|---|
| api | `DATABASE_URL` | Neon pooler (`postgresql+psycopg://…-pooler…`) |
| api | `DATABASE_URL_DIRECT` | Neon directo, para Alembic |
| api | `JWT_SECRET` | aleatorio; compartido con web |
| api | `ENVIRONMENT` | `development`/`staging`/`production` |
| api | `CORS_ORIGINS` | dominio de web |
| api | `STORAGE_BACKEND` | `s3` o `local` |
| api | `S3_ENDPOINT`, `S3_REGION`, `S3_BUCKET`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` | Railway Bucket |
| api | `FCM_CREDENTIALS_JSON` | opcional; vacío = push solo a log |
| api | `SCHEDULER_ENABLED` | `true` en Railway |
| api | `BOOTSTRAP_ADMIN_PHONE`, `BOOTSTRAP_ADMIN_PASSWORD` | crea el primer admin si no hay ninguno |
| api | `SEED_DEMO` | `1` = carga datos de demostración (solo staging) |
| api | `TEST_DATABASE_URL` | solo tests |
| web | `NEXT_PUBLIC_API_URL` | `https://<api>/api/v1` (se incrusta en build) |
| web | `JWT_SECRET` | `${{api.JWT_SECRET}}` (variable de referencia de Railway) |

## Despliegue (Railway)
- Servicios `api` (rootDirectory `api`) y `web` (rootDirectory `web`). **El archivo de config no sigue al rootDirectory**: fijar `railwayConfigFile=/api/railway.toml` y `/web/railway.toml` y verificarlo con `get-service-config`.
- Orden: crear servicios → `generate-domain` de ambos → variables → bucket → conectar repo (rama de integración) → aprobar despliegue (**el dueño**, ver CUESTIONARIO §Requiere al dueño).
- Responsable: el **orquestador** (no un agente en worktree).

## Entornos
| Entorno | BD | Despliegue |
|---|---|---|
| Local / agentes | Postgres 16 local, `panaderia_test_<id>` | — |
| CI | servicio `postgres:16` | push a la rama de integración; `android.yml` también en `block/M` y `block/Q2`; `workflow_dispatch` |
| staging | Neon rama `staging` | Railway, auto desde la rama de integración |
| production | Neon rama `main` | tras aprobación del dueño |

**Restricciones verificadas (2026-10-06)**: sin salida a Neon:5432 (uso por MCP; migraciones por Railway); `dl.google.com` y descargas de navegadores de Playwright bloqueados (Android y Playwright en GitHub Actions); accesibles npm, PyPI, Maven Central, `maven.google.com`, plugins de Gradle.
