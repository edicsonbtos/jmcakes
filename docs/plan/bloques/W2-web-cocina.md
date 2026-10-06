# W2 — Web: pantalla de producción (cocina)

**Fase 1** · **Rama** `block/W2` · Diseño: `DESIGN.md` y `docs/design/cocina.md` · Skill: `impeccable`

## Objetivo
En una tablet o TV de pared, legible a 2 metros: **qué hacer, para cuándo y en qué cantidad**. Un pedido nuevo **suena y se ve**; “Listo” es un toque.

## Alcance (`/cocina`)
1. **Hoy**
   - Columnas **Nuevos · Preparando · Listos**, ordenadas por `dueAt`.
   - Tarjetas grandes con:
     - **#número** y cliente o negocio;
     - **hora grande**, con el chip “Para ya” (ASAP) o “Programado 3:00 pm”;
     - **“Atrasado”** si corresponde;
     - productos y cantidades en tipografía grande;
     - notas resaltadas.
2. **Programados:** pedidos de días futuros, agrupados con la **fecha en grande** (“JUEVES 9 OCT”). Se pueden empezar antes (Preparando).
3. **Total a producir:** selector Hoy, Mañana o fecha → tabla de producto y cantidad.
4. **Tiempo real**
   - `useEventStream` (DSN) con `order.confirmed`, `order.updated` y `order.cancelled`.
   - Al reconectar, recarga completa.
   - Banner “Sin conexión”.
5. **Alerta:** botón inicial “Activar sonido” (política de autoplay). Sonido repetido y tarjeta resaltada hasta tocarla (“visto”, guardado localmente).
6. **Acciones**
   - **Preparando** y **Listo**, con un “Deshacer” de 5 s antes de enviar.
   - Pedido cancelado: tarjeta en rojo “CANCELADO” hasta confirmarla.
7. **PWA y pantalla:** PWA instalable (manifest e ícono), Wake Lock y modo pantalla completa. **Cero montos de dinero.**

## Contra qué construir
Mock de Prism para REST. **Prism no emite SSE**, así que se agrega un simulador de eventos solo en desarrollo (`?simular=1`). Q1 conecta con la API real.

## Pruebas exigidas
- Vitest del agrupado Hoy/Programados con zona Caracas (pedido de las 23:30).
- Playwright: el evento simulado aparece en Nuevos; Listo con deshacer; vista de Programados con fecha grande.
- Capturas en tablet horizontal (1280×800) y TV (1920×1080) en `docs/handoffs/assets/W2-*.png`.
- `impeccable detect` sin críticos.

## No tocar
`src/app/(admin)`, `src/components/ui` y `src/lib` (solo aditivo y declarado), `api/`, `android/`.
