# 09 — Entrega por etapas: primero la web del administrador (v2.5)

> **Decisión del dueño (2026-10-14):** se construye **primero la web del administrador**, empezando por el **cuaderno de clientes** (fiado de mostrador y abonos), y a partir de ahí las demás apps. **Sin sobreingeniería.**
>
> Los documentos 01–08 siguen siendo el diseño completo de destino. Este documento define **qué se construye en cada etapa**, **prevalece sobre el orden de 04** y, durante E1, **prevalece sobre las fichas** de `bloques/` (ver §E1 — Agentes).
>
> **Nombres:** las etapas son **E1–E4**. Los escenarios de aceptación de 07 §2 que se llaman `E1`…`E17` son otra cosa. Para no confundirlos, los escenarios del cuaderno se llaman **CU-1…CU-12** (§E1 — Aceptación).

## Orden de etapas
| Etapa | Qué recibe el dueño | Se puede usar en el negocio |
|---|---|---|
| **E1 — Admin web + cuaderno de clientes** | Panel web con clientes y su saldo, fiado de productos, abonos con referencia, estado de cuenta, productos y precios (mayor y detal), tasa BCV e inicio con totales. | **Sí**, desde el primer día: reemplaza el cuaderno de deudas del mostrador. |
| E2 — Pedidos y cocina | Pedidos creados desde el panel (por WhatsApp o teléfono), “hoy” o programados, y la pantalla de cocina en tablet. | Sí |
| E3 — App del motorizado | APK con “En camino” y “Entregado”. | Sí |
| E4 — App del cliente mayorista | Registro, catálogo, pedidos, billetera, reporte y aprobación de pagos, y crédito. | Sí (Play Store) |

Cada etapa se diseña sobre el modelo completo de 02 y 03. Por eso no hay que rehacer nada al pasar a la siguiente: solo se **agregan** endpoints, pantallas y, si hace falta, columnas.

---

## E1 — Alcance

### Lo que SÍ entra
1. **Acceso:**
   - login del administrador con teléfono y contraseña; puede haber uno o varios administradores;
   - **cambio de contraseña obligatorio en el primer ingreso** (`mustChangePassword`);
   - restablecer la contraseña de otro administrador.
2. **Clientes** (detal y mayoristas, sin app por ahora):
   - lista con **saldo** (debe / a favor) y búsqueda por nombre, negocio, teléfono o cédula/RIF;
   - filtros “con deuda” y “vencidos”, ordenada por mayor deuda;
   - total “Por cobrar” arriba.
3. **Ficha del cliente:**
   - **saldo grande**: “Debe $X (Bs Y)” o “A favor $X”;
   - dos botones principales: **Fiar productos** y **Registrar abono**;
   - historial de movimientos (fiados, abonos, anulaciones y reversos), con fecha, hora, quién lo registró y saldo resultante;
   - estado de cuenta para imprimir o compartir por WhatsApp (texto);
   - editar los datos del cliente, su límite de crédito y sus días de crédito.
4. **Fiar productos** (03 §3.10b):
   - **Qué se registra:** productos del catálogo y sus cantidades. El precio sale del catálogo (**precio detal** para clientes de detal, **precio mayor** para mayoristas) y se puede **editar por línea**. También se permite una nota o un cargo libre (“Otro”, con monto).
   - **Efecto en el saldo:** la deuda **sube**. Si el cliente tenía saldo a favor, se descuenta primero automáticamente.
   - **Total en vivo:** lo calcula la API con `fiado/quote`; la web no calcula dinero.
5. **Registrar abono:**
   - **Datos:** monto, moneda (USD o Bs), **referencia de pago** (no se pide en efectivo), método (pago móvil, transferencia, Zelle o efectivo), cuenta donde entró y fecha. En Bs, la conversión usa la tasa del día del pago, y el admin puede corregirla (`bcvRateUsed`).
   - **Efecto en el saldo:** la deuda **baja**, empezando por la que **vence primero**. Si el abono supera la deuda, el sobrante queda **a favor**.
