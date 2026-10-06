# 07 — Estrategia de pruebas y compuertas de calidad

## 1. El plan ya está probado: `spec/`

- `spec/money_model.py` es una implementación de referencia, en memoria, de los flujos de dinero de [03](03-flujos-de-negocio.md) §3: crear pedido (CASH/CREDIT), usar la billetera, reportar, aprobar, rechazar y revertir pagos, `settle`, cancelar, reducir, cargos y ajustes manuales, auto-cancelación.
- `spec/test_money_model.py` tiene **18 escenarios** y una **prueba de propiedades** (Hypothesis) que ejecuta miles de secuencias aleatorias y verifica las invariantes I-1…I-6 tras cada paso.
- Resultado al cerrar el plan:
  - `19 passed` (los 18 escenarios + la propiedad).
  - Corrida extendida de **3.000 secuencias × 60 operaciones**, sin violaciones.
  - Todas las ramas ejercitadas: límite de crédito, deuda vencida, referencia duplicada, reversos con y sin saldo, cancelaciones, reducciones y vencimientos.

Comando: `python -m pytest spec -q`. **Si la implementación real y el modelo discrepan, manda el modelo**, salvo que se demuestre un error en él; en ese caso se corrigen el modelo y el doc 03 en el mismo commit.

## 2. Escenarios de aceptación (los mismos en spec, en API y en E2E)

| ID | Escenario | Dónde se prueba |
|---|---|---|
| E1 | Contado con billetera suficiente → CONFIRMED sin admin, evento a cocina | spec · API (B3/B2) · E2E (Q1) |
| E2 | Contado con billetera parcial → AWAITING_PAYMENT, faltante en USD y Bs → reporte → aprobación → cocina → listo → motorizado → entregado | spec · API · E2E |
| E2b/c/d | Sobrepago a billetera · subpago deja menor faltante · tolerancia de redondeo Bs | spec · API |
| E3 | Crédito: límite, rechazo por límite, recarga FIFO, sobrante a favor | spec · API · E2E |
| E4 | Programado a +3 días: en cocina bajo “Programados” con la fecha en grande; el día que toca, en “Hoy” | API (B2) · E2E web (Q1) |
| E5 | Pago rechazado: sin dinero, la referencia se puede reutilizar | spec · API |
| E6 | Cancelación en cada estado; reembolso a billetera; cocina recibe `order.cancelled` | spec · API |
| E7 | Auto-cancelación de impagos, excepto si hay pago en revisión | spec · API (job) |
| E8 | Reverso de pago con y sin saldo (genera deuda) | spec · API |
| E9 | Idempotencia de pedido y de pago (misma llave = mismo recurso) | spec · API |
| E10 | Concurrencia: dos aprobaciones simultáneas del mismo cliente, y aprobar mientras el cliente crea un pedido → invariantes intactas | API (B3, Postgres real) |
| E11 | Día de Caracas: pedido a las 23:30 VET cuenta en el día correcto del dashboard y del cierre | API (B3) |
| E12 | Autorización: cada endpoint con cada rol; un cliente nunca ve datos de otro; cocina nunca recibe montos | API (FND crea el arnés, cada B lo llena) |

## 3. Pirámide por componente

| Componente | Herramientas | Mínimo exigido |
|---|---|---|
| API | pytest + pytest-asyncio (strict) + httpx `AsyncClient` + **Postgres 16 real** + Hypothesis | Unit de services; integración por router; invariantes después de cada prueba de dinero (`assert_money_invariants(session)` en `tests/helpers.py`, creado por FND); E10 con dos sesiones reales. |
| Contrato | `scripts/export_openapi.py` + verificación en CI de que `contracts/openapi.json` está al día (`--check`) | CI falla si el contrato cambió y no se regeneró. |
| Web | Vitest + Testing Library (componentes, formatos), **Playwright** (E2E contra la API local con seed) | Login por rol, verificación de pagos, cambio masivo de precios, cocina recibe un pedido por SSE. Capturas en `docs/handoffs/assets/`. |
| Diseño | `impeccable detect --json` sobre la UI cambiada + `$impeccable audit` | Cero hallazgos críticos; contraste AA. |
| Android | JUnit + Turbine (ViewModels), Robolectric + Compose UI tests (JVM), Roborazzi (capturas en JVM) | Compila en GitHub Actions (`assembleDebug`, `testDebugUnitTest`) para ambas apps; flujos de checkout CASH/CREDIT en tests de ViewModel con API falsa. |
| E2E de sistema | Script `e2e/run_scenarios.py`: levanta Postgres + API + seed y ejecuta E1–E9 por HTTP | Verde en CI (`e2e.yml`) y contra staging (solo lectura más un cliente de prueba). |

## 4. Compuertas (gates) por fase

| Gate | Cuándo | Condición para avanzar |
|---|---|---|
| G0 | Fin del plan | `spec` verde · plan auditado 2 veces. ✅ |
| G1 | Fin de Fase 0 (FND + DSN) | `pytest api` verde · `alembic upgrade head` aplica sobre Postgres vacío y `downgrade base` revierte · `contracts/openapi.json` con **todos** los endpoints de 03 (stubs con `501`) · `web` build + lint verdes · `PRODUCT.md` y `DESIGN.md` escritos · CI api/web verde en GitHub. |
| G2 | Fin de Fase 1 (7 agentes) | Cada rama: sus pruebas verdes y su handoff. Tras integrar: suite completa verde, `openapi.json` regenerado sin diferencias inesperadas, `alembic heads` = 1. |
| G3 | Fin de Fase 2 (Q1, Q2) | E2E E1–E12 verdes · Android compila en CI · staging desplegado (`/api/health` OK, migraciones aplicadas, login admin desde web staging) · auditoría contable y de seguridad sin hallazgos altos · `impeccable audit` sin críticos. |

## 5. Datos de prueba (seed)
`api/scripts/seed.py` (FND), idempotente:
- **Usuarios** (teléfonos ficticios `+58412000000x`, contraseñas desde variables de entorno, nunca en el repo): admin, producción, motorizado y 3 clientes:
  - CASH sin saldo;
  - CASH con $20 a favor;
  - CREDIT con límite $100.
- **Catálogo:** 3 categorías y 12 productos de panadería venezolana.
- **Cobros:** 2 métodos de pago (Pago móvil Bs, Zelle USD) con cuentas bancarias y sus cuentas del negocio.
- **Tasa:** tasa MANUAL de ejemplo.
