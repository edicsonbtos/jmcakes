---
name: migraciones-esquema-panaderia
description: Cómo cambiar el esquema de la panadería con Alembic — convenciones de 02 (snake_case/camelCase, cuid2, enums con nombre, restricciones nombradas), revisiones por bloque, registro de modelos y la prueba alembic check. Úsala antes de tocar api/src/domain/*/db_models.py, api/alembic/ o cualquier cambio que agregue tablas, columnas, índices o restricciones.
---
# Adaptado de OpenGravity: .agents/skills/migraciones-esquema-opengravity/SKILL.md

# Migraciones del esquema

## Reglas fijas (CLAUDE.md §BD y docs/plan/02)
- Tablas en `snake_case`; columnas en **camelCase** (nombre físico como primer argumento de `Column`);
  atributos Python en `snake_case`. Usa las ayudas de `src/db/columns.py` (`pk()`, `created_at()`,
  `updated_at()`, `enum_col()`, `fk()`, `MONEY`, `RATE`).
- IDs `String` con cuid2. `DateTime` naive en UTC. Dinero `Numeric(14,2)`; tasa `Numeric(14,4)`.
- Enums en `src/db/enums.py` y `SQLEnum(X, name="X")` (el valor guardado es el nombre del miembro).
- **Toda FK lleva índice** (o es la primera columna de un índice compuesto o de una única).
- Restricciones **nombradas**: `CheckConstraint(..., name="corto")` → `ck_<tabla>_corto` por la
  convención de `src/db/base.py`; únicas `uq_…`. El handler de `IntegrityError`
  (`core/errors.py::CONSTRAINT_CODES`) mapea el nombre a un `code` del catálogo: si agregas una
  única que el usuario puede violar, agrega su `code` ahí (cambio aditivo declarado).
- **Solo Alembic migra.** Nunca `create_all` en Postgres ni `DROP` sin autorización del humano.

## Flujo por bloque (docs/plan/05 §4)
1. Los `db_models.py` son de FND y están congelados: un cambio es **aditivo** y se declara en el handoff.
2. Una sola revisión por bloque: `api/alembic/versions/<id>_<bloque>_<desc>.py`, con
   `down_revision` = la cabeza de FND (`0001_fnd`). Idempotente (inspector o `IF NOT EXISTS`).
3. Genera contra una base vacía propia y revisa a mano:
   ```bash
   cd api
   DATABASE_URL=postgresql+psycopg://dev:dev@127.0.0.1:5432/<base_scratch> alembic upgrade head
   DATABASE_URL=… alembic revision --autogenerate --rev-id 0002_b1 -m "b1 <desc>"
   ```
   Alembic **no** genera secuencias (`op.execute(CreateSequence(...))`) ni compara CHECKs.
4. Si el modelo es de un dominio nuevo, importa su módulo en `src/db/models_registry.py`.
5. Pruebas: `tests/test_migrations.py` hace upgrade → downgrade base → upgrade en
   `panaderia_migrations_<id>` y `alembic check` sin diferencias. El orquestador fusiona cabezas.

## No hacer
- Editar una migración ya integrada.
- `server_default=func.now()` en tablas de ledger (repite la hora de inicio de la transacción).
- Borrado físico de pagos o de movimientos del ledger.
