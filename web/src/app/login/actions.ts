"use server";
// Adaptado de OpenGravity: apps/web/src/lib/actions.ts (patrón de Server Action con cookie httpOnly)

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { CHANGE_PASSWORD_PATH, safeNext } from "@/lib/auth-guard";
import { isApiError } from "@/lib/errors";
import { verifyAccessToken } from "@/lib/jwt";
import { normalizeVePhone } from "@/lib/phone";
import { apiLogin, apiMe, writeSession } from "@/lib/session";
import { LOGIN_TEXT } from "./texts";

export type LoginState = { error: string; phone: string } | null;

/**
 * Login del administrador (09 §E1 — Acceso): teléfono + contraseña → `POST /auth/login`.
 * Guarda `authToken` y `refreshToken` en cookies httpOnly y, si toca, manda a cambiar la
 * contraseña. El `detail` de la API se muestra tal cual (CLAUDE.md §7).
 */
export async function login(_prev: LoginState, formData: FormData): Promise<LoginState> {
  const rawPhone = String(formData.get("phone") ?? "");
  const password = String(formData.get("password") ?? "");
  const next = safeNext(String(formData.get("next") ?? ""));

  const phone = normalizeVePhone(rawPhone);
  if (!phone) return { error: LOGIN_TEXT.phoneInvalid, phone: rawPhone };
  if (!password) return { error: LOGIN_TEXT.passwordMissing, phone: rawPhone };

  let mustChange = false;
  try {
    const pair = await apiLogin(phone, password);
    const claims = await verifyAccessToken(pair.accessToken);
    if (!claims || claims.role !== "ADMIN") return { error: LOGIN_TEXT.notAdmin, phone: rawPhone };

    if (typeof pair.user?.mustChangePassword === "boolean") {
      mustChange = pair.user.mustChangePassword;
    } else {
      const me = await apiMe(pair.accessToken);
      mustChange = me?.user?.mustChangePassword === true;
    }
    writeSession(await cookies(), pair, mustChange);
  } catch (e) {
    return { error: isApiError(e) ? e.detail : LOGIN_TEXT.generic, phone: rawPhone };
  }

  // `redirect` lanza: va fuera del try para no confundirse con un error.
  redirect(mustChange ? CHANGE_PASSWORD_PATH : next);
}
