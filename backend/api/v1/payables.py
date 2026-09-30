from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, desc

from backend.api.deps import get_db, get_current_user, require_roles
from backend.database.models.identity import User
from backend.database.models.ap import PayableLedger, Payment, Invoice
from backend.application.services.payable_workflow_service import PayableWorkflowService
from backend.api.schemas.payable_schemas import (
    PayableLedgerOut,
    PaymentOut,
    RecordPaymentRequest,
)

router = APIRouter(prefix="/payables", tags=["Payable Ledger & Disbursements"])

@router.get("", response_model=list[PayableLedgerOut])
def list_payables(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List approved payable obligations committed to the general liability ledger."""
    stmt = (
        select(PayableLedger)
        .where(PayableLedger.tenant_id == current_user.tenant_id)
        .options(
            selectinload(PayableLedger.invoice).selectinload(Invoice.vendor),
            selectinload(PayableLedger.payments)
        )
        .order_by(PayableLedger.due_date, desc(PayableLedger.created_at))
    )

    if status_filter:
        stmt = stmt.where(PayableLedger.status == status_filter.upper())

    stmt = stmt.offset(offset).limit(limit)
    payables = db.execute(stmt).scalars().all()

    result = []
    for p in payables:
        inv_num = p.invoice.invoice_number if p.invoice else None
        vend_name = p.invoice.vendor.display_name if p.invoice and p.invoice.vendor else None
        paid_amt = sum(pm.amount for pm in p.payments)
        rem_balance = p.approved_amount - paid_amt
        payments_out = [PaymentOut.model_validate(pm) for pm in p.payments]

        result.append(
            PayableLedgerOut(
                id=p.id,
                tenant_id=p.tenant_id,
                invoice_id=p.invoice_id,
                invoice_number=inv_num,
                vendor_name=vend_name,
                payable_number=p.payable_number,
                currency=p.currency,
                approved_amount=p.approved_amount,
                paid_amount=paid_amt,
                remaining_balance=rem_balance,
                due_date=p.due_date,
                status=p.status,
                approved_at=p.approved_at,
                created_at=p.created_at,
                payments=payments_out
            )
        )
    return result

@router.get("/{payable_id}", response_model=PayableLedgerOut)
def get_payable_detail(
    payable_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full details of an open or settled payable obligation with transaction history."""
    stmt = (
        select(PayableLedger)
        .where(PayableLedger.tenant_id == current_user.tenant_id, PayableLedger.id == payable_id)
        .options(
            selectinload(PayableLedger.invoice).selectinload(Invoice.vendor),
            selectinload(PayableLedger.payments)
        )
    )
    p = db.execute(stmt).scalars().first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payable obligation not found.")

    inv_num = p.invoice.invoice_number if p.invoice else None
    vend_name = p.invoice.vendor.display_name if p.invoice and p.invoice.vendor else None
    paid_amt = sum(pm.amount for pm in p.payments)
    rem_balance = p.approved_amount - paid_amt
    payments_out = [PaymentOut.model_validate(pm) for pm in p.payments]

    return PayableLedgerOut(
        id=p.id,
        tenant_id=p.tenant_id,
        invoice_id=p.invoice_id,
        invoice_number=inv_num,
        vendor_name=vend_name,
        payable_number=p.payable_number,
        currency=p.currency,
        approved_amount=p.approved_amount,
        paid_amount=paid_amt,
        remaining_balance=rem_balance,
        due_date=p.due_date,
        status=p.status,
        approved_at=p.approved_at,
        created_at=p.created_at,
        payments=payments_out
    )

@router.post("/{payable_id}/payments", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def record_payment_disbursement(
    payable_id: UUID,
    payload: RecordPaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "FINANCE_MANAGER", "FINANCE_HEAD")),
):
    """
    Execute and record a financial disbursement against a committed payable obligation.
    Transitions status to PARTIALLY_PAID or PAID and settles the invoice.
    """
    workflow_service = PayableWorkflowService(db)
    try:
        payment = workflow_service.record_disbursement(
            tenant_id=current_user.tenant_id,
            payable_id=payable_id,
            actor=current_user,
            amount=payload.amount,
            payment_reference=payload.payment_reference,
            payment_method=payload.payment_method
        )
        db.commit()
        return PaymentOut.model_validate(payment)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
