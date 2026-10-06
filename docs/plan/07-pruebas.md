# 07 — Estrategia de pruebas y compuertas (v2.1)

## 1. El plan está probado: `spec/`
- `spec/money_model.py` es la referencia ejecutable de 03 §1–§3. Incluye:
  - pedidos ASAP y programados, CASH y CREDIT, uso de la billetera;
  - reportar, aprobar, rechazar y revertir pagos; `settle`;
  - cancelar y reducir; bloquear; condonar y anular CxC; devoluciones y ajustes;
  - vencimientos con ventana mínima de pago;
  - catálogo `ERROR_CODES`.
- `spec/test_money_model.py` tiene **29 escenarios** más una **prueba de propiedades** (Hypothesis, 500 ejemplos en CI) con las invariantes I-1…I-9 tras cada paso. Otra prueba exige que todo código del modelo esté en el catálogo de 03 §7.
- Resultados al cerrar la auditoría 1:
  - `31 passed`.
  - Corrida extendida de **4.000 secuencias × 80 operaciones (320.000 operaciones)** sin violaciones, con todas las ramas ejercitadas: OPEN_DEBT, OVERDUE_DEBT, bloqueos, condonación, anulación, reducción a 0 y referencias duplicadas.
- Instalar y correr: `pip install -r spec/requirements.txt && python -m pytest spec -q`.
- **Si la API y el modelo discrepan, manda el modelo**, salvo que se pruebe un error en él. En ese caso se corrigen el modelo y 03 en el mismo commit.

## 2. Escenarios de aceptación
| ID | Escenario | spec | B2/B3 (services + HTTP propio) | Q1 (HTTP de punta a punta) |
|---|---|---|---|---|
| E1 | Contado con billetera suficiente → CONFIRMED sin admin | ✅ | B3 (services) | ✅ |
| E2 | Contado parcial → faltante USD/Bs → reporte → aprobación → cocina → listo → motorizado → entregado | ✅ | B3 (services) · B2 (transiciones) | ✅ |
| E2b/c/d | Sobrepago a billetera · subpago · tolerancia | ✅ | B3 | ✅ |
| E3 | Crédito: límite, recarga FIFO, sobrante, `paymentStatus` PAID | ✅ | B3 | ✅ |
| E4 | Programado a +3 días: “Programados” con fecha grande → “Hoy” el día que toca | — | B2 | ✅ (+ web) |
| E5 | Pago rechazado: sin dinero, referencia reutilizable, ventana mínima | ✅ | B3 | ✅ |
| E6 | Cancelación en cada estado y reembolso; `order.cancelled` | ✅ | B3 (dinero) · B2 (estados y evento) | ✅ |
| E7 | Auto-cancelación (excepto con pago en revisión; ventana mínima) | ✅ | B2 (job, `SKIP LOCKED`) | ✅ |
| E8 | Reverso con y sin saldo; referencia bloqueada; OPEN_DEBT | ✅ | B3 | ✅ |
| E9 | Idempotencia (misma llave = mismo recurso; otro contenido = 409) | ✅ | B2 · B3 | ✅ |
| E10 | Concurrencia: dos aprobaciones del mismo cliente · aprobar mientras se crea un pedido · reporte contra el job de vencimiento | — | B3 (`checkout` y `approve` en sesiones reales) · B2 (job) | ✅ |
| E11 | Día de Caracas: pago aprobado a las 22:30 VET cuenta en ese día (dashboard y cierre) | — | B3 | ✅ |
| E12 | Autorización por rol y propiedad; cocina y delivery sin dinero | — | FND (arnés) + cada B | ✅ |
| E13 | Bloqueo, condonar/anular, devolución de saldo, reducción | ✅ | B3 · B2 | ✅ |
| E14 | Tasa: `rate_for` (MANUAL > BCV > última ≤ d), RATE_UNAVAILABLE, pago con los Bs exactos mostrados → CONFIRMED | — | FND (`rate_for`) · B3 | ✅ |

**B3 no crea pedidos por HTTP** (los endpoints son de B2): usa `tests/b3_orders_helper.py`, que inserta `OrderDB` con los modelos congelados y llama a `MoneyService.checkout` / `on_order_cancelled`.

