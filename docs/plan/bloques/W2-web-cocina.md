# W2 — Web de producción (cocina)

**Fase:** 2 (paralelo) · **Esfuerzo:** S · **Rama:** `block/W2-web-cocina`

## Decisión: web en tablet, no app Android
La cocina usa la misma web (`/cocina`) en una **tablet o TV con navegador**, fija en esa pantalla. Ventajas: cero instalación, se actualiza sola, reutiliza autenticación y SSE, una app menos que mantener. (Ver cuestionario **[C-10]** si se prefiere app.)

## Objetivo
Que cuando un cliente pida, en cocina **suene y aparezca** “Nueva orden #1042 — Pedro Pérez” con sus productos, y que con un toque se marque **Listo**.

## Entradas
- F0 (`useEventStream`, layout pantalla completa, login por rol `PRODUCTION`).
- Handoff de B2 para pasar del mock a staging.

## Alcance
1. Tablero de pantalla completa: columnas **Nuevos · Preparando · Listos hoy**; tarjetas grandes legibles a 2 metros (número, cliente/negocio, hora, productos y cantidades en tipografía grande, notas resaltadas).
2. **Alerta**: sonido repetido + tarjeta parpadeando hasta que alguien la toque (“visto”). Botón para activar el audio al iniciar (los navegadores bloquean audio sin interacción).
3. Botones grandes **Preparando** (opcional) y **Listo** con opción de deshacer por 5 s.
4. Pedido cancelado: la tarjeta se marca en rojo “CANCELADO” y desaparece tras confirmarlo.
5. Pestaña **Total a producir** por fecha (hoy/mañana): producto → cantidad total.
6. Selector de fecha de entrega (hoy / mañana) **[C-6]**.
7. Robustez: reconexión automática SSE, recarga completa al reconectar, indicador “Sin conexión”, *Wake Lock* para que la pantalla no se apague, PWA instalable (manifest + ícono) para abrir a pantalla completa.
8. Sin montos de dinero.

## Fuera de alcance
Gestión de pedidos (crear/editar/cancelar), finanzas.

## Carpetas propias
`web/src/app/cocina/**` y sus tests.

## Limitantes
- Solo usuarios con rol `PRODUCTION` (o `ADMIN`).
- El mock de Prism no emite SSE: simular eventos con un generador local en modo desarrollo hasta tener B2 en staging.

## Oportunidades
- Muy poco código y alto impacto visible: buen candidato para la primera demo al dueño.
- Test Playwright que simula evento SSE y verifica sonido/tarjeta.

## Definición de terminado
- Funciona contra staging: crear pedido por API → aparece en < 2 s en `/cocina` → “Listo” → el pedido aparece asignado al motorizado.
- Capturas y video corto (Playwright) en el handoff.

## Prompt para lanzar este bloque
```
Eres el agente del bloque W2 del proyecto JM Cakes (repo edicsonbtos/jmcakes).
Lee CLAUDE.md, docs/plan/, docs/plan/bloques/W2-web-cocina.md, docs/handoffs/
(F0 y B2 si existe) y docs/CUESTIONARIO.md. Construye la pantalla de cocina en
web/src/app/cocina siguiendo docs/plan/05-protocolo-agentes.md (rama
block/W2-web-cocina, CI verde, handoff docs/handoffs/W2.md, STATUS.md).
```
