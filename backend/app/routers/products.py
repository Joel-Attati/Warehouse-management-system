"""Product and category management router."""
import math
from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_active_user, require_manager
from app.models.inventory import InventoryStock
from app.models.product import Category, Product, ProductStatus
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.product import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    ProductCreate,
    ProductListItem,
    ProductResponse,
    ProductUpdate,
)
from app.utils.audit import log_action
from app.utils.files import delete_file, save_upload_file

router = APIRouter(prefix="/products", tags=["Products"], dependencies=[Depends(get_current_active_user)])


# ─────────────────────────────────────────────────────────────
# CATEGORIES
# ─────────────────────────────────────────────────────────────
@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    """List all product categories."""
    query = (
        select(Category, func.count(Product.id).label("product_count"))
        .outerjoin(Product, Category.id == Product.category_id)
        .group_by(Category.id)
        .order_by(Category.name.asc())
    )
    rows = (await db.execute(query)).all()
    results = []
    for cat, count in rows:
        dto = CategoryResponse.model_validate(cat)
        dto.product_count = count
        results.append(dto)
    return results


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Create a new category."""
    existing = await db.execute(select(Category).where(Category.name == data.name.strip()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Category with this name already exists")

    cat = Category(name=data.name.strip(), description=data.description)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return CategoryResponse.model_validate(cat)


@router.put("/categories/{cat_id}", response_model=CategoryResponse)
async def update_category(
    cat_id: int,
    data: CategoryUpdate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Update category."""
    cat = (await db.execute(select(Category).where(Category.id == cat_id))).scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    if data.name:
        cat.name = data.name.strip()
    if data.description is not None:
        cat.description = data.description
    await db.commit()
    await db.refresh(cat)
    return CategoryResponse.model_validate(cat)


@router.delete("/categories/{cat_id}", response_model=MessageResponse)
async def delete_category(
    cat_id: int,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Delete category."""
    cat = (await db.execute(select(Category).where(Category.id == cat_id))).scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    await db.delete(cat)
    await db.commit()
    return MessageResponse(message="Category deleted")


# ─────────────────────────────────────────────────────────────
# PRODUCTS
# ─────────────────────────────────────────────────────────────
@router.get("", response_model=PaginatedResponse[ProductListItem])
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    status: Optional[ProductStatus] = None,
    low_stock_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """List products with pagination, search, and stock level computation."""
    stock_subq = (
        select(
            InventoryStock.product_id,
            func.coalesce(func.sum(InventoryStock.quantity), 0).label("total_stock"),
        )
        .group_by(InventoryStock.product_id)
        .subquery()
    )

    query = (
        select(
            Product,
            Category.name.label("category_name"),
            func.coalesce(stock_subq.c.total_stock, 0).label("total_stock"),
        )
        .outerjoin(Category, Product.category_id == Category.id)
        .outerjoin(stock_subq, Product.id == stock_subq.c.product_id)
    )

    if search:
        s = f"%{search}%"
        query = query.where(
            (Product.sku.ilike(s))
            | (Product.name.ilike(s))
            | (Product.barcode.ilike(s))
        )
    if category_id:
        query = query.where(Product.category_id == category_id)
    if status:
        query = query.where(Product.status == status.value)
    if low_stock_only:
        query = query.where(func.coalesce(stock_subq.c.total_stock, 0) <= Product.reorder_level)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(Product.name.asc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(query)).all()

    items = []
    for prod, cat_name, total_stock in rows:
        items.append(
            ProductListItem(
                id=prod.id,
                sku=prod.sku,
                name=prod.name,
                category_id=prod.category_id,
                category_name=cat_name,
                unit=prod.unit,
                barcode=prod.barcode,
                min_stock=prod.min_stock,
                reorder_level=prod.reorder_level,
                has_expiry=prod.has_expiry,
                status=ProductStatus(prod.status),
                image_path=prod.image_path,
                total_stock=total_stock,
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


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    request: Request,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Register a new product."""
    sku = data.sku.strip().upper()
    existing_sku = await db.execute(select(Product).where(Product.sku == sku))
    if existing_sku.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="SKU already exists")

    if data.barcode:
        existing_bc = await db.execute(select(Product).where(Product.barcode == data.barcode.strip()))
        if existing_bc.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Barcode already assigned to another product")

    prod = Product(
        sku=sku,
        name=data.name.strip(),
        category_id=data.category_id,
        unit=data.unit,
        barcode=data.barcode.strip() if data.barcode else None,
        qr_code=data.qr_code.strip() if data.qr_code else None,
        min_stock=data.min_stock,
        reorder_level=data.reorder_level,
        has_expiry=data.has_expiry,
        status=data.status.value,
        description=data.description,
    )
    db.add(prod)
    await db.flush()

    client_ip = request.client.host if request.client else None
    await log_action(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE_PRODUCT",
        entity="Product",
        entity_id=str(prod.id),
        detail={"sku": prod.sku, "name": prod.name},
        ip_address=client_ip,
    )
    await db.commit()
    await db.refresh(prod)

    res = ProductResponse.model_validate(prod)
    return res


