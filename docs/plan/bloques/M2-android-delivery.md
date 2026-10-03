# M2 — App Android del motorizado (APK)

**Fase:** 2 (paralelo) · **Esfuerzo:** S · **Rama:** `block/M2-android-delivery`

## Objetivo
La app más simple posible: **“Nuevo pedido para X cliente, a X dirección”**, y dos botones: **En camino** y **Entregado**. Sin aceptar pedidos, sin rutas, sin mapas.

## Entradas
- F0 (`android/core`).
- Handoff de B2 para pasar del mock a staging.

## Pantallas
1. **Login** (una sola vez; sesión persistente).
2. **Mis pedidos** con dos pestañas:
   - **Por salir** (READY asignados): tarjeta con #número, cliente/negocio, **dirección + referencia** en grande, teléfono (botones **Llamar** y **WhatsApp**), lista de productos, **monto a cobrar** si aplica **[C-4]**. Selección múltiple → **En camino**.
   - **En camino**: botón **Entregado** con confirmación (“¿Entregaste el pedido #1042 a Pedro Pérez?”).
   - Pie: entregados hoy (contador).
3. Botón opcional “Abrir en Maps” que solo pasa la dirección en texto a Google Maps (sin integrar mapas).
4. **Push con sonido** al asignarse un pedido; tocarla abre la lista. Refresco al volver a primer plano y *pull-to-refresh*.

## Requisitos
- Funciona con mala señal: las acciones se reintentan; si falla, se muestran como “pendiente de enviar” y se reintentan solas (cola local mínima en DataStore/Room).
- Solo rol `DELIVERY`.

## Distribución
APK firmada **fuera de Play Store** (instalación directa). Se publica en **GitHub Releases** o un enlace privado (lo hace L1). Incluir verificación de versión mínima: si la API indica una versión mínima mayor, mostrar “Actualiza la app” con enlace.

## Fuera de alcance
Mapas, GPS, tracking, aceptación/rechazo, múltiples motorizados, cobro dentro de la app.

## Carpetas propias
`android/app-delivery/**`.

## Limitantes
- Igual que M1: sin Android SDK/emulador en el contenedor → CI de GitHub Actions; tests JVM.
- Sin `google-services.json`, el push queda deshabilitado y la app hace *polling* cada 30 s en primer plano.

## Oportunidades
- Reutiliza casi todo `:core`; bloque pequeño, ideal para cerrar rápido y probar el circuito cocina → motorizado.

## Definición de terminado
- APK `staging` en CI; flujo contra staging: pedido READY aparece → En camino → Entregado → el admin lo ve entregado.
- Capturas en el handoff.

## Prompt para lanzar este bloque
```
Eres el agente del bloque M2 del proyecto JM Cakes (repo edicsonbtos/jmcakes).
Lee CLAUDE.md, docs/plan/, docs/plan/bloques/M2-android-delivery.md,
docs/handoffs/ (F0 y B2 si existe) y docs/CUESTIONARIO.md. Construye la app en
android/app-delivery: sin sobreingeniería (sin mapas, sin aceptar pedidos).
Sigue docs/plan/05-protocolo-agentes.md (rama block/M2-android-delivery, CI verde,
handoff docs/handoffs/M2.md, STATUS.md).
```
