"""Warehouse hierarchy schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# --- Warehouse ---
class WarehouseBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class WarehouseResponse(WarehouseBase):
    id: int
    created_at: datetime
    aisle_count: Optional[int] = 0

    class Config:
        from_attributes = True


# --- Aisle ---
class AisleBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: bool = True


class AisleCreate(AisleBase):
    pass


class AisleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class AisleResponse(AisleBase):
    id: int
    warehouse_id: int
    rack_count: Optional[int] = 0

    class Config:
        from_attributes = True


# --- Rack ---
class RackBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: bool = True


class RackCreate(RackBase):
    pass


class RackUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RackResponse(RackBase):
    id: int
    aisle_id: int
    shelf_count: Optional[int] = 0

    class Config:
        from_attributes = True


# --- Shelf ---
class ShelfBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: bool = True


class ShelfCreate(ShelfBase):
    pass


class ShelfUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ShelfResponse(ShelfBase):
    id: int
    rack_id: int
    location_count: Optional[int] = 0

    class Config:
        from_attributes = True


# --- Storage Location ---
class StorageLocationBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: bool = True


class StorageLocationCreate(StorageLocationBase):
    pass


class StorageLocationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class StorageLocationResponse(StorageLocationBase):
    id: int
    shelf_id: int
    created_at: datetime
    full_path: Optional[str] = None

    class Config:
        from_attributes = True


class LocationFullPath(BaseModel):
    id: int
    code: str
    name: str
    full_path: str
    warehouse_name: str
    aisle_name: str
    rack_name: str
    shelf_name: str

    class Config:
        from_attributes = True

