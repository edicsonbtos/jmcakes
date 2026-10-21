---
name: Panel de la panadería
description: Cuaderno de fiado con la claridad de una app de delivery, para el dueño en el mostrador.
colors:
  canvas: "#FFFFFF"
  canvas-subtle: "#F4F4F2"
  surface-sunken: "#EDEDEA"
  line: "#E6E6E3"
  line-strong: "#CFCFCB"
  ink: "#111111"
  ink-muted: "#5C5C58"
  ink-faint: "#6B6B67"
  primary: "#111111"
  primary-hover: "#2E2E2C"
  on-primary: "#FFFFFF"
  brand: "#C94C0A"
  brand-ink: "#B8460A"
  brand-subtle: "#FFF0E6"
  debt: "#C4271B"
  debt-subtle: "#FDEDEB"
  favor: "#0A7A3F"
  favor-subtle: "#E6F4EC"
  warn: "#8F5B00"
  warn-subtle: "#FFF3D9"
typography:
  amount:
    fontFamily: "Archivo Variable, Archivo, system-ui, sans-serif"
    fontSize: "3rem"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "-0.03em"
    fontFeature: "\"tnum\" 1"
    fontVariation: "\"wdth\" 88"
  headline:
    fontFamily: "Archivo Variable, Archivo, system-ui, sans-serif"
    fontSize: "2rem"
    fontWeight: 800
    lineHeight: 1.125
    letterSpacing: "-0.025em"
    fontVariation: "\"wdth\" 92"
  title:
    fontFamily: "Archivo Variable, Archivo, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 800
    lineHeight: 1.25
    letterSpacing: "-0.025em"
    fontVariation: "\"wdth\" 92"
  section:
    fontFamily: "Archivo Variable, Archivo, system-ui, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 800
    lineHeight: 1.4
  body:
    fontFamily: "Archivo Variable, Archivo, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
  row-title:
    fontFamily: "Archivo Variable, Archivo, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.5
  label:
    fontFamily: "Archivo Variable, Archivo, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 600
    lineHeight: 1.43
  pill:
    fontFamily: "Archivo Variable, Archivo, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 700
    lineHeight: 1.33
rounded:
  sm: "8px"
  md: "12px"
  lg: "16px"
  sheet: "20px"
  pill: "9999px"
spacing:
  "1": "4px"
  "2": "8px"
  "3": "12px"
  "4": "16px"
  "5": "20px"
  "6": "24px"
  "8": "32px"
  "10": "40px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.md}"
    padding: "0 20px"
    height: "48px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-primary-lg:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.md}"
    padding: "0 24px"
    height: "56px"
  button-secondary:
    backgroundColor: "{colors.canvas-subtle}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "0 20px"
    height: "48px"
  button-danger:
    backgroundColor: "{colors.debt-subtle}"
    textColor: "{colors.debt}"
    rounded: "{rounded.md}"
    padding: "0 20px"
    height: "48px"
  field:
    backgroundColor: "{colors.canvas-subtle}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "0 16px"
    height: "48px"
  search:
    backgroundColor: "{colors.canvas-subtle}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    height: "48px"
  chip:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: "0 16px"
    height: "40px"
  chip-selected:
    backgroundColor: "{colors.brand-subtle}"
    textColor: "{colors.brand-ink}"
    rounded: "{rounded.pill}"
  status-pill-debt:
    backgroundColor: "{colors.debt-subtle}"
    textColor: "{colors.debt}"
    rounded: "{rounded.pill}"
    padding: "0 10px"
    height: "24px"
  list-row:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    padding: "12px 16px"
    height: "64px"
  icon-circle:
    backgroundColor: "{colors.canvas-subtle}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    size: "40px"
  sheet:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sheet}"
---

# Design System: Panel de la panadería

<!-- Escrito desde lo construido en E1 (web/src/app/globals.css, web/src/components/ui, /design y las muestras). Fuente de tokens: docs/design/tokens.json. Supuestos de este pase (sin entrevista al dueño): el nombre de la estrella polar y los nombres descriptivos de los colores. -->

## Overview

