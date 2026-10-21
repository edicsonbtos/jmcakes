---
name: cambios-quirurgicos-panaderia
description: Cambios mínimos y localizados sobre código existente de la panadería (API y web), respetando las carpetas de cada agente y los archivos congelados. Úsala SIEMPRE antes de editar un archivo que ya existe, sobre todo al "agregar una función" a un módulo que ya funciona.
---
# Adaptado de OpenGravity: .agents/skills/cambios-quirurgicos-opengravity/SKILL.md

# Cambios quirúrgicos

## Por qué
El sistema mueve dinero de clientes. Reescribir un archivo entero para agregar una función rompe
cosas que ya estaban probadas y hace imposible revisar el diff.

## Cómo
1. Lee el archivo completo y sus pruebas antes de tocarlo.
2. Usa `Edit` puntual (CLAUDE.md regla 12). Nada de reescrituras completas de archivos existentes.
3. No renombres, muevas ni reformatees lo que no cambias. No “mejores” código ajeno de paso.
4. Respeta la propiedad (docs/plan/09 §E1 — Agentes y 05 §3):
   - Escribe solo en tus carpetas.
   - **Congelados** (solo cambios aditivos mínimos, declarados en el handoff): `api/src/main.py`,
     `config.py`, `core/**`, `db/**`, `domain/*/db_models.py`, `domain/*/interface.py`,
     `services/interfaces.py`, `jobs/runner.py`, `alembic/env.py`, `requirements.txt`.
   - El dueño de un dominio puede **ampliar** su `schemas.py` y su router sin quitar campos.
   - Renombrar, quitar o cambiar semántica: **no se hace**; va a “Solicitudes de cambio”.
5. El contrato (`contracts/openapi.json`) se genera; no lo edites a mano.
6. Cada cambio de comportamiento lleva su prueba; corre la suite antes de commitear.

## Señales de alarma
- Un diff que toca más de lo que describe el mensaje del commit.
- Borrar pruebas que fallan en vez de entender por qué.
- Cambiar una firma de `services/interfaces.py` o de un `interface.py`.
