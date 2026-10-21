# Handoff DSN — Diseño y base web (E1)

Rama `block/DSN` (worktree propio). Alcance: el recorte de DSN en docs/plan/09 §E1 — Agentes. Lo que no está en E1 (cocina, Android, sonidos, `useEventStream`, páginas públicas, `FileUpload`, `ConnectionBanner`) **no** se hizo.

## Hecho
- **Tokens:** `docs/design/tokens.json` (fuente) y `web/src/app/globals.css` (Tailwind 4 `@theme`, paleta por defecto apagada con `--color-*: initial`, oscuro por `prefers-color-scheme` y `data-theme`). Contraste AA medido (ver `tokens.json › color.contrast`). Una prueba verifica que `globals.css` siga a `tokens.json`.
- **Fuente:** Archivo Variable autoalojada (`@fontsource-variable/archivo`, ejes `wght` y `wdth`).
- **Base web:** Next 16.2.2 / React 19.2.4 exactos, Tailwind 4, Vitest, Playwright 1.56.1 (coincide con el Chromium 1194 preinstalado), Prism, openapi-typescript (`npm run gen:api`), recharts, lucide-react, clsx, jose. `package-lock.json` commiteado. `web/AGENTS.md` + `web/CLAUDE.md` con las reglas de Next 16 y del panel.
- **Auth web (01 §Autenticación):**
  - Server Action `login` (`src/app/login/actions.ts`): normaliza el teléfono a E.164, `POST /auth/login`, verifica que el rol sea ADMIN, guarda `authToken` y `refreshToken` httpOnly/SameSite=Lax/path `/` y la cookie `mustChangePassword` (de la respuesta o de `/auth/me`); redirige a `next` (solo rutas internas) o a `/cambiar-contrasena`.
  - `src/app/api/auth/refresh/route.ts` (GET para el proxy, POST JSON para `client-api`), serializado por token (una sola llamada a la API por token a la vez).
  - `src/app/api/auth/token/route.ts`: solo mismo origen (`Sec-Fetch-Site`/`Origin`), entrega un access fresco (refresca si quedan < 5 min).
  - `src/app/api/auth/logout/route.ts`: `POST /auth/logout {refreshToken}`, borra cookies, 303 a `/login?motivo=salida`.
  - `src/proxy.ts`: protege `/admin/**` y `/cambiar-contrasena` (ADMIN), refresh si el access venció, `/login?next=` sin sesión, `/login?motivo=rol` con otro rol, y `mustChangePassword` desde `/auth/me` (una vez; luego cookie). Sin `console.log`.
- **`src/lib/`:** `api.ts` (servidor), `client-api.ts` (navegador; reintenta una vez tras 401 vía refresh; conserva `detail`, `code`, `meta`), `errors.ts`, `env.ts`, `format.ts` (Caracas: `fmtUsd`, `fmtBs`, `fmtRate`, `fmtDate`, `fmtTime`, `fmtDateBig`, `fmtRelativeDay`…), `money.ts` (BigInt, sin float), `phone.ts`, `session.ts`, `jwt.ts`, `auth-guard.ts`, `idempotency.ts` (`useIdempotencyKey`), `use-debounced-value.ts`, `settings.ts`/`brand.ts` (nombre del negocio de `/settings/public`), `rates.ts`, `query.ts`.
- **UI kit `src/components/ui/`:** Button/IconButton, TextField/SelectField/TextAreaField, SearchField, FilterChips/SegmentedControl, Switch, StatusPill, MoneyText/BalanceFigure, ListRow/IconCircle/Avatar, Sheet (sobre `<dialog>`), ConfirmDialog (motivo obligatorio + opciones), DataTable (`nextCursor` + `onLoadMore`, `mobileRender`), Toast, Stepper, EmptyState, Skeleton/SkeletonRows, InlineAlert, PageHeader/Section/ActionBar, Spinner. Sin `FileUpload` ni `ConnectionBanner` (fuera de E1).
- **Layout:** `src/app/(admin)/layout.tsx` + `components/layout/{AdminShell,Sidebar,BrandMark}.tsx`: riel en escritorio, barra superior y barra inferior (Inicio, Clientes, Productos, Más) en el teléfono; nombre del negocio y tasa de hoy de la API.
- **`/login`** (DSN) con textos de `docs/design/admin.md §2`.
- **`/design`** (solo desarrollo; en producción 404 salvo `ENABLE_DESIGN_PAGE=1`): tokens, tipografía, botones, campos, dinero y estados, listas, tabla con cursor, vacíos, hojas y avisos, en claro y oscuro.
- **Pantallas de muestra** (datos de ejemplo, contra fixtures con forma de 08 marcadas `TODO(contrato)`): `/design/ficha` (ficha a 390 px con saldo grande, barra fija “Fiar productos / Registrar abono”, hojas de abono con “queda debiendo”, fiar con total en vivo simulado, estado de cuenta, anular y revertir con motivo y opción) y `/design/clientes` (lista a 1440 px con Por cobrar, buscador, chips, tabla aireada y “Cargar más”).
- **`docs/design/admin.md`:** navegación, estados comunes y **textos exactos** de todas las pantallas de E1.
- **`DESIGN.md`** + `.impeccable/design.json` (sidecar) escritos desde lo construido.
- **`web/railway.toml`:** RAILPACK, `npm ci && npm run build`, `next start` en `0.0.0.0:$PORT`, healthcheck `/login` (verificado: `/login` 200 aunque la API no responda).
- **CI:** `.github/workflows/web.yml` (lint, typecheck, test, build, `playwright test --list`; job `e2e-web` contra Prism que sube `capturas-web` y el reporte).

