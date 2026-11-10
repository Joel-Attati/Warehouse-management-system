"""Warehouse hierarchy management router."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies.auth import get_current_active_user, require_manager
from app.models.user import User
from app.models.warehouse import Aisle, Rack, Shelf, StorageLocation, Warehouse
from app.schemas.common import MessageResponse
from app.schemas.warehouse import (
    AisleCreate,
    AisleResponse,
    AisleUpdate,
    LocationFullPath,
    RackCreate,
    RackResponse,
    RackUpdate,
    ShelfCreate,
    ShelfResponse,
    ShelfUpdate,
    StorageLocationCreate,
    StorageLocationResponse,
    StorageLocationUpdate,
    WarehouseCreate,
    WarehouseResponse,
    WarehouseUpdate,
)
from app.utils.audit import log_action

router = APIRouter(prefix="/warehouses", tags=["Warehouses"], dependencies=[Depends(get_current_active_user)])


# ─────────────────────────────────────────────────────────────
# WAREHOUSES
# ─────────────────────────────────────────────────────────────
@router.get("", response_model=List[WarehouseResponse])
async def list_warehouses(
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all warehouses with their aisle counts."""
    query = select(
        Warehouse,
        func.count(Aisle.id).label("aisle_count"),
    ).outerjoin(Aisle, Warehouse.id == Aisle.warehouse_id)

    if is_active is not None:
        query = query.where(Warehouse.is_active == is_active)

    query = query.group_by(Warehouse.id).order_by(Warehouse.id.asc())
    rows = (await db.execute(query)).all()

    results = []
    for wh, count in rows:
        wh_dict = WarehouseResponse.model_validate(wh)
        wh_dict.aisle_count = count
        results.append(wh_dict)
    return results


