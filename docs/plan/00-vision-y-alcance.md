# 00 — Visión, alcance y decisiones del dueño

> Plan **v2**. Incorpora las respuestas del dueño del 2026-10-06 y la decisión de **reutilizar OpenGravity** (su sistema de préstamos en producción) en vez de reinventar el manejo de dinero. Producto descrito para diseño en [`PRODUCT.md`](../../PRODUCT.md).

## Objetivo

Plataforma para una panadería en Caracas con cuatro roles:

| Rol | Superficie | Qué hace |
|---|---|---|
| **Administrador** | Web `/admin` | Control total: clientes, catálogo y precios, crédito, billeteras, **aprobación manual de pagos**, cuentas por cobrar, dashboards, cierres diarios. |
| **Producción** | Web `/cocina` (tablet/TV) | Cola en vivo de pedidos confirmados (“Hoy” y “Programados” con la fecha en grande), **Preparando** y **Listo**. |
| **Motorizado** | App Android (APK) | Recibe automáticamente los pedidos listos; **En camino** y **Entregado**. |
| **Cliente mayorista** | App Android (Play Store) | Registro sin aprobación, catálogo, pedido para hoy o programado, pago con billetera o reporte de pago, seguimiento, crédito si el admin lo habilita. |

## Decisiones confirmadas por el dueño

| # | Decisión |
|---|---|
| D-1 | **Precios en USD** y se muestran también en **Bs a tasa BCV**. Tasa del día con `rate_for(fecha)`: la MANUAL de esa fecha; si no hay, la BCV de esa fecha (DolarAPI oficial, como en OpenGravity); si no hay, la más reciente anterior. La misma función sirve para mostrar Bs y para convertir pagos (03 §0). |
| D-2 | **Registro sin aprobación.** Todo cliente nuevo queda en modo **contado** (`CASH`). El admin puede habilitar **crédito** (`CREDIT`) con límite y días. |
| D-3 | **Pedidos programados:** “Lo quiero hoy” (lo antes posible) o **fecha y hora** personalizadas. Producción los ve en cola con la **fecha en grande**. |
| D-4 | **Contado:** paga al terminar el pedido en la misma app. Si la billetera alcanza, **se descuenta sin preguntar**. Si no alcanza, **usa el saldo y pide la diferencia**: muestra los datos de pago y pide número de referencia y comprobante. |
| D-5 | El pedido de contado **entra a cocina al aprobar el pago**. Si el pago se rechaza o el pedido se cancela, lo descontado vuelve a la billetera. |
| D-6 | **Cada pago se aprueba manualmente**, como en OpenGravity (`PENDING_REVIEW` → `IN_REVIEW` → `APPROVED`/`REJECTED`, y `REVERSED` para revertir). |
| D-7 | **Billetera recargable:** el cliente reporta un pago de recarga; al aprobarse suma saldo; el saldo paga pedidos y deudas automáticamente. |
| D-8 | Crear proyectos **nuevos** en Neon y Railway (hecho: Neon `jmcakes` en la org personal, Railway `jmcakes`, entorno `staging`). |
| D-9 | Ejecución con un **enjambre de 10 agentes** por fases, con pruebas, y el plan **auditado dos veces** antes de ejecutar. |
| D-10 | Diseño definido con la skill **Impeccable** (copiada de OpenGravity a `.claude/skills/impeccable`). |
| D-11 | Nombre comercial **no definido**: “Panadería” por defecto y configurable (`business.name`), logo reemplazable. |
| D-12 | Clientes típicos: perros calienteros, bodegas y abastos, cafeterías y restaurantes, eventos y particulares. |

## Alcance v1

| Módulo | Incluido |
|---|---|
| Auth y roles | ADMIN, PRODUCTION, DELIVERY, CUSTOMER. Teléfono + contraseña. JWT (patrón de OpenGravity) + refresh. |
| Catálogo | Categorías, productos con foto, precio USD, unidad, mínimo por producto, publicar/ocultar, agotado hoy, **cambio masivo de precios** con vista previa, historial. |
| Clientes | Registro libre (contado). Admin: crédito (límite, días), bloqueo, creación de clientes sin app, ficha con estado de cuenta. |
| Pedidos | “Hoy” o programado (fecha+hora), repetir pedido, cancelar, máquina de estados, creación por el admin. |
| Pagos | Métodos de pago y cuentas bancarias de OpenGravity, reporte con referencia + comprobante, aprobación/rechazo/reverso manual, idempotencia, referencia única. |
| Billetera y CxC | Billetera del cliente (ledger solo-inserción), pago automático de pedidos y deudas, cuentas por cobrar de crédito con vencimiento, cargos y abonos manuales. |
| Cuentas del negocio | Saldos por cuenta real de cobro (Banco Bs, Zelle, efectivo) reutilizando las “wallets” de OpenGravity. |
| Producción | Tablero en vivo (SSE) con sonido, Hoy / Programados, “Total a producir” por día. |
| Delivery | Auto-asignación al único motorizado, En camino / Entregado, llamar / WhatsApp / abrir dirección en Maps (texto). |
| Dashboard y cierres | Ingresos del día por método/cuenta, ventas, CxC, pagos por verificar, top productos, **cierre diario** con PDF (de OpenGravity). |
| Tasa | Sincronización BCV diaria (06:00) y tasa manual del admin (de OpenGravity). |
| Notificaciones | Push FCM (cliente y motorizado); SSE (cocina y admin). |

## Fuera de alcance v1
Mapas y rutas, varios motorizados, pasarela de pago automática, facturación fiscal, inventario y recetas, POS de mostrador, iOS, bot de Telegram.

## Métrica de éxito
Recorridos verificados por pruebas end-to-end (ver [07-pruebas](07-pruebas.md)):
1. Contado con billetera suficiente: el pedido llega a cocina sin intervención del admin.
2. Contado con billetera parcial: reporte de la diferencia → aprobación → cocina → listo → motorizado → entregado.
3. Crédito: pedido confirmado al instante → deuda → recarga aprobada → deuda saldada y sobrante en billetera.
4. Pedido programado para dentro de 3 días: visible en cocina con la fecha en grande; entra a “Hoy” el día que toca.
