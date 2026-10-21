// @vitest-environment node
import { beforeEach, describe, expect, it, vi } from "vitest";
import { makeJwt, mockFetch } from "@/test/utils";

const cookieSet = vi.fn();
vi.mock("next/headers", () => ({ cookies: async () => ({ set: cookieSet, get: () => undefined }) }));
const redirect = vi.fn((to: string) => {
  throw new Error(`REDIRECT:${to}`);
});
vi.mock("next/navigation", () => ({ redirect: (to: string) => redirect(to) }));

const { login } = await import("../login/actions");

function form(values: Record<string, string>) {
  const fd = new FormData();
  for (const [k, v] of Object.entries(values)) fd.set(k, v);
  return fd;
}

beforeEach(() => {
  cookieSet.mockClear();
  redirect.mockClear();
});

describe("login (Server Action)", () => {
  it("valida el teléfono antes de llamar a la API", async () => {
    const spy = mockFetch({});
    const out = await login(null, form({ phone: "12", password: "x" }));
    expect(out).toEqual({ error: "Revisa el teléfono: escríbelo como 0414-123.45.67.", phone: "12" });
    expect(spy).not.toHaveBeenCalled();
  });

  it("muestra el detail de la API tal cual", async () => {
    mockFetch({ "/auth/login": { status: 401, detail: "Teléfono o contraseña incorrectos.", code: "INVALID_CREDENTIALS" } });
    const out = await login(null, form({ phone: "0414-123.45.67", password: "mala" }));
    expect(out?.error).toBe("Teléfono o contraseña incorrectos.");
    expect(cookieSet).not.toHaveBeenCalled();
  });

  it("guarda las cookies y vuelve a la página pedida", async () => {
    const access = await makeJwt({ role: "ADMIN" });
    const spy = mockFetch({
      "/auth/login": { accessToken: access, refreshToken: "r1", expiresIn: 1800 },
      "/auth/me": { user: { mustChangePassword: false } },
    });
    await expect(login(null, form({ phone: "0414-123.45.67", password: "buena", next: "/admin/clientes" }))).rejects.toThrow(
      "REDIRECT:/admin/clientes",
    );
    expect(JSON.parse(String(spy.mock.calls[0][1]?.body))).toEqual({ phone: "+584141234567", password: "buena" });
    const names = cookieSet.mock.calls.map((c) => c[0]);
    expect(names).toEqual(["authToken", "refreshToken", "mustChangePassword"]);
    expect(cookieSet.mock.calls[0][2]).toMatchObject({ httpOnly: true, sameSite: "lax" });
  });

  it("si debe cambiar la contraseña, va a /cambiar-contrasena", async () => {
    const access = await makeJwt({ role: "ADMIN" });
    mockFetch({ "/auth/login": { accessToken: access, refreshToken: "r1", user: { mustChangePassword: true } } });
    await expect(login(null, form({ phone: "04141234567", password: "temporal" }))).rejects.toThrow("REDIRECT:/cambiar-contrasena");
  });

  it("un usuario que no es ADMIN no entra al panel", async () => {
    mockFetch({ "/auth/login": { accessToken: await makeJwt({ role: "CUSTOMER" }), refreshToken: "r1" } });
    const out = await login(null, form({ phone: "04141234567", password: "x" }));
    expect(out?.error).toBe("Este usuario no tiene acceso al panel.");
    expect(cookieSet).not.toHaveBeenCalled();
  });

  it("ignora un next externo", async () => {
    mockFetch({
      "/auth/login": { accessToken: await makeJwt({ role: "ADMIN" }), refreshToken: "r1" },
      "/auth/me": { user: { mustChangePassword: false } },
    });
    await expect(login(null, form({ phone: "04141234567", password: "x", next: "https://evil.example" }))).rejects.toThrow("REDIRECT:/admin");
  });
});
