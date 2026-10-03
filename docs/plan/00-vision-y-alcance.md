# 00 — Visión y alcance

## Problema

La panadería vende a dos tipos de clientes y hoy no tiene un sistema que conecte la venta, la producción, el despacho y la cobranza:

- **Clientes del negocio (detal / mostrador)**: compran en el local; algunos compran fiado y generan cuentas por cobrar.
- **Clientes mayoristas**: compran volumen (canillas, panes, etc.); algunos pagan de contado y otros tienen **línea de crédito**.

## Objetivo

Una plataforma única donde:

1. El **cliente mayorista** pide desde una app Android sencilla.
2. El pedido llega al instante a **producción** (“Nueva orden — Pedro Pérez: 4 canillas, 5 panes…”), como en las apps de delivery.
3. Cuando producción marca **Listo**, el pedido se asigna automáticamente al **único motorizado**, que solo marca **En camino** y **Entregado**.
4. El **administrador** controla todo desde la web: catálogo y precios, clientes, crédito, billeteras, cuentas por cobrar, pagos y dashboards del día.

## Principios (no negociables)

- **Sin sobreingeniería.** Un solo motorizado, sin rutas, sin mapas, sin aceptación de pedidos. Un solo backend, una sola base de datos, una sola web.
- **Sencillo e intuitivo** para el cliente: pocas pantallas, botones grandes, español de Venezuela.
- **El dinero es un libro contable (ledger).** Nunca se edita un saldo a mano; todo movimiento es un asiento trazable.
- **Hora de Caracas** (`America/Caracas`, UTC−4, sin horario de verano) para todo lo que el usuario ve: “día”, cierres, reportes.
- **Construido por agentes de IA autónomos** en bloques independientes, con un contrato de API como fuente de verdad.

## Alcance v1 (MVP)

| Módulo | Incluido |
|---|---|
| Autenticación y roles | Admin, Producción, Delivery, Cliente. JWT + refresh. |
| Catálogo | Categorías, productos con foto, precio, unidad, pedido mínimo, publicar/ocultar, subir/bajar precios. |
| Clientes | Tipos detal y mayorista; aprobación de registros; modo **contado** o **crédito**; límite de crédito; bloqueo. |
| Pedidos | Crear desde la app (o desde la web por el admin), máquina de estados, cancelación. |
| Producción | Cola en tiempo real con alerta sonora, “Preparando” (opcional) y “Listo”. |
| Delivery | Auto-asignación, lista de pedidos con cliente/dirección/teléfono, “En camino”, “Entregado”. |
| Finanzas | Billetera por cliente, cuentas por cobrar (facturas por pedido), reporte de pagos desde la app, verificación por el admin, aplicación automática billetera → deuda (FIFO), cargos y abonos manuales. |
| Dashboards | Ingresos del día, ventas del día, CxC total y por tipo de cliente, deudores, pedidos por estado, productos más vendidos. |
| Notificaciones | Push (FCM) a cliente y motorizado; tiempo real (SSE) a cocina y admin. |

## Fuera de alcance v1

- Rutas, mapas, GPS, tracking en vivo, múltiples motorizados.
- Pasarela de pago automática (los pagos se reportan y el admin los verifica).
- Facturación fiscal SENIAT / máquina fiscal.
- Inventario de materia prima y recetas (costeo).
- App iOS.
- Punto de venta (POS) completo de mostrador (ver cuestionario: se puede agregar un registro simple de ventas de mostrador).

## Métrica de éxito del MVP

Un pedido de un mayorista con crédito recorre **app → cocina → motorizado → entregado** y su deuda aparece en CxC; al reportar y aprobarse un pago, la deuda baja sola. Todo esto visible en el dashboard del día en hora de Caracas.
