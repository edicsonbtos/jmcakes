# 01 — Arquitectura y stack (v2: reutiliza OpenGravity)

## Vista general

```
App Android Cliente ─┐                      ┌──────────── Railway · proyecto "jmcakes" ────────────┐
(Play Store)         │  HTTPS (Bearer JWT)  │                                                       │
App Android Delivery ┼─────────────────────▶│  api  · FastAPI + SQLAlchemy 2 async + Alembic        │──▶ Neon Postgres
(APK)                │                      │       · REST /api/v1  (OpenAPI generado)              │    proyecto "jmcakes"
                     │                      │       · SSE  /api/v1/events (cocina, admin)           │    ramas: main · staging
Navegador ───────────┘                      │       · APScheduler: tasa BCV 06:00, cierre 23:50,    │
 /admin  (admin)        cookie authToken    │         auto-cancelación de impagos                   │──▶ FCM (push)
 /cocina (producción) ─────────────────────▶│  web  · Next.js 16 + Tailwind 4 (panel + cocina)      │──▶ Railway Bucket (fotos,
                                            └───────────────────────────────────────────────────────┘    comprobantes)
```

## Stack

| Capa | Elección | De dónde viene |
|---|---|---|
| API | **Python 3.11+ · FastAPI · SQLAlchemy 2.0 async · psycopg 3 · Pydantic v2** | Igual que `apps/bot` de OpenGravity (sin Telegram). |
| Migraciones | **Alembic**, único ejecutor en producción (`preDeployCommand = "alembic upgrade head"`). | OpenGravity. **No usamos Prisma.** |
| Jobs | **APScheduler** dentro del proceso FastAPI (lifespan), envoltorio `_safe_job` con sesión propia y commit/rollback. | Patrón de `jobs-programados-opengravity`, sin PTB. |
| Tests API | **pytest + pytest-asyncio (strict)** contra **PostgreSQL 16 local** (en el contenedor y en CI como *service*), sesión con savepoint por test. | Fixtures de OpenGravity, adaptadas a Postgres (para que `FOR UPDATE` sea real). |
| Contrato | **OpenAPI generado por FastAPI**, exportado a `contracts/openapi.json` con `scripts/export_openapi.py`. Esquemas Pydantic definidos en F0 = contrato. Mock: **Prism** sobre ese archivo. | — |
| Web | **Next.js 16** (App Router, `src/proxy.ts` como middleware, cookie `authToken`), **Tailwind 4**, `lucide-react`, `recharts`, Vitest. **Leer `node_modules/next/dist/docs/` antes de escribir código.** | `apps/web` de OpenGravity. |
| Android | **Kotlin 2 · Jetpack Compose · Material 3 · Hilt · Retrofit + OkHttp + kotlinx.serialization · DataStore · Coil · FCM**. Un proyecto Gradle: `:core:designsystem`, `:core:network`, `:core:data`, `:app-cliente`, `:app-delivery`. `minSdk 24`. | Nuevo. |
| Diseño | **Impeccable** (`.claude/skills/impeccable`) → `PRODUCT.md`, `DESIGN.md` y tokens compartidos web/Android. | Skill de OpenGravity. |
| Hosting | Railway: servicios `api` (rootDirectory `api/`) y `web` (rootDirectory `web/`), entorno `staging`; luego `production`. | Igual que OpenGravity. |
| BD | Neon `jmcakes` (org personal `org-dawn-bar-06119989`, **nunca** `Finanzas_CAPS`), región aws-us-east-1, PG 17, BD `panaderia`. | — |
| Archivos | Railway Bucket (S3), URL prefirmada. Adaptador local en dev/test. | Nuevo (OpenGravity usaba Telegram/Drive). |

## Estructura del repositorio

```
jmcakes/
├─ PRODUCT.md · DESIGN.md            # Impeccable (producto y sistema visual)
├─ CLAUDE.md                         # reglas para agentes
├─ contracts/openapi.json            # generado desde la API (fuente de verdad del contrato)
├─ api/                              # FastAPI (dueña de TODA la lógica de negocio)
│  ├─ alembic/ · alembic.ini · railway.toml · requirements.txt · pytest.ini
│  ├─ src/
│  │  ├─ main.py · config.py
│  │  ├─ core/        (exceptions, logging, security/jwt, encryption)        ← OpenGravity
│  │  ├─ db/          (base, session, models_registry, types)               ← OpenGravity
│  │  ├─ utils/       (date_utils: Caracas, to_utc_naive)                    ← OpenGravity
│  │  ├─ domain/<x>/  (db_models · schemas · repository · service)           ← patrón OpenGravity
│  │  │   auth · users · customers · catalog · settings · orders · kitchen · delivery
│  │  │   payments · payment_methods · wallet · receivables · cash_accounts
│  │  │   exchange_rates · audit · closures · dashboard · notifications · files
│  │  ├─ api/v1/      (un router por dominio: SOLO valida y delega al service)
│  │  ├─ services/    (ledger.py: TODA escritura de dinero; events.py: bus SSE; push.py: FCM)
│  │  └─ jobs/        (bcv_sync · daily_closing · unpaid_auto_cancel)
│  └─ tests/
├─ web/                              # Next.js 16
│  └─ src/app/(admin)/admin/… · src/app/(cocina)/cocina/… · src/app/login · src/components/ui · src/lib
├─ android/                          # Gradle multi-módulo
├─ spec/                             # modelo ejecutable de las reglas de dinero (ver 07-pruebas)
├─ docs/plan · docs/design · docs/handoffs · docs/CUESTIONARIO.md
└─ .github/workflows/                # api.yml · web.yml · android.yml · contract.yml
```