@router.post("", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    data: WarehouseCreate,
    request: Request,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Create a new warehouse."""
    existing = await db.execute(select(Warehouse).where(Warehouse.code == data.code.strip().upper()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Warehouse code already exists")

    wh = Warehouse(
        code=data.code.strip().upper(),
        name=data.name.strip(),
        address=data.address,
        description=data.description,
        is_active=data.is_active,
    )
    db.add(wh)
    await db.flush()

    client_ip = request.client.host if request.client else None
    await log_action(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE_WAREHOUSE",
        entity="Warehouse",
        entity_id=str(wh.id),
        detail={"code": wh.code, "name": wh.name},
        ip_address=client_ip,
    )
    await db.commit()
    await db.refresh(wh)
    return WarehouseResponse.model_validate(wh)


@router.get("/{wh_id}", response_model=WarehouseResponse)
async def get_warehouse(wh_id: int, db: AsyncSession = Depends(get_db)):
    """Get warehouse by ID."""
    wh = (await db.execute(select(Warehouse).where(Warehouse.id == wh_id))).scalar_one_or_none()
    if not wh:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    count = (await db.execute(select(func.count(Aisle.id)).where(Aisle.warehouse_id == wh_id))).scalar_one()
    res = WarehouseResponse.model_validate(wh)
    res.aisle_count = count
    return res


@router.put("/{wh_id}", response_model=WarehouseResponse)
async def update_warehouse(
    wh_id: int,
    data: WarehouseUpdate,
    request: Request,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Update warehouse details."""
    wh = (await db.execute(select(Warehouse).where(Warehouse.id == wh_id))).scalar_one_or_none()
    if not wh:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    if data.name is not None:
        wh.name = data.name.strip()
    if data.address is not None:
        wh.address = data.address
    if data.description is not None:
        wh.description = data.description
    if data.is_active is not None:
        wh.is_active = data.is_active

    client_ip = request.client.host if request.client else None
    await log_action(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE_WAREHOUSE",
        entity="Warehouse",
        entity_id=str(wh.id),
        ip_address=client_ip,
    )
    await db.commit()
    await db.refresh(wh)
    return WarehouseResponse.model_validate(wh)


@router.delete("/{wh_id}", response_model=MessageResponse)
async def delete_warehouse(
    wh_id: int,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete warehouse."""
    wh = (await db.execute(select(Warehouse).where(Warehouse.id == wh_id))).scalar_one_or_none()
    if not wh:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    wh.is_active = False
    await db.commit()
    return MessageResponse(message=f"Warehouse {wh.code} deactivated")


# ─────────────────────────────────────────────────────────────
# AISLES
# ─────────────────────────────────────────────────────────────
@router.get("/{wh_id}/aisles", response_model=List[AisleResponse])
async def list_aisles(wh_id: int, db: AsyncSession = Depends(get_db)):
    """List aisles in a warehouse."""
    query = (
        select(Aisle, func.count(Rack.id).label("rack_count"))
        .outerjoin(Rack, Aisle.id == Rack.aisle_id)
        .where(Aisle.warehouse_id == wh_id)
        .group_by(Aisle.id)
        .order_by(Aisle.code.asc())
    )
    rows = (await db.execute(query)).all()
    results = []
    for aisle, count in rows:
        dto = AisleResponse.model_validate(aisle)
        dto.rack_count = count
        results.append(dto)
    return results


@router.post("/{wh_id}/aisles", response_model=AisleResponse, status_code=status.HTTP_201_CREATED)
async def create_aisle(
    wh_id: int,
    data: AisleCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Create an aisle in a warehouse."""
    wh = (await db.execute(select(Warehouse).where(Warehouse.id == wh_id))).scalar_one_or_none()
    if not wh:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    code = data.code.strip().upper()
    existing = await db.execute(
        select(Aisle).where(Aisle.warehouse_id == wh_id, Aisle.code == code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Aisle code already exists in this warehouse")

    aisle = Aisle(
        warehouse_id=wh_id,
        code=code,
        name=data.name.strip(),
        description=data.description,
        is_active=data.is_active,
    )
    db.add(aisle)
    await db.commit()
    await db.refresh(aisle)
    return AisleResponse.model_validate(aisle)


# ─────────────────────────────────────────────────────────────
# RACKS
# ─────────────────────────────────────────────────────────────
@router.get("/aisles/{aisle_id}/racks", response_model=List[RackResponse])
async def list_racks(aisle_id: int, db: AsyncSession = Depends(get_db)):
    """List racks in an aisle."""
    query = (
        select(Rack, func.count(Shelf.id).label("shelf_count"))
        .outerjoin(Shelf, Rack.id == Shelf.rack_id)
        .where(Rack.aisle_id == aisle_id)
        .group_by(Rack.id)
        .order_by(Rack.code.asc())
    )
    rows = (await db.execute(query)).all()
    results = []
    for rack, count in rows:
        dto = RackResponse.model_validate(rack)
        dto.shelf_count = count
        results.append(dto)
    return results


@router.post("/aisles/{aisle_id}/racks", response_model=RackResponse, status_code=status.HTTP_201_CREATED)
async def create_rack(
    aisle_id: int,
    data: RackCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Create a rack in an aisle."""
    aisle = (await db.execute(select(Aisle).where(Aisle.id == aisle_id))).scalar_one_or_none()
    if not aisle:
        raise HTTPException(status_code=404, detail="Aisle not found")

    code = data.code.strip().upper()
    existing = await db.execute(select(Rack).where(Rack.aisle_id == aisle_id, Rack.code == code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Rack code already exists in this aisle")

    rack = Rack(
        aisle_id=aisle_id,
        code=code,
        name=data.name.strip(),
        description=data.description,
        is_active=data.is_active,
    )
    db.add(rack)
    await db.commit()
    await db.refresh(rack)
    return RackResponse.model_validate(rack)


# ─────────────────────────────────────────────────────────────
# SHELVES
# ─────────────────────────────────────────────────────────────
@router.get("/racks/{rack_id}/shelves", response_model=List[ShelfResponse])
async def list_shelves(rack_id: int, db: AsyncSession = Depends(get_db)):
    """List shelves in a rack."""
    query = (
        select(Shelf, func.count(StorageLocation.id).label("location_count"))
        .outerjoin(StorageLocation, Shelf.id == StorageLocation.shelf_id)
        .where(Shelf.rack_id == rack_id)
        .group_by(Shelf.id)
        .order_by(Shelf.code.asc())
    )
    rows = (await db.execute(query)).all()
    results = []
    for shelf, count in rows:
        dto = ShelfResponse.model_validate(shelf)
        dto.location_count = count
        results.append(dto)
    return results


@router.post("/racks/{rack_id}/shelves", response_model=ShelfResponse, status_code=status.HTTP_201_CREATED)
async def create_shelf(
    rack_id: int,
    data: ShelfCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Create a shelf in a rack."""
    rack = (await db.execute(select(Rack).where(Rack.id == rack_id))).scalar_one_or_none()
    if not rack:
        raise HTTPException(status_code=404, detail="Rack not found")

    code = data.code.strip().upper()
    existing = await db.execute(select(Shelf).where(Shelf.rack_id == rack_id, Shelf.code == code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Shelf code already exists in this rack")

    shelf = Shelf(
        rack_id=rack_id,
        code=code,
        name=data.name.strip(),
        description=data.description,
        is_active=data.is_active,
    )
    db.add(shelf)
    await db.commit()
    await db.refresh(shelf)
    return ShelfResponse.model_validate(shelf)


# ─────────────────────────────────────────────────────────────
# STORAGE LOCATIONS
# ─────────────────────────────────────────────────────────────
@router.get("/shelves/{shelf_id}/locations", response_model=List[StorageLocationResponse])
async def list_locations(shelf_id: int, db: AsyncSession = Depends(get_db)):
    """List storage locations in a shelf."""
    locations = (
        (await db.execute(select(StorageLocation).where(StorageLocation.shelf_id == shelf_id).order_by(StorageLocation.code.asc())))
        .scalars()
        .all()
    )
    return [StorageLocationResponse.model_validate(loc) for loc in locations]


@router.post("/shelves/{shelf_id}/locations", response_model=StorageLocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    shelf_id: int,
    data: StorageLocationCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Create a storage location in a shelf."""
    shelf = (await db.execute(select(Shelf).where(Shelf.id == shelf_id))).scalar_one_or_none()
    if not shelf:
        raise HTTPException(status_code=404, detail="Shelf not found")

    code = data.code.strip().upper()
    existing = await db.execute(select(StorageLocation).where(StorageLocation.shelf_id == shelf_id, StorageLocation.code == code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Location code already exists on this shelf")

    loc = StorageLocation(
        shelf_id=shelf_id,
        code=code,
        name=data.name.strip(),
        description=data.description,
        is_active=data.is_active,
    )
    db.add(loc)
    await db.commit()
    await db.refresh(loc)
    return StorageLocationResponse.model_validate(loc)


@router.get("/locations/search", response_model=List[LocationFullPath])
async def search_locations(
    query: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    """Search storage locations across the warehouse hierarchy."""
    filter_expr = f"%{query}%"
    stmt = (
        select(StorageLocation, Shelf, Rack, Aisle, Warehouse)
        .join(Shelf, StorageLocation.shelf_id == Shelf.id)
        .join(Rack, Shelf.rack_id == Rack.id)
        .join(Aisle, Rack.aisle_id == Aisle.id)
        .join(Warehouse, Aisle.warehouse_id == Warehouse.id)
        .where(
            (StorageLocation.code.ilike(filter_expr))
            | (StorageLocation.name.ilike(filter_expr))
            | (Warehouse.name.ilike(filter_expr))
        )
        .limit(30)
    )
    rows = (await db.execute(stmt)).all()

    results = []
    for loc, shelf, rack, aisle, wh in rows:
        full_path = f"{wh.code}-{aisle.code}-{rack.code}-{shelf.code}-{loc.code}"
        results.append(
            LocationFullPath(
                id=loc.id,
                code=loc.code,
                name=loc.name,
                full_path=full_path,
                warehouse_name=wh.name,
                aisle_name=aisle.name,
                rack_name=rack.name,
                shelf_name=shelf.name,
            )
        )
    return results


@router.get("/locations/{loc_id}", response_model=LocationFullPath)
async def get_location_path(loc_id: int, db: AsyncSession = Depends(get_db)):
    """Get location full path and hierarchy details."""
    stmt = (
        select(StorageLocation, Shelf, Rack, Aisle, Warehouse)
        .join(Shelf, StorageLocation.shelf_id == Shelf.id)
        .join(Rack, Shelf.rack_id == Rack.id)
        .join(Aisle, Rack.aisle_id == Aisle.id)
        .join(Warehouse, Aisle.warehouse_id == Warehouse.id)
        .where(StorageLocation.id == loc_id)
    )
    row = (await db.execute(stmt)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Location not found")

    loc, shelf, rack, aisle, wh = row
    full_path = f"{wh.code}-{aisle.code}-{rack.code}-{shelf.code}-{loc.code}"
    return LocationFullPath(
        id=loc.id,
        code=loc.code,
        name=loc.name,
        full_path=full_path,
        warehouse_name=wh.name,
        aisle_name=aisle.name,
        rack_name=rack.name,
        shelf_name=shelf.name,
    )

