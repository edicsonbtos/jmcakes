"use client";

import { useMemo, useState } from "react";
import { Copy, MessageCircle, Pencil } from "lucide-react";
import {
  ActionBar,
  BalanceFigure,
  Button,
  ConfirmDialog,
  InlineAlert,
  PageHeader,
  SelectField,
  Sheet,
  Stepper,
  StatusPill,
  TextField,
  useToast,
} from "@/components/ui";
import { fmtBs, fmtDayMonth, fmtUsd } from "@/lib/format";
import { formatVePhone, whatsappLink } from "@/lib/phone";
import {
  ABONO_FILA,
  ABONO_QUOTE,
  CLIENTES,
  MOVIMIENTOS_C1,
  MUESTRA_AHORA,
  PRODUCTOS,
  mockFiadoQuote,
  type StatementRow,
} from "./fixtures";
import { KIND_LABEL, MovimientoRow, groupByDay } from "./movimientos";

const cliente = CLIENTES[0];

const METODOS = [
  { id: "pm", label: "Pago móvil (Bs)", currency: "VES", cash: false },
  { id: "tr", label: "Transferencia (Bs)", currency: "VES", cash: false },
  { id: "ze", label: "Zelle (USD)", currency: "USD", cash: false },
  { id: "ef", label: "Efectivo USD", currency: "USD", cash: true },
] as const;

/**
 * Muestra de la ficha del cliente a 390 px (09 §E1 — Agentes, DSN). Datos de ejemplo:
 * W-E1 la arma de verdad contra la API en `/admin/clientes/[id]`.
 */
