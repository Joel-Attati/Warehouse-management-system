"""Inventory, batch, and movement schemas."""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models.inventory import MovementType


# --- Batch ---
class BatchBase(BaseModel):
    product_id: int
    batch_number: str = Field(..., min_length=1, max_length=100)
    expiry_date: Optional[date] = None
    manufacture_date: Optional[date] = None
    notes: Optional[str] = None


class BatchCreate(BatchBase):
    pass


class BatchUpdate(BaseModel):
    expiry_date: Optional[date] = None
    manufacture_date: Optional[date] = None
    notes: Optional[str] = None


class BatchResponse(BatchBase):
    id: int
    created_at: datetime
    product_sku: Optional[str] = None
    product_name: Optional[str] = None

    class Config:
        from_attributes = True


# --- Inventory Stock ---
class InventoryStockResponse(BaseModel):
    id: int
    product_id: int
    product_sku: str
    product_name: str
    category_name: Optional[str] = None
    location_id: int
    location_code: str
    location_path: Optional[str] = None
    batch_id: Optional[int] = None
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None
    quantity: int
    min_stock: int
    reorder_level: int
    stock_status: str  # ok, low, critical
    last_updated: datetime

    class Config:
        from_attributes = True


class StockSummary(BaseModel):
    product_id: int
    sku: str
    name: str
    category_name: Optional[str] = None
    unit: str
    total_quantity: int
    min_stock: int
    reorder_level: int
    stock_status: str  # ok, low, critical
    location_count: int


# --- Movement Requests ---
class ReceiveStockRequest(BaseModel):
    product_id: int
    location_id: int
    quantity: int = Field(..., gt=0)
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None
    manufacture_date: Optional[date] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class IssueStockRequest(BaseModel):
    product_id: int
    location_id: int
    quantity: int = Field(..., gt=0)
    batch_id: Optional[int] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class TransferStockRequest(BaseModel):
    product_id: int
    from_location_id: int
    to_location_id: int
    quantity: int = Field(..., gt=0)
    batch_id: Optional[int] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class MovementResponse(BaseModel):
    id: int
    movement_type: MovementType
    product_id: int
    product_sku: str
    product_name: str
    batch_id: Optional[int] = None
    batch_number: Optional[str] = None
    from_location_id: Optional[int] = None
    from_location_name: Optional[str] = None
    to_location_id: Optional[int] = None
    to_location_name: Optional[str] = None
    quantity: int
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    performed_by: int
    performed_by_name: str
    created_at: datetime

    class Config:
        from_attributes = True

