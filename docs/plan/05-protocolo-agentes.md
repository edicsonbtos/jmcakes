# 05 — Protocolo de trabajo entre agentes

Reglas que todo agente sigue para que los bloques encajen sin supervisión constante.

## 1. Antes de empezar

1. Leer `CLAUDE.md`, `docs/plan/00`–`05`, la ficha de su bloque y las **notas de entrega** (`docs/handoffs/*.md`) de los bloques de los que depende.
2. Leer `docs/CUESTIONARIO.md`: usar las respuestas; si una pregunta que le afecta sigue sin responder, usar el **valor por defecto** indicado y dejarlo anotado en su handoff.
3. Marcar su bloque como `EN CURSO` en `docs/plan/STATUS.md` (en su rama).

## 2. Ramas y PRs

- Rama: `block/<ID>-<slug>` (p. ej. `block/B2-pedidos`) creada desde `main` actualizado.
- Un PR por bloque hacia `main` (si el bloque es grande, PRs incrementales `block/B2-pedidos-1`, `-2`…).
- El PR debe pasar CI. Título: `[B2] API de pedidos, cocina y delivery`.
- Nunca hacer push a `main` directamente. Nunca reescribir la historia de la rama de otro bloque.

## 3. Propiedad de carpetas

- Cada bloque **solo modifica** las carpetas listadas en su ficha.
- Archivos compartidos (`contracts/openapi.yaml`, `api/src/db/schema/*`, `web/src/shared/*`, `android/core/*`, `package.json` raíz, workflows de CI): se permite **cambio aditivo** (agregar un endpoint, una columna nullable, una dependencia) con estas condiciones:
  - Se explica en la sección “Cambios a archivos compartidos” del handoff y del PR.
  - Las migraciones nuevas se crean con `drizzle-kit generate` (nunca se edita una migración ya fusionada).
  - **Cambios que rompen** (renombrar/eliminar campos o endpoints, cambiar estados) **no se hacen**: se anotan como “Solicitud de cambio de contrato” en el handoff para que Q1 o el humano decidan.

## 4. Contrato primero

- Si el bloque necesita un endpoint que no existe en `openapi.yaml`, primero lo agrega al contrato (cambio aditivo), luego lo implementa.
- La API valida en tests que sus respuestas cumplen el contrato (`api/test/contract.test.ts`, creado en F0).
- La web y Android generan/ajustan tipos desde el contrato, nunca inventan campos.

## 5. Definición de terminado (común a todos)

- [ ] Todo el alcance de la ficha implementado o explícitamente diferido en el handoff.
- [ ] Tests nuevos pasando; CI verde.
- [ ] Lint y typecheck limpios.
- [ ] Sin secretos en el código; variables nuevas documentadas en `.env.example`.
- [ ] Textos de interfaz en español (Venezuela); horas en `America/Caracas`.
- [ ] `docs/handoffs/<ID>.md` escrito (plantilla abajo).
- [ ] `docs/plan/STATUS.md` actualizado a `LISTO PARA REVISIÓN`.
- [ ] PR abierto con resumen y checklist.

## 6. Plantilla de nota de entrega (`docs/handoffs/<ID>.md`)

```md
# Handoff <ID> — <nombre del bloque>

## Qué quedó hecho
- …

## Cómo probarlo
- Comandos, URLs de staging, usuarios de prueba (sin contraseñas reales).

## Endpoints / pantallas entregados
- …

## Cambios a archivos compartidos
- contrato: …   · esquema/migraciones: …   · dependencias: …

## Decisiones tomadas por defecto (preguntas del cuestionario sin responder)
- C-n: se usó <valor> porque …

## Pendiente / diferido
- …

## Solicitudes de cambio de contrato (rompen compatibilidad)
- …

## Qué necesita el siguiente bloque
- Para <ID>: …
```

## 7. Cómo un bloque “enlaza” con el siguiente

1. El agente termina, deja el handoff y abre el PR.
2. El humano (o un agente revisor) hace merge.
3. El siguiente bloque, al iniciar, lee el handoff del anterior: ahí encuentra exactamente qué quedó, cómo probarlo y qué le toca.
4. Los bloques de interfaz (W/M) que estaban usando el mock cambian la URL base a staging cuando el handoff del bloque backend correspondiente dice “desplegado en staging”.

Opcional — orquestación automática: una sesión “orquestadora” puede lanzar los bloques con `create_session` (Claude Code remoto), pasar el prompt de cada ficha, y vigilar sus PRs; lanza la siguiente fase cuando todos los PRs de la anterior están fusionados.

## 8. Qué hacer si se bloquea

- Falta un dato del negocio → usar el valor por defecto del cuestionario y anotarlo.
- Falta una credencial (Firebase, Railway, Neon, keystore) → dejar la integración detrás de una variable de entorno con un *fallback* inofensivo (p. ej. push deshabilitado que solo registra en log) y anotarlo como pendiente para el humano.
- Otro bloque no ha entregado algo que necesita → usar el stub/mock y anotarlo; no implementar el módulo ajeno.
