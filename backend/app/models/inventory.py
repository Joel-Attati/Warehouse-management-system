"""Inventory, batch, and stock movement models."""
from datetime import date, datetime
from enum import Enum
from typing import Optional
from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MovementType(str, Enum):
    RECEIVE = "RECEIVE"
    ISSUE = "ISSUE"
    TRANSFER = "TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_number: Mapped[str] = mapped_column(String(100), nullable=False)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    manufacture_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="batches")
    stocks: Mapped[list["InventoryStock"]] = relationship("InventoryStock", back_populates="batch")

    __table_args__ = (UniqueConstraint("product_id", "batch_number", name="uq_batch_product_number"),)


class InventoryStock(Base):
    __tablename__ = "inventory_stocks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("storage_locations.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("batches.id", ondelete="SET NULL"), nullable=True, index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    product: Mapped["Product"] = relationship("Product", back_populates="stocks")
    location: Mapped["StorageLocation"] = relationship("StorageLocation", back_populates="stocks")
    batch: Mapped[Optional["Batch"]] = relationship("Batch", back_populates="stocks")

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="chk_stock_quantity_non_negative"),
        UniqueConstraint("product_id", "location_id", "batch_id", name="uq_stock_product_loc_batch"),
    )


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    movement_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("batches.id", ondelete="SET NULL"), nullable=True, index=True)
    from_location_id: Mapped[Optional[int]] = mapped_column(ForeignKey("storage_locations.id", ondelete="SET NULL"), nullable=True, index=True)
    to_location_id: Mapped[Optional[int]] = mapped_column(ForeignKey("storage_locations.id", ondelete="SET NULL"), nullable=True, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    performed_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    product: Mapped["Product"] = relationship("Product")
    batch: Mapped[Optional["Batch"]] = relationship("Batch")
    from_location: Mapped[Optional["StorageLocation"]] = relationship("StorageLocation", foreign_keys=[from_location_id])
    to_location: Mapped[Optional["StorageLocation"]] = relationship("StorageLocation", foreign_keys=[to_location_id])
    user: Mapped["User"] = relationship("User")

