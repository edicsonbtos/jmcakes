# W2 — Web: pantalla de producción (cocina)

**Fase 1** · rama `block/W2` · `WEB_PORT=3002`, `MOCK_PORT=4012` · diseño `DESIGN.md` + `docs/design/cocina.md` · skill **impeccable**

## Objetivo
En una tablet o TV de pared, legible a 2 m: **qué hacer, para cuándo y cuánto**. Un pedido nuevo suena y se ve; “Listo” es un toque. La pantalla **funciona todo el día sin volver a iniciar sesión**.

## Alcance (`/cocina`)
1. **Hoy:** columnas Nuevos · Preparando · Listos, ordenadas por `dueAt`. Tarjeta (`KitchenCard`):
   - #número y cliente;
   - **hora grande**, con el chip “Para ya” o “Programado 3:00 pm”;
   - “Atrasado” si aplica;
   - productos y cantidades en grande;
   - notas resaltadas.
2. **Programados:** agrupados por día con la **fecha en grande**. Se pueden empezar antes.
3. **Total a producir:** Hoy, Mañana o una fecha.
4. **Tiempo real:**
   - `useEventStream` (de DSN) con los eventos `order.confirmed`, `order.updated` y `order.cancelled`;
   - reconexión con token nuevo y `lastEventId`;
   - con `reset`, recarga completa;
   - banner “Sin conexión”.
5. **Alerta:** “Activar sonido” al iniciar. El sonido de `web/public/sounds/nuevo-pedido.mp3` se repite y la tarjeta queda resaltada hasta tocarla (“visto” en `localStorage`, con try/catch).
6. **Acciones:** Preparando y Listo, con “Deshacer” de 5 s antes de enviar. Si el pedido se cancela, la tarjeta muestra “CANCELADO” en rojo hasta confirmar.
7. **PWA y pantalla:** PWA con `web/public/cocina/manifest.webmanifest` (de DSN; W2 puede ajustarlo dentro de `web/public/cocina/**`). Wake Lock y pantalla completa. **Cero montos.**
8. **Sesión larga:** la cocina sigue operando tras vencer el access token (refresh de DSN).

## Contra qué construir
Prism para REST (`MOCK_PORT=4012`). **Prism no emite SSE**: con `?simular=1` y solo en desarrollo, un simulador emite eventos usando `EventEnvelope` y `OrderEventData` de `api-types.ts`.

## Pruebas exigidas
- Vitest: agrupado Hoy/Programados con zona Caracas (pedido de las 23:30) y lógica de “Atrasado”.
- **Playwright** (lo corre el CI):
  - un evento simulado aparece en Nuevos;
  - Listo con deshacer;
  - Programados con la fecha grande;
  - **reloj adelantado 31 min**: sigue en `/cocina` y el SSE reconecta.
  - Capturas en 1280×800 y 1920×1080.
- Local: `npm run lint && npm test && npm run build && npx playwright test --list`.
- `impeccable detect` sin críticos.

## No tocar
`src/app/(admin)`, `src/components/{ui,admin,layout}`, archivos existentes de `src/lib`, `package.json`, `api/`, `android/`.
