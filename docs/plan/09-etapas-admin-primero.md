# 09 — Entrega por etapas: primero la web del administrador (v2.4)

> **Decisión del dueño (2026-10-14):** se construye **primero la web del administrador**, empezando por el **cuaderno de clientes** (fiado de mostrador y abonos), y a partir de ahí las demás apps. **Sin sobreingeniería.**
>
> Los documentos 01–08 siguen siendo el diseño completo de destino. Este documento define **qué se construye en cada etapa** y **prevalece sobre el orden de 04**.

## Orden de etapas
| Etapa | Qué recibe el dueño | Se puede usar en el negocio |
|---|---|---|
| **E1 — Admin web + cuaderno de clientes** | Panel web con clientes y su saldo, fiado de productos, abonos con referencia, estado de cuenta, productos y precios (mayor y detal), tasa BCV, inicio con totales. | **Sí**, desde el primer día: reemplaza el cuaderno de deudas del mostrador. |
| E2 — Pedidos y cocina | Pedidos creados desde el panel (por WhatsApp o teléfono), “hoy” o programados; pantalla de cocina en tablet. | Sí |
| E3 — App del motorizado | APK con “En camino” y “Entregado”. | Sí |
| E4 — App del cliente mayorista | Registro, catálogo, pedidos, billetera, reporte y aprobación de pagos, crédito. | Sí (Play Store) |

Cada etapa se diseña sobre el modelo completo de 02 y 03. Por eso no hay que rehacer nada al pasar a la siguiente: solo se **agregan** tablas, endpoints y pantallas.

---

## E1 — Alcance

### Lo que SÍ entra
1. **Acceso:** login del administrador (teléfono + contraseña), uno o varios administradores.
2. **Clientes** (detal y mayoristas, sin app por ahora):
   - lista con **saldo** (debe / a favor), búsqueda por nombre, negocio, teléfono o cédula/RIF;
   - filtro “con deuda” y “vencidos”, ordenada por mayor deuda;
   - total “Por cobrar” arriba.
3. **Ficha del cliente:**
   - **saldo grande**: “Debe $X (Bs Y)” o “A favor $X”;
   - dos botones principales: **Fiar productos** y **Registrar abono**;
   - historial de movimientos (fiados y abonos, con fecha, hora, quién lo registró y saldo resultante);
   - estado de cuenta para imprimir o compartir por WhatsApp (texto);
   - editar los datos del cliente.
4. **Fiar productos:**
   - **Qué se registra:** se eligen productos del catálogo y cantidades. El precio sale del catálogo (**precio detal** para clientes de detal, **precio mayor** para mayoristas) y se puede **editar por línea**. También se permite una nota o un cargo libre (“Otro”, con monto).
   - **Efecto en el saldo:** la deuda **sube**. Si el cliente tenía saldo a favor, se descuenta primero automáticamente.
5. **Registrar abono:**
   - **Datos:** monto, moneda (USD o Bs), **referencia de pago**, método (pago móvil, transferencia, Zelle, efectivo), cuenta donde entró y fecha. En Bs, la conversión usa la tasa del día del pago, que el admin puede corregir.
   - **Efecto en el saldo:** la deuda **baja**, de lo más viejo a lo más nuevo. Si el abono supera la deuda, el sobrante queda **a favor**.
6. **Corregir errores:** **anular un fiado** (con motivo; lo ya abonado sobre él queda a favor) y **revertir un abono** (con motivo; la deuda vuelve a subir). Nada se borra; todo queda en el historial y en la auditoría.
7. **Carga inicial:**
   - al crear un cliente se puede poner su **deuda actual** (“Saldo anterior”);
   - **importación por CSV** de la lista existente: nombre, teléfono, tipo, deuda y nota. Primero se ve una vista previa con los errores marcados por fila, y luego se confirma.
8. **Productos y precios:** categorías, productos con **precio mayor** y **precio detal**, activar o desactivar, **cambio masivo de precios** con vista previa (subir o bajar por porcentaje o monto), historial de precios.
9. **Tasa BCV del día:** se toma automáticamente a las 06:00, y el admin puede fijarla a mano. Todo saldo se muestra en USD y en Bs.
10. **Inicio:** total por cobrar (detal / mayoristas), abonos de hoy por método, fiado de hoy, clientes con deuda vencida, top 10 deudores.
11. **Configuración mínima:** nombre del negocio, WhatsApp, métodos de cobro y cuentas, días de crédito por defecto y administradores.
12. **Auditoría:** quién hizo qué y cuándo.

