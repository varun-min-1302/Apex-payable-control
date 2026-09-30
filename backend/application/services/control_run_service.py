import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from backend.domain.controls.base import ControlContext
from backend.domain.controls.registry import ControlRegistry, default_registry
from backend.domain.decisions.invoice_decision import InvoiceDecisionEngine
from backend.application.dto.control_dto import ControlEvaluation, ControlRunSummary, ToleranceConfig
from backend.application.dto.decision_dto import DecisionOutcome, InvoiceDecision
from backend.application.services.exception_service import ExceptionService
from backend.application.services.risk_service import RiskService
from backend.application.services.approval_routing_service import ApprovalRoutingService
from backend.repositories.invoice_repository import InvoiceRepository
from backend.repositories.vendor_repository import VendorRepository
from backend.repositories.purchase_order_repository import PurchaseOrderRepository
from backend.repositories.receipt_repository import ReceiptRepository
from backend.repositories.control_repository import ControlRepository
from backend.repositories.exception_repository import ExceptionRepository
from backend.repositories.risk_repository import RiskRepository
from backend.repositories.approval_repository import ApprovalRepository
from backend.repositories.audit_repository import AuditRepository
from backend.database.models.ap import ControlRun, Invoice
from backend.database.enums import ControlRunStatus, ControlStatus, InvoiceStatus

