# Tablero de estado

Estados: `PENDIENTE` · `EN CURSO` · `LISTO PARA INTEGRAR` · `INTEGRADO` · `BLOQUEADO`

| # | ID | Bloque | Fase | Estado | Rama | Handoff | Notas |
|---|---|---|---|---|---|---|---|
| — | PLAN | Plan v2.6 + spec + auditorías 1, 2, 2b, 3 y 3b | — | LISTO (G0) | `claude/happy-johnson-24innr` | `docs/plan/AUDITORIAS.md` | hallazgos aplicados; spec 58/58 |
| — | G0.5 | Dirección visual (Impeccable) con el dueño | — | LISTO (panel admin) | `claude/happy-johnson-24innr` | `.impeccable/surfaces/web-src-app-admin.md` | 2026-10-20: el dueño eligió la salida estándar con **Uber y Rappi** como vara de calidad (ronda degradada: el servicio de sorteo está bloqueado por la red). `buildPath: code`. Cocina y apps: su brief se hace en su etapa. |
| — | **E1** | **Admin web + cuaderno de clientes** (ver 09) | E1 | **EN CURSO** | `claude/happy-johnson-24innr` | — | G1-E1 ✅ (2026-10-21: local y CI api, contract, secrets y web en verde). Siguiente: E1.1 (B-E1a ∥ B-E1b ∥ W-E1). Inventario E1: 52 operaciones |
| E1.0 | FND-E1 | API base: esquema completo de 02, auth admin + change-password, contrato E1, seed | E1 | INTEGRADO | `block/FND-E1` | `docs/handoffs/FND-E1.md` | API 262 passed / 5 skipped; contrato al día (52); spec 58/58. Las 44 operaciones de B-E1a/B-E1b responden 501 hasta su bloque. Pendiente menor: login/refresh podrían devolver `expiresIn` y `user.mustChangePassword` (hoy la web usa el `exp` del JWT y `/auth/me`). |
| E1.0 | DSN | Sistema visual (estándar delivery, Uber/Rappi), base web, auth web, UI kit, DESIGN.md | E1 | INTEGRADO | `block/DSN` | `docs/handoffs/DSN.md` | web lint/typecheck/72 tests/build verdes; `api-types.ts` generado por el orquestador. Naranja de marca provisional `#C94C0A`. Revisión final de Impeccable en modo degradado (sin subagentes). |
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
