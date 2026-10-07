# 04 — Fases y enjambre de 10 agentes (v2.1)

Una sesión **orquestadora** coordina el trabajo:
- lanza los agentes, cada uno en su propio *git worktree*;
- integra sus ramas en `claude/happy-johnson-24innr`, corre las compuertas de [07](07-pruebas.md) y publica;
- es **la única** que toca infraestructura (Neon, Railway, GitHub Actions) y `docs/plan/STATUS.md`.

```
FASE 0 (paralelo, 2)          G1     FASE 1 (paralelo, 6)                         G2     FASE 2
FND  API base + contrato ─┐          B1  catálogo · clientes · archivos · config ─┐      Q1  integración, E2E, runbook staging,
DSN  Impeccable + web base┴─▶ int ─▶ B2  pedidos · agenda · cocina · delivery · SSE├─▶ int ─▶   auditorías (backend + web)
                                     B3  dinero · pagos · tasa · dashboard · cierres│      Q2  Android verde en CI, QA apps,
                                     W1  web admin                                  │          auditoría Impeccable
                                     W2  web cocina                                 │
                                     M   Android (cliente + delivery) ──(entrega temprana: el orquestador publica y CI compila)
```

## G0.5 — Dirección visual (orquestador + dueño, antes de lanzar DSN)
Impeccable exige que el **dueño** elija la dirección visual. Un agente desatendido no puede hacerlo. Pasos del orquestador:
1. Ejecuta `impeccable context` y hace con el dueño la ronda de preguntas de `new-work` §2, con la herramienta de preguntas estructuradas.
2. Corre `concept-seed --scope direction` y le presenta las opciones al dueño (con re-roll si lo pide).
3. Fija `.impeccable/config.json` = `{"buildPath":"code"}`: el flujo con comps necesita un navegador que el contenedor no tiene.
4. Registra el contrato de dirección y el *seed key* con `impeccable surface-brief write` para `web/src/app/(admin)`, `web/src/app/(cocina)`, `android/app-cliente` y `android/app-delivery`.
5. Para W1, W2 y M, en G1, corre `concept-seed --scope surface` con el dueño. Si el dueño no está disponible, el agente construye la primera estructura de la tirada y lo deja registrado en el brief para revisión.

## Los 10 agentes y sus carpetas propias
| # | ID | Fase | Escribe en (además de `docs/handoffs/<ID>.md`) | Ficha |
|---|---|---|---|---|
| 1 | FND | 0 | `api/**` (todo al inicio), `contracts/`, `scripts/dev-setup.sh`, `spec/requirements.txt`, `.github/workflows/{api,contract,secrets}.yml`, `.claude/skills/*-panaderia/`, `.claude/agents/auditor-contable.md`, `CLAUDE.md` §Comandos | [FND](bloques/FND-fundacion-api.md) |
| 2 | DSN | 0 | `DESIGN.md`, `docs/design/**`, `web/**` (todo al inicio), `.github/workflows/web.yml` | [DSN](bloques/DSN-diseno-y-web-base.md) |
| 3 | B1 | 1 | `api/src/domain/{catalog,files,customers,users,settings,audit}/` (excepto `db_models.py` e `interface.py`; sin cambiar las firmas de `SettingsService` ni de `AuditService`), `api/src/api/v1/{catalog,files,profile,customers,users,settings,audit}.py`, `api/tests/b1/**`, `api/alembic/versions/*_b1_*.py` | [B1](bloques/B1-api-catalogo-clientes.md) |
| 4 | B2 | 1 | `api/src/domain/{orders,kitchen,delivery}/` (ídem), `api/src/services/{events,push}.py`, `api/src/api/v1/{orders,kitchen,delivery,events}.py`, `api/src/jobs/unpaid_auto_cancel.py`, `api/tests/b2/**`, `api/alembic/versions/*_b2_*.py` | [B2](bloques/B2-api-pedidos-cocina-delivery.md) |
| 5 | B3 | 1 | `api/src/services/{ledger,money}.py`, `api/src/domain/{payments,payment_methods,wallet,receivables,cash_accounts,finance,exchange_rates,dashboard,closures}/` (ídem), `api/src/api/v1/{payments,payment_methods,wallet,admin_money,cash_accounts,rates,dashboard,closures,export}.py`, `api/src/jobs/{bcv_sync,daily_closing}.py`, `api/tests/b3/**`, `api/alembic/versions/*_b3_*.py` | [B3](bloques/B3-api-dinero.md) |
| 6 | W1 | 1 | `web/src/app/(admin)/**`, `web/src/components/admin/**`, `web/src/components/layout/**`, `web/e2e/admin*`, `web/public/admin/**` | [W1](bloques/W1-web-admin.md) |
| 7 | W2 | 1 | `web/src/app/(cocina)/**`, `web/src/components/cocina/**`, `web/e2e/cocina*`, `web/public/cocina/**` | [W2](bloques/W2-web-cocina.md) |
| 8 | M | 1 | `android/**`, `.github/workflows/android.yml` | [M](bloques/M-android.md) |
| 9 | Q1 | 2 (worktree `block/Q1`) | `e2e/**`, `.github/workflows/e2e.yml`, `docs/handoffs/Q1-runbook-staging.md`, correcciones en `api/**` y `web/**` (commits pequeños y explicados) | [Q1](bloques/Q1-integracion.md) |
| 10 | Q2 | 2 (worktree `block/Q2`) | `android/**`, `.github/workflows/{android,release-android}.yml`. La auditoría Impeccable de la web se entrega como **lista de correcciones** que aplica Q1 o el orquestador | [Q2](bloques/Q2-android-y-diseno.md) |

