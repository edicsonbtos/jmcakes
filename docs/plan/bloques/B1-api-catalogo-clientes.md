# B1 — API: catálogo, archivos, clientes, usuarios y configuración

**Fase 1** · rama `block/B1` · BD `panaderia_test_b1` · endpoints y archivos de router: [08](../08-api-endpoints.md) §B1

## Objetivo
Que el admin publique productos, suba y baje precios (también en masa), y gestione clientes, crédito, bloqueos, usuarios y configuración; y que la app lea el catálogo con fotos y Bs.

## Alcance
1. **Catálogo:**
   - CRUD de categorías y productos.
   - `GET /catalog` con `rate` y `priceVes` de `RateService.rate_for(hoy)`. Si no hay tasa, `priceVes` es `null`, sin error.
   - `imageUrl`: GET prefirmada, TTL 1 h.
2. **Cambio masivo de precios:**
   - `preview` devuelve un `previewToken` HMAC con TTL de 10 min, que fija el contenido.
   - `apply` verifica que el estado no cambió desde el preview y escribe `price_history` (con `batchId`) y `audit_logs`.
3. **`CatalogService.price_lines`:** valida publicado, disponible y `minQty`. Errores `PRODUCT_UNAVAILABLE` y `BELOW_MIN_QTY` con el producto en `meta`.
4. **Archivos:**
   - `POST /files` multipart (≤ 5 MB; jpeg, png, webp o pdf, validado por contenido) → almacenamiento `S3Storage` (Railway Bucket) o `LocalStorage`.
   - `GET /files/{id}/url` y `/local` con autorización por propósito: PRODUCT_IMAGE para C y A; PAYMENT_PROOF para su dueño y A.
   - **Implementar `FileService`** (`assert_owned`, `signed_get_url`).
5. **`GET`/`PATCH /me/profile`** en `profile.py`.
6. **Clientes (admin):**
   - Listado con filtros y búsqueda; las columnas de dinero vienen de `FinanceQueries` (stub hasta B3). Crear cliente sin app y editar.
   - `credit`: el cambio de modo **no altera pedidos existentes** (03 §1). Auditoría y push.
   - `block {reason}`: llama `OrdersService.cancel_for_block` (stub hasta B2) y audita. `unblock`.
7. **Usuarios internos:** ADMIN, PRODUCTION y DELIVERY. Crear, editar, desactivar y resetear contraseña.
8. **Configuración:**
   - `GET /settings/public` con la forma exacta de 08.
   - `GET`/`PATCH /admin/settings` por secciones, con validación: horas `HH:MM` con apertura menor que cierre, rangos y `delivery.driverUserId` de un DELIVERY activo.
   - El commit lo hace el endpoint, junto con la auditoría.
9. `GET /admin/audit`.

## No tocar
Pedidos y dinero (B2/B3), `db_models.py`, `interface.py`, `main.py`, `web/`, `android/`.

## Pruebas exigidas
- Cada endpoint con su rol, más la ampliación del arnés de autorización: el cliente A no ve al B; PAYMENT_PROOF ajeno da 403; PRODUCT_IMAGE es legible por C.
- Cambio masivo: preview = apply; token alterado o vencido se rechaza; queda el historial.
- `price_lines`: todos los casos.
- Archivos: tamaño, tipo y autorización.
- Configuración: validaciones.
- `/catalog` con y sin tasa.
- Bloquear invoca `cancel_for_block` (verificado con un doble).
