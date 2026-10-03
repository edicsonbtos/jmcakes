# 02 — Modelo de datos

Esquema lógico para Postgres (Neon). El bloque **F0** lo implementa en Drizzle con migraciones. Los nombres de tablas y columnas van en inglés (`snake_case`); la interfaz en español.

Convenciones: `id uuid pk default gen_random_uuid()`, `created_at timestamptz default now()`, `updated_at timestamptz`. Montos en `*_cents bigint` en moneda base.

## Identidad y acceso

### `users`
| Columna | Tipo | Notas |
|---|---|---|
| id | uuid | |
| role | enum `ADMIN \| PRODUCTION \| DELIVERY \| CUSTOMER` | |
| phone | text unique | Formato E.164 (`+58414...`). Login principal. |
| email | text unique null | Opcional. |
| password_hash | text | argon2id |
| full_name | text | |
| status | enum `PENDING \| ACTIVE \| BLOCKED` | Clientes nuevos quedan `PENDING` hasta aprobación (ver cuestionario). |
| last_login_at | timestamptz | |

### `refresh_tokens`
`id, user_id, token_hash, expires_at, revoked_at, device_label`

### `device_tokens`
`id, user_id, fcm_token unique, platform ('android'), app ('cliente'|'delivery'), last_seen_at` — para push.

## Clientes

### `customers` (1:1 con `users` de rol CUSTOMER; también existen clientes sin usuario creados por el admin, p. ej. de mostrador)
| Columna | Tipo | Notas |
|---|---|---|
| id | uuid | |
| user_id | uuid null fk | null = cliente sin app (solo backoffice). |
| type | enum `RETAIL \| WHOLESALE` | Detal / mayorista. |
| business_name | text null | Nombre del negocio del mayorista. |
| contact_name | text | |
| phone | text | |
| rif_ci | text null | RIF o cédula. |
| address_text | text | Dirección de entrega (texto libre). |
| address_reference | text null | “Frente a la panadería X…” |
| payment_mode | enum `CASH \| CREDIT` | **Contado** o **crédito**. Lo cambia solo el admin. |
| credit_limit_cents | bigint default 0 | Solo aplica en `CREDIT`. |
| credit_days | int default 7 | Días para considerar vencida una factura. |
| wallet_balance_cents | bigint default 0 **check ≥ 0** | Caché del ledger; se actualiza en la misma transacción. |
| price_list_id | uuid null | Para precios especiales por cliente (opcional, ver cuestionario). |
| notes | text | |
| is_active | bool | |

## Catálogo

### `categories`
`id, name, sort_order, is_active`

### `products`
| Columna | Tipo | Notas |
|---|---|---|
| id | uuid | |
| category_id | uuid fk | |
| name | text | “Canilla” |
| description | text null | |
| unit_label | text | “unidad”, “bolsa x10”, “docena” |
| price_cents | bigint | Precio mayorista base. |
| min_qty | int default 1 | Pedido mínimo por línea. |
| image_key | text null | Clave en el bucket. |
| is_published | bool | Visible en la app. |
| is_available | bool | Agotado hoy (visible pero no pedible). |
| sort_order | int | |

### `price_history`
`id, product_id, old_price_cents, new_price_cents, changed_by, changed_at` — auditoría de “subir y bajar precios”.

### `price_lists` / `price_list_items` (opcional v1)
Precios especiales por cliente: `price_list_items(price_list_id, product_id, price_cents)`.

## Pedidos

### `orders`
| Columna | Tipo | Notas |
|---|---|---|
| id | uuid | |
| number | serial unique | Número corto visible: **#1042**. |
| customer_id | uuid fk | |
| created_by | uuid fk users | Cliente o admin. |
| channel | enum `APP \| BACKOFFICE` | |
| status | enum (ver [flujos](03-flujos-de-negocio.md)) | |
| payment_mode | enum `CASH \| CREDIT` | Copiado del cliente al crear (snapshot). |
| subtotal_cents, total_cents | bigint | |
| delivery_address_text | text | Snapshot de la dirección. |
| requested_delivery_date | date | Fecha de entrega (día de Caracas). |
| notes | text null | |
| assigned_driver_id | uuid null fk users | Se llena al pasar a `READY`. |
| idempotency_key | text unique null | |
| confirmed_at, preparing_at, ready_at, out_for_delivery_at, delivered_at, cancelled_at | timestamptz | Marcas de cada estado. |
| cancel_reason | text null | |

