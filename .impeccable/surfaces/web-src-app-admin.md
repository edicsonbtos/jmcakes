---
version: 1
slug: "web-src-app-admin"
primary_target: "web/src/app/(admin)"
related_targets: []
---

# Panel del administrador

**Modo:** Operate. El dueño fía, cobra y revisa saldos desde el teléfono en el mostrador, interrumpido, con luz de día o fluorescente; de noche revisa en la computadora.

**Tarea de E1:** cuaderno de clientes (ficha, fiar, abonar, anular/revertir, estado de cuenta), productos y precios, tasa, inicio, configuración. Ver docs/plan/09.

**Decisión del dueño (2026-10-20):** salida estándar, con Uber y Rappi como vara de calidad. Ronda degradada (sin catálogo); se mostraron Fisicromía, Ticket de caja y Panel estándar.

## Direction contract
THESIS: El cuaderno de fiado con la factura de una app de delivery: cada cliente es una ficha con su saldo enorme y dos acciones al pulgar. Rechaza el panel de tarjetas KPI y tablas densas.
OWN-WORLD: Blanco y gris claro, tinta negra, botón primario negro, un naranja de horno solo para marca y selección; rojo “Debe”, verde “A favor”. Grotesca con cifras tabulares, títulos y montos muy pesados. Hojas inferiores, filas con ícono circular, chips de filtro.
STORY: El dueño encuentra al cliente, ve cuánto debe y fía o cobra en menos de 15 s, viendo el saldo resultante antes de confirmar.
FIRST VIEWPORT: Ficha a 390 px: nombre arriba; “Debe” y el monto a 48 px; Bs y chip “Vencido” debajo; historial en filas; barra fija inferior con “Fiar” y “Registrar abono” (negro).
FORM: canon (salida estándar), referencia Uber/Rappi; seed key f47c700d.
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Momento propio
Fiar y abonar son hojas inferiores con el total en vivo de la API (`quote`) y una confirmación “queda debiendo $Z”; el monto de la ficha transiciona al nuevo saldo.

## Pendiente
- Logo y color de marca del dueño (el naranja es provisional).
