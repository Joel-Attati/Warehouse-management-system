"""Authentication and authorization dependencies."""
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
try:
    import jwt
    from jwt.exceptions import PyJWTError as JWTError
except ImportError:
    from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a signed JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user(
    request: Request,
    token_header: Optional[str] = Depends(oauth2_scheme),
    access_token_cookie: Optional[str] = Cookie(default=None, alias="access_token"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate user from Bearer header or access_token cookie."""
    token = token_header or access_token_cookie
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: Optional[str] = payload.get("sub")
        token_type: Optional[str] = payload.get("type")
        if username is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Verify that current user account is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    return current_user


def require_roles(*allowed_roles: UserRole):
    """Factory dependency to enforce allowed role list."""
    allowed_values = [r.value for r in allowed_roles]

    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Requires role: {', '.join(allowed_values)}",
            )
        return current_user

    return role_checker


# Convenient role dependencies
require_admin = require_roles(UserRole.admin)
require_manager = require_roles(UserRole.admin, UserRole.manager)
require_staff = require_roles(UserRole.admin, UserRole.manager, UserRole.staff)

