# 06 — Reutilización de OpenGravity

OpenGravity (`edicsonbtos/OpenGraviti`, en el entorno de agentes clonado en **`/home/user/opengraviti`**) es un sistema de préstamos en producción, con dinero real. Su manejo de pagos, tasas, billeteras, auditoría, cierres y su panel ya están probados. **Regla: copiar y adaptar antes que escribir de cero.** Abreviatura: `OG/` = `/home/user/opengraviti/`.

## Reglas para copiar
1. Copia el archivo y adáptalo **mínimamente**: renombres de dominio (`borrower` → `customer`, `loan` → `order`) y quitar Telegram, préstamos, bóvedas y cuotas.
2. Deja una línea al inicio: `# Adaptado de OpenGravity: <ruta original>`.
3. **Nunca** copies `.env`, secretos, datos de clientes, `v1-legacy/`, `scratch/` ni backups.
4. Las pruebas de OpenGravity que cubren código copiado se copian y adaptan junto con él: son la red de seguridad que ya pagó sus bugs.
5. Lo que en OpenGravity es específico de préstamos (cuotas, interés, mora, bóvedas, score, pronto pago) **no se copia**.

## Mapa archivo por archivo

| Necesidad en la panadería | Copiar de `OG/apps/bot/…` | Destino | Bloque | Adaptación |
|---|---|---|---|---|
| Config | `src/config.py` | `api/src/config.py` | FND | Quitar Telegram/ADMIN_EMAIL; agregar JWT, FCM, bucket, CORS. |
| Base, sesión, registro de modelos | `src/db/base.py`, `session.py`, `pool.py`, `models_registry.py`, `types.py` | `api/src/db/` | FND | Registry con los dominios nuevos. Postgres en tests (no SQLite). |
| Errores y logging | `src/core/exceptions.py`, `logging_config.py` | `api/src/core/` | FND | `AppError` con `code` y `meta` (catálogo en 03 §7). |
| Fechas Caracas | `src/utils/date_utils.py` | `api/src/utils/date_utils.py` | FND | Tal cual (+ `end_of_day_caracas`, `combine_caracas`). |
| Rate limit | `src/api/limiter.py` | `api/src/api/limiter.py` | FND | Tal cual. |
| JWT y hash | `src/api/auth/service.py`, `utils.py`, `deps.py` | `api/src/domain/auth/` | FND | Multi-rol (`users.role`), refresh tokens, `require_role(...)`. |
| Alembic | `alembic/env.py`, `alembic.ini`, `railway.toml`, `nixpacks.toml` | `api/` | FND | Una migración inicial con **todas** las tablas de 02. |
| Fixtures de pruebas | `tests/conftest.py` | `api/tests/conftest.py` | FND | Postgres local/servicio CI; `db_session` con savepoint; fixture `money_setup` (cuentas del negocio + métodos de pago). |
| Tasa BCV | `src/domain/exchange_rates/*` (+ `tests/test_exchange_rates*.py`) | `api/src/domain/exchange_rates/` | FND (modelo) · B3 (endpoints, job) | Prioridad manual > BCV del día > DolarAPI > última conocida. **Sin cambios de lógica.** |
| Métodos de pago y cuentas bancarias | `src/domain/payment_methods/*`, `src/api/payment_methods.py` (incluye `public_router`) | `api/src/domain/payment_methods/` | FND (modelo) · B3 | `bank_accounts.cashAccountId`. El router público alimenta “datos para pagar” en la app. |
| Pagos: estados, idempotencia, aprobar/rechazar con `for_update` | `src/domain/payments/{db_models,constants,repository}.py`, `service.py` (solo esqueleto de `register_payment`, `reject_payment`, flujo de `apply_payment` sin cuotas) | `api/src/domain/payments/` | FND (modelo) · B3 | `apply_payment` → `approve_payment` según 03 §3.4 (billetera, no cuotas). |
| Cuentas del negocio | `src/domain/wallets/*` | `api/src/domain/cash_accounts/` | FND (modelo) · B3 | Renombre `wallets` → `cash_accounts`. |
| Ledger | `src/services/ledger.py` (`_add_wallet_entry`, patrón `balance_after`, conversión USD/VES) | `api/src/services/ledger.py` | B3 | Métodos nuevos: `charge_order`, `record_payment_approved`, `refund`, `settle_receivable`, `reverse_payment`, `adjust`. Sin bóvedas. |
| Auditoría | `src/domain/audit/*`, `src/utils/audit_logger.py` | `api/src/domain/audit/` | FND | Tal cual. |
| Settings con caché | `src/domain/settings/*` (`config_service.py`) | `api/src/domain/settings/` | FND (modelo) · B1 (endpoints) | Claves de 02. |
| Cierre diario + PDF | `src/domain/closures/*`, `src/jobs/daily_closing.py` | `api/src/domain/closures/` | B3 | Métricas de panadería (03 §6). |
| Jobs seguros | patrón `_safe_job` de `src/bot/app.py` | `api/src/jobs/runner.py` | FND | APScheduler en el lifespan de FastAPI. |
| Dashboard | `src/api/dashboard/*` | `api/src/domain/dashboard/` | B3 | Métricas nuevas, misma estructura. |
| Export CSV | `src/api/export.py` | `api/src/api/v1/export.py` | B3 | Pagos, CxC, pedidos. |

