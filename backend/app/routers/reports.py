"""Reports and CSV export router (Manager+)."""
import csv
import io
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.database import get_db
from app.dependencies.auth import require_manager
from app.models.inventory import Batch, InventoryMovement, InventoryStock
from app.models.product import Category, Product
from app.models.user import User
from app.models.warehouse import Aisle, Rack, Shelf, StorageLocation, Warehouse
from app.schemas.inventory import InventoryStockResponse, MovementResponse

router = APIRouter(prefix="/reports", tags=["Reports"], dependencies=[Depends(require_manager)])


@router.get("/inventory")
async def report_inventory(
    warehouse_id: Optional[int] = None,
    category_id: Optional[int] = None,
    format: Optional[str] = Query(None, pattern="^(csv|json)?$"),
    db: AsyncSession = Depends(get_db),
):
    """Generate comprehensive inventory stock report, exportable to CSV."""
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

    if warehouse_id:
        query = query.where(Warehouse.id == warehouse_id)
    if category_id:
        query = query.where(Product.category_id == category_id)

    query = query.order_by(Warehouse.code.asc(), Product.sku.asc())
    rows = (await db.execute(query)).all()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Warehouse",
            "Location Path",
            "Location Code",
            "SKU",
            "Product Name",
            "Category",
            "Batch Number",
            "Expiry Date",
            "Quantity",
            "Unit",
            "Min Stock",
            "Reorder Level",
            "Status",
        ])

        for stock, prod, cat_name, loc, shelf, rack, aisle, wh, batch in rows:
            path = f"{wh.code}-{aisle.code}-{rack.code}-{shelf.code}-{loc.code}"
            status = "ok"
            if stock.quantity <= prod.min_stock:
                status = "critical"
            elif stock.quantity <= prod.reorder_level:
                status = "low"

            writer.writerow([
                wh.name,
                path,
                loc.code,
                prod.sku,
                prod.name,
                cat_name or "",
                batch.batch_number if batch else "",
                batch.expiry_date.isoformat() if batch and batch.expiry_date else "",
                stock.quantity,
                prod.unit,
                prod.min_stock,
                prod.reorder_level,
                status,
            ])

        output.seek(0)
        filename = f"inventory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    # Return JSON by default
    results = []
    for stock, prod, cat_name, loc, shelf, rack, aisle, wh, batch in rows:
        path = f"{wh.code}-{aisle.code}-{rack.code}-{shelf.code}-{loc.code}"
        status = "ok"
        if stock.quantity <= prod.min_stock:
            status = "critical"
        elif stock.quantity <= prod.reorder_level:
            status = "low"

        results.append(
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
    return results


@router.get("/movements")
async def report_movements(
    movement_type: Optional[str] = None,
    product_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    format: Optional[str] = Query(None, pattern="^(csv|json)?$"),
    db: AsyncSession = Depends(get_db),
):
    """Generate movement history report, exportable to CSV."""
    FromLoc = aliased(StorageLocation)
    ToLoc = aliased(StorageLocation)

    query = (
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
    )

    if movement_type:
        query = query.where(InventoryMovement.movement_type == movement_type.upper())
    if product_id:
        query = query.where(InventoryMovement.product_id == product_id)
    if date_from:
        query = query.where(InventoryMovement.created_at >= date_from)
    if date_to:
        query = query.where(InventoryMovement.created_at <= date_to)

    query = query.order_by(InventoryMovement.id.desc())
    rows = (await db.execute(query)).all()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "ID",
            "Type",
            "SKU",
            "Product Name",
            "Batch",
            "From Location",
            "To Location",
            "Quantity",
            "Reference",
            "Notes",
            "Performed By",
            "Timestamp",
        ])

        for mov, sku, prod_name, batch_num, from_name, to_name, user_name in rows:
            writer.writerow([
                mov.id,
                mov.movement_type,
                sku,
                prod_name,
                batch_num or "",
                from_name or "",
                to_name or "",
                mov.quantity,
                mov.reference_number or "",
                mov.notes or "",
                user_name,
                mov.created_at.isoformat(),
            ])

        output.seek(0)
        filename = f"movement_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    return [
        MovementResponse(
            id=mov.id,
            movement_type=mov.movement_type,
            product_id=mov.product_id,
            product_sku=sku,
            product_name=prod_name,
            batch_id=mov.batch_id,
            batch_number=batch_num,
            from_location_id=mov.from_location_id,
            from_location_name=from_name,
            to_location_id=mov.to_location_id,
            to_location_name=to_name,
            quantity=mov.quantity,
            reference_number=mov.reference_number,
            notes=mov.notes,
            performed_by=mov.performed_by,
            performed_by_name=user_name,
            created_at=mov.created_at,
        )
        for mov, sku, prod_name, batch_num, from_name, to_name, user_name in rows
    ]

