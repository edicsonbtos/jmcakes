/**
 * Base de la API, con el prefijo `/api/v1` incluido (01 §Variables).
 * `NEXT_PUBLIC_API_URL` se incrusta en el build: la usan el servidor y el navegador.
 */
export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:4010/api/v1").replace(/\/+$/, "");

export function apiUrl(path: string): string {
  return `${API_URL}${path.startsWith("/") ? path : `/${path}`}`;
}
