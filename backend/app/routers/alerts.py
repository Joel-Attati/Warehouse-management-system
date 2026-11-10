"""Stock and expiry alerts router."""
from datetime import date, timedelta
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.inventory import Batch, InventoryStock
from app.models.product import Category, Product
from app.models.warehouse import StorageLocation
from app.schemas.dashboard import ExpiryAlert, LowStockAlert

router = APIRouter(prefix="/alerts", tags=["Alerts"], dependencies=[Depends(get_current_active_user)])


@router.get("/low-stock", response_model=List[LowStockAlert])
async def get_low_stock_alerts(db: AsyncSession = Depends(get_db)):
    """Retrieve all products currently below reorder level or minimum stock."""
    query = (
        select(
            Product.id,
            Product.sku,
            Product.name,
            Category.name.label("category_name"),
            Product.unit,
            func.coalesce(func.sum(InventoryStock.quantity), 0).label("current_stock"),
            Product.min_stock,
            Product.reorder_level,
        )
        .outerjoin(Category, Product.category_id == Category.id)
        .outerjoin(InventoryStock, Product.id == InventoryStock.product_id)
        .where(Product.status == "active")
        .group_by(Product.id, Category.name)
        .having(func.coalesce(func.sum(InventoryStock.quantity), 0) <= Product.reorder_level)
        .order_by(func.coalesce(func.sum(InventoryStock.quantity), 0).asc())
    )
    rows = (await db.execute(query)).all()

    alerts = []
    for row in rows:
        current_stock = int(row.current_stock)
        status_val = "critical" if current_stock <= row.min_stock else "low"
        alerts.append(
            LowStockAlert(
                product_id=row.id,
                sku=row.sku,
                name=row.name,
                category_name=row.category_name,
                unit=row.unit,
                current_stock=current_stock,
                min_stock=row.min_stock,
                reorder_level=row.reorder_level,
                status=status_val,
            )
        )
    return alerts


@router.get("/expiring", response_model=List[ExpiryAlert])
async def get_expiring_alerts(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all batches expiring within the specified days (default 30)."""
    today = date.today()
    threshold = today + timedelta(days=days)

    query = (
        select(
            Batch.id.label("batch_id"),
            Product.id.label("product_id"),
            Product.sku,
            Product.name,
            Batch.batch_number,
            Batch.expiry_date,
            func.coalesce(func.sum(InventoryStock.quantity), 0).label("quantity"),
            func.string_agg(StorageLocation.code, ", ").label("location_names"),
        )
        .join(Product, Batch.product_id == Product.id)
        .outerjoin(InventoryStock, Batch.id == InventoryStock.batch_id)
        .outerjoin(StorageLocation, InventoryStock.location_id == StorageLocation.id)
        .where(
            Batch.expiry_date.isnot(None),
            Batch.expiry_date <= threshold,
        )
        .group_by(Batch.id, Product.id)
        .order_by(Batch.expiry_date.asc())
    )
    rows = (await db.execute(query)).all()

    alerts = []
    for row in rows:
        diff_days = (row.expiry_date - today).days
        alerts.append(
            ExpiryAlert(
                batch_id=row.batch_id,
                product_id=row.product_id,
                sku=row.sku,
                name=row.name,
                batch_number=row.batch_number,
                expiry_date=row.expiry_date,
                days_until_expiry=diff_days,
                quantity=int(row.quantity),
                location_name=row.location_names or "Unassigned",
            )
        )
    return alerts