class ControlRunService:
    """
    Core orchestrator of the AP Control Engine.
    Executes all deterministic controls, persists results, generates exceptions/signals,
    routes approvals if eligible, and writes audit trails.
    CORE INVARIANT: NEVER directly creates a payable obligation in ap.payable_ledger.
    """

    def __init__(
        self,
        session: Session,
        registry: Optional[ControlRegistry] = None,
        decision_engine: Optional[InvoiceDecisionEngine] = None,
    ):
        self.session = session
        self.registry = registry or default_registry
        self.decision_engine = decision_engine or InvoiceDecisionEngine()

        # Repositories
        self.invoice_repo = InvoiceRepository(session)
        self.vendor_repo = VendorRepository(session)
        self.po_repo = PurchaseOrderRepository(session)
        self.receipt_repo = ReceiptRepository(session)
        self.control_repo = ControlRepository(session)
        self.exception_repo = ExceptionRepository(session)
        self.risk_repo = RiskRepository(session)
        self.approval_repo = ApprovalRepository(session)
        self.audit_repo = AuditRepository(session)

        # Domain Services
        self.exception_service = ExceptionService(self.exception_repo)
        self.risk_service = RiskService(self.risk_repo)
        self.approval_service = ApprovalRoutingService(self.approval_repo)

    def execute_control_run(
        self,
        tenant_id: UUID,
        invoice_id: UUID,
        revision_id: Optional[UUID] = None,
        triggered_by: Optional[UUID] = None,
        ruleset_version: str = "v1.0",
        tolerance_config: Optional[ToleranceConfig] = None,
        correlation_id: Optional[str] = None
    ) -> tuple[ControlRun, ControlRunSummary, InvoiceDecision]:
        """
        Execute a complete deterministic validation run for an invoice revision.
        """
        start_time = time.perf_counter()
        corr_id = correlation_id or f"CR-{uuid.uuid4().hex[:12]}"
        t_config = tolerance_config or ToleranceConfig()

        # 1. Fetch invoice and target revision
        invoice = self.invoice_repo.get_by_id(tenant_id, invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found in tenant {tenant_id}.")

        if revision_id:
            revision = self.invoice_repo.get_revision_by_id(tenant_id, revision_id)
        else:
            revision = self.invoice_repo.get_current_or_latest_revision(invoice)

        if not revision:
            raise ValueError(f"No revision found for invoice {invoice_id}.")

        # 2. Compute next run number for revision
        run_number = self.control_repo.get_next_run_number(tenant_id, revision.id)

        # 3. Create ControlRun in RUNNING status
        control_run = self.control_repo.create_control_run(
            tenant_id=tenant_id,
            invoice_id=invoice.id,
            invoice_revision_id=revision.id,
            run_number=run_number,
            triggered_by=triggered_by,
            ruleset_version=ruleset_version
        )

        # 4. Audit: CONTROL_RUN_STARTED
        self.audit_repo.record_event(
            tenant_id=tenant_id,
            action="CONTROL_RUN_STARTED",
            entity_type="CONTROL_RUN",
            entity_id=control_run.id,
            actor_user_id=triggered_by,
            correlation_id=corr_id,
            previous_state={"invoice_status": str(invoice.status)},
            metadata={
                "invoice_id": str(invoice.id),
                "revision_id": str(revision.id),
                "run_number": run_number,
                "invoice_number": invoice.invoice_number
            }
        )

        try:
            # 5. Build ControlContext in single query pass (Zero N+1)
            vendor = self.vendor_repo.get_by_id(tenant_id, invoice.vendor_id)
            po = None
            po_items = []
            goods_receipts = []
            goods_receipt_items = []

            if invoice.purchase_order_id:
                po = self.po_repo.get_by_id(tenant_id, invoice.purchase_order_id)
                if po:
                    po_items = list(po.items)
                    goods_receipts = self.receipt_repo.get_receipts_by_po_id(tenant_id, po.id)
                    goods_receipt_items = self.receipt_repo.get_items_by_po_id(tenant_id, po.id)

            approval_policies = self.approval_repo.get_active_policies(tenant_id)

            # Historical invoices for duplicate / statistical checks (prior invoices only)
            dup_candidates = self.invoice_repo.find_exact_duplicates(
                tenant_id=tenant_id,
                vendor_id=invoice.vendor_id,
                invoice_number=invoice.invoice_number,
                document_hash=invoice.document_hash,
                exclude_invoice_id=invoice.id,
                created_before=invoice.created_at
            )
            vendor_history = self.invoice_repo.get_historical_invoices_by_vendor(
                tenant_id=tenant_id,
                vendor_id=invoice.vendor_id,
                exclude_invoice_id=invoice.id,
                created_before=invoice.created_at
            )
            hist_map = {inv.id: inv for inv in (dup_candidates + vendor_history)}
            historical_invoices = list(hist_map.values())

            context = ControlContext(
                tenant_id=tenant_id,
                invoice=invoice,
                current_revision=revision,
                invoice_items=list(revision.items),
                vendor=vendor,
                purchase_order=po,
                po_items=po_items,
                goods_receipts=goods_receipts,
                goods_receipt_items=goods_receipt_items,
                approval_policies=approval_policies,
                historical_invoices=historical_invoices,
                tolerance_config=t_config
            )

            # 6. Execute all controls from registry
            evaluations: list[ControlEvaluation] = []
            for ctrl in self.registry.controls:
                try:
                    ev = ctrl.execute(context)
                except Exception as ex:
                    ev = ControlEvaluation(
                        control_code=ctrl.control_code,
                        category=ctrl.category,
                        status=ControlStatus.ERROR,
                        severity=SeverityLevel.HIGH,
                        message=f"Control execution exception: {str(ex)}",
                        rule_version=ctrl.rule_version
                    )
                evaluations.append(ev)

            # 7. Persist ControlResults
            persisted_results = self.control_repo.persist_evaluations(
                tenant_id=tenant_id,
                control_run_id=control_run.id,
                invoice_id=invoice.id,
                evaluations=evaluations
            )
            control_result_map = {res.control_code: res.id for res in persisted_results}

            # 8. Render overall invoice decision
            decision = self.decision_engine.evaluate(evaluations)

            # 9. Persist pending exceptions and risk signals
            if decision.pending_exceptions:
                self.exception_service.process_pending_exceptions(
                    tenant_id=tenant_id,
                    invoice_id=invoice.id,
                    control_result_map=control_result_map,
                    pending_exceptions=decision.pending_exceptions
                )
                self.audit_repo.record_event(
                    tenant_id=tenant_id,
                    action="EXCEPTIONS_GENERATED",
                    entity_type="INVOICE",
                    entity_id=invoice.id,
                    actor_user_id=triggered_by,
                    correlation_id=corr_id,
                    metadata={"exception_count": len(decision.pending_exceptions)}
                )

            if decision.pending_risk_signals:
                self.risk_service.process_pending_signals(
                    tenant_id=tenant_id,
                    invoice_id=invoice.id,
                    control_result_map=control_result_map,
                    pending_signals=decision.pending_risk_signals
                )
                self.audit_repo.record_event(
                    tenant_id=tenant_id,
                    action="RISK_SIGNALS_GENERATED",
                    entity_type="INVOICE",
                    entity_id=invoice.id,
                    actor_user_id=triggered_by,
                    correlation_id=corr_id,
                    metadata={"risk_signal_count": len(decision.pending_risk_signals)}
                )

            # 10. Update ControlRun status
            if decision.outcome in (DecisionOutcome.PASS, DecisionOutcome.PASS_WITH_WARNING):
                run_status = ControlRunStatus.PASSED
            elif decision.outcome == DecisionOutcome.EXCEPTION:
                run_status = ControlRunStatus.FAILED
            else:
                run_status = ControlRunStatus.ERROR

            completed_at = datetime.now(timezone.utc)
            self.control_repo.update_control_run_status(
                tenant_id=tenant_id,
                run_id=control_run.id,
                status=run_status,
                completed_at=completed_at
            )

            # 11. Update Invoice status
            old_inv_status = str(invoice.status)
            new_inv_status = decision.target_invoice_status
            self.invoice_repo.update_invoice_status(tenant_id, invoice.id, new_inv_status)

            # 12. Route approvals if eligible (NEVER creates payables!)
            is_controls_passed = (decision.outcome in (DecisionOutcome.PASS, DecisionOutcome.PASS_WITH_WARNING))
            if is_controls_passed:
                self.approval_service.route_approvals(tenant_id, invoice, is_controls_passed)

            # 13. Audit: CONTROL_RUN_COMPLETED
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            passed_cnt = sum(1 for e in evaluations if e.status == ControlStatus.PASS)
            failed_cnt = sum(1 for e in evaluations if e.status == ControlStatus.FAIL)
            warn_cnt = sum(1 for e in evaluations if e.status == ControlStatus.WARNING)
            err_cnt = sum(1 for e in evaluations if e.status == ControlStatus.ERROR)
            na_cnt = sum(1 for e in evaluations if e.status == ControlStatus.NOT_APPLICABLE)

            self.audit_repo.record_event(
                tenant_id=tenant_id,
                action="CONTROL_RUN_COMPLETED",
                entity_type="CONTROL_RUN",
                entity_id=control_run.id,
                actor_user_id=triggered_by,
                correlation_id=corr_id,
                previous_state={"status": "RUNNING", "invoice_status": old_inv_status},
                new_state={"status": run_status.value, "invoice_status": new_inv_status.value},
                metadata={
                    "duration_ms": duration_ms,
                    "total_controls": len(evaluations),
                    "passed": passed_cnt,
                    "failed": failed_cnt,
                    "warnings": warn_cnt,
                    "errors": err_cnt,
                    "decision_outcome": decision.outcome.value
                }
            )

            self.session.flush()

            summary = ControlRunSummary(
                run_id=control_run.id,
                invoice_id=invoice.id,
                revision_id=revision.id,
                run_number=run_number,
                status=run_status.value,
                total_controls=len(evaluations),
                passed_count=passed_cnt,
                failed_count=failed_cnt,
                warning_count=warn_cnt,
                error_count=err_cnt,
                not_applicable_count=na_cnt,
                duration_ms=duration_ms,
                correlation_id=corr_id
            )

            return control_run, summary, decision

        except Exception as ex:
            # Mark run as error on unhandled failure
            self.control_repo.update_control_run_status(
                tenant_id=tenant_id,
                run_id=control_run.id,
                status=ControlRunStatus.ERROR
            )
            self.session.flush()
            raise ex
