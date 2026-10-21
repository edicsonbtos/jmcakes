/**
 * Teléfonos venezolanos. La API normaliza a E.164 (02 §customers); la web normaliza
 * lo que escribe el dueño ("0414-123.45.67") para el login y arma los enlaces de WhatsApp.
 */

/** "0414-123.45.67" → "+584141234567". Devuelve `null` si no parece un número venezolano. */
export function normalizeVePhone(raw: string): string | null {
  const trimmed = raw.trim();
  const digits = trimmed.replace(/\D/g, "");
  if (trimmed.startsWith("+") && !digits.startsWith("58")) {
    return digits.length >= 8 && digits.length <= 15 ? `+${digits}` : null;
  }
  let national: string;
  if (digits.startsWith("58") && digits.length === 12) national = digits.slice(2);
  else if (digits.startsWith("0") && digits.length === 11) national = digits.slice(1);
  else if (digits.length === 10 && !digits.startsWith("0")) national = digits;
  else return null;
  return `+58${national}`;
}

/** "+584141234567" → "0414-123.45.67" (forma en que el dueño lo dicta). */
export function formatVePhone(e164: string | null | undefined): string {
  if (!e164) return "";
  const digits = e164.replace(/\D/g, "");
  if (digits.startsWith("58") && digits.length === 12) {
    const n = `0${digits.slice(2)}`;
    return `${n.slice(0, 4)}-${n.slice(4, 7)}.${n.slice(7, 9)}.${n.slice(9)}`;
  }
  return e164;
}

/** Enlace `wa.me` con texto (08 §Agregados: estado de cuenta por WhatsApp). */
export function whatsappLink(e164: string, text: string): string {
  return `https://wa.me/${e164.replace(/\D/g, "")}?text=${encodeURIComponent(text)}`;
}