| Necesidad web | Copiar de `OG/apps/web/…` | Destino | Bloque | Adaptación |
|---|---|---|---|---|
| Next 16 base | `package.json`, `next.config.*`, `tsconfig.json`, `eslint.config.*`, `postcss.config.*`, `vitest.config.*`, `AGENTS.md` | `web/` | DSN | Mismas versiones (next 16.2.2, react 19.2.4, tailwind 4). |
| Auth | `src/proxy.ts`, `src/lib/actions.ts`, `src/app/login/*`, `src/app/api/auth/*` | `web/src/…` | DSN | Roles: `/admin` exige ADMIN y `/cocina` exige PRODUCTION o ADMIN. Login por teléfono. |
| Cliente API | `src/lib/api.ts`, `client-api.ts`, `format.ts`, `utils.ts` | `web/src/lib/` | DSN | Base `NEXT_PUBLIC_API_URL`; preservar `detail`; `fmtDate` Caracas; `fmtUsd`, `fmtBs`. |
| Componentes UI | `src/components/ui/*` (Button, Card, Badge, DataTable, Modal, Input, Select, Switch, Textarea, Timeline, MetricCard) | `web/src/components/ui/` | DSN | **Re-vestidos** con los tokens de DESIGN.md (Impeccable). Misma API de props. |
| Layout panel | `src/components/layout/Sidebar.tsx` | `web/src/components/layout/` | DSN | Menú del panel de la panadería. |
| Vistas de pagos | `src/app/(dashboard)/payments/*` | `web/src/app/(admin)/admin/pagos/*` | W1 | Bandeja de verificación con comprobante, aprobar, rechazar y revertir. |
| Cuentas y tasas | `src/app/(dashboard)/wallets/*`, `configuracion/*` | `web/src/app/(admin)/admin/{cuentas,configuracion}` | W1 | |
| Cierres, auditoría, exportar | `cierres/*`, `auditoria/*`, `exportar/*` | `web/src/app/(admin)/admin/…` | W1 | |
| Dashboard | `dashboard/*`, `components/dashboard/*` | `web/src/app/(admin)/admin/page.tsx` | W1 | Métricas de 03 §6. |

| Skills y agentes de `OG/.agents/skills` y `OG/.claude/agents` | Destino | Estado |
|---|---|---|
| `impeccable` (+ agentes `impeccable-*`) | `.claude/skills/impeccable`, `.claude/agents/` | Copiada (D-10). |
| `contabilidad-opengravity`, `migraciones-esquema-opengravity`, `tests-bot-opengravity`, `cambios-quirurgicos-opengravity`, `jobs-programados-opengravity`, `panel-web-opengravity` | `.claude/skills/<nombre>-panaderia` | FND las adapta: mismas reglas, rutas y nombres de la panadería. |
| `auditor-contable` (subagente) | `.claude/agents/auditor-contable.md` | FND lo adapta; **B3 y Q1 lo ejecutan** sobre todo cambio que mueva dinero. |

## Qué NO se reutiliza
Bot de Telegram, préstamos, cuotas, mora, interés, pronto pago, bóvedas, score, KYC, encriptación PII (la panadería no guarda datos sensibles más allá de cédula/RIF opcional), Prisma y `v1-legacy`.
