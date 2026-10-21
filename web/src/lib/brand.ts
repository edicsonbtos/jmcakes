/**
 * Marca del negocio sin depender del servidor (lo usan componentes de cliente).
 * El nombre siempre viene de `GET /settings/public` (`business.name`).
 */
import type { components } from "./api-types";

export type PublicSettings = components["schemas"]["PublicSettings"];

/** Nombre a mostrar; si la API no responde, un rótulo neutro (no un nombre inventado). */
export function displayBusinessName(s: Pick<PublicSettings, "businessName"> | null): string {
  const name = s?.businessName?.trim();
  return name ? name : "Panel";
}

/** Inicial para la marca circular cuando no hay logo (el logo llega con el dueño). */
export function businessInitial(name: string): string {
  const letter = name.trim().match(/\p{L}|\p{N}/u)?.[0];
  return letter ? letter.toLocaleUpperCase("es-VE") : "·";
}
