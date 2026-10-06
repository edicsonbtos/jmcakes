# 08 — Inventario de endpoints (contrato v1)

**FND** declara **todos** estos endpoints con su router, esquemas Pydantic de request/response y roles; el cuerpo devuelve `501 NOT_IMPLEMENTED` hasta que el bloque dueño lo implemente. Así `contracts/openapi.json` está completo desde la Fase 0 y W1, W2 y M trabajan contra el mock.

- Prefijo `/api/v1`, salvo `/api/health`.
- Roles: **P** público · **C** cliente · **A** admin · **K** producción (cocina) · **D** delivery.
- Dinero como string decimal. Fechas ISO-8601 con zona (`Z`).
- Listas paginadas por cursor: `?cursor=&limit=` → `{items, nextCursor}`.

## Auth y cuenta — dueño FND
| Método y ruta | Rol | Notas |
|---|---|---|
| `GET /api/health` | P | `{status, version, db}`; healthcheck de Railway. |
| `POST /auth/register` | P | Cliente nuevo (CASH, sin aprobación) → `{accessToken, refreshToken, user, customer}`. |
| `POST /auth/login` | P | `{phone, password}`, con rate limit. |
| `POST /auth/refresh` · `POST /auth/logout` | C A K D | Refresh rotativo. |
| `GET /auth/me` | C A K D | Usuario + rol + resumen de cliente si aplica. |
| `POST /auth/device-tokens` · `DELETE /auth/device-tokens/{token}` | C D | FCM. |
| `DELETE /auth/account` | C | Requisito de Play Store: desactiva el usuario y anonimiza el perfil; conserva los registros contables. |

## Catálogo, archivos, clientes, usuarios y configuración — dueño B1
| Método y ruta | Rol | Notas |
|---|---|---|
| `GET /catalog` | C A | Categorías activas con productos publicados (incluye agotados, marcados). |
| `GET·POST /admin/categories` · `PATCH /admin/categories/{id}` | A | |
| `GET·POST /admin/products` · `GET·PATCH /admin/products/{id}` | A | Publicar/ocultar, disponible, mínimo, foto. |
| `POST /admin/products/bulk-price/preview` · `POST /admin/products/bulk-price/apply` | A | `{productIds? , categoryId?, mode: PERCENT\|AMOUNT, value, roundTo?}`. `apply` exige el `previewToken` devuelto por `preview`. |
| `GET /admin/products/{id}/price-history` | A | |
| `POST /files/upload-url` · `POST /files/{id}/complete` · `GET /files/{id}/url` | C A | URL prefirmada (bucket) o adaptador local. El cliente solo lee sus propios comprobantes. |
| `GET·PATCH /me/profile` | C | Dirección, referencia, contacto, segmento. No cambia modo ni crédito. |
| `GET·POST /admin/customers` · `GET·PATCH /admin/customers/{id}` | A | Filtros: `query`, `type`, `paymentMode`, `hasDebt`, `blocked`. Incluye billetera y deuda (vía `FinanceQueries` de B3). |
| `POST /admin/customers/{id}/credit` | A | `{paymentMode, creditLimit, creditDays}`; auditoría y push. |
| `POST /admin/customers/{id}/block` · `.../unblock` | A | |
| `GET·POST /admin/users` · `PATCH /admin/users/{id}` · `POST /admin/users/{id}/reset-password` | A | Usuarios ADMIN, PRODUCTION y DELIVERY. |
| `GET /settings/public` | P | Nombre del negocio, contacto, horario, `minLeadMinutes`, `maxDaysAhead`, `deliveryFee`, versiones mínimas de las apps. |
| `GET·PATCH /admin/settings` | A | Validación tipada de las claves de 02. |
| `GET /admin/audit` | A | Filtros: `entity`, `entityId`, `actor`. |

## Pedidos, cocina, delivery y eventos — dueño B2
| Método y ruta | Rol | Notas |
|---|---|---|
| `POST /orders/quote` | C | Sin efectos: totales, `walletWillUse`, `amountDue` (USD y Bs), `creditAvailable`, errores de validación. |
| `POST /orders` | C | `Idempotency-Key`. `{items[{productId, qty}], fulfillmentType, scheduledFor?, notes?, deliveryAddressText?, deliveryAddressReference?}` → `OrderDetail` + `checkout{walletUsed, amountDue, amountDueVes, rate, paymentMethods[]}`. |
| `GET /orders` · `GET /orders/{id}` | C | Solo los propios. Incluye pagos del pedido y su estado. |
| `POST /orders/{id}/cancel` | C | Solo en AWAITING_PAYMENT o CONFIRMED. |
| `GET /admin/orders` · `GET /admin/orders/{id}` | A | Filtros: `status`, `date` (dueAt Caracas), `customerId`, `channel`. Incluye bitácora. |
| `POST /admin/orders` | A | Pedido en nombre de un cliente (mismas reglas de cobro). |
| `POST /admin/orders/{id}/cancel` · `POST /admin/orders/{id}/reduce` · `POST /admin/orders/{id}/transition` | A | `reduce`: `{items[{orderItemId, qty}]}`. |
| `GET /kitchen/board` | K A | `{today:{new[], preparing[], ready[]}, scheduled:[{date, orders[]}]}` **sin montos**. |
| `POST /kitchen/orders/{id}/preparing` · `POST /kitchen/orders/{id}/ready` | K A | `ready` asigna al motorizado. |
| `GET /kitchen/production-totals?date=` | K A | Producto → cantidad. |
| `GET /delivery/orders` | D | `{ready[], outForDelivery[], deliveredTodayCount}`. Solo los asignados. |
| `POST /delivery/orders/out-for-delivery` · `POST /delivery/orders/{id}/delivered` | D | El primero recibe `{orderIds[]}`. |
| `POST /events/token` · `GET /events?token=` | K A | SSE. Tipos: `order.confirmed`, `order.updated`, `order.cancelled`, `payment.reported`, `payment.updated`, `heartbeat`. |