6. **Corregir errores:**
   - **Anular un fiado o un saldo anterior** (con motivo): lo ya abonado sobre él se reaplica a las otras deudas, y solo el sobrante queda a favor.
   - **Revertir un abono** (con motivo): la deuda vuelve a subir. Si no hay saldo a favor suficiente, la diferencia aparece como deuda vencida.
   - Nada se borra: todo queda en el historial y en la auditoría.
7. **Carga inicial:**
   - al crear un cliente se puede poner su **saldo anterior** (deuda, o saldo a favor si es negativo);
   - **importación por CSV** de la lista existente, ver §E1 — Carga inicial.
8. **Productos y precios:**
   - categorías;
   - productos con **precio mayor** y **precio detal**, que se pueden activar o desactivar;
   - **cambio masivo de precios** con vista previa (subir o bajar por porcentaje o monto), del precio mayor o del precio detal;
   - historial de precios de los dos tipos.
9. **Tasa BCV del día:** se toma automáticamente a las 06:00, y el admin puede fijarla a mano. Todo saldo se muestra en USD y en Bs.
10. **Inicio:** total por cobrar (detal / mayoristas), abonos de hoy por método, fiado de hoy, clientes con deuda vencida y top 10 deudores (§E1 — Inicio).
11. **Configuración mínima:** nombre del negocio, WhatsApp, métodos de cobro y cuentas, días de crédito por defecto y administradores.
12. **Auditoría:** quién hizo qué y cuándo.

### Lo que NO entra en E1 (llega en E2–E4)
- Pedidos, cocina, motorizado y app del cliente.
- Billetera vista por el cliente, pagos reportados por el cliente y su bandeja de aprobación.
- Condonar deudas, devolver saldo a favor en dinero, ajustes manuales sueltos y bloqueo de clientes.
- Push, Web Push, SSE, cierres diarios con PDF y exportaciones.
- Fotos de productos y páginas públicas de Play Store.

---

## E1 — Reglas (subconjunto exacto de 03; probado en `spec/`)
| Acción | Regla de 03 | Modelo (`spec/money_model.py`) |
|---|---|---|
| Fiar productos | §3.10b: CxC `MANUAL` con líneas, `dueAt` por `creditDays`, sin OPEN_DEBT ni límite; luego `settle` | `fiado` |
| Saldo anterior | §3.10b: CxC `OPENING_BALANCE` (deuda) o `ADJUSTMENT(+)` (a favor) | `manual_charge(source="OPENING_BALANCE")` · `adjust` |
| Registrar abono | §3.10b + §3.4: pago `purpose = MANUAL` APPROVED, entra a la billetera; `settle` por `dueAt ASC`; el sobrante queda a favor | `report_payment` + `approve` |
| Anular fiado o saldo anterior | §3.11 Anular: lo pagado vuelve y `settle` lo reaplica | `void_receivable` |
| Revertir abono | §3.7: si no alcanza el saldo a favor, la diferencia es una CxC `PAYMENT_REVERSAL` vencida | `reverse` |
| Saldo y vencido | §3.10b: `balance = openDebt − walletBalance`; vencido = `dueAt < ahora` | `balance()` en las pruebas |
| Advertencia de límite | §3.10b: solo si `creditLimit > 0`; nunca bloquea | — (API) |

**Escenarios de `spec` del cuaderno** (B-E1b los porta a services sobre Postgres):
- todos los `test_cuaderno_*` (8, incluido `test_cuaderno_flujo_completo_de_g3_e1`, que recorre el E2E de G3-E1);
- `test_manual_charge_paid_from_wallet`, `test_m8_reversed_reference_stays_locked` y `test_r2_reference_unique_per_bank_account`;
- la prueba de propiedades restringida a las operaciones de E1 (`fiado`, `opening`, `pay` + `approve`, `reverse` y `void`);
- después de cada prueba, todas las invariantes.

