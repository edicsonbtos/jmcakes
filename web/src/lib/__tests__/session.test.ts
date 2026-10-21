// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { makeJwt, mockFetch } from "@/test/utils";
import { readExp, secondsLeft, verifyAccessToken } from "../jwt";
import {
  ACCESS_COOKIE,
  MUST_CHANGE_COOKIE,
  REFRESH_COOKIE,
  __resetRefreshInflight,
  accessMaxAge,
  clearSession,
  isSameOrigin,
  refreshSession,
  writeSession,
  type CookieOptions,
} from "../session";
import { proxy } from "@/proxy";
import { GET as tokenGET } from "@/app/api/auth/token/route";
import { GET as refreshGET, POST as refreshPOST } from "@/app/api/auth/refresh/route";
import { POST as logoutPOST } from "@/app/api/auth/logout/route";

function jar() {
  const set = new Map<string, { value: string; options: CookieOptions }>();
  return { set: (name: string, value: string, options: CookieOptions) => set.set(name, { value, options }), cookies: set };
}

function req(url: string, cookies: Record<string, string> = {}, init: { method?: string; headers?: Record<string, string> } = {}) {
  const headers = new Headers(init.headers);
  const c = Object.entries(cookies)
    .map(([k, v]) => `${k}=${v}`)
    .join("; ");
  if (c) headers.set("cookie", c);
  return new NextRequest(new URL(url, "http://panel.test"), { method: init.method ?? "GET", headers });
}

beforeEach(() => {
  __resetRefreshInflight();
});
afterEach(() => {
  vi.unstubAllGlobals();
});

describe("jwt", () => {
  it("verifica la firma HS256 con JWT_SECRET y lee los claims", async () => {
    const t = await makeJwt({ role: "ADMIN", sub: "u1" });
    const claims = await verifyAccessToken(t);
    expect(claims).toMatchObject({ sub: "u1", role: "ADMIN" });
    expect(secondsLeft(claims!)).toBeGreaterThan(1700);
    expect(readExp(t)).toBe(claims!.exp);
  });

  it("rechaza tokens vencidos, con otra firma o con un rol desconocido", async () => {
    expect(await verifyAccessToken(await makeJwt({}, -10))).toBeNull();
    expect(await verifyAccessToken(await makeJwt({}, 1800, "otro-secreto"))).toBeNull();
    expect(await verifyAccessToken(await makeJwt({ role: "ROOT" }))).toBeNull();
    expect(await verifyAccessToken("basura")).toBeNull();
    expect(await verifyAccessToken(undefined)).toBeNull();
  });
});

describe("cookies de sesión", () => {
  it("guarda access y refresh httpOnly, SameSite=Lax, path /", async () => {
    const j = jar();
    const access = await makeJwt({}, 1800);
    writeSession(j, { accessToken: access, refreshToken: "r1", expiresIn: 1800 }, true);
    const a = j.cookies.get(ACCESS_COOKIE)!;
    expect(a.value).toBe(access);
    expect(a.options).toMatchObject({ httpOnly: true, sameSite: "lax", path: "/", maxAge: 1800 });
    expect(j.cookies.get(REFRESH_COOKIE)!.options.maxAge).toBe(30 * 24 * 3600);
    expect(j.cookies.get(MUST_CHANGE_COOKIE)!.value).toBe("1");
  });

  it("toma la vida del access de exp si la API no manda expiresIn", async () => {
    const access = await makeJwt({}, 600);
    expect(accessMaxAge({ accessToken: access, refreshToken: "r" })).toBeGreaterThan(590);
  });

  it("clearSession vacía las tres cookies", () => {
    const j = jar();
    clearSession(j);
    expect([...j.cookies.values()].every((c) => c.value === "" && c.options.maxAge === 0)).toBe(true);
    expect(j.cookies.size).toBe(3);
  });

  it("isSameOrigin usa Sec-Fetch-Site y, si falta, Origin", () => {
    expect(isSameOrigin(new Headers({ "sec-fetch-site": "same-origin" }), "http://panel.test/x")).toBe(true);
    expect(isSameOrigin(new Headers({ "sec-fetch-site": "cross-site" }), "http://panel.test/x")).toBe(false);
    expect(isSameOrigin(new Headers({ origin: "http://panel.test" }), "http://panel.test/x")).toBe(true);
    expect(isSameOrigin(new Headers({ origin: "https://evil.example" }), "http://panel.test/x")).toBe(false);
    expect(
      isSameOrigin(new Headers({ origin: "https://web.up.railway.app", "x-forwarded-host": "web.up.railway.app" }), "http://0.0.0.0:8080/x"),
    ).toBe(true);
  });
});

