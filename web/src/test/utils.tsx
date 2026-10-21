// Adaptado de OpenGravity: apps/web/src/test/utils.tsx
import { render as rtlRender } from "@testing-library/react";
import type { ReactElement } from "react";
import { vi } from "vitest";
import { ToastProvider } from "@/components/ui/Toast";
import { SignJWT } from "jose";

/** Render con los proveedores del panel (hoy, el de avisos). `rerender` los conserva. */
export function render(ui: ReactElement) {
  return rtlRender(ui, { wrapper: ToastProvider });
}

type MockValue = unknown | { status: number; detail?: string; code?: string; body?: unknown };

/**
 * Simula `fetch`. Las claves son fragmentos de URL; el valor es el JSON de respuesta o
 * `{status, detail, code}` para un error de FastAPI. Un error sin `detail` se rechaza al
 * declararlo: el test creería comprobar que el panel conserva el `detail` sin comprobar nada.
 * Un valor función recibe la llamada y devuelve la respuesta (para secuencias).
 */
export function mockFetch(routes: Record<string, MockValue | ((url: string, init?: RequestInit) => Response | Promise<Response>)>) {
  for (const [key, value] of Object.entries(routes)) {
    const v = value as { status?: number; detail?: unknown };
    if (v && typeof v === "object" && typeof v.status === "number" && v.status >= 400 && typeof v.detail !== "string") {
      throw new Error(`mockFetch: el error de "${key}" (status ${v.status}) no trae "detail".`);
    }
  }
  const fn = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
    const key = Object.keys(routes).find((k) => url.includes(k));
    if (!key) return new Response(JSON.stringify({ detail: `Sin mock para ${url}` }), { status: 404 });
    const value = routes[key];
    if (typeof value === "function") return value(url, init);
    const v = value as { status?: number; detail?: string; code?: string };
    if (v && typeof v === "object" && typeof v.status === "number" && v.status >= 400) {
      return new Response(JSON.stringify({ detail: v.detail, code: v.code }), {
        status: v.status,
        headers: { "Content-Type": "application/json" },
      });
    }
    return new Response(JSON.stringify(value), { status: 200, headers: { "Content-Type": "application/json" } });
  });
  vi.stubGlobal("fetch", fn);
  return fn;
}

export const TEST_SECRET = "dev-mock-secret-no-usar-en-prod";

/** JWT HS256 como los de la API (claims de 01 §Autenticación). */
export async function makeJwt(claims: { sub?: string; role?: string; cid?: string | null }, expiresInSeconds = 1800, secret = TEST_SECRET) {
  const now = Math.floor(Date.now() / 1000);
  return new SignJWT({ role: claims.role ?? "ADMIN", cid: claims.cid ?? null })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject(claims.sub ?? "u_admin")
    .setIssuedAt(now)
    .setExpirationTime(now + expiresInSeconds)
    .sign(new TextEncoder().encode(secret));
}
