/**
 * Error de la API con `detail`, `code` y `meta` tal cual (03 §7). El panel muestra
 * `detail` sin reescribirlo: la API ya lo manda en español de Venezuela.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly detail: string;
  readonly meta: Record<string, unknown> | null;

  constructor(status: number, detail: string, code = "UNKNOWN", meta: Record<string, unknown> | null = null) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.detail = detail;
    this.meta = meta;
  }
}

export const NETWORK_ERROR_DETAIL = "Sin conexión con el servidor. Revisa tu señal e intenta de nuevo.";
const FALLBACK_DETAIL = "Algo salió mal. Intenta de nuevo.";

type Body = { detail?: unknown; code?: unknown; meta?: unknown } | null;

/** Lee el cuerpo de un error de FastAPI, también los 422 de validación con `detail` en lista. */
export function apiErrorFromBody(status: number, body: Body): ApiError {
  const code = typeof body?.code === "string" ? body.code : status === 401 ? "UNAUTHENTICATED" : "UNKNOWN";
  const meta = body?.meta && typeof body.meta === "object" ? (body.meta as Record<string, unknown>) : null;
  let detail = FALLBACK_DETAIL;
  if (typeof body?.detail === "string" && body.detail.trim()) {
    detail = body.detail;
  } else if (Array.isArray(body?.detail) && body.detail.length > 0) {
    const first = body.detail[0] as { msg?: unknown };
    detail = typeof first?.msg === "string" ? `Revisa los datos: ${first.msg}` : "Revisa los datos.";
  } else if (status === 503) {
    detail = "Servicio no disponible. Intenta de nuevo.";
  }
  return new ApiError(status, detail, code, meta);
}

export async function apiErrorFromResponse(res: Response): Promise<ApiError> {
  let body: Body = null;
  try {
    body = (await res.json()) as Body;
  } catch {
    body = null;
  }
  return apiErrorFromBody(res.status, body);
}

export function isApiError(e: unknown): e is ApiError {
  return e instanceof ApiError;
}
