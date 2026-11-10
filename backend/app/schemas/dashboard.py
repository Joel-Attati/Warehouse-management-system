"""Dashboard and alert schemas."""
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel

from app.schemas.inventory import MovementResponse


class LowStockAlert(BaseModel):
    product_id: int
    sku: str
    name: str
    category_name: Optional[str] = None
    unit: str
    current_stock: int
    min_stock: int
    reorder_level: int
    status: str  # low or critical


class ExpiryAlert(BaseModel):
    batch_id: int
    product_id: int
    sku: str
    name: str
    batch_number: str
    expiry_date: date
    days_until_expiry: int
    quantity: int
    location_name: Optional[str] = None


class MovementChartPoint(BaseModel):
    date: str
    receives: int
    issues: int
    transfers: int


class DashboardStats(BaseModel):
    total_products: int
    total_locations: int
    total_movements_today: int
    low_stock_count: int
    expiring_soon_count: int
    recent_movements: List[MovementResponse]
    top_low_stock: List[LowStockAlert]
    movement_trends: List[MovementChartPoint]

