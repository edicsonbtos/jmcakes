// Adaptado de OpenGravity: apps/web/src/lib/api.ts (solo el `apiFetch` base)
/**
 * Cliente de la API para Server Components y Server Actions. Lee el access de la cookie
 * httpOnly (el proxy ya lo refrescó antes de renderizar) y nunca cachea vistas operativas.
 */
import { cookies } from "next/headers";
import { apiUrl } from "./env";
import { ApiError, NETWORK_ERROR_DETAIL, apiErrorFromResponse } from "./errors";
import { ACCESS_COOKIE } from "./session";
import { withQuery, type QueryValue } from "./query";

export type ServerFetchOptions = {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  query?: Record<string, QueryValue>;
  idempotencyKey?: string;
  /** false para endpoints públicos (P en 08). */
  auth?: boolean;
  /** Segundos de caché; solo para datos públicos que cambian poco (p. ej. `/settings/public`). */
  revalidate?: number;
  responseType?: "json" | "text";
  /** Corta la espera (p. ej. la barra no debe colgarse si la API tarda). */
  timeoutMs?: number;
};

export async function apiFetch<T = unknown>(path: string, opts: ServerFetchOptions = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (opts.auth !== false) {
    const token = (await cookies()).get(ACCESS_COOKIE)?.value;
    if (!token) throw new ApiError(401, "Tu sesión venció. Entra de nuevo.", "UNAUTHENTICATED");
    headers.Authorization = `Bearer ${token}`;
  }
  if (opts.body !== undefined) headers["Content-Type"] = "application/json";
  if (opts.idempotencyKey) headers["Idempotency-Key"] = opts.idempotencyKey;

  const cacheOpts: RequestInit & { next?: { revalidate: number } } =
    typeof opts.revalidate === "number" && opts.auth === false
      ? { next: { revalidate: opts.revalidate } }
      : { cache: "no-store" };

  let res: Response;
  try {
    res = await fetch(apiUrl(withQuery(path, opts.query)), {
      method: opts.method ?? (opts.body !== undefined ? "POST" : "GET"),
      headers,
      body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
      signal: opts.timeoutMs ? AbortSignal.timeout(opts.timeoutMs) : undefined,
      ...cacheOpts,
    });
  } catch {
    throw new ApiError(0, NETWORK_ERROR_DETAIL, "NETWORK_ERROR");
  }
  if (!res.ok) throw await apiErrorFromResponse(res);
  if (res.status === 204) return undefined as T;
  if (opts.responseType === "text") return (await res.text()) as T;
  return (await res.json()) as T;
}