**Creative North Star: "El cuaderno con factura de delivery"**

El panel reemplaza el cuaderno de deudas del mostrador y lo dibuja como la factura de una app de delivery: cada cliente es una ficha con su saldo enorme, la prueba del dinero (Bs debajo, chip de vencido) y dos acciones al alcance del pulgar. Es un sistema de salida estándar, con Uber y Rappi como vara de calidad: blanco y gris claro, tinta negra, un botón principal negro, hojas inferiores y un solo color de marca. Nada de tarjetas KPI en rejilla ni tablas apretadas.

La densidad es de app de teléfono aun en escritorio: filas de 64 px, toques de 48 px, montos muy pesados y estrechos con cifras tabulares. El color no decora: dice “Debe” (rojo), “A favor” (verde), qué está seleccionado o enfocado (naranja de horno) y nada más. Cada estado lleva texto; el color solo lo refuerza.

El movimiento existe en un solo momento: cuando se fía o se abona, el monto grande de la ficha entra al nuevo saldo con un fundido y desenfoque corto. Las hojas suben desde abajo en el teléfono y aparecen centradas en escritorio.

**Key Characteristics:**
- Restringido: neutros + un acento (naranja de horno) + dos colores de significado (Debe / A favor).
- Una sola familia (Archivo), títulos y montos a 800 y estrechos; cifras tabulares en todo número.
- Primario negro, uno por vista; secundario gris lleno; destructivo en rojo suave.
- Planos por defecto: bordes de 1 px para separar, sombra solo en lo que flota (hojas, avisos).
- El dinero lo calcula la API: la UI muestra USD con los Bs que manda el servidor.

## Colors

Paleta restringida de recibo: papel blanco, gris de mostrador, tinta negra y un naranja tostado que solo aparece para marcar marca, foco y selección.

