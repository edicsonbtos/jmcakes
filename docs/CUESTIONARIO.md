# Cuestionario de aclaraciones

Responde directamente en este archivo (en la línea **Respuesta:**) o en el chat. Cada pregunta tiene un **valor por defecto**: si no se responde, los agentes lo usan y lo anotan en su handoff.

Las preguntas marcadas 🔴 **afectan el esquema de la base de datos o el contrato** y conviene responderlas **antes de lanzar F0**. Las 🟡 se necesitan antes de la Fase 1/2. Las 🟢 pueden esperar hasta el lanzamiento.

---

## A. Dinero y cobranza

**C-1 🔴 ¿En qué moneda se fijan los precios y se lleva la deuda?**
Opciones: (a) USD, y los pagos en Bs se convierten a la tasa del día · (b) Bs · (c) ambas por separado (dos billeteras).
*Por qué importa:* define cómo se guardan todos los montos y cómo se muestra la deuda.
**Por defecto:** (a) USD como moneda base, mostrando el equivalente en Bs.
**Respuesta:**

**C-2 🟡 ¿Qué tasa de cambio se usa y quién la carga?**
Opciones: (a) el admin la escribe cada mañana · (b) se toma automáticamente la tasa oficial BCV · (c) tasa propia del negocio distinta a la BCV.
**Por defecto:** (a) manual, con la opción de automatizar BCV más adelante.
**Respuesta:**

**C-3 🔴 ¿Un cliente que se registra en la app puede pedir de inmediato o necesita aprobación del admin?**
**Por defecto:** necesita aprobación; al aprobarlo, el admin elige contado o crédito.
**Respuesta:**

**C-4 🔴 Clientes de contado: ¿cuándo pagan?**
Opciones: (a) **antes** de que el pedido pase a cocina (reportan pago móvil/transferencia y el admin lo verifica) · (b) **contra entrega** (el motorizado cobra) · (c) ambas, según el cliente.
*Por qué importa:* con (b) el motorizado necesitaría ver el monto a cobrar y registrar que cobró.
**Por defecto:** (a) prepago.
**Respuesta:**

**C-5 🔴 ¿Quién verifica los pagos reportados desde la app?**
Opciones: (a) el admin los revisa y aprueba uno a uno · (b) se acreditan automáticamente y el admin solo puede revertir · (c) automáticos hasta cierto monto.
**Por defecto:** (a) verificación manual (reduce riesgo de referencias falsas).
**Respuesta:**

**C-14 🟡 ¿Qué métodos de pago aceptan?** (marca todos) Pago móvil · Transferencia Bs · Zelle · Efectivo USD · Efectivo Bs · Punto de venta · Binance/USDT · Otro. Indica también los **datos de pago** que verá el cliente (bancos, teléfono de pago móvil, correo Zelle).
**Por defecto:** pago móvil, transferencia, Zelle, efectivo USD.
**Respuesta:**

**C-7 🟡 ¿Desde cuándo corre el plazo de una deuda a crédito y cuántos días tiene?**
Opciones: desde que se hace el pedido / desde que se entrega. Días: 7, 15, 30, distinto por cliente.
**Por defecto:** desde la entrega; 7 días, configurable por cliente.
**Respuesta:**

**C-23 🟡 ¿Qué pasa cuando un cliente a crédito tiene facturas vencidas?**
Opciones: (a) no puede pedir más hasta pagar · (b) puede pedir pero se avisa al admin · (c) bloqueo tras N días de vencida.
**Por defecto:** (c) bloqueo si tiene facturas vencidas hace más de 7 días.
**Respuesta:**

**C-20 🟢 ¿Necesitan factura fiscal (SENIAT), IVA o nota de entrega impresa?**
**Por defecto:** no en v1; el sistema genera una nota de entrega/estado de cuenta en PDF no fiscal.
**Respuesta:**

## B. Pedidos y producción

**C-6 🔴 ¿Los pedidos son para el mismo día o para el día siguiente? ¿Hay hora de corte?**
Ejemplo: “lo que se pide antes de las 6:00 pm se entrega mañana temprano”.
**Por defecto:** existe una hora de corte configurable; antes del corte = entrega hoy, después = mañana. El cliente puede elegir la fecha.
**Respuesta:**

**C-9 🟡 Si en cocina no alcanza un producto, ¿se permite entregar el pedido incompleto?**
Opciones: (a) el admin edita el pedido antes de “Listo” y se ajusta la cuenta · (b) cocina puede marcar cantidades entregadas · (c) no se permite.
**Por defecto:** (a) solo el admin edita.
**Respuesta:**

**C-19 🟡 ¿Hay monto mínimo por pedido o mínimo por producto?** (ej.: “mínimo 10 canillas”, “pedido mínimo $20”)
**Por defecto:** mínimo por producto configurable; sin mínimo por pedido total.
**Respuesta:**

