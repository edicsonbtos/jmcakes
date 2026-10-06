# B1 — API: catálogo, clientes, usuarios, configuración y archivos

**Fase 1** · **Rama** `block/B1` · Endpoints: [08](../08-api-endpoints.md) §B1

## Objetivo
El admin publica productos, sube y baja precios (también en masa), gestiona clientes y crédito, y usuarios internos. La app lee el catálogo y el perfil.

## Alcance
1. **Catálogo**
   - CRUD de categorías y productos, con publicar/ocultar, disponible (agotado hoy), `minQty` y orden.
   - `GET /catalog`: solo categorías activas y productos publicados, con los agotados marcados.
2. **Cambio masivo de precios**
   - `preview`: porcentaje o monto, por selección o por categoría, con redondeo opcional a 0.05 o 0.10. Devuelve un `previewToken` firmado (HMAC del contenido y TTL de 10 min).
   - `apply`: verifica que el token coincida con el estado actual y escribe `price_history` con un `batchId` y `audit_logs`.
3. **Implementar `CatalogService.price_lines`**: publicado, disponible y `qty ≥ minQty`, con los errores `PRODUCT_UNAVAILABLE` y `BELOW_MIN_QTY`, y `meta` del producto.
4. **Archivos**
   - Interfaz `Storage` con dos adaptadores:
     - `S3Storage` (Railway Bucket, URL prefirmada PUT/GET);
     - `LocalStorage` para dev y test, con endpoint PUT local.
   - Validación de tipo (jpeg, png, webp, pdf) y tamaño (≤ 5 MB).
   - Lectura: el cliente solo accede a sus propios comprobantes; el admin, a todo.
5. **Clientes (admin)**
   - Listado con filtros y búsqueda (nombre, negocio, teléfono, documento), con `pg_trgm` si conviene. Columnas de billetera y deuda vía `FinanceQueries` (stub hasta que llegue B3).
   - Crear cliente sin app. Editar.
   - `POST …/credit`: cambiar el modo, el límite y los días. Al pasar de CREDIT a CASH con deuda abierta, la deuda se mantiene. Con auditoría y push “Tienes crédito disponible”.
   - Bloquear y desbloquear.
6. **Perfil (cliente):** `GET` y `PATCH /me/profile`, sin acceso a modo ni crédito.
7. **Usuarios internos**: ADMIN, PRODUCTION y DELIVERY. Crear, editar, desactivar y resetear contraseña. Implementar `CustomersService`.
8. **Settings**
   - `GET /settings/public` y `GET`/`PATCH /admin/settings`, con validación por clave (horas `HH:MM`, enteros con rango, dinero ≥ 0).
   - `delivery.driverUserId` debe ser un usuario DELIVERY activo.
9. `GET /admin/audit`.

## No tocar
Pedidos, dinero, eventos (B2 y B3); `db_models.py` (congelado); `web/` y `android/`.

## Pruebas exigidas
- Cada endpoint con su rol válido.
- Arnés de autorización ampliado: cliente A no puede leer a B; cocina y delivery no ven `/admin/*`.
- Cambio masivo:
  - el `preview` coincide con el `apply`;
  - un token vencido o alterado se rechaza;
  - queda el historial.
- `price_lines`: casos de no publicado, agotado y bajo el mínimo.
- Storage local de punta a punta.
- Settings: validaciones.

## Definición de terminado
Ver protocolo §6. El handoff lleva ejemplos `curl` de cada endpoint.
