import { jwtVerify, decodeJwt } from "jose";

/** Roles de 01 §Autenticación. En E1 solo ADMIN entra al panel. */
export type Role = "ADMIN" | "PRODUCTION" | "DELIVERY" | "CUSTOMER";

export type AccessClaims = {
  sub: string;
  role: Role;
  /** customerId, solo para CUSTOMER. */
  cid?: string | null;
  /** Segundos epoch. */
  exp: number;
};

const ROLES: readonly Role[] = ["ADMIN", "PRODUCTION", "DELIVERY", "CUSTOMER"];

function secretKey(): Uint8Array | null {
  const s = process.env.JWT_SECRET;
  return s ? new TextEncoder().encode(s) : null;
}

function toClaims(payload: Record<string, unknown>): AccessClaims | null {
  const { sub, role, cid, exp } = payload;
  if (typeof sub !== "string" || typeof exp !== "number") return null;
  if (typeof role !== "string" || !ROLES.includes(role as Role)) return null;
  return { sub, role: role as Role, cid: typeof cid === "string" ? cid : null, exp };
}

/**
 * Verifica el access JWT (HS256, `JWT_SECRET` compartido con la API).
 * Devuelve `null` si falta, está vencido, la firma no coincide o no trae los claims.
 */
export async function verifyAccessToken(token: string | undefined | null): Promise<AccessClaims | null> {
  const key = secretKey();
  if (!token || !key) return null;
  try {
    const { payload } = await jwtVerify(token, key, { algorithms: ["HS256"] });
    return toClaims(payload as Record<string, unknown>);
  } catch {
    return null;
  }
}

/** Lee `exp` sin verificar (solo para fijar la duración de la cookie de un token recién emitido). */
export function readExp(token: string): number | null {
  try {
    const { exp } = decodeJwt(token);
    return typeof exp === "number" ? exp : null;
  } catch {
    return null;
  }
}

/** Segundos que le quedan al token, según `exp` (puede ser negativo). */
export function secondsLeft(claims: Pick<AccessClaims, "exp">, nowMs: number = Date.now()): number {
  return claims.exp - Math.floor(nowMs / 1000);
}
