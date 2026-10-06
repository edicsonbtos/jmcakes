# 04 — Fases y enjambre de 10 agentes

El trabajo se ejecuta con **10 agentes** en **3 fases**. Una sesión **orquestadora** coordina:
- lanza los agentes, cada uno en su propio *git worktree* y rama local;
- integra sus ramas en la rama de integración (`claude/happy-johnson-24innr`), corre las compuertas de [07-pruebas](07-pruebas.md) y publica;
- maneja la infraestructura: Neon, Railway y GitHub Actions.

```
FASE 0 · Fundación (paralelo, 2)        FASE 1 · Construcción (paralelo, 6)              FASE 2 · Integración (2)
┌───────────────────────────────┐       ┌─────────────────────────────────────────┐      ┌──────────────────────────────┐
│ FND  API base + BD + contrato │──┐    │ B1  API catálogo·clientes·config        │      │ Q1  Integración backend+web, │
│      completo + auth + CI api │  │    │ B2  API pedidos·cocina·delivery·SSE·push│      │     E2E, deploy Railway,     │
└───────────────────────────────┘  ├──▶ │ B3  API dinero·pagos·tasa·dashboard     │──G2─▶│     auditoría contable y     │
┌───────────────────────────────┐  │    │ W1  Web panel admin                     │      │     seguridad                │
│ DSN  Impeccable: DESIGN.md,   │──┘    │ W2  Web cocina                          │      ├──────────────────────────────┤
│      tokens, web base + UI kit│  G1   │ M   Android (cliente + delivery)        │      │ Q2  Android en CI + QA apps +│
│      + spec visual Android    │       └─────────────────────────────────────────┘      │     auditoría Impeccable     │
└───────────────────────────────┘                                                         └──────────────────────────────┘
```

## Los 10 agentes

| # | ID | Agente | Fase | Depende de | Carpetas propias (escritura) | Ficha |
|---|---|---|---|---|---|---|
| 1 | FND | Fundación API, BD y contrato | 0 | plan | `api/**` (todo al inicio), `contracts/`, `spec/` (solo lectura), `.github/workflows/{api,contract}.yml`, `.claude/skills/*-panaderia`, `.claude/agents/auditor-contable.md`, `CLAUDE.md` §Comandos | [FND](bloques/FND-fundacion-api.md) |
| 2 | DSN | Sistema de diseño (Impeccable) y base web | 0 | `PRODUCT.md` | `DESIGN.md`, `docs/design/**`, `web/**` (todo al inicio), `.github/workflows/web.yml` | [DSN](bloques/DSN-diseno-y-web-base.md) |
| 3 | B1 | API catálogo, clientes, usuarios, config, archivos | 1 | FND | `api/src/domain/{catalog,customers,users,settings,files}/`, `api/src/api/v1/{catalog,customers,users,settings,files,audit}.py`, `api/tests/b1_*` | [B1](bloques/B1-api-catalogo-clientes.md) |
| 4 | B2 | API pedidos, agenda, cocina, delivery, eventos, push | 1 | FND | `api/src/domain/{orders,kitchen,delivery}/`, `api/src/services/{events,push}.py`, `api/src/api/v1/{orders,kitchen,delivery,events}.py`, `api/src/jobs/unpaid_auto_cancel.py`, `api/tests/b2_*` | [B2](bloques/B2-api-pedidos-cocina-delivery.md) |
| 5 | B3 | API dinero: pagos, billetera, CxC, cuentas, tasa, dashboard, cierres | 1 | FND | `api/src/services/{ledger,money}.py`, `api/src/domain/{payments,payment_methods,wallet,receivables,cash_accounts,exchange_rates,finance,dashboard,closures}/`, `api/src/api/v1/{payments,wallet,admin_money,rates,dashboard,closures,export}.py`, `api/src/jobs/{bcv_sync,daily_closing}.py`, `api/tests/b3_*` | [B3](bloques/B3-api-dinero.md) |
| 6 | W1 | Web panel del administrador | 1 | DSN (+ mock de FND) | `web/src/app/(admin)/**`, `web/src/components/admin/**`, `web/e2e/admin*` | [W1](bloques/W1-web-admin.md) |
| 7 | W2 | Web de producción (cocina) | 1 | DSN (+ mock de FND) | `web/src/app/(cocina)/**`, `web/src/components/cocina/**`, `web/e2e/cocina*` | [W2](bloques/W2-web-cocina.md) |
| 8 | M | Android: app cliente + app delivery | 1 | DSN (spec visual) + contrato de FND | `android/**`, `.github/workflows/android.yml` | [M](bloques/M-android.md) |
| 9 | Q1 | Integración backend+web, E2E, staging, auditorías | 2 | todo lo anterior integrado | `e2e/**`, `.github/workflows/e2e.yml`, correcciones transversales (commits pequeños) | [Q1](bloques/Q1-integracion.md) |
| 10 | Q2 | Android en CI, QA de apps, auditoría de diseño | 2 | Q1 (staging) | `android/**` (correcciones), `docs/handoffs/assets/**`, correcciones de UI web vía Impeccable | [Q2](bloques/Q2-android-y-diseno.md) |

## Por qué funciona en paralelo

1. **El contrato está completo antes de la Fase 1.** FND declara todos los endpoints de [08](08-api-endpoints.md), con esquemas y stubs `501`, y exporta `contracts/openapi.json`. W1, W2 y M construyen contra el mock (Prism) sin esperar a B1–B3.
2. **Las tablas también.** FND crea **todo** el esquema de [02](02-modelo-de-datos.md) en la migración inicial. B1–B3 no necesitan migraciones; si una es imprescindible, el protocolo §4 evita choques.
3. **Interfaces internas con stubs** ([08](08-api-endpoints.md) §Interfaces): B2 llama a `MoneyService` y B3 a `OrdersService` sin esperarse.
4. **Routers ya registrados.** FND deja `main.py` con todos los routers incluidos; nadie más toca `main.py` ni `models_registry.py`.
5. **Carpetas disjuntas** por agente (tabla de arriba) → merges sin conflictos.
6. **Diseño antes que pantallas.** DSN entrega tokens, componentes y layouts; W1 y W2 solo componen pantallas con ellos.

## Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| Android no compila en el contenedor (sin SDK; `dl.google.com` bloqueado) | M escribe código siguiendo patrones estándar y pruebas JVM. El orquestador publica y GitHub Actions compila. Q2 itera sobre los logs de CI hasta verde. Si Q2 logra armar un SDK mínimo desde `maven.google.com`, compila local. |
| Neon no es accesible por 5432 desde el contenedor | Las pruebas usan Postgres 16 local. Las migraciones en Neon las aplica Railway (`preDeployCommand`). Las verificaciones de esquema van por el MCP de Neon. |
| Divergencia entre implementación y reglas de dinero | `spec/` es la referencia. B3 porta los escenarios. Q1 los corre por HTTP. Auditor contable obligatorio. |
| Merge de 6 ramas | Carpetas disjuntas. El contrato se regenera tras integrar. Si hay varias cabezas de Alembic, se agrega una revisión de merge. |
| Agente que se sale de su alcance | La ficha lista lo que **no** debe tocar. El orquestador revisa el `git diff --stat` por carpeta antes de integrar y rechaza cambios fuera de alcance. |

## Duración estimada
- Fase 0: ~1 sesión larga por agente.
- Fase 1: ~1–2 por agente.
- Fase 2: ~1 por agente, más ciclos de CI de Android.
