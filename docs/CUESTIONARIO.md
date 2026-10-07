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
| C-32 | Cliente de contado con deuda (por pago revertido, fiado o crédito anterior) | No puede pedir hasta pagarla (`OPEN_DEBT`). |
| C-33 | Bloquear a un cliente | Se cancelan sus pedidos que esperan pago; los pagos en revisión siguen y su dinero queda a favor. |
| C-34 | Ventana mínima para pagar un pedido | 30 min (también tras un rechazo). |
| C-35 | Devolver saldo a favor en dinero | Lo hace el admin desde la ficha del cliente; queda como egreso en la cuenta elegida. |
| C-36 | Perdonar deuda | “Condonar” deja la deuda en lo ya pagado, sin devolver nada. “Anular” solo aplica a cargos manuales y reversos. |

## Decisión pendiente del dueño (importante)

| # | Pregunta | Recomendación |
|---|---|---|
| C-37 | El repo `jmcakes` es **público** y va a contener código adaptado de OpenGravity, que es **privado** (lógica de pagos y seguridad). ¿Lo hacemos privado? | **Hacerlo privado.** Play Store no exige que sea público. Mientras tanto, los agentes sanean todo lo que copian y CI corre `gitleaks`. |

## Requiere al dueño (no lo puede hacer un agente)
1. **Railway ↔ GitHub:** instalar o verificar la GitHub App de Railway con acceso a `edicsonbtos/jmcakes`, y **aprobar los despliegues** (`accept-deploy`) de staging y luego de producción.
2. **Firebase:** crear el proyecto para las notificaciones push y entregar `google-services.json` (apps) y `FCM_CREDENTIALS_JSON` (API).
3. **Google Play Console:** cuenta (25 USD) y 12 testers durante 14 días para la prueba cerrada, si la cuenta es personal.
4. **Firma Android:** generar los keystores y cargarlos como secretos de GitHub.
5. **Dominio propio** (opcional).
6. **Datos reales:** catálogo, precios, métodos de pago con sus cuentas, clientes y deudas actuales (CSV).

7. **Entorno `production`** en Railway y la rama `main` de Neon: aprobar su creación antes del primer despliegue a producción.
8. **Llaves VAPID** (Web Push al panel): las genera el orquestador. Solo hace falta que el dueño instale el panel como app (PWA) en su teléfono y acepte las notificaciones.

## Exposición del código privado (importante)
Los primeros commits de este repo **público** ya publicaron, en `docs/plan/`, descripciones de defectos concretos del código de OpenGravity. Desde la v2.3 esos detalles se movieron a una nota privada fuera del repo, pero **siguen en el historial de git**. Opciones (todas requieren tu decisión):
- **(Recomendado)** Hacer privado el repo `jmcakes` y corregir esos puntos en OpenGravity.
- Reescribir la historia del repo para borrarlos (acción destructiva: solo con tu autorización expresa).