## Convenciones heredadas de OpenGravity (obligatorias)

1. **Capas:** el router valida y delega; el `service` orquesta y hace `commit`/`rollback`; el `repository` hace `flush()`, **nunca** `commit()`.
2. **Dinero:**
   - `Numeric(14,2)` con `Decimal` en Python, nunca `float`. Tasa `Numeric(14,4)`.
   - En JSON el dinero viaja como **string decimal** (`"12.50"`). Android lo lee con `BigDecimal`.
3. **Toda escritura de dinero pasa por `services/ledger.py`.**
   - Ningún service toca `walletBalance` ni `balance` directamente.
   - Bloqueo **`SELECT … FOR UPDATE`** del cliente o cuenta antes de mover saldo.
   - Cada asiento guarda `balanceAfter`.
4. **USD/VES:** los montos llegan al ledger en USD. Si el pago registró importe local (`amountLocal` y `bcvRateUsed`), ese manda. Nunca se reconvierte dos veces.
5. **Fechas:**
   - Columnas `DateTime` **naive en UTC**; persistir con `to_utc_naive()`.
   - Lógica de “día” con `get_today_caracas()` / `as_caracas_date()`.
   - Nunca `.date()` sobre un UTC crudo.
6. **BD:**
   - Tablas en `snake_case` minúscula; columnas en **camelCase** (nombre físico como primer argumento de `Column`).
   - IDs `String` (cuid2).
   - Los `SQLEnum` llevan `name=` explícito.
   - Registro único de modelos en `src/db/models_registry.py`, usado por alembic, tests y session.
7. **Errores:**
   - `HTTPException(detail="mensaje para el usuario")` en español, o `AppError` con `code`.
   - El cliente muestra `detail` tal cual.
   - Formato: `{"detail": "...", "code": "CREDIT_LIMIT_EXCEEDED", "meta": {...}}`.
8. **Web:**
   - Cliente delgado: **no calcula** dinero ni estados.
   - Vistas operativas con `cache: 'no-store'`.
   - Fechas con `timeZone: "America/Caracas"`.
   - IDs string; filtros y paginación del lado del servidor.
9. **Idempotencia:** header `Idempotency-Key` en crear pedido y reportar pago (columna `idempotencyKey` única).
10. **Cambios quirúrgicos:** `Edit`, no reescrituras, sobre archivos existentes (skill `cambios-quirurgicos`).

## Autenticación

- `users` con `role` ∈ {ADMIN, PRODUCTION, DELIVERY, CUSTOMER}. Login por **teléfono** (E.164 `+58…`) + contraseña (bcrypt, como OpenGravity).
- Access JWT HS256 de 30 min, con `sub`, `role` y `cid` (customerId). Refresh rotativo de 30 días, guardado hasheado.
- **Web:**
  - La Server Action de login guarda la cookie `authToken` (httpOnly).
  - `src/proxy.ts` la verifica con `jose`. Las rutas `/admin/*` requieren ADMIN y `/cocina` requiere PRODUCTION o ADMIN.
  - Las peticiones del navegador a la API llevan `Authorization: Bearer`, con el token obtenido vía `/api/auth/me` como en OpenGravity.
- **Android:** Bearer más refresh automático en un interceptor de OkHttp.
- **SSE:**
  - El navegador no manda headers con `EventSource`, así que primero pide un token de stream de corta vida (`POST /api/v1/events/token`, 60 s, un solo uso).
  - Luego abre `GET /api/v1/events?token=…`. Heartbeat cada 20 s y `Last-Event-ID` para reanudar.

## Tiempo real y push

- **Bus de eventos:**
  - En memoria por proceso (Railway con 1 réplica) detrás de la interfaz `EventBus`.
  - Si se escala, se cambia a Postgres `LISTEN/NOTIFY` sin tocar a los consumidores.
  - Los eventos se emiten **después del commit**: `session.info["after_commit"]`.
- **Push FCM:**
  - Adaptador `PushSender`. Sin credenciales (`FCM_CREDENTIALS_JSON` vacío) solo registra en el log, sin fallar.
  - Tokens inválidos se borran.

## Entornos

| Entorno | API | Web | BD | Despliegue |
|---|---|---|---|---|
| Local / tests | uvicorn :8000 | next dev :3000 | Postgres 16 local | — |
| CI (GitHub Actions) | pytest con Postgres como servicio | build + lint + vitest | servicio `postgres:16` | en cada push a la rama de integración |
| **staging** | Railway `api` | Railway `web` | Neon rama `staging` | auto desde la rama de integración |
| production | Railway | Railway | Neon rama `main` | tras la aprobación del dueño |

**Restricciones de red del entorno de agentes (verificadas el 2026-10-06):**
- **Neon (puerto 5432):** no hay salida. Se maneja por el MCP de Neon, y las migraciones las aplica el `preDeployCommand` de Railway.
- **`dl.google.com`:** bloqueado, así que no se puede instalar el Android SDK en el contenedor. Android se compila en GitHub Actions.
- **Sí accesibles:** `maven.google.com`, Maven Central, Gradle plugins, npm y PyPI.
