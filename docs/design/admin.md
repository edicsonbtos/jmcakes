# Panel del administrador — especificación de pantallas (E1)

> Alcance: **solo la Etapa 1** (docs/plan/09 §E1). Las pantallas de pedidos, pagos reportados, cocina y cierres llegan con su etapa y no tienen menú, ruta ni hueco aquí.
> Dirección visual: contrato en `.impeccable/surfaces/web-src-app-admin.md` (salida estándar de apps de delivery, Uber y Rappi como vara). Tokens: `docs/design/tokens.json`. Componentes: `web/src/components/ui` (se ven en `/design`).
> Los textos entre comillas son **exactos**. Los mensajes de error de la API se muestran **tal cual** (`detail`); los de esta hoja son solo las validaciones locales de la web.

## 0. Reglas que valen para todas las pantallas
- **Teléfono primero (390 px).** Un abono se registra en menos de 15 s: la ficha pone el saldo arriba y las dos acciones fijas abajo, al pulgar.
- **La web no calcula dinero.** Totales, Bs, saldos “antes → después” y advertencias vienen de la API (`fiado/quote`, `manual-payment/quote`, `balance`, `*Ves`). Los montos se escriben como “12,50” y se envían como `"12.50"`.
- **Bs:** debajo de cada monto en USD, con los Bs de la API. Si la API manda `null` (sin tasa): “Bs —” con el título “Sin tasa del día”.
- **Saldo:** positivo = “Debe” (rojo `debt`), negativo = “A favor” (verde `favor`), cero = “Al día” (tinta). Nunca solo color: siempre el rótulo.
- **Hora:** todo en `America/Caracas`. Fechas relativas en historiales: “Hoy”, “Ayer”, “12 oct”; hora “3:30 p. m.”.
- **Idempotencia:** fiado, abono, anular, revertir e importar crean su `Idempotency-Key` al abrir la hoja y la reutilizan en cada reintento; el botón queda deshabilitado (con indicador) hasta la respuesta.
- **Confirmación** antes de anular o revertir, con motivo obligatorio.
- **Avisos breves** (píldora negra abajo, 3 s) tras cada guardado. Errores de guardado: dentro de la hoja con `InlineAlert` rojo y el `detail` de la API.

### Estados comunes
| Estado | Cómo se ve | Texto |
|---|---|---|
| Cargando | `Skeleton`/`SkeletonRows` con la forma del contenido (nunca un spinner en medio) | lector de pantalla: “Cargando…” |
| Error al cargar | `InlineAlert` rojo arriba del contenido + botón secundario | `detail` de la API · botón “Reintentar” |
| Sin conexión | mismo patrón (código `NETWORK_ERROR`) | “Sin conexión con el servidor. Revisa tu señal e intenta de nuevo.” · “Reintentar” |
| Sesión vencida | la web refresca sola; si no puede, va a `/login?next=…` | “Tu sesión venció. Entra de nuevo.” |
| Vacío | `EmptyState` con ícono en círculo, título, una frase y la acción | ver cada pantalla |

## 1. Navegación
```
Escritorio (≥1024 px)                         Teléfono (<1024 px)
┌────────────┬──────────────────────────┐     ┌──────────────────────────────┐
│ (P) Nombre │                          │     │ (P) Nombre      [Tasa Bs 185,20]│  barra superior
│            │   contenido              │     ├──────────────────────────────┤
│ ⌂ Inicio   │   máx. 1152 px           │     │ contenido                    │
│ ☺ Clientes │                          │     │                              │
│ 🥐 Productos│                          │     ├──────────────────────────────┤
│ $ Tasa     │                          │     │ Inicio Clientes Productos Más│  solo en páginas principales
│ ⚙ Configur.│                          │     └──────────────────────────────┘
│ ☰ Auditoría│                          │
│────────────│                          │
│ Tasa BCV de hoy                       │
│ Bs 185,20  │                          │
│ ⇥ Cerrar sesión                       │
└────────────┴──────────────────────────┘
```
- Marca: inicial del negocio en círculo naranja + `business.name` de `GET /settings/public` (si no responde: “Panel”). Nunca un nombre fijo.
- Secciones: “Inicio”, “Clientes”, “Productos”, “Tasa”, “Configuración”, “Auditoría”. Activa: fondo gris, texto en negrita e ícono naranja (`aria-current="page"`).
- Teléfono: barra inferior con “Inicio”, “Clientes”, “Productos” y “Más”. “Más” abre la hoja **“Más”** con “Tasa”, “Configuración”, “Auditoría”, la tasa y “Cerrar sesión”.
- Subpáginas (ficha, importar): sin barra inferior; arriba “‹ Clientes”.
- Tasa en la barra: “Tasa Bs 185,20” (título: “Tasa BCV de hoy”, “Tasa manual de hoy” o “Tasa BCV del 20/10” si es la última conocida). Sin tasa: “Sin tasa”.
- “Cerrar sesión”: `POST /api/auth/logout` → `/login` con “Cerraste sesión. Vuelve a entrar cuando quieras.”