## Por qué el paralelismo es seguro
1. **Contrato completo antes de la Fase 1:** FND declara todos los endpoints de [08](08-api-endpoints.md) con su archivo de router, ya registrado en `main.py`.
2. **Esquema completo:** todas las tablas de [02](02-modelo-de-datos.md) están en la migración inicial.
3. **Interfaces congeladas y fábricas con stubs** ([08](08-api-endpoints.md) §Interfaces). Nadie edita un archivo ajeno para conectar su implementación.
4. **Jobs registrados por FND** en `jobs/runner.py`, con funciones `run()` vacías que cada dueño completa.
5. **Entorno aislado por agente:** base de datos y puertos propios (05 §1).
6. **Web:**
   - DSN deja instaladas todas las dependencias y los sonidos (`web/public/sounds/`).
   - El orquestador genera `api-types.ts` antes de la Fase 1.
   - W1 y W2 no tocan `package.json` ni editan `src/lib`.
7. **Carpetas disjuntas** y `STATUS.md` solo del orquestador → merges sin conflictos.

## Infraestructura: quién hace qué
| Tarea | Responsable |
|---|---|
| Neon (proyecto `jmcakes`, ramas `main`/`staging`) | Orquestador ✅ (hecho) |
| Railway (proyecto `jmcakes`, entorno `staging`) | Orquestador ✅ (hecho) |
| Servicios api/web, dominios, variables, bucket y ruta del config file | Orquestador, con el runbook de Q1 |
| Conectar Railway al repo y aprobar despliegues | **El dueño** (GitHub App de Railway y `accept-deploy`) |
| Publicar la rama y leer CI (Actions, artifacts) | Orquestador |

## Riesgos y mitigación
| Riesgo | Mitigación |
|---|---|
| Android no compila en el contenedor | Módulos JVM puros probados en local. `android.yml` se dispara con `push` a la rama de integración y a `block/M` y `block/Q2` (`paths: android/**`), más `workflow_dispatch`. El orquestador publica `block/M` en cuanto M entrega, para que CI corra durante la Fase 1. Q2 itera sobre los logs. |
| Playwright no descarga navegadores | Las pruebas se escriben en local y corren en GitHub Actions; capturas como artifacts. |
| Neon inaccesible por 5432 | Postgres local para pruebas; Alembic y bootstrap por `preDeployCommand`; verificación por MCP. |
| Divergencia con las reglas de dinero | `spec/` como referencia, B3 portando sus escenarios, Q1 por HTTP y auditor contable. |
| Fuga de código privado de OpenGravity (repo público) | Reglas de saneo (06), `gitleaks`, revisión del orquestador. Recomendación al dueño: hacer privado `jmcakes`. |
| Límite de uso de la sesión | Workflows reanudables (`resumeFromRunId`). Cada agente deja commits y handoff; el orquestador retoma desde el último estado integrado. |
