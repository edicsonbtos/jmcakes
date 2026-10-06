# Q1 — Integración backend + web, E2E, staging y auditorías

**Fase 2** · Trabaja **sobre la rama de integración** en el directorio principal, después de que el orquestador integra la Fase 1.

## Objetivo
Que todo funcione **junto**: la API real con las reglas de `spec/`, la web contra la API real, el despliegue en staging y las auditorías contable y de seguridad sin hallazgos altos.

## Alcance
1. **Costuras**
   - Resolver las “Solicitudes de cambio” de todos los handoffs.
   - Reemplazar los stubs que queden.
   - Verificar que `alembic heads` = 1 (si no, crear la revisión de merge) y regenerar `contracts/openapi.json`.
   - Correr la suite completa y arreglar lo roto con commits pequeños.
2. **E2E de sistema:** `e2e/run_scenarios.py` levanta Postgres local, la API con seed y uvicorn, y ejecuta **E1–E12** por HTTP, incluyendo:
   - verificación SSE de que la cocina recibe `order.confirmed` y nunca montos;
   - `assert_money_invariants` al final.
   - Agregarlo al workflow `e2e.yml`.
3. **Web contra la API real:** Playwright de W1 y W2 apuntando a la API local con seed. Corregir divergencias entre UI y contrato.
4. **Staging en Railway** (proyecto `jmcakes`, entorno `staging`):
   - **Servicios:**
     - `api` con rootDirectory `api`;
     - `web` con rootDirectory `web`;
     - ambos conectados al repo `edicsonbtos/jmcakes`, rama de integración.
   - **Variables** (sin imprimir secretos en logs ni en el repo):
     - `DATABASE_URL` de Neon `staging` (vía MCP de Neon, rol owner, con pooler);
     - `JWT_SECRET` aleatorio;
     - `CORS_ORIGINS`;
     - `NEXT_PUBLIC_API_URL`;
     - adaptadores nulos para FCM y bucket hasta tener credenciales (o crear el Railway Bucket y sus credenciales).
   - **Dominios** generados, y `/api/health` en OK.
   - **Migraciones** aplicadas por `preDeployCommand`, verificadas con el MCP de Neon (`get_database_tables`).
   - **Seed** de staging con un admin (contraseña aleatoria, entregada **solo** en el resumen privado al orquestador, nunca en el repo).
5. **Auditorías**
   - Auditor contable (`.claude/agents/auditor-contable.md`) sobre todo `api/src/services/` y `api/src/domain/` de dinero.
   - `/security-review`: authz por rol, propiedad, rate limit, subida de archivos, CORS, secretos.
   - Correcciones de lo alto o crítico, y el resto documentado.
6. **`docs/handoffs/Q1.md`:** informe de QA (qué se probó, resultados, URLs de staging, pendientes) y una **checklist manual** para el dueño.

## No tocar
`android/` (es de Q2).

## Definición de terminado
Compuerta G3 (parte backend y web) de [07](../07-pruebas.md).