export function FichaMuestra() {
  const toast = useToast();
  const [rows, setRows] = useState<StatementRow[]>(MOVIMIENTOS_C1);
  const [balance, setBalance] = useState<{ usd: string; ves: string | null | undefined; overdue: string }>({
    usd: cliente.balance,
    ves: cliente.balanceVes,
    overdue: cliente.overdueDebt,
  });
  const [sheet, setSheet] = useState<null | "abono" | "fiar" | "estado">(null);
  const [detalle, setDetalle] = useState<StatementRow | null>(null);
  const [confirm, setConfirm] = useState<null | "anular" | "revertir">(null);

  const groups = useMemo(() => groupByDay(rows, MUESTRA_AHORA), [rows]);
  const overdue = balance.overdue !== "0.00";

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <PageHeader back={{ href: "/design/clientes", label: "Clientes" }} title={cliente.contactName} />

      <div className="-mt-3 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-sm text-ink-muted">
        <StatusPill tone="neutral">{cliente.type === "WHOLESALE" ? "Mayor" : "Detal"}</StatusPill>
        {/* Cada dato es un bloque: al partir la línea no queda un separador colgando. */}
        <span className="tnum">{cliente.phone ? formatVePhone(cliente.phone) : "Sin teléfono"}</span>
        <span>Crédito {cliente.creditDays} días</span>
        {cliente.creditLimit !== "0.00" ? <span className="tnum">Límite {fmtUsd(cliente.creditLimit)}</span> : null}
      </div>

      <BalanceFigure balance={balance.usd} balanceVes={balance.ves}>
        {overdue ? (
          <StatusPill tone="debt" dot>
            Vencido {fmtUsd(balance.overdue)}
          </StatusPill>
        ) : null}
      </BalanceFigure>

      <ActionBar>
        <Button variant="secondary" size="lg" onClick={() => setSheet("fiar")}>
          Fiar productos
        </Button>
        <Button size="lg" onClick={() => setSheet("abono")}>
          Registrar abono
        </Button>
      </ActionBar>

      <div className="-mt-2 flex flex-wrap gap-2">
        <Button variant="ghost" icon={<MessageCircle aria-hidden className="size-5" />} onClick={() => setSheet("estado")} className="-ml-2">
          Estado de cuenta
        </Button>
        <Button variant="ghost" icon={<Pencil aria-hidden className="size-5" />}>
          Editar
        </Button>
      </div>

      <section aria-labelledby="mov-title" className="flex flex-col">
        <h2 id="mov-title" className="text-xl font-heavy text-ink">
          Movimientos
        </h2>
        {groups.map((g) => (
          <div key={g.day} className="mt-3">
            <h3 className="py-2 text-sm font-bold text-ink-muted">{g.day}</h3>
            <ul className="-mx-4 divide-y divide-line">
              {g.rows.map((r) => (
                <li key={r.seq}>
                  <MovimientoRow row={r} onOpen={r.kind === "FIADO" || r.kind === "ABONO" ? setDetalle : undefined} />
                </li>
              ))}
            </ul>
          </div>
        ))}
      </section>

      <AbonoSheet
        open={sheet === "abono"}
        onClose={() => setSheet(null)}
        onDone={() => {
          setSheet(null);
          setRows((prev) => [ABONO_FILA, ...prev]);
          setBalance({ usd: ABONO_QUOTE.balanceAfter, ves: ABONO_QUOTE.balanceAfterVes, overdue: "41.00" });
          toast.show(`Abono de ${fmtUsd(ABONO_QUOTE.amountUsd)} registrado`);
        }}
        balance={balance.usd}
        balanceVes={balance.ves}
      />
      <FiarSheet
        open={sheet === "fiar"}
        onClose={() => setSheet(null)}
        balance={balance.usd}
        onDone={(total, after) => {
          setSheet(null);
          setRows((prev) => [
            {
              seq: (prev[0]?.seq ?? 0) + 1,
              at: MUESTRA_AHORA.toISOString(),
              kind: "FIADO",
              description: "Fiado de la muestra",
              amount: total,
              balanceAfter: after,
              actorName: "Admin",
            },
            ...prev,
          ]);
          // Sin API no hay Bs del nuevo saldo: la muestra oculta esa línea en vez de inventarla.
          setBalance((b) => ({ ...b, usd: after, ves: undefined }));
          toast.show(`Fiado de ${fmtUsd(total)} registrado`);
        }}
      />
      <EstadoSheet open={sheet === "estado"} onClose={() => setSheet(null)} balance={balance.usd} balanceVes={balance.ves} rows={rows} />

      <Sheet
        open={!!detalle}
        onClose={() => setDetalle(null)}
        title={detalle ? KIND_LABEL[detalle.kind] : ""}
        description={detalle?.description}
        footer={
          detalle && !detalle.voided ? (
            <Button variant="danger" fullWidth size="lg" onClick={() => setConfirm(detalle.kind === "FIADO" ? "anular" : "revertir")}>
              {detalle.kind === "FIADO" ? "Anular fiado" : "Revertir abono"}
            </Button>
          ) : null
        }
      >
        {detalle ? (
          <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-3 pt-2 text-base">
            <dt className="text-ink-muted">Monto</dt>
            <dd className="text-right font-bold tnum">{fmtUsd(detalle.amount, { abs: true })}</dd>
            <dt className="text-ink-muted">Saldo después</dt>
            <dd className="text-right tnum">{fmtUsd(detalle.balanceAfter)}</dd>
            <dt className="text-ink-muted">Registró</dt>
            <dd className="text-right">{detalle.actorName}</dd>
            {detalle.voided ? (
              <>
                <dt className="text-ink-muted">Estado</dt>
                <dd className="text-right">
                  <StatusPill tone="neutral">Anulado</StatusPill>
                </dd>
              </>
            ) : null}
          </dl>
        ) : null}
      </Sheet>

      <ConfirmDialog
        open={confirm === "anular"}
        onClose={() => setConfirm(null)}
        title="Anular fiado"
        description="Lo que ya se abonó sobre este fiado paga primero otras deudas; solo el sobrante queda a favor. Queda en el historial."
        confirmLabel="Anular"
        reason={{ placeholder: "Ej.: se registró dos veces" }}
        onConfirm={async () => {
          setConfirm(null);
          setDetalle(null);
          toast.show("Fiado anulado");
        }}
      />
      <ConfirmDialog<"ENTRY_ERROR" | "BANK_RETURN">
        open={confirm === "revertir"}
        onClose={() => setConfirm(null)}
        title="Revertir abono"
        description="La deuda vuelve a subir. Si no hay saldo a favor suficiente, la diferencia aparece como deuda vencida."
        confirmLabel="Revertir"
        choicesLabel="¿Por qué lo reviertes?"
        choices={[
          { value: "ENTRY_ERROR", label: "Me equivoqué al registrarlo", description: "La referencia queda libre para cargarlo bien." },
          { value: "BANK_RETURN", label: "El banco lo devolvió", description: "La referencia queda bloqueada." },
        ]}
        reason={{ placeholder: "Ej.: el banco devolvió la transferencia" }}
        onConfirm={async () => {
          setConfirm(null);
          setDetalle(null);
          toast.show("Abono revertido");
        }}
      />
    </div>
  );
}