## 2. `/login` (DSN, hecho)
```
(P) Nombre del negocio

Entra al panel                       ← 32 px, 800
Con tu teléfono y tu contraseña.

Teléfono        [0414-123.45.67    ]  ← 56 px
Contraseña      [••••••••      👁 ]
[ aviso ]
[          Entrar          ]          ← negro, 56 px, ancho completo

¿Olvidaste la contraseña? Pídele a otro administrador que te la restablezca desde Configuración.
```
- Teléfono: acepta “0414-123.45.67”, “04141234567” o “+58 414…”; se envía en E.164.
- Validaciones locales: “Revisa el teléfono: escríbelo como 0414-123.45.67.” · “Escribe tu contraseña.”
- Errores de la API (credenciales, 429): `detail` tal cual. Rol distinto de ADMIN: “Este usuario no tiene acceso al panel.”
- Avisos por `?motivo=`: `salida` “Cerraste sesión. Vuelve a entrar cuando quieras.” · `rol` “Este usuario no tiene acceso al panel.” · `red` “Sin conexión con el servidor. Revisa tu señal e intenta de nuevo.”
- Botón “Entrar” con indicador mientras espera. Ojo: “Mostrar contraseña” / “Ocultar contraseña”.
- Tras entrar: a `next` (solo rutas internas) o `/admin`; si `mustChangePassword`, a `/cambiar-contrasena`.

## 3. `/cambiar-contrasena` (W-E1)
`proxy.ts` manda aquí mientras `mustChangePassword = true`; no se puede ir a otra pantalla del panel.
```
Cambia tu contraseña
Es tu primer ingreso: elige una contraseña nueva para seguir.
Contraseña actual   [        ]
Contraseña nueva    [        ]   Mínimo 8 caracteres.
Repite la nueva     [        ]
[        Guardar y entrar        ]
```
- Locales: “La nueva debe tener al menos 8 caracteres.” · “Las contraseñas no coinciden.”
- API: `INVALID_CURRENT_PASSWORD` y otros → `detail` tal cual.
- Al guardar: la API devuelve un par nuevo; W-E1 llama `writeSession(cookies, par, false)` (lib/session.ts) y va a `/admin` con el aviso “Contraseña cambiada”.

## 4. `/admin` — Inicio (W-E1)
Fuente: `GET /admin/dashboard/summary?date=` (día de Caracas). Sin tarjetas KPI en rejilla: una columna de cifras grandes y listas.
```
Hoy · martes 21 de octubre

Por cobrar                              Detal $28,50   Mayor $398,90
$427,40                                 Vencido $160,00
Bs 79.154,48

Abonos de hoy              $35,00     ← Σ totalUsd
 (◉) Pago móvil    Bs 3.704,00  $20,00
 (◉) Zelle                      $15,00
 Reversos de hoy: 1 · $10,00            (solo si hay)

Fiado de hoy               $27,60 · 2 fiados
Clientes con deuda vencida      4      → /admin/clientes?filtro=vencidos

Top deudores
 (BE) Bodega El Samán   Vencido $61,00      Debe $97,00 ›
 …hasta 10
```
- Vacíos: abonos “Todavía no hay abonos hoy.” · fiado “Todavía no se ha fiado hoy.” · top deudores “Nadie debe. Todo al día.”
- “Por cobrar” y “A favor de clientes” (`walletTotal`, si > 0): “A favor de clientes $X”.

