# Adaptado de OpenGravity: apps/bot/src/core/exceptions.py
"""Catálogo de errores (03 §7) y sus handlers.

Toda respuesta de error tiene la forma `{detail, code, meta}`; `detail` va en español de
Venezuela y el cliente lo muestra tal cual.

- `AppError(code, meta)` → el HTTP y el texto del catálogo (o un `detail` concreto).
- `IntegrityError` → 409 con el `code` de la restricción violada (`CONSTRAINT_CODES`).
- `OperationalError` → 503 `SERVICE_UNAVAILABLE`.
- Validación → 422 `VALIDATION_ERROR` con el detalle en español.
"""
from __future__ import annotations

import enum
import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class ErrorCode(str, enum.Enum):
    """`code` → (HTTP, texto). El orden sigue 03 §7."""

    def __new__(cls, value: str, http: int, text: str):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.http = http
        obj.text = text
        return obj

    INVALID_CREDENTIALS = ("INVALID_CREDENTIALS", 401, "Teléfono o contraseña incorrectos.")
    FORBIDDEN = ("FORBIDDEN", 403, "No tienes permiso para esta acción.")
    NOT_FOUND = ("NOT_FOUND", 404, "No encontramos lo que buscas.")
    CUSTOMER_BLOCKED = ("CUSTOMER_BLOCKED", 403, "Tu cuenta está bloqueada. Escríbenos por WhatsApp.")
    OVERDUE_DEBT = ("OVERDUE_DEBT", 422, "Tienes una deuda vencida. Págala para hacer nuevos pedidos.")
    OPEN_DEBT = ("OPEN_DEBT", 422, "Tienes una deuda pendiente de $X. Págala para hacer nuevos pedidos.")
    CREDIT_LIMIT_EXCEEDED = (
        "CREDIT_LIMIT_EXCEEDED",
        422,
        "Tu crédito disponible es $X y este pedido necesita $Y. Recarga tu billetera.",
    )
    EMPTY_ORDER = ("EMPTY_ORDER", 422, "Agrega al menos un producto.")
    PRODUCT_UNAVAILABLE = ("PRODUCT_UNAVAILABLE", 422, "“<producto>” no está disponible ahora.")
    BELOW_MIN_QTY = ("BELOW_MIN_QTY", 422, "“<producto>” se vende desde N unidades.")
    INVALID_SCHEDULE = ("INVALID_SCHEDULE", 422, "Esa fecha u hora no está disponible: <motivo>.")
    INVALID_TRANSITION = ("INVALID_TRANSITION", 409, "El pedido ya cambió de estado. Actualiza la pantalla.")
    ORDER_NOT_CANCELLABLE = ("ORDER_NOT_CANCELLABLE", 409, "Este pedido ya no se puede cancelar.")
    ONLY_REDUCTION = ("ONLY_REDUCTION", 422, "Solo se puede reducir el pedido.")
    ORDER_NOT_REDUCIBLE = ("ORDER_NOT_REDUCIBLE", 409, "Este pedido tiene deuda condonada y no se puede modificar.")
    ORDER_NOT_PAYABLE = ("ORDER_NOT_PAYABLE", 409, "Este pedido ya no está esperando pago.")
    DUPLICATE_REFERENCE = ("DUPLICATE_REFERENCE", 409, "Esa referencia ya fue reportada.")
    INVALID_PAID_ON = ("INVALID_PAID_ON", 422, "La fecha del pago no puede ser futura.")
    INVALID_AMOUNT = ("INVALID_AMOUNT", 422, "El monto debe ser mayor que cero.")
    PAYMENT_NOT_REVIEWABLE = ("PAYMENT_NOT_REVIEWABLE", 409, "Este pago ya fue revisado.")
    PAYMENT_NOT_REVERSIBLE = ("PAYMENT_NOT_REVERSIBLE", 409, "Solo se puede revertir un pago aprobado.")
    ADJUSTMENT_EXCEEDS_BALANCE = ("ADJUSTMENT_EXCEEDS_BALANCE", 422, "El ajuste supera el saldo de la billetera.")
    PAYOUT_EXCEEDS_BALANCE = ("PAYOUT_EXCEEDS_BALANCE", 422, "La devolución supera el saldo a favor.")
    RECEIVABLE_NOT_VOIDABLE = (
        "RECEIVABLE_NOT_VOIDABLE",
        409,
        "Esta deuda no se puede anular; cancela el pedido o condónala.",
    )
    RATE_UNAVAILABLE = ("RATE_UNAVAILABLE", 409, "No hay tasa del día. El administrador debe cargarla.")
    IDEMPOTENCY_CONFLICT = ("IDEMPOTENCY_CONFLICT", 409, "Esta solicitud ya se envió con otros datos.")
    FILE_INVALID = ("FILE_INVALID", 422, "El archivo debe ser una imagen o PDF de hasta 5 MB.")
    PAYMENT_ACCOUNT_MISMATCH = (
        "PAYMENT_ACCOUNT_MISMATCH",
        422,
        "La cuenta elegida no corresponde a ese método o moneda.",
    )
    PRICE_PREVIEW_EXPIRED = (
        "PRICE_PREVIEW_EXPIRED",
        409,
        "La vista previa venció o los precios cambiaron. Genera una nueva.",
    )
    IMPORT_PREVIEW_EXPIRED = (
        "IMPORT_PREVIEW_EXPIRED",
        409,
        "La vista previa de la importación venció. Sube el archivo otra vez.",
    )
    INVALID_CURRENT_PASSWORD = ("INVALID_CURRENT_PASSWORD", 422, "La contraseña actual no es correcta.")
    PHONE_TAKEN = (
        "PHONE_TAKEN",
        409,
        "Ese teléfono ya está registrado. Inicia sesión o escríbenos si olvidaste tu contraseña.",
    )
    RATE_LIMITED = ("RATE_LIMITED", 429, "Demasiados intentos. Espera un minuto.")
    UNAUTHENTICATED = ("UNAUTHENTICATED", 401, "Tu sesión expiró. Inicia sesión de nuevo.")
    VALIDATION_ERROR = ("VALIDATION_ERROR", 422, "Revisa los datos: <detalle>.")
    INVALID_SETTINGS = ("INVALID_SETTINGS", 422, "Configuración inválida: <detalle>.")
    SERVICE_UNAVAILABLE = ("SERVICE_UNAVAILABLE", 503, "Servicio no disponible. Intenta de nuevo.")
    NOT_IMPLEMENTED = ("NOT_IMPLEMENTED", 501, "Aún no disponible.")


