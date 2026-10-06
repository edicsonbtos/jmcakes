# Q2 — Android en CI, QA de las apps y auditoría de diseño

**Fase 2** (después de Q1) · Trabaja sobre la rama de integración.

## Objetivo
Las dos APKs compilan y pasan sus pruebas en GitHub Actions apuntando a staging, y todas las superficies pasan la auditoría de Impeccable.

## Alcance
1. **Android verde en CI**
   - El orquestador publica la rama; GitHub Actions corre `android.yml`.
   - Q2 lee los logs (MCP de GitHub: `actions_list`, `get_job_logs`), corrige y entrega el commit. Se repite hasta verde.
   - **Opcional:** armar un SDK mínimo desde `maven.google.com` (aapt2 y artefactos de AGP) para compilar en local. Si no se logra en un intento razonable, seguir con CI.
2. **Alinear las apps con la API real**
   - DTOs contra el `openapi.json` final.
   - Flavor `staging` con la URL de Railway.
   - Pruebas JVM de integración contra un servidor falso (MockWebServer) que reproduce respuestas reales capturadas de staging.
3. **Auditoría Impeccable**
   - `$impeccable audit` y `polish` (variantes nativas para Android) sobre admin, cocina, cliente y delivery.
   - Corregir lo crítico y lo alto.
   - Capturas finales: web con Playwright; Android con Roborazzi o las APKs de CI si se pueden ejecutar.
4. **Distribución**
   - Workflow `release-android.yml` (manual) que construye la APK firmada de delivery y el AAB de cliente cuando existan los secretos del keystore. Sin secretos, queda documentado.
   - Pasos para el dueño: Play Console, prueba cerrada con 12 testers × 14 días y Firebase.
5. `docs/handoffs/Q2.md` con un informe y una **checklist de prueba manual** en un teléfono real.

## Definición de terminado
`android.yml` verde en el último commit; APKs como artefactos; auditoría de diseño sin críticos; handoff completo.
