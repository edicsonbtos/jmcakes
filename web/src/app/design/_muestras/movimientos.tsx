import { ArrowDownLeft, BookOpen, RotateCcw, ShoppingBasket, SlidersHorizontal, Undo2 } from "lucide-react";
import { IconCircle, ListRow, StatusPill, type CircleTone } from "@/components/ui";
import { fmtRelativeDay, fmtTime, fmtUsd } from "@/lib/format";
import { sign } from "@/lib/money";
import { cn } from "@/lib/utils";
import type { StatementKind, StatementRow } from "./fixtures";

export const KIND_LABEL: Record<StatementKind, string> = {
  SALDO_ANTERIOR: "Saldo anterior",
  FIADO: "Fiado",
  ABONO: "Abono",
  ANULACION: "Anulación",
  REVERSO: "Reverso",
  AJUSTE: "Ajuste",
};

const KIND_ICON: Record<StatementKind, { icon: React.ReactNode; tone: CircleTone }> = {
  SALDO_ANTERIOR: { icon: <BookOpen />, tone: "neutral" },
  FIADO: { icon: <ShoppingBasket />, tone: "neutral" },
  ABONO: { icon: <ArrowDownLeft />, tone: "favor" },
  ANULACION: { icon: <Undo2 />, tone: "muted" },
  REVERSO: { icon: <RotateCcw />, tone: "debt" },
  AJUSTE: { icon: <SlidersHorizontal />, tone: "neutral" },
};

/** Agrupa por día de Caracas: "Hoy", "Ayer", "12 oct". Las filas ya vienen de lo más nuevo a lo más viejo. */
export function groupByDay(rows: StatementRow[], now: Date): { day: string; rows: StatementRow[] }[] {
  const groups: { day: string; rows: StatementRow[] }[] = [];
  for (const r of rows) {
    const day = fmtRelativeDay(r.at, now);
    const last = groups[groups.length - 1];
    if (last && last.day === day) last.rows.push(r);
    else groups.push({ day, rows: [r] });
  }
  return groups;
}

/**
 * Una fila del historial: ícono por tipo, concepto, "Fiado · 3:30 p. m. · Admin",
 * el efecto en el saldo (+ sube la deuda en rojo, − la baja en verde) y el saldo resultante.
 */
export function MovimientoRow({ row, onOpen }: { row: StatementRow; onOpen?: (row: StatementRow) => void }) {
  const up = sign(row.amount) > 0;
  const { icon, tone } = KIND_ICON[row.kind];
  return (
    <ListRow
      leading={<IconCircle tone={row.voided ? "muted" : tone}>{icon}</IconCircle>}
      title={row.description}
      struck={row.voided}
      subtitle={
        <>
          {KIND_LABEL[row.kind]} · {fmtTime(row.at)} · {row.actorName}
        </>
      }
      trailing={
        <>
          <span className={cn("text-base font-bold tnum", row.voided ? "text-ink-muted line-through" : up ? "text-debt" : "text-favor")}>
            {fmtUsd(row.amount, { signed: true })}
          </span>
          {row.voided ? (
            <StatusPill tone="neutral">Anulado</StatusPill>
          ) : (
            <span className="text-xs tnum text-ink-muted">Saldo {fmtUsd(row.balanceAfter)}</span>
          )}
        </>
      }
      onClick={onOpen ? () => onOpen(row) : undefined}
      chevron={false}
    />
  );
}
