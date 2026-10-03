# F0 — Fundación, contrato e infraestructura

**Fase:** 0 (secuencial, bloqueante) · **Esfuerzo:** L · **Rama:** `block/F0-fundacion`

## Objetivo
Dejar el monorepo listo para que **siete agentes trabajen en paralelo** sin pisarse: contrato de API completo, base de datos con todas las tablas, autenticación funcionando, esqueletos de API/web/Android, CI y entorno de staging desplegado.

## Entradas
- Todo `docs/plan/`.
- `docs/CUESTIONARIO.md` (como mínimo C-1 a C-5; si no están, valores por defecto).

## Alcance (tareas)

### 1. Monorepo y convenciones
- `pnpm` workspaces para `api/` y `web/`; `android/` como proyecto Gradle independiente.
- TypeScript estricto, ESLint, Prettier, `.editorconfig`, `.nvmrc` (Node 22).
- `CLAUDE.md` raíz ya existe: completarlo con comandos reales (`pnpm -C api test`, etc.).
- `.env.example` en `api/` y `web/`.

### 2. Contrato `contracts/openapi.yaml` (v1 completa)
- **Todos** los endpoints que necesitan B1–B3, W1, W2, M1, M2 según `03-flujos-de-negocio.md`, con esquemas, ejemplos y códigos de error. Grupos mínimos:
  - `auth`: register, login, refresh, logout, me, device-token.
  - `catalog`: categorías y productos (público para cliente autenticado; CRUD admin), subida de imagen (URL prefirmada), historial de precios.
  - `customers`: perfil propio (cliente); listado/detalle/aprobación/edición/crédito/bloqueo (admin); creación de cliente sin app.
  - `orders`: crear (con `Idempotency-Key`), listar propios, detalle, cancelar (cliente); listar/filtrar/crear/editar/cancelar (admin).
  - `kitchen`: cola por fecha, transición `PREPARING`/`READY`, totales a producir.
  - `delivery`: mis pedidos, transición `OUT_FOR_DELIVERY`/`DELIVERED`.
  - `finance`: billetera y estado de cuenta propio (cliente); reportar pago (con `Idempotency-Key`); admin: pagos pendientes, aprobar/rechazar, cargos/abonos/ajustes manuales, CxC por cliente y global, tasa del día.
  - `dashboard`: resumen del día, top productos, deudores, cierre CSV.
  - `settings`: leer/editar (admin).
  - `events`: `GET /v1/events` (SSE) con tipos de evento documentados.
- Script `pnpm mock` que levanta **Prism** sobre el contrato (para W/M).
- Tag git `contract-v1` al fusionar.

### 3. Base de datos
- Esquema Drizzle completo de `02-modelo-de-datos.md` (todas las tablas, enums, índices, `CHECK wallet_balance_cents >= 0`).
- Primera migración + `seed` de desarrollo: 1 admin, 1 producción, 1 motorizado, 3 clientes (contado, crédito, detal sin app), 3 categorías, 10 productos de panadería venezolana (canilla, pan campesino, pan dulce, cachito, golfeado…), tasa del día.

### 4. API esqueleto (`api/`)
- Fastify + plugins: CORS, helmet, rate limit, logger (pino), manejo de errores con formato único, `/health`.
- `lib/time.ts` (zona Caracas), `lib/money.ts` (centavos, conversión VES/USD), `lib/rbac.ts` (`requireRole`, `requireOwnership`), `lib/idempotency.ts`, `lib/errors.ts`.
- Módulo `auth` **completo** (argon2id, JWT, refresh rotativo, registro de cliente en `PENDING`, `device_tokens`).
- Interfaces + **stubs** de `FinanceService`, `OrdersService`, `Notifier`, `CatalogService`, `CustomersService` (ver `04-fases-y-bloques.md`).
- Rutas registradas por módulo vacías (cada bloque llena las suyas).
- Test de contrato (`test/contract.test.ts`): valida respuestas contra `openapi.yaml`.
- Tests con Postgres real (contenedor de servicio en CI).

### 5. Web esqueleto (`web/`)
- Vite + React + TS + Tailwind + shadcn/ui + TanStack Router/Query.
- `shared/`: cliente API tipado generado desde el contrato (`openapi-typescript` + `openapi-fetch`), login, guard por rol, layout con menú lateral (admin) y layout de pantalla completa (cocina), formato de dinero y hora Caracas, componente de tabla, toasts, hook `useEventStream()` para SSE.
- Rutas vacías `/admin/*` y `/cocina` con “En construcción”.
- `VITE_API_URL` configurable (mock / staging / prod).