## 5. `/admin/clientes` — Lista (W-E1; muestra DSN a 1440 px en `/design/clientes`)
Fuente: `GET /admin/customers?query=&hasDebt=&overdue=&sort=debt_desc&cursor=`. Búsqueda, filtros, orden y cursor en el servidor (debounce 300 ms en la búsqueda).
```
Clientes                                   [⇪ Importar] [+ Nuevo cliente]
Ordenados por mayor deuda.

Por cobrar                                 Detal $28,50   Mayor $398,90
$427,40
Bs 79.154,48
────────────────────────────────────────────────────────────────────
(🔍 Nombre, negocio, teléfono, cédula o apodo)     (Todos) (Con deuda) (Vencidos)

Cliente                  Tipo    Teléfono         Vencido      Saldo
(BE) Bodega El Samán     Mayor   0424-555.01.77   ● $61,00     Debe $97,00
                                                               Bs 17.964,40
(PL) Perros Los Panas    Mayor   …
     “frente a la plaza”                                       A favor / Al día
                            [ Cargar más ]
```
- Teléfono (<768 px): filas `ListRow` con iniciales, nombre, subtítulo (vencido en rojo “Vencido $61,00”, o negocio/apodo, o “Detal”/“Mayor”) y el saldo a la derecha. Toda la fila abre la ficha.
- Subtítulo: negocio si es distinto del nombre y el apodo (`notes`) entre comillas: “frente a la plaza”.
- Filtros: “Todos”, “Con deuda” (`hasDebt=true`), “Vencidos” (`overdue=true`). El filtro activo va en la URL (`?filtro=vencidos`).
- Buscador: lector de pantalla “Buscar cliente”; placeholder “Nombre, negocio, teléfono, cédula o apodo”; botón “Limpiar búsqueda”.
- Sin teléfono: “Sin teléfono” (gris).
- Vacío sin clientes: título “Todavía no hay clientes” · “Crea el primero o importa tu lista de deudores desde Excel.” · botones “Nuevo cliente” e “Importar”.
- Vacío con filtro: “Nadie con ese filtro” · “Prueba con otra búsqueda o quita el filtro para ver a todos.” · “Ver todos”.

### 5.1 Hoja “Nuevo cliente”
```
Nuevo cliente
Nombre                [Ej.: Sra. Ana Pérez        ]
Tipo                  ( Detal | Mayor )   ← obligatorio, marcado en Detal
                      Decide el precio del fiado.
Teléfono (opcional)   [0414-1234567]
Negocio (opcional)    [ ]
Cédula o RIF (opcional)[ ]
Apodo o nota (opcional)[Ej.: la del kiosko]
Saldo anterior $ (opcional) [0,00]
                      Lo que ya debía. Negativo = saldo a favor. Escribe 1234,56 sin puntos de miles.
[            Crear cliente            ]
```
- Locales: “Escribe el nombre.” · “Revisa el teléfono: escríbelo como 0414-123.45.67.” · “Monto inválido: escribe 1234,56 sin puntos de miles”.
- Éxito: va a la ficha nueva con el aviso “Cliente creado”.

## 6. `/admin/clientes/[id]` — Ficha (W-E1; muestra DSN a 390 px en `/design/ficha`)
Fuentes: `GET /admin/customers/{id}` (con `balance`, `balanceVes`, `overdueDebt`) y `GET /admin/customers/{id}/statement`.
```
‹ Clientes
Bodega El Samán                       ← 24/32 px, 800
[Mayor] 0424-555.01.77 · Crédito 7 días · Límite $60,00

Debe                                   ← rojo, 16 px, 700
$97,00                                 ← 48 px, 800, estrecha, rojo
Bs 17.964,40   [● Vencido $61,00]

(💬 Estado de cuenta)  (✎ Editar)

Movimientos
Hoy
 (↶) Anulado: 2 Pan de perro… · Se registró dos veces        −$3,60
     Anulación · 10:20 a. m. · María                      Saldo $97,00
 (🧺) 2̶ ̶P̶a̶n̶ ̶d̶e̶ ̶p̶e̶r̶r̶o̶…                                     +̶$̶3̶,̶6̶0̶
     Fiado · 10:12 a. m. · María                            [Anulado]
Ayer
 (↙) Zelle · ref. ZL-88213                                    −$15,00
     Abono · 12:05 p. m. · Admin                          Saldo $97,00
…
┌──────────────────────────────────────────────┐  fija abajo en el teléfono
│ [ Fiar productos ]   [■ Registrar abono ■]   │  (en escritorio, en línea bajo el saldo)
└──────────────────────────────────────────────┘
```
- Rótulos de saldo: “Debe”, “A favor”, “Al día”. Chip “Vencido $X” solo si `overdueDebt > 0`.
- Línea de datos: tipo (“Detal”/“Mayor”), teléfono o “Sin teléfono”, “Crédito N días”, “Límite $X” solo si `creditLimit > 0`.
- Filas del historial (de lo más nuevo a lo más viejo, agrupadas por día): ícono por tipo, `description`, “<Tipo> · <hora> · <quién>”, efecto (+ rojo / − verde) y “Saldo $X”. Tipos: “Saldo anterior”, “Fiado”, “Abono”, “Anulación”, “Reverso”, “Ajuste”.
- Fila anulada/revertida: tachada, gris, chip “Anulado” o “Revertido”; sigue en el historial.
- Tocar un fiado o saldo anterior → hoja con el detalle (líneas con cantidad × precio = total) y “Anular fiado” (o “Anular saldo anterior”). Tocar un abono → detalle (método, referencia, cuenta, fecha del pago, tasa) y “Revertir abono”.
- Vacío: “Todavía no hay movimientos” · “Cuando fíes productos o registres un abono, aparecerán aquí con su saldo.” · “Fiar productos”.
- Transición: al guardar, el monto grande entra con fundido y desenfoque de 420 ms al nuevo saldo (`BalanceFigure`).