`spec`: **54 de 54 en verde** (42 del modelo de dinero + 12 de coherencia del plan, `spec/test_plan_consistency.py`).

## E1 — Datos
**La migración inicial crea el esquema completo de 02**, igual que dice FND, aunque E1 solo use una parte. Así se corrige v2.4, que pedía crear solo las tablas de E1. Los motivos:
- las invariantes de 02 (I-2, I-4, I-5, I-6 e I-9), que `assert_money_invariants` copia **literalmente**, consultan `orders`. Sin esa tabla, la prueba de dinero de E1 no corre;
- `receivables.orderId`, `payments.orderId`, `wallet_movements.orderId`, `products.imageFileId` y `payments.proofFileId` son FK a `orders` y `files`. Sin esas tablas habría que crear las columnas sin FK y agregarlas después con migraciones;
- las tablas sin uso no cuestan nada, y E2–E4 solo agregan código.

Lo que **no** se construye en E1 son los endpoints, servicios, jobs y pantallas de esas tablas.

Agregados respecto a v2.3, ya incluidos en 02:
- `products.retailPrice` (precio detal; null = usa `price`);
- `price_history.priceType` (WHOLESALE / RETAIL);
- **`receivable_items`**, las líneas de un fiado;
- `receivables.source` con el valor `OPENING_BALANCE`.

**Seed de E1** (reemplaza el de 07 §5 durante E1; idempotente):
- el admin del bootstrap;
- 3 categorías y 12 productos con `price` y `retailPrice`;
- métodos de cobro: Pago móvil (Bs), Transferencia (Bs), Zelle (USD) y **Efectivo USD**, con la `bank_account` “Caja” ligada a la cuenta del negocio “Caja USD”;
- tasa BCV y MANUAL de hoy;
- 3 clientes sin app: uno de detal con saldo anterior de $50, un mayorista con un fiado de 2 líneas y un cliente con $10 a favor.

## E1 — Carga inicial (CSV)
- **Archivo:**
  - UTF-8, con o sin BOM; si no decodifica, se lee como Windows-1252 (Excel en español).
  - Separador `,` o `;`, detectado automáticamente. Máximo 1 MB y 2.000 filas.
  - Si el dueño entrega un Excel, se guarda como CSV antes de subirlo.
- **Encabezados** (sin importar mayúsculas ni acentos): `nombre` (obligatorio), `telefono`, `tipo`, `deuda`, `nota`, más los opcionales `negocio` y `cedula`.
- **Validación por fila** (los errores se muestran con el número de línea):

| Campo | Regla | Error |
|---|---|---|
| `nombre` | No vacío. Va a `customers.contactName`. | “Falta el nombre” |
| `telefono` | Opcional. Se normaliza a E.164 venezolano (`0414-123.45.67` → `+584141234567`). No puede repetirse en el archivo ni coincidir con el de un cliente existente. | “Teléfono inválido” · “Teléfono repetido en la línea N” · “Ya existe un cliente con ese teléfono” |
| `tipo` | `detal` o `mayor`/`mayorista`. Si está vacío, `detal`. | “Tipo debe ser detal o mayor” |
| `deuda` | Decimal con `.` o `,` como separador decimal, hasta 2 decimales y sin separador de miles. Si está vacía, 0. Si es negativa, es saldo a favor. | “Monto inválido: escribe 1234,56 sin puntos de miles” |

- **Aplicar:**
  - se crean solo las filas válidas, en **una transacción**: el cliente más su saldo anterior (03 §3.10b) mediante `MoneyService.open_balance`. Las filas con error se informan como `skipped`;
  - todo queda en auditoría con un `batchId`;
  - repetir el mismo `previewToken` devuelve el mismo resultado. El token dura 30 min; si venció → `409 IMPORT_PREVIEW_EXPIRED`.

