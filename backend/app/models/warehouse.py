"""Warehouse hierarchy models."""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    aisles: Mapped[List["Aisle"]] = relationship("Aisle", back_populates="warehouse", cascade="all, delete-orphan")


class Aisle(Base):
    __tablename__ = "aisles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="aisles")
    racks: Mapped[List["Rack"]] = relationship("Rack", back_populates="aisle", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("warehouse_id", "code", name="uq_aisle_warehouse_code"),)


class Rack(Base):
    __tablename__ = "racks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    aisle_id: Mapped[int] = mapped_column(ForeignKey("aisles.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    aisle: Mapped["Aisle"] = relationship("Aisle", back_populates="racks")
    shelves: Mapped[List["Shelf"]] = relationship("Shelf", back_populates="rack", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("aisle_id", "code", name="uq_rack_aisle_code"),)


class Shelf(Base):
    __tablename__ = "shelves"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    rack_id: Mapped[int] = mapped_column(ForeignKey("racks.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    rack: Mapped["Rack"] = relationship("Rack", back_populates="shelves")
    locations: Mapped[List["StorageLocation"]] = relationship("StorageLocation", back_populates="shelf", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("rack_id", "code", name="uq_shelf_rack_code"),)


class StorageLocation(Base):
    __tablename__ = "storage_locations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    shelf_id: Mapped[int] = mapped_column(ForeignKey("shelves.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    shelf: Mapped["Shelf"] = relationship("Shelf", back_populates="locations")
    stocks: Mapped[List["InventoryStock"]] = relationship("InventoryStock", back_populates="location")

    __table_args__ = (UniqueConstraint("shelf_id", "code", name="uq_location_shelf_code"),)

