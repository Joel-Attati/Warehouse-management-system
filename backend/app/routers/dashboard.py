"""Dashboard statistics and summary router."""
from datetime import date, datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.inventory import Batch, InventoryMovement, InventoryStock, MovementType
from app.models.product import Category, Product
from app.models.user import User
from app.models.warehouse import StorageLocation
from app.schemas.dashboard import DashboardStats, LowStockAlert, MovementChartPoint
from app.schemas.inventory import MovementResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"], dependencies=[Depends(get_current_active_user)])


@router.get("", response_model=DashboardStats)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Retrieve unified dashboard summary and KPIs."""
    today = date.today()
    start_of_today = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)

    # 1. Total active products
    total_products = (
        await db.execute(select(func.count(Product.id)).where(Product.status == "active"))
    ).scalar_one()

    # 2. Total active storage locations
    total_locations = (
        await db.execute(select(func.count(StorageLocation.id)).where(StorageLocation.is_active == True))
    ).scalar_one()

    # 3. Movements today
    movements_today = (
        await db.execute(
            select(func.count(InventoryMovement.id)).where(InventoryMovement.created_at >= start_of_today)
        )
    ).scalar_one()

    # 4. Low stock count
    low_stock_subq = (
        select(Product.id)
        .outerjoin(InventoryStock, Product.id == InventoryStock.product_id)
        .where(Product.status == "active")
        .group_by(Product.id)
        .having(func.coalesce(func.sum(InventoryStock.quantity), 0) <= Product.reorder_level)
        .subquery()
    )
    low_stock_count = (await db.execute(select(func.count()).select_from(low_stock_subq))).scalar_one()

    # 5. Expiring soon (within 30 days)
    threshold_30d = today + timedelta(days=30)
    expiring_soon_count = (
        await db.execute(
            select(func.count(Batch.id)).where(
                Batch.expiry_date.isnot(None),
                Batch.expiry_date <= threshold_30d,
            )
        )
    ).scalar_one()

    # 6. Top 5 low stock items
    low_query = (
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
        .limit(5)
    )
    low_rows = (await db.execute(low_query)).all()
    top_low_stock = [
        LowStockAlert(
            product_id=row.id,
            sku=row.sku,
            name=row.name,
            category_name=row.category_name,
            unit=row.unit,
            current_stock=int(row.current_stock),
            min_stock=row.min_stock,
            reorder_level=row.reorder_level,
            status="critical" if int(row.current_stock) <= row.min_stock else "low",
        )
        for row in low_rows
    ]

    # 7. Recent 10 movements
    FromLoc = aliased(StorageLocation)
    ToLoc = aliased(StorageLocation)
    mov_query = (
        select(
            InventoryMovement,
            Product.sku.label("product_sku"),
            Product.name.label("product_name"),
            Batch.batch_number.label("batch_number"),
            FromLoc.name.label("from_location_name"),
            ToLoc.name.label("to_location_name"),
            User.username.label("performed_by_name"),
        )
        .join(Product, InventoryMovement.product_id == Product.id)
        .outerjoin(Batch, InventoryMovement.batch_id == Batch.id)
        .outerjoin(FromLoc, InventoryMovement.from_location_id == FromLoc.id)
        .outerjoin(ToLoc, InventoryMovement.to_location_id == ToLoc.id)
        .join(User, InventoryMovement.performed_by == User.id)
        .order_by(InventoryMovement.id.desc())
        .limit(10)
    )
    mov_rows = (await db.execute(mov_query)).all()
    recent_movements = [
        MovementResponse(
            id=m.id,
            movement_type=m.movement_type,
            product_id=m.product_id,
            product_sku=sku,
            product_name=pname,
            batch_id=m.batch_id,
            batch_number=bnum,
            from_location_id=m.from_location_id,
            from_location_name=fname,
            to_location_id=m.to_location_id,
            to_location_name=tname,
            quantity=m.quantity,
            reference_number=m.reference_number,
            notes=m.notes,
            performed_by=m.performed_by,
            performed_by_name=uname,
            created_at=m.created_at,
        )
        for m, sku, pname, bnum, fname, tname, uname in mov_rows
    ]

    # 8. Movement trends (last 7 days)
    trends: List[MovementChartPoint] = []
    for i in range(6, -1, -1):
        target_day = today - timedelta(days=i)
        day_start = datetime.combine(target_day, datetime.min.time(), tzinfo=timezone.utc)
        day_end = datetime.combine(target_day, datetime.max.time(), tzinfo=timezone.utc)

        day_query = (
            select(
                InventoryMovement.movement_type,
                func.count(InventoryMovement.id),
            )
            .where(
                InventoryMovement.created_at >= day_start,
                InventoryMovement.created_at <= day_end,
            )
            .group_by(InventoryMovement.movement_type)
        )
        counts = dict((await db.execute(day_query)).all())
        trends.append(
            MovementChartPoint(
                date=target_day.strftime("%d %b"),
                receives=counts.get(MovementType.RECEIVE.value, 0),
                issues=counts.get(MovementType.ISSUE.value, 0),
                transfers=counts.get(MovementType.TRANSFER.value, 0),
            )
        )

    return DashboardStats(
        total_products=total_products,
        total_locations=total_locations,
        total_movements_today=movements_today,
        low_stock_count=low_stock_count,
        expiring_soon_count=expiring_soon_count,
        recent_movements=recent_movements,
        top_low_stock=top_low_stock,
        movement_trends=trends,
    )

