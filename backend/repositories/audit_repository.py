import uuid
from datetime import datetime, timezone
from typing import Optional, Any
from uuid import UUID
from sqlalchemy.orm import Session
from backend.database.models.audit import AuditLog

class AuditRepository:
    def __init__(self, session: Session):
        self.session = session

    def record_event(
        self,
        tenant_id: UUID,
        action: str,
        entity_type: str,
        entity_id: UUID,
        actor_user_id: Optional[UUID] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        previous_state: Optional[dict[str, Any]] = None,
        new_state: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Record an immutable audit log entry.
        Note: audit.audit_logs is protected by an engine trigger preventing UPDATE/DELETE.
        """
        log = AuditLog(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            request_id=request_id,
            correlation_id=correlation_id,
            previous_state=previous_state,
            new_state=new_state,
            metadata_json=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(timezone.utc)
        )
        self.session.add(log)
        self.session.flush()
        return log
