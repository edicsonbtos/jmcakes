import { NextResponse, type NextRequest } from "next/server";
import { ACCESS_COOKIE, REFRESH_COOKIE, apiLogout, clearSession, isSameOrigin, publicUrl } from "@/lib/session";

export const dynamic = "force-dynamic";

/**
 * Cierra la sesión: avisa a la API (revoca el refresh) y borra las cookies.
 * Se llama con `<form method="post" action="/api/auth/logout">`; responde 303 a `/login`.
 */
export async function POST(request: NextRequest) {
  if (!isSameOrigin(request.headers, request.url)) {
    return NextResponse.json({ detail: "Solicitud no permitida.", code: "FORBIDDEN" }, { status: 403 });
  }
  await apiLogout(request.cookies.get(ACCESS_COOKIE)?.value, request.cookies.get(REFRESH_COOKIE)?.value);
  const res = NextResponse.redirect(publicUrl("/login?motivo=salida", request.headers, request.url), 303);
  clearSession(res.cookies);
  return res;
}
