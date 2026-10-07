# DSN — Sistema de diseño (Impeccable) y base web

**Fase 0** (en paralelo con FND) · rama `block/DSN` · puertos `WEB_PORT=3000`, `MOCK_PORT=4010` · skill obligatoria: **impeccable**

## Objetivo
Definir el mundo visual de la panadería y dejarlo listo en código (web) y en especificación (Android), para que W1, W2 y M solo compongan pantallas.

## Alcance
1. **Impeccable**
   - `sh .claude/skills/impeccable/scripts/impeccable context`. `PRODUCT.md` ya está confirmado por el dueño: **no rehacer init**.
   - Seguir `reference/new-work.md` hasta escribir **`DESIGN.md`**: dirección, paleta por roles en claro y oscuro, tipografía, espaciado, radios, elevación, movimiento, iconografía y voz.
   - Dirección **propia de panadería venezolana**: cálida y apetitosa, pero operativa. No una plantilla SaaS.
   - Requisitos: contraste AA, cocina legible a 2 m, nombre del negocio configurable.
   - Ruta **code-first**: no hay generación de imágenes garantizada. Si la skill pide decisiones al usuario y no hay forma de preguntarle, documentar las inferencias como “supuestos” en `DESIGN.md`.
2. **Tokens:**
   - `docs/design/tokens.json` es la fuente.
   - `web/src/app/globals.css`: variables CSS + `@theme` de Tailwind 4, con oscuro.
   - `docs/design/android-theme.md`: `ColorScheme`, `Typography` y `Shapes` de Material 3, más fragmentos `Color.kt`, `Type.kt` y `Theme.kt`.
3. **Especificaciones por superficie** en `docs/design/`: `admin.md`, `cocina.md`, `cliente-android.md` y `delivery-android.md`.
   - Cada una con navegación, pantallas (layout ASCII), componentes, estados (vacío, cargando, error, sin conexión) y **textos exactos**.
   - En detalle:
     - checkout CASH: billetera usada, faltante USD/Bs, datos de pago con botón copiar, referencia y comprobante, y la hora límite;
     - selector “Lo quiero hoy / Programar”;
     - tablero de cocina con “Programados” y la fecha en grande;
     - bandeja de pagos con el comprobante a la vista.
4. **Base web** (copiando OpenGravity según 06):
   - **Proyecto:**
     - Next 16.2.2, React 19.2.4 y Tailwind 4. Leer `node_modules/next/dist/docs/` antes de escribir.
     - **Todas las dependencias** que W1 y W2 necesitarán: recharts, openapi-typescript, @playwright/test, testing-library, clsx y lucide-react. W1 y W2 **no** tocarán `package.json`.
   - **Auth con refresh** (01 §Autenticación):
     - Server Action de login que guarda las cookies httpOnly `authToken` y `refreshToken`;
     - `src/app/api/auth/refresh/route.ts`, `src/app/api/auth/token/route.ts` y logout;
     - `src/proxy.ts` con roles por ruta y redirección a refresh, sin `console.log`;
     - ninguna ruta recibe tokens desde el navegador.
   - **`src/lib/`:**
     - `api.ts` y `client-api.ts`: base `NEXT_PUBLIC_API_URL`, conservan `detail` y `code`, reintentan una vez tras un 401 vía refresh;
     - `format.ts` (Caracas): `fmtUsd`, `fmtBs`, `fmtDate`, `fmtTime` y `fmtDateBig`;
     - `useEventStream.ts`: token fresco por `/api/auth/token` → `POST /events/token`, reconexión con backoff y `lastEventId`, y manejo del evento `reset`;
     - script `npm run gen:api` (openapi-typescript → `src/lib/api-types.ts`), que ejecutará el orquestador.
   - **UI kit** `src/components/ui/`:
     - componentes de OpenGravity re-vestidos con los tokens; `DataTable` agrega `cursor` y `onLoadMore`;
     - nuevos: `MoneyText` (USD con los Bs **de la API** debajo), `StatusPill` (con texto), `EmptyState`, `Skeleton`, `ConnectionBanner`, `FileUpload` (multipart a `/files`) y `ConfirmDialog`.
   - **Layouts:**
     - `(admin)/layout.tsx` con `components/layout/Sidebar.tsx` (que pasa a ser de W1) y topbar con el nombre del negocio desde `/settings/public`;
     - `(cocina)/layout.tsx` a pantalla completa, con Wake Lock y “Activar sonido”;
     - páginas placeholder.
   - **Recursos:** `web/public/sounds/{nuevo-pedido,pago-reportado}.mp3` (sonidos cortos generados, de licencia libre), íconos, `web/public/cocina/manifest.webmanifest`.
   - **Página `/design`** (solo en desarrollo) con tokens y componentes.
   - **Playwright:** `playwright.config.ts` lee `WEB_PORT`/`MOCK_PORT` y arranca Prism y `next dev`. Spec de capturas de `/design` en escritorio y móvil, claro y oscuro.
   - `web/.env.example`: `NEXT_PUBLIC_API_URL` y `JWT_SECRET` (en modo mock, `dev-mock-secret-no-usar-en-prod`).
