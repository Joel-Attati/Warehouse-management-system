"""Inventory stock and batch management router."""
import math
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_active_user, require_manager
from app.models.inventory import Batch, InventoryStock
from app.models.product import Category, Product
from app.models.user import User
from app.models.warehouse import Aisle, Rack, Shelf, StorageLocation, Warehouse
from app.schemas.common import PaginatedResponse
from app.schemas.inventory import (
    BatchCreate,
    BatchResponse,
    BatchUpdate,
    InventoryStockResponse,
    StockSummary,
)

router = APIRouter(prefix="/inventory", tags=["Inventory"], dependencies=[Depends(get_current_active_user)])


# ─────────────────────────────────────────────────────────────
# INVENTORY STOCK
# ─────────────────────────────────────────────────────────────
@router.get("/stock", response_model=PaginatedResponse[InventoryStockResponse])
async def list_stock(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    product_id: Optional[int] = None,
    location_id: Optional[int] = None,
    warehouse_id: Optional[int] = None,
    search: Optional[str] = None,
    low_stock_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """List inventory stock by product, location, and batch."""
    query = (
        select(
            InventoryStock,
            Product,
            Category.name.label("category_name"),
            StorageLocation,
            Shelf,
            Rack,
            Aisle,
            Warehouse,
            Batch,
        )
        .join(Product, InventoryStock.product_id == Product.id)
        .outerjoin(Category, Product.category_id == Category.id)
        .join(StorageLocation, InventoryStock.location_id == StorageLocation.id)
        .join(Shelf, StorageLocation.shelf_id == Shelf.id)
        .join(Rack, Shelf.rack_id == Rack.id)
        .join(Aisle, Rack.aisle_id == Aisle.id)
        .join(Warehouse, Aisle.warehouse_id == Warehouse.id)
        .outerjoin(Batch, InventoryStock.batch_id == Batch.id)
    )

    if product_id:
        query = query.where(InventoryStock.product_id == product_id)
    if location_id:
        query = query.where(InventoryStock.location_id == location_id)
    if warehouse_id:
        query = query.where(Warehouse.id == warehouse_id)
    if search:
        s = f"%{search}%"
        query = query.where(
            (Product.sku.ilike(s))
            | (Product.name.ilike(s))
            | (StorageLocation.code.ilike(s))
        )
    if low_stock_only:
        query = query.where(InventoryStock.quantity <= Product.reorder_level)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(Product.name.asc(), StorageLocation.code.asc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(query)).all()

    items = []
    for stock, prod, cat_name, loc, shelf, rack, aisle, wh, batch in rows:
        path = f"{wh.code}-{aisle.code}-{rack.code}-{shelf.code}-{loc.code}"
        status = "ok"
        if stock.quantity <= prod.min_stock:
            status = "critical"
        elif stock.quantity <= prod.reorder_level:
            status = "low"

        items.append(
            InventoryStockResponse(
                id=stock.id,
                product_id=prod.id,
                product_sku=prod.sku,
                product_name=prod.name,
                category_name=cat_name,
                location_id=loc.id,
                location_code=loc.code,
                location_path=path,
                batch_id=batch.id if batch else None,
                batch_number=batch.batch_number if batch else None,
                expiry_date=batch.expiry_date if batch else None,
                quantity=stock.quantity,
                min_stock=prod.min_stock,
                reorder_level=prod.reorder_level,
                stock_status=status,
                last_updated=stock.last_updated,
            )
        )

    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/stock/summary", response_model=List[StockSummary])
async def stock_summary(
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Product-level aggregated inventory summary across all locations."""
    query = (
        select(
            Product.id,
            Product.sku,
            Product.name,
            Category.name.label("category_name"),
            Product.unit,
            func.coalesce(func.sum(InventoryStock.quantity), 0).label("total_quantity"),
            Product.min_stock,
            Product.reorder_level,
            func.count(func.distinct(InventoryStock.location_id)).label("location_count"),
        )
        .outerjoin(Category, Product.category_id == Category.id)
        .outerjoin(InventoryStock, Product.id == InventoryStock.product_id)
        .where(Product.status == "active")
        .group_by(Product.id, Category.name)
    )

    if category_id:
        query = query.where(Product.category_id == category_id)
    if search:
        s = f"%{search}%"
        query = query.where((Product.sku.ilike(s)) | (Product.name.ilike(s)))

    query = query.order_by(Product.name.asc())
    rows = (await db.execute(query)).all()

    results = []
    for row in rows:
        total_qty = int(row.total_quantity)
        status = "ok"
        if total_qty <= row.min_stock:
            status = "critical"
        elif total_qty <= row.reorder_level:
            status = "low"

        results.append(
            StockSummary(
                product_id=row.id,
                sku=row.sku,
                name=row.name,
                category_name=row.category_name,
                unit=row.unit,
                total_quantity=total_qty,
                min_stock=row.min_stock,
                reorder_level=row.reorder_level,
                stock_status=status,
                location_count=row.location_count,
            )
        )
    return results


# ─────────────────────────────────────────────────────────────
# BATCHES
# ─────────────────────────────────────────────────────────────
@router.get("/batches", response_model=List[BatchResponse])
async def list_batches(
    product_id: Optional[int] = None,
    expiring_before: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    """List batches with optional product and expiry filtering."""
    query = (
        select(Batch, Product.sku.label("product_sku"), Product.name.label("product_name"))
        .join(Product, Batch.product_id == Product.id)
    )

    if product_id:
        query = query.where(Batch.product_id == product_id)
    if expiring_before:
        query = query.where(Batch.expiry_date <= expiring_before)

    query = query.order_by(Batch.expiry_date.asc().nulls_last())
    rows = (await db.execute(query)).all()

    results = []
    for batch, sku, name in rows:
        dto = BatchResponse.model_validate(batch)
        dto.product_sku = sku
        dto.product_name = name
        results.append(dto)
    return results


@router.post("/batches", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def create_batch(
    data: BatchCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Register a new batch for a product."""
    prod = (await db.execute(select(Product).where(Product.id == data.product_id))).scalar_one_or_none()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    batch_num = data.batch_number.strip()
    existing = await db.execute(
        select(Batch).where(Batch.product_id == data.product_id, Batch.batch_number == batch_num)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Batch number already exists for this product")

    batch = Batch(
        product_id=data.product_id,
        batch_number=batch_num,
        expiry_date=data.expiry_date,
        manufacture_date=data.manufacture_date,
        notes=data.notes,
    )
    db.add(batch)
    await db.commit()
    await db.refresh(batch)

    dto = BatchResponse.model_validate(batch)
    dto.product_sku = prod.sku
    dto.product_name = prod.name
    return dto


@router.put("/batches/{batch_id}", response_model=BatchResponse)
async def update_batch(
    batch_id: int,
    data: BatchUpdate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Update batch details."""
    query = (
        select(Batch, Product.sku.label("product_sku"), Product.name.label("product_name"))
        .join(Product, Batch.product_id == Product.id)
        .where(Batch.id == batch_id)
    )
    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Batch not found")

    batch, sku, name = row
    if data.expiry_date is not None:
        batch.expiry_date = data.expiry_date
    if data.manufacture_date is not None:
        batch.manufacture_date = data.manufacture_date
    if data.notes is not None:
        batch.notes = data.notes

    await db.commit()
    await db.refresh(batch)

    dto = BatchResponse.model_validate(batch)
    dto.product_sku = sku
    dto.product_name = name
    return dto

