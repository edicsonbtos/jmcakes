import { apiFetch } from "./api";
import type { PublicSettings } from "./brand";

export { displayBusinessName, businessInitial, type PublicSettings } from "./brand";

/**
 * `GET /settings/public` (08 §B1). El nombre del negocio siempre sale de aquí
 * (`business.name`): ninguna pantalla lo tiene fijo en el código (PRODUCT.md §Brand Commitments).
 * Se cachea 60 s: el nombre casi nunca cambia y la barra lo pide en cada página.
 */
export async function getPublicSettings(): Promise<PublicSettings | null> {
  try {
    const s = await apiFetch<PublicSettings>("/settings/public", { auth: false, revalidate: 60, timeoutMs: 3000 });
    return s && typeof s === "object" ? s : null;
  } catch {
    return null;
  }
}