@router.get("/barcode/{barcode}", response_model=ProductResponse)
async def lookup_by_barcode(barcode: str, db: AsyncSession = Depends(get_db)):
    """Lookup product details by scanned barcode or QR code."""
    query = (
        select(Product, Category.name.label("category_name"))
        .outerjoin(Category, Product.category_id == Category.id)
        .where((Product.barcode == barcode.strip()) | (Product.qr_code == barcode.strip()))
    )
    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found with scanned code")

    prod, cat_name = row
    total_stock = (
        await db.execute(
            select(func.coalesce(func.sum(InventoryStock.quantity), 0)).where(InventoryStock.product_id == prod.id)
        )
    ).scalar_one()

    res = ProductResponse.model_validate(prod)
    res.category_name = cat_name
    res.total_stock = total_stock
    return res


@router.get("/sku/{sku}", response_model=ProductResponse)
async def lookup_by_sku(sku: str, db: AsyncSession = Depends(get_db)):
    """Lookup product details by exact SKU."""
    query = (
        select(Product, Category.name.label("category_name"))
        .outerjoin(Category, Product.category_id == Category.id)
        .where(Product.sku == sku.strip().upper())
    )
    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found with SKU")

    prod, cat_name = row
    total_stock = (
        await db.execute(
            select(func.coalesce(func.sum(InventoryStock.quantity), 0)).where(InventoryStock.product_id == prod.id)
        )
    ).scalar_one()

    res = ProductResponse.model_validate(prod)
    res.category_name = cat_name
    res.total_stock = total_stock
    return res


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve full product detail including total stock."""
    query = (
        select(Product, Category.name.label("category_name"))
        .outerjoin(Category, Product.category_id == Category.id)
        .where(Product.id == product_id)
    )
    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")

    prod, cat_name = row
    total_stock = (
        await db.execute(
            select(func.coalesce(func.sum(InventoryStock.quantity), 0)).where(InventoryStock.product_id == prod.id)
        )
    ).scalar_one()

    res = ProductResponse.model_validate(prod)
    res.category_name = cat_name
    res.total_stock = total_stock
    return res


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    request: Request,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Update product information."""
    prod = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    if data.name is not None:
        prod.name = data.name.strip()
    if data.category_id is not None:
        prod.category_id = data.category_id
    if data.unit is not None:
        prod.unit = data.unit
    if data.barcode is not None:
        prod.barcode = data.barcode.strip() if data.barcode else None
    if data.qr_code is not None:
        prod.qr_code = data.qr_code.strip() if data.qr_code else None
    if data.min_stock is not None:
        prod.min_stock = data.min_stock
    if data.reorder_level is not None:
        prod.reorder_level = data.reorder_level
    if data.has_expiry is not None:
        prod.has_expiry = data.has_expiry
    if data.status is not None:
        prod.status = data.status.value
    if data.description is not None:
        prod.description = data.description

    client_ip = request.client.host if request.client else None
    await log_action(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE_PRODUCT",
        entity="Product",
        entity_id=str(prod.id),
        detail=data.model_dump(exclude_unset=True),
        ip_address=client_ip,
    )
    await db.commit()
    await db.refresh(prod)
    return ProductResponse.model_validate(prod)


@router.delete("/{product_id}", response_model=MessageResponse)
async def delete_product(
    product_id: int,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate product (soft-delete)."""
    prod = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    prod.status = ProductStatus.inactive.value
    await db.commit()
    return MessageResponse(message=f"Product {prod.sku} set to inactive")


@router.post("/{product_id}/image", response_model=ProductResponse)
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    request: Request = None,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Upload or replace product image."""
    prod = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    # Delete old image if present
    if prod.image_path:
        await delete_file(prod.image_path)

    relative_path = await save_upload_file(file, subfolder="products")
    prod.image_path = relative_path

    client_ip = request.client.host if request and request.client else None
    await log_action(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="UPLOAD_IMAGE",
        entity="Product",
        entity_id=str(prod.id),
        detail={"image_path": relative_path},
        ip_address=client_ip,
    )
    await db.commit()
    await db.refresh(prod)
    return ProductResponse.model_validate(prod)


@router.delete("/{product_id}/image", response_model=MessageResponse)
async def remove_product_image(
    product_id: int,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Remove product image."""
    prod = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    if prod.image_path:
        await delete_file(prod.image_path)
        prod.image_path = None
        await db.commit()

    return MessageResponse(message="Image removed successfully")

