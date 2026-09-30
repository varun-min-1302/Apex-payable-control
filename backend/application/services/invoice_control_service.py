from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from backend.application.services.control_run_service import ControlRunService
from backend.application.dto.control_dto import ControlRunSummary, ToleranceConfig
from backend.application.dto.decision_dto import InvoiceDecision
from backend.application.dto.routing_dto import ApprovalRoutingPlan
from backend.database.models.ap import ControlRun, ControlResult, Exception as APException, RiskSignal, Approval

class InvoiceControlService:
    """
    Facade application service designed to power future FastAPI REST endpoints:
    - POST /api/v1/invoices/{invoice_id}/control-runs
    - GET /api/v1/invoices/{invoice_id}/control-runs/latest
    - GET /api/v1/control-runs/{run_id}
    - GET /api/v1/invoices/{invoice_id}/control-results
    - GET /api/v1/invoices/{invoice_id}/exceptions
    - GET /api/v1/invoices/{invoice_id}/risk-signals
    - POST /api/v1/invoices/{invoice_id}/request-approval
    """

    def __init__(self, session: Session, control_run_service: Optional[ControlRunService] = None):
        self.session = session
        self.run_service = control_run_service or ControlRunService(session)

    def trigger_control_run(
        self,
        tenant_id: UUID,
        invoice_id: UUID,
        revision_id: Optional[UUID] = None,
        triggered_by: Optional[UUID] = None,
        ruleset_version: str = "v1.0",
        tolerance_config: Optional[ToleranceConfig] = None
    ) -> tuple[ControlRun, ControlRunSummary, InvoiceDecision]:
        """Trigger a validation control run on an invoice revision."""
        return self.run_service.execute_control_run(
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            revision_id=revision_id,
            triggered_by=triggered_by,
            ruleset_version=ruleset_version,
            tolerance_config=tolerance_config
        )

    def get_latest_control_run(self, tenant_id: UUID, invoice_id: UUID) -> Optional[ControlRun]:
        """Fetch the most recent control run for an invoice."""
        return self.run_service.control_repo.get_latest_by_invoice(tenant_id, invoice_id)

    def get_control_run_by_id(self, tenant_id: UUID, run_id: UUID) -> Optional[ControlRun]:
        """Fetch a specific control run by ID."""
        return self.run_service.control_repo.get_by_id(tenant_id, run_id)

    def get_control_results(self, tenant_id: UUID, invoice_id: UUID) -> list[ControlResult]:
        """Fetch control results for the latest run of an invoice."""
        latest_run = self.get_latest_control_run(tenant_id, invoice_id)
        if latest_run and latest_run.results:
            return list(latest_run.results)
        return []

    def get_exceptions(self, tenant_id: UUID, invoice_id: UUID) -> list[APException]:
        """Fetch all exceptions logged for an invoice."""
        return self.run_service.exception_repo.get_by_invoice(tenant_id, invoice_id)

    def get_risk_signals(self, tenant_id: UUID, invoice_id: UUID) -> list[RiskSignal]:
        """Fetch all risk signals logged for an invoice."""
        return self.run_service.risk_repo.get_by_invoice(tenant_id, invoice_id)

    def request_approval(self, tenant_id: UUID, invoice_id: UUID) -> ApprovalRoutingPlan:
        """
        Request approval routing for an invoice.
        Enforces policy: if mandatory controls failed, returns blocked plan.
        """
        invoice = self.run_service.invoice_repo.get_by_id(tenant_id, invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found.")

        latest_run = self.get_latest_control_run(tenant_id, invoice_id)
        is_passed = (
            latest_run is not None and
            latest_run.status == "PASSED"
        )

        plan = self.run_service.approval_service.determine_routing(tenant_id, invoice, is_passed)
        if plan.is_eligible_for_approval and plan.steps:
            self.run_service.approval_service.route_approvals(tenant_id, invoice, is_passed)

        return plan
