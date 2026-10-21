import { describe, expect, it } from "vitest";
import { ApiError, apiErrorFromBody, apiErrorFromResponse, isApiError } from "../errors";
import { decideAccess, requiredRoles, safeNext } from "../auth-guard";
import { businessInitial, displayBusinessName } from "../brand";
import { withQuery } from "../query";
import { rateSummary } from "../rates";

describe("errores de la API", () => {
  it("conserva detail, code y meta tal cual", async () => {
    const res = new Response(JSON.stringify({ detail: "Esa referencia ya fue registrada.", code: "DUPLICATE_REFERENCE", meta: { line: 3 } }), {
      status: 409,
    });
    const e = await apiErrorFromResponse(res);
    expect(isApiError(e)).toBe(true);
    expect(e).toMatchObject({ status: 409, detail: "Esa referencia ya fue registrada.", code: "DUPLICATE_REFERENCE", meta: { line: 3 } });
  });

  it("lee los 422 de validación con detail en lista y cuerpos vacíos", () => {
    expect(apiErrorFromBody(422, { detail: [{ msg: "El monto debe ser mayor que cero" }] }).detail).toBe(
      "Revisa los datos: El monto debe ser mayor que cero",
    );
    expect(apiErrorFromBody(401, null).code).toBe("UNAUTHENTICATED");
    expect(apiErrorFromBody(503, null).detail).toBe("Servicio no disponible. Intenta de nuevo.");
    expect(new ApiError(500, "x") instanceof Error).toBe(true);
  });
});

describe("auth-guard", () => {
  const admin = { sub: "u1", role: "ADMIN" as const, exp: 9_999_999_999 };
  const base = { pathname: "/admin/clientes", target: "/admin/clientes?x=1", hasRefreshToken: false, mustChangePassword: false as boolean | null };

  it("solo protege /admin y /cambiar-contrasena", () => {
    expect(requiredRoles("/admin")).toEqual(["ADMIN"]);
    expect(requiredRoles("/admin/clientes/c1")).toEqual(["ADMIN"]);
    expect(requiredRoles("/administrador")).toBeNull();
    expect(requiredRoles("/login")).toBeNull();
    expect(decideAccess({ ...base, pathname: "/login", claims: null })).toEqual({ type: "next" });
  });

  it("sin access: refresh si hay refreshToken, si no /login con la página", () => {
    expect(decideAccess({ ...base, claims: null, hasRefreshToken: true })).toEqual({ type: "refresh", next: "/admin/clientes?x=1" });
    expect(decideAccess({ ...base, claims: null })).toEqual({ type: "login", next: "/admin/clientes?x=1" });
  });

  it("rechaza otros roles", () => {
    expect(decideAccess({ ...base, claims: { ...admin, role: "CUSTOMER" } })).toEqual({ type: "forbidden" });
    expect(decideAccess({ ...base, claims: { ...admin, role: "PRODUCTION" } })).toEqual({ type: "forbidden" });
  });

  it("mustChangePassword obliga a /cambiar-contrasena y deja entrar allí", () => {
    expect(decideAccess({ ...base, claims: admin, mustChangePassword: true })).toEqual({ type: "change-password" });
    expect(decideAccess({ ...base, pathname: "/cambiar-contrasena", claims: admin, mustChangePassword: true })).toEqual({ type: "next" });
    expect(decideAccess({ ...base, claims: admin, mustChangePassword: null })).toEqual({ type: "check-me" });
    expect(decideAccess({ ...base, claims: admin })).toEqual({ type: "next" });
  });

  it("safeNext evita redirecciones abiertas y bucles", () => {
    expect(safeNext("/admin/clientes?f=1")).toBe("/admin/clientes?f=1");
    expect(safeNext("https://evil.example")).toBe("/admin");
    expect(safeNext("//evil.example")).toBe("/admin");
    expect(safeNext("/\\evil.example")).toBe("/admin");
    expect(safeNext("/api/auth/token")).toBe("/admin");
    expect(safeNext("/login?next=/admin")).toBe("/admin");
    expect(safeNext("/admin\n")).toBe("/admin");
    expect(safeNext(null)).toBe("/admin");
  });
});

describe("marca, consultas y tasa", () => {
  it("el nombre sale de la configuración; sin API, un rótulo neutro", () => {
    expect(displayBusinessName({ businessName: "  La Canilla  " })).toBe("La Canilla");
    expect(displayBusinessName(null)).toBe("Panel");
    expect(businessInitial("él horno")).toBe("É");
    expect(businessInitial("  ")).toBe("·");
  });

  it("withQuery omite vacíos", () => {
    expect(withQuery("/admin/customers", { query: "0414", hasDebt: true, cursor: null, sort: "" })).toBe(
      "/admin/customers?query=0414&hasDebt=true",
    );
    expect(withQuery("/x?a=1", { b: 2 })).toBe("/x?a=1&b=2");
  });

  it("rateSummary dice de qué día es la tasa", () => {
    expect(rateSummary({ date: "2026-10-21", value: "185.2000", rateType: "BCV", isFallback: false })).toEqual({
      label: "Tasa BCV de hoy",
      value: "Bs 185,20",
    });
    expect(rateSummary({ date: "2026-10-20", value: "184.1", rateType: "BCV", isFallback: true })?.label).toBe("Tasa BCV del 20/10");
    expect(rateSummary({ date: "2026-10-21", value: "190", rateType: "MANUAL", isFallback: false })?.label).toBe("Tasa manual de hoy");
    expect(rateSummary(null)).toBeNull();
  });
});
