/**
 * Dinero como string decimal (CLAUDE.md §Dinero). La web NO calcula montos: solo
 * los formatea y valida lo que escribe el usuario antes de mandarlo a la API.
 * Todo se hace con BigInt sobre la representación escalada; nunca con float.
 */

const DECIMAL_RE = /^([+-])?(\d+)(?:\.(\d+))?$/;

/** Convierte "1234.567" a BigInt escalado (scale=2 → 123457n), redondeo HALF_UP como la API. */
export function toScaled(value: string, scale = 2): bigint {
  const m = DECIMAL_RE.exec(value.trim());
  if (!m) throw new Error(`Monto inválido: "${value}"`);
  const [, sign, intPart, frac = ""] = m;
  const padded = (frac + "0".repeat(scale + 1)).slice(0, scale + 1);
  let scaled = BigInt(intPart) * 10n ** BigInt(scale) + BigInt(padded.slice(0, scale) || "0");
  const nextDigit = Number(padded[scale]);
  const restNonZero = nextDigit >= 5;
  if (restNonZero) scaled += 1n;
  return sign === "-" ? -scaled : scaled;
}

/** Inverso de `toScaled`: 123457n, 2 → "1234.57". */
export function fromScaled(value: bigint, scale = 2): string {
  const neg = value < 0n;
  const abs = neg ? -value : value;
  const base = 10n ** BigInt(scale);
  const int = abs / base;
  const frac = (abs % base).toString().padStart(scale, "0");
  return `${neg ? "-" : ""}${int.toString()}${scale > 0 ? `.${frac}` : ""}`;
}

export function isDecimal(value: unknown): value is string {
  return typeof value === "string" && DECIMAL_RE.test(value.trim());
}

/** -1, 0 o 1 según el signo del monto. */
export function sign(value: string): -1 | 0 | 1 {
  const v = toScaled(value, 4);
  return v === 0n ? 0 : v < 0n ? -1 : 1;
}

export function abs(value: string): string {
  const t = value.trim();
  return t.startsWith("-") || t.startsWith("+") ? t.slice(1) : t;
}

/**
 * Normaliza lo que escribe el dueño en un campo de monto: acepta "12,50", "12.50" o "12".
 * Rechaza separadores de miles ("1.234,56"), más de 2 decimales y texto (09 §Carga inicial).
 * Devuelve "12.50" o `null` si no es válido. `allowNegative` solo para el saldo anterior.
 */
export function normalizeAmountInput(raw: string, opts: { allowNegative?: boolean; decimals?: number } = {}): string | null {
  const decimals = opts.decimals ?? 2;
  let t = raw.trim().replace(/\s+/g, "").replace(/^\$/, "").replace("−", "-");
  if (!t) return null;
  let neg = false;
  if (t.startsWith("-")) {
    if (!opts.allowNegative) return null;
    neg = true;
    t = t.slice(1);
  }
  const seps = t.match(/[.,]/g) ?? [];
  if (seps.length > 1) return null;
  t = t.replace(",", ".");
  const re = new RegExp(`^\\d+(?:\\.\\d{1,${decimals}})?$`);
  if (!re.test(t)) return null;
  const normalized = fromScaled(toScaled(t, decimals), decimals);
  if (normalized === fromScaled(0n, decimals)) return neg ? null : normalized;
  return neg ? `-${normalized}` : normalized;
}

/** Agrupa miles con "." y usa "," decimal (es-VE): "1234.5" → "1.234,50". */
export function groupDecimal(value: string, decimals = 2): string {
  const s = fromScaled(toScaled(abs(value), decimals), decimals);
  const [int, frac] = s.split(".");
  const grouped = int.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return frac ? `${grouped},${frac}` : grouped;
}