5. **CI:** `.github/workflows/web.yml` con `npm ci`, lint, test y build, más un job `e2e-web` (`npx playwright install --with-deps chromium`, contra Prism) que sube capturas y reporte como artifacts.
6. `impeccable detect --json web/src` sin críticos; la salida va en el handoff.

## No tocar
`api/`, `android/`, `contracts/`.

## Limitantes
- **Playwright no corre en el contenedor**: no puede descargar navegadores. Las pruebas se escriben en local y se ejecutan en CI.
- El contrato aún no existe mientras trabaja: los tipos los genera el orquestador en G1.

## Compuerta G1 (parte DSN)
- `DESIGN.md`, `tokens.json`, `android-theme.md` y las 4 especificaciones.
- `npm ci && npm run lint && npm test && npm run build && npx playwright test --list` en verde (salida en el handoff).
- `impeccable detect` sin críticos.


## Ajustes v2.3 (auditoría 2b) — prevalecen sobre lo anterior
- **La dirección visual ya está elegida por el dueño** en el paso G0.5 (04): contrato de dirección y *seed key* registrados en `.impeccable/surfaces/*.md` y `.impeccable/config.json` (`buildPath: code`).
  - DSN **no vuelve a tirar** la dirección: la recibe.
  - Corre `impeccable context --target "web/src/app/(admin)"` y `--target "web/src/app/(cocina)"`. `PRODUCT.md` raíz = plataforma `web`; `android/PRODUCT.md` = `android`.
- **Orden correcto de new-work** (reemplaza “escribir DESIGN.md primero”):
  1. construir tokens, `globals.css`, el UI kit, `/design` y **una pantalla de muestra por superficie** (tarjeta de cocina a 1920×1080, bandeja de pagos a 390 px);
  2. commit y aviso al orquestador. El orquestador publica `block/DSN`, `web.yml` captura a 1440 y 390 px y el orquestador baja las capturas a `.impeccable/review/`;
  3. el orquestador lanza `impeccable-finish-reviewer` (sin historial), y DSN aplica **una** ronda de correcciones;
  4. `impeccable-documenter` escribe `DESIGN.md` y su sidecar **a partir de lo construido**.

  `docs/design/*.md` sigue siendo la especificación de pantallas. `.impeccable/review/` y `.impeccable/mocks/` van en `.gitignore`.
- **Páginas públicas** (exigidas por Play Store), con nombre y WhatsApp desde `/settings/public` y exentas en `proxy.ts`:
  - `web/src/app/(publico)/privacidad/page.tsx`: datos guardados (teléfono, dirección, comprobantes y token de push);
  - `/eliminar-cuenta`: cómo borrar la cuenta en la app, más el botón “Escribir por WhatsApp”.
- **`web/package-lock.json`** generado y commiteado. `next`, `react` y `react-dom` en versión exacta. Ver 06 §Web para los archivos base adicionales.
