# W1 — Web: panel del administrador

**Fase 1** · **Rama** `block/W1` · Diseño: `DESIGN.md` y `docs/design/admin.md` · Skill: `impeccable` · Reutiliza las vistas de OpenGravity ([06](../06-reutilizacion-opengravity.md))

## Objetivo
El dueño controla todo desde el navegador del teléfono o la computadora. Lo más urgente, **aprobar pagos**, está a un toque desde cualquier pantalla.

## Pantallas (`/admin/...`)
1. **Inicio:** métricas del día (03 §6) con selector de fecha; pedidos por estado en vivo (SSE); pagos por verificar, que lleva a la bandeja; top productos y deudores; alerta “sin motorizado configurado” si aplica.
2. **Pagos** (adaptado de OpenGravity `payments`):
   - Bandeja por estado, con el **comprobante a la vista**: imagen ampliable, referencia, monto en Bs y USD, tasa, titular y pedido asociado.
   - Acciones: **Tomar · Aprobar** (con corrección de monto o tasa) · **Rechazar** (con motivo) · **Revertir**.
   - Sonido y contador en vivo con `payment.reported`.
3. **Pedidos:**
   - Tabla con filtros del servidor: estado, fecha de entrega, cliente y canal.
   - Detalle con líneas, bitácora, pagos y CxC.
   - Acciones: cancelar (con motivo), reducir, forzar transición y **crear pedido para un cliente** (pedidos por WhatsApp).
   - Vista tablero opcional.
4. **Clientes:**
   - Listado con billetera, deuda, modo y estado.
   - Ficha con pestañas:
     - Datos;
     - **Crédito**: modo, límite y días;
     - Estado de cuenta: movimientos y CxC, exportable;
     - Pedidos;
     - Pagos.
   - Acciones: abono manual, cargo (fiado), ajuste con nota y bloquear.
   - Crear cliente sin app.
5. **Cobranza:** CxC con antigüedad, vencidas y exportación CSV.
6. **Catálogo:**
   - Categorías y productos, con foto (subida directa), publicar, agotado hoy y mínimo.
   - **Cambio masivo de precios** con vista previa (tabla antes y después) y confirmación.
   - Historial de precios.
7. **Cuentas y tasa:** cuentas del negocio con transacciones; tasa del día (BCV o MANUAL) con “fijar tasa manual” y “sincronizar”.
8. **Cierres:** listado, detalle, PDF y “ejecutar cierre” (de OpenGravity).
9. **Configuración:**
   - negocio (nombre, contacto), horario, anticipación mínima y días máximos para programar;
   - costo de envío y motorizado asignado;
   - reglas de crédito y tolerancia;
   - métodos de pago y cuentas bancarias;
   - usuarios internos.
10. **Auditoría:** listado filtrable.

## Reglas
- Cliente delgado: **no calcula** dinero ni estados; muestra lo que dice la API, con `detail` tal cual.
- `cache: 'no-store'` en vistas operativas; fechas en Caracas; filtros y paginación del servidor.
- Confirmación en toda acción de dinero. Botones de acción con estado de carga y **una sola ejecución** (deshabilitar mientras corre).
- Responsive: la bandeja de pagos y el inicio, impecables en el teléfono.
- Componer con el UI kit de DSN. Componentes nuevos de admin en `src/components/admin/`.

## Contra qué construir
Mientras B1–B3 no estén integrados, se usa **mock** (`scripts/mock.sh`, Prism en :4010, `NEXT_PUBLIC_API_URL=http://127.0.0.1:4010/api/v1`). Q1 cambia a la API real.

## Pruebas exigidas
- Vitest de componentes clave: bandeja de pagos y formulario de cambio masivo.
- Playwright contra el mock: login de admin, aprobar un pago (flujo de UI), cambio masivo (vista previa → aplicar) y crédito de un cliente.
- Capturas de escritorio y móvil de cada pantalla en `docs/handoffs/assets/W1-*.png`.
- `impeccable detect` sin críticos.

## No tocar
`src/app/(cocina)`, `src/components/ui` (solo aditivo y declarado), `src/lib` (solo aditivo y declarado), `api/`, `android/`.
