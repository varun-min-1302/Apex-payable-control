from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, desc

from backend.api.deps import get_db, get_current_user
from backend.database.models.identity import User
from backend.database.models.audit import AuditLog
from backend.api.schemas.audit_schemas import AuditLogOut

router = APIRouter(prefix="/audit", tags=["Audit Trail"])

@router.get("/logs", response_model=list[AuditLogOut])
def list_audit_logs(
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    action: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Query the append-only, immutable audit trail.
    All state transitions, control runs, exceptions, approvals, and disbursements are permanently indexed.
    """
    stmt = (
        select(AuditLog)
        .where(AuditLog.tenant_id == current_user.tenant_id)
        .options(selectinload(AuditLog.actor))
        .order_by(desc(AuditLog.created_at))
    )

    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type.upper())
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if action:
        stmt = stmt.where(AuditLog.action == action.upper())

    stmt = stmt.offset(offset).limit(limit)
    logs = db.execute(stmt).scalars().all()

    result = []
    for l in logs:
        actor_name = l.actor.full_name if l.actor else None
        result.append(
            AuditLogOut(
                id=l.id,
                tenant_id=l.tenant_id,
                action=l.action,
                entity_type=l.entity_type,
                entity_id=l.entity_id,
                actor_user_id=l.actor_user_id,
                actor_name=actor_name,
                correlation_id=l.correlation_id,
                previous_state=l.previous_state,
                new_state=l.new_state,
                metadata_info=l.metadata_json,
                created_at=l.created_at
            )
        )
    return result
