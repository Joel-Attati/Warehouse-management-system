"""Seed rich, realistic operational sample data into the Warehouse Management System."""
import asyncio
from datetime import date, datetime, timedelta, timezone

from app.database import AsyncSessionLocal
from app.models.audit import AuditLog
from app.models.inventory import Batch, InventoryMovement, InventoryStock, MovementType
from app.models.product import Category, Product, ProductStatus
from app.models.user import User, UserRole
from app.models.warehouse import Aisle, Rack, Shelf, StorageLocation, Warehouse
from sqlalchemy import delete, select


async def seed():
    async with AsyncSessionLocal() as s:
        print("🌱 Seeding realistic warehouse dataset...")

        # 1. Clean existing transactional & catalog tables for fresh seed (preserves users)
        await s.execute(delete(AuditLog))
        await s.execute(delete(InventoryMovement))
        await s.execute(delete(InventoryStock))
        await s.execute(delete(Batch))
        await s.execute(delete(Product))
        await s.execute(delete(Category))
        await s.execute(delete(StorageLocation))
        await s.execute(delete(Shelf))
        await s.execute(delete(Rack))
        await s.execute(delete(Aisle))
        await s.execute(delete(Warehouse))
        await s.flush()

        # Get user references
        admin = (await s.execute(select(User).where(User.username == "admin"))).scalar_one()
        manager = (await s.execute(select(User).where(User.username == "manager"))).scalar_one()
        staff = (await s.execute(select(User).where(User.username == "staff"))).scalar_one()

        # 2. Warehouses & Hierarchies
        wh_main = Warehouse(
            code="WH-MAIN",
            name="Main Logistics Center",
            address="Building 4A, Gateway Logistics Zone",
            description="Primary fulfillment and dry goods storage facility",
        )
        wh_cold = Warehouse(
            code="WH-COLD",
            name="Cold Chain Storage Hub",
            address="Zone 2, Refrigerated Industrial Park",
            description="Temperature-controlled cold and deep-freeze warehouse",
        )
        s.add_all([wh_main, wh_cold])
        await s.flush()

        # Aisles in Main
        aisle1 = Aisle(warehouse_id=wh_main.id, code="A01", name="Electronics & Tech")
        aisle2 = Aisle(warehouse_id=wh_main.id, code="A02", name="Packaging & Supplies")
        # Aisle in Cold
        aisle_cold = Aisle(warehouse_id=wh_cold.id, code="C01", name="Perishables & Dairy")
        s.add_all([aisle1, aisle2, aisle_cold])
        await s.flush()

        # Racks
        rack_tech = Rack(aisle_id=aisle1.id, code="R01", name="Electronics Rack 1")
        rack_pkg = Rack(aisle_id=aisle2.id, code="R01", name="Pallet Rack Packaging")
        rack_fridge = Rack(aisle_id=aisle_cold.id, code="R01", name="Chilled Dairy Rack")
        s.add_all([rack_tech, rack_pkg, rack_fridge])
        await s.flush()

        # Shelves
        sh_tech1 = Shelf(rack_id=rack_tech.id, code="S01", name="Ground Tier")
        sh_tech2 = Shelf(rack_id=rack_tech.id, code="S02", name="Upper Tier")
        sh_pkg1 = Shelf(rack_id=rack_pkg.id, code="S01", name="Pallet Bay Ground")
        sh_cold1 = Shelf(rack_id=rack_fridge.id, code="S01", name="Chilled 4°C Tier")
        s.add_all([sh_tech1, sh_tech2, sh_pkg1, sh_cold1])
        await s.flush()

        # Storage Locations (Bins)
        loc_bin01 = StorageLocation(shelf_id=sh_tech1.id, code="BIN-101", name="Small Devices Bin 101")
        loc_bin02 = StorageLocation(shelf_id=sh_tech1.id, code="BIN-102", name="Cables & Accessories Bin 102")
        loc_bin03 = StorageLocation(shelf_id=sh_tech2.id, code="BIN-201", name="Docking Stations Bin 201")
        loc_pallet01 = StorageLocation(shelf_id=sh_pkg1.id, code="PAL-01", name="Box Pallet Floor Location")
        loc_pallet02 = StorageLocation(shelf_id=sh_pkg1.id, code="PAL-02", name="Label Rolls Location")
        loc_fridge01 = StorageLocation(shelf_id=sh_cold1.id, code="FRIDGE-01", name="Milk & Dairy Bin 1")
        loc_fridge02 = StorageLocation(shelf_id=sh_cold1.id, code="FRIDGE-02", name="Yogurt Bin 2")
        s.add_all([loc_bin01, loc_bin02, loc_bin03, loc_pallet01, loc_pallet02, loc_fridge01, loc_fridge02])
        await s.flush()

        # 3. Product Categories
        cat_elec = Category(name="Electronics & Scanners", description="Handheld terminals, scanners, docks")
        cat_cable = Category(name="Networking & Cables", description="CAT6, patch cords, adapters")
        cat_pkg = Category(name="Packaging & Materials", description="Shipping boxes, rolls, tape")
        cat_food = Category(name="Chilled Dairy & Beverages", description="Perishable grocery goods")
        s.add_all([cat_elec, cat_cable, cat_pkg, cat_food])
        await s.flush()

        # 4. Products (SKUs, Barcodes, Thresholds)
        prod_scanner = Product(
            sku="SCAN-BT-01",
            name="Wireless Bluetooth Barcode Scanner",
            category_id=cat_elec.id,
            unit="pcs",
            barcode="8901234567890",
            qr_code="QR-SCAN-BT01",
            min_stock=5,
            reorder_level=15,
            has_expiry=False,
            status=ProductStatus.active.value,
            description="Rugged 2D handheld imager with USB cradle",
        )
        prod_cable = Product(
            sku="CBL-CAT6-3M",
            name="CAT6 Shielded Ethernet Cable (3m)",
            category_id=cat_cable.id,
            unit="pcs",
            barcode="8901234567891",
            qr_code="QR-CAT6-3M",
            min_stock=20,
            reorder_level=50,  # Will have 14 in stock -> LOW STOCK ALERT!
            has_expiry=False,
            status=ProductStatus.active.value,
            description="Snagless Gigabit RJ45 patch cable",
        )
        prod_dock = Product(
            sku="LGT-DOCK-USB4",
            name="Universal USB4 Triple-Display Docking Station",
            category_id=cat_elec.id,
            unit="pcs",
            barcode="8901234567892",
            qr_code="QR-DOCK-U4",
            min_stock=10,
            reorder_level=25,
            has_expiry=False,
            status=ProductStatus.active.value,
            description="100W Power Delivery with dual HDMI and DP",
        )
        prod_box = Product(
            sku="PKG-BOX-MED",
            name="Corrugated Shipping Boxes (Medium 16x12x8)",
            category_id=cat_pkg.id,
            unit="bundle",
            barcode="8901234567895",
            qr_code="QR-BOX-MED",
            min_stock=40,
            reorder_level=80,  # Will have 18 in stock -> CRITICAL STOCK ALERT!
            has_expiry=False,
            status=ProductStatus.active.value,
            description="200 lb. test heavy-duty kraft shipping cartons",
        )
        prod_label = Product(
            sku="LBL-THERM-4X6",
            name="Direct Thermal Shipping Labels 4x6 Roll",
            category_id=cat_pkg.id,
            unit="roll",
            barcode="8901234567896",
            qr_code="QR-LBL-4X6",
            min_stock=15,
            reorder_level=30,
            has_expiry=False,
            status=ProductStatus.active.value,
            description="Perforated 500 labels per roll",
        )
        prod_milk = Product(
            sku="EXP-MILK-1L",
            name="Farm Fresh Organic Whole Milk 1L",
            category_id=cat_food.id,
            unit="carton",
            barcode="8901234567893",
            qr_code="QR-MILK-1L",
            min_stock=25,
            reorder_level=50,
            has_expiry=True,  # Will have lots expiring in 5 days -> EXPIRY ALERT!
            status=ProductStatus.active.value,
            description="Pasteurized grade-A chilled organic whole milk",
        )
        prod_yogurt = Product(
            sku="EXP-YOG-500G",
            name="Greek Strained Honey Yogurt 500g",
            category_id=cat_food.id,
            unit="tub",
            barcode="8901234567894",
            qr_code="QR-YOG-500",
            min_stock=10,
            reorder_level=25,
            has_expiry=True,  # Will have lot expiring in 12 days -> EXPIRY ALERT!
            status=ProductStatus.active.value,
            description="High protein chilled whole milk Greek yogurt",
        )
        s.add_all([prod_scanner, prod_cable, prod_dock, prod_box, prod_label, prod_milk, prod_yogurt])
        await s.flush()

        # 5. Batches (with realistic expiry dates)
        today = date.today()
        batch_milk_soon = Batch(
            product_id=prod_milk.id,
            batch_number="LOT-2026-MILK-URGENT",
            expiry_date=today + timedelta(days=5),  # 5 days left!
            manufacture_date=today - timedelta(days=9),
            notes="First received shipment. Rotate immediately.",
        )
        batch_milk_fresh = Batch(
            product_id=prod_milk.id,
            batch_number="LOT-2026-MILK-FRESH",
            expiry_date=today + timedelta(days=22),
            manufacture_date=today - timedelta(days=1),
            notes="Latest supply delivery.",
        )
        batch_yogurt = Batch(
            product_id=prod_yogurt.id,
            batch_number="LOT-2026-YOG-A12",
            expiry_date=today + timedelta(days=12),  # 12 days left!
            manufacture_date=today - timedelta(days=6),
            notes="Keep at 2°C - 4°C.",
        )
        s.add_all([batch_milk_soon, batch_milk_fresh, batch_yogurt])
        await s.flush()

        # 6. Physical Inventory Stock
        s.add_all([
            # Scanners: 42 pcs (healthy)
            InventoryStock(product_id=prod_scanner.id, location_id=loc_bin01.id, quantity=42),
            # Cables: 14 pcs (LOW STOCK alert: <= 50)
            InventoryStock(product_id=prod_cable.id, location_id=loc_bin02.id, quantity=14),
            # Docks: 35 pcs (healthy)
            InventoryStock(product_id=prod_dock.id, location_id=loc_bin03.id, quantity=35),
            # Boxes: 18 bundles (CRITICAL alert: <= 40)
            InventoryStock(product_id=prod_box.id, location_id=loc_pallet01.id, quantity=18),
            # Labels: 72 rolls (healthy)
            InventoryStock(product_id=prod_label.id, location_id=loc_pallet02.id, quantity=72),
            # Milk Batch 1 (Expiring in 5 days): 30 cartons
            InventoryStock(product_id=prod_milk.id, location_id=loc_fridge01.id, batch_id=batch_milk_soon.id, quantity=30),
            # Milk Batch 2 (Fresh): 65 cartons
            InventoryStock(product_id=prod_milk.id, location_id=loc_fridge01.id, batch_id=batch_milk_fresh.id, quantity=65),
            # Yogurt: 24 tubs
            InventoryStock(product_id=prod_yogurt.id, location_id=loc_fridge02.id, batch_id=batch_yogurt.id, quantity=24),
        ])
        await s.flush()

        # 7. Recent Movements Across Past 7 Days (populates Recharts trends & history)
        now = datetime.now(timezone.utc)
        movements = [
            # 6 days ago: Receive shipment of scanners & boxes
            InventoryMovement(
                movement_type=MovementType.RECEIVE.value,
                product_id=prod_scanner.id,
                to_location_id=loc_bin01.id,
                quantity=50,
                reference_number="PO-2026-8801",
                notes="Initial vendor shipment received",
                performed_by=staff.id,
                created_at=now - timedelta(days=6, hours=4),
            ),
            InventoryMovement(
                movement_type=MovementType.RECEIVE.value,
                product_id=prod_box.id,
                to_location_id=loc_pallet01.id,
                quantity=100,
                reference_number="PO-2026-8802",
                notes="Container shipment unload",
                performed_by=staff.id,
                created_at=now - timedelta(days=6, hours=2),
            ),
            # 5 days ago: Issue scanners & boxes for outbound orders
            InventoryMovement(
                movement_type=MovementType.ISSUE.value,
                product_id=prod_scanner.id,
                from_location_id=loc_bin01.id,
                quantity=8,
                reference_number="DO-2026-1044",
                notes="Fulfillment order for IT department",
                performed_by=staff.id,
                created_at=now - timedelta(days=5, hours=3),
            ),
            InventoryMovement(
                movement_type=MovementType.ISSUE.value,
                product_id=prod_box.id,
                from_location_id=loc_pallet01.id,
                quantity=40,
                reference_number="SO-2026-3011",
                notes="Dispatched to packaging department",
                performed_by=staff.id,
                created_at=now - timedelta(days=5, hours=1),
            ),
            # 4 days ago: Receive cables & docks
            InventoryMovement(
                movement_type=MovementType.RECEIVE.value,
                product_id=prod_cable.id,
                to_location_id=loc_bin02.id,
                quantity=30,
                reference_number="PO-2026-8910",
                notes="Delivery from cable supplier",
                performed_by=staff.id,
                created_at=now - timedelta(days=4, hours=5),
            ),
            InventoryMovement(
                movement_type=MovementType.RECEIVE.value,
                product_id=prod_dock.id,
                to_location_id=loc_bin03.id,
                quantity=40,
                reference_number="PO-2026-8912",
                notes="Docking stations inward inspection passed",
                performed_by=manager.id,
                created_at=now - timedelta(days=4, hours=3),
            ),
            # 3 days ago: Issue cables & transfer boxes
            InventoryMovement(
                movement_type=MovementType.ISSUE.value,
                product_id=prod_cable.id,
                from_location_id=loc_bin02.id,
                quantity=16,
                reference_number="REQ-NET-409",
                notes="Network deployment project phase 1",
                performed_by=staff.id,
                created_at=now - timedelta(days=3, hours=2),
            ),
            InventoryMovement(
                movement_type=MovementType.TRANSFER.value,
                product_id=prod_box.id,
                from_location_id=loc_pallet01.id,
                to_location_id=loc_pallet02.id,
                quantity=10,
                reference_number="RELOC-009",
                notes="Staging area consolidation",
                performed_by=staff.id,
                created_at=now - timedelta(days=3, hours=1),
            ),
            # 2 days ago: Receive milk & dairy lots
            InventoryMovement(
                movement_type=MovementType.RECEIVE.value,
                product_id=prod_milk.id,
                batch_id=batch_milk_soon.id,
                to_location_id=loc_fridge01.id,
                quantity=35,
                reference_number="COLD-IN-201",
                notes="Dairy farm direct delivery (Lot Urgent)",
                performed_by=staff.id,
                created_at=now - timedelta(days=2, hours=6),
            ),
            InventoryMovement(
                movement_type=MovementType.RECEIVE.value,
                product_id=prod_yogurt.id,
                batch_id=batch_yogurt.id,
                to_location_id=loc_fridge02.id,
                quantity=30,
                reference_number="COLD-IN-202",
                notes="Chilled yoghurt lot received",
                performed_by=staff.id,
                created_at=now - timedelta(days=2, hours=4),
            ),
            # 1 day ago: Issue yogurt & boxes
            InventoryMovement(
                movement_type=MovementType.ISSUE.value,
                product_id=prod_yogurt.id,
                batch_id=batch_yogurt.id,
                from_location_id=loc_fridge02.id,
                quantity=6,
                reference_number="DISP-CAF-01",
                notes="Cafeteria replenishment",
                performed_by=staff.id,
                created_at=now - timedelta(days=1, hours=3),
            ),
            InventoryMovement(
                movement_type=MovementType.ISSUE.value,
                product_id=prod_box.id,
                from_location_id=loc_pallet01.id,
                quantity=32,
                reference_number="DISP-OUT-99",
                notes="Peak dispatch volume packing",
                performed_by=staff.id,
                created_at=now - timedelta(days=1, hours=1),
            ),
            # Today: Receive milk & issue milk
            InventoryMovement(
                movement_type=MovementType.RECEIVE.value,
                product_id=prod_milk.id,
                batch_id=batch_milk_fresh.id,
                to_location_id=loc_fridge01.id,
                quantity=65,
                reference_number="COLD-IN-305",
                notes="Fresh morning milk intake",
                performed_by=staff.id,
                created_at=now - timedelta(hours=3),
            ),
            InventoryMovement(
                movement_type=MovementType.ISSUE.value,
                product_id=prod_milk.id,
                batch_id=batch_milk_soon.id,
                from_location_id=loc_fridge01.id,
                quantity=5,
                reference_number="PICK-FIFO-01",
                notes="FEFO pick for priority dispatch",
                performed_by=staff.id,
                created_at=now - timedelta(hours=1),
            ),
        ]
        s.add_all(movements)
        await s.flush()

        # 8. Audit Trail
        s.add_all([
            AuditLog(
                user_id=admin.id,
                username="admin",
                action="INITIALIZE_WAREHOUSE",
                entity="Warehouse",
                entity_id=str(wh_main.id),
                detail={"code": "WH-MAIN", "name": "Main Logistics Center"},
                ip_address="127.0.0.1",
                created_at=now - timedelta(days=6),
            ),
            AuditLog(
                user_id=manager.id,
                username="manager",
                action="REGISTER_CATALOG",
                entity="Product",
                entity_id=str(prod_scanner.id),
                detail={"sku": "SCAN-BT-01", "barcode": "8901234567890"},
                ip_address="192.168.1.15",
                created_at=now - timedelta(days=6),
            ),
            AuditLog(
                user_id=staff.id,
                username="staff",
                action="RECEIVE_STOCK",
                entity="InventoryMovement",
                entity_id="1",
                detail={"sku": "SCAN-BT-01", "qty": 50, "location": "BIN-101"},
                ip_address="192.168.1.42",
                created_at=now - timedelta(days=6),
            ),
            AuditLog(
                user_id=staff.id,
                username="staff",
                action="ISSUE_STOCK",
                entity="InventoryMovement",
                entity_id="2",
                detail={"sku": "PKG-BOX-MED", "qty": 40},
                ip_address="192.168.1.42",
                created_at=now - timedelta(days=5),
            ),
            AuditLog(
                user_id=staff.id,
                username="staff",
                action="LOGIN",
                entity="User",
                entity_id=str(staff.id),
                detail={"method": "password"},
                ip_address="192.168.1.42",
                created_at=now - timedelta(hours=2),
            ),
        ])
        await s.commit()

        print("✅ Sample database successfully populated with:")
        print("  - 2 Warehouses, 3 Aisles, 3 Racks, 4 Shelves, 7 Storage Bins")
        print("  - 4 Categories, 7 Products with Barcodes & QR codes")
        print("  - 3 Batches with Expiry Tracking")
        print("  - 8 Inventory Stock records (including Low Stock & Critical Minimum items)")
        print("  - 14 Historical Movements across the last 7 days (7-day activity graph ready)")
        print("  - 5 System Audit Log entries")


if __name__ == "__main__":
    asyncio.run(seed())