### `order_items`
`id, order_id, product_id, product_name_snapshot, unit_label_snapshot, unit_price_cents, qty, line_total_cents`

### `order_events`
`id, order_id, from_status, to_status, actor_user_id, at, note` — bitácora de auditoría.

## Finanzas

### `receivables` (cuentas por cobrar: una por pedido a crédito o cargo manual)
| Columna | Tipo | Notas |
|---|---|---|
| id | uuid | |
| customer_id | uuid fk | |
| source | enum `ORDER \| MANUAL` | |
| order_id | uuid null unique | |
| description | text | |
| amount_cents | bigint | |
| paid_cents | bigint default 0 | |
| status | enum `OPEN \| PARTIAL \| PAID \| VOID` | |
| issued_at | timestamptz | |
| due_at | timestamptz | `issued_at + credit_days`. |

### `payments` (reportados por el cliente o registrados por el admin)
| Columna | Tipo | Notas |
|---|---|---|
| id | uuid | |
| customer_id | uuid fk | |
| order_id | uuid null | Si es pago de contado de un pedido específico. |
| method | enum `PAGO_MOVIL \| TRANSFERENCIA \| ZELLE \| EFECTIVO_USD \| EFECTIVO_VES \| PUNTO_VENTA \| OTRO` | |
| currency | enum `USD \| VES` | |
| amount_original | numeric(14,2) | En la moneda reportada. |
| exchange_rate | numeric(14,4) null | Tasa aplicada si `VES`. |
| amount_cents | bigint | Equivalente en moneda base (se fija al aprobar). |
| reference | text | Nº de referencia bancaria. **Unique por (method, reference)** para evitar doble reporte. |
| paid_on | date | Fecha del pago según el cliente. |
| proof_image_key | text null | Capture del comprobante. |
| status | enum `PENDING \| APPROVED \| REJECTED` | |
| reviewed_by, reviewed_at, reject_reason | | |
| idempotency_key | text unique null | |

### `wallet_entries` (libro contable de la billetera — **solo inserción**)
| Columna | Tipo | Notas |
|---|---|---|
| id | uuid | |
| customer_id | uuid fk | |
| type | enum `PAYMENT_IN \| APPLIED_TO_RECEIVABLE \| ADJUSTMENT \| REFUND_OUT` | |
| amount_cents | bigint | Positivo = entra a la billetera; negativo = sale. |
| payment_id | uuid null | |
| receivable_id | uuid null | |
| balance_after_cents | bigint | Saldo resultante (facilita auditoría). |
| created_by | uuid | |
| note | text | |

Invariante: `customers.wallet_balance_cents = SUM(wallet_entries.amount_cents)` y nunca negativo.

### `receivable_allocations`
`id, receivable_id, wallet_entry_id, amount_cents, created_at` — qué parte de qué factura se pagó con qué movimiento.

### `exchange_rates`
`id, date (día de Caracas) unique, ves_per_usd numeric(14,4), source ('MANUAL'|'BCV'), created_by`

## Configuración y operación

### `settings` (clave–valor tipado)
- `business.name`, `business.phone`
- `orders.cutoff_time` (p. ej. `"18:00"` — pedidos después de esa hora pasan a la fecha siguiente)
- `orders.allow_customer_cancel_until` (`CONFIRMED`)
- `delivery.default_driver_id` (el único motorizado)
- `credit.block_if_overdue_days` (bloquear pedidos si tiene facturas vencidas hace más de N días)
- `currency.base` (`USD`)

### `audit_log`
`id, actor_user_id, action, entity, entity_id, before jsonb, after jsonb, at` — cambios de precio, crédito, aprobaciones de pago, ajustes manuales.

## Índices clave
- `orders(status, requested_delivery_date)` — cola de cocina.
- `orders(assigned_driver_id, status)` — app del motorizado.
- `receivables(customer_id, status, issued_at)` — aplicación FIFO.
- `payments(status, created_at)` — bandeja de verificación.
- `payments(method, reference)` unique.
