# Registro de auditorías del plan

El detalle de cada hallazgo (problema y corrección) se guarda **fuera de este repositorio público**, porque varios hallazgos describen código del proyecto privado del que se reutilizan piezas. Aquí queda solo la trazabilidad: qué ronda, cuántos hallazgos y su estado.

Cada hallazgo lo revisó el orquestador contra el modelo ejecutable (`spec/`) y contra los documentos del plan antes de aplicarlo.

## Auditoría 1 (2026-10-06)

Seis lentes: dinero, paralelismo, contrato, reutilización, pruebas/infra y producto (esta última se cortó por el límite de uso y pasó a la ronda 2b).

**69 hallazgos, todos aplicados.** Severidades: {'critica': 3, 'alta': 33, 'media': 25, 'baja': 8}

| ID | Severidad |
|---|---|
| M1 | critica |
| M2 | alta |
| M3 | alta |
| M4 | alta |
| M5 | alta |
| M6 | media |
| M7 | media |
| M8 | media |
| M9 | media |
| M10 | media |
| M11 | media |
| M12 | baja |
| SW-01 | critica |
| SW-02 | alta |
| SW-03 | alta |
| SW-04 | alta |
| SW-05 | alta |
| SW-06 | alta |
| SW-07 | alta |
| SW-08 | alta |
| SW-09 | alta |
| SW-10 | alta |
| SW-11 | media |
| SW-12 | media |
| SW-13 | media |
| SW-14 | media |
| SW-15 | media |
| SW-16 | baja |
| C1 | alta |
| C2 | alta |
| C3 | alta |
| C4 | alta |
| C5 | alta |
| C6 | media |
| C7 | media |
| C8 | media |
| C9 | media |
| C10 | media |
| C11 | media |
| C12 | media |
| C13 | baja |
| C14 | baja |
| C15 | baja |
| OG-01 | critica |
| OG-02 | alta |
| OG-03 | alta |
| OG-04 | alta |
| OG-05 | alta |
| OG-06 | alta |
| OG-07 | alta |
| OG-08 | alta |
| OG-09 | media |
| OG-10 | media |
| OG-11 | media |
| OG-12 | baja |
| INF-01 | alta |
| INF-02 | alta |
| INF-03 | alta |
| INF-04 | alta |
| INF-05 | alta |
| INF-06 | alta |
| INF-07 | alta |
| INF-08 | alta |
| INF-09 | media |
| INF-10 | media |
| INF-11 | media |
| INF-12 | media |
| INF-13 | baja |
| INF-14 | baja |

## Auditoría 2 (2026-10-07)

Lentes de dinero, paralelismo y contrato sobre el plan v2.1.

**32 hallazgos, todos aplicados.** Severidades: {'alta': 12, 'media': 18, 'baja': 2}

| ID | Severidad |
|---|---|
| R2-M1 | alta |
| R2-M2 | alta |
| R2-M3 | alta |
| R2-M4 | media |
| R2-M5 | media |
| R2-M6 | media |
| R2-M7 | media |
| R2-M8 | media |
| R2-M9 | media |
| R2-M10 | baja |
| R2-SW-01 | alta |
| R2-SW-02 | alta |
| R2-SW-03 | alta |
| R2-SW-04 | alta |
| R2-SW-05 | alta |
| R2-SW-06 | media |
| R2-SW-07 | media |
| R2-SW-08 | media |
| R2-SW-09 | media |
| C2-01 | alta |
| C2-02 | alta |
| C2-03 | media |
| C2-04 | alta |
| C2-05 | alta |
| C2-06 | media |
| C2-07 | media |
| C2-08 | media |
| C2-09 | media |
| C2-10 | media |
| C2-11 | media |
| C2-12 | media |
| C2-13 | baja |

## Auditoría 2b (2026-10-07)

Lentes de reutilización, pruebas/infra y producto/UX sobre el plan v2.2.

**30 hallazgos, todos aplicados.** Severidades: {'critica': 1, 'alta': 11, 'media': 13, 'baja': 5}

| ID | Severidad |
|---|---|
| R2b-INF-01 | critica |
| R2b-INF-02 | alta |
| R2b-INF-03 | alta |
| R2b-INF-04 | alta |
| R2b-INF-05 | alta |
| R2b-INF-06 | media |
| R2b-INF-07 | media |
| R2b-INF-08 | media |
| R2b-INF-09 | media |
| R2b-INF-10 | baja |
| R2b-OG-01 | alta |
| R2b-OG-02 | alta |
| R2b-OG-03 | media |
| R2b-OG-04 | media |
| R2b-OG-05 | media |
| R2b-OG-06 | media |
| R2b-OG-07 | baja |
| R2b-OG-08 | baja |
| R2b-OG-09 | baja |
| R2b-OG-10 | baja |
| UX-01 | alta |
| UX-02 | alta |
| DSN-01 | alta |
| DSN-02 | alta |
| UX-03 | alta |
| DSN-03 | media |
| UX-04 | media |
| UX-05 | media |
| UX-06 | media |
| UX-07 | media |

## Resultado
- **`spec/`:** 34 pruebas en verde y prueba de estrés de 320.000 operaciones aleatorias sin violar invariantes.
- **Contrato:** inventario de 105 operaciones contadas por script.
- **Temas corregidos:** reglas de dinero; concurrencia; propiedad de archivos entre agentes; contrato y eventos; sesión web con refresh; infraestructura (Railway, Neon, CI, Android); experiencia de usuario (horarios, avisos al dueño, datos móviles, Play Store); seguridad del código reutilizado.
