"""User management router (Admin only)."""
import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import require_admin
from app.models.user import User, UserRole
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.user import ResetPasswordRequest, UserCreate, UserResponse, UserUpdate
from app.utils.audit import log_action
from app.utils.password import hash_password

router = APIRouter(prefix="/users", tags=["Users"], dependencies=[Depends(require_admin)])


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List users with pagination and filtering."""
    query = select(User)

    if role:
        query = query.where(User.role == role.value)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if search:
        search_filter = f"%{search}%"
        query = query.where((User.username.ilike(search_filter)) | (User.email.ilike(search_filter)))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size)
    users = (await db.execute(query)).scalars().all()

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedResponse(
        items=users,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    request: Request,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user account."""
    # Check username / email uniqueness
    existing = await db.execute(
        select(User).where((User.username == data.username) | (User.email == data.email))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists",
        )

    user = User(
        username=data.username,
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        role=data.role.value,
        is_active=data.is_active,
    )
    db.add(user)
    await db.flush()

    client_ip = request.client.host if request.client else None
    await log_action(
        db=db,
        user_id=current_admin.id,
        username=current_admin.username,
        action="CREATE_USER",
        entity="User",
        entity_id=str(user.id),
        detail={"username": user.username, "role": user.role},
        ip_address=client_ip,
    )
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve user details by ID."""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    request: Request,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update user information and role."""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if data.email and data.email != user.email:
        existing = (await db.execute(select(User).where(User.email == data.email))).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        user.email = data.email

    if data.full_name is not None:
        user.full_name = data.full_name
    if data.role is not None:
        user.role = data.role.value
    if data.is_active is not None:
        if user_id == current_admin.id and not data.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot deactivate your own administrative account",
            )
        user.is_active = data.is_active

    client_ip = request.client.host if request.client else None
    await log_action(
        db=db,
        user_id=current_admin.id,
        username=current_admin.username,
        action="UPDATE_USER",
        entity="User",
        entity_id=str(user.id),
        detail=data.model_dump(exclude_unset=True),
        ip_address=client_ip,
    )
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    request: Request,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete user by setting is_active = False."""
    if user_id == current_admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate your own account")

    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = False
    client_ip = request.client.host if request.client else None
    await log_action(
        db=db,
        user_id=current_admin.id,
        username=current_admin.username,
        action="DEACTIVATE_USER",
        entity="User",
        entity_id=str(user.id),
        ip_address=client_ip,
    )
    await db.commit()
    return MessageResponse(message=f"User {user.username} deactivated")


@router.post("/{user_id}/reset-password", response_model=MessageResponse)
async def reset_password(
    user_id: int,
    data: ResetPasswordRequest,
    request: Request,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin reset of a user's password."""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.hashed_password = hash_password(data.new_password)
    client_ip = request.client.host if request.client else None
    await log_action(
        db=db,
        user_id=current_admin.id,
        username=current_admin.username,
        action="RESET_PASSWORD",
        entity="User",
        entity_id=str(user.id),
        ip_address=client_ip,
    )
    await db.commit()
    return MessageResponse(message=f"Password reset for {user.username}")