### 6. Android esqueleto (`android/`)
- Gradle Kotlin DSL, version catalog, módulos `:core`, `:app-cliente`, `:app-delivery`.
- `:core`: Retrofit + OkHttp (interceptor de auth + refresh automático), kotlinx.serialization, DTOs del contrato, `SessionStore` (DataStore), manejo de errores (`ApiError` con `code`), formato de dinero y hora Caracas, tema Material 3 de marca, componentes comunes, receptor FCM base (detrás de flag si falta `google-services.json`).
- Ambas apps compilan y muestran login funcional contra la API.
- `applicationId`: `com.jmcakes.cliente` y `com.jmcakes.delivery` (confirmar en cuestionario C-12).
- `BASE_URL` por *build flavor* (`mock`, `staging`, `prod`).

### 7. CI/CD e infraestructura
- GitHub Actions: `api.yml` (lint, typecheck, test con Postgres), `web.yml` (lint, typecheck, test, build), `android.yml` (assembleDebug + unit tests en `ubuntu-latest`, que trae Android SDK), `contract.yml` (lint del OpenAPI con Spectral).
- Filtros por ruta (`paths:`) para no compilar Android en cambios de web, etc.
- Neon: proyecto `jmcakes`, ramas `main` (prod) y `staging`. Railway: proyecto `jmcakes`, servicios `api` y `web`, entorno `staging` conectado a la rama `main` del repo; bucket de imágenes. Variables documentadas.
- Despliegue de staging funcionando (`/health` OK).

## Fuera de alcance
- Lógica de negocio de catálogo, pedidos, finanzas (solo stubs).
- Pantallas reales de admin, cocina o apps (solo login y layout).

## Carpetas propias
Todo el esqueleto. Tras F0, las carpetas `shared/core/db/lib/contracts` pasan a ser **compartidas** (solo cambios aditivos).

## Limitantes
- El contenedor de la nube **no tiene Android SDK ni KVM**: compilar Android localmente requiere instalar `cmdline-tools` (si la red lo permite) o apoyarse en el workflow de GitHub Actions. No hay emulador.
- Crear el proyecto de **Firebase** y el **keystore** de firma requiere al humano: dejar todo detrás de variables/archivos opcionales y documentar los pasos.
- El acceso a Neon/Railway depende de que el humano tenga conectados esos MCP en la sesión; si no, dejar scripts y pasos documentados.
- Acciones destructivas en Neon/Railway (borrar ramas, proyectos) siempre con confirmación humana.

## Oportunidades
- **Neon MCP** para crear proyecto, ramas y correr migraciones; **ramas por PR** para tests de integración realistas.
- **Railway MCP** para crear servicios, bucket, variables y ver logs de despliegue.
- El contrato bien hecho multiplica el paralelismo: es la mejor inversión de todo el proyecto. Incluir **ejemplos realistas** en el YAML para que el mock devuelva datos útiles.
- Generar los DTOs Kotlin y los tipos TS desde el mismo contrato evita discrepancias.

## Definición de terminado
- [ ] `pnpm install && pnpm -r test` verde; CI verde en los 4 workflows.
- [ ] `pnpm mock` levanta el mock con todos los endpoints.
- [ ] Staging: `GET /health` responde; login con el usuario admin del seed funciona desde la web de staging.
- [ ] Ambas APKs debug se generan como artefacto en CI.
- [ ] `docs/handoffs/F0.md` con URLs de staging, usuarios de seed, cómo correr todo y estado de cada stub.

## Siguiente
Desbloquea **B1, B2, B3, W1, W2, M1, M2** en paralelo.

## Prompt para lanzar este bloque
```
Eres el agente del bloque F0 del proyecto JM Cakes (repo edicsonbtos/jmcakes).
Lee CLAUDE.md, todo docs/plan/, docs/plan/bloques/F0-fundacion.md y docs/CUESTIONARIO.md.
Ejecuta TODO el alcance de F0 siguiendo docs/plan/05-protocolo-agentes.md:
rama block/F0-fundacion, PRs hacia main, CI verde, handoff en docs/handoffs/F0.md,
STATUS.md actualizado. Usa los MCP de Neon y Railway si están disponibles (pide
confirmación antes de cualquier acción destructiva). Si falta una credencial
(Firebase, keystore), deja la integración detrás de una variable y documéntalo.
No implementes lógica de negocio de otros bloques: solo interfaces y stubs.
```
