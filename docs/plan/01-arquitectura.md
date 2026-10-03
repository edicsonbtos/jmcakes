# 01 — Arquitectura y stack

## Vista general

```
                    ┌──────────────────────────────────────────┐
                    │              Railway (hosting)            │
 App Android        │                                           │
 Cliente  ──HTTPS──▶│  api  (Node 22 + Fastify + TypeScript)    │──▶ Neon Postgres
 (Play Store)       │   ├─ REST /v1  (contrato OpenAPI)         │     (main / staging / ramas por PR)
                    │   ├─ SSE  /v1/events  (cocina, admin)     │
 App Android        │   ├─ FCM  (push a cliente y motorizado)   │──▶ Firebase Cloud Messaging
 Delivery ──HTTPS──▶│   └─ subida de imágenes                   │──▶ Railway Bucket (S3)
 (APK)              │                                           │
                    │  web  (React + Vite, estático)            │
 Navegador ────────▶│   ├─ /admin    → Administrador            │
 (PC / tablet)      │   └─ /cocina   → Producción               │
                    └──────────────────────────────────────────┘
```

Un solo backend (`api`), una sola base de datos, una sola web con dos áreas por rol, dos apps Android que comparten un módulo `core`.

## Stack elegido y por qué

| Capa | Elección | Motivo |
|---|---|---|
| Base de datos | **Neon Postgres** | Experiencia previa del dueño; **ramas** por PR/staging gratis; MCP disponible para que los agentes migren y consulten. |
| Hosting | **Railway** | Experiencia previa; MCP disponible; despliegue desde GitHub; buckets S3 nativos. |
| API | **Node.js 22 + TypeScript + Fastify** | Rápido, tipado, mismo lenguaje que la web; ecosistema que los agentes dominan. |
| ORM / migraciones | **Drizzle ORM + drizzle-kit** | SQL explícito, migraciones versionadas en el repo, tipado end-to-end. |
| Validación | **Zod** | Mismo esquema para validar requests y tipar. |
| Contrato | **OpenAPI 3.1** escrito a mano en `contracts/openapi.yaml` | *Contract-first*: permite que web y Android avancen en paralelo contra un **mock** (Prism) antes de que exista la API. |
| Tiempo real web | **Server-Sent Events (SSE)** | Más simple que WebSockets, pasa por el proxy de Railway, suficiente para “nuevo pedido”. |
| Push móvil | **Firebase Cloud Messaging** | Estándar en Android; notificación aunque la app esté cerrada. |
| Imágenes | **Railway Bucket** (S3-compatible) | Sin otro proveedor; URLs prefirmadas. |
| Web | **React 19 + Vite + TypeScript + TanStack Router/Query + Tailwind + shadcn/ui** | SPA estática barata de servir; componentes listos para backoffice. Cliente tipado generado del contrato (`openapi-typescript` + `openapi-fetch`). |
| Android | **Kotlin 2 + Jetpack Compose + Material 3 + Hilt + Retrofit/OkHttp + kotlinx.serialization + DataStore + Coil** | Stack moderno estándar; un proyecto Gradle con módulos `:core`, `:app-cliente`, `:app-delivery`. `minSdk 24` (teléfonos económicos comunes en Venezuela). |
| Tests | Vitest (API/web), Playwright (E2E web), JUnit + Robolectric + Compose UI test (Android, sin emulador) | Todo corre en CI y en contenedores sin KVM. |
| CI | **GitHub Actions** | Los runners `ubuntu-latest` traen Android SDK: los agentes en la nube compilan Android ahí aunque su contenedor no tenga SDK. |

## Estructura del repositorio (monorepo)

```
jmcakes/
├─ CLAUDE.md                  # reglas para cualquier agente que trabaje aquí
├─ contracts/
│  └─ openapi.yaml            # FUENTE DE VERDAD de la API
├─ api/                       # backend Fastify
│  ├─ src/
│  │  ├─ modules/
│  │  │  ├─ auth/             # F0
│  │  │  ├─ catalog/          # B1
│  │  │  ├─ customers/        # B1
│  │  │  ├─ settings/         # B1
│  │  │  ├─ orders/           # B2
│  │  │  ├─ kitchen/          # B2
│  │  │  ├─ delivery/         # B2
│  │  │  ├─ notifications/    # B2 (SSE + FCM)
│  │  │  ├─ finance/          # B3 (billetera, CxC, pagos)
│  │  │  └─ dashboard/        # B3
│  │  ├─ db/                  # schema Drizzle + migraciones (F0; cambios vía PR con nota)
│  │  └─ lib/                 # tiempo, dinero, errores, rbac (F0)
│  └─ test/
├─ web/                       # React + Vite
│  └─ src/
│     ├─ app/admin/           # W1
│     ├─ app/cocina/          # W2
│     └─ shared/              # F0 (layout, auth, cliente API)
├─ android/                   # proyecto Gradle
│  ├─ core/                   # F0 (red, sesión, DTOs, tema)
│  ├─ app-cliente/            # M1
│  └─ app-delivery/           # M2
├─ docs/
│  ├─ plan/                   # este plan
│  ├─ handoffs/               # notas de entrega de cada bloque
│  └─ CUESTIONARIO.md
└─ .github/workflows/         # CI por carpeta (api, web, android)
```

**Regla de propiedad:** cada bloque solo escribe en sus carpetas. Así siete agentes pueden trabajar en paralelo sin conflictos de merge.

## Decisiones transversales

### Dinero
- Todo monto se guarda en **centavos enteros** (`bigint`) en la **moneda base** (USD por defecto, ver cuestionario). Nunca `float`.
- Los pagos en bolívares guardan `monto_ves`, `tasa_aplicada` y el equivalente en moneda base, calculado al aprobar.
- Tasa del día: tabla `exchange_rates` que el admin carga (o se automatiza luego con BCV).

### Tiempo
- En BD: `timestamptz` (UTC).
- “Día de negocio” = día calendario en `America/Caracas`. Helpers únicos en `api/src/lib/time.ts` (`startOfBusinessDay`, `businessDate(ts)`). Prohibido calcular “hoy” con la zona del servidor.
- La web y las apps muestran siempre en hora de Caracas, independientemente de la zona del dispositivo.

### Seguridad
- Contraseñas con **argon2id**. Access token JWT 15 min + refresh token rotativo 30 días (guardado hasheado).
- RBAC por ruta: `requireRole('ADMIN')`, etc. Un cliente solo ve sus propios datos (chequeo de propiedad en cada consulta).
- Cocina **no ve montos** de dinero; el motorizado solo ve nombre, dirección, teléfono, items y monto a cobrar si aplica.
- Rate limit en login y registro. CORS limitado al dominio web.
- Secretos solo en variables de Railway / GitHub Secrets. Nunca en el repo.

### Entornos
| Entorno | API | Web | BD |
|---|---|---|---|
| Local / CI | localhost | localhost | Postgres en contenedor de CI |
| PR preview (opcional) | Railway PR env | Railway PR env | Rama Neon por PR |
| Staging | `api-staging` | `web-staging` | Rama Neon `staging` |
| Producción | `api` | `web` | Rama Neon `main` |

### Errores y API
- Formato de error único: `{ "error": { "code": "CREDIT_LIMIT_EXCEEDED", "message": "texto para el usuario", "details": {} } }`.
- Versionado en ruta: `/v1/...`.
- Paginación por cursor: `?cursor=&limit=`.
- Idempotencia en creación de pedidos y reportes de pago: header `Idempotency-Key` (las conexiones móviles en Venezuela fallan y reintentan).
