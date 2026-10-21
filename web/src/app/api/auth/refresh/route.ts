import { NextResponse, type NextRequest } from "next/server";
import { safeNext } from "@/lib/auth-guard";
import { REFRESH_COOKIE, clearSession, isSameOrigin, publicUrl, refreshSession, writeSession } from "@/lib/session";

export const dynamic = "force-dynamic";

const EXPIRED = { detail: "Tu sesión venció. Entra de nuevo.", code: "UNAUTHENTICATED" };

/**
 * GET: lo usa `proxy.ts` cuando el access venció. Rota ambas cookies y vuelve a `next`;
 * si el refresh ya no sirve, borra la sesión y manda a `/login?next=…`.
 */
export async function GET(request: NextRequest) {
  const next = safeNext(request.nextUrl.searchParams.get("next"));
  const refreshToken = request.cookies.get(REFRESH_COOKIE)?.value;
  const toLogin = () => {
    const res = NextResponse.redirect(publicUrl(`/login?next=${encodeURIComponent(next)}`, request.headers, request.url));
    clearSession(res.cookies);
    return res;
  };
  if (!refreshToken) return toLogin();

  let pair;
  try {
    pair = await refreshSession(refreshToken);
  } catch {
    // API caída: no se borra la sesión; se reintenta en la próxima navegación.
    return NextResponse.redirect(publicUrl(`/login?next=${encodeURIComponent(next)}&motivo=red`, request.headers, request.url));
  }
  if (!pair) return toLogin();

  const res = NextResponse.redirect(publicUrl(next, request.headers, request.url));
  writeSession(res.cookies, pair);
  res.headers.set("Cache-Control", "no-store");
  return res;
}

/** POST: lo usa `client-api` tras un 401. Responde JSON, sin redirigir. */
export async function POST(request: NextRequest) {
  if (!isSameOrigin(request.headers, request.url)) {
    return NextResponse.json({ detail: "Solicitud no permitida.", code: "FORBIDDEN" }, { status: 403 });
  }
  const refreshToken = request.cookies.get(REFRESH_COOKIE)?.value;
  if (!refreshToken) return NextResponse.json(EXPIRED, { status: 401 });

  let pair;
  try {
    pair = await refreshSession(refreshToken);
  } catch {
    return NextResponse.json(
      { detail: "Sin conexión con el servidor. Revisa tu señal e intenta de nuevo.", code: "NETWORK_ERROR" },
      { status: 503 },
    );
  }
  if (!pair) {
    const res = NextResponse.json(EXPIRED, { status: 401 });
    clearSession(res.cookies);
    return res;
  }
  const res = NextResponse.json({ ok: true }, { headers: { "Cache-Control": "no-store" } });
  writeSession(res.cookies, pair);
  return res;
}
