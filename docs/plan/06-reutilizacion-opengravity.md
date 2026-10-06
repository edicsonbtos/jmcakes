# 06 — Reutilización de OpenGravity (v2.1, verificada en el código)

OpenGravity está clonado en **`/home/user/opengraviti`** (abreviado `OG/`). Es un sistema de préstamos en producción. La auditoría 1 revisó cada archivo citado aquí.
- **Copiar y adaptar** donde OpenGravity ya lo resuelve bien.
- **No copiar** sus defectos conocidos.
- Lo de pagos que la panadería necesita (referencia, método, cuenta, tomar, revertir, comprobante en bucket) es **código nuevo** sobre su base.

## Reglas para copiar (el repo `jmcakes` es PÚBLICO y OpenGravity es privado)
1. Adaptar **mínimamente**: renombrar dominios y quitar Telegram, préstamos, bóvedas, cuotas, KYC y encriptación PII. Primera línea del archivo: `# Adaptado de OpenGravity: <ruta>`.
2. **Sanear al copiar.** Eliminar:
   - comentarios que citen incidentes, IDs de hallazgos (`N-002`, `C-005`, `BUG-…`), montos o fechas de producción;
   - nombres de personas o clientes;
   - nombres de proyectos u organizaciones de Neon/Railway de OpenGravity.

   Las pruebas se renombran por comportamiento: no se copian archivos como `test_carla_*` ni `test_ln_*`.
3. Nunca copiar `.env`, secretos, datos, `v1-legacy/`, `scratch/`, backups ni `graphify-out/`.
4. Las pruebas de OpenGravity que cubren código copiado se copian adaptadas (sobre Postgres, no SQLite).
5. En CI corre `gitleaks` sobre todo el repo.

## Mapa — API
| Necesidad | Origen en `OG/apps/bot/` | Destino | Bloque | Adaptación obligatoria |
|---|---|---|---|---|
| Config | `src/config.py` | `api/src/config.py` | FND | Sin Telegram, sin ADMIN_EMAIL ni BCV_SOURCE_URL fijo; variables de 01. |
| Base y sesión | `src/db/base.py`, `src/db/session.py`, `src/db/models_registry.py` | `api/src/db/` | FND | **Sin** `pool.py` ni `types.py` (dependen de PTB y de encriptación), sin rama SQLite. `prepare_threshold=None` con pooler. |
| Errores | `src/core/exceptions.py` | `api/src/core/errors.py` | FND | Reescribir los handlers: `IntegrityError` → 409 + `code` por restricción; `OperationalError` → 503; textos en español; sobre `{detail, code, meta}`. |
| Logging | `src/core/logging_config.py` | `api/src/core/logging.py` | FND | Tal cual. |
| Fechas | `src/utils/date_utils.py` | `api/src/utils/date_utils.py` | FND | Tal cual (ya trae `start/end_of_day_caracas`). Agregar `combine_caracas(date, time)`. |
| Rate limit | `src/api/limiter.py` | `api/src/api/limiter.py` | FND | `key_func` con el primer `X-Forwarded-For`; login por IP + teléfono. |
| JWT y hash | `src/api/auth/{service,utils,deps}.py` | `api/src/domain/auth/` | FND | Multi-rol, refresh rotativo, `require_role`. Sin `ADMIN_EMAIL`. |
| Alembic | `alembic/env.py`, `alembic.ini`, `alembic/script.py.mako`, `railway.toml` | `api/` | FND | `env.py` usa `models_registry` y `DATABASE_URL_DIRECT`. **`nixpacks.toml` se escribe nuevo** (no existe en `apps/bot`). `startCommand` y `numReplicas` según 01. |
| Fixtures | `tests/conftest.py` | `api/tests/conftest.py` | FND | **Solo la idea** de `db_session` con savepoint. **No** copiar el engine SQLite, `_create_tables`/`create_all`, `event_loop` ni el TRUNCATE global (diseño en la ficha de FND). |
| Tasa: modelo, repositorio, fetcher | `src/domain/exchange_rates/{db_models,repository,fetcher}.py` | `api/src/domain/exchange_rates/` | FND | Fetcher de DolarAPI oficial. **Lógica de lectura reescrita:** `rate_for(d)` de 03 §0, solo lectura y sin commit. `sync_daily_rate()` separado, con su propia sesión. **Sin** caché por instancia ni el respaldo “manual más vieja gana”. |
| Métodos de pago y cuentas | `src/domain/payment_methods/*`, `src/api/payment_methods.py` | `api/src/domain/payment_methods/`, `api/v1/payment_methods.py` | FND (modelo) · B3 | `bank_accounts.cashAccountId`. El router público devuelve **todas** las cuentas activas **con `id`** (OpenGravity no lo hacía). |
| Pagos (base) | `src/domain/payments/{db_models,constants,repository}.py`, partes de `service.py` (`register_payment`, `reject_payment`) | `api/src/domain/payments/` | FND (modelo) · B3 | **Código nuevo:** `reference`, `paidOn`, método, cuenta, `take`, `reverse` y comprobante en bucket. Idempotencia por cliente + `requestHash`, con relectura ante `IntegrityError`. **NO copiar:** el respaldo `Decimal("1.0")` de tasa, la reconversión de `ledger.record_payment_applied`, `delete_payment` ni su endpoint. |
| Cuentas del negocio | `src/domain/wallets/*` | `api/src/domain/cash_accounts/` | FND (modelo) · B3 | Renombrar. **`amount` con signo** en las transacciones. |
| Ledger | `src/services/ledger.py` (patrones `_add_wallet_entry`, `balance_after` y metadata USD/VES) | `api/src/services/ledger.py` | B3 | Solo los patrones; los métodos son nuevos (03 §3). El signo va en el monto. Sin bóvedas. Si la moneda no coincide → error, nunca reconvertir. |
| Auditoría | `src/domain/audit/*`, `src/utils/audit_logger.py` | `api/src/domain/audit/` | FND | Tal cual, saneado. |
| Configuración | `src/domain/settings/config_service.py` (idea) | `api/src/domain/settings/` | FND (modelo y servicio) · B1 (endpoints) | Tabla `app_settings` por secciones (02); el **commit lo hace quien llama**. |
| Cierre diario y PDF | `src/domain/closures/{service,pdf_builder,repository,db_models,models}.py`, `src/api/closings.py` | `api/src/domain/closures/`, `api/v1/closures.py` | B3 | **No** `src/jobs/daily_closing.py` (es otro cierre, de bóvedas) ni `mailer.py`. Métricas por `approvedAt`/`confirmedAt` **en SQL** con los límites del día de Caracas, nunca `.date()` sobre UTC. Sin commit interno. Cuentas VES en su moneda + USD. |
| Jobs | patrón `_safe_job` de `src/bot/app.py` | `api/src/jobs/runner.py` | FND | **Reescrito:** `safe_job(name, fn)` sobre APScheduler (TZ Caracas), sin `context` de PTB. |
| Dashboard | `src/api/dashboard/*` (estructura) | `api/src/domain/dashboard/` | B3 | Métricas de 03 §6. |
| Export CSV | `src/api/export.py` | `api/v1/export.py` | B3 | |

