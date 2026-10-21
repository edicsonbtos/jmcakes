// Adaptado de OpenGravity: apps/web/src/proxy.ts (patrón de rutas públicas y redirección a /login)
import type { AccessClaims, Role } from "./jwt";

/**
 * Reglas de acceso por ruta (01 §Autenticación, 09 §E1 — Pantallas). Se evalúan en
 * `src/proxy.ts`; esta función es pura para poder probarla sin Next.
 * En E1 solo existe el panel del administrador.
 */
export const ROUTE_ROLES: ReadonlyArray<{ prefix: string; roles: readonly Role[] }> = [
  { prefix: "/admin", roles: ["ADMIN"] },
  { prefix: "/cambiar-contrasena", roles: ["ADMIN"] },
];

export const CHANGE_PASSWORD_PATH = "/cambiar-contrasena";
export const HOME_BY_ROLE: Partial<Record<Role, string>> = { ADMIN: "/admin" };
export const DEFAULT_NEXT = "/admin";

function matches(pathname: string, prefix: string): boolean {
  return pathname === prefix || pathname.startsWith(`${prefix}/`);
}

export function requiredRoles(pathname: string): readonly Role[] | null {
  return ROUTE_ROLES.find((r) => matches(pathname, r.prefix))?.roles ?? null;
}

/**
 * Solo rutas internas: empieza con "/" y no es "//" ni "/\" (evita redirecciones abiertas).
 * Nunca devuelve rutas de /api ni /login para no crear bucles.
 */
export function safeNext(raw: string | null | undefined, fallback: string = DEFAULT_NEXT): string {
  if (!raw || typeof raw !== "string") return fallback;
  if (!raw.startsWith("/") || raw.startsWith("//") || raw.startsWith("/\\")) return fallback;
  if (Array.from(raw).some((ch) => ch.charCodeAt(0) < 32)) return fallback;
  if (raw.startsWith("/api/") || raw === "/login" || raw.startsWith("/login?")) return fallback;
  return raw;
}

export type GuardInput = {
  pathname: string;
  /** `pathname + search` para volver después del login o del refresh. */
  target: string;
  /** Claims del access válido, o null si falta, venció o es inválido. */
  claims: AccessClaims | null;
  hasRefreshToken: boolean;
  /** Valor de la cookie `mustChangePassword`: true, false o null si aún no se consultó `/auth/me`. */
  mustChangePassword: boolean | null;
};

export type GuardDecision =
  | { type: "next" }
  | { type: "login"; next: string }
  | { type: "refresh"; next: string }
  | { type: "forbidden" }
  | { type: "check-me" }
  | { type: "change-password" };

export function decideAccess(input: GuardInput): GuardDecision {
  const roles = requiredRoles(input.pathname);
  if (!roles) return { type: "next" };

  if (!input.claims) {
    return input.hasRefreshToken ? { type: "refresh", next: input.target } : { type: "login", next: input.target };
  }
  if (!roles.includes(input.claims.role)) return { type: "forbidden" };

  if (input.mustChangePassword === null) return { type: "check-me" };
  if (input.mustChangePassword && !matches(input.pathname, CHANGE_PASSWORD_PATH)) {
    return { type: "change-password" };
  }
  return { type: "next" };
}
