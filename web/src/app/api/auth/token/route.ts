import { NextResponse, type NextRequest } from "next/server";
import { secondsLeft, verifyAccessToken } from "@/lib/jwt";
import { ACCESS_COOKIE, REFRESH_COOKIE, accessMaxAge, clearSession, isSameOrigin, refreshSession, writeSession } from "@/lib/session";

export const dynamic = "force-dynamic";

/** Si al access le quedan menos de 5 min, se refresca antes de entregarlo (01). */
const MIN_SECONDS_LEFT = 5 * 60;

const NO_STORE = { "Cache-Control": "no-store" };

/**
 * Entrega al JS del mismo origen un access **fresco** para llamar a la API con Bearer.
 * Es la única forma de que el navegador obtenga un token: ninguna ruta recibe uno.
 */
export async function GET(request: NextRequest) {
  if (!isSameOrigin(request.headers, request.url)) {
    return NextResponse.json({ detail: "Solicitud no permitida.", code: "FORBIDDEN" }, { status: 403, headers: NO_STORE });
  }
  const access = request.cookies.get(ACCESS_COOKIE)?.value;
  const claims = await verifyAccessToken(access);
  if (access && claims && secondsLeft(claims) >= MIN_SECONDS_LEFT) {
    return NextResponse.json({ accessToken: access, expiresAt: claims.exp }, { headers: NO_STORE });
  }

  const refreshToken = request.cookies.get(REFRESH_COOKIE)?.value;
  if (refreshToken) {
    try {
      const pair = await refreshSession(refreshToken);
      if (pair) {
        const expiresAt = Math.floor(Date.now() / 1000) + accessMaxAge(pair);
        const res = NextResponse.json({ accessToken: pair.accessToken, expiresAt }, { headers: NO_STORE });
        writeSession(res.cookies, pair);
        return res;
      }
    } catch {
      // Sin red: si el access actual todavía sirve, se entrega; si no, 503.
      if (access && claims && secondsLeft(claims) > 0) {
        return NextResponse.json({ accessToken: access, expiresAt: claims.exp }, { headers: NO_STORE });
      }
      return NextResponse.json(
        { detail: "Sin conexión con el servidor. Revisa tu señal e intenta de nuevo.", code: "NETWORK_ERROR" },
        { status: 503, headers: NO_STORE },
      );
    }
  }

  const res = NextResponse.json(
    { detail: "Tu sesión venció. Entra de nuevo.", code: "UNAUTHENTICATED" },
    { status: 401, headers: NO_STORE },
  );
  clearSession(res.cookies);
  return res;
}
