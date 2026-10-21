// Adaptado de OpenGravity: apps/web/src/proxy.ts
import { NextResponse, type NextRequest } from "next/server";
import { CHANGE_PASSWORD_PATH, decideAccess } from "@/lib/auth-guard";
import { verifyAccessToken } from "@/lib/jwt";
import {
  ACCESS_COOKIE,
  MUST_CHANGE_COOKIE,
  REFRESH_COOKIE,
  apiMe,
  clearSession,
  publicUrl,
  readMustChange,
  writeMustChange,
} from "@/lib/session";

/**
 * Protege `/admin/**` y `/cambiar-contrasena` (09 §E1 — Pantallas):
 * - sin access válido y con refresh → `/api/auth/refresh?next=…`; sin nada → `/login?next=…`;
 * - rol distinto de ADMIN → `/login` con aviso;
 * - `mustChangePassword` (de `/auth/me`, recordado en cookie) → `/cambiar-contrasena`.
 */
export async function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const target = `${pathname}${search}`;
  const access = request.cookies.get(ACCESS_COOKIE)?.value;
  const claims = await verifyAccessToken(access);
  let mustChange = readMustChange(request.cookies.get(MUST_CHANGE_COOKIE)?.value);

  let decision = decideAccess({
    pathname,
    target,
    claims,
    hasRefreshToken: !!request.cookies.get(REFRESH_COOKIE)?.value,
    mustChangePassword: mustChange,
  });

  let learned: boolean | null = null;
  if (decision.type === "check-me" && access) {
    try {
      const me = await apiMe(access);
      if (me) {
        learned = me.user?.mustChangePassword === true;
        mustChange = learned;
        decision = decideAccess({ pathname, target, claims, hasRefreshToken: true, mustChangePassword: mustChange });
      } else {
        decision = { type: "refresh", next: target };
      }
    } catch {
      // API caída: se deja pasar; la página mostrará el error de la API y la API exige el cambio igual.
      decision = { type: "next" };
    }
  }

  const to = (path: string) => publicUrl(path, request.headers, request.url);

  switch (decision.type) {
    case "next": {
      const res = NextResponse.next();
      if (learned !== null) writeMustChange(res.cookies, learned);
      res.headers.set("Cache-Control", "private, no-store");
      return res;
    }
    case "refresh":
      return NextResponse.redirect(to(`/api/auth/refresh?next=${encodeURIComponent(decision.next)}`));
    case "login":
      return NextResponse.redirect(to(`/login?next=${encodeURIComponent(decision.next)}`));
    case "forbidden": {
      const res = NextResponse.redirect(to("/login?motivo=rol"));
      clearSession(res.cookies);
      return res;
    }
    case "change-password": {
      const res = NextResponse.redirect(to(CHANGE_PASSWORD_PATH));
      if (learned !== null) writeMustChange(res.cookies, learned);
      return res;
    }
    case "check-me":
      return NextResponse.redirect(to(`/login?next=${encodeURIComponent(target)}`));
  }
}

export const config = {
  matcher: ["/admin", "/admin/:path*", "/cambiar-contrasena", "/cambiar-contrasena/:path*"],
};
