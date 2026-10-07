# Q1 — Integración backend + web, E2E, runbook de staging y auditorías

**Fase 2** · **worktree aislado `block/Q1`** creado desde el estado integrado en G2 (como todos los agentes); escribe en `e2e/**` y en correcciones de `api/**` y `web/**`. Aplica además la lista de correcciones de UI web que entregue Q2 · BD `panaderia_test_q1` y `panaderia_e2e` · puertos API 8020 y web 3020

## Objetivo
Que todo funcione **junto**: la API real cumple `spec/`, la web habla con la API real, existe un runbook exacto para staging y las auditorías no dejan hallazgos altos.

## Alcance
1. **Costuras**
   - Resolver las “Solicitudes de cambio” de todos los handoffs y reemplazar los stubs que queden.
   - `alembic heads` = 1.
   - Regenerar `contracts/openapi.json` y pedir al orquestador `npm run gen:api`.
   - Suite completa en verde; arreglos con commits pequeños.
2. **E2E de sistema:** `e2e/run_scenarios.py`
   - recibe `DATABASE_URL` y solo arranca Postgres si no se le pasa;
   - levanta uvicorn con seed y ejecuta **E1–E3 y E5–E14 por HTTP**;
   - incluye un **stream SSE real** (uvicorn): la cocina recibe `order.confirmed` y ningún campo de dinero;
   - `assert_money_invariants` al final;
   - workflow `.github/workflows/e2e.yml` con servicio `postgres:16`.
3. **Web contra la API real:** Playwright de W1 y W2 apuntando a la API local con seed, ejecutado en `e2e.yml`. Corregir divergencias entre la UI y el contrato.
4. **Runbook de staging** (`docs/handoffs/Q1-runbook-staging.md`). **Q1 no crea infraestructura**; el orquestador ejecuta el runbook. Debe cubrir:
   - servicios `api` y `web`: rootDirectory y **`railwayConfigFile=/api/railway.toml` y `/web/railway.toml`**;
   - `generate-domain`;
   - la tabla de variables de 01 (con `DATABASE_URL` pooler y `DATABASE_URL_DIRECT` de Neon `staging`);
   - creación del **Railway Bucket** y sus `S3_*`;
   - `BOOTSTRAP_ADMIN_*` y `SEED_DEMO=1`;
   - el orden de los pasos;
   - las verificaciones: `get-service-config`, `/api/health`, `get_database_tables` y `alembic_version`, login de admin.
5. **Auditorías:**
   - Auditor contable sobre `services/` y los dominios de dinero.
   - `/security-review`: authz por rol y propiedad, rate limit, archivos, CORS, cookies, secretos, saneo de código copiado de OpenGravity.
   - Corregir lo alto y lo crítico; documentar el resto.
6. **`docs/handoffs/Q1.md`:** informe de QA, **checklist manual** para el dueño y la lista **“Requiere al dueño”**.

## No tocar
`android/` (es de Q2). La infraestructura es del orquestador.

## Definición de terminado
G3 en la parte backend y web ([07](../07-pruebas.md)), con las salidas en el handoff.


## Ajustes v2.3 (auditoría 2b) — prevalecen sobre lo anterior
- **Verificación de staging sin navegador:**
  - `curl POST https://<api>/api/v1/auth/login` con el admin → 200 y `role=ADMIN`;
  - `GET https://<web>/login` → 200;
  - job `staging-smoke` en `e2e.yml` (`workflow_dispatch` con `web_url` y `api_url`) que hace el login con Playwright usando los secretos `STAGING_ADMIN_PHONE` y `STAGING_ADMIN_PASSWORD`, cargados por el orquestador.
- **Runbook:** builder RAILPACK, región `us-east4`, config file, todas las variables de 01 (incluidas `SEED_PASSWORD` y VAPID).
  - La contraseña del admin la genera el orquestador, se la entrega al dueño **solo por el chat**, y el dueño la cambia al primer ingreso.
- **E2E con `ACCESS_TOKEN_TTL_SECONDS=60`** para la prueba de sesión larga de cocina (W2).
- Aplica la lista de correcciones web que entregue Q2.
