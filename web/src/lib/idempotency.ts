"use client";

import { useCallback, useState } from "react";

/** Llave para `Idempotency-Key` (01 §Convenciones 7). */
export function newIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") return crypto.randomUUID();
  // Respaldo para navegadores viejos sin randomUUID (sigue siendo aleatorio y único por intento).
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

/**
 * Una llave por formulario abierto (09 §Requisitos de uso): se crea al montar, se
 * **reutiliza en cada reintento** del mismo guardado y se renueva solo tras el éxito
 * (o al abrir el formulario de nuevo).
 */
export function useIdempotencyKey(): { key: string; renew: () => void } {
  const [key, setKey] = useState(newIdempotencyKey);
  const renew = useCallback(() => setKey(newIdempotencyKey()), []);
  return { key, renew };
}