## Pruebas ejecutadas (comando → resultado)
```
cd web && npm ci                                  → ok
npm run lint                                      → eslint sin errores
npm run typecheck                                 → tsc --noEmit sin errores
npm test                                          → Test Files 7 passed (7) · Tests 72 passed (72)
npm run build                                     → ✓ Compiled successfully; rutas /, /login, /design*, /api/auth/{logout,refresh,token}; ƒ Proxy
npx playwright test --list                        → Total: 18 tests in 2 files
WEB_PORT=3000 PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers npx playwright test
                                                  → 16 passed, 2 skipped (local, Chromium preinstalado, next dev; sin Prism porque contracts/openapi.json aún no existe)
next start (smoke, sin API)                       → /login 200 · /design 404 · /admin 307 → /login?next=%2Fadmin · /api/auth/token 401
impeccable detect --json web/src                  → []
impeccable detect --json --viewport 390x844  /design/ficha /login /design /design/clientes   → []
impeccable detect --json --viewport 1440x900 /design/clientes /design /login /design/ficha   → []
```
Primera corrida del detector (antes de corregir): `low-contrast` blanco sobre la marca 3,7:1 (se tostó el naranja a #C94C0A → 4,64:1), `text-overflow` en títulos truncados de filas (ahora dos líneas), `cramped-padding` en dos enlaces de `/design` (corregido).
**Solo en CI:** `e2e-web` (Playwright con `next start` + Prism) corre en GitHub Actions; aquí se corrió con `next dev` y sin mock.

## Revisión final de Impeccable
Sin herramienta de subagentes en este entorno: el `impeccable-finish-reviewer` y el `impeccable-documenter` se corrieron en línea desde `reference/degraded/` (sustitución declarada). Construcción code-led (sin comp; la ronda G0.5 fue degradada y no dejó tarjeta QUALITY BAR). Capturas: `.impeccable/review/desktop.png` (lista a 1440), `mobile.png` (ficha a 390), `mobile-abono.png`, `design-desktop.png`, `design-mobile-dark.png`, `login-mobile.png` (gitignored; las sube `web.yml`).
```
disposition: fix
persistence: pass — PRODUCT.md, surface brief con contrato y seed key f47c700d; build code-led (sin state.json); DESIGN.md se escribe después.
fidelity: FIRST VIEWPORT match (nombre, “Debe” + monto a 48 px, Bs + chip Vencido, historial en filas, barra fija con “Registrar abono” negro);
  TYPE match (grotesca pesada, estrecha, tabular); MATERIAL match (plano, sin imitaciones); GROUND match (blanco y gris claro de OWN-WORLD);
  lista a 1440 = tabla aireada (adaptación: modo Operate, escaneo por columnas a 1440; filas de 64 px, no densa).
ceiling: sin tarjeta QUALITY BAR; momento propio (transición del saldo y hojas con “queda debiendo”) presente.
material_fixes: 1) nombre del negocio desborda el riel a 1440 → truncar; 2) separador “·” colgando al partir la línea de datos de la ficha;
  3) “Abona $X (Bs Y a tasa del dd/mm)” se parte en mitad del paréntesis en la hoja de abono.
keep: el saldo enorme con su rótulo y la barra de dos acciones al pulgar.
```
Pase de veredicto sobre las recapturas: 1) resuelto (trunca con “…”), 2) resuelto (datos como bloques sin separador), 3) resuelto (paréntesis en su línea). Regresiones: ninguna vista. `remaining: clear` → **disposition: ship** (cubre los tres arreglos puntuados, no es aprobación de todo E1).

