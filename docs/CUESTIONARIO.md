# Cuestionario de aclaraciones (v2)

## Respondidas por el dueño (2026-10-06)

| # | Pregunta | Respuesta |
|---|---|---|
| C-1 | Moneda | Precios en **USD**, mostrados en **Bs a tasa BCV**. |
| C-2 | Tasa | BCV automática con la lógica de OpenGravity (la manual del admin manda). |
| C-3 | Aprobación de clientes | **No requiere aprobación.** Todo cliente nuevo queda en **contado**. |
| C-4 | Contado: cuándo paga | Al terminar el pedido en la app. **Entra a cocina al aprobar el pago.** |
| C-5 | Verificación de pagos | **Manual, uno por uno**, como en OpenGravity. |
| C-6 | Programación | “Lo quiero hoy” o **fecha y hora personalizadas**; en cocina, la fecha en grande. |
| C-6b | Billetera insuficiente | **Usa el saldo y pide la diferencia**; si el pago se rechaza o se cancela el pedido, el saldo vuelve. |
| C-13 | Marca | Nombre por definir (“Panadería”, configurable); sin logo todavía. |
| C-21 | Clientes típicos | Perros calienteros, bodegas y abastos, cafeterías y restaurantes, eventos y particulares. |
| C-27 | Infraestructura | Proyectos **nuevos** en Neon y Railway (creados). |
| C-29 | Ejecución | Enjambre de **10 agentes** por fases, con pruebas; plan auditado dos veces. |

## Pendientes (no bloquean: los agentes usan el valor por defecto)

| # | Pregunta | Valor por defecto |
|---|---|---|
| C-7 | Días de crédito y desde cuándo corren | 7 días por cliente, contados desde la fecha de entrega programada. |
| C-23 | Deuda vencida | Bloquea pedidos si hay facturas vencidas hace más de 7 días. |
| C-9 | Faltante en cocina | Solo el admin reduce el pedido antes de “Listo”; la diferencia vuelve a la billetera o reduce la deuda. |
| C-14 | Métodos de pago y datos | Pago móvil Bs, transferencia Bs, Zelle, efectivo USD (se cargan en Configuración). |
| C-16 | Costo de delivery | $0 (configurable). |
| C-17 | Horario | Pedidos programables de 06:00 a 19:00; 60 min de anticipación mínima; hasta 30 días. |
| C-19 | Mínimos | Mínimo por producto; sin mínimo por pedido. |
| C-20 | Factura fiscal | No en v1. |
| C-22 | Datos a migrar | Se importan por CSV cuando el dueño los entregue. |
| C-24 | Varios administradores | Todos con control total. |
| C-25 | Avisos por WhatsApp | No en v1 (solo botón “Escribir por WhatsApp”). |
| C-11 | Dominio propio | Dominios de Railway hasta tener uno. |
| C-12 | Cuenta de Google Play | Se asume personal (prueba cerrada de 12 testers × 14 días). |
| C-28 | Firebase (push) | Lo crea el dueño; mientras tanto el push queda desactivado sin romper nada. |
| C-30 | Auto-cancelación de pedidos impagos | A las 24 h (o antes de la hora programada), salvo que haya un pago en revisión. |
| C-31 | Retiro en tienda (pickup) | No: todo es delivery en v1. |
