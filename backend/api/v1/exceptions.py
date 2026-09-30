from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, desc

from backend.api.deps import get_db, get_current_user, require_roles
from backend.database.models.identity import User
from backend.database.models.ap import Exception as APException, Invoice
from backend.database.enums import ExceptionStatus, InvoiceStatus
from backend.repositories.audit_repository import AuditRepository
from backend.api.schemas.exception_schemas import ExceptionOut, ExceptionResolveRequest

router = APIRouter(prefix="/exceptions", tags=["Exceptions Management"])

@router.get("", response_model=list[ExceptionOut])
def list_exceptions(
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = None,
    invoice_id: Optional[UUID] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List open, in-review, or resolved exceptions logged against invoices."""
    stmt = (
        select(APException)
        .where(APException.tenant_id == current_user.tenant_id)
        .options(
            selectinload(APException.invoice).selectinload(Invoice.vendor),
            selectinload(APException.assignee)
        )
        .order_by(desc(APException.created_at))
    )

    if status_filter:
        stmt = stmt.where(APException.status == status_filter.upper())
    if severity:
        stmt = stmt.where(APException.severity == severity.upper())
    if invoice_id:
        stmt = stmt.where(APException.invoice_id == invoice_id)

    stmt = stmt.offset(offset).limit(limit)
    exceptions = db.execute(stmt).scalars().all()

    result = []
    for exc in exceptions:
        inv_num = exc.invoice.invoice_number if exc.invoice else None
        vend_name = exc.invoice.vendor.display_name if exc.invoice and exc.invoice.vendor else None
        assignee_name = exc.assignee.full_name if exc.assignee else None

        result.append(
            ExceptionOut(
                id=exc.id,
                tenant_id=exc.tenant_id,
                invoice_id=exc.invoice_id,
                control_result_id=exc.control_result_id,
                exception_code=exc.exception_code,
                title=exc.title,
                description=exc.description,
                severity=exc.severity,
                status=exc.status,
                assigned_to=exc.assigned_to,
                assigned_to_name=assignee_name,
                invoice_number=inv_num,
                vendor_name=vend_name,
                resolution_reason=exc.resolution,
                created_at=exc.created_at,
                resolved_at=exc.resolved_at
            )
        )
    return result

@router.post("/{exception_id}/resolve", response_model=ExceptionOut)
def resolve_exception(
    exception_id: UUID,
    payload: ExceptionResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "FINANCE_MANAGER", "PROCUREMENT_MANAGER")),
):
    """
    Resolve or waive a flagged control exception with mandatory audit reason.
    If all exceptions on the invoice are cleared, updates invoice state to AWAITING_APPROVAL.
    """
    exc = db.query(APException).filter(
        APException.tenant_id == current_user.tenant_id,
        APException.id == exception_id
    ).with_for_update().first()

    if not exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exception not found.")

    if exc.status in [ExceptionStatus.RESOLVED.value, ExceptionStatus.REJECTED.value, ExceptionStatus.CANCELLED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Exception is already {exc.status}."
        )

    prev_status = exc.status
    target_status = (
        ExceptionStatus.REJECTED.value
        if payload.action.upper() in ("REJECT", "CANCEL")
        else ExceptionStatus.RESOLVED.value
    )

    exc.status = target_status
    exc.resolution = payload.reason
    exc.resolved_by = current_user.id
    exc.resolved_at = datetime.now(timezone.utc)
    db.flush()

    audit_repo = AuditRepository(db)
    audit_repo.record_event(
        tenant_id=current_user.tenant_id,
        action=f"EXCEPTION_{target_status}",
        entity_type="EXCEPTION",
        entity_id=exc.id,
        actor_user_id=current_user.id,
        previous_state={"status": prev_status},
        new_state={"status": exc.status, "reason": payload.reason},
        metadata={"invoice_id": str(exc.invoice_id), "exception_code": exc.exception_code}
    )

    # Check if this was the last active exception on the invoice
    remaining = db.query(APException).filter(
        APException.tenant_id == current_user.tenant_id,
        APException.invoice_id == exc.invoice_id,
        APException.status.in_([ExceptionStatus.OPEN.value, ExceptionStatus.IN_REVIEW.value])
    ).count()

    if remaining == 0:
        inv = db.query(Invoice).filter(Invoice.id == exc.invoice_id).with_for_update().first()
        if inv and inv.status == InvoiceStatus.EXCEPTION.value:
            inv_prev = inv.status
            inv.status = InvoiceStatus.AWAITING_APPROVAL.value
            db.flush()

            audit_repo.record_event(
                tenant_id=current_user.tenant_id,
                action="INVOICE_EXCEPTIONS_CLEARED",
                entity_type="INVOICE",
                entity_id=inv.id,
                actor_user_id=current_user.id,
                previous_state={"status": inv_prev},
                new_state={"status": inv.status},
                metadata={"reason": "All exceptions resolved/waived. Ready for approval."}
            )

    db.commit()

    return ExceptionOut(
        id=exc.id,
        tenant_id=exc.tenant_id,
        invoice_id=exc.invoice_id,
        control_result_id=exc.control_result_id,
        exception_code=exc.exception_code,
        title=exc.title,
        description=exc.description,
        severity=exc.severity,
        status=exc.status,
        assigned_to=exc.assigned_to,
        assigned_to_name=current_user.full_name,
        invoice_number=exc.invoice.invoice_number if exc.invoice else None,
        vendor_name=exc.invoice.vendor.display_name if exc.invoice and exc.invoice.vendor else None,
        resolution_reason=exc.resolution,
        created_at=exc.created_at,
        resolved_at=exc.resolved_at
    )
