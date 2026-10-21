"""Catálogo (02 §Catálogo): `price` es el precio **mayor**; `retailPrice` el **detal** (null = usa `price`)."""
from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, Column, Integer, String

from src.db.base import Base
from src.db.columns import MONEY, created_at, enum_col, fk, pk, updated_at
from src.db.enums import PriceType


class CategoryDB(Base):
    __tablename__ = "categories"

    id = pk()
    name = Column("name", String, nullable=False)
    sort_order = Column("sortOrder", Integer, nullable=False, default=0)
    is_active = Column("isActive", Boolean, nullable=False, default=True)
    created_at = created_at()
    updated_at = updated_at()


class ProductDB(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price > 0", name="price_pos"),
        CheckConstraint('"retailPrice" IS NULL OR "retailPrice" > 0', name="retail_price_pos"),
        CheckConstraint('"minQty" >= 1', name="min_qty"),
    )

    id = pk()
    category_id = fk("categoryId", "categories.id", nullable=False)
    name = Column("name", String, nullable=False)
    description = Column("description", String, nullable=True)
    unit_label = Column("unitLabel", String, nullable=False)
    price = Column("price", MONEY, nullable=False)
    retail_price = Column("retailPrice", MONEY, nullable=True)
    min_qty = Column("minQty", Integer, nullable=False, default=1)
    image_file_id = fk("imageFileId", "files.id")
    is_published = Column("isPublished", Boolean, nullable=False, default=True)
    is_available = Column("isAvailable", Boolean, nullable=False, default=True)
    sort_order = Column("sortOrder", Integer, nullable=False, default=0)
    created_at = created_at()
    updated_at = updated_at()


class PriceHistoryDB(Base):
    __tablename__ = "price_history"

    id = pk()
    product_id = fk("productId", "products.id", nullable=False)
    price_type = enum_col("priceType", PriceType, nullable=False)
    # null si no había precio detal / si se quita el precio detal.
    old_price = Column("oldPrice", MONEY, nullable=True)
    new_price = Column("newPrice", MONEY, nullable=True)
    changed_by = fk("changedBy", "users.id")
    batch_id = Column("batchId", String, nullable=True, index=True)
    created_at = created_at()
