# 06 — Reutilización de OpenGravity (v2.3)

OpenGravity, el sistema privado de préstamos del dueño, está clonado en **`/home/user/opengraviti`** (abreviado `OG/`). De él se reutilizan **estructura y patrones probados**. Las reglas de la panadería las definen 01, 02 y 03, no el código de origen.

La lista de piezas puntuales que **no** se copian, o que se reescriben, está en una nota **privada** fuera del repositorio: **`/home/user/panaderia-privado/NO-COPIAR-OPENGRAVITY.md`**. Todo agente que copie de OG la lee antes de empezar.

## Reglas para copiar (este repo es PÚBLICO)
1. Adaptar mínimamente.
   - Quitar Telegram, préstamos, bóvedas, cuotas, KYC y encriptación.
   - Primera línea del archivo: `# Adaptado de OpenGravity: <ruta>`.
2. **Sanear:**
   - sin comentarios de incidentes ni IDs de hallazgos;
   - sin montos, fechas, personas, clientes ni nombres de proyectos u organizaciones de producción;
   - las pruebas se nombran por comportamiento.
3. Nunca copiar `.env`, secretos, datos, `v1-legacy/`, `scratch/` ni backups.
4. Las pruebas de OG que cubran código copiado se adaptan a Postgres, salvo las que indique la nota privada.
5. `gitleaks` corre en CI.
6. **Ni el código ni los documentos de este repositorio describen defectos de OpenGravity.** Se escriben reglas de la panadería en positivo (“la tasa nunca tiene respaldo”, “no hay borrado físico de pagos”). El detalle va a la nota privada.

## Mapa — API (`OG/apps/bot/`)
| Necesidad | Origen | Destino | Bloque | Cómo |
|---|---|---|---|---|
| Config | `src/config.py` | `api/src/config.py` | FND | Variables de 01. Sin `load_dotenv` bajo pytest. |
| Base y sesión | `src/db/{base,session,models_registry}.py` | `api/src/db/` | FND | Engine perezoso; `options=-c timezone=UTC`; `prepare_threshold=None` con pooler. |
| Errores y logging | `src/core/{exceptions,logging_config}.py` | `api/src/core/{errors,logging}.py` | FND | Catálogo de 03 §7, `IntegrityError` → 409 con `code`, textos en español. |
| Fechas | `src/utils/date_utils.py` | `api/src/utils/date_utils.py` | FND | Solo las funciones de Caracas, más `caracas_day_bounds_utc(d) -> (inicio, inicioSiguiente)` naive UTC y semiabierto: **todo filtro por día usa esta función**. |
| Rate limit | `src/api/limiter.py` | `api/src/api/limiter.py` | FND | Clave = cabecera **`X-Real-IP`** (la pone el edge de Railway), con respaldo `client.host`. **Nunca** el primer `X-Forwarded-For`. Límite por teléfono dentro del handler de login. |
| JWT y hash | `src/api/auth/{service,utils,deps}.py` (patrón) | `api/src/domain/auth/` | FND | Multi-rol, refresh con gracia (01), PyJWT. |
| Alembic | `alembic/env.py`, `alembic.ini`, `script.py.mako` | `api/` | FND | URL: la fijada por quien llama > `DATABASE_URL_DIRECT` > `DATABASE_URL`. `railway.toml` **nuevo** (Railpack). |
| Tasa | `src/domain/exchange_rates/{db_models,repository,fetcher}.py` | `api/src/domain/exchange_rates/` | FND | El fetcher **solo acepta JSON** de DolarAPI oficial con valor numérico > 0 y guarda `fechaActualizacion` en metadata. `sync_daily_rate` **inserta la fila BCV de hoy solo si no existe** (nunca la actualiza; las correcciones se hacen con MANUAL). Lectura `rate_for(d)` de 03 §0. |
| Métodos de pago y cuentas | `src/domain/payment_methods/*`, `src/api/payment_methods.py` | `api/src/domain/payment_methods/` | FND (modelo) · B3 | `bank_accounts.cashAccountId`; la vista pública devuelve todas las cuentas activas con `id`; sin borrado: `PATCH {isActive:false}`. |
| Pagos | `src/domain/payments/{db_models,constants,repository}.py` | `api/src/domain/payments/` | FND (modelo) · B3 | Base de estados de OG + **código nuevo**: referencia, `paidOn`, método, cuenta, tomar, revertir, comprobante, idempotencia por cliente + `requestHash`. Sin borrado físico. |
| Cuentas del negocio | `src/domain/wallets/*` | `api/src/domain/cash_accounts/` | FND (modelo) · B3 | Montos con signo; `seq`. |
| Ledger | `src/services/ledger.py` (patrones) | `api/src/services/ledger.py` | B3 | Métodos nuevos de 03 §3; sin bóvedas; si la moneda no coincide → error. |
| Auditoría | `src/domain/audit/{db_models,service}.py` | `api/src/domain/audit/` | FND · B1 | `log_event` y `json_safe_payload`. Repositorio **reescrito**: cursor por `(createdAt, id)` y filtro de actor con JOIN a `users`. |
| Configuración | `src/domain/settings/config_service.py` (idea) | `api/src/domain/settings/` | FND · B1 | `app_settings` por secciones (02); el commit lo hace quien llama. |
| Cierre diario + PDF | `src/domain/closures/{service,pdf_builder,repository,db_models,models}.py`, `src/api/closings.py` | `api/src/domain/closures/` | B3 | Métricas en SQL con `caracas_day_bounds_utc`, sin commit interno, cuentas VES en su moneda. PDF con `reportlab`. |
| Jobs | patrón de envoltorio de jobs | `api/src/jobs/runner.py` | FND | Reescrito sobre APScheduler (03 §3.10). |
| Dashboard | `src/api/dashboard/*` (estructura) | `api/src/domain/dashboard/` | B3 | 03 §6. |
| Export | — | `api/v1/export.py` | B3 | **Reescrito:** `kind ∈ {payments, receivables, orders}`, solo CSV, rango con `caracas_day_bounds_utc` sobre `approvedAt`/`issuedAt`/`createdAt`, streaming por lotes, celdas que empiezan con `= + - @` con prefijo `'`. |

