"""Esquemas de `catalog.py` (08 §B1, recortado a E1: sin fotos y sin `GET /catalog`).

`price` es el precio **mayor** y `retailPrice` el **detal** (`null` = usa `price`). Los `*Ves` se
calculan con `rate_for(hoy)` y son `null` si no hay tasa.
"""
from __future__ import annotations

import enum

from pydantic import ConfigDict, Field

from src.core import examples as ex
from src.core.schemas import ApiModel, Money, UtcDateTime
from src.db.enums import PriceType

_CAT_EXAMPLE = {
    "id": ex.EXAMPLE_CATEGORY_ID,
    "name": "Panes",
    "sortOrder": 1,
    "isActive": True,
    "createdAt": "2026-10-01T12:00:00.000Z",
    "updatedAt": "2026-10-01T12:00:00.000Z",
}

_PRODUCT_EXAMPLE = {
    "id": ex.EXAMPLE_PRODUCT_ID,
    "categoryId": ex.EXAMPLE_CATEGORY_ID,
    "categoryName": "Panes",
    "name": "Pan canilla",
    "description": "Pan largo de corteza crujiente, horneado en la mañana.",
    "unitLabel": "unidad",
    "price": "0.80",
    "priceVes": "145.96",
    "retailPrice": "1.00",
    "retailPriceVes": "182.45",
    "minQty": 10,
    "isPublished": True,
    "isAvailable": True,
    "sortOrder": 1,
    "createdAt": "2026-10-01T12:00:00.000Z",
    "updatedAt": ex.EXAMPLE_TS,
}


class CategoryOut(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": _CAT_EXAMPLE})

    id: str
    name: str
    sort_order: int
    is_active: bool
    created_at: UtcDateTime
    updated_at: UtcDateTime


class CategoryCreate(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": {"name": "Dulces", "sortOrder": 2}})

    name: str = Field(min_length=1, max_length=80)
    sort_order: int = 0
    is_active: bool = True


class CategoryUpdate(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": {"name": "Dulces criollos", "isActive": True}})

    name: str | None = Field(default=None, min_length=1, max_length=80)
    sort_order: int | None = None
    is_active: bool | None = None


class AdminProduct(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": _PRODUCT_EXAMPLE})

    id: str
    category_id: str
    category_name: str | None = None
    name: str
    description: str | None = None
    unit_label: str
    price: Money
    price_ves: Money | None = None
    retail_price: Money | None = None
    retail_price_ves: Money | None = None
    min_qty: int
    is_published: bool
    is_available: bool
    sort_order: int
    created_at: UtcDateTime
    updated_at: UtcDateTime


class ProductCreate(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "categoryId": ex.EXAMPLE_CATEGORY_ID,
                "name": "Cachito de jamón",
                "unitLabel": "unidad",
                "price": "1.20",
                "retailPrice": "1.50",
                "minQty": 6,
            }
        }
    )

    category_id: str
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    unit_label: str = Field(default="unidad", min_length=1, max_length=30)
    price: Money = Field(description="Precio mayor en USD (> 0).")
    retail_price: Money | None = Field(default=None, description="Precio detal en USD (> 0); null = usa `price`.")
    min_qty: int = Field(default=1, ge=1)
    is_published: bool = True
    is_available: bool = True
    sort_order: int = 0


class ProductUpdate(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": {"retailPrice": "1.60", "isAvailable": False}})

    category_id: str | None = None
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    unit_label: str | None = Field(default=None, min_length=1, max_length=30)
    price: Money | None = None
    retail_price: Money | None = Field(default=None, description="Enviar `null` explícito quita el precio detal.")
    min_qty: int | None = Field(default=None, ge=1)
    is_published: bool | None = None
    is_available: bool | None = None
    sort_order: int | None = None


class BulkPriceMode(str, enum.Enum):
    PERCENT = "PERCENT"
    AMOUNT = "AMOUNT"


class BulkPriceIn(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"categoryId": ex.EXAMPLE_CATEGORY_ID, "target": "RETAIL", "mode": "PERCENT", "value": "10", "roundTo": "0.05"}
        }
    )

    product_ids: list[str] | None = None
    category_id: str | None = None
    target: PriceType = PriceType.WHOLESALE
    mode: BulkPriceMode
    value: Money = Field(description="Porcentaje o monto en USD; negativo para bajar.")
    round_to: Money | None = Field(default=None, description="Redondeo del precio nuevo, p. ej. 0.05.")


class BulkPriceRow(ApiModel):
    product_id: str
    name: str
    old_price: Money | None = None
    new_price: Money


class BulkPricePreview(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rows": [{"productId": ex.EXAMPLE_PRODUCT_ID, "name": "Pan canilla", "oldPrice": "1.00", "newPrice": "1.10"}],
                "previewToken": "bp_9f2c1e7a4b6d8e0f",
            }
        }
    )

    rows: list[BulkPriceRow]
    preview_token: str


class BulkPriceApplyIn(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": {"previewToken": "bp_9f2c1e7a4b6d8e0f"}})

    preview_token: str = Field(min_length=1)


class BulkPriceApplyOut(ApiModel):
    model_config = ConfigDict(json_schema_extra={"example": {"updated": 12, "batchId": "h5j1k8l2m6n9p3q7r0s4t2v8"}})

    updated: int
    batch_id: str


class PriceHistoryRow(ApiModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "e2f7g3h9j4k0l5m1n6p2q8r3",
                "productId": ex.EXAMPLE_PRODUCT_ID,
                "priceType": "RETAIL",
                "oldPrice": "1.00",
                "newPrice": "1.10",
                "changedBy": ex.EXAMPLE_ADMIN_ID,
                "changedByName": ex.EXAMPLE_ADMIN_NAME,
                "batchId": "h5j1k8l2m6n9p3q7r0s4t2v8",
                "createdAt": ex.EXAMPLE_TS,
            }
        }
    )

    id: str
    product_id: str
    price_type: PriceType
    old_price: Money | None = None
    new_price: Money | None = None
    changed_by: str | None = None
    changed_by_name: str | None = None
    batch_id: str | None = None
    created_at: UtcDateTime