## E1 — Inicio (`GET /admin/dashboard/summary?date=`, día de Caracas)
| Campo | Definición |
|---|---|
| `receivables{total, retail, wholesale, overdue}` | Σ(`amount − paidAmount`) de las CxC OPEN/PARTIAL; `overdue` con `dueAt < ahora`. |
| `walletTotal` | Σ `walletBalance` (saldo a favor de clientes). |
| `paymentsToday{totalUsd, byMethod[{paymentMethodId, name, currency, totalLocal, totalUsd}]}` | Pagos APPROVED o REVERSED con `approvedAt` en el día (regla de 03 §6). |
| `reversalsToday{count, totalUsd}` | Pagos REVERSED con `reversedAt` en el día. |
| `fiadoToday{count, totalUsd}` | CxC `MANUAL` (no `OPENING_BALANCE`) con `issuedAt` en el día y status ≠ VOID. |
| `overdueCustomersCount` | Clientes con `overdueDebt > 0`. |
| `topDebtors[10]{customerId, name, balance, overdueDebt}` | Por `balance` descendente. |

El esquema de E1 solo tiene estos campos. E2 agrega los de pedidos de 03 §6 sin quitar ninguno.

## E1 — API (51 operaciones; subconjunto de 08 + 5 nuevas)
**Inventario E1** (lo compara `test_contract_inventory.py` durante E1; en E2 se amplía hacia el de 08):
```
GET /api/health
POST /api/v1/auth/login|refresh|logout|change-password · GET /api/v1/auth/me
GET|POST /api/v1/admin/categories · PATCH /api/v1/admin/categories/{id}
GET|POST /api/v1/admin/products · GET|PATCH /api/v1/admin/products/{id} · POST /api/v1/admin/products/bulk-price/preview · POST /api/v1/admin/products/bulk-price/apply · GET /api/v1/admin/products/{id}/price-history
GET|POST /api/v1/admin/customers · GET|PATCH /api/v1/admin/customers/{id} · POST /api/v1/admin/customers/{id}/credit
POST /api/v1/admin/customers/import/preview · POST /api/v1/admin/customers/import/apply
GET|POST /api/v1/admin/users · PATCH /api/v1/admin/users/{id} · POST /api/v1/admin/users/{id}/reset-password
GET /api/v1/settings/public · GET|PATCH /api/v1/admin/settings · GET /api/v1/admin/audit
GET /api/v1/rates/today · GET /api/v1/admin/rates · POST /api/v1/admin/rates/manual|sync
GET|POST /api/v1/admin/payment-methods · PATCH /api/v1/admin/payment-methods/{id} · GET|POST /api/v1/admin/bank-accounts · PATCH /api/v1/admin/bank-accounts/{id}
GET|POST /api/v1/admin/cash-accounts · GET /api/v1/admin/cash-accounts/{id}/transactions
POST /api/v1/admin/customers/{id}/fiado/quote · POST /api/v1/admin/customers/{id}/fiado · POST /api/v1/admin/customers/{id}/manual-payment
POST /api/v1/admin/receivables/{id}/void · POST /api/v1/admin/payments/{id}/reverse · GET /api/v1/admin/customers/{id}/statement
GET /api/v1/admin/dashboard/summary
```
**Nuevas respecto a v2.3:** `fiado`, `fiado/quote`, `import/preview`, `import/apply` y `auth/change-password`. Su contrato está en 08 §Agregados.

Notas de E1 sobre operaciones existentes:
- **`auth`:** solo el rol ADMIN inicia sesión en E1. `register`, `device-tokens` y `DELETE /auth/account` llegan en E4.
- **`POST /admin/users`:** en E1 solo crea usuarios ADMIN; los demás roles llegan con su etapa.
- **`POST /admin/customers/{id}/credit`:** en E1 solo guarda `creditLimit` y `creditDays` (`paymentMode` queda CASH) y audita, sin push.
- **`/admin/settings`:** en E1 solo las secciones `business` y `credit`. `/settings/public` alimenta el nombre del negocio en la barra superior.
- **`/admin/cash-accounts`:** no tiene PATCH (08). Para desactivar una cuenta, se desactiva su `bank_account` o su método.
- **`reverse` y `void`:** piden `{reason}`. En la ficha, el `paymentId` y el `receivableId` salen de las filas del estado de cuenta.
- Lo que no está en el inventario **no existe** en E1: ni rutas 501, ni stubs, ni pantallas vacías, ni menús.

