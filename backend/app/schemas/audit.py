"""Audit log schemas."""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: str
    action: str
    entity: str
    entity_id: Optional[str] = None
    detail: Optional[Any] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

