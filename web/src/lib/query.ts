export type QueryValue = string | number | boolean | null | undefined;

/** Agrega `?a=1&b=2` omitiendo vacíos (los filtros y el cursor los resuelve el servidor). */
export function withQuery(path: string, query?: Record<string, QueryValue>): string {
  if (!query) return path;
  const params = new URLSearchParams();
  for (const [k, v] of Object.entries(query)) {
    if (v === undefined || v === null || v === "") continue;
    params.set(k, String(v));
  }
  const qs = params.toString();
  return qs ? `${path}${path.includes("?") ? "&" : "?"}${qs}` : path;
}
