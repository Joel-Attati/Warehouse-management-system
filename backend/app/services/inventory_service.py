"""Inventory movement business logic with atomic database transactions."""
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import Batch, InventoryMovement, InventoryStock, MovementType
from app.models.product import Product
from app.models.warehouse import StorageLocation
from app.schemas.inventory import IssueStockRequest, ReceiveStockRequest, TransferStockRequest
from app.utils.audit import log_action


class InventoryService:
    @staticmethod
    def _apply_lock(stmt, db: AsyncSession):
        try:
            bind = db.bind
            if bind and getattr(bind.dialect, "name", "") != "sqlite":
                return stmt.with_for_update()
        except Exception:
            pass
        return stmt

    @staticmethod
    async def receive_stock(
        db: AsyncSession,
        data: ReceiveStockRequest,
        user_id: int,
        username: str,
        ip_address: Optional[str] = None,
    ) -> InventoryMovement:
        """Receive inventory into a storage location atomically."""
        # 1. Verify product exists and is active
        prod_res = await db.execute(select(Product).where(Product.id == data.product_id))
        product = prod_res.scalar_one_or_none()
        if not product or product.status != "active":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active product not found")

        # 2. Verify storage location exists and is active
        loc_res = await db.execute(select(StorageLocation).where(StorageLocation.id == data.location_id))
        location = loc_res.scalar_one_or_none()
        if not location or not location.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active storage location not found")

        # 3. Handle batch if provided
        batch_id: Optional[int] = None
        if data.batch_number:
            batch_res = await db.execute(
                select(Batch).where(
                    Batch.product_id == data.product_id,
                    Batch.batch_number == data.batch_number.strip(),
                )
            )
            batch = batch_res.scalar_one_or_none()
            if not batch:
                batch = Batch(
                    product_id=data.product_id,
                    batch_number=data.batch_number.strip(),
                    expiry_date=data.expiry_date,
                    manufacture_date=data.manufacture_date,
                    notes=data.notes,
                )
                db.add(batch)
                await db.flush()
            batch_id = batch.id

        # 4. Lock and update or create InventoryStock
        stock_stmt = (
            select(InventoryStock)
            .where(
                InventoryStock.product_id == data.product_id,
                InventoryStock.location_id == data.location_id,
                InventoryStock.batch_id == batch_id,
            )
        )
        stock_stmt = InventoryService._apply_lock(stock_stmt, db)
        stock_res = await db.execute(stock_stmt)
        stock = stock_res.scalar_one_or_none()

        if stock:
            stock.quantity += data.quantity
        else:
            stock = InventoryStock(
                product_id=data.product_id,
                location_id=data.location_id,
                batch_id=batch_id,
                quantity=data.quantity,
            )
            db.add(stock)

        # 5. Record movement
        movement = InventoryMovement(
            movement_type=MovementType.RECEIVE.value,
            product_id=data.product_id,
            batch_id=batch_id,
            from_location_id=None,
            to_location_id=data.location_id,
            quantity=data.quantity,
            reference_number=data.reference_number,
            notes=data.notes,
            performed_by=user_id,
        )
        db.add(movement)
        await db.flush()

        # 6. Audit log
        await log_action(
            db=db,
            user_id=user_id,
            username=username,
            action="RECEIVE_STOCK",
            entity="InventoryMovement",
            entity_id=str(movement.id),
            detail={
                "product_id": data.product_id,
                "sku": product.sku,
                "location_id": data.location_id,
                "quantity": data.quantity,
                "batch_id": batch_id,
                "reference": data.reference_number,
            },
            ip_address=ip_address,
        )

        return movement

    @staticmethod
    async def issue_stock(
        db: AsyncSession,
        data: IssueStockRequest,
        user_id: int,
        username: str,
        ip_address: Optional[str] = None,
    ) -> InventoryMovement:
        """Issue inventory from a storage location atomically."""
        # 1. Verify product
        prod_res = await db.execute(select(Product).where(Product.id == data.product_id))
        product = prod_res.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        # 2. Lock source stock
        stock_stmt = (
            select(InventoryStock)
            .where(
                InventoryStock.product_id == data.product_id,
                InventoryStock.location_id == data.location_id,
                InventoryStock.batch_id == data.batch_id,
            )
        )
        stock_stmt = InventoryService._apply_lock(stock_stmt, db)
        stock_res = await db.execute(stock_stmt)
        stock = stock_res.scalar_one_or_none()

        if not stock or stock.quantity < data.quantity:
            avail = stock.quantity if stock else 0
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock at location. Available: {avail}, requested: {data.quantity}",
            )

        # 3. Deduct stock
        stock.quantity -= data.quantity

        # 4. Record movement
        movement = InventoryMovement(
            movement_type=MovementType.ISSUE.value,
            product_id=data.product_id,
            batch_id=data.batch_id,
            from_location_id=data.location_id,
            to_location_id=None,
            quantity=data.quantity,
            reference_number=data.reference_number,
            notes=data.notes,
            performed_by=user_id,
        )
        db.add(movement)
        await db.flush()

        # 5. Audit log
        await log_action(
            db=db,
            user_id=user_id,
            username=username,
            action="ISSUE_STOCK",
            entity="InventoryMovement",
            entity_id=str(movement.id),
            detail={
                "product_id": data.product_id,
                "sku": product.sku,
                "location_id": data.location_id,
                "quantity": data.quantity,
                "batch_id": data.batch_id,
                "reference": data.reference_number,
            },
            ip_address=ip_address,
        )

        return movement

    @staticmethod
    async def transfer_stock(
        db: AsyncSession,
        data: TransferStockRequest,
        user_id: int,
        username: str,
        ip_address: Optional[str] = None,
    ) -> InventoryMovement:
        """Transfer inventory between locations atomically."""
        if data.from_location_id == data.to_location_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source and destination locations cannot be identical",
            )

        # 1. Verify product
        prod_res = await db.execute(select(Product).where(Product.id == data.product_id))
        product = prod_res.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        # 2. Verify destination location exists
        dest_res = await db.execute(select(StorageLocation).where(StorageLocation.id == data.to_location_id))
        dest_loc = dest_res.scalar_one_or_none()
        if not dest_loc or not dest_loc.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination location not found or inactive")

        # 3. Lock source stock
        src_stmt = (
            select(InventoryStock)
            .where(
                InventoryStock.product_id == data.product_id,
                InventoryStock.location_id == data.from_location_id,
                InventoryStock.batch_id == data.batch_id,
            )
        )
        src_stmt = InventoryService._apply_lock(src_stmt, db)
        src_res = await db.execute(src_stmt)
        src_stock = src_res.scalar_one_or_none()

        if not src_stock or src_stock.quantity < data.quantity:
            avail = src_stock.quantity if src_stock else 0
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock at source location. Available: {avail}, requested: {data.quantity}",
            )

        # 4. Lock or create destination stock
        dest_stmt = (
            select(InventoryStock)
            .where(
                InventoryStock.product_id == data.product_id,
                InventoryStock.location_id == data.to_location_id,
                InventoryStock.batch_id == data.batch_id,
            )
        )
        dest_stmt = InventoryService._apply_lock(dest_stmt, db)
        dest_res = await db.execute(dest_stmt)
        dest_stock = dest_res.scalar_one_or_none()

        # 5. Move quantities
        src_stock.quantity -= data.quantity
        if dest_stock:
            dest_stock.quantity += data.quantity
        else:
            dest_stock = InventoryStock(
                product_id=data.product_id,
                location_id=data.to_location_id,
                batch_id=data.batch_id,
                quantity=data.quantity,
            )
            db.add(dest_stock)

        # 6. Record movement
        movement = InventoryMovement(
            movement_type=MovementType.TRANSFER.value,
            product_id=data.product_id,
            batch_id=data.batch_id,
            from_location_id=data.from_location_id,
            to_location_id=data.to_location_id,
            quantity=data.quantity,
            reference_number=data.reference_number,
            notes=data.notes,
            performed_by=user_id,
        )
        db.add(movement)
        await db.flush()

        # 7. Audit log
        await log_action(
            db=db,
            user_id=user_id,
            username=username,
            action="TRANSFER_STOCK",
            entity="InventoryMovement",
            entity_id=str(movement.id),
            detail={
                "product_id": data.product_id,
                "sku": product.sku,
                "from_location_id": data.from_location_id,
                "to_location_id": data.to_location_id,
                "quantity": data.quantity,
                "batch_id": data.batch_id,
                "reference": data.reference_number,
            },
            ip_address=ip_address,
        )

        return movement