## 3. Por componente
| Componente | Herramientas | Exigido |
|---|---|---|
| API | pytest-asyncio (strict, loop de sesión), httpx `ASGITransport`, Postgres real con una base por agente, Hypothesis | `assert_money_invariants` (SQL de 02) tras cada prueba de dinero; fixture `committed_db` (TRUNCATE de su propia base) para E10 y `after_commit`; SSE probado a nivel de `EventBus` y generador (el stream infinito no se prueba con ASGITransport). |
| Contrato | `export_openapi.py --check`; Spectral (`casing: camel`) | CI rojo si el contrato no está regenerado. |
| Errores | Prueba: `core/errors.py` ⊇ `spec.ERROR_CODES` | |
| Web | Vitest + Testing Library (local) · **Playwright en GitHub Actions** (`web.yml`: job `e2e-web` contra Prism; `e2e.yml`: contra la API + Postgres) | Local: `npm run lint && npm test && npm run build && npx playwright test --list`. Las capturas se suben como artifact y el orquestador las baja a `docs/handoffs/assets/`. |
| Diseño | `sh .claude/skills/impeccable/scripts/impeccable detect --json <rutas>` | Sin críticos. |
| Android | Local: `gradle :core:network:test :core:data:test` (módulos JVM). CI: `./gradlew :app-cliente:assembleMockDebug :app-delivery:assembleMockDebug :app-cliente:testMockDebugUnitTest :app-delivery:testMockDebugUnitTest :core:network:test :core:data:test :core:designsystem:testDebugUnitTest` | Reportes `**/build/test-results/**` como artifact. En G3, más de 0 pruebas en `app-cliente`. |
| E2E de sistema | `e2e/run_scenarios.py` (recibe `DATABASE_URL`; solo arranca Postgres si no se le pasa) + uvicorn + seed | E1–E3 y E5–E14 por HTTP, más el stream SSE real. |
| Secretos | `gitleaks` (`secrets.yml`) | Sin hallazgos. |

## 4. Compuertas
| Gate | Responsable | Condición |
|---|---|---|
| **G0** fin del plan | orquestador | `spec` verde · 2 auditorías aplicadas · CLAUDE.md coherente con v2. |
| **G1** fin de Fase 0 | orquestador | FND: `pytest` verde; `alembic upgrade head` → `downgrade base` → `upgrade head` sobre una base aparte; `alembic check` sin diferencias; `contracts/openapi.json` con **todos los endpoints de 08** (contados); cada fábrica de 08 importable y probada; `bootstrap` y `seed` idempotentes. DSN: `DESIGN.md`, tokens y specs; `web` lint/test/build verdes. **Luego el orquestador:** integra FND y DSN, ejecuta `cd web && npm run gen:api` (commit de `web/src/lib/api-types.ts`), publica, verifica CI y recién entonces crea los worktrees de la Fase 1. |
| **G2** fin de Fase 1 (6 agentes) | orquestador | Cada rama con sus pruebas verdes y su handoff · `git diff --stat` dentro de sus carpetas · tras integrar: suite completa verde, `alembic heads` = 1, contrato regenerado, `api-types.ts` regenerado, CI verde (incluido `android.yml` si M ya entregó). |
| **G3** fin de Fase 2 | orquestador + Q1/Q2 | E2E E1–E14 verdes en CI · staging: `/api/health` OK, `get_database_tables` con las tablas de 02, `alembic_version` = head, login de admin en la web de staging · `android.yml` verde con pruebas > 0 · auditor contable y `/security-review` sin hallazgos altos · `impeccable detect`/`audit` sin críticos. |

## 5. Datos
- `api/scripts/bootstrap.py` es idempotente. Si hay `BOOTSTRAP_ADMIN_PHONE`/`PASSWORD` y no existe ningún ADMIN, lo crea. Si `SEED_DEMO=1`, ejecuta `seed.py`. Corre en el `preDeployCommand`.
- `api/scripts/seed.py` (demo, idempotente):
  - **Usuarios:** producción, motorizado y 3 clientes: CASH sin saldo, CASH con $20 a favor y CREDIT con límite $100. Teléfonos `+5841200000xx`; contraseña de `SEED_PASSWORD`.
  - **Catálogo:** 3 categorías y 12 productos.
  - **Cobros:** 2 métodos (Pago móvil Bs y Zelle USD) con sus cuentas bancarias y cuentas del negocio.
  - **Tasa:** BCV y MANUAL de hoy.