### 6.1 Hoja “Fiar a <nombre>”
```
Fiar a Bodega El Samán
Precios de mayor. Puedes cambiar el precio de cada línea.     (detal: “Precios de detal.”)
(🔍 Buscar producto)
Canilla            $0,40 / unidad         (−) 30 (+)
  Precio $ [0,40]  ← al tocar el precio
Golfeado           $1,00 / unidad         (−) 12 (+)
…
Otro (cargo libre)  Descripción [        ]  Monto $ [0,00]
Nota (opcional)     [Ej.: lo retiró su hijo]
Vence (opcional)    [fecha]   Si no eliges, vence en 7 días.
───────────────────────────────────────────────
[⚠ Supera el límite de crédito ($60,00). Se registra igual.]
Total                                Saldo: $97,00 → $121,00
$24,00
[                 Fiar                 ]
```
- Total, “Saldo: antes → después” y advertencia vienen de `POST /fiado/quote` (debounce 300 ms). Mientras calcula: el total se atenúa y queda el último valor.
- Advertencia: la API manda `warning = CREDIT_LIMIT_EXCEEDED` con `meta{limit}` → “Supera el límite de crédito ($X). Se registra igual.” Nunca bloquea.
- Botón “Fiar” deshabilitado sin líneas. Locales: “El monto debe ser mayor que cero.” · “Escribe la descripción del cargo.”
- Éxito: cierra, aviso “Fiado de $24,00 registrado”, el saldo transiciona.

### 6.2 Hoja “Registrar abono”
```
Registrar abono
Bodega El Samán · Debe $97,00 (Bs 17.964,40)      (sin deuda: “No tiene deuda: el abono queda a favor.”)
Método              [Pago móvil (Bs)        ▾]
Monto en Bs  [Bs 3704,00]   Tasa del 21/10 [185,20]     ← la tasa solo en Bs; editable (bcvRateUsed)
Referencia          [118204]   Los dígitos que aparecen en el comprobante.   ← oculta en efectivo
Cuenta donde entró  [Banesco · 0134-…-4521  ▾]
Fecha del pago      [21/10/2026]
───────────────────────────────────────────────
│ Abona $20,00 (Bs 3.704,00 a tasa del 21/10)  │   ← `manual-payment/quote`
│ → queda debiendo $77,00                       │   (o “→ queda a favor $X”, o “→ queda al día”)
[            Registrar abono            ]
```
- Monto en USD para Zelle y efectivo (“Monto en USD”, prefijo “$”); en Bs para pago móvil y transferencia (“Monto en Bs”, prefijo “Bs”).
- Locales: “Escribe el monto.” · “Monto inválido: escribe 1234,56 sin puntos de miles” · “Escribe la referencia del pago.” (no en efectivo).
- API: `DUPLICATE_REFERENCE`, `RATE_UNAVAILABLE`, `IDEMPOTENCY_CONFLICT` → `detail` tal cual.
- Éxito: aviso “Abono de $20,00 registrado”; el saldo transiciona.

### 6.3 Confirmar “Anular fiado”
- Título “Anular fiado” (o “Anular saldo anterior”). Texto: “Lo que ya se abonó sobre este fiado paga primero otras deudas; solo el sobrante queda a favor. Queda en el historial.”
- Campo “Motivo (obligatorio)”, placeholder “Ej.: se registró dos veces”. Botones “Cancelar” y “Anular” (rojo).
- Éxito: aviso “Fiado anulado”.