## E1 — Pantallas (web admin)
| Ruta | Pantalla | Dueño |
|---|---|---|
| `/login` | Teléfono + contraseña. | DSN |
| `/cambiar-contrasena` | Se muestra si `mustChangePassword`; no deja seguir sin cambiarla. | W-E1 |
| `/admin` | **Inicio:** Por cobrar · Abonos de hoy · Fiado de hoy · Vencidos · Top deudores. | W-E1 |
| `/admin/clientes` | **Lista** con saldo, búsqueda y filtros, y los botones “Nuevo cliente” e “Importar”. | W-E1 |
| `/admin/clientes/[id]` | **Ficha:** saldo grande, **Fiar productos**, **Registrar abono**, historial, estado de cuenta y editar. | W-E1 |
| `/admin/clientes/importar` | CSV → vista previa con errores → confirmar. | W-E1 |
| `/admin/productos` | Productos y categorías, precio mayor y detal, cambio masivo. | W-E1 |
| `/admin/tasa` | Tasa de hoy e historial; fijar a mano o sincronizar. | W-E1 |
| `/admin/configuracion` | Negocio, cobros (métodos y cuentas), crédito por defecto y administradores. | W-E1 |
| `/admin/auditoria` | Registro. | W-E1 |

`/cambiar-contrasena` vive en `web/src/app/(admin)/cambiar-contrasena/` (carpeta de W-E1). `proxy.ts` (DSN) redirige ahí cuando `/auth/me` trae `mustChangePassword = true`.

**Prototipo de referencia:** [`docs/prototipos/cuaderno-e1.html`](../prototipos/cuaderno-e1.html). Es un prototipo funcional que se abre en el navegador, con datos de ejemplo y las reglas de 03 §3.10b. Muestra el **flujo** y los **textos**, no la dirección visual, que se elige en G0.5. DSN y W-E1 lo usan como guía de interacción.

**Requisitos de uso:**
- **Teléfono primero:** el dueño registra un abono en menos de 15 segundos desde el celular. La ficha muestra el saldo arriba y los dos botones al alcance del pulgar.
- **Fiar rápido:** buscador de productos con − / + y el total en vivo de `fiado/quote` (con *debounce* de 300 ms). El `Idempotency-Key` se genera **una vez por intento** de guardar.
- **Confirmación** antes de anular o revertir, con el motivo obligatorio.

## E1 — Agentes (6), carpetas y orden
Cada agente es la ficha de 04 **recortada a E1**. Cuando la ficha y este documento no coinciden, manda este documento. Las ramas, bases y puertos se toman de 05 §1, con estos nombres:

| Agente | Ficha base | Rama | BD de pruebas · puertos | Escribe en (además de `docs/handoffs/<ID>.md`) |
|---|---|---|---|---|
| FND-E1 | FND | `block/FND-E1` | `panaderia_test_fnd` (+ `panaderia_migrations_fnd`) · 8001 | Lo mismo que FND en 04 (todo `api/**` al inicio, `contracts/`, `scripts/dev-setup.sh`, `spec/requirements.txt`, `.github/workflows/{api,contract,secrets}.yml`, `.claude/skills/*-panaderia/`, `.claude/agents/auditor-contable.md`, `CLAUDE.md` §Comandos). |
| DSN | DSN | `block/DSN` | — · 3000 / 4010 | Lo mismo que DSN en 04 (`DESIGN.md`, `docs/design/**`, todo `web/**` al inicio, `.github/workflows/web.yml`). |
| B-E1a | B1 | `block/B-E1a` | `panaderia_test_b1` · 8011 | `api/src/domain/{catalog,customers,users,settings,audit}/` (excepto `db_models.py` e `interface.py`), `api/src/api/v1/{catalog,customers,users,settings,audit}.py`, `api/tests/b1/**`, `api/alembic/versions/*_b1_*.py`. |
| B-E1b | B3 | `block/B-E1b` | `panaderia_test_b3` · 8013 | `api/src/services/{ledger,money}.py`, `api/src/domain/{payments,payment_methods,wallet,receivables,cash_accounts,finance,exchange_rates,dashboard}/` (ídem), `api/src/api/v1/{payments,payment_methods,admin_money,cash_accounts,rates,dashboard}.py`, `api/src/jobs/bcv_sync.py`, `api/tests/b3/**`, `api/alembic/versions/*_b3_*.py`. |
| W-E1 | W1 | `block/W-E1` | — · 3001 / 4011 | `web/src/app/(admin)/**`, `web/src/components/admin/**`, `web/src/components/layout/**`, `web/e2e/admin*`. |
| Q-E1 | Q1 | `block/Q-E1` | `panaderia_test_q1`, `panaderia_e2e` · 8020 / 3020 | `e2e/**`, `.github/workflows/e2e.yml`, `docs/handoffs/Q-E1-runbook-staging.md` y correcciones pequeñas y explicadas en `api/**` y `web/**`. |

**Por qué no se cruzan:**
- Se reutilizan las carpetas de B1, B3 y W1 (04). Por eso E2 continúa sin mover archivos.
- B-E1a y B-E1b tienen dominios, routers, pruebas y migraciones disjuntos.
- `auth.py` (incluido `change-password`) es de FND-E1.
- `/login` y `proxy.ts` son de DSN; `/cambiar-contrasena` es de W-E1.
- FND-E1 y DSN corren en paralelo sobre `api/` y `web/`, que son disjuntos. B-E1a, B-E1b y W-E1 arrancan **después** de integrar G1-E1. Q-E1 trabaja sobre lo integrado en G2-E1.

**Costuras entre B-E1a y B-E1b** (solo por interfaces congeladas de FND-E1, 08 §Interfaces):

| Necesidad | Quién llama → quién implementa | Interfaz | Stub de FND-E1 |
|---|---|---|---|
| Saldo anterior al crear o importar clientes | B-E1a → B-E1b | `MoneyService.open_balance` | lo registra en `money_double` |
| `balance`, `openDebt` y `overdueDebt` en la lista y la ficha, con filtro y orden por deuda | B-E1a → B-E1b | `FinanceQueries.balances_for` · `FinanceQueries.debt_subquery` | ceros |
| Precio de un producto y tipo del cliente para el fiado | B-E1b lee `products` y `customers` | modelos congelados, **solo lectura** | — |
| Días de crédito y nombre del negocio | ambos | `SettingsService.get` (real de FND-E1) | — |
| Auditoría | ambos | `AuditService.log` (real de FND-E1) | — |

**Recortes por agente:**
- **FND-E1:**
  - esquema **completo** de 02;
  - contrato y routers **solo del inventario E1** (sin 501). `test_contract_inventory` usa las 51 operaciones de E1;
  - auth: login, refresh, logout, me y **change-password** (más sus pruebas, incluida E15);
  - interfaces de E1: `CustomersService`, `SettingsService`, `AuditService`, `RateService`, `FinanceQueries` y `MoneyService.open_balance`. Las de pedidos, eventos, push y archivos llegan con E2–E4;
  - solo el job `bcv_sync` registrado;
  - el seed de E1 (§Datos).
- **DSN:**
  - tokens, `globals.css` y UI kit (sin `FileUpload` ni `ConnectionBanner`);
  - auth web (`/login`, refresh, logout, `proxy.ts` para `/admin` y `/cambiar-contrasena`);
  - `(admin)/layout.tsx` con el Sidebar inicial y `/design`;
  - `docs/design/admin.md` con las pantallas de E1 y sus **textos exactos**;
  - pantallas de muestra: **ficha del cliente a 390 px** y **lista de clientes a 1440 px**.
  - Quedan para su etapa: la cocina (layout, Wake Lock, sonidos, manifest), `useEventStream`, las páginas públicas y las especificaciones y el tema de Android.
