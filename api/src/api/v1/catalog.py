"""Catálogo del panel (08 §B1). Dueño: **B-E1a**. FND-E1 declara el contrato; B-E1a completa los cuerpos.

E1: sin fotos y sin `GET /catalog` (llega en E4).
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from src.core.errors import ErrorCode, error_responses, not_implemented
from src.core.schemas import Page
from src.db.enums import UserRole
from src.domain.auth.deps import access
from src.domain.catalog.schemas import (
    AdminProduct,
    BulkPriceApplyIn,
    BulkPriceApplyOut,
    BulkPriceIn,
    BulkPricePreview,
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
    PriceHistoryRow,
    ProductCreate,
    ProductUpdate,
)

OWNER = "B-E1a"
router = APIRouter(prefix="/admin", tags=["catalog"])
_A = access(UserRole.ADMIN)
_ERR = error_responses(ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN, ErrorCode.VALIDATION_ERROR)
_ERR_ID = error_responses(ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN, ErrorCode.NOT_FOUND, ErrorCode.VALIDATION_ERROR)

Cursor = Annotated[str | None, Query(description="Cursor opaco de la página anterior.")]
Limit = Annotated[int, Query(ge=1, le=200)]


@router.get("/categories", response_model=Page[CategoryOut], summary="Categorías", responses=_ERR, **_A)
async def list_categories(cursor: Cursor = None, limit: Limit = 100):
    not_implemented(OWNER)


@router.post("/categories", response_model=CategoryOut, status_code=201, summary="Crear categoría", responses=_ERR, **_A)
async def create_category(body: CategoryCreate):
    not_implemented(OWNER)


@router.patch("/categories/{id}", response_model=CategoryOut, summary="Editar categoría", responses=_ERR_ID, **_A)
async def update_category(id: str, body: CategoryUpdate):
    not_implemented(OWNER)


@router.get("/products", response_model=Page[AdminProduct], summary="Productos con precio mayor y detal", responses=_ERR, **_A)
async def list_products(
    category_id: Annotated[str | None, Query(alias="categoryId")] = None,
    query: Annotated[str | None, Query(max_length=80)] = None,
    is_published: Annotated[bool | None, Query(alias="isPublished")] = None,
    is_available: Annotated[bool | None, Query(alias="isAvailable")] = None,
    cursor: Cursor = None,
    limit: Limit = 50,
):
    not_implemented(OWNER)


@router.post("/products", response_model=AdminProduct, status_code=201, summary="Crear producto", responses=_ERR, **_A)
async def create_product(body: ProductCreate):
    not_implemented(OWNER)


@router.get("/products/{id}", response_model=AdminProduct, summary="Detalle de producto", responses=_ERR_ID, **_A)
async def get_product(id: str):
    not_implemented(OWNER)


@router.patch("/products/{id}", response_model=AdminProduct, summary="Editar producto", responses=_ERR_ID, **_A)
async def update_product(id: str, body: ProductUpdate):
    not_implemented(OWNER)


@router.post(
    "/products/bulk-price/preview",
    response_model=BulkPricePreview,
    summary="Vista previa del cambio masivo de precios",
    responses=_ERR,
    **_A,
)
async def bulk_price_preview(body: BulkPriceIn):
    not_implemented(OWNER)


@router.post(
    "/products/bulk-price/apply",
    response_model=BulkPriceApplyOut,
    summary="Aplicar el cambio masivo de precios",
    responses=error_responses(
        ErrorCode.UNAUTHENTICATED, ErrorCode.FORBIDDEN, ErrorCode.PRICE_PREVIEW_EXPIRED, ErrorCode.VALIDATION_ERROR
    ),
    **_A,
)
async def bulk_price_apply(body: BulkPriceApplyIn):
    not_implemented(OWNER)


@router.get(
    "/products/{id}/price-history",
    response_model=Page[PriceHistoryRow],
    summary="Historial de precios (mayor y detal)",
    responses=_ERR_ID,
    **_A,
)
async def price_history(id: str, cursor: Cursor = None, limit: Limit = 50):
    not_implemented(OWNER)
