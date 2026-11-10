"""Audit logging helper."""
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def log_action(
    db: AsyncSession,
    user_id: Optional[int],
    username: str,
    action: str,
    entity: str,
    entity_id: Optional[str] = None,
    detail: Optional[Any] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """Insert an audit log entry."""
    entry = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        entity=entity,
        entity_id=str(entity_id) if entity_id is not None else None,
        detail=detail,
        ip_address=ip_address,
    )
    db.add(entry)
    await db.flush()
    return entry

