---
name: jobs-programados-panaderia
description: Tareas programadas de la API de la panadería — APScheduler en el lifespan con zona America/Caracas, el envoltorio safe_job, SCHEDULER_ENABLED y las reglas de idempotencia (bcv_sync; unpaid_auto_cancel y daily_closing en su etapa). Úsala antes de tocar api/src/jobs/ o cualquier cosa que dependa de cuándo corre algo.
---
# Adaptado de OpenGravity: .agents/skills/jobs-programados-opengravity/SKILL.md

# Jobs programados

## Dónde vive
- `api/src/jobs/runner.py` (congelado, FND): `AsyncIOScheduler(timezone=America/Caracas)` arrancado
  en el lifespan de `main.py` solo si `SCHEDULER_ENABLED=true` (Railway). En pruebas, E2E y CI es false.
- `JOBS = [(nombre, run, trigger)]`. Cada dueño completa `run(session)` en **su** archivo.
- `safe_job(name, fn)`: sesión propia, `commit` si termina bien, `rollback` y log si falla. Un job
  fallido nunca tumba la API.
- Railway corre **una réplica** (`numReplicas = 1`): no hay jobs duplicados entre procesos.

## Jobs (03 §3.10)
| Job | Cuándo | Etapa |
|---|---|---|
| `bcv_sync` | 06:00 Caracas | E1: `sync_daily_rate()` inserta la fila BCV del día solo si falta. |
| `unpaid_auto_cancel` | cada 10 min | E2: `FOR UPDATE SKIP LOCKED`, respeta pagos en revisión. |
| `daily_closing` | 00:05, día anterior | Después de E1: métricas en SQL con `caracas_day_bounds_utc`. |

## Reglas
- **Idempotentes**: correr dos veces no cambia el resultado (insert-if-absent, upsert por fecha).
- El día es de Caracas: `get_today_caracas()`, `caracas_day_bounds_utc(d)`; nunca `.date()` sobre UTC.
- Nada de HTTP dentro de una transacción de dinero. La tasa se sincroniza en su propia sesión.
- Prueba `run(session)` directamente con `db_session`; el horario se prueba sobre `JOBS`.
