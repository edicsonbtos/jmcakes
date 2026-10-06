# M — Android: app del cliente (Play Store) y app del motorizado (APK)

**Fase 1** · **Rama** `block/M` · Diseño: `DESIGN.md`, `docs/design/android-theme.md`, `cliente-android.md`, `delivery-android.md` · Skill: `impeccable` (`reference/android.md`) · Contrato: `contracts/openapi.json`

## Objetivo
Dos apps nativas, sencillas y robustas con mala señal, en un solo proyecto Gradle.

## Estructura
```
android/ (Gradle Kotlin DSL, version catalog, AGP y Kotlin estables recientes, minSdk 24, targetSdk 35)
├─ core/designsystem   tema Material 3 de DSN + componentes (MoneyText USD/Bs, StatusPill, EmptyState…)
├─ core/network        Retrofit + OkHttp (auth interceptor + refresh, Idempotency-Key), kotlinx.serialization,
│                      BigDecimal desde string, ApiError{code, detail}, DTOs del contrato
├─ core/data           SessionStore (DataStore), repositorios, cola de acciones pendientes (delivery)
├─ app-cliente         com.panaderia.cliente   (flavors: mock, staging, prod → BASE_URL)
└─ app-delivery        com.panaderia.delivery
```
FCM detrás de un flag: sin `google-services.json`, el push queda apagado y la app sigue funcionando (el motorizado hace *polling* cada 30 s en primer plano).

## App cliente — pantallas
1. **Registro e inicio de sesión:** registro sin aprobación, con tipo de negocio (perros calientes, bodega, cafetería/restaurante, eventos, otro).
2. **Catálogo:** chips de categorías; tarjetas con foto, precio USD y Bs (tasa de hoy), unidad y − / + respetando `minQty`; “Agotado”.
3. **Carrito**
   - Selector **“Lo quiero hoy” / “Programar”**, con fecha y hora dentro de la ventana de `/settings/public`.
   - Dirección, notas y resumen con `POST /orders/quote`: “Usamos $X de tu billetera”, faltante o crédito disponible.
4. **Confirmar y pagar** (03 §3.2):
   - **Billetera alcanza:** “¡Listo! Pagado con tu billetera” y el pedido en camino a producción.
   - **No alcanza:** la pantalla de pago muestra el **faltante en USD y Bs**, los datos de pago (métodos y cuentas, con botón copiar) y el formulario: método o cuenta, monto, **referencia**, fecha, titular y **foto del comprobante** (Photo Picker o cámara). Luego, el estado “Pago en revisión”.
   - **Crédito:** confirmado al instante; si excede el límite, el mensaje de la API y la acción “Recargar billetera”.
5. **Mis pedidos:** estados en lenguaje simple, detalle, cancelar si se puede, **Repetir pedido**, y “Pagar faltante” si está en AWAITING_PAYMENT.
6. **Billetera:** saldo a favor, deuda y vencidas, crédito disponible, movimientos, **Recargar** (mismo formulario de pago) y mis pagos con estado y motivo de rechazo.
7. **Perfil:** datos, dirección, contacto o WhatsApp del negocio, **eliminar cuenta** (requisito de Play) y cerrar sesión.
8. **Push:** pedido confirmado o en camino, pago aprobado o rechazado y crédito habilitado. Al tocar, abre el pedido o el pago.

## App delivery — pantallas
Login persistente. **Por salir** (con la hora programada visible), con selección múltiple para “En camino”. **En camino**, con “Entregado” y confirmación. Llamar, WhatsApp y “Abrir en Maps” (dirección en texto). Contador de entregados hoy. Push con sonido. Cola local de acciones fallidas con reintento automático. Aviso “Actualiza la app” si la versión es menor a la de `/settings/public`.

## Reglas
- La app **no calcula dinero**: muestra los montos de la API. `BigDecimal` siempre; nunca `Double`.
- `Idempotency-Key` (UUID) generado **una vez** por intento de pedido o pago y reutilizado en los reintentos.
- Material 3 según `impeccable/reference/android.md`: Back predictivo, edge-to-edge, 48 dp, `sp`, tema oscuro.
- Textos en español de Venezuela; fechas y horas en `America/Caracas`.

## Limitantes
- **Sin Android SDK ni emulador** en el contenedor (`dl.google.com` bloqueado). Escribir código conservador y estándar, y pruebas JVM (ViewModels con repositorios falsos, Turbine). La compilación la verifica GitHub Actions al integrar; Q2 corrige lo que falle.
- `.github/workflows/android.yml`: JDK 17, `setup-android`, `./gradlew :app-cliente:assembleMockDebug :app-delivery:assembleMockDebug testDebugUnitTest`, y las APKs como artefactos.
- Incluir el **Gradle wrapper** (`gradlew`, `gradle/wrapper/*`), generado con el Gradle local (`gradle wrapper --gradle-version <estable>`).

## Pruebas exigidas
- ViewModel de checkout en sus 4 casos: billetera suficiente, parcial, cero y crédito excedido.
- Formulario de pago: validaciones e idempotencia en el reintento.
- Repositorio de delivery: la cola de reintentos.
- Mapper de `ApiError`.
- Capturas Roborazzi (si se logra en JVM) en `docs/handoffs/assets/M-*.png`.

## No tocar
`api/`, `web/`, `contracts/` (solo lectura).