function AbonoSheet({
  open,
  onClose,
  onDone,
  balance,
  balanceVes,
}: {
  open: boolean;
  onClose: () => void;
  onDone: () => void;
  balance: string;
  balanceVes: string | null | undefined;
}) {
  const [metodo, setMetodo] = useState<(typeof METODOS)[number]["id"]>("pm");
  const [monto, setMonto] = useState("3704,00");
  const [ref, setRef] = useState("118204");
  const [saving, setSaving] = useState(false);
  const m = METODOS.find((x) => x.id === metodo)!;
  const day = fmtDayMonth(`${ABONO_QUOTE.rate.date}T12:00:00Z`);

  return (
    <Sheet
      open={open}
      onClose={onClose}
      busy={saving}
      title="Registrar abono"
      description={`${cliente.contactName} · Debe ${fmtUsd(balance)}${balanceVes ? ` (${fmtBs(balanceVes)})` : ""}`}
      footer={
        <div className="flex flex-col gap-3">
          <div className="rounded-md bg-canvas-subtle px-4 py-3" aria-live="polite">
            <p className="text-base font-bold tnum text-ink">
              Abona {fmtUsd(ABONO_QUOTE.amountUsd)}{" "}
              <span className="whitespace-nowrap font-medium text-ink-muted">
                ({fmtBs(ABONO_QUOTE.amountLocal)} a tasa del {day})
              </span>
            </p>
            <p className="mt-0.5 text-base tnum text-ink-muted">
              → queda debiendo <span className="font-bold text-debt">{fmtUsd(ABONO_QUOTE.balanceAfter)}</span>
            </p>
          </div>
          <Button
            size="lg"
            fullWidth
            loading={saving}
            onClick={() => {
              setSaving(true);
              setTimeout(() => {
                setSaving(false);
                onDone();
              }, 700);
            }}
          >
            Registrar abono
          </Button>
        </div>
      }
    >
      <div className="flex flex-col gap-4 pt-2">
        <SelectField label="Método" value={metodo} onChange={(e) => setMetodo(e.target.value as typeof metodo)}>
          {METODOS.map((x) => (
            <option key={x.id} value={x.id}>
              {x.label}
            </option>
          ))}
        </SelectField>
        <div className="grid grid-cols-[1fr_8.5rem] gap-3">
          <TextField
            label={m.currency === "VES" ? "Monto en Bs" : "Monto en USD"}
            prefix={m.currency === "VES" ? "Bs" : "$"}
            inputMode="decimal"
            value={monto}
            onChange={(e) => setMonto(e.target.value)}
            size="lg"
          />
          {m.currency === "VES" ? (
            <TextField label={`Tasa del ${day}`} inputMode="decimal" defaultValue="185,20" size="lg" />
          ) : null}
        </div>
        {!m.cash ? (
          <TextField
            label="Referencia"
            hint="Los dígitos que aparecen en el comprobante."
            inputMode="numeric"
            autoComplete="off"
            value={ref}
            onChange={(e) => setRef(e.target.value)}
          />
        ) : null}
        <SelectField label="Cuenta donde entró" defaultValue="b1">
          <option value="b1">Banesco · 0134-…-4521</option>
          <option value="b2">Mercantil · 0105-…-9910</option>
        </SelectField>
        <TextField label="Fecha del pago" type="date" defaultValue="2026-10-21" />
      </div>
    </Sheet>
  );
}

