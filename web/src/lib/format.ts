// Adaptado de OpenGravity: apps/web/src/lib/format.ts (solo el patrón de timeZone fijo)
import { abs, groupDecimal, sign, toScaled, fromScaled } from "./money";

/** Toda fecha y hora se muestra en la hora de Caracas, nunca en la del navegador. */
export const TIME_ZONE = "America/Caracas";
const LOCALE = "es-VE";
const MINUS = "−";

type MoneyOpts = { signed?: boolean; abs?: boolean };

function signPrefix(value: string, opts: MoneyOpts): string {
  if (opts.abs) return "";
  const s = sign(value);
  if (s < 0) return MINUS;
  if (s > 0 && opts.signed) return "+";
  return "";
}

/** "$1.234,50". `signed` agrega "+" a los positivos; `abs` quita el signo. */
export function fmtUsd(value: string, opts: MoneyOpts = {}): string {
  return `${signPrefix(value, opts)}$${groupDecimal(abs(value))}`;
}

/** "Bs 1.234,50". Los Bs siempre vienen calculados por la API (03 §0). */
export function fmtBs(value: string, opts: MoneyOpts = {}): string {
  return `${signPrefix(value, opts)}Bs ${groupDecimal(abs(value))}`;
}

/** Tasa con 2 a 4 decimales: "185,2045" → "Bs 185,2045"; "185.2000" → "Bs 185,20". */
export function fmtRate(value: string): string {
  const four = fromScaled(toScaled(value, 4), 4);
  const trimmed = four.replace(/0{1,2}$/, "");
  const decimals = trimmed.split(".")[1]?.length ?? 2;
  return `Bs ${groupDecimal(trimmed, Math.max(2, decimals))}`;
}

/** Cantidad con hasta 3 decimales y coma decimal: "2.500" → "2,5"; "12" → "12". */
export function fmtQty(value: string): string {
  const s = fromScaled(toScaled(value, 3), 3).replace(/\.?0+$/, "");
  return s.replace(".", ",");
}

function parts(iso: string | Date, options: Intl.DateTimeFormatOptions): string {
  const d = typeof iso === "string" ? new Date(iso) : iso;
  return new Intl.DateTimeFormat(LOCALE, { timeZone: TIME_ZONE, ...options })
    .format(d)
    .replace(/\.(?=\s|$|,)/g, "");
}

/** "13 oct 2026" */
export function fmtDate(iso: string | Date): string {
  return parts(iso, { day: "numeric", month: "short", year: "numeric" });
}

/** "13/10" (para el estado de cuenta y la tasa del día). */
export function fmtDayMonth(iso: string | Date): string {
  return parts(iso, { day: "2-digit", month: "2-digit" });
}

/** "3:30 p. m." */
export function fmtTime(iso: string | Date): string {
  return new Intl.DateTimeFormat(LOCALE, { timeZone: TIME_ZONE, hour: "numeric", minute: "2-digit" }).format(
    typeof iso === "string" ? new Date(iso) : iso,
  );
}

/** Día de Caracas como "aaaa-mm-dd". */
export function caracasDay(iso: string | Date): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: TIME_ZONE }).format(typeof iso === "string" ? new Date(iso) : iso);
}

/** "Hoy", "Ayer" o "13 oct" según el día de Caracas. */
export function fmtRelativeDay(iso: string | Date, now: Date = new Date()): string {
  const day = caracasDay(iso);
  if (day === caracasDay(now)) return "Hoy";
  const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  if (day === caracasDay(yesterday)) return "Ayer";
  const sameYear = day.slice(0, 4) === caracasDay(now).slice(0, 4);
  return sameYear ? parts(iso, { day: "numeric", month: "short" }) : fmtDate(iso);
}

/** "Hoy · 3:30 p. m." */
export function fmtDateTime(iso: string | Date, now: Date = new Date()): string {
  return `${fmtRelativeDay(iso, now)} · ${fmtTime(iso)}`;
}

/** Fecha grande para encabezados: "martes 13 de octubre". */
export function fmtDateBig(iso: string | Date): string {
  return parts(iso, { weekday: "long", day: "numeric", month: "long" }).replace(",", "");
}