#: Restricción nombrada (02) → `code`. Lo que no esté aquí responde 409 `VALIDATION_ERROR`.
CONSTRAINT_CODES: dict[str, ErrorCode] = {
    "uq_users_phone": ErrorCode.PHONE_TAKEN,
    "uq_payments_bank_account_reference_live": ErrorCode.DUPLICATE_REFERENCE,
    "uq_payments_customer_idem": ErrorCode.IDEMPOTENCY_CONFLICT,
    "uq_orders_customer_idem": ErrorCode.IDEMPOTENCY_CONFLICT,
    "uq_idempotency_records_scope_key": ErrorCode.IDEMPOTENCY_CONFLICT,
}

_UNMAPPED_INTEGRITY_DETAIL = "Revisa los datos: ya existe un registro igual o falta uno relacionado."


class AppError(Exception):
    """Error de negocio con `code` del catálogo.

    `detail` reemplaza el texto genérico del catálogo cuando hay uno concreto
    (p. ej. “Tienes una deuda pendiente de $12.50…”). `meta` viaja tal cual al cliente.
    """

    def __init__(self, code: ErrorCode, meta: dict[str, Any] | None = None, detail: str | None = None):
        self.code = code
        self.meta = meta or {}
        self.detail = detail or code.text
        super().__init__(f"{code.value}: {self.detail}")

    @property
    def status_code(self) -> int:
        return self.code.http


def not_implemented(owner: str):
    """Operación del inventario E1 declarada por FND-E1 cuyo cuerpo completa el bloque `owner`."""
    raise AppError(ErrorCode.NOT_IMPLEMENTED, {"owner": owner})


def error_body(code: ErrorCode | str, detail: str, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"detail": detail, "code": code.value if isinstance(code, ErrorCode) else code, "meta": meta or {}}


def error_response(code: ErrorCode, detail: str | None = None, meta: dict | None = None, headers=None) -> JSONResponse:
    return JSONResponse(status_code=code.http, content=error_body(code, detail or code.text, meta), headers=headers)


# --------------------------------------------------------------------------- validación en español
_FIELD_NAMES = {"body": "cuerpo", "query": "consulta", "path": "ruta", "header": "cabecera"}

_MESSAGES = {
    "missing": "falta {field}",
    "string_too_short": "{field} es muy corto (mínimo {min_length})",
    "string_too_long": "{field} es muy largo (máximo {max_length})",
    "string_type": "{field} debe ser texto",
    "string_pattern_mismatch": "{field} no tiene el formato esperado",
    "int_parsing": "{field} debe ser un número entero",
    "int_type": "{field} debe ser un número entero",
    "decimal_parsing": "{field} debe ser un monto decimal",
    "decimal_type": "{field} debe ser un monto decimal",
    "decimal_max_places": "{field} admite como máximo {decimal_places} decimales",
    "greater_than": "{field} debe ser mayor que {gt}",
    "greater_than_equal": "{field} debe ser mayor o igual que {ge}",
    "less_than_equal": "{field} debe ser menor o igual que {le}",
    "bool_parsing": "{field} debe ser verdadero o falso",
    "bool_type": "{field} debe ser verdadero o falso",
    "date_from_datetime_parsing": "{field} debe ser una fecha AAAA-MM-DD",
    "date_parsing": "{field} debe ser una fecha AAAA-MM-DD",
    "date_type": "{field} debe ser una fecha AAAA-MM-DD",
    "datetime_parsing": "{field} debe ser una fecha y hora ISO",
    "datetime_type": "{field} debe ser una fecha y hora ISO",
    "enum": "{field} debe ser uno de: {expected}",
    "literal_error": "{field} debe ser uno de: {expected}",
    "list_type": "{field} debe ser una lista",
    "too_short": "{field} necesita al menos {min_length} elemento(s)",
    "too_long": "{field} admite como máximo {max_length} elemento(s)",
    "extra_forbidden": "{field} no se reconoce",
    "json_invalid": "el cuerpo no es un JSON válido",
    "model_attributes_type": "el cuerpo debe ser un objeto JSON",
    "dict_type": "{field} debe ser un objeto",
    "uuid_parsing": "{field} no tiene el formato esperado",
}


