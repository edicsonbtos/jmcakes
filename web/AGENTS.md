<!-- BEGIN:nextjs-agent-rules -->
# Este no es el Next.js que conoces

Next.js 16.2.2: APIs, convenciones y estructura cambiaron (p. ej. `middleware` ahora es `src/proxy.ts`, siempre en Node; `cookies()`, `headers()`, `params` y `searchParams` son asíncronos; `next lint` ya no existe). Lee la guía correspondiente en `node_modules/next/dist/docs/` antes de escribir código.
<!-- END:nextjs-agent-rules -->

# Web del panel — reglas para agentes

- **Comandos:** `npm ci && npm run lint && npm run typecheck && npm test && npm run build && npx playwright test --list`.
  Playwright completo: `npx playwright test` (en el contenedor, con `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers`; nunca `playwright install`).
- **Puertos** por agente (docs/plan/05 §1): `WEB_PORT` y `MOCK_PORT`. `npm run dev` y `npm run mock` los leen.
- **Dinero:** la web no calcula montos. Los Bs vienen de la API; `lib/money.ts` solo valida lo que se escribe y formatea. Prohibido `parseFloat` (ESLint lo bloquea).
- **Tiempo:** todo se muestra en `America/Caracas` con `lib/format.ts`.
- **Errores:** se muestra el `detail` de la API tal cual (`ApiError`).
- **Sesión:** cookies httpOnly; en el navegador, `clientFetch` (lib/client-api.ts). En el servidor, `apiFetch` (lib/api.ts). Ninguna ruta recibe tokens del navegador.
- **Idempotencia:** `useIdempotencyKey()` al abrir el formulario; la misma llave en cada reintento.
- **UI:** solo el kit de `src/components/ui` y los tokens de `globals.css` (sin colores sueltos). Ver `DESIGN.md` y `docs/design/admin.md`.
- **Congelados tras DSN** (docs/plan/05 §3): `package.json` y lockfile, `src/lib/**` (solo agregar), `src/components/ui/**`, `src/app/globals.css`, `src/proxy.ts`, `public/**`.
- **Contrato:** `src/lib/api-types.ts` lo genera solo el orquestador (`npm run gen:api`). Mientras falte un campo, fixture local marcado `TODO(contrato)`.