### Lo que NO entra en E1 (llega en E2–E4)
Pedidos, cocina, motorizado, app del cliente, billetera vista por el cliente, pagos reportados por el cliente y su bandeja de aprobación, push, cierres diarios con PDF, fotos de productos, Web Push.

---

## E1 — Reglas (subconjunto exacto de 03; probado en `spec/`)
| Acción | Regla de 03 | Modelo (`spec/money_model.py`) |
|---|---|---|
| Fiar productos o saldo anterior | CxC `source = MANUAL` con líneas (§3.11, cargo manual); luego `settle` | `manual_charge` |
| Registrar abono | Pago `purpose = MANUAL` en APPROVED, que entra a la billetera; luego `settle` FIFO; el sobrante queda a favor (§3.4–§3.5) | `report_payment` + `approve` |
| Anular fiado | §3.11 Anular (MANUAL): lo pagado vuelve a favor | `void_receivable` |
| Revertir abono | §3.7: si no hay saldo a favor suficiente, la diferencia vuelve como deuda | `reverse` |
| Saldo mostrado | `saldo = deuda abierta − saldo a favor` (positivo = debe) | `balance()` en las pruebas |

**Escenarios probados:**
- `test_cuaderno_fiado_y_abonos_suben_y_bajan_la_deuda`;
- `test_cuaderno_anular_fiado_y_revertir_abono`;
- además, todas las invariantes. `spec`: **36 de 36 en verde**.

Los fiados del admin **no** pasan por `OPEN_DEBT` ni por el límite de crédito: el admin decide. Si el cliente tiene un `creditLimit` y el fiado lo supera, se muestra una **advertencia**, sin bloquear.

## E1 — Datos
Una sola migración inicial con **solo** estas tablas, tal como se definen en 02:
- **usuarios y configuración:** `users`, `refresh_tokens`, `app_settings`, `audit_logs`, `idempotency_records`;
- **clientes y catálogo:** `customers`, `categories`, `products`, `price_history`;
- **dinero:** `receivables`, `wallet_movements`, `payments`, `payment_methods`, `bank_accounts`, `cash_accounts`, `cash_account_transactions`, `exchange_rates`.

Agregados respecto a 02, que también quedan para las etapas siguientes:
- `products.retailPrice` (precio detal, null = usa `price`);
- **`receivable_items`** (`receivableId`, `productId` null, `productName`, `unitLabel`, `qty`, `unitPrice`, `lineTotal`): las líneas de un fiado;
- `receivables.source` agrega el valor `OPENING_BALANCE` (saldo anterior; se comporta igual que MANUAL).

Pedidos, archivos, tokens de dispositivo y cierres se crean en su etapa, con migraciones nuevas.

## E1 — API (subconjunto de 08 + 3 nuevos)
- **Acceso y sistema:** `auth` (solo admin: login, refresh, logout, me) y `health`.
- **Catálogo:** categorías y productos (admin) con `retailPrice`, cambio masivo de precios e historial.
- **Clientes:** `GET·POST·PATCH /admin/customers` con `balance`, `openDebt`, `walletBalance`, `overdueDebt` y Bs.
- **Cuaderno:**
  - **nuevo** `POST /admin/customers/{id}/fiado` `{items[{productId?, name?, qty, unitPrice?}], note?, dueDate?}` (`Idempotency-Key`). Sin `productId` = cargo libre “Otro”;
  - `POST /admin/customers/{id}/manual-payment` (abono, `Idempotency-Key`);
  - `POST /admin/receivables/{id}/void`;
  - `POST /admin/payments/{id}/reverse`;
  - `GET /admin/customers/{id}/statement` (JSON / CSV / texto para WhatsApp: `format=whatsapp`).
