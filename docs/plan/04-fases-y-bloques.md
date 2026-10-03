# 04 — Fases y bloques para agentes autónomos

El proyecto se divide en **11 bloques** agrupados en **5 fases**. Cada bloque es una unidad que un agente de Claude puede ejecutar de principio a fin en una sesión en la nube, con entradas, salidas, límites y criterio de terminado bien definidos.

La pieza que permite el paralelismo es el **contrato de API** (`contracts/openapi.yaml`) que produce la Fase 0: con él, la web y las apps Android pueden construirse contra un **servidor mock** mientras el backend se construye al mismo tiempo.

## Mapa de dependencias

```
FASE 0 (secuencial)      FASE 1 (paralelo: backend)        FASE 2 (paralelo: interfaces)      FASE 3          FASE 4
                                                            ── arrancan contra MOCK al ──
                                                               terminar F0, cierran contra
                                                               staging al terminar Fase 1

                    ┌──▶ B1 API Catálogo/Clientes ──┐      ┌──▶ W1 Web Admin ───────────┐
                    │                               │      │                            │
 F0 Fundación ──────┼──▶ B2 API Pedidos/Cocina/Del ─┼─────▶├──▶ W2 Web Cocina ──────────┼──▶ Q1 Integración ──▶ L1 Lanzamiento
 + contrato v1      │                               │      │                            │      y QA E2E          (prod, Play Store,
                    └──▶ B3 API Finanzas/Dashboard ─┘      ├──▶ M1 Android Cliente ─────┤                         APK, manuales)
                    │                                      │                            │
                    └──────────────── (mock) ─────────────▶└──▶ M2 Android Delivery ────┘
```

## Resumen de bloques

| ID | Bloque | Fase | Depende de | Paralelo con | Carpetas propias | Esfuerzo* |
|---|---|---|---|---|---|---|
| [F0](bloques/F0-fundacion.md) | Fundación, contrato, BD, auth, esqueletos, CI, infra | 0 | Cuestionario respondido (mín. C-1..C-5) | — | todo el esqueleto, `contracts/`, `api/src/db`, `api/src/lib`, `api/src/modules/auth`, `web/src/shared`, `android/core` | L |
| [B1](bloques/B1-api-catalogo-clientes.md) | API catálogo, clientes, configuración, imágenes | 1 | F0 | B2, B3, W*, M* | `api/src/modules/{catalog,customers,settings}` | M |
| [B2](bloques/B2-api-pedidos-produccion-delivery.md) | API pedidos, cocina, delivery, SSE, push | 1 | F0 | B1, B3, W*, M* | `api/src/modules/{orders,kitchen,delivery,notifications}` | L |
| [B3](bloques/B3-api-finanzas-dashboard.md) | API billetera, CxC, pagos, tasa, dashboard | 1 | F0 | B1, B2, W*, M* | `api/src/modules/{finance,dashboard}` | L |
| [W1](bloques/W1-web-admin.md) | Web backoffice del administrador | 2 | F0 (mock) → B1-B3 (real) | todos | `web/src/app/admin` | L |
| [W2](bloques/W2-web-cocina.md) | Web de producción (tablet) | 2 | F0 (mock) → B2 (real) | todos | `web/src/app/cocina` | S |
| [M1](bloques/M1-android-cliente.md) | App Android del cliente (Play Store) | 2 | F0 (mock) → B1-B3 (real) | todos | `android/app-cliente` | L |
| [M2](bloques/M2-android-delivery.md) | App Android del motorizado (APK) | 2 | F0 (mock) → B2 (real) | todos | `android/app-delivery` | S |
| [Q1](bloques/Q1-integracion-qa.md) | Integración end-to-end, QA, seguridad | 3 | B1-B3, W1, W2, M1, M2 | — | `e2e/`, correcciones transversales | M |
| [L1](bloques/L1-lanzamiento.md) | Producción, Play Store, APK, respaldo, manuales | 4 | Q1 | — | `docs/manuales`, `.github/workflows/release-*`, `android/*/fastlane` | M |

\* S ≈ 1 sesión de agente · M ≈ 1–2 sesiones · L ≈ 2–4 sesiones.

## Contratos internos entre bloques del backend

Para que B1, B2 y B3 no se bloqueen entre sí, F0 deja creadas estas **interfaces con implementación stub** en `api/src/modules/*/index.ts`. Cada bloque implementa la suya; los demás solo la llaman.

```ts
// api/src/modules/finance/index.ts  — implementa B3, consume B2
export interface FinanceService {
  assertCanPlaceOrder(customerId: string, totalCents: bigint): Promise<void>; // lanza CREDIT_LIMIT_EXCEEDED
  onOrderConfirmed(tx: Tx, order: Order): Promise<void>;   // crea receivable si CREDIT + settle()
  onOrderCancelled(tx: Tx, order: Order): Promise<void>;   // VOID + devolución a billetera
  onOrderDelivered(tx: Tx, order: Order): Promise<void>;   // fija due_at
}

// api/src/modules/orders/index.ts  — implementa B2, consume B3
export interface OrdersService {
  confirmPaidOrder(tx: Tx, orderId: string, actor: Actor): Promise<void>; // AWAITING_PAYMENT → CONFIRMED
}

// api/src/modules/notifications/index.ts — implementa B2, consumen B1/B3
export interface Notifier {
  publish(event: DomainEvent): void;               // SSE a web
  push(userId: string, msg: PushMessage): Promise<void>; // FCM
}

// api/src/modules/catalog/index.ts — implementa B1, consume B2
export interface CatalogService {
  priceOrderLines(customerId: string, lines: {productId: string; qty: number}[]): Promise<PricedLine[]>; // valida min_qty, disponibilidad, lista de precios
}

// api/src/modules/customers/index.ts — implementa B1, consumen B2/B3
export interface CustomersService {
  getForUpdate(tx: Tx, customerId: string): Promise<Customer>;
  getByUserId(userId: string): Promise<Customer | null>;
}
```

Los stubs de F0 devuelven valores razonables (p. ej. `assertCanPlaceOrder` no lanza) para que cada bloque pueda probar su parte aislado. Los tests de integración entre módulos los hace Q1.

## Orden de lanzamiento recomendado

1. **Responder el cuestionario** (al menos C-1 a C-5, que afectan el esquema).
2. Lanzar **F0** (una sesión). Revisar y hacer merge de su PR.
3. Lanzar en paralelo **B1, B2, B3, W1, W2, M1, M2** (7 sesiones). Los W/M trabajan contra el mock; cuando un B se fusiona, el W/M correspondiente cambia a staging.
   - Si se prefiere menos paralelismo: primero B1+B2+B3, luego W1+W2+M1+M2.
4. Lanzar **Q1** cuando todo lo anterior esté fusionado.
5. Lanzar **L1**.

Cada ficha de bloque incluye un **prompt listo para pegar** en una nueva sesión de Claude Code en la nube.
