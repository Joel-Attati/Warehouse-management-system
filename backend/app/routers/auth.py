"""Authentication router."""
from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
try:
    import jwt
    from jwt.exceptions import PyJWTError as JWTError
except ImportError:
    from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies.auth import (
    create_access_token,
    create_refresh_token,
    get_current_active_user,
    get_current_user,
)
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.user import ChangePasswordRequest, LoginRequest, Token, UserResponse
from app.utils.audit import log_action
from app.utils.password import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user with username and password, setting secure httpOnly cookies."""
    stmt = select(User).where(User.username == login_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    refresh_token = create_refresh_token(data={"sub": user.username})

    # Set httpOnly cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=False,  # Suitable for local LAN HTTP
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )

    client_ip = request.client.host if request.client else None
    await log_action(
        db=db,
        user_id=user.id,
        username=user.username,
        action="LOGIN",
        entity="User",
        entity_id=str(user.id),
        ip_address=client_ip,
    )
    await db.commit()

    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        username=user.username,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Clear session cookies."""
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

    if current_user:
        client_ip = request.client.host if request.client else None
        await log_action(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            action="LOGOUT",
            entity="User",
            entity_id=str(current_user.id),
            ip_address=client_ip,
        )
        await db.commit()

    return MessageResponse(message="Successfully logged out")


@router.post("/refresh", response_model=Token)
async def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new access token using the refresh token cookie."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        if not username or token_type != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    new_access_token = create_access_token(data={"sub": user.username, "role": user.role})
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return Token(
        access_token=new_access_token,
        token_type="bearer",
        role=user.role,
        username=user.username,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Return the profile of the authenticated user."""
    return current_user


@router.post("/me/change-password", response_model=MessageResponse)
async def change_password(
    data: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the authenticated user's password."""
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    current_user.hashed_password = hash_password(data.new_password)
    client_ip = request.client.host if request.client else None
    await log_action(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="CHANGE_PASSWORD",
        entity="User",
        entity_id=str(current_user.id),
        ip_address=client_ip,
    )
    await db.commit()
    return MessageResponse(message="Password successfully updated")