## Mapa — Web (`OG/apps/web/`)
| Necesidad | Origen | Destino | Bloque | Adaptación |
|---|---|---|---|---|
| Base Next 16 | `package.json`, `next.config.*`, `tsconfig.json`, `eslint.config.*`, `postcss.config.*`, `vitest.config.*`, `AGENTS.md` | `web/` | DSN | Mismas versiones; más `openapi-typescript`, `@playwright/test`, testing-library, `clsx`, `lucide-react`, `recharts` (todas instaladas por DSN). |
| Auth | `src/proxy.ts`, `src/lib/actions.ts`, `src/app/login/*`, `src/app/api/auth/{me,logout}` | `web/src/…` | DSN | **Refresh** con cookies httpOnly (01 §Autenticación). **No** copiar `api/auth/set-token`. Sin `console.log`. Roles por ruta. |
| Cliente API | `src/lib/{api,client-api,format,utils}.ts` | `web/src/lib/` | DSN | Base `NEXT_PUBLIC_API_URL` (`…/api/v1`), JSON camelCase, se preserva `detail`/`code`, cursor. |
| UI kit | `src/components/ui/*` | `web/src/components/ui/` | DSN | Re-vestido con los tokens. `DataTable` recibe además `cursor`/`onLoadMore` (aditivo). |
| Sidebar | `src/components/layout/Sidebar.tsx` | `web/src/components/layout/` | DSN (base) → **W1 (dueño en la Fase 1)** | |
| CRUD de métodos y cuentas | `src/components/settings/{PaymentMethodsTab,BankAccountsTab,PaymentMethodForm,BankAccountForm,MethodPreview}.tsx` | `web/src/components/admin/settings/` | W1 | Ya están completos en OpenGravity: adaptar a camelCase y agregar `cashAccountId`. |
| Pagos | `src/app/(dashboard)/payments/*` | `web/src/app/(admin)/admin/pagos/*` | W1 | La bandeja es casi nueva: comprobante real (bucket), tomar, revertir, corrección de tasa, cursor. |
| Cuentas | `src/app/(dashboard)/wallets/*` | `web/src/app/(admin)/admin/cuentas/*` | W1 | **Sin** `components/vaults`, `TransferModal` ni `useCountUp`. |
| Cierres, auditoría, exportar | `src/app/(dashboard)/{cierres,auditoria,exportar}/*` | `web/src/app/(admin)/admin/…` | W1 | camelCase y cursor. |

## Skills y agentes
| Origen | Destino | Quién |
|---|---|---|
| `OG/.agents/skills/impeccable` + `OG/.claude/agents/impeccable-*` | `.claude/skills/impeccable`, `.claude/agents/` | Copiado ✅ |
| `contabilidad-`, `migraciones-esquema-`, `tests-bot-`, `cambios-quirurgicos-`, `jobs-programados-`, `panel-web-opengravity` | `.claude/skills/<x>-panaderia` | FND (saneadas, con las reglas de esta panadería) |
| `OG/.claude/agents/auditor-contable.md` | `.claude/agents/auditor-contable.md` | FND (invariantes I-1…I-9 de 02) |

## Qué NO se reutiliza
Telegram, préstamos, cuotas, mora, interés, pronto pago, bóvedas, score, KYC, encriptación PII, Prisma, `v1-legacy`, `db/pool.py`, `db/types.py`, `mailer.py`, `jobs/daily_closing.py`, `delete_payment` y `api/auth/set-token`.
