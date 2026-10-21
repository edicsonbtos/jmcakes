"use client";

import { useState, type ReactNode } from "react";
import { fmtBs, fmtUsd } from "@/lib/format";
import { sign } from "@/lib/money";
import { cn } from "@/lib/utils";

export type MoneySize = "sm" | "md" | "lg" | "xl" | "hero";
export type MoneyTone = "ink" | "muted" | "debt" | "favor";

const USD_SIZE: Record<MoneySize, string> = {
  sm: "text-sm font-bold",
  md: "text-base font-bold",
  lg: "text-xl amount",
  xl: "text-3xl amount",
  hero: "text-amount amount",
};
const VES_SIZE: Record<MoneySize, string> = {
  sm: "text-xs",
  md: "text-sm",
  lg: "text-sm",
  xl: "text-base",
  hero: "text-lg",
};
const TONE: Record<MoneyTone, string> = {
  ink: "text-ink",
  muted: "text-ink-muted",
  debt: "text-debt",
  favor: "text-favor",
};

/**
 * Monto en USD con los Bs **de la API** debajo (03 §0: la web no convierte).
 * - `ves` ausente (`undefined`): no se muestra la línea de Bs.
 * - `ves === null`: la API no tenía tasa → "Bs —" con su explicación.
 */
export function MoneyText({
  usd,
  ves,
  size = "md",
  tone = "ink",
  signed = false,
  abs = false,
  align = "start",
  className,
}: {
  usd: string;
  ves?: string | null;
  size?: MoneySize;
  tone?: MoneyTone;
  /** "+$12,00" para cargos y "−$10,00" para abonos. */
  signed?: boolean;
  /** Sin signo (el rótulo "Debe"/"A favor" ya lo dice). */
  abs?: boolean;
  align?: "start" | "end";
  className?: string;
}) {
  return (
    <span className={cn("inline-flex flex-col", align === "end" ? "items-end text-right" : "items-start", className)}>
      <span className={cn("tnum leading-none", USD_SIZE[size], TONE[tone])}>{fmtUsd(usd, { signed, abs })}</span>
      {ves !== undefined ? (
        <span className={cn("mt-1 tnum text-ink-muted", VES_SIZE[size])} title={ves === null ? "Sin tasa del día" : undefined}>
          {ves === null ? "Bs —" : fmtBs(ves, { abs })}
        </span>
      ) : null}
    </span>
  );
}

export type BalanceKind = "debt" | "favor" | "zero";

/** Saldo del cliente: positivo = debe, negativo = a favor (09 §E1 — Reglas). */
export function balanceKind(balance: string): BalanceKind {
  const s = sign(balance);
  return s > 0 ? "debt" : s < 0 ? "favor" : "zero";
}

export const BALANCE_LABEL: Record<BalanceKind, string> = { debt: "Debe", favor: "A favor", zero: "Al día" };

/**
 * Saldo grande de la ficha: rótulo "Debe" / "A favor" / "Al día", el monto a 48 px y los Bs
 * debajo. Cuando el saldo cambia (tras fiar o abonar), el monto entra con un fundido y
 * desenfoque cortos: el dueño ve que el número cambió sin buscarlo.
 */
export function BalanceFigure({
  balance,
  balanceVes,
  children,
  size = "hero",
  className,
}: {
  balance: string;
  balanceVes?: string | null;
  /** Lo que va junto a los Bs (p. ej. el chip "Vencido $X"). */
  children?: ReactNode;
  size?: "hero" | "xl";
  className?: string;
}) {
  const kind = balanceKind(balance);
  // Patrón de "información del render anterior": solo anima cuando el valor cambia.
  const [prev, setPrev] = useState(balance);
  const [changed, setChanged] = useState(false);
  if (prev !== balance) {
    setPrev(balance);
    setChanged(true);
  }
  const tone = kind === "debt" ? "text-debt" : kind === "favor" ? "text-favor" : "text-ink";
  return (
    <div className={cn("flex flex-col", className)} aria-live="polite" aria-atomic="true">
      <span className={cn("text-base font-bold", tone)}>{BALANCE_LABEL[kind]}</span>
      <span
        key={balance}
        className={cn(
          "tnum leading-none",
          size === "hero" ? "mt-1 text-amount amount" : "mt-0.5 text-3xl amount",
          tone,
          changed && "animate-amount-in",
        )}
      >
        {fmtUsd(balance, { abs: true })}
      </span>
      {balanceVes !== undefined || children ? (
        <span className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1.5">
          {balanceVes !== undefined ? (
            <span className="text-lg tnum text-ink-muted" title={balanceVes === null ? "Sin tasa del día" : undefined}>
              {balanceVes === null ? "Bs —" : fmtBs(balanceVes, { abs: true })}
            </span>
          ) : null}
          {children}
        </span>
      ) : null}
    </div>
  );
}
