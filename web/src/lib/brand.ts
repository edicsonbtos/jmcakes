/**
 * Marca del negocio sin depender del servidor (lo usan componentes de cliente).
 * El nombre siempre viene de `GET /settings/public` (`business.name`).
 * TODO(contrato): reemplazar `PublicSettings` por el tipo de `api-types.ts` cuando el orquestador lo genere en G1.
 */
export type PublicSettings = {
  businessName: string | null;
  phone?: string | null;
  whatsapp?: string | null;
  address?: string | null;
};

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