- **B-E1a:**
  - catálogo sin fotos y sin `GET /catalog`;
  - cambio masivo con `target`, e historial con `priceType`;
  - clientes: CRUD, `credit` sin push, saldo anterior e importación;
  - usuarios ADMIN con `reset-password`;
  - configuración (`business` y `credit`) y `settings/public`;
  - auditoría.
- **B-E1b:**
  - el ledger y `settle` completos según 03 (sin pedidos que liquidar todavía);
  - fiado y su `quote`, abono, anular, revertir, estado de cuenta (JSON, CSV y WhatsApp) y `open_balance`;
  - `FinanceQueries`, tasa con `bcv_sync`, métodos, cuentas bancarias y cuentas del negocio, e inicio de E1;
  - el auditor contable sobre su diff.
- **W-E1:**
  - las pantallas de la tabla;
  - **Vitest:** formulario de fiado (llama a `quote`, una sola llave por intento, muestra la advertencia) y formulario de abono (referencia obligatoria salvo en efectivo);
  - **Playwright:** el flujo de G3-E1 más importación y cambio masivo, con capturas a 390 y 1440 px.
  - Quedan para su etapa: pagos, pedidos, cobranza, cierres, PWA y Web Push.
- **Q-E1:**
  - `e2e/run_scenarios.py` con CU-1…CU-12 por HTTP, y Playwright de W-E1 contra la API real en `e2e.yml`;
  - runbook de staging de E1: servicios `api` y `web`, Neon `staging` y variables de 01. Sin bucket, FCM ni VAPID;
  - `staging-smoke`, auditor contable y `/security-review`;
  - checklist para el dueño.

```
E1.0 (paralelo):   FND-E1 · DSN                      → G1-E1 (orquestador: integra, gen:api, publica)
E1.1 (paralelo):   B-E1a · B-E1b · W-E1 (contra mock) → G2-E1
E1.2:              Q-E1 (integración, E2E, staging)   → G3-E1 → acceso al dueño
```
Cada agente sigue el protocolo 05: worktree propio, sin push, y el orquestador integra.

## E1 — Aceptación (CU)
| ID | Escenario | B-E1a / B-E1b | Q-E1 (HTTP) | W-E1 (Playwright) |
|---|---|---|---|---|
| CU-1 | Crear cliente con saldo anterior (deuda y a favor); `dueAt` según `creditDays` | B-E1a (con `money_double`) · B-E1b (`open_balance`) | ✅ | ✅ |
| CU-2 | Fiar con líneas: precio detal o mayor según el tipo, precio editado, cargo libre, redondeo por línea; `quote` = `fiado` | B-E1b | ✅ | ✅ |
| CU-3 | Abono parcial USD con referencia; abono en Bs con la tasa de `paidOn` y tasa corregida; efectivo sin referencia | B-E1b | ✅ | ✅ |
| CU-4 | Sobrepago → a favor; nuevo fiado consume el saldo a favor | B-E1b | ✅ | ✅ |
| CU-5 | Anular un fiado pagado → se reaplica a otro fiado; el sobrante queda a favor | B-E1b | ✅ | ✅ |
| CU-6 | Revertir un abono con y sin saldo a favor → CxC `PAYMENT_REVERSAL` vencida | B-E1b | ✅ | ✅ |
| CU-7 | `DUPLICATE_REFERENCE` en la misma cuenta; idempotencia de fiado y abono (misma llave = mismo recurso; otro contenido = 409) | B-E1b | ✅ | — |
| CU-8 | Importar CSV: errores por fila, `apply` crea clientes y saldos, token repetido = mismo resultado, token vencido = 409 | B-E1a | ✅ | ✅ |
| CU-9 | Límite de crédito: advertencia sin bloquear; sin advertencia con límite 0 | B-E1b | ✅ | ✅ |
| CU-10 | Inicio del día de Caracas: un abono a las 22:30 VET cuenta ese día; un reverso al día siguiente no cambia el día anterior; top deudores | B-E1b | ✅ | — |
| CU-11 | Autorización: toda ruta de E1 solo para ADMIN; `mustChangePassword` obliga a `change-password` | FND-E1 · cada B | ✅ | ✅ |
| CU-12 | Concurrencia: dos abonos simultáneos del mismo cliente (`committed_db`) sin romper invariantes | B-E1b | ✅ | — |