describe("refresh serializado", () => {
  it("dos refresh simultáneos con el mismo token hacen una sola llamada a la API", async () => {
    const access = await makeJwt({});
    const fetchSpy = mockFetch({ "/auth/refresh": { accessToken: access, refreshToken: "r2", expiresIn: 1800 } });
    const [a, b] = await Promise.all([refreshSession("r1"), refreshSession("r1")]);
    expect(a).toEqual(b);
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  it("un 401 de la API devuelve null (sesión vencida)", async () => {
    mockFetch({ "/auth/refresh": { status: 401, detail: "Tu sesión venció." } });
    expect(await refreshSession("viejo")).toBeNull();
  });
});

describe("proxy.ts", () => {
  it("sin sesión manda a /login con la página pedida", async () => {
    const res = await proxy(req("/admin/clientes?f=vencidos"));
    expect(res.headers.get("location")).toBe("http://panel.test/login?next=%2Fadmin%2Fclientes%3Ff%3Dvencidos");
  });

  it("access vencido con refresh manda a /api/auth/refresh", async () => {
    const res = await proxy(req("/admin", { [ACCESS_COOKIE]: await makeJwt({}, -5), [REFRESH_COOKIE]: "r1" }));
    expect(res.headers.get("location")).toBe("http://panel.test/api/auth/refresh?next=%2Fadmin");
  });

  it("un usuario que no es ADMIN sale con la sesión borrada", async () => {
    const res = await proxy(req("/admin", { [ACCESS_COOKIE]: await makeJwt({ role: "CUSTOMER" }), [MUST_CHANGE_COOKIE]: "0" }));
    expect(res.headers.get("location")).toBe("http://panel.test/login?motivo=rol");
    expect(res.cookies.get(ACCESS_COOKIE)?.value).toBe("");
  });

  it("consulta /auth/me una vez y obliga a cambiar la contraseña", async () => {
    const fetchSpy = mockFetch({ "/auth/me": { user: { mustChangePassword: true } } });
    const res = await proxy(req("/admin", { [ACCESS_COOKIE]: await makeJwt({}), [REFRESH_COOKIE]: "r1" }));
    expect(res.headers.get("location")).toBe("http://panel.test/cambiar-contrasena");
    expect(res.cookies.get(MUST_CHANGE_COOKIE)?.value).toBe("1");
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  it("con la cookie ya resuelta deja pasar sin llamar a la API", async () => {
    const fetchSpy = mockFetch({});
    const res = await proxy(req("/admin/clientes", { [ACCESS_COOKIE]: await makeJwt({}), [MUST_CHANGE_COOKIE]: "0" }));
    expect(res.headers.get("location")).toBeNull();
    expect(res.headers.get("x-middleware-next")).toBe("1");
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});

describe("rutas /api/auth/*", () => {
  it("token: entrega el access vigente solo al mismo origen", async () => {
    const access = await makeJwt({}, 1800);
    const ok = await tokenGET(req("/api/auth/token", { [ACCESS_COOKIE]: access }, { headers: { "sec-fetch-site": "same-origin" } }));
    expect(ok.status).toBe(200);
    expect((await ok.json()).accessToken).toBe(access);
    expect(ok.headers.get("cache-control")).toBe("no-store");

    const cross = await tokenGET(req("/api/auth/token", { [ACCESS_COOKIE]: access }, { headers: { "sec-fetch-site": "cross-site" } }));
    expect(cross.status).toBe(403);
  });

  it("token: si quedan menos de 5 min, refresca y rota las cookies", async () => {
    const fresh = await makeJwt({ sub: "nuevo" }, 1800);
    mockFetch({ "/auth/refresh": { accessToken: fresh, refreshToken: "r2", expiresIn: 1800 } });
    const res = await tokenGET(
      req("/api/auth/token", { [ACCESS_COOKIE]: await makeJwt({}, 120), [REFRESH_COOKIE]: "r1" }, { headers: { "sec-fetch-site": "same-origin" } }),
    );
    expect((await res.json()).accessToken).toBe(fresh);
    expect(res.cookies.get(REFRESH_COOKIE)?.value).toBe("r2");
  });

  it("token: sin sesión responde 401 en español", async () => {
    const res = await tokenGET(req("/api/auth/token", {}, { headers: { "sec-fetch-site": "same-origin" } }));
    expect(res.status).toBe(401);
    expect(await res.json()).toEqual({ detail: "Tu sesión venció. Entra de nuevo.", code: "UNAUTHENTICATED" });
  });

  it("refresh GET vuelve a la página; si el refresh no sirve, a /login sin cookies", async () => {
    const fresh = await makeJwt({}, 1800);
    mockFetch({ "/auth/refresh": { accessToken: fresh, refreshToken: "r2", expiresIn: 1800 } });
    const ok = await refreshGET(req("/api/auth/refresh?next=%2Fadmin%2Fclientes", { [REFRESH_COOKIE]: "r1" }));
    expect(ok.headers.get("location")).toBe("http://panel.test/admin/clientes");
    expect(ok.cookies.get(ACCESS_COOKIE)?.value).toBe(fresh);

    __resetRefreshInflight();
    mockFetch({ "/auth/refresh": { status: 401, detail: "Tu sesión venció." } });
    const bad = await refreshGET(req("/api/auth/refresh?next=https://evil.example", { [REFRESH_COOKIE]: "r1" }));
    expect(bad.headers.get("location")).toBe("http://panel.test/login?next=%2Fadmin");
    expect(bad.cookies.get(REFRESH_COOKIE)?.value).toBe("");
  });

  it("refresh POST responde JSON para client-api", async () => {
    mockFetch({ "/auth/refresh": { accessToken: await makeJwt({}), refreshToken: "r2", expiresIn: 1800 } });
    const res = await refreshPOST(req("/api/auth/refresh", { [REFRESH_COOKIE]: "r1" }, { method: "POST", headers: { "sec-fetch-site": "same-origin" } }));
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ ok: true });
  });

  it("logout avisa a la API, borra cookies y responde 303 a /login", async () => {
    const fetchSpy = mockFetch({ "/auth/logout": {} });
    const res = await logoutPOST(
      req("/api/auth/logout", { [ACCESS_COOKIE]: "a", [REFRESH_COOKIE]: "r1" }, { method: "POST", headers: { origin: "http://panel.test" } }),
    );
    expect(res.status).toBe(303);
    expect(res.headers.get("location")).toBe("http://panel.test/login?motivo=salida");
    expect(res.cookies.get(ACCESS_COOKIE)?.value).toBe("");
    expect(JSON.parse(String(fetchSpy.mock.calls[0][1]?.body))).toEqual({ refreshToken: "r1" });
  });
});
