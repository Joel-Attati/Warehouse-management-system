"""Product and category models."""
from datetime import datetime
from enum import Enum
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProductStatus(str, Enum):
    active = "active"
    inactive = "inactive"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    products: Mapped[List["Product"]] = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    unit: Mapped[str] = mapped_column(String(50), default="pcs", nullable=False)
    barcode: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    qr_code: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    min_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reorder_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    has_expiry: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    image_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=ProductStatus.active.value, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="products")
    batches: Mapped[List["Batch"]] = relationship("Batch", back_populates="product", cascade="all, delete-orphan")
    stocks: Mapped[List["InventoryStock"]] = relationship("InventoryStock", back_populates="product")

