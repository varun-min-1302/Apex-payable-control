from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, desc

from backend.api.deps import get_db, get_current_user, require_roles
from backend.database.models.identity import User
from backend.database.models.ap import Approval, Invoice, ApprovalPolicy
from backend.database.enums import ApprovalStatus, ApprovalDecision
from backend.application.services.payable_workflow_service import PayableWorkflowService
from backend.api.schemas.approval_schemas import (
    ApprovalOut,
    ApprovalDecisionRequest,
    ApprovalDecisionResponse,
)

router = APIRouter(prefix="/approvals", tags=["Approval Workflow"])

@router.get("", response_model=list[ApprovalOut])
@router.get("/", response_model=list[ApprovalOut])
@router.get("/pending", response_model=list[ApprovalOut])
def list_pending_approvals(
    status_filter: Optional[str] = Query(None, alias="status"),
    role_filter: Optional[str] = None,
    invoice_id: Optional[UUID] = None,
    all_org: Optional[bool] = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List pending approval checkpoints requiring management authorization.
    Filtered by the current actor's assigned enterprise roles unless all_org or invoice_id is specified.
    """
    target_status = status_filter.upper() if status_filter else ApprovalStatus.PENDING.value
    stmt = (
        select(Approval)
        .where(
            Approval.tenant_id == current_user.tenant_id,
            Approval.status == target_status
        )
        .options(
            selectinload(Approval.invoice).selectinload(Invoice.vendor),
            selectinload(Approval.invoice).selectinload(Invoice.revisions),
            selectinload(Approval.policy)
        )
        .order_by(Approval.sequence_order, Approval.created_at)
    )

    if invoice_id:
        stmt = stmt.where(Approval.invoice_id == invoice_id)

    user_roles = getattr(current_user, "role_codes", [])
    if not all_org and "ADMIN" not in user_roles and not role_filter and not invoice_id:
        # Filter for policies matching user's roles
        stmt = stmt.join(ApprovalPolicy).where(ApprovalPolicy.required_role.in_(user_roles))
    elif role_filter:
        stmt = stmt.join(ApprovalPolicy).where(ApprovalPolicy.required_role == role_filter.upper())

    stmt = stmt.offset(offset).limit(limit)
    approvals = db.execute(stmt).scalars().all()

    result = []
    for app in approvals:
        inv = app.invoice
        inv_num = inv.invoice_number if inv else None
        vend_name = inv.vendor.display_name if inv and inv.vendor else None
        inv_amt = inv.revisions[-1].grand_total if inv and inv.revisions else None
        pol_name = app.policy.name if app.policy else None
        req_role = app.policy.required_role if app.policy else None
        
        tier = None
        if pol_name:
            if "Tier 1" in pol_name:
                tier = 1
            elif "Tier 2" in pol_name:
                tier = 2
            elif "Tier 3" in pol_name:
                tier = 3
            elif "Tier 4" in pol_name:
                tier = 4

        result.append(
            ApprovalOut(
                id=app.id,
                tenant_id=app.tenant_id,
                invoice_id=app.invoice_id,
                invoice_number=inv_num,
                vendor_name=vend_name,
                invoice_amount=inv_amt,
                approval_policy_id=app.approval_policy_id,
                policy_name=pol_name,
                policy_tier=tier,
                required_role=req_role,
                sequence_order=app.sequence_order,
                approver_user_id=app.approver_user_id,
                approver_name=current_user.full_name if app.approver_user_id else None,
                status=app.status,
                decision=app.decision,
                comments=app.comments,
                decided_at=app.decided_at,
                created_at=app.created_at
            )
        )
    return result

@router.post("/{approval_id}/decide", response_model=ApprovalDecisionResponse)
def decide_approval(
    approval_id: UUID,
    payload: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "FINANCE_MANAGER", "FINANCE_HEAD")),
):
    """
    Submit an executive sign-off decision (APPROVE or REJECT).
    
    CRITICAL WORKFLOW (The Golden Transaction):
    If APPROVE: Upon satisfying all required approval steps for a verified invoice,
    atomically generates an official Payable Ledger obligation record.
    """
    decision_enum = (
        ApprovalDecision.APPROVE
        if payload.decision.upper() == "APPROVE"
        else ApprovalDecision.REJECT
    )

    workflow_service = PayableWorkflowService(db)
    try:
        approval, invoice, payable = workflow_service.decide_approval(
            tenant_id=current_user.tenant_id,
            approval_id=approval_id,
            actor=current_user,
            decision=decision_enum,
            comments=payload.comments
        )
        db.commit()

        msg = (
            f"Approval successfully recorded as {decision_enum.value}."
            if not payable
            else f"Final approval completed! Payable obligation {payable.payable_number} successfully committed to the ledger."
        )

        return ApprovalDecisionResponse(
            approval_id=approval.id,
            invoice_id=invoice.id,
            decision=approval.decision,
            invoice_status=invoice.status,
            payable_created=payable is not None,
            payable_id=payable.id if payable else None,
            payable_number=payable.payable_number if payable else None,
            message=msg
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
