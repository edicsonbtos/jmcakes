/**
 * Sesión web con refresh (01 §Autenticación). Solo se usa en el servidor: Server Actions,
 * Route Handlers de `/api/auth/*` y `src/proxy.ts`. Los tokens viven en cookies httpOnly
 * y ninguna ruta los recibe desde el navegador.
 */
import { apiUrl } from "./env";
import { apiErrorFromResponse, ApiError, NETWORK_ERROR_DETAIL } from "./errors";
import { readExp } from "./jwt";

export const ACCESS_COOKIE = "authToken";
export const REFRESH_COOKIE = "refreshToken";
/** "1" si `/auth/me` trae `mustChangePassword = true`; "0" si no. Es solo para la UX: la API lo exige igual. */
export const MUST_CHANGE_COOKIE = "mustChangePassword";

/** El refresh rota cada vez; dura 30 días (01 §Autenticación). */
export const REFRESH_MAX_AGE_SECONDS = 30 * 24 * 60 * 60;
const ACCESS_FALLBACK_SECONDS = 30 * 60;

export type TokenPair = {
  accessToken: string;
  refreshToken: string;
  /** Segundos de vida del access. Si la API no lo manda, se toma de `exp`. */
  expiresIn?: number | null;
};

export type CookieOptions = {
  httpOnly: boolean;
  secure: boolean;
  sameSite: "lax";
  path: string;
  maxAge: number;
};

/** Lo mínimo que comparten `cookies()` de next/headers y `NextResponse.cookies`. */
export type CookieWriter = {
  set(name: string, value: string, options: CookieOptions): unknown;
};

function baseOptions(maxAge: number): CookieOptions {
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge,
  };
}

export function accessMaxAge(pair: TokenPair, nowMs: number = Date.now()): number {
  if (typeof pair.expiresIn === "number" && pair.expiresIn > 0) return Math.floor(pair.expiresIn);
  const exp = readExp(pair.accessToken);
  if (exp) return Math.max(0, exp - Math.floor(nowMs / 1000));
  return ACCESS_FALLBACK_SECONDS;
}

/** Guarda el par en cookies httpOnly. `mustChangePassword` solo se escribe si se conoce. */
export function writeSession(store: CookieWriter, pair: TokenPair, mustChangePassword?: boolean | null): void {
  store.set(ACCESS_COOKIE, pair.accessToken, baseOptions(accessMaxAge(pair)));
  store.set(REFRESH_COOKIE, pair.refreshToken, baseOptions(REFRESH_MAX_AGE_SECONDS));
  if (typeof mustChangePassword === "boolean") writeMustChange(store, mustChangePassword);
}

export function writeMustChange(store: CookieWriter, value: boolean): void {
  store.set(MUST_CHANGE_COOKIE, value ? "1" : "0", baseOptions(REFRESH_MAX_AGE_SECONDS));
}

export function clearSession(store: CookieWriter): void {
  for (const name of [ACCESS_COOKIE, REFRESH_COOKIE, MUST_CHANGE_COOKIE]) {
    store.set(name, "", baseOptions(0));
  }
}

export function readMustChange(value: string | undefined): boolean | null {
  if (value === "1") return true;
  if (value === "0") return false;
  return null;
}

function isTokenPair(v: unknown): v is TokenPair {
  const o = v as Record<string, unknown> | null;
  return !!o && typeof o.accessToken === "string" && typeof o.refreshToken === "string";
}

async function postJson(path: string, body: unknown, accessToken?: string): Promise<Response> {
  try {
    return await fetch(apiUrl(path), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });
  } catch {
    throw new ApiError(0, NETWORK_ERROR_DETAIL, "NETWORK_ERROR");
  }
}

export type LoginResult = TokenPair & { user?: { mustChangePassword?: boolean } | null };

/** `POST /auth/login {phone, password}`. Lanza `ApiError` con el `detail` de la API. */
export async function apiLogin(phone: string, password: string): Promise<LoginResult> {
  const res = await postJson("/auth/login", { phone, password });
  if (!res.ok) throw await apiErrorFromResponse(res);
  const data: unknown = await res.json();
  if (!isTokenPair(data)) throw new ApiError(502, "La respuesta del servidor no es válida. Intenta de nuevo.", "BAD_RESPONSE");
  return data as LoginResult;
}

/** `GET /auth/me`. Devuelve `null` si el access ya no sirve (401). */
export async function apiMe(accessToken: string): Promise<{ user: { mustChangePassword?: boolean; role?: string } } | null> {
  let res: Response;
  try {
    res = await fetch(apiUrl("/auth/me"), {
      headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(0, NETWORK_ERROR_DETAIL, "NETWORK_ERROR");
  }
  if (res.status === 401) return null;
  if (!res.ok) throw await apiErrorFromResponse(res);
  return (await res.json()) as { user: { mustChangePassword?: boolean } };
}

/**
 * Refresh serializado por token: dos pestañas que vencen a la vez comparten la misma
 * llamada (01: "la ruta web serializa las llamadas por cookie"). La API además da
 * 60 s de gracia al token rotado. Hay una sola réplica de web, así que basta la memoria.
 */
const inflight = new Map<string, Promise<TokenPair | null>>();

export function refreshSession(refreshToken: string): Promise<TokenPair | null> {
  const current = inflight.get(refreshToken);
  if (current) return current;
  const p = (async () => {
    const res = await postJson("/auth/refresh", { refreshToken });
    if (res.status === 401 || res.status === 403) return null;
    if (!res.ok) throw await apiErrorFromResponse(res);
    const data: unknown = await res.json();
    return isTokenPair(data) ? data : null;
  })().finally(() => {
    // Se deja un instante para que las peticiones que ya leyeron la cookie vieja se unan.
    setTimeout(() => inflight.delete(refreshToken), 5_000);
  });
  inflight.set(refreshToken, p);
  return p;
}

/** Solo para pruebas. */
export function __resetRefreshInflight(): void {
  inflight.clear();
}

/** `POST /auth/logout`. Nunca falla: cerrar sesión en la web no depende de la API. */
export async function apiLogout(accessToken: string | undefined, refreshToken: string | undefined): Promise<void> {
  if (!accessToken && !refreshToken) return;
  try {
    await postJson("/auth/logout", { refreshToken: refreshToken ?? null }, accessToken);
  } catch {
    /* sin red: igual se borran las cookies */
  }
}

/**
 * Las rutas `/api/auth/*` solo aceptan llamadas del mismo origen (01: "solo mismo origen").
 * `Sec-Fetch-Site` lo mandan todos los navegadores actuales; si falta, se compara `Origin`.
 */
export function isSameOrigin(headers: Headers, requestUrl: string): boolean {
  const site = headers.get("sec-fetch-site");
  if (site) return site === "same-origin";
  const origin = headers.get("origin");
  if (!origin) return true; // navegación GET sin Origin (misma pestaña)
  try {
    const expected = forwardedOrigin(headers) ?? new URL(requestUrl).origin;
    return origin === expected;
  } catch {
    return false;
  }
}

/** Detrás del edge de Railway, el host público viene en `x-forwarded-host`. */
function forwardedOrigin(headers: Headers): string | null {
  const host = headers.get("x-forwarded-host");
  if (!host) return null;
  const proto = headers.get("x-forwarded-proto") ?? "https";
  return `${proto}://${host}`;
}

/** URL absoluta para redirigir, respetando el host público detrás del proxy de Railway. */
export function publicUrl(path: string, headers: Headers, requestUrl: string): URL {
  return new URL(path, forwardedOrigin(headers) ?? requestUrl);
}
