// Adaptado de OpenGravity: apps/web/src/lib/utils.ts (solo `cn`)
import { clsx, type ClassValue } from "clsx";

/** Une clases condicionales. Sin tailwind-merge: los componentes no apilan utilidades en conflicto. */
export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}