## Endpoints / pantallas entregados
- Pantallas: `/login`, `(admin)/layout.tsx`, `/design`, `/design/ficha`, `/design/clientes`. Rutas web: `/api/auth/{refresh,token,logout}`. Raíz `/` → `/admin`.
- Consume (08): `POST /auth/login|refresh|logout`, `GET /auth/me`, `GET /settings/public`, `GET /rates/today`.

## Cambios a archivos compartidos (aditivos)
- `.impeccable/design.json` (nuevo: sidecar de DESIGN.md).
- `.github/workflows/web.yml` (nuevo; de DSN según 09).
- Nada en `api/`, `android/`, `contracts/`, `docs/plan/` ni `.gitignore` raíz (`web/.gitignore` propio para `e2e-capturas/`).

## Dependencias nuevas pedidas
Ninguna fuera de `web/package.json` (ya incluye todo lo que W-E1 necesita: recharts, openapi-typescript, @playwright/test, testing-library, clsx, lucide-react, jose, Prism).

## Decisiones por defecto tomadas
- **Forma del contrato asumida** (FND aún no publica `contracts/openapi.json`): `login`/`refresh` → `{accessToken, refreshToken, expiresIn?, user?{mustChangePassword}}` (si falta `expiresIn` se usa `exp` del JWT; si falta `user`, se consulta `/auth/me`); `refresh {refreshToken}`; `logout {refreshToken}` con Bearer; `/auth/me` → `{user{mustChangePassword}}`; `/settings/public.businessName`; `Rate{date, value, rateType, isFallback}`. Tipos locales marcados `TODO(contrato)` en `lib/brand.ts`, `lib/rates.ts` y los fixtures de `/design`.
- `mustChangePassword` se recuerda en una cookie httpOnly (`mustChangePassword=0|1`) para no llamar `/auth/me` en cada navegación; la API lo exige igual (CU-11).
- Sin API, la marca muestra el rótulo neutro “Panel” (nunca un nombre fijo).
- Naranja de marca #C94C0A (tostado) en vez de #E35A0F para que el blanco encima cumpla AA; sigue siendo provisional hasta el color del dueño.
- Nombres descriptivos de DESIGN.md (estrella polar “El cuaderno con factura de delivery”, nombres de color) son supuestos del documentador: no hubo entrevista.

## Pendiente / diferido
- `/admin` (Inicio), `/cambiar-contrasena` y el resto de pantallas de E1 son de **W-E1**; hasta que existan, tras el login `/admin` responde 404. `/cambiar-contrasena` debe llamar `writeSession(cookies, par, false)` al cambiar la contraseña.
- `npm run gen:api` (genera `src/lib/api-types.ts`) lo ejecuta el orquestador en G1; luego reemplazar los tipos `TODO(contrato)`.
- `e2e-web` con Prism solo puede correr cuando exista `contracts/openapi.json` (el config de Playwright arranca Prism solo si el archivo existe).
- Logo y color definitivos del dueño (el naranja es provisional).

## Solicitudes de cambio (rompen compatibilidad)
Ninguna. Pedidos a FND-E1 (no rompen): que `POST /auth/login` y `/auth/refresh` devuelvan `expiresIn` y `user.mustChangePassword`; que `POST /auth/logout` acepte `{refreshToken}`; y que `CORS_ORIGINS` incluya el dominio de web (el navegador llama a la API con Bearer desde `client-api`).

## Para el siguiente bloque
- W-E1: compón con `@/components/ui` (no edites `ui/**`, `lib/**` existentes, `globals.css`, `proxy.ts` ni `package.json`); helpers propios en `src/components/admin/lib/`. Toma `/design/ficha` y `/design/clientes` como punto de partida y `docs/design/admin.md` como fuente de textos.
- Formularios de dinero: `useIdempotencyKey()` al abrir la hoja, `clientFetch(path, { body, idempotencyKey })`, `useDebouncedValue(…, 300)` para `fiado/quote`, y `ApiError.detail` tal cual en `InlineAlert`.
- La ficha usa `ActionBar` (barra fija en el teléfono) y `BalanceFigure` (transición del saldo).
- Playwright de W-E1 va en `web/e2e/admin*` y reutiliza `playwright.config.ts` (proyectos `desktop` 1440 y `mobile` 390).
