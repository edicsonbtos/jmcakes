# W1 — Web backoffice del administrador

**Fase:** 2 (paralelo; arranca contra el mock al terminar F0) · **Esfuerzo:** L · **Rama:** `block/W1-web-admin`

## Objetivo
El panel desde el cual el dueño **controla todo el negocio** en el navegador: dashboard del día, pedidos, producción y delivery en vivo, clientes y crédito, catálogo y precios, cobranza.

## Entradas
- F0 fusionado (`web/src/shared`, cliente API tipado, mock con `pnpm mock`).
- Handoffs de B1, B2, B3 cuando estén (para pasar de mock a staging).

## Pantallas (rutas `/admin/...`)
1. **Inicio / Dashboard**: tarjetas (ingresos del día, ventas del día, CxC total detal/mayorista, pagos por verificar), pedidos por estado en vivo (SSE), top productos, top deudores, botón “Cierre del día” (CSV/imprimir). Selector de fecha.
2. **Pedidos**: tabla filtrable (estado, fecha de entrega, cliente, canal), detalle con líneas, bitácora y acciones (cancelar con motivo, editar antes de “Listo”), **crear pedido para un cliente** (pedidos por teléfono/WhatsApp). Vista tablero en vivo como la de cocina, pero con montos.
3. **Clientes**: listado (tipo, modo contado/crédito, deuda, billetera, estado), bandeja **“Por aprobar”**, ficha del cliente con pestañas: datos · crédito (modo, límite, días) · estado de cuenta · pedidos · pagos. Acciones: aprobar, bloquear, cargo manual, abono manual, ajuste.
4. **Cobranza**: **pagos por verificar** (con foto del comprobante, aprobar/rechazar, editar tasa), CxC global con antigüedad, exportar CSV.
5. **Catálogo**: categorías; productos con foto (subida directa al bucket), publicar/ocultar, agotado hoy, pedido mínimo; **cambio masivo de precios con vista previa**; historial de precios.
6. **Configuración**: datos del negocio, hora de corte, motorizado asignado, reglas de crédito, tasa del día, usuarios internos (producción/delivery).

## Requisitos de UX
- Español, montos `$ 12,50` y `Bs. 456,78` (formato venezolano: coma decimal) **[C-1]**; horas en Caracas.
- Responsive: usable en laptop y en teléfono (el dueño revisa desde el celular).
- Notificación sonora/visual opcional en el admin al entrar pedido nuevo o pago por verificar.
- Confirmación en acciones de dinero; mensajes de error usando `error.message` del API.

## Fuera de alcance
La vista de cocina (W2). Lógica de negocio (vive en la API).

## Carpetas propias
`web/src/app/admin/**` y sus tests. Cambios aditivos en `web/src/shared` documentados.

## Limitantes
- Trabajar contra el **mock** mientras B1–B3 no estén en staging; el mock no tiene estado (crear no persiste): está bien para construir UI; los flujos reales se validan después contra staging.
- No inventar campos: si falta algo en el contrato, agregarlo aditivamente y avisar en el handoff.

## Oportunidades
- shadcn/ui `DataTable` + TanStack Table para todas las tablas.
- **Playwright** con capturas de pantalla de cada pantalla para el handoff (sirven para que el humano revise sin abrir nada).
- Modo oscuro gratis con Tailwind.

## Definición de terminado
- Todas las pantallas funcionando contra **staging** (no solo mock) con los flujos de B1–B3.
- Tests de componentes clave y E2E Playwright de: aprobar cliente, cambiar precio masivo, aprobar pago y ver bajar la deuda.
- Capturas en el handoff.

## Siguiente
Insumo para **Q1**.

## Prompt para lanzar este bloque
```
Eres el agente del bloque W1 del proyecto JM Cakes (repo edicsonbtos/jmcakes).
Lee CLAUDE.md, docs/plan/, docs/plan/bloques/W1-web-admin.md, docs/handoffs/
(F0 y los B* que existan) y docs/CUESTIONARIO.md. Construye el backoffice en
web/src/app/admin. Si B1–B3 aún no están en staging, trabaja contra el mock
(pnpm mock) y cambia a staging cuando sus handoffs lo indiquen. Sigue
docs/plan/05-protocolo-agentes.md (rama block/W1-web-admin, CI verde, capturas
Playwright y handoff docs/handoffs/W1.md, STATUS.md).
```
