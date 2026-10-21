"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowDownLeft, ArrowUpRight, Inbox, ShoppingBasket, Users } from "lucide-react";
import {
  Avatar,
  BalanceFigure,
  Button,
  ConfirmDialog,
  DataTable,
  EmptyState,
  FilterChips,
  IconButton,
  IconCircle,
  InlineAlert,
  ListRow,
  MoneyText,
  SearchField,
  SegmentedControl,
  SelectField,
  Sheet,
  Skeleton,
  SkeletonRows,
  StatusPill,
  Stepper,
  Switch,
  TextAreaField,
  TextField,
  useToast,
} from "@/components/ui";
import { fmtUsd } from "@/lib/format";
import { PRODUCTOS } from "./fixtures";

type Theme = "system" | "light" | "dark";

const COLOR_ROLES: { group: string; tokens: { name: string; use: string }[] }[] = [
  {
    group: "Superficies",
    tokens: [
      { name: "canvas", use: "Fondo de página" },
      { name: "canvas-subtle", use: "Campos, chips, filas activas" },
      { name: "surface-raised", use: "Hojas y diálogos" },
      { name: "line", use: "Divisores" },
    ],
  },
  {
    group: "Tinta",
    tokens: [
      { name: "ink", use: "Texto y montos" },
      { name: "ink-muted", use: "Texto secundario, Bs" },
      { name: "ink-faint", use: "Marcadores de posición" },
      { name: "primary", use: "Botón principal" },
    ],
  },
  {
    group: "Significado",
    tokens: [
      { name: "brand", use: "Marca, foco y selección" },
      { name: "debt", use: "Debe, vencido, anular" },
      { name: "favor", use: "A favor, abono" },
      { name: "warn", use: "Advertencias que no bloquean" },
    ],
  },
];

const TYPE_SCALE = [
  { cls: "text-amount amount", label: "Monto 48 · 800", sample: "$97,00" },
  { cls: "text-3xl font-heavy [font-stretch:92%] tracking-[-0.025em]", label: "Título 32 · 800", sample: "Clientes" },
  { cls: "text-2xl font-heavy [font-stretch:92%] tracking-[-0.025em]", label: "Título 24 · 800", sample: "Bodega El Samán" },
  { cls: "text-xl font-heavy", label: "Sección 20 · 800", sample: "Movimientos" },
  { cls: "text-base font-semibold", label: "Fila 16 · 600", sample: "80 Canilla, 24 Golfeado" },
  { cls: "text-base", label: "Texto 16 · 400", sample: "Lo que ya se abonó paga primero otras deudas." },
  { cls: "text-sm text-ink-muted", label: "Detalle 14 · 400", sample: "Fiado · 3:30 p. m. · Admin" },
];

function useTheme(): [Theme, (t: Theme) => void] {
  const [theme, setTheme] = useState<Theme>("system");
  useEffect(() => {
    const root = document.documentElement;
    if (theme === "system") delete root.dataset.theme;
    else root.dataset.theme = theme;
    return () => {
      delete root.dataset.theme;
    };
  }, [theme]);
  return [theme, setTheme];
}

function Block({ title, children, id }: { title: string; children: React.ReactNode; id: string }) {
  return (
    <section aria-labelledby={id} className="border-t border-line py-10">
      <h2 id={id} className="mb-6 text-2xl font-heavy text-ink">
        {title}
      </h2>
      {children}
    </section>
  );
}

