"""Programador de jobs (03 §3.10): `AsyncIOScheduler(timezone=America/Caracas)` en el lifespan.

- `safe_job(name, fn)`: sesión propia, commit si termina bien, rollback y log si falla; nunca tumba la API.
- Respeta `SCHEDULER_ENABLED` (false en pruebas, E2E y CI).
- En E1 solo está registrado `bcv_sync` (06:00). `unpaid_auto_cancel` y `daily_closing` llegan con su etapa.
"""
from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.session import SessionLocal
from src.jobs import bcv_sync
from src.utils.date_utils import CARACAS_TZ

logger = logging.getLogger("jobs")

JobFn = Callable[[AsyncSession], Awaitable[None]]

#: (nombre, función, trigger). Los dueños completan `run` en su archivo; aquí solo el horario.
JOBS: list[tuple[str, JobFn, CronTrigger]] = [
    ("bcv_sync", bcv_sync.run, CronTrigger(hour=6, minute=0, timezone=CARACAS_TZ)),
]


def safe_job(name: str, fn: JobFn) -> Callable[[], Awaitable[None]]:
    async def _run() -> None:
        async with SessionLocal() as session:
            try:
                await fn(session)
                await session.commit()
                logger.info("Job %s terminó", name)
            except Exception:  # noqa: BLE001  (un job fallido no tumba la API)
                await session.rollback()
                logger.exception("Job %s falló", name)

    _run.__name__ = f"job_{name}"
    return _run


def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=CARACAS_TZ)
    for name, fn, trigger in JOBS:
        scheduler.add_job(safe_job(name, fn), trigger, id=name, name=name, coalesce=True, max_instances=1,
                          misfire_grace_time=3600, replace_existing=True)
    return scheduler


_scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> AsyncIOScheduler | None:
    global _scheduler
    if not settings.SCHEDULER_ENABLED:
        logger.info("Programador desactivado (SCHEDULER_ENABLED=false)")
        return None
    _scheduler = build_scheduler()
    _scheduler.start()
    logger.info("Programador iniciado con %d job(s)", len(JOBS))
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
