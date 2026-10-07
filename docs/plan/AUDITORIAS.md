# Registro de auditorías del plan

## Auditoría 1 (2026-10-06)

Seis lentes independientes: dinero, paralelismo, contrato, reutilización de OpenGravity, pruebas e infraestructura, y producto/UX.
- La lente de producto/UX no llegó a terminar por el límite de uso de la sesión; se cubre en la auditoría 2.
- La verificación adversarial también se cortó por ese límite. Cada hallazgo lo revisó el orquestador contra el código de OpenGravity y contra el modelo ejecutable antes de aplicarlo.

**69 hallazgos.** Todos se aplicaron. Ninguno se descartó: los de severidad baja también se corrigieron.

| ID | Sev. | Problema (resumen) | Corregido en |
|---|---|---|---|
| M1 | critica | El plan dice que el pago en Bs usa `ExchangeRateService.get_rate_at_date(paidOn)` y que eso es 'lógica de OpenGravity'. No lo es. En /home/user/opengraviti/apps… | 03 §0–§3.13 · 02 · spec v2.1 |
| M2 | alta | (a) Con un pedido AWAITING_PAYMENT, el modelo devuelve a la billetera el monto de la REDUCCIÓN y no lo cobrado de más. Lo verifiqué ejecutando el modelo: el ped… | 03 §0–§3.13 · 02 · spec v2.1 |
| M3 | alta | Las fórmulas en SQL del doc no coinciden con el modelo y fallarían sobre una implementación correcta (lo verifiqué ejecutando el modelo). I-2: el doc suma todos… | 03 §0–§3.13 · 02 · spec v2.1 |
| M4 | alta | La regla OVERDUE_DEBT solo se aplica a clientes CREDIT. Un cliente CASH con deuda abierta puede seguir pidiendo para siempre sin pagarla. Esa deuda puede venir … | 03 §0–§3.13 · 02 · spec v2.1 |
| M5 | alta | Para un programado, `expiresAt = min(ahora+24h, dueAt − minLeadMinutes)`. Como §2 permite `dueAt = ahora + minLeadMinutes`, ese pedido nace con `expiresAt = aho… | 03 §0–§3.13 · 02 · spec v2.1 |
| M6 | media | La anulación manual de una CxC ('devuelve lo pagado') no existe en el modelo ni en 03, así que no tiene reglas ni pruebas. Si se aplica a una CxC de source ORDE… | 03 §0–§3.13 · 02 · spec v2.1 |
| M7 | media | No existe una forma de devolverle al cliente su saldo a favor en dinero (por ejemplo, después de cancelar un pedido o de un pago aprobado sobre un pedido ya can… | 03 §0–§3.13 · 02 · spec v2.1 |
| M8 | media | El índice de referencia única excluye a los pagos REVERSED. Un pago revertido (transferencia devuelta o falsa) puede volver a reportarse con la misma referencia… | 03 §0–§3.13 · 02 · spec v2.1 |
| M9 | media | No hay regla para lo que pasa con pedidos AWAITING_PAYMENT y pagos en revisión cuando el admin bloquea al cliente o le cambia el modo. Según el modelo, a un cli… | 03 §0–§3.13 · 02 · spec v2.1 |
| M10 | media | Hay una carrera entre el job y el reporte de pago. `report_payment` valida que el pedido esté AWAITING_PAYMENT sin bloquear nada (§3.3 no menciona lock), mientr… | 03 §0–§3.13 · 02 · spec v2.1 |
| M11 | media | El modelo, que según 07 manda sobre la implementación, lanza códigos que no están en el catálogo: EMPTY_ORDER, ONLY_REDUCTION, ORDER_NOT_PAYABLE, PAYMENT_NOT_RE… | 03 §0–§3.13 · 02 · spec v2.1 |
| M12 | baja | `paymentStatus` de un pedido CREDIT se queda en ON_CREDIT para siempre, aunque su CxC pase a PAID por `settle` o por una reducción. El cliente y el admin verían… | 03 §0–§3.13 · 02 · spec v2.1 |
| SW-01 | critica | CLAUDE.md se inyecta a cada agente como instrucción de máxima prioridad y sigue en la v1 del plan, así que contradice al plan v2 en cuatro puntos. (a) Regla 2: … | 04 · 05 · 08 · fichas |
| SW-02 | alta | 08 no dice dónde viven los stubs ni cómo se cambia el stub por la implementación real. Si FND pone el stub o la fábrica en `domain/*/interface.py` (congelado) o… | 04 · 05 · 08 · fichas |
| SW-03 | alta | Solo se define el comportamiento del stub de `checkout`, `price_lines` y `EventBus`. Faltan cuatro piezas. (1) `PushSender`: no hay stub. B1, al cambiar el créd… | 04 · 05 · 08 · fichas |
| SW-04 | alta | Hay dos llamadas cruzadas que no cubre ninguna interfaz. (a) B2 debe responder `checkout.paymentMethods[]` con métodos y cuentas activas (`POST /orders`, `/orde… | 04 · 05 · 08 · fichas |
| SW-05 | alta | B3 debe portar los 18 escenarios 'a pruebas de API (HTTP y services)', con Hypothesis de 'pedir… cancelar' y E10 'aprobar mientras el cliente crea un pedido'. P… | 04 · 05 · 08 · fichas |
| SW-06 | alta | En la Fase 1, B1, B2 y B3 corren pytest a la vez desde tres worktrees contra el mismo Postgres 16 local, y FND solo prevé una base `panaderia_test`. El setup de… | 04 · 05 · 08 · fichas |
| SW-07 | alta | W1 tiene que hacer Playwright con 'login de admin' contra Prism, y W2 tiene que pasar por `/cocina`. El `src/proxy.ts` de OpenGravity, que DSN copia, hace `jwtV… | 04 · 05 · 08 · fichas |
| SW-08 | alta | Hay archivos web que W1 y W2 necesitan pero que no son de nadie en la Fase 1, o que están congelados como compartidos. (1) `web/package.json` y `package-lock.js… | 04 · 05 · 08 · fichas |
| SW-09 | alta | DSN corre en paralelo con FND, así que el contrato no existe todavía. La ficha dice que `npm run gen:api` 'se ejecuta al integrar', pero no dice quién lo ejecut… | 04 · 05 · 08 · fichas |
| SW-10 | alta | (a) 'Seed de staging con un admin' no se puede ejecutar: el contenedor no tiene salida a Neon:5432 y `scripts/seed.py` usa psycopg. Sin el admin no se cumple G3… | 04 · 05 · 08 · fichas |
| SW-11 | media | 08 no asigna cada endpoint a un archivo de router, y las listas de 04 no alcanzan. B3 no tiene archivo para `/payment-methods`, `/admin/payment-methods`, `/admi… | 04 · 05 · 08 · fichas |
| SW-12 | media | Los jobs se registran en el lifespan de `main.py`, que está congelado. B2 (`unpaid_auto_cancel`) y B3 (`bcv_sync`, `daily_closing`) son dueños de sus archivos d… | 04 · 05 · 08 · fichas |
| SW-13 | media | Cada agente debe marcar su fila de `STATUS.md` como 'LISTO PARA INTEGRAR'. Las filas de B1 a M son líneas consecutivas, y git trata como conflicto los cambios e… | 04 · 05 · 08 · fichas |
| SW-14 | media | W1 y W2 corren a la vez en el mismo contenedor y las dos fichas fijan Prism en `:4010` (`scripts/mock.sh`) y `next dev`/Playwright en `:3000`. El segundo agente… | 04 · 05 · 08 · fichas |
| SW-15 | media | M no puede compilar ni correr ninguna prueba en toda la Fase 1. Los módulos `com.android.*` ni siquiera se configuran sin SDK, así que 'pruebas JVM' en `:core:n… | 04 · 05 · 08 · fichas |
| SW-16 | baja | G1 exige 'todos los endpoints de 03', pero el inventario está en 08. G2 dice 'Fase 1 (7 agentes)', pero la Fase 1 tiene 6 (B1, B2, B3, W1, W2, M). | 04 · 05 · 08 · fichas |
| C1 | alta | El access JWT dura 30 min, pero la web copia el patrón de OpenGravity: cookie `authToken` con solo el access token. `OG/apps/web/src/app/api/auth/me/route.ts` d… | 08 · 01 · fichas W1/W2/M |
| C2 | alta | El plan no fija cómo se escriben los nombres de los campos en el JSON de la API. 08 usa camelCase (`accessToken`, `nextCursor`, `walletWillUse`, `amountDueVes`,… | 08 · 01 · fichas W1/W2/M |
| C3 | alta | 06 dice que el `public_router` de OpenGravity alimenta los 'datos para pagar'. Ese endpoint (`OG/apps/bot/src/api/payment_methods.py`, `list_active_payment_meth… | 08 · 01 · fichas W1/W2/M |
| C4 | alta | La app cliente no puede mostrar las fotos de los productos. `products` solo guarda `imageFileId`. 08 no dice que `GET /catalog` devuelva una URL. Y `GET /files/… | 08 · 01 · fichas W1/W2/M |
| C5 | alta | El faltante (`amountDue`, `amountDueVes`, tasa, métodos de pago) solo llega en el `checkout` de la respuesta de `POST /orders`. Pero M §5 tiene "Pagar faltante"… | 08 · 01 · fichas W1/W2/M |
| C6 | media | M §2 pide "precio USD y Bs (tasa de hoy)" en el catálogo y el resumen del carrito en Bs, pero la misma ficha prohíbe que la app calcule dinero. `GET /catalog` n… | 08 · 01 · fichas W1/W2/M |
| C7 | media | El token de stream es de un solo uso y dura 60 s. Al cortarse la conexión, `EventSource` se reconecta solo con la **misma URL**, el token ya consumido devuelve … | 08 · 01 · fichas W1/W2/M |
| C8 | media | Falta definir el contenido de los eventos SSE: 08 solo lista los tipos. OpenAPI no describe bien `text/event-stream` y Prism no lo emite, así que el simulador d… | 08 · 01 · fichas W1/W2/M |
| C9 | media | 03 §4: "Si no hay motorizado configurado, queda READY sin asignar y el admin ve una alerta". Pero ningún endpoint asigna después: `GET /delivery/orders` devuelv… | 08 · 01 · fichas W1/W2/M |
| C10 | media | `GET /settings/public` promete "versiones mínimas de las apps" y M usa ese valor para el aviso "Actualiza la app". Pero no existe ninguna clave para eso en la t… | 08 · 01 · fichas W1/W2/M |
| C11 | media | La app del motorizado tiene una cola local que reintenta las acciones fallidas. Si "Entregado" se aplicó en el servidor pero la respuesta se perdió por mala señ… | 08 · 01 · fichas W1/W2/M |
| C12 | media | W1 pide "crear pedido para un cliente" (pedidos por WhatsApp) y "abono manual". Pero `POST /orders/quote` es solo rol C, así que el admin no puede ver antes cuá… | 08 · 01 · fichas W1/W2/M |
| C13 | baja | Hay nombres distintos entre 02 y 08 para la misma cosa: `payments.localCurrency` (02) vs `currency` (08, `POST /payments`); `walletWillUse` (quote) vs `walletUs… | 08 · 01 · fichas W1/W2/M |
| C14 | baja | M §8 dice que, al tocar un push de pago aprobado o rechazado, se abre el pago. Pero el cliente no tiene `GET /payments/{id}`, solo la lista. Además, B2 §10 defi… | 08 · 01 · fichas W1/W2/M |
| C15 | baja | Las listas paginadas por cursor devuelven `{items, nextCursor}` sin total. Las vistas de pagos de OG que W1 copia usan `skip/limit/total` (`OG/apps/bot/src/api/… | 08 · 01 · fichas W1/W2/M |
| OG-01 | critica | Copiar el 'flujo de apply_payment' y el ExchangeRateService 'sin cambios de lógica' trae dos defectos que rompen el dinero. (1) En OG/apps/bot/src/domain/paymen… | 06 · 03 §0 · 01 · CLAUDE.md |
| OG-02 | alta | Lo que el plan afirma de la tasa no coincide con OG. (a) No existen 'BCV del día' y 'DolarAPI' como fuentes separadas: hay una sola fuente externa, BCV_SOURCE_U… | 06 · 03 §0 · 01 · CLAUDE.md |
| OG-03 | alta | El conftest de OG (OG/apps/bot/tests/conftest.py) tiene fijo `TEST_DATABASE_URL = "sqlite+aiosqlite:///test_db.sqlite3"`. Su fixture autouse `_create_tables` ha… | 06 · 03 §0 · 01 · CLAUDE.md |
| OG-04 | alta | OG `_add_wallet_entry` (services/ledger.py L452-484) guarda `amount` siempre positivo y deduce el signo del tipo (EXPENSE/TRANSFER_OUT restan; ADJUSTMENT siempr… | 06 · 03 §0 · 01 · CLAUDE.md |
| OG-05 | alta | OG/apps/bot/src/domain/closures/service.py._build_metrics calcula el día con `p.created_at.date() == target_date` sobre un UTC sin zona: los pagos aprobados ent… | 06 · 03 §0 · 01 · CLAUDE.md |
| OG-06 | alta | El patrón web de OG que se copia no tiene refresh. actions.ts guarda solo `access_token` en la cookie; proxy.ts hace jwtVerify y redirige a /login si expiró. Co… | 06 · 03 §0 · 01 · CLAUDE.md |
| OG-07 | alta | jmcakes es PÚBLICO (gh api: visibility=public) y opengraviti es PRIVADO, con un sistema financiero en producción. Copiar 'tal cual' publica su lógica de segurid… | 06 · 03 §0 · 01 · CLAUDE.md |
| OG-08 | alta | El plan presenta pagos como reutilización, pero lo central de la panadería no existe en OG. PaymentDB (OG/.../payments/db_models.py) no tiene `reference`, `paid… | 06 · 03 §0 · 01 · CLAUDE.md |
| OG-09 | media | Rutas y supuestos falsos en el mapa: (a) `src/db/types.py` contiene solo EncryptedString/EncryptedJSON e importa `src.core.encryption`, que el plan excluye (PII… | 06 · 03 §0 · 01 · CLAUDE.md |
| OG-10 | media | OG/apps/bot/src/api/limiter.py usa `Limiter(key_func=get_remote_address)` y el arranque de OG es `uvicorn src.main:app --host 0.0.0.0 --port ${PORT}`, sin --for… | 06 · 03 §0 · 01 · CLAUDE.md |
| OG-11 | media | OG/apps/bot/src/core/exceptions.py convierte TODO SQLAlchemyError (incluido IntegrityError) en 503 con 'Database connection error or integrity constraint violat… | 06 · 03 §0 · 01 · CLAUDE.md |
| OG-12 | baja | (a) settings de OG no es 'clave–valor tipado': ConfigService guarda 4 secciones JSON fijas (finances, wallets, bot_control, operations) validadas con el AppConf… | 06 · 03 §0 · 01 · CLAUDE.md |
| INF-01 | alta | §4 asume que `api/railway.toml` (preDeployCommand `alembic upgrade head`, healthcheck `/api/health`, startCommand) se aplica al servicio con rootDirectory `api`… | 01 · 07 · FND · Q1 · M · Q2 |
| INF-02 | alta | Q1 no puede desplegar staging sin intervención humana y el plan no lo dice: (a) Las instrucciones del MCP de Railway exigen confirmación del usuario para `accep… | 01 · 07 · FND · Q1 · M · Q2 |
| INF-03 | alta | §7 pide un `conftest.py` 'Postgres local por TEST_DATABASE_URL y sesión con savepoint, como OpenGravity', pero el de OpenGravity (`apps/bot/tests/conftest.py`) … | 01 · 07 · FND · Q1 · M · Q2 |
| INF-04 | alta | Playwright no puede descargar navegadores en el contenedor. Verificado: `CONNECT cdn.playwright.dev:443` y `playwright.azureedge.net` responden 403 en el proxy,… | 01 · 07 · FND · Q1 · M · Q2 |
| INF-05 | alta | El comando de `android.yml` (`./gradlew :app-cliente:assembleMockDebug :app-delivery:assembleMockDebug testDebugUnitTest`) da un falso verde. Ambas apps tienen … | 01 · 07 · FND · Q1 · M · Q2 |
| INF-06 | alta | Falta un catálogo de variables de entorno, y la lista de Q1 §4 deja el login web de staging roto: (1) `web/src/proxy.ts` (copiado de OpenGravity) verifica la co… | 01 · 07 · FND · Q1 · M · Q2 |
| INF-07 | alta | Q1 §4 pide un seed de staging con un admin, pero desde el contenedor no hay salida a Neon:5432, así que `scripts/seed.py` no puede ejecutarse contra Neon. `rail… | 01 · 07 · FND · Q1 · M · Q2 |
| INF-08 | alta | El diseño SSE falla detrás del proxy de Railway y no se puede probar como está escrito: (1) El token es 'de un solo uso, 60 s' y va en la URL. Railway corta con… | 01 · 07 · FND · Q1 · M · Q2 |
| INF-09 | media | §4 pone `DATABASE_URL` 'con pooler' y usa la misma URL para `alembic upgrade head`. El pooler de Neon es PgBouncer en modo transacción, y Neon recomienda conexi… | 01 · 07 · FND · Q1 · M · Q2 |
| INF-10 | media | Faltan detalles de arranque en Railway que causarán bugs probables: (1) `limiter.py` de OpenGravity usa `get_remote_address` (`request.client.host`). Detrás del… | 01 · 07 · FND · Q1 · M · Q2 |
| INF-11 | media | Archivos (§4) y Q1 §4 ('adaptadores nulos para bucket hasta tener credenciales'): - El comprobante es obligatorio en el flujo de pago de contado. Con un adaptad… | 01 · 07 · FND · Q1 · M · Q2 |
| INF-12 | media | El entorno de Python no es reproducible en un worktree nuevo: - `python -m pytest spec -q` (CLAUDE.md §Comandos, G0, G1) falla en el contenedor con 'No module n… | 01 · 07 · FND · Q1 · M · Q2 |
| INF-13 | baja | §1 propone como opcional 'armar un SDK mínimo desde maven.google.com (aapt2 y artefactos de AGP)'. AGP necesita `platforms/android-35/android.jar` y `build-tool… | 01 · 07 · FND · Q1 · M · Q2 |
| INF-14 | baja | Hay inconsistencias entre compuertas y fichas: - 07 §3 dice que `e2e/run_scenarios.py` ejecuta 'E1–E9', mientras que G3 y Q1 §2 exigen E1–E12; - G1 pide 'todos … | 01 · 07 · FND · Q1 · M · Q2 |

Verificación posterior: `spec` 31/31 en verde; 4.000 secuencias aleatorias × 80 operaciones sin violar invariantes.

## Auditoría 2 (2026-10-07)

Se repitieron las seis lentes. Dinero, paralelismo y contrato completaron; reutilización, pruebas/infra y producto/UX se cortaron por el límite de uso y se re-ejecutan en la ronda 2b. El orquestador revisó cada hallazgo contra el modelo ejecutable y los documentos antes de aplicarlo.

**32 hallazgos, todos aplicados.**

| ID | Sev. | Problema (resumen) |
|---|---|---|
| R2-M1 | alta | El orden del ledger no es determinista. I-1 verifica balanceAfter 'ordenando por createdAt, id', pero los id son cuid2, que son aleatorios. Además, OpenGravity, que se co… |
| R2-M2 | alta | Al aprobar, el admin solo puede corregir `amountUsd` y/o `bcvRateUsed`; no puede corregir `amountLocal`. El caso real más común es un cliente que escribió mal el monto en… |
| R2-M3 | alta | Hay un escenario sin regla: un pago insuficiente que se aprueba después del vencimiento. El job no cancela mientras hay un pago en revisión, así que expiresAt queda en el… |
| R2-M4 | media | Hay un conflicto de propiedad de `orders.expiresAt`. 02 asigna expiresAt a B2, pero la ficha de B3 dice 'reject (extiende expiresAt)', y R2-M3 suma una extensión al aprob… |
| R2-M5 | media | Un cliente CASH con deuda abierta (por reverso o cargo manual) puede seguir confirmando pedidos que ya estaban en AWAITING_PAYMENT, porque settle paga primero los pedidos… |
| R2-M6 | media | 02 dice que FND escribe las invariantes 'tal cual' en assert_money_invariants, pero solo I-1…I-3 están en SQL. I-4, I-5, I-6 e I-9 son prosa, y cada agente las traducirá … |
| R2-M7 | media | 'Ingresos del día' cuenta solo los pagos con status APPROVED. Cuando un pago se revierte, pasa a REVERSED y desaparece de forma retroactiva del ingreso de su día de aprob… |
| R2-M8 | media | La unicidad de la referencia es por `(paymentMethodId, reference)`, pero lo que identifica una transferencia es la cuenta destino más la referencia. Con un método 'Pago m… |
| R2-M9 | media | 08 define reduce como `{items[{orderItemId, qty}]}`, pero 03 y el modelo solo validan `0 < nuevoTotal ≤ total`. Así se acepta subir la cantidad de una línea y bajar otra … |
| R2-M10 | baja | El cierre corre a las 23:50 y hace un upsert del día en curso. Los pagos aprobados y los pedidos confirmados entre las 23:50 y las 23:59 VET quedan fuera del PDF y de dai… |
| R2-SW-01 | alta | §8 dice que `tests/test_authz_matrix.py` lo crea FND y que «B1, B2 y B3 lo amplían», y la ficha B1 también pide «ampliar el arnés de autorización». Pero ese archivo es de… |
| R2-SW-02 | alta | La propiedad de `orders.expiresAt` es contradictoria y la interfaz no la transporta. Por un lado, 02 («Quién escribe qué en orders») asigna `expiresAt` a B2. Por otro, la… |
| R2-SW-03 | alta | §Interfaces: las pruebas de la Fase 1 dependen de la semántica de los stubs por defecto, que se reemplazan en G2. (1) El stub de `checkout` dice «CREDIT confirma (PAID)»,… |
| R2-SW-04 | alta | §4 G2 no se puede cumplir por el orden de las fases. G2 exige «CI verde (incluido `android.yml` si M ya entregó)», y `web.yml` corre el job `e2e-web` con los Playwright d… |
| R2-SW-05 | alta | Q1 «trabaja en el directorio de la rama de integración», y Q2 arranca en G2 «en paralelo con Q1». STATUS.md también le asigna a Q2 la rama «integración». Así quedan dos a… |
| R2-SW-06 | media | Hay escrituras legítimas fuera de las carpetas propias de 04, así que la revisión `git diff --stat` contra las carpetas (05 §2.1, G2) marca falsos positivos o lleva a mer… |
| R2-SW-07 | media | La compuerta de inventario del contrato no se puede ejecutar como está escrita. «Compuerta G1» pide que el número de endpoints del OpenAPI sea «igual al número de filas d… |
| R2-SW-08 | media | §Interfaces deja sin Protocol dos servicios de FND que viven en carpetas ajenas. (1) La configuración (`domain/settings/`, de B1 según 04) la leen B2 (`minLeadMinutes`, h… |
| R2-SW-09 | media | §Riesgos dice que el orquestador «publica `block/M` en cuanto M entrega, para que `android.yml` corra durante la Fase 1», y Q2 itera igual sobre los logs. Pero 01 §Entorn… |
| C2-01 | alta | Al catálogo de errores le faltan códigos que el propio plan exige. Como FND solo escribe el catálogo de 03 §7 y `core/errors.py` queda congelado, B1 y B3 no tienen con qu… |
| C2-02 | alta | El contenido de los eventos no alcanza para la cocina ni para el admin: - **Cuándo se emite `order.updated`:** no está definido. 03 y B2 solo lo emiten al reducir y en RE… |
| C2-03 | media | No está fijado el formato del stream. DSN escribe `useEventStream` en la Fase 0, antes de que B2 implemente el generador, y el formato queda abierto en tres puntos: - **L… |
| C2-04 | alta | El admin comparte el esquema `OrderDetail` con el cliente, y a ese esquema le faltan `customerId`, `customerName`, `channel`, `assignedDriverId`, `contactPhone` y `prepar… |
| C2-05 | alta | El refresh rota de forma estricta y no es idempotente. Hay tres casos en que el usuario pierde la sesión: - **Web:** `proxy.ts` (que redirige a refresh), `/api/auth/token… |
| C2-06 | media | Pedidos a crédito: - **`amountDue` sin regla de estado:** 08 y el stub de FND lo definen como `total − paidFromWallet − roundingAdjustment`, sin condición. El modelo (`am… |
| C2-07 | media | Faltan datos para mostrar USD y Bs: - **`GET /me/wallet` sin Bs:** devuelve saldo, deuda y vencidas solo en USD, sin Bs ni `rate`. PRODUCT exige “saldo a favor, deuda y m… |
| C2-08 | media | El push es contrato entre B2/B3 (emisores) y M (receptor), pero no está en el OpenAPI ni en 08. B2 dice “Textos de 03 y 08”, y 08 no tiene textos ni claves de `data`. M d… |
| C2-09 | media | Hay tres reintentos que no son idempotentes: 1. **Movimientos manuales del admin:** `POST /admin/customers/{id}/charges`, `/adjustments` y `/payouts` mueven dinero sin `I… |
| C2-10 | media | Con `STORAGE_BACKEND=local` (dev, Prism/E2E de Q1, y staging mientras no exista el bucket), `signed_get_url` devuelve `/api/v1/files/{id}/local`, que pide la misma autori… |
| C2-11 | media | G1 exige que el número de endpoints del OpenAPI sea “igual al número de filas de 08”. Las filas agrupan varias operaciones (por ejemplo, `GET·POST /admin/categories · PAT… |
| C2-12 | media | B3 debe extender `expiresAt` al rechazar un pago (03 §3.6; B3 §3: “reject (extiende expiresAt)”). Pero 02 asigna `expiresAt` en exclusiva a B2, y el Protocol congelado `O… |
| C2-13 | baja | 03 §3.2 dice que `GET /orders/{id}` incluye `walletUsed` y `paymentMethods[]`. 08 dice lo contrario: `OrderDetail` lleva `paidFromWallet` y no trae métodos, que M lee de … |

Verificación: `spec` 34/34 en verde (escenarios nuevos: aprobación insuficiente después del vencimiento, deuda de contado antes que el pedido, referencia por cuenta destino); prueba de estrés de 320.000 operaciones sin violaciones; inventario del contrato con 104 operaciones contadas por script.
