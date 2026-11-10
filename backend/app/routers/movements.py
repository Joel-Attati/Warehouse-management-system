"""Inventory movements router (Receive, Issue, Transfer, Movement History)."""
import math
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.database import get_db
from app.dependencies.auth import get_current_active_user, require_staff
from app.models.inventory import Batch, InventoryMovement
from app.models.product import Product
from app.models.user import User
from app.models.warehouse import StorageLocation
from app.schemas.common import PaginatedResponse
from app.schemas.inventory import (
    IssueStockRequest,
    MovementResponse,
    ReceiveStockRequest,
    TransferStockRequest,
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/movements", tags=["Movements"], dependencies=[Depends(get_current_active_user)])


@router.post("/receive", response_model=MovementResponse, status_code=status.HTTP_201_CREATED)
async def receive_stock(
    data: ReceiveStockRequest,
    request: Request,
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Receive inventory into a storage location."""
    client_ip = request.client.host if request.client else None
    movement = await InventoryService.receive_stock(
        db=db,
        data=data,
        user_id=current_user.id,
        username=current_user.username,
        ip_address=client_ip,
    )
    await db.commit()

    return await get_movement(movement.id, db)


@router.post("/issue", response_model=MovementResponse)
async def issue_stock(
    data: IssueStockRequest,
    request: Request,
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Issue inventory out of a storage location."""
    client_ip = request.client.host if request.client else None
    movement = await InventoryService.issue_stock(
        db=db,
        data=data,
        user_id=current_user.id,
        username=current_user.username,
        ip_address=client_ip,
    )
    await db.commit()

    return await get_movement(movement.id, db)


@router.post("/transfer", response_model=MovementResponse)
async def transfer_stock(
    data: TransferStockRequest,
    request: Request,
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Transfer inventory between two storage locations."""
    client_ip = request.client.host if request.client else None
    movement = await InventoryService.transfer_stock(
        db=db,
        data=data,
        user_id=current_user.id,
        username=current_user.username,
        ip_address=client_ip,
    )
    await db.commit()

    return await get_movement(movement.id, db)


@router.get("", response_model=PaginatedResponse[MovementResponse])
async def list_movements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    product_id: Optional[int] = None,
    movement_type: Optional[str] = None,
    performed_by: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List inventory movement audit trail with pagination and filters."""
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

    if product_id:
        query = query.where(InventoryMovement.product_id == product_id)
    if movement_type:
        query = query.where(InventoryMovement.movement_type == movement_type.upper())
    if performed_by:
        query = query.where(InventoryMovement.performed_by == performed_by)
    if date_from:
        query = query.where(InventoryMovement.created_at >= date_from)
    if date_to:
        query = query.where(InventoryMovement.created_at <= date_to)
    if search:
        s = f"%{search}%"
        query = query.where(
            (Product.sku.ilike(s))
            | (Product.name.ilike(s))
            | (InventoryMovement.reference_number.ilike(s))
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(InventoryMovement.id.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(query)).all()

    items = []
    for mov, sku, prod_name, batch_num, from_name, to_name, user_name in rows:
        items.append(
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
        )

    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{movement_id}", response_model=MovementResponse)
async def get_movement(movement_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve detailed information on a single movement."""
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
        .where(InventoryMovement.id == movement_id)
    )
    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Movement record not found")

    mov, sku, prod_name, batch_num, from_name, to_name, user_name = row
    return MovementResponse(
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

