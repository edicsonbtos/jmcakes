import { apiFetch } from "./api";
import type { components } from "./api-types";
import { fmtDayMonth, fmtRate } from "./format";

/**
 * `Rate{date, value, rateType, isFallback}` de 08 §Convenciones.
 */
export type Rate = components["schemas"]["RateOut"];

/** `GET /rates/today` (público). `null` si la API responde `409 RATE_UNAVAILABLE` o no responde. */
export async function getTodayRate(): Promise<Rate | null> {
  try {
    return await apiFetch<Rate>("/rates/today", { auth: false, revalidate: 60, timeoutMs: 3000 });
  } catch {
    return null;
  }
}

/** Rótulo para la barra: "Tasa BCV de hoy · Bs 185,20" (o la última conocida, con su fecha). */
export function rateSummary(rate: Rate | null): { label: string; value: string } | null {
  if (!rate) return null;
  // `date` es un día "aaaa-mm-dd": se ancla al mediodía UTC para que Caracas muestre ese mismo día.
  const day = fmtDayMonth(`${rate.date.slice(0, 10)}T12:00:00Z`);
  const kind = rate.rateType === "MANUAL" ? "Tasa manual" : "Tasa BCV";
  return {
    label: rate.isFallback ? `${kind} del ${day}` : `${kind} de hoy`,
    value: fmtRate(rate.value),
  };
}
