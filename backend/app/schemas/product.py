"""Product and category schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models.product import ProductStatus


# --- Category ---
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    product_count: Optional[int] = 0

    class Config:
        from_attributes = True


# --- Product ---
class ProductBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    category_id: Optional[int] = None
    unit: str = "pcs"
    barcode: Optional[str] = None
    qr_code: Optional[str] = None
    min_stock: int = 0
    reorder_level: int = 0
    has_expiry: bool = False
    status: ProductStatus = ProductStatus.active
    description: Optional[str] = None
    image_path: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    unit: Optional[str] = None
    barcode: Optional[str] = None
    qr_code: Optional[str] = None
    min_stock: Optional[int] = None
    reorder_level: Optional[int] = None
    has_expiry: Optional[bool] = None
    status: Optional[ProductStatus] = None
    description: Optional[str] = None


class ProductResponse(ProductBase):
    id: int
    image_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    category_name: Optional[str] = None
    total_stock: Optional[int] = 0

    class Config:
        from_attributes = True


class ProductListItem(BaseModel):
    id: int
    sku: str
    name: str
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    unit: str
    barcode: Optional[str] = None
    min_stock: int
    reorder_level: int
    has_expiry: bool
    status: ProductStatus
    image_path: Optional[str] = None
    total_stock: int = 0

    class Config:
        from_attributes = True

