// Adaptado de OpenGravity: apps/web/src/lib/client-api.ts
/**
 * Cliente de la API para componentes de cliente ("use client").
 * - Pide un access fresco a `/api/auth/token` (mismo origen) y llama con Bearer.
 * - Ante un 401, refresca una vez (`POST /api/auth/refresh`) y reintenta; si vuelve a
 *   fallar, manda a `/login`.
 * - Conserva `detail`, `code` y `meta` del error (`ApiError`), para mostrarlos tal cual.
 * - El `Idempotency-Key` lo pone quien llama y se reutiliza en sus reintentos.
 */
import { apiUrl } from "./env";
import { ApiError, NETWORK_ERROR_DETAIL, apiErrorFromResponse } from "./errors";
import { withQuery, type QueryValue } from "./query";

export { withQuery, type QueryValue };

type Cached = { token: string; expiresAt: number };
let cached: Cached | null = null;
let pending: Promise<string | null> | null = null;

/** Margen para no usar un token que vence durante la petición. */
const SKEW_SECONDS = 30;

function nowSeconds(): number {
  return Math.floor(Date.now() / 1000);
}

export function clearClientToken(): void {
  cached = null;
  pending = null;
}

async function fetchToken(): Promise<string | null> {
  let res: Response;
  try {
    res = await fetch("/api/auth/token", { credentials: "same-origin", cache: "no-store" });
  } catch {
    throw new ApiError(0, NETWORK_ERROR_DETAIL, "NETWORK_ERROR");
  }
  if (res.status === 401) return null;
  if (!res.ok) throw await apiErrorFromResponse(res);
  const data = (await res.json()) as { accessToken?: unknown; expiresAt?: unknown };
  if (typeof data.accessToken !== "string") return null;
  cached = { token: data.accessToken, expiresAt: typeof data.expiresAt === "number" ? data.expiresAt : nowSeconds() + 60 };
  return cached.token;
}

/** Token en memoria mientras le quede vida; si no, uno nuevo (una sola petición a la vez). */
export async function getClientToken(force = false): Promise<string | null> {
  if (!force && cached && cached.expiresAt - SKEW_SECONDS > nowSeconds()) return cached.token;
  if (!pending) pending = fetchToken().finally(() => (pending = null));
  return pending;
}

async function refreshViaWeb(): Promise<boolean> {
  try {
    const res = await fetch("/api/auth/refresh", { method: "POST", credentials: "same-origin", cache: "no-store" });
    return res.ok;
  } catch {
    throw new ApiError(0, NETWORK_ERROR_DETAIL, "NETWORK_ERROR");
  }
}

/** Navega a /login conservando la página actual. Reemplazable en pruebas. */
export let redirectToLogin = (): void => {
  if (typeof window === "undefined") return;
  const next = `${window.location.pathname}${window.location.search}`;
  window.location.assign(`/login?next=${encodeURIComponent(next)}`);
};

export function __setRedirectToLogin(fn: () => void): void {
  redirectToLogin = fn;
}

const SESSION_EXPIRED = "Tu sesión venció. Entra de nuevo.";

export type ClientFetchOptions = {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  /** Objeto (se envía como JSON) o FormData (multipart, p. ej. la importación por CSV). */
  body?: unknown;
  query?: Record<string, QueryValue>;
  idempotencyKey?: string;
  signal?: AbortSignal;
  /** `text` para `statement?format=whatsapp|csv`. */
  responseType?: "json" | "text";
};

async function send(path: string, opts: ClientFetchOptions, token: string): Promise<Response> {
  const headers: Record<string, string> = { Authorization: `Bearer ${token}`, Accept: "application/json" };
  let body: BodyInit | undefined;
  if (opts.body instanceof FormData) {
    body = opts.body;
  } else if (opts.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.body);
  }
  if (opts.idempotencyKey) headers["Idempotency-Key"] = opts.idempotencyKey;
  try {
    return await fetch(apiUrl(withQuery(path, opts.query)), {
      method: opts.method ?? (body ? "POST" : "GET"),
      headers,
      body,
      cache: "no-store",
      signal: opts.signal,
    });
  } catch (e) {
    if ((e as { name?: string })?.name === "AbortError") throw e;
    throw new ApiError(0, NETWORK_ERROR_DETAIL, "NETWORK_ERROR");
  }
}

export async function clientFetch<T = unknown>(path: string, opts: ClientFetchOptions = {}): Promise<T> {
  let token = await getClientToken();
  if (!token) {
    redirectToLogin();
    throw new ApiError(401, SESSION_EXPIRED, "UNAUTHENTICATED");
  }

  let res = await send(path, opts, token);
  if (res.status === 401) {
    clearClientToken();
    const refreshed = await refreshViaWeb();
    token = refreshed ? await getClientToken(true) : null;
    if (!token) {
      redirectToLogin();
      throw new ApiError(401, SESSION_EXPIRED, "UNAUTHENTICATED");
    }
    res = await send(path, opts, token);
    if (res.status === 401) {
      clearClientToken();
      redirectToLogin();
      throw await apiErrorFromResponse(res);
    }
  }

  if (!res.ok) throw await apiErrorFromResponse(res);
  if (res.status === 204) return undefined as T;
  if (opts.responseType === "text") return (await res.text()) as T;
  return (await res.json()) as T;
}

/** Página de una lista con cursor (08: `{items, nextCursor}`). */
export type Page<T> = { items: T[]; nextCursor: string | null };
