# Tablero de estado

Estados: `PENDIENTE` · `EN CURSO` · `LISTO PARA INTEGRAR` · `INTEGRADO` · `BLOQUEADO`

| # | ID | Bloque | Fase | Estado | Rama | Handoff | Notas |
|---|---|---|---|---|---|---|---|
| — | PLAN | Plan v2 + spec + 2 auditorías | — | EN CURSO | `claude/happy-johnson-24innr` | — | Gate G0 |
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
