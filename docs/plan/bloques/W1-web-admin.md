# W1 — Web: panel del administrador

**Fase 1** · rama `block/W1` · `WEB_PORT=3001`, `MOCK_PORT=4011` · diseño `DESIGN.md` + `docs/design/admin.md` · skill **impeccable** · reutiliza las vistas de OpenGravity según [06](../06-reutilizacion-opengravity.md)

## Objetivo
El dueño controla todo desde el teléfono o la computadora. Aprobar pagos está a un toque desde cualquier pantalla.

## Pantallas (`/admin/...`)
1. **Inicio:**
   - métricas del día (03 §6) con selector de fecha;
   - pedidos por estado en vivo (SSE `order.*`);
   - pagos por verificar;
   - top productos y deudores;
   - alerta de READY sin motorizado.
2. **Pagos:**
   - Bandeja con cursor por estado.
   - **Comprobante a la vista:** imagen ampliable o PDF, referencia, monto en Bs y USD, tasa, titular, pedido y cliente.
   - Acciones: Tomar · Aprobar (corregir **monto recibido en la moneda del pago** o tasa; el USD lo recalcula la API) · Rechazar (con motivo) · Revertir (con motivo).
   - Contador global en el Sidebar con `GET /admin/payments/pending-count` + SSE `payment.*` + sonido.
3. **Pedidos:**
   - Tabla con filtros del servidor; detalle con bitácora, pagos y CxC.
   - Acciones: cancelar, reducir (cantidades por línea, solo hacia abajo), forzar transición y reasignar motorizado.
   - Filtro “sin motorizado” (`unassigned=true`). Usa `AdminOrderDetail`.
   - **Crear pedido para un cliente:** `POST /admin/orders/quote` y luego `POST /admin/orders`, con `Idempotency-Key` generado una vez por intento.
4. **Clientes:**
   - Listado con billetera, deuda, modo y estado.
   - Ficha con pestañas: Datos · Crédito · Estado de cuenta (exportable) · Pedidos · Pagos.
   - Acciones: abono manual (con pedido opcional), cargo, ajuste, **devolver saldo**, anular o condonar CxC, bloquear (cancela sus pedidos pendientes; pedir confirmación).
   - Crear cliente sin app.
5. **Cobranza:** CxC con antigüedad, vencidas y CSV.
6. **Catálogo:** categorías y productos con foto (`FileUpload` → `/files`), publicar, agotado y mínimo; **cambio masivo** con vista previa y aplicar; historial.
7. **Cuentas y tasa:** cuentas del negocio con transacciones (sin bóvedas ni transferencias); tasa del día con fijar manual y sincronizar.
8. **Cierres:** listado, detalle, PDF y ejecutar.
9. **Configuración:**
   - negocio, horario, anticipación, días máximos y ventana de pago;
   - envío y motorizado;
   - crédito y tolerancia;
   - versiones mínimas de las apps;
   - **métodos de pago y cuentas bancarias**: componentes `components/settings/*` de OpenGravity adaptados, con `cashAccountId`;
   - usuarios internos.
10. **Auditoría.**

## Reglas
- Cliente delgado: los montos, incluidos los Bs, son los que manda la API. `detail` y `code` se muestran tal cual.
- `cache: 'no-store'`, fechas en Caracas, cursor del servidor.
- Las vistas copiadas de OpenGravity pasan a **camelCase** y a cursor (“Cargar más”).
- Confirmación en toda acción de dinero. Botones con estado de carga y una sola ejecución.
- Responsive: inicio y pagos impecables en el teléfono.
- **No** tocar `package.json` ni editar archivos existentes de `src/lib`. Los helpers van en `src/components/admin/lib/`. **Sí** es dueño de `src/components/layout/**`.
- Tipos desde `src/lib/api-types.ts` (generado por el orquestador; no regenerar).

## Contra qué construir
Mock con `MOCK_PORT=4011 api/scripts/mock.sh` y `NEXT_PUBLIC_API_URL=http://127.0.0.1:4011/api/v1`. En modo mock, `JWT_SECRET=dev-mock-secret-no-usar-en-prod`. Q1 conecta con la API real.

## Pruebas exigidas
- Vitest: bandeja de pagos (estados, acciones y errores de la API) y formulario de cambio masivo.
- **Playwright** (lo corre el CI): login de admin; aprobar un pago; vista previa y aplicar cambio masivo; habilitar crédito. Capturas de escritorio y móvil de cada pantalla.
- Local: `npm run lint && npm test && npm run build && npx playwright test --list`.
- `impeccable detect` sin críticos.

## No tocar
`src/app/(cocina)`, `src/components/{ui,cocina}`, archivos existentes de `src/lib`, `package.json`, `api/`, `android/`.