def _field_label(loc: tuple) -> str:
    parts = [str(p) for p in loc if p not in _FIELD_NAMES and not isinstance(p, int)]
    return f"“{'.'.join(parts)}”" if parts else "un dato"


def spanish_validation_message(err: dict) -> str:
    etype = err.get("type", "")
    field = _field_label(tuple(err.get("loc", ())))
    ctx = {k: v for k, v in (err.get("ctx") or {}).items()}
    if etype == "value_error":
        # Mensajes propios de los validadores (ya en español).
        msg = str(ctx.get("error") or err.get("msg") or "")
        msg = msg.removeprefix("Value error, ")
        return f"{field}: {msg}" if field != "un dato" else msg
    template = _MESSAGES.get(etype)
    if template is None:
        return f"{field} no es válido"
    try:
        return template.format(field=field, **ctx)
    except (KeyError, IndexError):
        return f"{field} no es válido"


def validation_detail(errors: list[dict]) -> str:
    msgs: list[str] = []
    for e in errors[:3]:
        m = spanish_validation_message(e)
        if m not in msgs:
            msgs.append(m)
    return "Revisa los datos: " + "; ".join(msgs) + "."


# --------------------------------------------------------------------------- handlers
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return error_response(exc.code, exc.detail, exc.meta)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = list(exc.errors())
    fields = [".".join(str(p) for p in e.get("loc", ()) if p not in _FIELD_NAMES) for e in errors]
    return error_response(ErrorCode.VALIDATION_ERROR, validation_detail(errors), {"fields": fields})


def _constraint_name(exc: IntegrityError) -> str | None:
    diag = getattr(getattr(exc, "orig", None), "diag", None)
    return getattr(diag, "constraint_name", None)


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    name = _constraint_name(exc)
    code = CONSTRAINT_CODES.get(name or "")
    if code is None:
        logger.warning("IntegrityError sin código (%s) en %s %s", name, request.method, request.url.path)
        return JSONResponse(
            status_code=409,
            content=error_body(ErrorCode.VALIDATION_ERROR, _UNMAPPED_INTEGRITY_DETAIL, {"constraint": name}),
        )
    return JSONResponse(status_code=409, content=error_body(code, code.text, {"constraint": name}))


async def operational_error_handler(request: Request, exc: OperationalError) -> JSONResponse:
    logger.error("Base de datos no disponible en %s %s: %s", request.method, request.url.path, exc.__class__.__name__)
    return error_response(ErrorCode.SERVICE_UNAVAILABLE)


_HTTP_CODES = {
    401: ErrorCode.UNAUTHENTICATED,
    403: ErrorCode.FORBIDDEN,
    404: ErrorCode.NOT_FOUND,
    429: ErrorCode.RATE_LIMITED,
    501: ErrorCode.NOT_IMPLEMENTED,
    503: ErrorCode.SERVICE_UNAVAILABLE,
}


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = _HTTP_CODES.get(exc.status_code)
    if code is not None:
        return error_response(code, headers=getattr(exc, "headers", None))
    if exc.status_code == 405:
        return JSONResponse(
            status_code=405, content=error_body(ErrorCode.NOT_FOUND, "Esta operación no existe para esta ruta.")
        )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(ErrorCode.VALIDATION_ERROR, "Revisa los datos de la solicitud."),
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500, content=error_body(ErrorCode.SERVICE_UNAVAILABLE, ErrorCode.SERVICE_UNAVAILABLE.text)
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(OperationalError, operational_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)


# --------------------------------------------------------------------------- OpenAPI
def error_responses(*codes: ErrorCode) -> dict[int | str, dict]:
    """`responses=` de una operación: un 4xx/5xx por HTTP con los `code` posibles."""
    by_status: dict[int, list[ErrorCode]] = {}
    for c in codes:
        by_status.setdefault(c.http, []).append(c)
    out: dict[int | str, dict] = {}
    for status, cs in sorted(by_status.items()):
        out[status] = {
            "model": ErrorOut,
            "description": " · ".join(f"`{c.value}`: {c.text}" for c in cs),
            "content": {"application/json": {"example": error_body(cs[0], cs[0].text)}},
        }
    return out


from src.core.schemas import ApiModel  # noqa: E402


class ErrorOut(ApiModel):
    detail: str
    code: str
    meta: dict[str, Any] = {}