/** `/design`: tokens y componentes del panel con sus estados, en claro y oscuro. */
export function DesignShowcase() {
  const toast = useToast();
  const [theme, setTheme] = useTheme();
  const [chip, setChip] = useState<"todos" | "deuda" | "vencidos">("deuda");
  const [seg, setSeg] = useState<"RETAIL" | "WHOLESALE">("RETAIL");
  const [sw, setSw] = useState(true);
  const [q, setQ] = useState("0414");
  const [qty, setQty] = useState("3");
  const [bal, setBal] = useState("97.00");
  const [sheet, setSheet] = useState(false);
  const [confirm, setConfirm] = useState(false);

  return (
    <div className="mx-auto w-full max-w-6xl px-4 pb-24 pt-8 md:px-8">
      <header className="flex flex-wrap items-end justify-between gap-6 pb-10">
        <div className="max-w-2xl">
          <h1 className="text-3xl font-heavy text-ink">Sistema del panel</h1>
          <p className="mt-2 text-base text-ink-muted">
            Salida estándar de apps de delivery: blanco y gris claro, tinta negra, botón principal negro y un solo color de
            marca para foco y selección. Los datos de esta página son de ejemplo.
          </p>
          <nav aria-label="Pantallas de muestra" className="mt-4 flex flex-wrap gap-2">
            <Link href="/design/ficha" className="inline-flex h-12 items-center rounded-pill bg-canvas-subtle px-5 font-semibold text-ink hover:bg-surface-sunken">
              Muestra: ficha del cliente (390 px)
            </Link>
            <Link href="/design/clientes" className="inline-flex h-12 items-center rounded-pill bg-canvas-subtle px-5 font-semibold text-ink hover:bg-surface-sunken">
              Muestra: lista de clientes (1440 px)
            </Link>
          </nav>
        </div>
        <SegmentedControl
          label="Tema"
          value={theme}
          onChange={setTheme}
          options={[
            { value: "system", label: "Sistema" },
            { value: "light", label: "Claro" },
            { value: "dark", label: "Oscuro" },
          ]}
          className="w-full sm:w-80"
        />
      </header>

      <Block title="Color por rol" id="color">
        <div className="grid gap-8 md:grid-cols-3">
          {COLOR_ROLES.map((g) => (
            <div key={g.group}>
              <h3 className="mb-3 text-base font-bold text-ink">{g.group}</h3>
              <ul className="flex flex-col gap-3">
                {g.tokens.map((t) => (
                  <li key={t.name} className="flex items-center gap-3">
                    <span aria-hidden className="size-12 shrink-0 rounded-md border border-line" style={{ background: `var(--color-${t.name})` }} />
                    <span className="flex flex-col">
                      <code className="text-sm font-semibold text-ink">{t.name}</code>
                      <span className="text-sm text-ink-muted">{t.use}</span>
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </Block>

      <Block title="Tipografía" id="tipo">
        <p className="mb-6 max-w-2xl text-base text-ink-muted">
          Archivo, una sola familia: títulos y montos estrechos y muy pesados, cifras tabulares en todo número.
        </p>
        <ul className="flex flex-col divide-y divide-line">
          {TYPE_SCALE.map((t) => (
            <li key={t.label} className="flex flex-col gap-1 py-4 md:flex-row md:items-baseline md:gap-8">
              <span className="w-44 shrink-0 text-sm text-ink-muted">{t.label}</span>
              <span className={`${t.cls} text-ink`}>{t.sample}</span>
            </li>
          ))}
        </ul>
      </Block>

      <Block title="Botones" id="botones">
        <div className="flex flex-wrap items-center gap-3">
          <Button>Registrar abono</Button>
          <Button variant="secondary">Fiar productos</Button>
          <Button variant="ghost">Estado de cuenta</Button>
          <Button variant="danger">Anular</Button>
          <Button loading>Guardando</Button>
          <Button disabled>Fiar</Button>
          <Button size="lg">Entrar</Button>
          <IconButton label="Más opciones" variant="secondary">
            <ArrowUpRight aria-hidden className="size-5" />
          </IconButton>
        </div>
      </Block>

      <Block title="Campos y controles" id="campos">
        <div className="grid gap-6 md:grid-cols-2">
          <TextField label="Teléfono" placeholder="0414-123.45.67" inputMode="tel" />
          <TextField label="Monto en Bs" prefix="Bs" defaultValue="3704,00" size="lg" inputMode="decimal" />
          <TextField label="Referencia" defaultValue="0045" error="Esa referencia ya fue registrada en esta cuenta." />
          <TextField label="Saldo anterior $" hint="Negativo = a favor. Escribe 1234,56 sin puntos de miles." placeholder="0,00" />
          <SelectField label="Método" defaultValue="pm">
            <option value="pm">Pago móvil (Bs)</option>
            <option value="ze">Zelle (USD)</option>
            <option value="ef">Efectivo USD</option>
          </SelectField>
          <TextAreaField label="Nota (opcional)" placeholder="Ej.: lo retiró su hijo" rows={2} />
          <SearchField label="Buscar cliente" placeholder="Nombre, negocio, teléfono, cédula o apodo" value={q} onValueChange={setQ} />
          <SegmentedControl
            label="Tipo de cliente"
            value={seg}
            onChange={setSeg}
            options={[
              { value: "RETAIL", label: "Detal" },
              { value: "WHOLESALE", label: "Mayor" },
            ]}
          />
          <FilterChips
            label="Filtrar clientes"
            value={chip}
            onChange={setChip}
            options={[
              { value: "todos", label: "Todos" },
              { value: "deuda", label: "Con deuda" },
              { value: "vencidos", label: "Vencidos" },
            ]}
          />
          <Switch checked={sw} onChange={setSw} label="Activo" description="Se puede fiar y aparece en la lista de precios." />
          <div className="flex items-center justify-between gap-3">
            <span className="text-base font-semibold text-ink">Canilla</span>
            <Stepper label="Canilla" value={qty} onChange={setQty} />
          </div>
        </div>
      </Block>

      <Block title="Dinero y estados" id="dinero">
        <div className="grid gap-10 md:grid-cols-2">
          <div className="flex flex-col gap-4">
            <BalanceFigure balance={bal} balanceVes={bal === "97.00" ? "17964.40" : "14260.40"}>
              <StatusPill tone="debt" dot>
                Vencido $61,00
              </StatusPill>
            </BalanceFigure>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => setBal((b) => (b === "97.00" ? "77.00" : "97.00"))}>
                Simular abono de $20
              </Button>
            </div>
            <BalanceFigure balance="-4.00" balanceVes="-740.80" size="xl" />
            <BalanceFigure balance="0.00" balanceVes="0.00" size="xl" />
          </div>
          <div className="flex flex-col gap-5">
            <div className="flex flex-wrap gap-2">
              <StatusPill tone="debt" dot>
                Vencido $18,50
              </StatusPill>
              <StatusPill tone="favor">A favor $4,00</StatusPill>
              <StatusPill tone="neutral">Detal</StatusPill>
              <StatusPill tone="neutral">Anulado</StatusPill>
              <StatusPill tone="warn">Sin tasa</StatusPill>
              <StatusPill tone="brand">Nuevo</StatusPill>
            </div>
            <div className="flex flex-wrap items-start gap-8">
              <MoneyText usd="1234.50" ves="228629.40" size="xl" />
              <MoneyText usd="36.00" ves="6667.20" size="md" signed tone="debt" />
              <MoneyText usd="-20.00" ves="-3704.00" size="md" signed tone="favor" />
              <MoneyText usd="12.00" ves={null} size="md" />
            </div>
            <InlineAlert tone="warn">Supera el límite de crédito ($60,00). Se registra igual.</InlineAlert>
            <InlineAlert tone="error">Esa referencia ya fue registrada en esta cuenta.</InlineAlert>
            <InlineAlert tone="success">Se importaron 4 clientes. 1 fila con error no se importó.</InlineAlert>
            <InlineAlert tone="info">El abono queda a favor: este cliente no tiene deuda.</InlineAlert>
          </div>
        </div>
      </Block>

      <Block title="Listas" id="listas">
        <div className="grid gap-10 md:grid-cols-2">
          <ul className="-mx-4 divide-y divide-line">
            <li>
              <ListRow
                leading={<IconCircle><ShoppingBasket /></IconCircle>}
                title="80 Canilla, 24 Golfeado"
                subtitle="Fiado · 9:15 a. m. · Admin"
                trailing={
                  <>
                    <span className="text-base font-bold tnum text-debt">+$56,00</span>
                    <span className="text-xs tnum text-ink-muted">Saldo $76,00</span>
                  </>
                }
              />
            </li>
            <li>
              <ListRow
                leading={<IconCircle tone="favor"><ArrowDownLeft /></IconCircle>}
                title="Pago móvil · ref. 004512 · Bs 3.704,00"
                subtitle="Abono · 11:30 a. m. · Admin"
                trailing={
                  <>
                    <span className="text-base font-bold tnum text-favor">−$20,00</span>
                    <span className="text-xs tnum text-ink-muted">Saldo $20,00</span>
                  </>
                }
              />
            </li>
            <li>
              <ListRow
                href="/design/ficha"
                leading={<Avatar name="Bodega El Samán" />}
                title="Bodega El Samán"
                subtitle={<span className="text-debt">Vencido $61,00</span>}
                trailing={<MoneyText usd="97.00" ves="17964.40" tone="debt" align="end" />}
              />
            </li>
          </ul>
          <div className="flex flex-col gap-6">
            <SkeletonRows rows={3} />
            <div className="flex gap-3">
              <Skeleton className="h-12 w-40" />
              <Skeleton className="h-12 flex-1" />
            </div>
          </div>
        </div>
      </Block>

      <Block title="Tabla con cursor" id="tabla">
        <DataTable
          caption="Productos de ejemplo"
          rows={PRODUCTOS}
          rowKey={(p) => p.id}
          columns={[
            { key: "n", header: "Producto", render: (p) => <span className="font-semibold">{p.name}</span> },
            { key: "u", header: "Unidad", render: (p) => <span className="text-ink-muted">{p.unitLabel}</span> },
            { key: "m", header: "Mayor", align: "end", render: (p) => fmtUsd(p.price) },
            {
              key: "d",
              header: "Detal",
              align: "end",
              render: (p) => (p.retailPrice ? fmtUsd(p.retailPrice) : <span className="text-ink-faint">Usa el de mayor</span>),
            },
          ]}
          nextCursor="muestra"
          onLoadMore={() => toast.show("En la muestra no hay más productos")}
        />
      </Block>

      <Block title="Vacíos, hojas y avisos" id="hojas">
        <div className="grid gap-10 md:grid-cols-2">
          <EmptyState
            icon={<Inbox />}
            title="Todavía no hay movimientos"
            description="Cuando fíes productos o registres un abono, aparecerán aquí con su saldo."
            action={<Button variant="secondary">Fiar productos</Button>}
          />
          <EmptyState
            icon={<Users />}
            title="Nadie con ese filtro"
            description="Prueba con otra búsqueda o quita el filtro para ver a todos."
          />
        </div>
        <div className="mt-6 flex flex-wrap gap-3">
          <Button variant="secondary" onClick={() => setSheet(true)}>
            Abrir hoja
          </Button>
          <Button variant="danger" onClick={() => setConfirm(true)}>
            Anular fiado
          </Button>
          <Button variant="ghost" onClick={() => toast.show("Abono de $20,00 registrado")}>
            Mostrar aviso
          </Button>
          <Button variant="ghost" onClick={() => toast.show("Sin conexión con el servidor.", { tone: "error" })}>
            Mostrar error
          </Button>
        </div>
        <Sheet
          open={sheet}
          onClose={() => setSheet(false)}
          title="Hoja inferior"
          description="En el teléfono sube desde abajo; desde 640 px es un diálogo centrado."
          footer={
            <Button fullWidth size="lg" onClick={() => setSheet(false)}>
              Listo
            </Button>
          }
        >
          <p className="pt-2 text-base text-ink-muted">Fiar y abonar viven en hojas como esta, con el total de la API al pie.</p>
        </Sheet>
        <ConfirmDialog
          open={confirm}
          onClose={() => setConfirm(false)}
          title="Anular fiado"
          description="Lo que ya se abonó sobre este fiado paga primero otras deudas; solo el sobrante queda a favor."
          confirmLabel="Anular"
          reason={{ placeholder: "Ej.: se registró dos veces" }}
          onConfirm={async () => {
            toast.show("Fiado anulado");
          }}
        />
      </Block>
    </div>
  );
}
