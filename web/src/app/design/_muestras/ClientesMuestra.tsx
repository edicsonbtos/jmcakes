"use client";

import { useMemo, useState } from "react";
import { Upload, UserPlus, Users } from "lucide-react";
import {
  Avatar,
  BALANCE_LABEL,
  Button,
  DataTable,
  EmptyState,
  FilterChips,
  ListRow,
  MoneyText,
  PageHeader,
  SearchField,
  StatusPill,
  balanceKind,
  useToast,
  type DataTableColumn,
} from "@/components/ui";
import { fmtBs, fmtUsd } from "@/lib/format";
import { sign } from "@/lib/money";
import { formatVePhone } from "@/lib/phone";
import { cn } from "@/lib/utils";
import { CLIENTES, POR_COBRAR, type MuestraCliente } from "./fixtures";

type Filtro = "todos" | "deuda" | "vencidos";

const FILTROS = [
  { value: "todos", label: "Todos" },
  { value: "deuda", label: "Con deuda" },
  { value: "vencidos", label: "Vencidos" },
] as const;

function subtitulo(c: MuestraCliente): string {
  const parts = [c.businessName && c.businessName !== c.contactName ? c.businessName : null, c.notes ? `“${c.notes}”` : null];
  return parts.filter(Boolean).join(" · ");
}

function Saldo({ c }: { c: MuestraCliente }) {
  const kind = balanceKind(c.balance);
  return (
    <span className="inline-flex flex-col items-end">
      <span className={cn("text-xs font-bold", kind === "debt" ? "text-debt" : kind === "favor" ? "text-favor" : "text-ink-muted")}>
        {BALANCE_LABEL[kind]}
      </span>
      <MoneyText
        usd={c.balance}
        ves={kind === "zero" ? undefined : c.balanceVes}
        abs
        size="md"
        tone={kind === "debt" ? "debt" : kind === "favor" ? "favor" : "muted"}
        align="end"
      />
    </span>
  );
}

/**
 * Muestra de la lista de clientes a 1440 px (09 §E1 — Agentes, DSN). En el panel real la
 * búsqueda, los filtros, el orden y el cursor los resuelve `GET /admin/customers`; aquí se
 * filtra la lista de ejemplo en memoria solo para que la muestra responda.
 */
export function ClientesMuestra() {
  const toast = useToast();
  const [q, setQ] = useState("");
  const [filtro, setFiltro] = useState<Filtro>("todos");

  const rows = useMemo(() => {
    const needle = q.trim().toLocaleLowerCase("es-VE").normalize("NFD").replace(/\p{M}/gu, "");
    const digits = q.replace(/\D/g, "");
    return CLIENTES.filter((c) => {
      if (filtro === "deuda" && sign(c.balance) <= 0) return false;
      if (filtro === "vencidos" && sign(c.overdueDebt) <= 0) return false;
      if (!needle) return true;
      const hay = [c.contactName, c.businessName, c.notes].join(" ").toLocaleLowerCase("es-VE").normalize("NFD").replace(/\p{M}/gu, "");
      const phoneHit = digits.length >= 3 && (c.phone ?? "").replace(/\D/g, "").replace(/^58/, "0").includes(digits);
      return hay.includes(needle) || phoneHit;
    });
  }, [q, filtro]);

  const columns: DataTableColumn<MuestraCliente>[] = [
    {
      key: "cliente",
      header: "Cliente",
      render: (c) => (
        <span className="flex items-center gap-3">
          <Avatar name={c.contactName} />
          <span className="flex min-w-0 flex-col">
            <span className="truncate font-semibold text-ink">{c.contactName}</span>
            {subtitulo(c) ? <span className="truncate text-sm text-ink-muted">{subtitulo(c)}</span> : null}
          </span>
        </span>
      ),
    },
    { key: "tipo", header: "Tipo", render: (c) => <StatusPill tone="neutral">{c.type === "WHOLESALE" ? "Mayor" : "Detal"}</StatusPill> },
    {
      key: "telefono",
      header: "Teléfono",
      hideBelowLg: true,
      render: (c) =>
        c.phone ? <span className="tnum text-ink-muted">{formatVePhone(c.phone)}</span> : <span className="text-ink-faint">Sin teléfono</span>,
    },
    {
      key: "vencido",
      header: "Vencido",
      render: (c) =>
        sign(c.overdueDebt) > 0 ? (
          <StatusPill tone="debt" dot>
            {fmtUsd(c.overdueDebt)}
          </StatusPill>
        ) : (
          <span className="text-ink-faint">—</span>
        ),
    },
    { key: "saldo", header: "Saldo", align: "end", render: (c) => <Saldo c={c} /> },
  ];

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Clientes"
        description="Ordenados por mayor deuda."
        actions={
          <>
            <Button variant="secondary" icon={<Upload aria-hidden className="size-5" />}>
              Importar
            </Button>
            <Button icon={<UserPlus aria-hidden className="size-5" />}>Nuevo cliente</Button>
          </>
        }
      />

      <div className="flex flex-wrap items-end justify-between gap-x-10 gap-y-2 border-b border-line pb-6">
        <div>
          <p className="text-base font-bold text-ink-muted">Por cobrar</p>
          <p className="mt-1 text-amount amount text-ink">{fmtUsd(POR_COBRAR.total)}</p>
          <p className="mt-2 text-lg tnum text-ink-muted">{fmtBs(POR_COBRAR.totalVes)}</p>
        </div>
        <dl className="flex gap-8 pb-1 text-base tnum">
          <div>
            <dt className="text-ink-muted">Detal</dt>
            <dd className="font-bold text-ink">{fmtUsd(POR_COBRAR.retail)}</dd>
          </div>
          <div>
            <dt className="text-ink-muted">Mayor</dt>
            <dd className="font-bold text-ink">{fmtUsd(POR_COBRAR.wholesale)}</dd>
          </div>
        </dl>
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <SearchField
          label="Buscar cliente"
          placeholder="Nombre, negocio, teléfono, cédula o apodo"
          value={q}
          onValueChange={setQ}
          className="lg:max-w-xl"
        />
        <FilterChips label="Filtrar clientes" options={FILTROS} value={filtro} onChange={setFiltro} className="lg:ml-auto" />
      </div>

      <DataTable
        caption="Clientes con su saldo"
        columns={columns}
        rows={rows}
        rowKey={(c) => c.id}
        rowHref={() => "/design/ficha"}
        mobileRender={(c) => (
          <ListRow
            href="/design/ficha"
            leading={<Avatar name={c.contactName} />}
            title={c.contactName}
            subtitle={
              sign(c.overdueDebt) > 0 ? (
                <span className="text-debt">Vencido {fmtUsd(c.overdueDebt)}</span>
              ) : (
                subtitulo(c) || (c.type === "WHOLESALE" ? "Mayor" : "Detal")
              )
            }
            trailing={<Saldo c={c} />}
            chevron={false}
          />
        )}
        nextCursor={rows.length > 0 ? "muestra" : null}
        onLoadMore={() => toast.show("En la muestra no hay más clientes")}
        empty={
          <EmptyState
            icon={<Users />}
            title="Nadie con ese filtro"
            description="Prueba con otra búsqueda o quita el filtro para ver a todos."
            action={
              <Button
                variant="secondary"
                onClick={() => {
                  setQ("");
                  setFiltro("todos");
                }}
              >
                Ver todos
              </Button>
            }
          />
        }
      />
    </div>
  );
}
