# M — Android: app del cliente (Play Store) y app del motorizado (APK)

**Fase 1** · rama `block/M` · diseño `DESIGN.md`, `docs/design/{android-theme,cliente-android,delivery-android}.md` · skill **impeccable** (`reference/android.md`) · contrato `contracts/openapi.json`

## Objetivo
Dos apps nativas sencillas y robustas con mala señal, en un solo proyecto Gradle.

## Estructura
```
android/  (Gradle Kotlin DSL + version catalog + **wrapper** generado con el Gradle local; AGP y Kotlin estables; minSdk 24, targetSdk 35)
├─ core/network      kotlin("jvm") PURO: Retrofit, OkHttp (auth interceptor + Authenticator de refresh, Idempotency-Key),
│                    kotlinx.serialization, BigDecimal desde string, ApiError{code, detail, meta}, DTOs del contrato (camelCase)
├─ core/data         kotlin("jvm") PURO: repositorios, SessionStore sobre datastore-preferences-core, cola de acciones pendientes
├─ core/designsystem Android library: tema Material 3 de DSN + componentes (MoneyText muestra los Bs de la API, StatusPill, EmptyState…)
├─ app-cliente       com.panaderia.cliente   (flavors mock/staging/prod → BASE_URL)
└─ app-delivery      com.panaderia.delivery
```
FCM va detrás de un flag: sin `google-services.json`, el push se apaga y la app sigue funcionando. En delivery, *polling* cada 30 s en primer plano.

## App cliente
1. **Registro** sin aprobación, con tipo de negocio (perros calientes, bodega, cafetería/restaurante, eventos, otro). **Login.**
2. **Catálogo:** `GET /catalog` con `price` (USD) y `priceVes` (Bs **de la API**; si es `null`, solo USD), foto (`imageUrl`), − / + con `minQty` y estado “Agotado”.
3. **Carrito:** “Lo quiero hoy” o “Programar” (fecha y hora dentro de la ventana de `/settings/public`). `POST /orders/quote` para el resumen (“Usamos $X de tu billetera”, `totalVes`, faltante o crédito disponible).
4. **Confirmar** (`POST /orders`, `Idempotency-Key` generado una vez por intento):
   - **Billetera suficiente:** “¡Listo! Pagado con tu billetera.”
   - **Faltante:**
     - pantalla de pago con `amountDue`, `amountDueVes` y `expiresAt` (“paga antes de las HH:MM”);
     - datos de pago (`paymentMethods[].accounts[]` con `id`, botón copiar);
     - formulario: cuenta, `localCurrency`, monto **prellenado con `amountDueVes` o `amountDue`**, referencia, fecha, titular y comprobante (Photo Picker o cámara → `POST /files`, multipart);
     - envío con `POST /payments`, y luego “Pago en revisión”.
   - **Crédito:** confirmado al instante. Si se excede, se muestra el `detail` de la API con la acción “Recargar billetera”.
   - `OPEN_DEBT` u `OVERDUE_DEBT` → pantalla para pagar la deuda.
5. **Mis pedidos:** estados en lenguaje simple, detalle, cancelar, **repetir pedido** y “Pagar faltante”. Esta última lee de `GET /orders/{id}` los valores `amountDue`, `amountDueVes`, `rate` y `expiresAt`, y los métodos de `GET /payment-methods`.
6. **Billetera:** saldo, deuda y vencidas (en USD y en Bs **de la API**), crédito disponible, movimientos, **Recargar** y mis pagos (`GET /payments`, `GET /payments/{id}` con el motivo de rechazo).
7. **Perfil:** datos, dirección, WhatsApp del negocio, **eliminar cuenta** (`DELETE /auth/account`) y cerrar sesión.
8. **Push:** tipos y claves de `data` según la tabla §Push de 08. Se navega por `type` al pedido o al pago.

## App delivery
- **Login** persistente.
- **Por salir:** READY asignados a mí o sin asignar, con la hora visible; selección múltiple → “En camino” (respuesta `{updated, skipped}`).
- **En camino:** “Entregado” con confirmación. Un 200 repetido es éxito.
- `skipped` con razón: solo `ALREADY_OUT` cuenta como éxito; `CANCELLED`, `NOT_READY` y `ASSIGNED_TO_OTHER` se muestran al motorizado.
- Llamar, WhatsApp y “Abrir en Maps” (dirección en texto). Contador de entregados hoy.
- Push con sonido.
- **Cola local** de acciones fallidas con reintento: `skipped` o 200 cuentan como éxito; un 409 real se muestra al usuario.
- Aviso “Actualiza la app” si `versionCode < minVersionDelivery`.

## Reglas
- La app **no calcula dinero**: todo monto, USD o Bs, viene de la API. Siempre `BigDecimal`.
- Material 3 según `android.md` de Impeccable: Back predictivo, edge-to-edge, 48 dp, `sp`, tema oscuro.
- Español de Venezuela; hora de Caracas.

## Limitantes y verificación
- **Sin Android SDK** en el contenedor. En local corre `gradle :core:network:test :core:data:test` (JVM puro): DTOs, mapper de `ApiError`, serializer de BigDecimal, repositorios con MockWebServer, cola de reintentos e idempotencia.
- Los ViewModels y la UI se compilan y prueban en CI.
- `.github/workflows/android.yml`: `on: push` a `claude/happy-johnson-24innr`, `block/M` y `block/Q2` (`paths: android/**, .github/workflows/android.yml`) más `workflow_dispatch`; JDK 17, `android-actions/setup-android`, y luego `./gradlew :app-cliente:assembleMockDebug :app-delivery:assembleMockDebug :app-cliente:testMockDebugUnitTest :app-delivery:testMockDebugUnitTest :core:network:test :core:data:test :core:designsystem:testDebugUnitTest`. Se suben APKs y `**/build/test-results/**`.
- **Entrega temprana:** en cuanto el esqueleto compile en su cabeza (módulos, wrapper, login), el agente hace commit y lo informa. El orquestador lo publica para que CI dé su primer veredicto mientras M sigue.

## Pruebas exigidas
- **JVM (local):** red y datos según lo anterior.
- **App (CI):** ViewModel de checkout en 4 casos (billetera suficiente, parcial, cero, crédito excedido); formulario de pago (validaciones, reintento con la misma llave); cola de delivery.

## No tocar
`api/`, `web/`, `contracts/` (solo lectura).
