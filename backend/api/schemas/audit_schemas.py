from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel

class AuditLogOut(BaseModel):
    id: UUID
    tenant_id: UUID
    action: str
    entity_type: str
    entity_id: UUID
    actor_user_id: Optional[UUID] = None
    actor_name: Optional[str] = None
    correlation_id: Optional[str] = None
    previous_state: Optional[dict[str, Any]] = None
    new_state: Optional[dict[str, Any]] = None
    metadata_info: Optional[dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
