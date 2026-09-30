import uuid
from decimal import Decimal
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from backend.database.models.ap import ApprovalPolicy, Approval
from backend.database.enums import ApprovalStatus

class ApprovalRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_active_policies(self, tenant_id: UUID) -> list[ApprovalPolicy]:
        """Fetch all active approval policies for a tenant ordered by sequence_order."""
        stmt = (
            select(ApprovalPolicy)
            .where(ApprovalPolicy.tenant_id == tenant_id, ApprovalPolicy.active.is_(True))
            .order_by(ApprovalPolicy.sequence_order)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_matching_policies(self, tenant_id: UUID, amount: Decimal) -> list[ApprovalPolicy]:
        """
        Fetch active approval policies applicable to the given monetary amount.
        min_amount <= amount AND (max_amount IS NULL OR max_amount >= amount)
        """
        stmt = (
            select(ApprovalPolicy)
            .where(
                ApprovalPolicy.tenant_id == tenant_id,
                ApprovalPolicy.active.is_(True),
                ApprovalPolicy.min_amount <= amount,
                or_(ApprovalPolicy.max_amount.is_(None), ApprovalPolicy.max_amount >= amount)
            )
            .order_by(ApprovalPolicy.sequence_order)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_approvals_by_invoice(self, tenant_id: UUID, invoice_id: UUID) -> list[Approval]:
        """Fetch all existing approvals for an invoice."""
        stmt = (
            select(Approval)
            .where(Approval.tenant_id == tenant_id, Approval.invoice_id == invoice_id)
            .order_by(Approval.sequence_order)
        )
        return list(self.session.execute(stmt).scalars().all())

    def create_pending_approval(
        self,
        tenant_id: UUID,
        invoice_id: UUID,
        policy_id: UUID,
        sequence_order: int,
        approver_user_id: Optional[UUID] = None
    ) -> Approval:
        """Create a pending approval checkpoint."""
        appr = Approval(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            approval_policy_id=policy_id,
            sequence_order=sequence_order,
            approver_user_id=approver_user_id,
            status=ApprovalStatus.PENDING.value
        )
        self.session.add(appr)
        self.session.flush()
        return appr
