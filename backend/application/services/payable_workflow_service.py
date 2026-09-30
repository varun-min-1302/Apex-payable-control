from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.database.models.ap import (
    Invoice,
    Approval,
    PayableLedger,
    Payment,
    Exception as APException,
    ControlRun,
)
from backend.database.models.identity import User
from backend.database.enums import (
    ApprovalStatus,
    ApprovalDecision,
    InvoiceStatus,
    PayableStatus,
    PaymentStatus,
    ExceptionStatus,
)
from backend.repositories.audit_repository import AuditRepository

class PayableWorkflowService:
    """
    Authoritative workflow service governing:
    1. Human Approval Sign-Offs
    2. The 'Golden Transaction': Committing approved invoices into ap.payable_ledger
    3. Payment / Disbursement Recording into ap.payments
    """

    def __init__(self, session: Session, audit_repo: Optional[AuditRepository] = None):
        self.session = session
        self.audit_repo = audit_repo or AuditRepository(session)

    def decide_approval(
        self,
        tenant_id: UUID,
        approval_id: UUID,
        actor: User,
        decision: ApprovalDecision,
        comments: Optional[str] = None
    ) -> tuple[Approval, Invoice, Optional[PayableLedger]]:
        """
        Execute an approval decision on an invoice checkpoint.
        
        If decision is APPROVE:
          - Marks approval as APPROVED.
          - Checks if all pending approvals for the invoice are now approved.
          - If all approvals are completed AND invoice is verified:
            ATOMICALLY commits the invoice to ap.payable_ledger and updates status to PAYABLE_CREATED.
            
        If decision is REJECT:
          - Marks approval as REJECTED.
          - Transitions invoice to REJECTED.
        """
        # 1. Fetch approval with row lock
        approval = self.session.query(Approval).filter(
            Approval.tenant_id == tenant_id,
            Approval.id == approval_id
        ).with_for_update().first()

        if not approval:
            raise ValueError(f"Approval request {approval_id} not found in tenant {tenant_id}.")

        if approval.status != ApprovalStatus.PENDING.value:
            raise ValueError(f"Approval {approval_id} is already in state '{approval.status}'.")

        invoice = self.session.query(Invoice).filter(
            Invoice.tenant_id == tenant_id,
            Invoice.id == approval.invoice_id
        ).with_for_update().first()

        if not invoice:
            raise ValueError(f"Associated invoice {approval.invoice_id} not found.")

        # 2. Record approval decision
        approval.status = (
            ApprovalStatus.APPROVED.value
            if decision == ApprovalDecision.APPROVE
            else ApprovalStatus.REJECTED.value
        )
        approval.decision = decision.value
        approval.approver_user_id = actor.id
        approval.comments = comments
        approval.decided_at = datetime.now(timezone.utc)
        self.session.flush()

        payable_entry = None

        if decision == ApprovalDecision.REJECT:
            # Rejection halts the invoice
            prev_status = invoice.status
            invoice.status = InvoiceStatus.REJECTED.value
            self.session.flush()

            self.audit_repo.record_event(
                tenant_id=tenant_id,
                action="INVOICE_REJECTED",
                entity_type="INVOICE",
                entity_id=invoice.id,
                actor_user_id=actor.id,
                previous_state={"status": prev_status},
                new_state={"status": invoice.status, "rejection_comments": comments},
                metadata={"approval_id": str(approval.id)}
            )
            return approval, invoice, None

        # 3. Check for any remaining pending approvals for this invoice
        pending_count = self.session.query(Approval).filter(
            Approval.tenant_id == tenant_id,
            Approval.invoice_id == invoice.id,
            Approval.status == ApprovalStatus.PENDING.value
        ).count()

        if pending_count == 0:
            # 4. Strict Safety Gate: Verify there are no UNRESOLVED exceptions
            open_exceptions = self.session.query(APException).filter(
                APException.tenant_id == tenant_id,
                APException.invoice_id == invoice.id,
                APException.status.in_([ExceptionStatus.OPEN.value, ExceptionStatus.IN_REVIEW.value])
            ).count()

            if open_exceptions > 0:
                raise ValueError(
                    f"Cannot create payable obligation: Invoice has {open_exceptions} open/unresolved exception(s)."
                )

            # 5. Check if payable ledger entry already exists (Idempotency)
            existing_payable = self.session.query(PayableLedger).filter(
                PayableLedger.tenant_id == tenant_id,
                PayableLedger.invoice_id == invoice.id
            ).first()

            if not existing_payable:
                # Latest revision for amount and dates
                latest_rev = (
                    self.session.query(Invoice)
                    .filter(Invoice.id == invoice.id)
                    .first()
                    .current_revision_id
                )
                from backend.database.models.ap import InvoiceRevision
                rev = self.session.query(InvoiceRevision).filter(InvoiceRevision.id == latest_rev).first()
                if not rev:
                    rev = invoice.revisions[-1] if invoice.revisions else None

                subtotal = rev.subtotal if rev else Decimal("0.00")
                tax_total = rev.tax_total if rev else Decimal("0.00")
                grand_total = rev.grand_total if rev else Decimal("0.00")
                due_date = rev.due_date if rev else (datetime.now(timezone.utc).date() + timedelta(days=30))

                target_rev_id = rev.id if rev else invoice.current_revision_id
                payable_number = f"PAY-2026-{invoice.invoice_number.split('-')[-1]}"

                payable_entry = PayableLedger(
                    tenant_id=tenant_id,
                    invoice_id=invoice.id,
                    invoice_revision_id=target_rev_id,
                    vendor_id=invoice.vendor_id,
                    payable_number=payable_number,
                    approved_amount=grand_total,
                    currency=invoice.currency or "INR",
                    due_date=due_date,
                    status=PayableStatus.OPEN.value,
                    approved_at=datetime.now(timezone.utc)
                )
                self.session.add(payable_entry)
                self.session.flush()

                prev_status = invoice.status
                invoice.status = InvoiceStatus.PAYABLE_CREATED.value
                self.session.flush()

                self.audit_repo.record_event(
                    tenant_id=tenant_id,
                    action="PAYABLE_CREATED",
                    entity_type="PAYABLE_LEDGER",
                    entity_id=payable_entry.id,
                    actor_user_id=actor.id,
                    previous_state={"invoice_status": prev_status},
                    new_state={
                        "invoice_status": invoice.status,
                        "payable_number": payable_number,
                        "approved_amount": str(grand_total)
                    },
                    metadata={"invoice_id": str(invoice.id), "due_date": str(due_date)}
                )
            else:
                payable_entry = existing_payable

        return approval, invoice, payable_entry

    def record_disbursement(
        self,
        tenant_id: UUID,
        payable_id: UUID,
        actor: User,
        amount: Decimal,
        payment_reference: str,
        payment_method: str = "NEFT"
    ) -> Payment:
        """
        Record a financial disbursement against an open payable ledger obligation.
        Updates payable ledger paid amount and transitions to PARTIALLY_PAID or PAID.
        """
        payable = self.session.query(PayableLedger).filter(
            PayableLedger.tenant_id == tenant_id,
            PayableLedger.id == payable_id
        ).with_for_update().first()

        if not payable:
            raise ValueError(f"Payable ledger {payable_id} not found in tenant {tenant_id}.")

        if payable.status == PayableStatus.PAID.value:
            raise ValueError(f"Payable {payable_id} is already fully paid.")

        paid_so_far = sum(p.amount for p in payable.payments)
        remaining = payable.approved_amount - paid_so_far
        if amount <= Decimal("0.00"):
            raise ValueError("Disbursement amount must be greater than zero.")

        if amount > remaining:
            raise ValueError(
                f"Disbursement amount (₹{amount}) exceeds remaining payable balance (₹{remaining})."
            )

        payment = Payment(
            tenant_id=tenant_id,
            payable_id=payable.id,
            payment_reference=payment_reference,
            payment_method=payment_method,
            amount=amount,
            currency=payable.currency,
            payment_date=datetime.now(timezone.utc).date(),
            status=PaymentStatus.COMPLETED.value,
        )
        self.session.add(payment)
        self.session.flush()

        new_paid_total = paid_so_far + amount
        if new_paid_total >= payable.approved_amount:
            payable.status = PayableStatus.PAID.value
            # Also update invoice status to PAID
            inv = self.session.query(Invoice).filter(Invoice.id == payable.invoice_id).first()
            if inv:
                inv.status = InvoiceStatus.PAID.value
        else:
            payable.status = PayableStatus.PARTIALLY_PAID.value

        self.session.flush()

        self.audit_repo.record_event(
            tenant_id=tenant_id,
            action="PAYMENT_RECORDED",
            entity_type="PAYMENT",
            entity_id=payment.id,
            actor_user_id=actor.id,
            previous_state={"payable_status": payable.status, "paid_amount": str(paid_so_far)},
            new_state={
                "payable_status": payable.status,
                "paid_amount": str(new_paid_total),
                "disbursed_amount": str(amount),
                "payment_reference": payment_reference
            },
            metadata={"payable_id": str(payable.id)}
        )

        return payment