- **Carga inicial:** **nuevo** `POST /admin/customers/import/preview` (CSV → filas validadas + `previewToken`) y **nuevo** `POST /admin/customers/import/apply` `{previewToken}`.
- **Tasa:** `GET /rates/today`, `GET /admin/rates`, `POST /admin/rates/manual`, `POST /admin/rates/sync`. Job 06:00.
- **Cobros:** `GET·POST·PATCH /admin/payment-methods`, `/admin/bank-accounts`, `/admin/cash-accounts` (+ transacciones).
- **Resto:** `GET /admin/dashboard/summary` (métricas E1), `GET·PATCH /admin/settings` (secciones `business` y `credit`), `GET·POST·PATCH /admin/users` (solo ADMIN) y `GET /admin/audit`.

## E1 — Pantallas (web admin)
| Ruta | Pantalla |
|---|---|
| `/login` | Teléfono + contraseña. |
| `/admin` | **Inicio:** Por cobrar · Abonos de hoy · Fiado de hoy · Vencidos · Top deudores. |
| `/admin/clientes` | **Lista** con saldo, búsqueda y filtros, botón “Nuevo cliente” e “Importar”. |
| `/admin/clientes/[id]` | **Ficha:** saldo grande, **Fiar productos**, **Registrar abono**, historial, estado de cuenta, editar. |
| `/admin/clientes/importar` | CSV → vista previa con errores → confirmar. |
| `/admin/productos` | Productos y categorías, precio mayor y detal, cambio masivo. |
| `/admin/tasa` | Tasa de hoy e historial; fijar manual o sincronizar. |
| `/admin/configuracion` | Negocio, cobros (métodos, cuentas), crédito por defecto, administradores. |
| `/admin/auditoria` | Registro. |

**Requisitos de uso:**
- **Teléfono primero:** el dueño registra un abono en menos de 15 segundos desde el celular. La ficha muestra el saldo arriba y los dos botones al alcance del pulgar.
- **Fiar rápido:** buscador de productos con − / + y total en vivo, **calculado por la API** con un preview; la web no calcula dinero.

## E1 — Agentes (6) y orden
```
E1.0 (paralelo):   FND-E1  API base (solo tablas E1) + auth + contrato E1 + pruebas base
                   DSN     dirección visual (con el dueño, G0.5) + base web + UI kit
E1.1 (paralelo):   B-E1a   catálogo, clientes (CRUD, import), configuración, usuarios, auditoría
                   B-E1b   cuaderno (fiado, abonos, anular/revertir, estado de cuenta), tasa, cobros, inicio
                   W-E1    pantallas del admin (contra el mock; luego contra la API real)
E1.2:              Q-E1    integración, E2E de los escenarios del cuaderno, despliegue en staging
                           (Railway + Neon) y verificación; entrega de acceso al dueño
```
- Cada agente sigue el protocolo 05: worktree propio, sin push, el orquestador integra.
- Las fichas de 01–08 aplican, **recortadas a E1** según este documento. Lo que no está en E1 no se implementa: ni stubs, ni pantallas vacías, ni menús.

**Compuertas E1**
- **G1-E1:** API base verde (migración, auth, inventario E1) + DESIGN.md + base web verde.
- **G2-E1:** cuaderno con los escenarios de `spec` portados a la API, cada uno seguido de `assert_money_invariants`; pantallas completas contra el mock.
- **G3-E1:** E2E en CI (crear cliente con saldo anterior → fiar → abonar → saldo a favor → nuevo fiado → anular → revertir) + staging en línea + login del dueño + importación de un CSV de prueba.

**Requiere al dueño en E1:**
- elegir la dirección visual (G0.5, unos minutos);
- aprobar el despliegue en Railway;
- **entregar la lista de deudores** (CSV o Excel: nombre, teléfono, deuda), los precios de mayor y detal, y los métodos de cobro con sus cuentas.

## Etapas siguientes (resumen)
| Etapa | Agentes | Agrega |
|---|---|---|
| **E2** | B2 (pedidos, agenda, cocina, SSE), W2 (cocina), W1+ (pedidos en el panel) | `orders`, `order_items`, `order_events`; pedidos “hoy” / programados creados por el admin; cocina en tablet. |
| **E3** | M-delivery, B2+ (delivery, push) | `device_tokens`; app del motorizado. |
| **E4** | M-cliente, B3+ (pagos reportados, billetera de la app, crédito), B1+ (registro, archivos, imágenes), W1+ (bandeja de pagos, Web Push) | Todo lo demás de 01–08. |
