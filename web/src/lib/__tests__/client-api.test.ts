import { beforeEach, describe, expect, it, vi } from "vitest";
import { mockFetch } from "@/test/utils";
import { __setRedirectToLogin, clearClientToken, clientFetch } from "../client-api";
import { isApiError } from "../errors";

const FUTURE = Math.floor(Date.now() / 1000) + 1800;

let redirected = 0;
beforeEach(() => {
  clearClientToken();
  redirected = 0;
  __setRedirectToLogin(() => {
    redirected += 1;
  });
});

describe("clientFetch", () => {
  it("pide el token al mismo origen y llama a la API con Bearer e Idempotency-Key", async () => {
    const spy = mockFetch({
      "/api/auth/token": { accessToken: "tok-1", expiresAt: FUTURE },
      "/admin/customers/c1/manual-payment": { id: "p1" },
    });
    const out = await clientFetch<{ id: string }>("/admin/customers/c1/manual-payment", {
      body: { amountLocal: "3704.00" },
      idempotencyKey: "llave-1",
    });
    expect(out).toEqual({ id: "p1" });
    const [url, init] = spy.mock.calls[1];
    expect(String(url)).toBe("http://api.test/api/v1/admin/customers/c1/manual-payment");
    const headers = init?.headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer tok-1");
    expect(headers["Idempotency-Key"]).toBe("llave-1");
    expect(init?.method).toBe("POST");
  });

  it("reusa el token mientras le quede vida", async () => {
    const spy = mockFetch({ "/api/auth/token": { accessToken: "tok-1", expiresAt: FUTURE }, "/rates/today": { value: "185.20" } });
    await clientFetch("/rates/today");
    await clientFetch("/rates/today");
    expect(spy.mock.calls.filter(([u]) => String(u).includes("/api/auth/token"))).toHaveLength(1);
  });

  it("conserva detail y code del error de la API", async () => {
    mockFetch({
      "/api/auth/token": { accessToken: "tok-1", expiresAt: FUTURE },
      "/manual-payment": { status: 409, detail: "Esa referencia ya fue registrada en esta cuenta.", code: "DUPLICATE_REFERENCE" },
    });
    const err = await clientFetch("/admin/customers/c1/manual-payment", { body: {} }).catch((e) => e);
    expect(isApiError(err)).toBe(true);
    expect(err).toMatchObject({ status: 409, detail: "Esa referencia ya fue registrada en esta cuenta.", code: "DUPLICATE_REFERENCE" });
  });

  it("ante un 401 refresca una vez y reintenta con el token nuevo", async () => {
    let tokenCalls = 0;
    let apiCalls = 0;
    const spy = mockFetch({
      "/api/auth/token": () => {
        tokenCalls += 1;
        return Response.json({ accessToken: `tok-${tokenCalls}`, expiresAt: FUTURE });
      },
      "/api/auth/refresh": { ok: true },
      "/admin/customers": (_u: string, init?: RequestInit) => {
        apiCalls += 1;
        const auth = (init?.headers as Record<string, string>).Authorization;
        return auth === "Bearer tok-2"
          ? Response.json({ items: [], nextCursor: null })
          : Response.json({ detail: "Tu sesión venció.", code: "UNAUTHENTICATED" }, { status: 401 });
      },
    });
    const out = await clientFetch("/admin/customers");
    expect(out).toEqual({ items: [], nextCursor: null });
    expect(apiCalls).toBe(2);
    expect(spy.mock.calls.some(([u, i]) => String(u).includes("/api/auth/refresh") && i?.method === "POST")).toBe(true);
    expect(redirected).toBe(0);
  });

  it("si el refresh falla, manda a /login", async () => {
    mockFetch({
      "/api/auth/token": { accessToken: "tok-1", expiresAt: FUTURE },
      "/api/auth/refresh": { status: 401, detail: "Tu sesión venció. Entra de nuevo." },
      "/admin/customers": { status: 401, detail: "Tu sesión venció." },
    });
    const err = await clientFetch("/admin/customers").catch((e) => e);
    expect(err).toMatchObject({ status: 401, code: "UNAUTHENTICATED" });
    expect(redirected).toBe(1);
  });

  it("sin red da un error en español", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (u: string) => {
        if (String(u).includes("/api/auth/token")) return Response.json({ accessToken: "t", expiresAt: FUTURE });
        throw new TypeError("Failed to fetch");
      }),
    );
    const err = await clientFetch("/admin/customers").catch((e) => e);
    expect(err).toMatchObject({ status: 0, code: "NETWORK_ERROR", detail: "Sin conexión con el servidor. Revisa tu señal e intenta de nuevo." });
  });

  it("envía FormData sin Content-Type y lee texto si se pide", async () => {
    const spy = mockFetch({
      "/api/auth/token": { accessToken: "t", expiresAt: FUTURE },
      "/import/preview": { previewToken: "x" },
      "/statement": () => new Response("*Debe $5,00*", { status: 200 }),
    });
    const fd = new FormData();
    fd.set("file", new Blob(["nombre\nAna"]), "deudores.csv");
    await clientFetch("/admin/customers/import/preview", { body: fd, idempotencyKey: "k" });
    const headers = spy.mock.calls[1][1]?.headers as Record<string, string>;
    expect(headers["Content-Type"]).toBeUndefined();
    const text = await clientFetch<string>("/admin/customers/c1/statement", { query: { format: "whatsapp" }, responseType: "text" });
    expect(text).toBe("*Debe $5,00*");
  });
});
