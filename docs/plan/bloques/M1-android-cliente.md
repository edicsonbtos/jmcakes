# M1 — App Android del cliente mayorista (Play Store)

**Fase:** 2 (paralelo) · **Esfuerzo:** L · **Rama:** `block/M1-android-cliente`

## Objetivo
Una app **muy sencilla** para que el mayorista se registre, vea los productos, pida en pocos toques, siga su pedido y maneje su **billetera y deuda**, en sus dos modos: **contado** y **crédito**.

## Entradas
- F0 (`android/core`: red, sesión, DTOs, tema, FCM base).
- Handoffs de B1, B2, B3 para pasar del flavor `mock` a `staging`.

## Pantallas
1. **Bienvenida / Login / Registro** (nombre, negocio, teléfono, cédula/RIF, dirección, referencia, contraseña). Tras registrarse: pantalla “Tu cuenta está en revisión” **[C-3]**.
2. **Catálogo**: categorías en chips, tarjetas con foto, precio (USD y Bs a la tasa del día **[C-1]**), unidad, botones − / + con mínimo, “Agotado”.
3. **Carrito / Confirmar pedido**: resumen, fecha de entrega (hoy/mañana según hora de corte), dirección (editable), notas.
   - **Modo crédito**: muestra “Crédito disponible: $X”. Si no alcanza, mensaje claro y botón “Recargar billetera”.
   - **Modo contado**: tras confirmar, pantalla de **pago**: datos de pago del negocio (pago móvil, cuentas, Zelle — desde settings) y formulario de reporte.
4. **Mis pedidos**: lista con estado en lenguaje simple (Esperando pago · Confirmado · En preparación · Listo · En camino · Entregado · Cancelado), detalle, cancelar si aún se puede, **repetir pedido** con un toque.
5. **Billetera** (visible en ambos modos; principal en crédito): saldo a favor, deuda total, facturas pendientes con vencimiento, movimientos, botón **Reportar pago / Recargar** (método, moneda, monto, referencia, fecha, foto opcional del comprobante con la cámara/galería), estado de mis pagos.
6. **Perfil**: datos, dirección, cerrar sesión, contacto/WhatsApp del negocio.
7. **Notificaciones push**: cuenta aprobada, pago aprobado/rechazado, pedido confirmado/en camino/entregado. Tocar la notificación abre el pedido o el pago.

## Requisitos
- Español; botones grandes; funciona en teléfonos de gama baja (minSdk 24) y con conexión inestable: reintentos, `Idempotency-Key` en crear pedido y reportar pago, estados de carga/sin conexión claros.
- La interfaz cambia según `payment_mode` del perfil (no hay que reinstalar si el admin habilita crédito).
- Cumplir políticas de Google Play: **eliminación de cuenta** desde la app (requisito), política de privacidad enlazada, permisos mínimos (cámara/galería con *Photo Picker*, notificaciones en Android 13+).

## Fuera de alcance
Pagos automáticos con pasarela, mapas, chat.

## Carpetas propias
`android/app-cliente/**`. Cambios aditivos en `android/core` documentados.

## Limitantes
- **El contenedor de la nube no tiene Android SDK ni emulador.** Compilar y testear en CI de GitHub Actions (`android.yml`), o instalar `cmdline-tools` en la sesión si la red lo permite. Tests: unitarios de ViewModel + Robolectric + Compose UI tests en JVM.
- Sin `google-services.json` real, el push queda deshabilitado (flag) — la app debe funcionar igual.
- No se puede publicar en Play Store desde el agente (lo hace L1 con el humano).

## Oportunidades
- **Capturas automáticas** con Roborazzi/Paparazzi (JVM, sin emulador) para el handoff y luego para la ficha de Play Store.
- Caché del catálogo en memoria/DataStore para abrir instantáneo.
- “Repetir pedido” reduce la fricción del mayorista que pide lo mismo cada día.

## Definición de terminado
- APK debug de flavor `staging` generada en CI como artefacto.
- Flujos probados contra staging: registro → aprobación → pedido crédito → pedido contado + reporte de pago.
- Capturas de todas las pantallas en el handoff.

## Prompt para lanzar este bloque
```
Eres el agente del bloque M1 del proyecto JM Cakes (repo edicsonbtos/jmcakes).
Lee CLAUDE.md, docs/plan/ (especialmente 03-flujos-de-negocio.md),
docs/plan/bloques/M1-android-cliente.md, docs/handoffs/ (F0 y B* que existan) y
docs/CUESTIONARIO.md. Construye la app en android/app-cliente con Kotlin + Compose.
Tu contenedor no tiene Android SDK: apóyate en el workflow de CI o instala
cmdline-tools si la red lo permite. Sigue docs/plan/05-protocolo-agentes.md
(rama block/M1-android-cliente, CI verde, capturas y handoff docs/handoffs/M1.md).
```