### 6.4 Confirmar “Revertir abono”
- Texto: “La deuda vuelve a subir. Si no hay saldo a favor suficiente, la diferencia aparece como deuda vencida.”
- “¿Por qué lo reviertes?” (obligatorio):
  - “Me equivoqué al registrarlo” — “La referencia queda libre para cargarlo bien.” (`ENTRY_ERROR`)
  - “El banco lo devolvió” — “La referencia queda bloqueada.” (`BANK_RETURN`)
- “Motivo (obligatorio)”, placeholder “Ej.: el banco devolvió la transferencia”. Botones “Cancelar” y “Revertir” (rojo). Éxito: “Abono revertido”.

### 6.5 Hoja “Estado de cuenta”
- Descripción: “Texto listo para mandar por WhatsApp.” Vista previa del texto de `statement?format=whatsapp`.
- Botones: “Copiar texto” (aviso “Texto copiado”; si falla, “No se pudo copiar. Selecciona el texto y cópialo.”) y “Enviar” → `https://wa.me/<dígitos>?text=…`. Sin teléfono: “Compartir” (menú del sistema) en lugar de “Enviar”.
- Enlace secundario “Ver para imprimir”: el estado de cuenta en una página limpia con `window.print()`.

### 6.6 Hoja “Editar cliente”
- Campos de “Nuevo cliente” (sin saldo anterior) + sección **Crédito**: “Límite de crédito $” (hint “0 = sin límite: no se avisa.”) y “Días de crédito” (hint “Los fiados vencen a los N días.”). Guarda con `PATCH /admin/customers/{id}` y `POST /admin/customers/{id}/credit`.
- Botón “Guardar cambios”. Éxito: “Cliente actualizado”.

## 7. `/admin/clientes/importar` (W-E1)
```
‹ Clientes
Importar deudores
Sube la lista en CSV (en Excel: Archivo → Guardar como → CSV). Columnas: nombre, telefono, tipo, deuda, nota (y opcionales negocio, cedula).
[ Elegir archivo CSV ]      Máximo 1 MB y 2.000 filas.

Vista previa · 5 filas: 3 listas, 2 con error · Deuda total $1.290,50
Línea  Nombre            Tipo    Deuda     Resultado
2      Sra. Elena Díaz   Detal   $12,50    [Lista]
5      —                 Detal   $3,00     [Falta el nombre]
…
[ Importar 3 filas válidas ]     Las filas con error no se importan.
```
- Errores por fila: los de la API tal cual (“Falta el nombre”, “Teléfono inválido”, “Teléfono repetido en la línea N”, “Ya existe un cliente con ese teléfono”, “Tipo debe ser detal o mayor”, “Monto inválido: escribe 1234,56 sin puntos de miles”).
- Éxito: “Se importaron N clientes.” y, si hubo, “M filas con error no se importaron.” Token vencido (`IMPORT_PREVIEW_EXPIRED`): `detail` + “Vuelve a subir el archivo.”

## 8. `/admin/productos` (W-E1)
- Encabezado “Productos” · acciones “Cambiar precios” (secundario) y “Nuevo producto” (primario). Chips por categoría + “Todas”; “Nueva categoría” como enlace.
- Tabla (escritorio) / filas (teléfono): “Producto”, “Unidad”, “Mayor”, “Detal” (sin detal: “Usa el de mayor”), “Detal en Bs”, “Activo” (Switch). Inactivo: chip “Inactivo”.
- Hoja “Nuevo producto” / “Editar producto”: “Nombre”, “Categoría”, “Unidad” (placeholder “unidad, paquete, kg”), “Precio mayor $”, “Precio detal $ (opcional)” (hint “Si lo dejas vacío, se usa el de mayor.”), “Descripción (opcional)”, “Activo”. Botón “Guardar”. Pestaña “Historial de precios”: fecha, tipo (“Mayor”/“Detal”), antes → después, quién.
- Hoja “Cambiar precios”: “¿Qué precio?” (Mayor | Detal) · “¿Cómo?” (Porcentaje | Monto) · “Valor” (hint “Negativo para bajar.”) · “Redondear a” (opcional) · alcance (categoría o seleccionados). “Ver cambios” → tabla “Producto · Antes · Después” → “Aplicar a N productos”. Éxito: “Precios actualizados”. `PRICE_PREVIEW_EXPIRED`: `detail` + “Vuelve a ver los cambios.”
- Vacío: “Todavía no hay productos” · “Crea las categorías y productos con su precio mayor y detal.”

