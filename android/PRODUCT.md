# Product

<!-- impeccable:product-schema 1 -->

## Platform

android

Este archivo cubre las apps nativas (cliente y motorizado). El `PRODUCT.md` raíz cubre las superficies web. Las cuatro superficies sobre una sola API:

- **Panel del administrador**: web (escritorio y teléfono).
- **Pantalla de producción (cocina)**: web en tablet o TV, fija en la pared.
- **App del cliente mayorista**: Android nativa (Jetpack Compose, Material 3), en Play Store.
- **App del motorizado**: Android nativa (Jetpack Compose, Material 3), APK fuera de Play Store.

## Stack

Decidido por el dueño: reutilizar el stack de su proyecto OpenGravity.

- **API:** FastAPI + SQLAlchemy 2 async + Alembic.
- **Base de datos:** Neon Postgres.
- **Web:** Next.js 16 + Tailwind 4.
- **Android:** Kotlin + Jetpack Compose.
- **Hosting:** Railway.

## Users

- **Dueño / administrador.** Controla el negocio desde el teléfono o la computadora: aprueba pagos uno por uno (verificando en su banco), revisa cuánto le deben, sube y baja precios según la tasa y ve los ingresos del día. Interrumpido todo el día, decide rápido.
- **Producción (cocina).** Panaderos con las manos ocupadas y enharinadas, a 1–2 metros de una tablet. Necesitan saber **qué hacer, para cuándo y en qué cantidad**, y marcar “Listo” con un toque.
- **Motorizado (uno solo).** En la calle, con el teléfono en la mano y mala señal. Necesita **a dónde ir, a quién entregar y qué llevar**; solo marca “En camino” y “Entregado”.
- **Cliente mayorista.** Perros calienteros, bodegas y abastos, cafeterías y restaurantes, y particulares con pedidos para eventos. Piden lo mismo casi todos los días o programan para una fecha y hora. Usan teléfonos Android de gama baja o media, con datos móviles inestables. Pagan por pago móvil o transferencia en bolívares a tasa BCV, o en dólares.

## Product Purpose

Que un pedido mayorista pase de la app a la cocina, de la cocina al motorizado y del motorizado a “entregado” sin llamadas ni WhatsApp. Al mismo tiempo, que cada dólar quede contabilizado: pagos verificados, billetera de saldo a favor y cuentas por cobrar de los clientes con crédito.

Éxito: el dueño deja de anotar pedidos y deudas a mano, cocina produce solo lo pagado o aprobado a crédito, y el cliente sabe en todo momento cuánto tiene a favor y cuánto debe.

## Positioning

Es la panadería de barrio con la operación de una app de delivery:

- **Pedido programado:** “lo quiero hoy” o fecha y hora exactas.
- **Billetera prepagada:** se descuenta sola.
- **Crédito controlado por cliente.**
- **Pagos venezolanos reales:** pago móvil, transferencia y Zelle, verificados a mano como ya lo hace el dueño en OpenGravity.

## Operating Context

- Precios en **USD**, mostrados también en **Bs a tasa BCV del día**. La tasa manual del admin tiene prioridad.
- Hora de **Caracas** (UTC−4) para todo.
- **El cliente se registra sin aprobación** y queda en modo **contado**. El admin puede habilitarle **crédito** con límite y días.
- **Contado:**
  - Al terminar el pedido, si la billetera alcanza, se descuenta sin preguntar.
  - Si no alcanza, usa el saldo y pide la diferencia con los datos de pago, el número de referencia y el comprobante.
  - El pedido entra a cocina solo cuando el admin aprueba el pago.
- Pedidos “lo quiero hoy” o **programados con fecha y hora**. En cocina, los programados aparecen con la fecha en grande.
- Cocina en una tablet o TV de pared. Motorizado en la calle con señal irregular.

## Capabilities and Constraints

- Un solo motorizado; los pedidos listos se le asignan solos. Sin mapas, rutas ni aceptación de pedidos.
- Pagos aprobados **manualmente** por el admin, como en OpenGravity.
- La cocina no ve montos de dinero.
- Sin facturación fiscal en v1.
- **Abierto:** nombre comercial definitivo (por ahora “Panadería”, configurable), logo y colores de marca, costo de delivery, horario de operación.

## Brand Commitments

- El nombre se muestra desde la configuración (`business.name`, por defecto “Panadería”) y el logo es reemplazable. Ninguna pantalla debe tener el nombre fijo en el código.
- Voz: español de Venezuela, cercano y directo (“Tu pedido va en camino”), sin tecnicismos ni anglicismos innecesarios.

## Evidence on Hand

- No hay logo, fotos de productos, testimonios ni datos de clientes todavía. **No inventar** testimonios, reseñas ni cifras.
- El catálogo inicial (canilla, pan campesino, pan dulce, cachito, golfeado, etc.) es de ejemplo y lo reemplaza el dueño.

## Product Principles

1. **Lo urgente primero.** Cada pantalla responde a una sola pregunta: “¿qué hago ahora?”.
2. **El dinero nunca es ambiguo.** Saldo a favor, deuda y monto a pagar siempre visibles, en USD y en Bs, con su estado (por verificar, aprobado, rechazado).
3. **Funciona con mala señal.** Las acciones se reintentan, los pedidos y pagos no se duplican, y siempre se ve qué está pendiente de enviar.
4. **Un toque para lo frecuente.** Repetir el pedido de ayer, marcar “Listo”, marcar “Entregado”, aprobar un pago.

## Accessibility & Inclusion

- Toques de 48 dp mínimo; en cocina y delivery, botones mucho más grandes.
- Texto legible a 2 metros en cocina.
- Contraste WCAG AA.
- Soporte de tamaño de fuente del sistema en Android.
- Nada debe depender solo del color: los estados llevan texto.
