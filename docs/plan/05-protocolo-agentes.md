# 05 — Protocolo de trabajo del enjambre

## 1. Al empezar (cada agente)
1. Leer `CLAUDE.md`, `PRODUCT.md`, `docs/plan/00`–`08`, la ficha propia en `docs/plan/bloques/` y los handoffs existentes en `docs/handoffs/`.
2. Si la tarea toca dinero, leer `spec/money_model.py` y `.claude/skills/contabilidad-panaderia` (si existe; si no, `/home/user/opengraviti/.agents/skills/contabilidad-opengravity/SKILL.md`).
3. Si la tarea toca UI, cargar la skill **impeccable** y seguir `DESIGN.md`.
4. Crear la rama de trabajo **en el worktree**: `git checkout -b block/<ID>`.

## 2. Git: ramas, commits e integración
- Cada agente trabaja en su **worktree aislado**, en `block/<ID>`, creada desde el estado integrado de la fase anterior.
- Commits pequeños y descriptivos, en español, con el prefijo `[<ID>]`. Terminan con las líneas de atribución que indique el orquestador.
- **Los agentes no hacen push.** El orquestador:
  1. revisa `git diff --stat` contra las carpetas propias de la ficha;
  2. integra con `git merge --no-ff block/<ID>` en `claude/happy-johnson-24innr`;
  3. corre las compuertas;
  4. hace push.
- Nunca reescribir historia ajena, ni hacer `--force`, ni borrar ramas de otros.

## 3. Propiedad de archivos
- Solo se escribe en las **carpetas propias** de la ficha. Lectura libre.
- **Archivos compartidos congelados después de FND:** `api/src/main.py`, `api/src/db/models_registry.py`, `api/src/config.py`, `api/src/core/**`, `api/src/domain/*/db_models.py`, `api/src/domain/*/interface.py`, `api/src/domain/*/schemas.py`, `web/src/lib/**`, `web/src/components/ui/**`, `web/src/app/globals.css`, `DESIGN.md`.
  - Se permiten **cambios aditivos mínimos**: agregar un campo opcional a un esquema, un setting nuevo o un método a un componente sin romper sus props. Cada uno se declara en el handoff, en “Cambios a compartidos”.
  - Los cambios que **rompen** (renombrar o quitar campos, cambiar semánticas o estados) no se hacen. Se piden en el handoff, en “Solicitudes de cambio”, y los resuelve Q1.
- Excepción: `api/src/domain/<dominio>/schemas.py` lo puede ampliar el bloque dueño de ese dominio, sin quitar campos.

## 4. Migraciones (Alembic)
- FND crea la revisión inicial con todo el esquema.
- Un bloque de la Fase 1 que necesite un cambio de esquema crea **una** revisión, con nombre `<ID>_<descripcion>` y `down_revision = <cabeza de FND>`. Debe ser idempotente: inspector y `IF NOT EXISTS`, según `migraciones-esquema-opengravity`.
- El orquestador fusiona las cabezas con `alembic merge heads` al integrar.
- Prohibido editar una migración ya integrada, `create_all` en Postgres, o un `DROP` sin autorización.

## 5. Contrato
- `contracts/openapi.json` **se genera** (`python api/scripts/export_openapi.py`), nunca se edita a mano.
- B1–B3 pueden regenerarlo en su rama. Al integrar, el orquestador lo regenera de nuevo; en caso de conflicto, se resuelve regenerando.
- W1, W2 y M consumen el contrato. Si les falta un campo, lo piden en el handoff y no lo inventan. Mientras tanto usan el mock y, si hace falta, un *fixture* local marcado `TODO(contrato)`.

## 6. Definición de terminado (todo agente)
- [ ] Alcance de la ficha completo, o cada punto diferido explicado en el handoff.
- [ ] Pruebas nuevas verdes en el worktree: `pytest` (api), `npm run build && npm run lint && npm test` (web) o tests JVM escritos (android).
- [ ] Sin secretos en el código; variables nuevas en `.env.example`.
- [ ] Textos en español de Venezuela; horas en `America/Caracas`; dinero en string decimal en la API.
- [ ] `docs/handoffs/<ID>.md` con la plantilla del §7.
- [ ] La fila propia de `docs/plan/STATUS.md` marcada `LISTO PARA INTEGRAR`.
- [ ] Commit final en `block/<ID>`. Respuesta final al orquestador con: rama, SHA, resumen, pruebas ejecutadas y su resultado, pendientes.

## 7. Plantilla de handoff (`docs/handoffs/<ID>.md`)
```md
# Handoff <ID> — <nombre>
## Hecho
## Cómo probar (comandos exactos y resultado obtenido)
## Endpoints / pantallas entregados
## Cambios a compartidos (aditivos)
## Decisiones por defecto tomadas (preguntas del cuestionario sin respuesta)
## Pendiente / diferido
## Solicitudes de cambio (rompen compatibilidad)
## Para el siguiente bloque
```

## 8. Si un agente se bloquea
- **Falta un dato del negocio:** usar el valor por defecto de `docs/CUESTIONARIO.md` y anotarlo.
- **Falta una credencial** (FCM, bucket, SMTP): usar el adaptador nulo o local y anotarlo.
- **Falta algo de otro bloque:** usar el stub o el mock; nunca implementar el módulo ajeno.
- **Duda que cambia dinero o estados:** detenerse en ese punto, dejar una prueba `xfail(strict=True)` que documente el caso y reportarlo. No improvisar reglas de dinero.
