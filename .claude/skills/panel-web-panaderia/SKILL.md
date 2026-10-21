---
name: panel-web-panaderia
description: Convenciones de la web de la panadería (Next.js 16, panel /admin y cocina /cocina) — cliente de API que preserva detail y code, sesión con cookies httpOnly y proxy.ts, cliente delgado que no calcula dinero, idempotencia en formularios y formato de fechas y moneda de Caracas. Úsala antes de tocar web/.
---
# Adaptado de OpenGravity: .agents/skills/panel-web-opengravity/SKILL.md

# Web de la panadería (Next.js 16)

## Primero
- Este Next.js puede diferir de lo que conoces: lee `web/node_modules/next/dist/docs/` antes de usar
  una API. Carga la skill **impeccable** y sigue `DESIGN.md`.
- El nombre del negocio sale de `GET /api/v1/settings/public` (`businessName`), nunca fijo.

## Contrato
- Los tipos salen de `web/src/lib/api-types.ts`, generado por el orquestador desde
  `contracts/openapi.json`. No inventes campos; si falta algo, pídelo en el handoff y usa un fixture
  marcado `TODO(contrato)`.
- Dinero: **string decimal** en USD; Bs en `*Ves` (null si no hay tasa). La web **no calcula dinero**:
  totales del fiado con `fiado/quote` y confirmación del abono con `manual-payment/quote`.
- Errores: `{detail, code, meta}`. Muestra `detail` tal cual (ya viene en español de Venezuela).
- Listas: `?cursor=&limit=` → `{items, nextCursor}`.

## Sesión (01 §Autenticación)
- Cookies httpOnly `authToken` y `refreshToken`; `proxy.ts` (DSN) refresca y protege `/admin/**`
  (ADMIN). Si `/auth/me` trae `mustChangePassword`, redirige a `/cambiar-contrasena`.
- Ninguna ruta recibe un token desde el navegador.

## Formularios con dinero
- `Idempotency-Key` creado al abrir el formulario y **reutilizado en los reintentos** del mismo
  guardado (fiado, abono, anular, revertir, importar); botón deshabilitado hasta la respuesta.
- Confirmación con motivo obligatorio antes de anular o revertir.

## Formato
- `timeZone: "America/Caracas"` en toda fecha mostrada; `cache: 'no-store'` en vistas operativas.
- IDs son strings (cuid2), nunca números.