## 9. `/admin/tasa` (W-E1)
```
Tasa
Tasa BCV de hoy · martes 21 de octubre
Bs 185,20                        ← 48 px
[ Fijar a mano ]  [ Traer del BCV ]

Historial
21 oct   BCV      Bs 185,20
20 oct   Manual   Bs 186,00   (Admin)
```
- “Fijar a mano”: hoja con “Fecha” y “Bs por dólar” → “Guardar tasa”. Éxito: “Tasa guardada”.
- “Traer del BCV” (`POST /admin/rates/sync`): éxito “Tasa actualizada”; error de la API tal cual.
- Sin tasa hoy: `InlineAlert` amarillo “No hay tasa de hoy. Los montos en Bs se muestran como “Bs —” hasta que la fijes o llegue la del BCV.”

## 10. `/admin/configuracion` (W-E1)
Secciones (en el teléfono, filas que abren cada hoja; en escritorio, pestañas):
- **Negocio:** “Nombre del negocio” (hint “Se ve en la barra y en el estado de cuenta.”), “WhatsApp”, “Teléfono”, “Dirección”. “Guardar”. Éxito: “Configuración guardada”.
- **Cobros:** métodos (“Pago móvil”, “Transferencia”, “Zelle”, “Efectivo USD”) con su moneda, cuentas bancarias (con su cuenta del negocio) y cuentas del negocio. Desactivar = Switch “Activo” (no hay borrar). Botones “Nuevo método”, “Nueva cuenta”.
- **Crédito:** “Días de crédito por defecto” (hint “Se usan al crear clientes nuevos.”).
- **Administradores:** lista con nombre y teléfono; “Nuevo administrador” (nombre, teléfono, contraseña temporal); por fila “Restablecer contraseña” → confirmación “Se le pedirá cambiarla al entrar.” y muestra la contraseña temporal una sola vez con “Copiar”.

## 11. `/admin/auditoria` (W-E1)
- Filtros: “Qué” (entidad), “Quién” (actor). Filas: hora, quién, acción en palabras (“Registró un abono de $20,00”, “Anuló un fiado”, “Cambió precios (12 productos)”), entidad enlazada y, al tocar, el detalle. Cursor “Cargar más”.
- Vacío: “Todavía no hay acciones registradas.”

## 12. Componentes (UI kit, `web/src/components/ui`)
| Componente | Uso |
|---|---|
| `Button` (primary negro, secondary gris, ghost, danger rojo; md 48 px, lg 56 px; `loading`) | una sola acción primaria por vista |
| `IconButton` (48 px, `label` obligatorio) | cerrar, menú |
| `TextField`, `SelectField`, `TextAreaField` | caja gris; al enfocar, borde de tinta de 2 px; error en rojo con `aria-describedby` |
| `SearchField` | píldora gris con “Limpiar búsqueda” |
| `FilterChips` · `SegmentedControl` | selección en naranja de horno (único uso del color de marca junto al foco) |
| `Switch` | activar/desactivar productos, métodos y cuentas |
| `MoneyText` · `BalanceFigure` | USD con Bs de la API · saldo grande con rótulo y transición |
| `StatusPill` | estados con texto: “Vencido $X”, “Detal”, “Mayor”, “Anulado”, “Inactivo”, “Sin tasa” |
| `ListRow` · `IconCircle` · `Avatar` | filas con círculo de 40 px |
| `DataTable` | catálogos y registros; `nextCursor` + `onLoadMore` → “Cargar más”; `mobileRender` bajo 768 px |
| `Sheet` | hoja inferior en el teléfono, diálogo centrado desde 640 px |
| `ConfirmDialog` | anular/revertir: motivo obligatorio y, si aplica, opciones |
| `ActionBar` | dos acciones fijas abajo en el teléfono |
| `InlineAlert` · `useToast` | avisos en el flujo · confirmación breve |
| `EmptyState` · `Skeleton` · `SkeletonRows` | vacíos que enseñan · carga con la forma del contenido |
| `Stepper` | − cantidad + (48 px), hasta 3 decimales |
| `PageHeader` · `Section` | título, contexto, acciones y “‹ volver” |

Helpers de `web/src/lib`: `clientFetch` / `apiFetch`, `useIdempotencyKey`, `useDebouncedValue` (300 ms), `fmtUsd` / `fmtBs` / `fmtRate` / `fmtDate` / `fmtTime` / `fmtDateBig` / `fmtRelativeDay`, `normalizeAmountInput`, `normalizeVePhone` / `formatVePhone` / `whatsappLink`, `writeSession` (para `/cambiar-contrasena`).