**C-16 🟡 ¿Se cobra el delivery?** (gratis / monto fijo / por zona)
**Por defecto:** gratis (no se modela costo de envío).
**Respuesta:**

**C-17 🟡 Horario y días de operación** (¿abren domingos? ¿a qué hora sale el motorizado?). ¿Se debe impedir pedir en días cerrados?
**Por defecto:** lunes a sábado; pedidos permitidos siempre, con fecha de entrega al próximo día hábil.
**Respuesta:**

**C-10 🟢 Cocina: ¿web en una tablet/TV (recomendado) o app Android?**
**Por defecto:** web en tablet (`/cocina`), instalable como PWA.
**Respuesta:**

## C. Clientes y catálogo

**C-8 🟡 ¿Todos los mayoristas pagan el mismo precio, o hay precios especiales por cliente / por volumen?**
**Por defecto:** un solo precio mayorista; listas de precios por cliente quedan preparadas pero opcionales.
**Respuesta:**

**C-15 🟡 Clientes del negocio (detal): ¿usarán la app o solo se llevan sus cuentas desde la web?** ¿Necesitan registrar las **ventas de mostrador** del día (un POS simple) para que el dashboard muestre los ingresos totales del local?
**Por defecto:** los clientes detal no usan app; el admin registra sus fiados (cargos) y abonos. Sin POS en v1; los ingresos del dashboard son solo de pagos registrados en el sistema.
**Respuesta:**

**C-21 🟢 Volumen aproximado:** ¿cuántos mayoristas, cuántos pedidos por día y cuántos productos?
**Por defecto:** < 100 clientes, < 150 pedidos/día, < 100 productos (el diseño escala mucho más).
**Respuesta:**

**C-22 🟡 ¿Hay datos existentes para migrar?** (lista de clientes, deudas actuales, productos y precios en Excel)
**Por defecto:** sí, se importarán por CSV en L1.
**Respuesta:**

## D. Usuarios, marca y operación

**C-24 🟡 ¿Cuántas personas usan el panel de administración?** ¿Se necesitan permisos distintos (p. ej. un cajero que solo aprueba pagos)?
**Por defecto:** uno o más usuarios con rol ADMIN, todos con control total.
**Respuesta:**

**C-13 🟡 Marca:** nombre comercial exacto (¿“JM Cakes”?), logo, colores, teléfono/WhatsApp del negocio.
**Por defecto:** “JM Cakes”, paleta cálida de panadería; se reemplaza cuando llegue el logo.
**Respuesta:**

**C-25 🟢 ¿Quieren avisos por WhatsApp además de las notificaciones push?** (tiene costo con la API oficial de WhatsApp Business)
**Por defecto:** no en v1; solo botón “Escribir por WhatsApp”.
**Respuesta:**

## E. Infraestructura, cuentas y publicación

**C-27 🔴 Accesos para los agentes:** ¿los MCP de **Neon** y **Railway** de esta cuenta son los que se deben usar para este proyecto? ¿Crear un proyecto nuevo en cada uno o reutilizar uno existente?
**Por defecto:** crear proyecto nuevo `jmcakes` en Neon y en Railway (staging primero).
**Respuesta:**

**C-26 🟢 Presupuesto mensual de infraestructura** (Railway + Neon + dominio).
**Por defecto:** planes de entrada (≈ US$5–25/mes en total al inicio).
**Respuesta:**

**C-11 🟢 Dominio:** ¿tienen uno? (ej. `jmcakes.com`; panel en `admin.jmcakes.com`)
**Por defecto:** dominios gratuitos de Railway hasta tener uno propio.
**Respuesta:**

**C-12 🟡 Google Play:** ¿tienen cuenta de desarrollador? ¿Personal u organización? (Las cuentas **personales nuevas** deben hacer una **prueba cerrada con 12 testers durante 14 días** antes de publicar; las de **organización** requieren número D-U-N-S pero no tienen esa espera.) Confirma también los identificadores `com.jmcakes.cliente` y `com.jmcakes.delivery`.
**Por defecto:** se asume cuenta personal y se planifican los 14 días de prueba cerrada.
**Respuesta:**

**C-28 🟢 Firebase:** ¿tienen una cuenta de Google para crear el proyecto de Firebase (notificaciones push)? Es gratuito; se necesita para descargar `google-services.json`.
**Por defecto:** el humano lo crea durante F0 siguiendo los pasos que deje el agente; mientras tanto el push queda deshabilitado.
**Respuesta:**

**C-29 🟢 Ejecución:** ¿prefieres lanzar los 7 agentes de la Fase 1–2 todos a la vez, o por tandas (primero backend B1–B3, luego interfaces)? ¿Quieres que una sesión orquestadora los lance y vigile sus PRs automáticamente?
**Por defecto:** por tandas, con revisión humana de cada PR antes del merge.
**Respuesta:**
