# Q1 — Integración end-to-end, QA y seguridad

**Fase:** 3 · **Esfuerzo:** M · **Rama:** `block/Q1-integracion`

## Objetivo
Comprobar que las piezas construidas por separado **funcionan juntas** en staging y corregir las costuras.

## Entradas
- B1, B2, B3, W1, W2, M1, M2 fusionados; todos los handoffs (en especial sus secciones “Pendiente” y “Solicitudes de cambio de contrato”).

## Alcance
1. **Suite E2E de API** (`e2e/api`): escenarios completos contra una rama Neon efímera:
   - Mayorista crédito: pedido → cocina → listo → motorizado → entregado → CxC → reporte de pago → aprobación → deuda baja (FIFO) → sobrante en billetera → siguiente pedido lo consume.
   - Mayorista contado: pedido → esperando pago → reporte → aprobación → cocina → … → entregado.
   - Límite de crédito excedido; facturas vencidas bloquean; cancelaciones en cada estado; referencia duplicada; idempotencia.
   - Cliente detal sin app: cargo manual → abono manual.
   - Cambio de día en Caracas (pedido a las 23:30 VET aparece en el día correcto del dashboard).
2. **E2E web** (Playwright) admin + cocina contra staging.
3. **Smoke Android**: instalar APKs `staging` no es posible sin emulador → verificar con tests JVM de integración contra staging y dejar **checklist de prueba manual** para el humano en un teléfono real.
4. **Resolver** solicitudes de cambio de contrato pendientes y discrepancias contrato ↔ implementación.
5. **Revisión de seguridad**: autorización por rol y propiedad en todos los endpoints (test que recorre el contrato con cada rol), rate limit, validación de subida de archivos, secretos, CORS, cabeceras. Ejecutar `/security-review`.
6. **Rendimiento básico**: 50 pedidos simultáneos; cola de cocina < 300 ms.
7. Actualizar `docs/plan/STATUS.md` y escribir el **informe de QA** en `docs/handoffs/Q1.md`.

## Carpetas propias
`e2e/**`; puede tocar cualquier carpeta **solo para corregir defectos** encontrados (commits pequeños y explicados).

## Limitantes
- No agregar funcionalidades nuevas; solo integrar y corregir.
- Sin dispositivo físico: la validación final de las apps la hace el humano con la checklist.

## Oportunidades
- Ramas Neon por ejecución → datos limpios en cada corrida.
- Usar la API de Railway/Neon por MCP para revisar logs de errores en staging.

## Definición de terminado
- Todas las suites verdes en CI; cero solicitudes de cambio abiertas; checklist manual entregada; informe de QA.

## Prompt para lanzar este bloque
```
Eres el agente del bloque Q1 del proyecto JM Cakes (repo edicsonbtos/jmcakes).
Lee CLAUDE.md, docs/plan/, docs/plan/bloques/Q1-integracion-qa.md y TODOS los
docs/handoffs/. Integra y prueba el sistema completo en staging, corrige defectos
con commits pequeños, resuelve las solicitudes de cambio de contrato y entrega el
informe docs/handoffs/Q1.md con una checklist de prueba manual para Android.
```