`api/requirements.txt` (todas con `==`, versiones de OG cuando existan):
- **Servidor y datos:** fastapi, starlette, uvicorn, SQLAlchemy, psycopg[binary], alembic, pydantic, pydantic-settings, python-dotenv.
- **Infraestructura de la API:** slowapi, limits, httpx, bcrypt, cuid2, APScheduler, reportlab, python-multipart, tzdata, Pillow.
- **Integraciones:** PyJWT, boto3, firebase-admin, pywebpush.
- **Pruebas:** pytest, pytest-asyncio, hypothesis.

## Mapa — Web (`OG/apps/web/`)
| Necesidad | Origen | Destino | Bloque | Cómo |
|---|---|---|---|---|
| Base Next 16 | `package.json`, `next.config.ts`, `tsconfig.json`, `tsconfig.build.json`, `eslint.config.*`, `postcss.config.*`, `vitest.config.ts`, `vitest.setup.ts`, `src/test/utils.tsx`, `AGENTS.md` | `web/` | DSN | `next`, `react` y `react-dom` en versión **exacta**. DSN genera y commitea `web/package-lock.json` (en OG el lock es del workspace raíz). `engines` / `.nvmrc` = Node 22. |
| Login | `src/app/login/*` (solo el layout visual), `src/proxy.ts` (patrón) | `web/src/…` | DSN | `LoginForm` reescrito con `useActionState(login)` y campo teléfono. `actions.ts` lee `accessToken`, `refreshToken` y `expiresIn` y guarda **dos cookies httpOnly**. Rutas `api/auth/{refresh,token,logout}` nuevas (01). |
| Cliente API | `src/lib/{api,client-api,format,utils}.ts` | `web/src/lib/` | DSN | De `api.ts` solo el `apiFetch` base (sin fetchers de préstamos ni bóvedas). Se preservan `detail` y `code`; cursor. |
| UI kit | `src/components/ui/*`, `src/components/page-title.tsx`, `src/components/data-section.tsx` | `web/src/components/ui/` | DSN | Re-vestidos con tokens; `DataTable` con `cursor`/`onLoadMore`. No se copian `lib/export-utils`, `hooks/*` ni `types/*`: los tipos salen de `api-types.ts` y el export es del servidor. |
| Sidebar | `src/components/layout/Sidebar.tsx` | `web/src/components/layout/` | DSN → W1 | |
| Métodos y cuentas | `src/components/settings/{PaymentMethodsTab,BankAccountsTab,PaymentMethodForm,BankAccountForm}.tsx` | `web/src/components/admin/settings/` | W1 | camelCase; “eliminar” = `PATCH {isActive:false}`; orden = `PATCH {displayOrder}`; agregar `cashAccountId`; vista previa = cómo lo verá el cliente en la app; sin textos de otros canales. |
| Pagos | `src/app/(dashboard)/payments/{page,[id]}` (estructura) | `web/src/app/(admin)/admin/pagos/*` | W1 | Acciones solo de 08: Tomar, Aprobar, Rechazar, Revertir. El abono manual vive en la ficha del cliente. |
| Cuentas, cierres, auditoría | `src/app/(dashboard)/{wallets,cierres,auditoria}/*` | `web/src/app/(admin)/admin/…` | W1 | camelCase, cursor; solo lo que existe en 08. |

## Skills y agentes
| Origen | Destino | Estado |
|---|---|---|
| `OG/.agents/skills/impeccable` + `OG/.claude/agents/impeccable-*` | `.claude/skills/impeccable`, `.claude/agents/` | Copiado ✅ |
| Skills de dominio de OG (contabilidad, migraciones, tests, cambios quirúrgicos, jobs, panel web) | `.claude/skills/<x>-panaderia` | FND, saneadas y con las reglas de esta panadería |
| `OG/.claude/agents/auditor-contable.md` | `.claude/agents/auditor-contable.md` | FND (invariantes I-1…I-9) |