function FiarSheet({
  open,
  onClose,
  onDone,
  balance,
}: {
  open: boolean;
  onClose: () => void;
  onDone: (total: string, after: string) => void;
  balance: string;
}) {
  const [qty, setQty] = useState<Record<string, string>>({ p1: "30", p4: "12" });
  const [saving, setSaving] = useState(false);
  const lines = Object.entries(qty).map(([productId, q]) => ({ productId, qty: q }));
  const quote = mockFiadoQuote(lines, balance, cliente.creditLimit);
  const empty = quote.total === "0.00";

  return (
    <Sheet
      open={open}
      onClose={onClose}
      busy={saving}
      title={`Fiar a ${cliente.contactName}`}
      description="Precios de mayor. Puedes cambiar el precio de cada línea."
      footer={
        <div className="flex flex-col gap-3">
          {quote.warning ? <InlineAlert tone="warn">{quote.warning}</InlineAlert> : null}
          <div className="flex items-end justify-between gap-3">
            <div>
              <p className="text-sm text-ink-muted">Total</p>
              <p className="text-3xl amount text-ink">{fmtUsd(quote.total)}</p>
            </div>
            <p className="pb-1 text-sm tnum text-ink-muted">
              Saldo: {fmtUsd(balance)} → <span className="font-bold text-ink">{fmtUsd(quote.balanceAfter)}</span>
            </p>
          </div>
          <Button
            size="lg"
            fullWidth
            loading={saving}
            disabled={empty}
            onClick={() => {
              setSaving(true);
              setTimeout(() => {
                setSaving(false);
                onDone(quote.total, quote.balanceAfter);
              }, 700);
            }}
          >
            Fiar
          </Button>
        </div>
      }
    >
      <ul className="-mx-5 divide-y divide-line">
        {PRODUCTOS.map((p) => (
          <li key={p.id} className="flex items-center gap-3 px-5 py-3">
            <div className="min-w-0 flex-1">
              <p className="truncate text-base font-semibold text-ink">{p.name}</p>
              <p className="text-sm tnum text-ink-muted">
                {fmtUsd(p.price)} / {p.unitLabel}
              </p>
            </div>
            <Stepper label={p.name} value={qty[p.id] ?? "0"} onChange={(v) => setQty((s) => ({ ...s, [p.id]: v }))} />
          </li>
        ))}
      </ul>
      <div className="mt-4 flex flex-col gap-3">
        <TextField label="Otro (cargo libre)" placeholder="Descripción" />
        <TextField label="Nota (opcional)" placeholder="Ej.: lo retiró su hijo" />
      </div>
    </Sheet>
  );
}

function EstadoSheet({
  open,
  onClose,
  balance,
  balanceVes,
  rows,
}: {
  open: boolean;
  onClose: () => void;
  balance: string;
  balanceVes: string | null | undefined;
  rows: StatementRow[];
}) {
  const toast = useToast();
  // En el panel real este texto lo arma la API (`statement?format=whatsapp`, 08 §Agregados).
  const text = [
    "*Panadería de ejemplo*",
    cliente.contactName,
    "",
    `*Debe ${fmtUsd(balance)}*${balanceVes ? ` (${fmtBs(balanceVes)} a tasa BCV del 21/10)` : ""}`,
    "",
    ...rows.slice(0, 5).map((r) => `${fmtDayMonth(r.at)}  ${r.description.slice(0, 36)}  ${fmtUsd(r.amount, { signed: true })}`),
    rows.length > 5 ? `… y ${rows.length - 5} más` : "",
  ]
    .filter((l, i, a) => l !== "" || a[i - 1] !== "")
    .join("\n");

  return (
    <Sheet
      open={open}
      onClose={onClose}
      title="Estado de cuenta"
      description="Texto listo para mandar por WhatsApp."
      footer={
        <div className="grid grid-cols-2 gap-3">
          <Button
            variant="secondary"
            icon={<Copy aria-hidden className="size-5" />}
            onClick={() => {
              void navigator.clipboard?.writeText(text).then(
                () => toast.show("Texto copiado"),
                () => toast.show("No se pudo copiar. Selecciona el texto y cópialo.", { tone: "error" }),
              );
            }}
          >
            Copiar texto
          </Button>
          <a
            href={cliente.phone ? whatsappLink(cliente.phone, text) : undefined}
            target="_blank"
            rel="noreferrer"
            className="inline-flex h-12 items-center justify-center gap-2 rounded-md bg-primary px-5 text-base font-bold text-on-primary hover:bg-primary-hover"
          >
            <MessageCircle aria-hidden className="size-5" />
            Enviar
          </a>
        </div>
      }
    >
      <pre className="whitespace-pre-wrap rounded-md bg-canvas-subtle p-4 font-sans text-sm leading-relaxed tnum text-ink">{text}</pre>
    </Sheet>
  );
}