Todas las pruebas de dinero terminan con `assert_money_invariants`.

## E1 — Compuertas
- **G1-E1:**
  - FND-E1: `pytest` verde; migración upgrade → downgrade → upgrade; `alembic check` sin cambios; inventario E1 (51); fábricas E1; `bootstrap` y `seed` idempotentes.
  - DSN: tokens, UI kit, `/login`, layout del admin, `admin.md`; web lint, test y build verdes; `impeccable detect` sin críticos.
  - Luego el orquestador ejecuta `gen:api` y publica.
- **G2-E1:**
  - CU-1…CU-12 a nivel de services y de HTTP propio, más los escenarios de `spec` portados;
  - pantallas completas contra el mock;
  - `git diff --stat` dentro de las carpetas de cada agente;
  - `alembic heads` = 1;
  - CI verde en `api`, `contract`, `secrets` y `web`.
- **G3-E1:**
  - E2E en CI: crear cliente con saldo anterior → fiar → abonar → saldo a favor → nuevo fiado → anular → revertir → importar un CSV de prueba;
  - staging en línea (`/api/health`, tablas de 02 y `alembic_version` = head);
  - login del dueño con cambio de contraseña;
  - auditor contable y `/security-review` sin hallazgos altos.

**Requiere al dueño en E1:**
- elegir la dirección visual (G0.5, unos minutos);
- aprobar el despliegue en Railway;
- **entregar la lista de deudores** (CSV o Excel: nombre, teléfono, tipo, deuda), los precios de mayor y detal, y los métodos de cobro con sus cuentas;
- decidir C-37 (hacer privado el repositorio) antes de copiar código de OpenGravity.

## Decisión pendiente para E2 (no bloquea E1)
Con las reglas de 03 §2, un cliente **CASH** que tenga un fiado abierto recibe `OPEN_DEBT` al hacer un pedido. Si el fiado lleva más de `credit.blockOverdueDays` vencido, recibe `OVERDUE_DEBT`, aunque el pedido lo tome el admin.

En E1 no hay pedidos, pero en E2 la mayoría de los clientes del cuaderno serán CASH con deuda. Antes de lanzar E2 hay que elegir una opción (CUESTIONARIO C-41):
- **(a)** mantener la regla: se cobra antes de tomar un pedido;
- **(b) recomendada:** pasar a CREDIT, con límite, a los clientes de mostrador que fían;
- **(c)** que los pedidos del panel no apliquen `OPEN_DEBT`.

Cualquiera de las tres se implementa sin cambiar los datos de E1.

## Etapas siguientes (resumen)
| Etapa | Agentes | Agrega |
|---|---|---|
| **E2** | B2 (pedidos, agenda, cocina, SSE), W2 (cocina), W1+ (pedidos en el panel), FND+ (contrato de pedidos y eventos) | Endpoints y pantallas de `orders`, `order_items` y `order_events` (las tablas ya existen desde E1); pedidos “hoy” o programados creados por el admin; cocina en tablet. |
| **E3** | M-delivery, B2+ (delivery, push) | `device_tokens` en uso; app del motorizado. |
| **E4** | M-cliente, B3+ (pagos reportados, billetera de la app, crédito), B1+ (registro, archivos, imágenes), W1+ (bandeja de pagos, Web Push) | Todo lo demás de 01–08. |
