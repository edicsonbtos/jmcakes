# DSN — Sistema de diseño (Impeccable) y base web

**Fase 0** (en paralelo con FND) · **Rama** `block/DSN` · **Skill obligatoria:** `impeccable` (en `.claude/skills/impeccable`)

## Objetivo
Definir el **mundo visual** de la panadería y dejarlo en código para web, y en especificación lista para Android, de modo que W1, W2 y M solo compongan pantallas.

## Alcance
1. **Impeccable**
   - Ejecutar `sh .claude/skills/impeccable/scripts/impeccable context`. `PRODUCT.md` ya existe y fue confirmado por el dueño: **no rehacer** el init.
   - Seguir `reference/new-work.md` para crear **`DESIGN.md`**: dirección visual, paleta con roles (claro y oscuro), tipografía, escala de espaciado, radios, elevación, movimiento, iconografía y voz de los textos.
   - Una dirección **propia de panadería venezolana**, cálida y apetitosa pero operativa. No una plantilla genérica de SaaS.
   - Respetar `PRODUCT.md`: nombre configurable, sin logo fijo, contraste AA, legible a 2 m en cocina.
   - Usar código primero: la generación de imágenes no está garantizada en este entorno.
2. **Tokens compartidos**
   - `docs/design/tokens.json` es la fuente: color por rol, tipo, espaciado, radios y movimiento.
   - Derivados:
     - `web/src/app/globals.css`: variables CSS y `@theme` de Tailwind 4, con modo oscuro;
     - `docs/design/android-theme.md`: valores para `ColorScheme`, `Typography` y `Shapes` de Material 3, más los fragmentos `Color.kt`, `Type.kt` y `Theme.kt` listos para copiar.
3. **Especificación por superficie** en `docs/design/`:
   - `admin.md` (panel), `cocina.md` (tablet/TV, 2 m) y `cliente-android.md` y `delivery-android.md` (Material 3 según `reference/android.md`).
   - Cada una con: mapa de navegación, lista de pantallas, para cada pantalla un esquema de layout (ASCII), componentes, estados (vacío, cargando, error, sin conexión) y textos exactos en español.
   - Pantallas clave a especificar con detalle:
     - checkout CASH: billetera usada, faltante en USD y Bs, datos de pago, formulario de referencia y comprobante;
     - selector “Lo quiero hoy / Programar fecha y hora”;
     - tablero de cocina con “Programados” y la fecha en grande;
     - bandeja de verificación de pagos con el comprobante a la vista.
4. **Base web** (copiando OpenGravity `apps/web`, ver [06](../06-reutilizacion-opengravity.md)):
   - Configuración y dependencias:
     - Next 16.2.2, React 19.2.4 y Tailwind 4, con las mismas versiones que OpenGravity;
     - `AGENTS.md` con la advertencia de Next 16;
     - ESLint, Vitest y Playwright configurado (`web/e2e/`).
   - Auth y datos:
     - `src/proxy.ts` con roles: `/admin/**` exige ADMIN y `/cocina/**` exige PRODUCTION o ADMIN;
     - login por teléfono (`src/app/login`) y Server Actions;
     - `src/lib/api.ts` y `client-api.ts`, que preservan `detail` y `code`;
     - `src/lib/format.ts`: `fmtUsd`, `fmtBs`, `fmtDate`, `fmtTime` y `fmtDateBig`, todos con zona Caracas;
     - `src/lib/useEventStream.ts`: SSE con token de stream, reconexión y `Last-Event-ID`;
     - tipos TypeScript generados desde `contracts/openapi.json` (`openapi-typescript`), con el script `npm run gen:api`;
     - si el contrato aún no existe al empezar, el script queda listo y se ejecuta al integrar.
   - **UI kit** en `src/components/ui/`:
     - componentes de OpenGravity re-vestidos con los tokens: Button, Card, Badge, DataTable (paginación del servidor), Modal, Input, Select, Switch, Textarea, Timeline y MetricCard;
     - componentes nuevos: `MoneyText` (USD con Bs debajo), `StatusPill` (estado con texto, no solo color), `EmptyState`, `Skeleton`, `ConnectionBanner`, `ImageUpload` y `ConfirmDialog`.
   - Layouts:
     - `src/app/(admin)/layout.tsx` con Sidebar y topbar con nombre del negocio de `/settings/public`;
     - `src/app/(cocina)/layout.tsx` a pantalla completa, con Wake Lock y botón “Activar sonido”;
     - páginas índice placeholder con `EmptyState`.
   - Página `/design` (solo en desarrollo) que muestra tokens y componentes: el catálogo vivo.
5. **CI:** `.github/workflows/web.yml` con `npm ci`, `lint`, `test` y `build`.
6. **Detector:** al terminar, `impeccable detect --json` sobre `web/src` sin hallazgos críticos, y el resultado en el handoff.

## No tocar
`api/`, `android/`, `contracts/`.

## Limitantes
- No hay emulador Android: la parte Android es especificación más fragmentos Kotlin; M los integra.
- Leer `node_modules/next/dist/docs/` antes de escribir código Next 16.
- Las versiones de las dependencias se fijan a las de OpenGravity.

## Oportunidades
- Ya existe un panel probado (OpenGravity). Basta con re-vestirlo, sin reinventar las interacciones.
- Las capturas de `/design` con Playwright sirven al dueño para aprobar la dirección visual.

## Compuerta G1 (parte DSN)
- [ ] `DESIGN.md`, `docs/design/tokens.json`, `android-theme.md` y las 4 especificaciones de superficie.
- [ ] `npm ci && npm run lint && npm test && npm run build` verdes en `web/`.
- [ ] Capturas de `/design` (escritorio y móvil, claro y oscuro) en `docs/handoffs/assets/DSN-*.png`.
- [ ] Salida de `impeccable detect` en el handoff.