## Dinero, tasa, dashboard y cierres — dueño B3
| Método y ruta | Rol | Notas |
|---|---|---|
| `GET /rates/today` | P | `{date, value, rateType}` (lógica de OpenGravity). |
| `GET /payment-methods` | C | Métodos activos con cuentas bancarias (los “datos para pagar”). |
| `POST /payments` | C | `Idempotency-Key`. `{purpose: ORDER\|WALLET_TOPUP, orderId?, paymentMethodId, bankAccountId, currency, amountLocal, reference, paidOn, senderName?, proofFileId?}`. |
| `GET /payments` | C | Propios, con estado y motivo de rechazo. |
| `GET /me/wallet` · `GET /me/wallet/movements` | C | `{walletBalance, openDebt, overdueDebt, paymentMode, creditLimit, creditAvailable, receivables[]}` + movimientos paginados. |
| `GET /admin/payments` · `GET /admin/payments/{id}` | A | Filtros: `status`, `date`, `customerId`. Incluye la URL del comprobante. |
| `POST /admin/payments/{id}/take` · `.../approve` · `.../reject` · `.../reverse` | A | `approve {amountUsd?, bcvRateUsed?, note?}` · `reject {reason}` · `reverse {reason}`. |
| `POST /admin/customers/{id}/manual-payment` | A | Abono en el local (pago APPROVED, `purpose = MANUAL`). |
| `POST /admin/customers/{id}/charges` | A | Fiado o cargo manual → CxC MANUAL. |
| `POST /admin/customers/{id}/adjustments` | A | ± con nota obligatoria. |
| `GET /admin/customers/{id}/statement?from&to&format=csv` | A | Estado de cuenta. |
| `GET /admin/receivables` · `GET /admin/receivables/aging` · `POST /admin/receivables/{id}/void` | A | |
| `GET·POST·PATCH /admin/payment-methods` · `/admin/bank-accounts` | A | CRUD de OpenGravity. |
| `GET·POST /admin/cash-accounts` · `GET /admin/cash-accounts/{id}/transactions` | A | Cuentas del negocio. |
| `GET /admin/rates` · `POST /admin/rates/manual` · `POST /admin/rates/sync` | A | |
| `GET /admin/dashboard/summary?date=` · `GET /admin/dashboard/top-products?range=` | A | Métricas de 03 §6. |
| `GET /admin/closures` · `GET /admin/closures/{date}` · `GET /admin/closures/{date}/pdf` · `POST /admin/closures/{date}/run` | A | |
| `GET /admin/export/{payments\|receivables\|orders}.csv?from&to` | A | |

## Interfaces internas entre bloques (FND crea los stubs)
```python
# api/src/domain/catalog/interface.py      — implementa B1, consume B2
class CatalogService(Protocol):
    async def price_lines(self, session, lines: list[LineIn]) -> list[PricedLine]: ...   # valida publicado, disponible y minQty

# api/src/domain/customers/interface.py    — implementa B1, consumen B2/B3
class CustomersService(Protocol):
    async def get_for_update(self, session, customer_id: str) -> CustomerDB: ...
    async def get_by_user(self, session, user_id: str) -> CustomerDB | None: ...

# api/src/services/money.py                — implementa B3, consume B2
class MoneyService(Protocol):
    async def assert_can_order(self, session, customer: CustomerDB) -> None: ...       # bloqueo y deuda vencida
    async def checkout(self, session, customer: CustomerDB, order: OrderDB) -> CheckoutResult: ...  # 03 §3.1/§3.2
    async def on_order_cancelled(self, session, order: OrderDB) -> None: ...           # 03 §3.8
    async def on_order_reduced(self, session, order: OrderDB, old_total: Decimal) -> None: ...  # 03 §3.9
    async def quote(self, session, customer: CustomerDB, total: Decimal) -> QuoteResult: ...

# api/src/domain/orders/interface.py       — implementa B2, consume B3
class OrdersService(Protocol):
    async def confirm_paid(self, session, order: OrderDB, actor_id: str | None) -> None: ...  # AWAITING_PAYMENT → CONFIRMED + evento

# api/src/services/events.py · push.py     — implementa B2, consumen B1/B3
class EventBus(Protocol):
    def publish_after_commit(self, session, event: DomainEvent) -> None: ...
class PushSender(Protocol):
    async def send_to_user(self, session, user_id: str, title: str, body: str, data: dict) -> None: ...

# api/src/domain/finance/queries.py        — implementa B3, consume B1
class FinanceQueries(Protocol):
    async def balances_for(self, session, customer_ids: list[str]) -> dict[str, CustomerBalance]: ...
```
Los stubs de FND tienen un comportamiento mínimo coherente para que cada bloque pruebe lo suyo aislado:
- `checkout` confirma si el cliente es CREDIT y deja AWAITING_PAYMENT si es CASH, sin mover dinero;
- `price_lines` usa el precio del producto;
- `EventBus` registra los eventos en una lista.
