# Q2 — Android en CI, QA de las apps y auditoría de diseño

**Fase 2**. Arranca en **G2**, en paralelo con Q1, para el ciclo de CI de Android. La parte que depende de staging espera a Q1.

## Objetivo
Las dos apps compilan y pasan sus pruebas en GitHub Actions, alineadas con la API real, y todas las superficies pasan la auditoría Impeccable.

## Alcance
1. **Android verde en CI.** Es la única vía de compilación: el SDK no se puede descargar en el contenedor, así que no se intenta armar uno.
   - Ciclo: el orquestador publica → Q2 lee los logs de `android.yml` (MCP de GitHub: `actions_list`, `get_job_logs`) → corrige → entrega el commit → repetir.
   - Cuando el orquestador espera un CI, Q2 entrega una lista exacta de lo que corrigió y por qué.
2. **Alinear con la API real:** DTOs contra el `openapi.json` final; flavor `staging` con la URL de Railway; pruebas con MockWebServer usando respuestas reales capturadas de la API local con seed.
3. **Auditoría Impeccable:**
   - `audit` y `polish` (variantes nativas para Android) sobre admin, cocina, cliente y delivery;
   - corregir lo crítico y lo alto (UI web solo en `web/src/app/**` y `web/src/components/{admin,cocina}/**`);
   - capturas finales: Playwright en CI para la web; Roborazzi en CI para Android, si se logra.
4. **Distribución:**
   - `.github/workflows/release-android.yml` (manual): APK de delivery firmada y AAB de cliente, si existen los secretos del keystore. Si no existen, se documenta.
   - Pasos para el dueño: Play Console, prueba cerrada de 12 testers × 14 días, Firebase.
5. **`docs/handoffs/Q2.md`:** informe más la **checklist de prueba manual en un teléfono real**.

## Definición de terminado
`android.yml` verde en el último commit, con más de 0 pruebas en `app-cliente`. APKs como artifacts. Auditoría de diseño sin críticos.
