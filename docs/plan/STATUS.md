# Tablero de estado

Estados: `PENDIENTE` · `EN CURSO` · `LISTO PARA INTEGRAR` · `INTEGRADO` · `BLOQUEADO`

| # | ID | Bloque | Fase | Estado | Rama | Handoff | Notas |
|---|---|---|---|---|---|---|---|
| — | PLAN | Plan v2.5 + spec + auditorías 1, 2, 2b y 3 | — | LISTO (G0) | `claude/happy-johnson-24innr` | `docs/plan/AUDITORIAS.md` | 155 hallazgos aplicados; spec 41/41 |
| — | G0.5 | Dirección visual (Impeccable) con el dueño | — | EN CURSO | — | — | Ronda de preguntas hecha (cocina iluminada en tablet; evitar: frío como banco, infantil, lujo); falta elegir la dirección |
| — | **E1** | **Admin web + cuaderno de clientes** (ver 09) | E1 | **SIGUIENTE** | — | — | Agentes: FND-E1, DSN, B-E1a, B-E1b, W-E1, Q-E1 (ramas `block/<ID>`, 09 §E1 — Agentes). Inventario E1: 51 operaciones |
| 1 | FND | Fundación API, BD, contrato | 0 | PENDIENTE | `block/FND` | — | |
| 2 | DSN | Diseño Impeccable + base web | 0 | PENDIENTE | `block/DSN` | — | |
| 3 | B1 | API catálogo, clientes, config | 1 | PENDIENTE | `block/B1` | — | |
| 4 | B2 | API pedidos, cocina, delivery | 1 | PENDIENTE | `block/B2` | — | |
| 5 | B3 | API dinero | 1 | PENDIENTE | `block/B3` | — | |
| 6 | W1 | Web admin | 1 | PENDIENTE | `block/W1` | — | |
| 7 | W2 | Web cocina | 1 | PENDIENTE | `block/W2` | — | |
| 8 | M | Android cliente + delivery | 1 | PENDIENTE | `block/M` | — | |
| 9 | Q1 | Integración, E2E, staging | 2 | PENDIENTE | integración | — | |
| 10 | Q2 | Android CI + diseño | 2 | PENDIENTE | integración | — | |

## Infraestructura creada
| Recurso | Identificador |
|---|---|
| Neon proyecto `jmcakes` (org personal) | `square-poetry-91370020` · BD `panaderia` · ramas `main` y `staging` (`br-summer-fog-b7ywq8hr`) |
| Railway proyecto `jmcakes` | `dab8a4d1-b0ac-442a-afdb-c9e63d6ae36c` · entorno `staging` |
