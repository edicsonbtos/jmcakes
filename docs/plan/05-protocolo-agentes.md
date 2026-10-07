# 05 — Protocolo de trabajo del enjambre (v2.1)

## 1. Al empezar (cada agente)
1. Leer `CLAUDE.md`, `PRODUCT.md`, `docs/plan/00`–`08`, la ficha propia (`docs/plan/bloques/`) y los handoffs existentes (`docs/handoffs/`).
2. Si la tarea toca dinero: leer `spec/money_model.py` y `.claude/skills/contabilidad-panaderia` (o, si aún no existe, `OG/.agents/skills/contabilidad-opengravity/SKILL.md` teniendo en cuenta las diferencias de 06).
3. Si la tarea toca UI: cargar la skill **impeccable** y seguir `DESIGN.md`.
4. `git checkout -b block/<ID>` dentro de su worktree.
5. **Entorno propio** (paralelo seguro en un solo contenedor):

| Agente | Base de datos de pruebas | Puertos |
|---|---|---|
| FND | `panaderia_test_fnd` (+ `panaderia_migrations_fnd` para la prueba de migración) | API 8001 |
| B1 | `panaderia_test_b1` | 8011 |
| B2 | `panaderia_test_b2` | 8012 |
| B3 | `panaderia_test_b3` | 8013 |
| DSN | — | `WEB_PORT=3000`, `MOCK_PORT=4010` |
| W1 | — | `WEB_PORT=3001`, `MOCK_PORT=4011` |
| W2 | — | `WEB_PORT=3002`, `MOCK_PORT=4012` |
| Q1 | `panaderia_test_q1`, `panaderia_e2e` | API 8020, web 3020 |
| Q2 | — | — |

   - Conexión: `TEST_DATABASE_URL=postgresql+psycopg://dev:dev@127.0.0.1:5432/<base>`. El conftest crea la base si no existe.
   - Postgres: `service postgresql start`. Si falta el rol `dev`, crearlo con `su postgres -c "psql -c \"CREATE ROLE dev LOGIN SUPERUSER PASSWORD 'dev'\""`. `scripts/dev-setup.sh` (FND) hace todo esto.

## 2. Git
- Cada agente trabaja en su **worktree aislado**, en la rama `block/<ID>`, creada desde el estado integrado más reciente.
- Commits pequeños en español con el prefijo `[<ID>]`, terminados con las líneas de atribución que indique el orquestador.
- **Los agentes NO hacen push ni abren PR.** El orquestador:
  1. revisa `git diff --stat claude/happy-johnson-24innr...block/<ID>` contra las carpetas propias. También se permiten `docs/handoffs/<ID>.md`, la revisión Alembic propia (`*_<id>_*.py`) y los cambios aditivos **declarados** en el handoff;
  2. integra con `git merge --no-ff` en `claude/happy-johnson-24innr`;
  3. corre las compuertas;
  4. publica.
- Nunca reescribir historia ajena, usar `--force` ni borrar ramas.

## 3. Propiedad de archivos
- Solo se escribe en las **carpetas propias** de la ficha (tabla de 04). Lectura libre.
- **Congelados después de FND y DSN.** Solo admiten cambios aditivos mínimos, declarados en el handoff:

| Lado | Archivos congelados |
|---|---|
| API | `api/src/main.py`, `config.py`, `core/**`, `db/**`, `domain/*/db_models.py`, `domain/*/interface.py`, `services/interfaces.py`, `jobs/runner.py`, `alembic/env.py`, `requirements.txt` (pedir dependencias en el handoff) |
| Web | `web/package.json` y lockfile (W1 y W2 **no** los tocan), `web/src/lib/**` (W1 y W2 **no** editan archivos existentes; sus helpers van en `src/components/{admin,cocina}/lib/`), `web/src/components/ui/**`, `web/src/app/globals.css`, `web/src/proxy.ts`, `web/public/**` (salvo lo que la ficha permita) |
| Diseño | `DESIGN.md`, `docs/design/tokens.json` |

- Excepción: el bloque dueño de un dominio puede **ampliar** su `domain/<x>/schemas.py` y su router, sin quitar campos.
- Cambios que rompen compatibilidad (renombrar, quitar, cambiar semántica): **no se hacen**. Se piden en el handoff en “Solicitudes de cambio”, y los resuelve el orquestador o Q1.
- **`docs/plan/STATUS.md` lo edita solo el orquestador.** Los agentes informan su estado en el handoff y en su respuesta final.

## 4. Migraciones
- FND crea la revisión inicial con todo el esquema y las restricciones nombradas.
- Si un bloque de la Fase 1 necesita un cambio, crea **una** revisión `<ID>_<desc>` con `down_revision` igual a la cabeza de FND. Debe ser idempotente (inspector o `IF NOT EXISTS`) y reflejarse también en `db_models` (cambio aditivo declarado).
- El orquestador fusiona las cabezas (`alembic merge heads`).
- Prohibido: editar migraciones integradas, `create_all` y `DROP` sin autorización.

## 5. Contrato y tipos
- `contracts/openapi.json` **se genera**: `cd api && python scripts/export_openapi.py`.
  - B1, B2 y B3 **no lo commitean**: lo exportan solo para verificar en local.
  - El orquestador lo regenera y lo commitea tras cada integración.
- `web/src/lib/api-types.ts` lo genera **solo el orquestador** (`npm run gen:api`), en G1 y G2. W1 y W2 no lo regeneran.
- W1, W2 y M consumen el contrato. Si les falta algo, lo piden en el handoff; mientras tanto usan un fixture local marcado `TODO(contrato)`.

## 6. Definición de terminado (todo agente)
- [ ] Alcance de la ficha cumplido, o lo diferido explicado en el handoff.
- [ ] **Pruebas ejecutadas localmente y en verde.** Comandos según el componente (ver 07 §3):
  - API: `pytest` (con su `TEST_DATABASE_URL`).
  - Web: `npm run lint && npm test && npm run build && npx playwright test --list`.
  - Android: `gradle :core:network:test :core:data:test`.
  Pegar el resumen de la salida en el handoff.
- [ ] Sin secretos, sin datos ni comentarios de producción de OpenGravity (06 §Reglas).
- [ ] Textos en español de Venezuela; hora de Caracas; dinero como string decimal.
- [ ] `docs/handoffs/<ID>.md` escrito con la plantilla (§7).
- [ ] Commit final en `block/<ID>`. Respuesta al orquestador con rama, SHA, resumen, pruebas y resultados, pendientes y solicitudes de cambio.

## 7. Plantilla de handoff
```md
# Handoff <ID> — <nombre>
## Hecho
## Pruebas ejecutadas (comando → resultado)
## Endpoints / pantallas entregados
## Cambios a archivos compartidos (aditivos)
## Dependencias nuevas pedidas
## Decisiones por defecto tomadas
## Pendiente / diferido
## Solicitudes de cambio (rompen compatibilidad)
## Para el siguiente bloque
```

## 8. Si un agente se bloquea

| Caso | Qué hacer |
|---|---|
| Falta un dato del negocio | Usar el default del cuestionario y anotarlo. |
| Falta una credencial | Usar el adaptador nulo o local y anotarlo. |
| Falta algo de otro bloque | Usar el stub o la fábrica de 08; nunca implementar el módulo ajeno. |
| Duda de dinero o de estados | Detenerse, dejar una prueba `xfail(strict=True)` con el caso y reportarlo. No improvisar reglas. |
