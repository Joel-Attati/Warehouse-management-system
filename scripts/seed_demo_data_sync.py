"""Synchronous SQLite database populator for fast, reliable local seeding."""
import json
import sqlite3
import os
from datetime import date, datetime, timedelta, timezone

DB_PATH = r"E:\Warehouse Management System\backend\warehouse.db"

def seed():
    print(f"Connecting to {DB_PATH}...")
    con = sqlite3.connect(DB_PATH, timeout=10)
    cur = con.cursor()

    # Enable foreign keys
    cur.execute("PRAGMA foreign_keys = ON;")

    # 1. Clean existing transactional tables (keep users)
    print("Cleaning existing inventory and catalog tables...")
    cur.execute("DELETE FROM audit_logs;")
    cur.execute("DELETE FROM inventory_movements;")
    cur.execute("DELETE FROM inventory_stocks;")
    cur.execute("DELETE FROM batches;")
    cur.execute("DELETE FROM products;")
    cur.execute("DELETE FROM categories;")
    cur.execute("DELETE FROM storage_locations;")
    cur.execute("DELETE FROM shelves;")
    cur.execute("DELETE FROM racks;")
    cur.execute("DELETE FROM aisles;")
    cur.execute("DELETE FROM warehouses;")
    con.commit()

    # Get users
    cur.execute("SELECT id, username FROM users WHERE username IN ('admin', 'manager', 'staff');")
    users = {row[1]: row[0] for row in cur.fetchall()}
    admin_id = users.get('admin', 1)
    manager_id = users.get('manager', 2)
    staff_id = users.get('staff', 3)

    now = datetime.now(timezone.utc).isoformat()
    today = date.today()

    # 2. Warehouses
    print("Creating warehouses...")
    cur.execute("""
        INSERT INTO warehouses (code, name, address, description, is_active, created_at)
        VALUES 
        ('WH-MAIN', 'Main Logistics Center', 'Building 4A, Gateway Logistics Zone', 'Primary fulfillment and dry goods facility', 1, ?),
        ('WH-COLD', 'Cold Chain Storage Hub', 'Zone 2, Refrigerated Industrial Park', 'Temperature-controlled cold and deep-freeze warehouse', 1, ?)
    """, (now, now))
    wh_main_id = cur.execute("SELECT id FROM warehouses WHERE code = 'WH-MAIN'").fetchone()[0]
    wh_cold_id = cur.execute("SELECT id FROM warehouses WHERE code = 'WH-COLD'").fetchone()[0]

    # Aisles
    print("Creating aisles...")
    cur.execute("""
        INSERT INTO aisles (warehouse_id, code, name, description, is_active)
        VALUES 
        (?, 'A01', 'Electronics & Tech', 'Aisle 1 - Tech hardware', 1),
        (?, 'A02', 'Packaging & Supplies', 'Aisle 2 - Shipping cartons and materials', 1),
        (?, 'C01', 'Perishables & Dairy', 'Chilled dairy and beverage zone', 1)
    """, (wh_main_id, wh_main_id, wh_cold_id))
    aisle1_id = cur.execute("SELECT id FROM aisles WHERE warehouse_id = ? AND code = 'A01'", (wh_main_id,)).fetchone()[0]
    aisle2_id = cur.execute("SELECT id FROM aisles WHERE warehouse_id = ? AND code = 'A02'", (wh_main_id,)).fetchone()[0]
    aisle_cold_id = cur.execute("SELECT id FROM aisles WHERE warehouse_id = ? AND code = 'C01'", (wh_cold_id,)).fetchone()[0]

    # Racks
    print("Creating racks...")
    cur.execute("""
        INSERT INTO racks (aisle_id, code, name, description, is_active)
        VALUES 
        (?, 'R01', 'Electronics Rack 1', 'Heavy-duty steel rack for hardware', 1),
        (?, 'R01', 'Packaging Pallet Rack', 'Wide pallet rack for shipping materials', 1),
        (?, 'R01', 'Chilled Dairy Rack', 'Stainless steel refrigeration rack', 1)
    """, (aisle1_id, aisle2_id, aisle_cold_id))
    rack_tech_id = cur.execute("SELECT id FROM racks WHERE aisle_id = ? AND code = 'R01'", (aisle1_id,)).fetchone()[0]
    rack_pkg_id = cur.execute("SELECT id FROM racks WHERE aisle_id = ? AND code = 'R01'", (aisle2_id,)).fetchone()[0]
    rack_cold_id = cur.execute("SELECT id FROM racks WHERE aisle_id = ? AND code = 'R01'", (aisle_cold_id,)).fetchone()[0]

    # Shelves
    print("Creating shelves...")
    cur.execute("""
        INSERT INTO shelves (rack_id, code, name, description, is_active)
        VALUES 
        (?, 'S01', 'Ground Tier A', 'Ground accessible bin level', 1),
        (?, 'S02', 'Upper Tier B', 'Upper bin level', 1),
        (?, 'S01', 'Pallet Bay Ground', 'Direct floor storage bay', 1),
        (?, 'S01', 'Chilled 4C Tier', 'Climate controlled 4°C tier', 1)
    """, (rack_tech_id, rack_tech_id, rack_pkg_id, rack_cold_id))
    sh_tech1_id = cur.execute("SELECT id FROM shelves WHERE rack_id = ? AND code = 'S01'", (rack_tech_id,)).fetchone()[0]
    sh_tech2_id = cur.execute("SELECT id FROM shelves WHERE rack_id = ? AND code = 'S02'", (rack_tech_id,)).fetchone()[0]
    sh_pkg1_id = cur.execute("SELECT id FROM shelves WHERE rack_id = ? AND code = 'S01'", (rack_pkg_id,)).fetchone()[0]
    sh_cold1_id = cur.execute("SELECT id FROM shelves WHERE rack_id = ? AND code = 'S01'", (rack_cold_id,)).fetchone()[0]

    # Storage Locations (Bins)
    print("Creating storage locations...")
    cur.execute("""
        INSERT INTO storage_locations (shelf_id, code, name, description, is_active, created_at)
        VALUES 
        (?, 'BIN-101', 'Small Devices Bin 101', 'Bin for handheld scanners', 1, ?),
        (?, 'BIN-102', 'Cables Bin 102', 'Bin for networking cables', 1, ?),
        (?, 'BIN-201', 'Docking Stations Bin 201', 'Bin for triple-display docks', 1, ?),
        (?, 'PAL-01', 'Box Pallet Floor Location', 'Pallet space for medium shipping boxes', 1, ?),
        (?, 'PAL-02', 'Label Rolls Location', 'Pallet space for thermal label rolls', 1, ?),
        (?, 'FRIDGE-01', 'Milk & Dairy Bin 1', 'Chilled storage for fresh milk', 1, ?),
        (?, 'FRIDGE-02', 'Yogurt Bin 2', 'Chilled storage for Greek yogurt', 1, ?)
    """, (sh_tech1_id, now, sh_tech1_id, now, sh_tech2_id, now, sh_pkg1_id, now, sh_pkg1_id, now, sh_cold1_id, now, sh_cold1_id, now))

    loc_bin01_id = cur.execute("SELECT id FROM storage_locations WHERE code = 'BIN-101'").fetchone()[0]
    loc_bin02_id = cur.execute("SELECT id FROM storage_locations WHERE code = 'BIN-102'").fetchone()[0]
    loc_bin03_id = cur.execute("SELECT id FROM storage_locations WHERE code = 'BIN-201'").fetchone()[0]
    loc_pal01_id = cur.execute("SELECT id FROM storage_locations WHERE code = 'PAL-01'").fetchone()[0]
    loc_pal02_id = cur.execute("SELECT id FROM storage_locations WHERE code = 'PAL-02'").fetchone()[0]
    loc_fridge01_id = cur.execute("SELECT id FROM storage_locations WHERE code = 'FRIDGE-01'").fetchone()[0]
    loc_fridge02_id = cur.execute("SELECT id FROM storage_locations WHERE code = 'FRIDGE-02'").fetchone()[0]

    # 3. Categories
    print("Creating categories...")
    cur.execute("""
        INSERT INTO categories (name, description, created_at)
        VALUES 
        ('Electronics & Scanners', 'Handheld terminals, scanners, docks', ?),
        ('Networking & Cables', 'CAT6, patch cords, adapters', ?),
        ('Packaging & Materials', 'Shipping boxes, rolls, tape', ?),
        ('Chilled Dairy & Beverages', 'Perishable grocery goods', ?)
    """, (now, now, now, now))
    cat_elec_id = cur.execute("SELECT id FROM categories WHERE name = 'Electronics & Scanners'").fetchone()[0]
    cat_cable_id = cur.execute("SELECT id FROM categories WHERE name = 'Networking & Cables'").fetchone()[0]
    cat_pkg_id = cur.execute("SELECT id FROM categories WHERE name = 'Packaging & Materials'").fetchone()[0]
    cat_food_id = cur.execute("SELECT id FROM categories WHERE name = 'Chilled Dairy & Beverages'").fetchone()[0]

    # 4. Products
    print("Creating products...")
    products_data = [
        ("SCAN-BT-01", "Wireless Bluetooth Barcode Scanner", cat_elec_id, "pcs", "8901234567890", "QR-SCAN-BT01", 5, 15, 0, "active", "Rugged 2D handheld imager with USB cradle", now, now),
        ("CBL-CAT6-3M", "CAT6 Shielded Ethernet Cable (3m)", cat_cable_id, "pcs", "8901234567891", "QR-CAT6-3M", 20, 50, 0, "active", "Snagless Gigabit RJ45 patch cable (Low stock alert)", now, now),
        ("LGT-DOCK-USB4", "Universal USB4 Triple-Display Docking Station", cat_elec_id, "pcs", "8901234567892", "QR-DOCK-U4", 10, 25, 0, "active", "100W Power Delivery dual HDMI and DP", now, now),
        ("PKG-BOX-MED", "Corrugated Shipping Boxes (Medium 16x12x8)", cat_pkg_id, "bundle", "8901234567895", "QR-BOX-MED", 40, 80, 0, "active", "200 lb. test heavy-duty kraft shipping cartons (Critical stock alert)", now, now),
        ("LBL-THERM-4X6", "Direct Thermal Shipping Labels 4x6 Roll", cat_pkg_id, "roll", "8901234567896", "QR-LBL-4X6", 15, 30, 0, "active", "Perforated 500 labels per roll", now, now),
        ("EXP-MILK-1L", "Farm Fresh Organic Whole Milk 1L", cat_food_id, "carton", "8901234567893", "QR-MILK-1L", 25, 50, 1, "active", "Pasteurized grade-A chilled organic whole milk (Expiring soon alert)", now, now),
        ("EXP-YOG-500G", "Greek Strained Honey Yogurt 500g", cat_food_id, "tub", "8901234567894", "QR-YOG-500", 10, 25, 1, "active", "High protein chilled whole milk Greek yogurt (Expiring alert)", now, now),
    ]
    cur.executemany("""
        INSERT INTO products (sku, name, category_id, unit, barcode, qr_code, min_stock, reorder_level, has_expiry, status, description, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, products_data)

    prod_scanner_id = cur.execute("SELECT id FROM products WHERE sku = 'SCAN-BT-01'").fetchone()[0]
    prod_cable_id = cur.execute("SELECT id FROM products WHERE sku = 'CBL-CAT6-3M'").fetchone()[0]
    prod_dock_id = cur.execute("SELECT id FROM products WHERE sku = 'LGT-DOCK-USB4'").fetchone()[0]
    prod_box_id = cur.execute("SELECT id FROM products WHERE sku = 'PKG-BOX-MED'").fetchone()[0]
    prod_label_id = cur.execute("SELECT id FROM products WHERE sku = 'LBL-THERM-4X6'").fetchone()[0]
    prod_milk_id = cur.execute("SELECT id FROM products WHERE sku = 'EXP-MILK-1L'").fetchone()[0]
    prod_yogurt_id = cur.execute("SELECT id FROM products WHERE sku = 'EXP-YOG-500G'").fetchone()[0]

    # 5. Batches
    print("Creating batches...")
    exp_urgent = (today + timedelta(days=5)).isoformat()
    exp_fresh = (today + timedelta(days=22)).isoformat()
    exp_yog = (today + timedelta(days=12)).isoformat()
    mfg_milk = (today - timedelta(days=8)).isoformat()
    mfg_fresh = (today - timedelta(days=1)).isoformat()
    mfg_yog = (today - timedelta(days=5)).isoformat()

    cur.execute("""
        INSERT INTO batches (product_id, batch_number, expiry_date, manufacture_date, notes, created_at)
        VALUES 
        (?, 'LOT-2026-MILK-URGENT', ?, ?, 'Urgent rotation required - 5 days left', ?),
        (?, 'LOT-2026-MILK-FRESH', ?, ?, 'Fresh lot delivery', ?),
        (?, 'LOT-2026-YOG-A12', ?, ?, 'Keep cold at 2C to 4C - 12 days left', ?)
    """, (prod_milk_id, exp_urgent, mfg_milk, now,
          prod_milk_id, exp_fresh, mfg_fresh, now,
          prod_yogurt_id, exp_yog, mfg_yog, now))

    batch_milk_soon_id = cur.execute("SELECT id FROM batches WHERE batch_number = 'LOT-2026-MILK-URGENT'").fetchone()[0]
    batch_milk_fresh_id = cur.execute("SELECT id FROM batches WHERE batch_number = 'LOT-2026-MILK-FRESH'").fetchone()[0]
    batch_yogurt_id = cur.execute("SELECT id FROM batches WHERE batch_number = 'LOT-2026-YOG-A12'").fetchone()[0]

    # 6. Physical Inventory Stocks
    print("Creating inventory stock balances...")
    cur.execute("""
        INSERT INTO inventory_stocks (product_id, location_id, batch_id, quantity, last_updated)
        VALUES 
        (?, ?, NULL, 42, ?),
        (?, ?, NULL, 14, ?),
        (?, ?, NULL, 35, ?),
        (?, ?, NULL, 18, ?),
        (?, ?, NULL, 72, ?),
        (?, ?, ?, 30, ?),
        (?, ?, ?, 65, ?),
        (?, ?, ?, 24, ?)
    """, (
        prod_scanner_id, loc_bin01_id, now,
        prod_cable_id, loc_bin02_id, now,
        prod_dock_id, loc_bin03_id, now,
        prod_box_id, loc_pal01_id, now,
        prod_label_id, loc_pal02_id, now,
        prod_milk_id, loc_fridge01_id, batch_milk_soon_id, now,
        prod_milk_id, loc_fridge01_id, batch_milk_fresh_id, now,
        prod_yogurt_id, loc_fridge02_id, batch_yogurt_id, now
    ))

    # 7. Inventory Movements (spread across past 7 days)
    print("Creating historical movements across the past 7 days...")
    dt_now = datetime.now(timezone.utc)
    movements_data = [
        ("RECEIVE", prod_scanner_id, None, None, loc_bin01_id, 50, "PO-2026-8801", "Initial bulk vendor shipment received", staff_id, (dt_now - timedelta(days=6, hours=4)).isoformat()),
        ("RECEIVE", prod_box_id, None, None, loc_pal01_id, 100, "PO-2026-8802", "Container shipment unload", staff_id, (dt_now - timedelta(days=6, hours=2)).isoformat()),
        ("ISSUE", prod_scanner_id, None, loc_bin01_id, None, 8, "DO-2026-1044", "Fulfillment order for IT department", staff_id, (dt_now - timedelta(days=5, hours=3)).isoformat()),
        ("ISSUE", prod_box_id, None, loc_pal01_id, None, 40, "SO-2026-3011", "Dispatched to packaging department", staff_id, (dt_now - timedelta(days=5, hours=1)).isoformat()),
        ("RECEIVE", prod_cable_id, None, None, loc_bin02_id, 30, "PO-2026-8910", "Delivery from cable supplier", staff_id, (dt_now - timedelta(days=4, hours=5)).isoformat()),
        ("RECEIVE", prod_dock_id, None, None, loc_bin03_id, 40, "PO-2026-8912", "Docking stations inward inspection passed", manager_id, (dt_now - timedelta(days=4, hours=3)).isoformat()),
        ("ISSUE", prod_cable_id, None, loc_bin02_id, None, 16, "REQ-NET-409", "Network deployment project phase 1", staff_id, (dt_now - timedelta(days=3, hours=2)).isoformat()),
        ("TRANSFER", prod_box_id, None, loc_pal01_id, loc_pal02_id, 10, "RELOC-009", "Staging area consolidation", staff_id, (dt_now - timedelta(days=3, hours=1)).isoformat()),
        ("RECEIVE", prod_milk_id, batch_milk_soon_id, None, loc_fridge01_id, 35, "COLD-IN-201", "Dairy farm direct delivery (Lot Urgent)", staff_id, (dt_now - timedelta(days=2, hours=6)).isoformat()),
        ("RECEIVE", prod_yogurt_id, batch_yogurt_id, None, loc_fridge02_id, 30, "COLD-IN-202", "Chilled yoghurt lot received", staff_id, (dt_now - timedelta(days=2, hours=4)).isoformat()),
        ("ISSUE", prod_yogurt_id, batch_yogurt_id, loc_fridge02_id, None, 6, "DISP-CAF-01", "Cafeteria replenishment pick", staff_id, (dt_now - timedelta(days=1, hours=3)).isoformat()),
        ("ISSUE", prod_box_id, None, loc_pal01_id, None, 32, "DISP-OUT-99", "Peak dispatch volume packing", staff_id, (dt_now - timedelta(days=1, hours=1)).isoformat()),
        ("RECEIVE", prod_milk_id, batch_milk_fresh_id, None, loc_fridge01_id, 65, "COLD-IN-305", "Fresh morning milk intake", staff_id, (dt_now - timedelta(hours=3)).isoformat()),
        ("ISSUE", prod_milk_id, batch_milk_soon_id, loc_fridge01_id, None, 5, "PICK-FIFO-01", "FEFO pick for priority dispatch", staff_id, (dt_now - timedelta(hours=1)).isoformat()),
    ]
    cur.executemany("""
        INSERT INTO inventory_movements (movement_type, product_id, batch_id, from_location_id, to_location_id, quantity, reference_number, notes, performed_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, movements_data)

    # 8. Audit Logs
    print("Creating audit logs...")
    audit_data = [
        (admin_id, "admin", "INITIALIZE_WAREHOUSE", "Warehouse", str(wh_main_id), json.dumps({"code": "WH-MAIN", "name": "Main Logistics Center"}), "127.0.0.1", (dt_now - timedelta(days=6)).isoformat()),
        (manager_id, "manager", "REGISTER_CATALOG", "Product", str(prod_scanner_id), json.dumps({"sku": "SCAN-BT-01", "barcode": "8901234567890"}), "192.168.1.15", (dt_now - timedelta(days=6)).isoformat()),
        (staff_id, "staff", "RECEIVE_STOCK", "InventoryMovement", "1", json.dumps({"sku": "SCAN-BT-01", "qty": 50, "location": "BIN-101"}), "192.168.1.42", (dt_now - timedelta(days=6)).isoformat()),
        (staff_id, "staff", "ISSUE_STOCK", "InventoryMovement", "2", json.dumps({"sku": "PKG-BOX-MED", "qty": 40}), "192.168.1.42", (dt_now - timedelta(days=5)).isoformat()),
        (staff_id, "staff", "LOGIN", "User", str(staff_id), json.dumps({"method": "password"}), "192.168.1.42", (dt_now - timedelta(hours=2)).isoformat()),
    ]
    cur.executemany("""
        INSERT INTO audit_logs (user_id, username, action, entity, entity_id, detail, ip_address, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, audit_data)

    con.commit()
    print("Database committed successfully.")

    # Verification count
    print("\n--- Seed Verification ---")
    for tbl in ["users", "warehouses", "aisles", "racks", "shelves", "storage_locations", "categories", "products", "batches", "inventory_stocks", "inventory_movements", "audit_logs"]:
        count = cur.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"  {tbl:<22}: {count} records")

    con.close()

if __name__ == "__main__":
    seed()

