# Tablero de estado

Cada agente actualiza **su fila** al empezar (`EN CURSO`) y al terminar (`LISTO PARA REVISIÓN`). El humano la pasa a `FUSIONADO` al hacer merge.

Estados: `PENDIENTE` · `BLOQUEADO` · `EN CURSO` · `LISTO PARA REVISIÓN` · `FUSIONADO`

| ID | Bloque | Fase | Estado | Rama / PR | Handoff | Notas |
|---|---|---|---|---|---|---|
| — | Plan y cuestionario | — | LISTO PARA REVISIÓN | `claude/happy-johnson-24innr` | — | Responder `docs/CUESTIONARIO.md` |
| F0 | Fundación y contrato | 0 | BLOQUEADO | — | — | Espera respuestas C-1, C-3, C-4, C-5, C-6, C-27 |
| B1 | API catálogo y clientes | 1 | PENDIENTE | — | — | Requiere F0 |
| B2 | API pedidos, cocina, delivery | 1 | PENDIENTE | — | — | Requiere F0 |
| B3 | API finanzas y dashboard | 1 | PENDIENTE | — | — | Requiere F0 |
| W1 | Web administrador | 2 | PENDIENTE | — | — | Requiere F0 (mock) |
| W2 | Web cocina | 2 | PENDIENTE | — | — | Requiere F0 (mock) |
| M1 | Android cliente | 2 | PENDIENTE | — | — | Requiere F0 (mock) |
| M2 | Android delivery | 2 | PENDIENTE | — | — | Requiere F0 (mock) |
| Q1 | Integración y QA | 3 | PENDIENTE | — | — | Requiere todo lo anterior |
| L1 | Lanzamiento | 4 | PENDIENTE | — | — | Requiere Q1 |