### Primary
- **Tinta de recibo** (#111111): botón principal, títulos y montos. En oscuro se invierte a casi blanco (#F4F4F2) con texto negro.
- **Naranja de horno** (#C94C0A): círculo de marca con la inicial del negocio, anillo de foco (2 px, separado 2 px), chip y segmento seleccionados, ícono de la sección activa. Blanco sobre él cumple 4,64:1.
- **Naranja tostado para texto** (#B8460A) sobre **crema de horno** (#FFF0E6): texto y fondo del chip seleccionado.

### Secondary
- **Rojo Debe** (#C4271B) sobre **rosa deuda** (#FDEDEB): rótulo y monto de “Debe”, chip “Vencido”, cargos (+) del historial, botón destructivo, borde de campo con error.
- **Verde A favor** (#0A7A3F) sobre **verde claro** (#E6F4EC): rótulo y monto de “A favor”, abonos (−) del historial, avisos de éxito.

### Tertiary
- **Mostaza de aviso** (#8F5B00) sobre **amarillo pálido** (#FFF3D9): advertencias que no bloquean (“Supera el límite de crédito ($X). Se registra igual.”, “Sin tasa”).

### Neutral
- **Papel** (#FFFFFF): fondo de página, filas, hojas.
- **Gris de mostrador** (#F4F4F2): campos, buscador, botón secundario, círculos de ícono, fila en hover, nav activa.
- **Gris hundido** (#EDEDEA): estado presionado del secundario y del Stepper.
- **Línea** (#E6E6E3) y **línea fuerte** (#CFCFCB): divisores de filas y bordes de chips; la fuerte en hover y en la manija de la hoja.
- **Tinta suave** (#5C5C58): textos secundarios, Bs debajo de cada monto, horas y autores.
- **Tinta tenue** (#6B6B67): marcadores de posición y “—”.

### Named Rules
**The Un Solo Horno Rule.** El naranja solo marca la marca, el foco y la selección. Nunca un botón, un fondo de sección ni un monto.

**The Debe Es Rojo Rule.** Rojo = la deuda sube o existe; verde = baja o hay saldo a favor. Ningún otro elemento usa esos dos colores, y siempre van con su palabra (“Debe”, “A favor”, “Vencido”).

## Typography

**Display Font:** Archivo Variable (con system-ui)
**Body Font:** Archivo Variable (con system-ui)

**Character:** Una grotesca de trabajo con eje de ancho: estrecha y muy pesada en títulos y montos, normal en el texto. Suena a total de factura, no a revista.

### Hierarchy
- **Amount** (800, 3rem, 1, ancho 88 %, −0,03em, tabular): el saldo de la ficha y el “Por cobrar” de la lista. Uno por pantalla.
- **Headline** (800, 2rem, ancho 92 %, −0,025em): título de página en escritorio y del login.
- **Title** (800, 1.5rem): título de página en el teléfono, nombre del cliente.
- **Section** (800, 1.25rem): “Movimientos”, títulos de hoja; 3xl estrecho (2rem) para el total de la hoja de fiar.
- **Row title** (600, 1rem): concepto de cada fila, hasta dos líneas.
- **Body** (400, 1rem, 1.5): textos y descripciones.
- **Label** (600, 0.875rem): etiquetas de campo; los grupos por día (“Hoy”, “Ayer”) a 700 en tinta suave.
- **Pill** (700, 0.75rem, tabular): chips de estado.

### Named Rules
**The Cifra Tabular Rule.** Todo número de dinero, fecha, hora o cantidad usa cifras tabulares (`tnum`). Los montos alineados a la derecha deben cuadrar como en un recibo.

**The Rótulo Antes Del Monto Rule.** Un monto grande siempre va con su rótulo (“Debe”, “A favor”, “Al día”, “Por cobrar”) y sus Bs debajo; nunca un número suelto.

## Layout

- **Teléfono primero (390 px):** columna única con 16 px de margen. Barra superior de 64 px con la marca y la tasa; barra inferior de 64 px con Inicio, Clientes, Productos y Más solo en páginas principales.
- **Ficha:** nombre → datos en línea → saldo grande → acciones secundarias → historial agrupado por día. Las dos acciones principales viven en una barra fija abajo (con el área segura); la página reserva su alto para que nada quede tapado.
- **Escritorio (≥1024 px):** riel izquierdo de 248 px (marca, secciones, tasa, cerrar sesión) y contenido centrado hasta 1152 px con 40 px de margen. La barra de acciones de la ficha pasa a estar en línea bajo el saldo (≥768 px).
- **Listas:** filas a ancho completo con divisores; en escritorio, tabla aireada (filas de 64 px, encabezado de 14 px sin mayúsculas); bajo 768 px, la misma información en filas de app.
- **Ritmo:** múltiplos de 4 px; 24 px entre bloques de la ficha, 40 px entre secciones de `/design`; más aire arriba de un título que debajo.

## Elevation & Depth

Plano por defecto. Las superficies se separan con fondo gris y líneas de 1 px; la sombra aparece solo en lo que flota sobre la página.

### Shadow Vocabulary
- **Hoja** (`box-shadow: 0 -8px 32px rgba(17, 17, 17, 0.16)`): hojas inferiores y diálogos, sobre un velo de tinta al 48 %.
- **Flotante** (`box-shadow: 0 8px 24px rgba(17, 17, 17, 0.12)`): avisos (toast) y el pulgar del interruptor.

### Named Rules
**The Borde O Sombra Rule.** Cada superficie declara su elevación una vez: borde de 1 px o sombra, nunca ambos.

## Shapes

Esquinas suaves y consistentes: 12 px para botones, campos y cajas de resumen; 16 px para diálogos en escritorio; 20 px para la parte superior de las hojas; píldora completa para chips, buscador, estados, círculos de ícono e iniciales. Las filas no tienen esquinas: son franjas a sangre separadas por líneas. Nada de tarjetas anidadas.

## Components

### Buttons
- **Shape:** esquinas de 12 px; 48 px de alto (56 px en las acciones principales de la ficha y el login).
- **Primary:** tinta (#111111) con texto blanco, 700. Uno por vista: “Registrar abono”, “Entrar”, “Nuevo cliente”.
- **Hover / Focus:** hover a #2E2E2C; al presionar se encoge al 98 %; foco con anillo naranja de 2 px. Deshabilitado: gris hundido con tinta tenue. Cargando: indicador giratorio y deshabilitado hasta la respuesta.
- **Secondary / Ghost / Danger:** secundario gris lleno (“Fiar productos”, “Importar”); fantasma sin fondo con ícono (“Estado de cuenta”, “Editar”); peligro rosa con texto rojo (“Anular”, “Revertir”).
- **IconButton:** círculo de 48 px con etiqueta obligatoria.

### Chips
- **Style:** píldora de 40 px (zona táctil de 48 px), borde de 1,5 px en línea, texto 14 px 600.
- **State:** seleccionado con borde naranja, crema de horno y texto naranja tostado (`aria-pressed`). El control segmentado usa la misma selección con un anillo naranja sobre papel.

### Cards / Containers
- **Corner Style:** 12 px en cajas de resumen (p. ej. “Abona $20,00 … → queda debiendo $77,00”).
- **Background:** gris de mostrador, sin borde ni sombra.
- **Border:** ninguno; los grupos se separan con espacio y líneas.

### Inputs / Fields
- **Style:** caja gris de mostrador sin borde visible, 48 px (56 px en el login), esquinas de 12 px, etiqueta 14 px 600 arriba.
- **Focus:** el borde transparente de 2 px pasa a tinta y el fondo a papel.
- **Error / Disabled:** borde rojo y mensaje rojo debajo (enlazado con `aria-describedby`); deshabilitado al 60 %.
- **Search:** píldora gris con lupa y botón “Limpiar búsqueda”.

### Navigation
- **Escritorio:** riel con secciones de 48 px; activa en gris de mostrador, 700 y el ícono en naranja; inactivas en tinta suave.
- **Teléfono:** barra superior con la marca y “Tasa Bs X”; barra inferior de 4 pestañas con íconos de 24 px; “Más” abre una hoja.

### Ficha del cliente (firma)
El saldo grande (`BalanceFigure`): rótulo de color a 16 px 700, monto a 48 px estrecho y pesado en el color del saldo, Bs a 18 px en tinta suave y el chip “Vencido $X”. Al cambiar el saldo, el monto entra con fundido, desplazamiento de 0,35em y desenfoque de 6 px en 420 ms (`cubic-bezier(0.2, 0.8, 0.2, 1)`); con movimiento reducido, cambia sin animar.

### Fila de movimiento
Círculo de 40 px con el ícono del tipo (fiado, abono, anulación, reverso, saldo anterior, ajuste), concepto en dos líneas, “Tipo · hora · quién” debajo, y a la derecha el efecto (+ rojo / − verde) con “Saldo $X”. Anulados y revertidos quedan tachados en gris con su chip.

### Hoja inferior
Sobre `<dialog>`: manija, título a 20 px 800, botón de cerrar, cuerpo con scroll y un pie fijo con el total de la API y la acción. Sube en 260 ms en el teléfono; en escritorio es un diálogo centrado de hasta 512 px.

## Do's and Don'ts

### Do:
- **Do** mostrar cada monto en USD con sus Bs de la API debajo; sin tasa, “Bs —”.
- **Do** poner una sola acción negra por vista y las dos acciones de la ficha en la barra fija inferior del teléfono.
- **Do** usar hojas inferiores para fiar, abonar, anular y revertir, con el resultado (“queda debiendo $Z”) visible antes de confirmar.
- **Do** dar a cada toque al menos 48 px y a cada estado su palabra.
- **Do** usar solo los tokens de `globals.css`; la paleta por defecto de Tailwind está apagada (`--color-*: initial`).

### Don't:
- **Don't** usar el naranja para botones, fondos o montos: es marca, foco y selección.
- **Don't** armar rejillas de tarjetas KPI ni tablas densas; los totales van como una cifra grande con su rótulo.
- **Don't** escribir el nombre del negocio en el código: sale de `business.name`.
- **Don't** combinar borde y sombra en la misma superficie, ni anidar tarjetas.
- **Don't** animar más que el cambio de saldo, la entrada de las hojas y los avisos.
