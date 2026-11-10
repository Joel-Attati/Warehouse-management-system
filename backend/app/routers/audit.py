"""Audit log query router (Admin only)."""
import math
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import require_admin
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/audit", tags=["Audit"], dependencies=[Depends(require_admin)])


@router.get("", response_model=PaginatedResponse[AuditLogResponse])
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    action: Optional[str] = None,
    entity: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve immutable audit logs with flexible filtering."""
    query = select(AuditLog)

    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if username:
        query = query.where(AuditLog.username.ilike(f"%{username}%"))
    if action:
        query = query.where(AuditLog.action == action.upper())
    if entity:
        query = query.where(AuditLog.entity == entity)
    if date_from:
        query = query.where(AuditLog.created_at >= date_from)
    if date_to:
        query = query.where(AuditLog.created_at <= date_to)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(query)).scalars().all()

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedResponse(
        items=[AuditLogResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

