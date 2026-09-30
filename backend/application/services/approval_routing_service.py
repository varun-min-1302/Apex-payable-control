from decimal import Decimal
from typing import Optional
from uuid import UUID
from backend.repositories.approval_repository import ApprovalRepository
from backend.application.dto.routing_dto import ApprovalRouteStep, ApprovalRoutingPlan
from backend.database.models.ap import Invoice, Approval, ApprovalPolicy

class ApprovalRoutingService:
    """
    Computes required approval sequences based on active database approval policies.
    Guarantees that invoices with failing controls are blocked from approval routing.
    NOTE: NEVER directly creates a payable ledger obligation.
    """

    def __init__(self, approval_repo: ApprovalRepository):
        self.approval_repo = approval_repo

    def determine_routing(
        self,
        tenant_id: UUID,
        invoice: Invoice,
        is_controls_passed: bool
    ) -> ApprovalRoutingPlan:
        """
        Evaluate active database approval policies against the invoice grand total.
        If mandatory controls have failed, normal approval routing is blocked.
        """
        amount = (
            invoice.revisions[0].grand_total
            if invoice.revisions
            else Decimal("0.00")
        )

        matching_policies = self.approval_repo.get_matching_policies(tenant_id, amount)

        if not matching_policies:
            return ApprovalRoutingPlan(
                invoice_id=invoice.id,
                is_eligible_for_approval=False,
                requires_all_controls_pass=True,
                steps=[],
                reason=f"No active approval policy found for invoice amount ₹{amount}."
            )

        # Check if any matching policy requires all controls to pass
        requires_pass = any(p.requires_all_controls_pass for p in matching_policies)

        if requires_pass and not is_controls_passed:
            return ApprovalRoutingPlan(
                invoice_id=invoice.id,
                is_eligible_for_approval=False,
                requires_all_controls_pass=True,
                steps=[],
                reason="Invoice failed mandatory control checks. Approval routing blocked until exceptions are resolved."
            )

        steps = [
            ApprovalRouteStep(
                policy_id=p.id,
                policy_name=p.name,
                sequence_order=p.sequence_order,
                required_role=p.required_role,
                min_amount=p.min_amount,
                max_amount=p.max_amount,
                requires_all_controls_pass=p.requires_all_controls_pass
            )
            for p in matching_policies
        ]

        return ApprovalRoutingPlan(
            invoice_id=invoice.id,
            is_eligible_for_approval=True,
            requires_all_controls_pass=requires_pass,
            steps=steps,
            reason=f"Invoice eligible for approval under {len(steps)} policy tier(s)."
        )

    def route_approvals(
        self,
        tenant_id: UUID,
        invoice: Invoice,
        is_controls_passed: bool
    ) -> list[Approval]:
        """
        Determine routing and idempotently create pending approval checkpoints.
        """
        plan = self.determine_routing(tenant_id, invoice, is_controls_passed)
        if not plan.is_eligible_for_approval or not plan.steps:
            return []

        existing_approvals = self.approval_repo.get_approvals_by_invoice(tenant_id, invoice.id)
        existing_seqs = {a.sequence_order for a in existing_approvals}

        created = []
        for step in plan.steps:
            if step.sequence_order in existing_seqs:
                continue
            appr = self.approval_repo.create_pending_approval(
                tenant_id=tenant_id,
                invoice_id=invoice.id,
                policy_id=step.policy_id,
                sequence_order=step.sequence_order
            )
            created.append(appr)

        return created
