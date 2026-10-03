# B1 — API: catálogo, clientes y configuración

**Fase:** 1 (paralelo) · **Esfuerzo:** M · **Rama:** `block/B1-catalogo-clientes`

## Objetivo
Que el administrador pueda **publicar productos, subir y bajar precios, gestionar clientes, aprobar registros y habilitar crédito**, y que la app del cliente pueda leer el catálogo.

## Entradas
- `main` con F0 fusionado; `docs/handoffs/F0.md`.
- Contrato `contracts/openapi.yaml` (grupos `catalog`, `customers`, `settings`).

## Alcance
1. **Categorías**: CRUD admin, orden, activar/desactivar.
2. **Productos**: CRUD admin; publicar/ocultar; marcar agotado hoy (`is_available`); orden; pedido mínimo; unidad.
3. **Precios**: cambio individual y **cambio masivo** (porcentaje o monto, por categoría o selección) con vista previa; cada cambio escribe `price_history` y `audit_log`.
4. **Imágenes**: endpoint que entrega URL prefirmada de subida al bucket; validación de tipo/tamaño; URL pública/firmada para lectura; redimensionado opcional (miniatura).
5. **Catálogo para el cliente**: solo productos publicados de categorías activas; precio resuelto por lista de precios del cliente si existe **[C-8]**.
6. **Implementar `CatalogService.priceOrderLines`** (usado por B2): valida existencia, publicación, disponibilidad, `min_qty`, y devuelve precios snapshot.
7. **Clientes (admin)**: listado con filtros (tipo, modo, estado, con deuda — la deuda la aporta B3 vía consulta), detalle, edición, creación de cliente sin app, **aprobar/rechazar registro**, cambiar **modo contado/crédito**, límite y días de crédito, bloquear/desbloquear. Push al cliente al aprobar (vía `Notifier`, stub hasta que B2 lo implemente).
8. **Perfil del cliente (app)**: ver y editar sus datos permitidos (dirección, referencia, teléfono de contacto). No puede cambiar su modo ni límite.
9. **Implementar `CustomersService`**.
10. **Usuarios internos (admin)**: crear/editar usuarios de producción y delivery; resetear contraseña.
11. **Settings**: lectura/edición tipada de las claves de `02-modelo-de-datos.md`, con validación.

## Fuera de alcance
Pedidos, pagos, billetera, dashboard (B2/B3). Interfaces web/Android.

## Carpetas propias
`api/src/modules/catalog`, `api/src/modules/customers`, `api/src/modules/settings`, `api/src/modules/users` y sus tests.

## Limitantes
- No modificar módulos de B2/B3; solo llamar sus interfaces.
- Cambios al contrato o esquema solo aditivos y documentados.
- Si no hay bucket configurado, usar un adaptador de almacenamiento local para dev/test (interfaz `Storage`).

## Oportunidades
- El cambio masivo de precios con **vista previa** es una función muy valorada en Venezuela (inflación): hacerla bien.
- Búsqueda de clientes por nombre/teléfono/RIF con `ILIKE` + índice trigram (`pg_trgm`).

## Definición de terminado
- Tests de cada endpoint (autorización por rol incluida: un cliente no puede ver otro cliente; producción/delivery no acceden a precios de admin).
- Test de contrato verde.
- Desplegado en staging; handoff con ejemplos `curl`.

## Siguiente
Desbloquea pantallas reales de catálogo/clientes en **W1** y **M1**; habilita a **B2** a usar precios reales.

## Prompt para lanzar este bloque
```
Eres el agente del bloque B1 del proyecto JM Cakes (repo edicsonbtos/jmcakes).
Lee CLAUDE.md, docs/plan/, docs/plan/bloques/B1-api-catalogo-clientes.md,
docs/handoffs/F0.md y docs/CUESTIONARIO.md. Implementa todo el alcance de B1
solo dentro de tus carpetas, siguiendo docs/plan/05-protocolo-agentes.md
(rama block/B1-catalogo-clientes, CI verde, handoff docs/handoffs/B1.md,
STATUS.md). Otros agentes trabajan en paralelo en B2 y B3: no toques sus módulos.
```
