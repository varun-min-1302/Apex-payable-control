"""Control Explanation Service.

Provides deterministic, finance-friendly intelligence and explainability for:
1. "Why isn't this payable?" explanation system
2. Multi-stage visual Control Graph
3. Chronological Audit Replay
4. Multi-revision Diff ("What changed?")
5. Dashboard Control Health analytics

AI explains / human-friendly templates format.
Deterministic controls decide.
Humans approve.
The ledger records.
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from backend.database.enums import (
    ControlStatus,
    ExceptionStatus,
    InvoiceStatus,
    RiskSignalStatus,
)
from backend.database.models.ap import (
    Approval,
    ControlResult,
    ControlRun,
    Exception as APException,
    Invoice,
    InvoiceDocument,
    InvoiceDraft,
    InvoiceItem,
    InvoiceRevision,
    PayableLedger,
    Payment,
    RiskSignal,
)
from backend.database.models.audit import AuditLog
from backend.database.models.identity import User
from backend.domain.controls.metadata import (
    CONTROL_METADATA_REGISTRY,
    format_actual_value,
    format_expected_value,
    format_variance_str,
    get_control_metadata,
)


class ControlExplanationService:
    """Service generating deterministic explanations, control graphs, audit replays, and diffs."""

    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # FEATURE 1: "Why isn't this payable?"
    # =========================================================================

    def explain_invoice_payability(
        self,
        tenant_id: UUID,
        invoice_id: UUID,
    ) -> Dict[str, Any]:
        """Explain why an invoice can or cannot be paid using deterministic control evidence."""
        invoice = (
            self.db.query(Invoice)
            .filter(Invoice.tenant_id == tenant_id, Invoice.id == invoice_id)
            .first()
        )
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found in tenant.")

        # Latest control run and results
        latest_run = (
            self.db.query(ControlRun)
            .filter(ControlRun.tenant_id == tenant_id, ControlRun.invoice_id == invoice_id)
            .order_by(desc(ControlRun.run_number))
            .first()
        )
        results: List[ControlResult] = []
        if latest_run:
            results = (
                self.db.query(ControlResult)
                .filter(ControlResult.control_run_id == latest_run.id)
                .all()
            )

        passed_checks = sum(1 for r in results if r.status == ControlStatus.PASS.value)

        # Active exceptions
        exceptions = (
            self.db.query(APException)
            .filter(
                APException.tenant_id == tenant_id,
                APException.invoice_id == invoice_id,
                APException.status.in_([ExceptionStatus.OPEN.value, ExceptionStatus.IN_REVIEW.value]),
            )
            .all()
        )

        # Active risk signals
        risk_signals = (
            self.db.query(RiskSignal)
            .filter(
                RiskSignal.tenant_id == tenant_id,
                RiskSignal.invoice_id == invoice_id,
                RiskSignal.status == RiskSignalStatus.ACTIVE.value,
            )
            .all()
        )

        # Approvals
        approvals = (
            self.db.query(Approval)
            .filter(Approval.tenant_id == tenant_id, Approval.invoice_id == invoice_id)
            .all()
        )

        # Payable ledger
        payable = (
            self.db.query(PayableLedger)
            .filter(PayableLedger.tenant_id == tenant_id, PayableLedger.invoice_id == invoice_id)
            .first()
        )

        inv_status = str(invoice.status)

        # Build blocking reasons and status narrative
        blocking_reasons: List[Dict[str, Any]] = []
        can_be_paid = False

        if inv_status == InvoiceStatus.PAID.value:
            headline = "Invoice is fully paid"
            summary = "All automated checks passed, approval was granted, and disbursement was completed."
            next_action = "No action required. Payment complete."
            can_be_paid = False

        elif inv_status in (InvoiceStatus.PAYABLE_CREATED.value, "PARTIALLY_PAID"):
            can_be_paid = True
            headline = "Ready for payment disbursement"
            if inv_status == "PARTIALLY_PAID":
                summary = "Partially paid. Remaining balance is queued for scheduled disbursement."
                next_action = "Treasury may process the remaining payment balance."
            else:
                summary = "All automated checks and approvals passed. Payable ledger obligation is open."
                next_action = "Treasury may disburse funds via payment batch."

        elif inv_status == InvoiceStatus.APPROVED.value:
            can_be_paid = False
            headline = "Approved — Pending payment posting"
            summary = "The invoice has received formal approval and is being posted to the payable ledger."
            next_action = "Await ledger posting by payment operations."

        elif inv_status == InvoiceStatus.AWAITING_APPROVAL.value:
            can_be_paid = False
            headline = "Waiting for management approval"
            summary = f"All automated controls passed ({passed_checks} checks verified). Requires managerial authorization before payment can be scheduled."
            pending_appr = next((a for a in approvals if a.status == "PENDING"), None)
            if pending_appr and pending_appr.policy:
                next_action = f"Authorized approver must sign off under policy '{pending_appr.policy.name}'."
            else:
                next_action = "Authorized approver must review and approve this invoice."

            # If there are active risk signals (e.g. threshold proximity), add as advisory blocking note
            for sig in risk_signals:
                meta = get_control_metadata(sig.signal_code)
                blocking_reasons.append({
                    "control_code": sig.signal_code,
                    "title": meta.title,
                    "what_happened": sig.description,
                    "why_it_matters": meta.why_it_matters,
                    "recommended_action": meta.recommended_action,
                    "severity": sig.severity,
                    "expected": "Normal historical range",
                    "actual": f"Signal score: {sig.score or 'High'}",
                    "variance": "Flagged",
                    "technical_rule": meta.technical_rule,
                })

        elif inv_status == InvoiceStatus.EXCEPTION.value:
            can_be_paid = False
            failed_results = [r for r in results if r.status == ControlStatus.FAIL.value]
            n_issues = len(failed_results) or len(exceptions) or 1
            headline = "Payment blocked — Action required"
            summary = f"{n_issues} automated check(s) flagged issues that must be resolved before this invoice can be approved or paid."
            next_action = "Review the issues below and coordinate with Procurement, Receiving, or the Vendor to resolve."

            # Construct structured blocking reason for each failure
            for r in failed_results:
                meta = get_control_metadata(r.control_code)
                exc = next((e for e in exceptions if e.control_result_id == r.id), None)
                what_happened = exc.description if exc else (r.message or meta.failed_message)
                blocking_reasons.append({
                    "control_code": r.control_code,
                    "title": meta.title,
                    "what_happened": what_happened,
                    "why_it_matters": meta.why_it_matters,
                    "recommended_action": meta.recommended_action,
                    "severity": r.severity,
                    "expected": format_expected_value(r.control_code, r.expected_value),
                    "actual": format_actual_value(r.control_code, r.actual_value),
                    "variance": format_variance_str(r.variance_value, r.variance_percentage, r.control_code),
                    "technical_rule": meta.technical_rule,
                })

            # If there were exceptions without matching control results
            for exc in exceptions:
                if not any(b["control_code"] == exc.exception_code for b in blocking_reasons):
                    meta = get_control_metadata(exc.exception_code)
                    blocking_reasons.append({
                        "control_code": exc.exception_code,
                        "title": exc.title or meta.title,
                        "what_happened": exc.description or meta.failed_message,
                        "why_it_matters": meta.why_it_matters,
                        "recommended_action": meta.recommended_action,
                        "severity": exc.severity,
                        "expected": "Not specified",
                        "actual": "Discrepancy flagged",
                        "variance": "Flagged",
                        "technical_rule": meta.technical_rule,
                    })

        elif inv_status == InvoiceStatus.REJECTED.value:
            can_be_paid = False
            headline = "Invoice rejected"
            summary = "This invoice was rejected during approval review and cannot be paid."
            rejection = next((a for a in approvals if a.status == "REJECTED" or a.decision == "REJECT"), None)
            comm = rejection.comments if rejection else "Rejected by finance management"
            blocking_reasons.append({
                "control_code": "APPROVAL_REJECTED",
                "title": "Management rejection",
                "what_happened": f"Invoice was formally rejected: {comm}",
                "why_it_matters": "A rejected invoice is permanently barred from payable creation.",
                "recommended_action": "Contact the vendor to cancel or resubmit a corrected invoice.",
                "severity": "CRITICAL",
                "expected": "Approval authorization",
                "actual": "Formal rejection",
                "variance": "REJECTED",
                "technical_rule": "Management Approval Authority Policy",
            })
            next_action = "No payment will be made. Request a revised invoice if appropriate."

        else:
            # RECEIVED, PROCESSING, VALIDATING
            can_be_paid = False
            headline = "Automated verification pending"
            summary = "This invoice has been ingested, but deterministic controls have not completed evaluation."
            blocking_reasons.append({
                "control_code": "CONTROL_RUN_PENDING",
                "title": "Automated verification pending",
                "what_happened": "Deterministic control rules have not yet been evaluated for this invoice.",
                "why_it_matters": "Invoices cannot be approved or paid without completing all 18 automated controls.",
                "recommended_action": "Run automated checks to evaluate invoice validity.",
                "severity": "MEDIUM",
                "expected": "Control run completed",
                "actual": f"Current status: {inv_status}",
                "variance": "Pending",
                "technical_rule": "Deterministic AP Control Engine Execution",
            })
            next_action = "Trigger automated checks to verify the invoice against purchase orders and receipts."

        return {
            "invoice_id": str(invoice_id),
            "invoice_number": invoice.invoice_number,
            "status": inv_status,
            "headline": headline,
            "summary": summary,
            "blocking_reasons": blocking_reasons,
            "passed_checks": passed_checks,
            "next_action": next_action,
            "can_be_paid": can_be_paid,
        }

    # =========================================================================
    # FEATURE 3: Control Graph
    # =========================================================================

    def get_control_graph(
        self,
        tenant_id: UUID,
        invoice_id: UUID,
    ) -> Dict[str, Any]:
        """Build the visual multi-stage Control Graph for an invoice from actual control results."""
        invoice = (
            self.db.query(Invoice)
            .filter(Invoice.tenant_id == tenant_id, Invoice.id == invoice_id)
            .first()
        )
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found in tenant.")

        latest_run = (
            self.db.query(ControlRun)
            .filter(ControlRun.tenant_id == tenant_id, ControlRun.invoice_id == invoice_id)
            .order_by(desc(ControlRun.run_number))
            .first()
        )

        results_map: Dict[str, ControlResult] = {}
        if latest_run:
            results = (
                self.db.query(ControlResult)
                .filter(ControlResult.control_run_id == latest_run.id)
                .all()
            )
            for r in results:
                results_map[r.control_code] = r

        # Stage definitions with their mapped control codes
        stages_def = [
            {
                "id": "vendor",
                "title": "Vendor Verification",
                "category": "VENDOR",
                "order": 1,
                "controls": ["VENDOR_EXISTS", "VENDOR_STATUS", "VENDOR_TAX_ID_MATCH", "BANK_DETAILS_MATCH"],
            },
            {
                "id": "po",
                "title": "Purchase Order",
                "category": "PO",
                "order": 2,
                "controls": ["PO_EXISTS", "PO_APPROVED", "PO_VENDOR_MATCH", "PO_ITEM_MATCH"],
            },
            {
                "id": "receipt",
                "title": "Goods Receipt",
                "category": "RECEIPT",
                "order": 3,
                "controls": ["RECEIPT_MATCH", "QUANTITY_MATCH"],
            },
            {
                "id": "financial",
                "title": "Financial Validation",
                "category": "FINANCIAL",
                "order": 4,
                "controls": ["PRICE_MATCH", "TAX_VALIDATION", "TOTAL_VALIDATION", "PAYMENT_TERMS_VALIDATION"],
            },
            {
                "id": "duplicate",
                "title": "Duplicate Prevention",
                "category": "DUPLICATE",
                "order": 5,
                "controls": ["DUPLICATE_EXACT", "DUPLICATE_SEMANTIC"],
            },
            {
                "id": "risk",
                "title": "Risk Signals",
                "category": "RISK",
                "order": 6,
                "controls": ["THRESHOLD_PROXIMITY", "UNUSUAL_AMOUNT"],
            },
        ]

        nodes: List[Dict[str, Any]] = []

        for s_def in stages_def:
            stage_checks = []
            pass_cnt = 0
            fail_cnt = 0
            warn_cnt = 0

            for code in s_def["controls"]:
                r = results_map.get(code)
                meta = get_control_metadata(code)

                if r:
                    status_val = r.status
                    if status_val == ControlStatus.PASS.value:
                        pass_cnt += 1
                        msg = r.message or meta.passed_message
                    elif status_val == ControlStatus.FAIL.value:
                        fail_cnt += 1
                        msg = r.message or meta.failed_message
                    elif status_val == ControlStatus.WARNING.value:
                        warn_cnt += 1
                        msg = r.message or "Advisory warning flagged."
                    else:
                        msg = r.message or "Not applicable"

                    stage_checks.append({
                        "control_code": code,
                        "title": meta.title,
                        "status": status_val,
                        "severity": r.severity,
                        "message": msg,
                        "expected": format_expected_value(code, r.expected_value),
                        "actual": format_actual_value(code, r.actual_value),
                        "variance": format_variance_str(r.variance_value, r.variance_percentage, code),
                        "why_it_matters": meta.why_it_matters,
                        "recommended_action": meta.recommended_action,
                        "evaluated_at": r.evaluated_at.isoformat() if r.evaluated_at else None,
                    })
                else:
                    stage_checks.append({
                        "control_code": code,
                        "title": meta.title,
                        "status": "WAITING",
                        "severity": "INFO",
                        "message": "Evaluation pending.",
                        "expected": "Pending",
                        "actual": "Pending",
                        "variance": "None",
                        "why_it_matters": meta.why_it_matters,
                        "recommended_action": meta.recommended_action,
                        "evaluated_at": None,
                    })

            # Derive node status
            if fail_cnt > 0:
                node_status = "FAIL"
                summary_text = f"{fail_cnt} failed, {pass_cnt} passed"
            elif warn_cnt > 0:
                node_status = "WARNING"
                summary_text = f"{warn_cnt} warning, {pass_cnt} passed"
            elif pass_cnt > 0 and (pass_cnt + fail_cnt + warn_cnt) == len(s_def["controls"]):
                node_status = "PASS"
                summary_text = f"All {pass_cnt}/{pass_cnt} passed"
            elif pass_cnt > 0:
                node_status = "PASS"
                summary_text = f"{pass_cnt}/{len(s_def['controls'])} passed"
            else:
                node_status = "WAITING"
                summary_text = "Pending evaluation"

            nodes.append({
                "id": s_def["id"],
                "label": s_def["title"],
                "category": s_def["category"],
                "order": s_def["order"],
                "status": node_status,
                "total_checks": len(s_def["controls"]),
                "passed_count": pass_cnt,
                "failed_count": fail_cnt,
                "warning_count": warn_cnt,
                "summary": summary_text,
                "checks": stage_checks,
            })

        # Stage 7: Approval Node
        approvals = (
            self.db.query(Approval)
            .filter(Approval.tenant_id == tenant_id, Approval.invoice_id == invoice_id)
            .all()
        )
        inv_st = str(invoice.status)
        if inv_st in (InvoiceStatus.APPROVED.value, InvoiceStatus.PAYABLE_CREATED.value, InvoiceStatus.PAID.value):
            appr_status = "PASS"
            appr_summary = "Approved"
        elif inv_st == InvoiceStatus.REJECTED.value:
            appr_status = "FAIL"
            appr_summary = "Rejected"
        elif inv_st == InvoiceStatus.AWAITING_APPROVAL.value:
            appr_status = "WAITING"
            appr_summary = "Awaiting decision"
        elif inv_st == InvoiceStatus.EXCEPTION.value:
            appr_status = "SKIPPED"
            appr_summary = "Blocked by exception"
        else:
            appr_status = "WAITING"
            appr_summary = "Pending"

        appr_checks = []
        for app in approvals:
            pol_name = app.policy.name if app.policy else f"Policy #{app.sequence_order}"
            appr_checks.append({
                "control_code": "APPROVAL_DECISION",
                "title": f"Approval ({pol_name})",
                "status": "PASS" if app.status == "APPROVED" else ("FAIL" if app.status == "REJECTED" else "WAITING"),
                "severity": "INFO",
                "message": f"Decision: {app.decision or 'Pending'}. Note: {app.comments or 'None'}",
                "expected": "Approved by designated authority",
                "actual": f"{app.status} (Step {app.sequence_order})",
                "variance": "None",
                "why_it_matters": "Financial authority limits mandate sign-off before funds are legally committed.",
                "recommended_action": "Review invoice documents and approve or reject.",
                "evaluated_at": app.decided_at.isoformat() if app.decided_at else None,
            })

        nodes.append({
            "id": "approval",
            "label": "Management Approval",
            "category": "APPROVAL",
            "order": 7,
            "status": appr_status,
            "total_checks": max(1, len(approvals)),
            "passed_count": 1 if appr_status == "PASS" else 0,
            "failed_count": 1 if appr_status == "FAIL" else 0,
            "warning_count": 0,
            "summary": appr_summary,
            "checks": appr_checks,
        })

        # Stage 8: Payable Node
        payable = (
            self.db.query(PayableLedger)
            .filter(PayableLedger.tenant_id == tenant_id, PayableLedger.invoice_id == invoice_id)
            .first()
        )
        if inv_st == InvoiceStatus.PAID.value:
            pay_status = "PASS"
            pay_summary = "Fully paid"
        elif inv_st in (InvoiceStatus.PAYABLE_CREATED.value, "PARTIALLY_PAID"):
            pay_status = "PASS"
            pay_summary = "Payable open" if inv_st == InvoiceStatus.PAYABLE_CREATED.value else "Partially paid"
        elif inv_st in (InvoiceStatus.EXCEPTION.value, InvoiceStatus.REJECTED.value):
            pay_status = "SKIPPED"
            pay_summary = "Not payable"
        else:
            pay_status = "WAITING"
            pay_summary = "Pending approval"

        pay_checks = []
        if payable:
            pay_checks.append({
                "control_code": "PAYABLE_LEDGER_POSTING",
                "title": "Payable ledger liability",
                "status": "PASS",
                "severity": "INFO",
                "message": f"Payable #{payable.payable_number} created for ₹{payable.approved_amount:,.2f}.",
                "expected": f"₹{payable.approved_amount:,.2f} obligation",
                "actual": f"Remaining balance ₹{payable.remaining_balance:,.2f}",
                "variance": "None",
                "why_it_matters": "Formal ledger commitment permits payment disbursement by Treasury.",
                "recommended_action": "Disburse funds according to invoice payment terms.",
                "evaluated_at": payable.created_at.isoformat() if payable.created_at else None,
            })

        nodes.append({
            "id": "payable",
            "label": "Payable & Payment",
            "category": "PAYMENT",
            "order": 8,
            "status": pay_status,
            "total_checks": 1 if payable else 0,
            "passed_count": 1 if pay_status == "PASS" else 0,
            "failed_count": 0,
            "warning_count": 0,
            "summary": pay_summary,
            "checks": pay_checks,
        })

        return {
            "invoice_id": str(invoice_id),
            "invoice_number": invoice.invoice_number,
            "current_status": str(invoice.status),
            "nodes": nodes,
        }

    # =========================================================================
    # FEATURE 4: Audit Replay
    # =========================================================================

    def get_audit_replay(
        self,
        tenant_id: UUID,
        invoice_id: UUID,
    ) -> Dict[str, Any]:
        """Fetch the complete, append-only chronological audit trail for this invoice."""
        invoice = (
            self.db.query(Invoice)
            .filter(Invoice.tenant_id == tenant_id, Invoice.id == invoice_id)
            .first()
        )
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found in tenant.")

        # Identify all associated entity IDs for this invoice
        doc_ids = [d.id for d in self.db.query(InvoiceDocument).filter(InvoiceDocument.invoice_id == invoice_id).all()]
        draft_ids = [d.id for d in self.db.query(InvoiceDraft).filter(InvoiceDraft.confirmed_invoice_id == invoice_id).all()]
        control_run_ids = [cr.id for cr in self.db.query(ControlRun).filter(ControlRun.invoice_id == invoice_id).all()]
        approval_ids = [a.id for a in self.db.query(Approval).filter(Approval.invoice_id == invoice_id).all()]
        payable_ids = [p.id for p in self.db.query(PayableLedger).filter(PayableLedger.invoice_id == invoice_id).all()]
        payment_ids = [
            pmt.id for pmt in self.db.query(Payment)
            .join(PayableLedger, Payment.payable_id == PayableLedger.id)
            .filter(PayableLedger.invoice_id == invoice_id)
            .all()
        ]

        # Gather audit logs
        # 1. Directly on INVOICE entity
        query = (
            self.db.query(AuditLog)
            .filter(AuditLog.tenant_id == tenant_id)
            .filter(
                (AuditLog.entity_id == invoice_id)
                | (AuditLog.metadata_json["invoice_id"].as_string() == str(invoice_id))
                | (AuditLog.entity_id.in_(doc_ids) if doc_ids else False)
                | (AuditLog.entity_id.in_(draft_ids) if draft_ids else False)
                | (AuditLog.entity_id.in_(control_run_ids) if control_run_ids else False)
                | (AuditLog.entity_id.in_(approval_ids) if approval_ids else False)
                | (AuditLog.entity_id.in_(payable_ids) if payable_ids else False)
                | (AuditLog.entity_id.in_(payment_ids) if payment_ids else False)
            )
            .order_by(AuditLog.created_at.asc())
        )
        logs = query.all()

        timeline: List[Dict[str, Any]] = []

        for log in logs:
            actor_name = log.actor.full_name if log.actor else "System Automation"
            actor_email = log.actor.email if log.actor else None
            role_label = "System"
            if log.actor and log.actor.user_roles:
                first_ur = log.actor.user_roles[0]
                if first_ur.role:
                    role_label = first_ur.role.code

            # Humanized title and description
            title, desc_text, category = self._humanize_audit_action(log.action, log.metadata_json)

            timeline.append({
                "id": str(log.id),
                "timestamp": log.created_at.isoformat(),
                "actor_name": actor_name,
                "actor_email": actor_email,
                "actor_role": role_label,
                "action": log.action,
                "title": title,
                "description": desc_text,
                "category": category,
                "entity_type": log.entity_type,
                "entity_id": str(log.entity_id),
                "previous_state": log.previous_state,
                "new_state": log.new_state,
                "metadata": log.metadata_json,
                "technical_details": {
                    "request_id": log.request_id,
                    "correlation_id": log.correlation_id,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                },
            })

        return {
            "invoice_id": str(invoice_id),
            "invoice_number": invoice.invoice_number,
            "events_count": len(timeline),
            "timeline": timeline,
        }

    def _humanize_audit_action(self, action: str, metadata: Dict[str, Any]) -> tuple[str, str, str]:
        """Convert a technical audit action code into a human-friendly narrative."""
        if action == "INVOICE_DOCUMENT_UPLOADED":
            fn = metadata.get("filename", "document")
            return "Document uploaded", f"Original invoice document '{fn}' uploaded and stored securely.", "INTAKE"
        if action == "INVOICE_DOCUMENT_EXTRACTED":
            conf = metadata.get("overall_confidence", "high")
            return "AI extraction completed", f"Gemini extracted draft invoice fields with confidence {conf}.", "EXTRACTION"
        if action == "INVOICE_DRAFT_UPDATED":
            return "Draft edited by user", "Fields were reviewed and modified by accounts payable user.", "REVIEW"
        if action == "INVOICE_DRAFT_CONFIRMED":
            inv_num = metadata.get("invoice_number", "")
            return "Invoice confirmed", f"Draft confirmed as formal invoice '{inv_num}' in the system.", "INTAKE"
        if action == "INVOICE_CREATED":
            return "Invoice record created", "Invoice entered the accounts payable processing queue.", "INTAKE"
        if action == "CONTROL_RUN_STARTED":
            return "Automated checks started", "Evaluation of 18 deterministic AP controls initiated.", "VALIDATION"
        if action == "CONTROL_RUN_COMPLETED":
            passed = metadata.get("passed_controls", 0)
            failed = metadata.get("failed_controls", 0)
            return "Automated checks completed", f"Evaluation finished: {passed} controls passed, {failed} flagged.", "VALIDATION"
        if action == "EXCEPTION_CREATED":
            code = metadata.get("exception_code", "ISSUE")
            return "Issue flagged", f"Control failure generated exception '{code}'.", "EXCEPTION"
        if action == "EXCEPTION_RESOLVED":
            res = metadata.get("resolution_action", "RESOLVED")
            return "Issue resolved", f"Exception marked as {res} by authorized finance user.", "EXCEPTION"
        if action == "APPROVAL_REQUESTED":
            return "Approval requested", "Invoice submitted for management approval sign-off.", "APPROVAL"
        if action == "INVOICE_APPROVED":
            return "Invoice approved", "Management granted formal authorization for invoice payment.", "APPROVAL"
        if action == "INVOICE_REJECTED":
            return "Invoice rejected", "Management rejected invoice for payment.", "APPROVAL"
        if action == "PAYABLE_CREATED":
            num = metadata.get("payable_number", "")
            return "Added to payment ledger", f"Payable record '{num}' created in general ledger.", "LEDGER"
        if action in ("PAYMENT_RECORDED", "DISBURSEMENT_RECORDED"):
            amt = metadata.get("amount", "")
            return "Payment recorded", f"Funds disbursement of ₹{amt} executed.", "PAYMENT"

        # Fallback
        readable = action.replace("_", " ").title()
        return readable, f"Action '{action}' recorded in audit log.", "GENERAL"

    # =========================================================================
    # FEATURE 5: "What Changed?" (Revision Diff)
    # =========================================================================

    def get_revision_diff(
        self,
        tenant_id: UUID,
        invoice_id: UUID,
    ) -> Dict[str, Any]:
        """Compute structured field-level and line-item differences between invoice revisions."""
        invoice = (
            self.db.query(Invoice)
            .filter(Invoice.tenant_id == tenant_id, Invoice.id == invoice_id)
            .first()
        )
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found in tenant.")

        revisions = (
            self.db.query(InvoiceRevision)
            .filter(InvoiceRevision.tenant_id == tenant_id, InvoiceRevision.invoice_id == invoice_id)
            .order_by(InvoiceRevision.revision_number.asc())
            .all()
        )

        if len(revisions) < 2:
            return {
                "invoice_id": str(invoice_id),
                "invoice_number": invoice.invoice_number,
                "has_multiple_revisions": False,
                "revisions_count": len(revisions),
                "diffs": [],
            }

        # Compare adjacent revisions: Revision N vs Revision N-1
        diff_comparisons: List[Dict[str, Any]] = []

        for i in range(1, len(revisions)):
            rev_old = revisions[i - 1]
            rev_new = revisions[i]

            submitter = (
                self.db.query(User).filter(User.id == rev_new.submitted_by).first()
                if rev_new.submitted_by
                else None
            )

            # Header field comparisons
            header_diffs = []

            def _compare_field(name: str, label: str, old_val: Any, new_val: Any, is_currency: bool = False):
                old_s = str(old_val) if old_val is not None else ""
                new_s = str(new_val) if new_val is not None else ""
                if old_s != new_s:
                    fmt_old = f"₹{old_val:,.2f}" if is_currency and isinstance(old_val, (int, float, Decimal)) else old_s
                    fmt_new = f"₹{new_val:,.2f}" if is_currency and isinstance(new_val, (int, float, Decimal)) else new_s
                    header_diffs.append({
                        "field": name,
                        "label": label,
                        "previous_value": fmt_old,
                        "new_value": fmt_new,
                    })

            _compare_field("subtotal", "Subtotal", rev_old.subtotal, rev_new.subtotal, is_currency=True)
            _compare_field("tax_total", "Tax Total", rev_old.tax_total, rev_new.tax_total, is_currency=True)
            _compare_field("discount_total", "Discount Total", rev_old.discount_total, rev_new.discount_total, is_currency=True)
            _compare_field("grand_total", "Grand Total", rev_old.grand_total, rev_new.grand_total, is_currency=True)
            _compare_field("invoice_number", "Invoice Number", rev_old.invoice_number, rev_new.invoice_number)
            _compare_field("invoice_date", "Invoice Date", rev_old.invoice_date, rev_new.invoice_date)
            _compare_field("due_date", "Due Date", rev_old.due_date, rev_new.due_date)

            # Line items comparison
            items_old = {item.line_number: item for item in rev_old.items}
            items_new = {item.line_number: item for item in rev_new.items}
            all_line_numbers = sorted(set(items_old.keys()) | set(items_new.keys()))

            item_diffs = []
            for num in all_line_numbers:
                it_old = items_old.get(num)
                it_new = items_new.get(num)

                if it_old and not it_new:
                    item_diffs.append({
                        "line_number": num,
                        "change_type": "REMOVED",
                        "description": it_old.description,
                        "previous": f"{it_old.quantity} @ ₹{it_old.unit_price:,.2f} = ₹{it_old.line_total:,.2f}",
                        "current": "Item removed",
                    })
                elif it_new and not it_old:
                    item_diffs.append({
                        "line_number": num,
                        "change_type": "ADDED",
                        "description": it_new.description,
                        "previous": "New item",
                        "current": f"{it_new.quantity} @ ₹{it_new.unit_price:,.2f} = ₹{it_new.line_total:,.2f}",
                    })
                elif it_old and it_new:
                    changes = []
                    if it_old.quantity != it_new.quantity:
                        changes.append(f"Quantity: {it_old.quantity} → {it_new.quantity}")
                    if it_old.unit_price != it_new.unit_price:
                        changes.append(f"Unit Price: ₹{it_old.unit_price:,.2f} → ₹{it_new.unit_price:,.2f}")
                    if it_old.tax_rate != it_new.tax_rate:
                        changes.append(f"Tax Rate: {it_old.tax_rate}% → {it_new.tax_rate}%")
                    if it_old.line_total != it_new.line_total:
                        changes.append(f"Line Total: ₹{it_old.line_total:,.2f} → ₹{it_new.line_total:,.2f}")

                    if changes:
                        item_diffs.append({
                            "line_number": num,
                            "change_type": "MODIFIED",
                            "description": it_new.description,
                            "changes": changes,
                            "previous": f"{it_old.quantity} @ ₹{it_old.unit_price:,.2f} = ₹{it_old.line_total:,.2f}",
                            "current": f"{it_new.quantity} @ ₹{it_new.unit_price:,.2f} = ₹{it_new.line_total:,.2f}",
                        })

            # Check if controls were rerun on new revision
            new_run = (
                self.db.query(ControlRun)
                .filter(ControlRun.invoice_revision_id == rev_new.id)
                .order_by(desc(ControlRun.run_number))
                .first()
            )

            diff_comparisons.append({
                "from_revision_number": rev_old.revision_number,
                "to_revision_number": rev_new.revision_number,
                "changed_by": submitter.full_name if submitter else "AP User",
                "changed_by_email": submitter.email if submitter else None,
                "changed_at": rev_new.created_at.isoformat(),
                "header_diffs": header_diffs,
                "item_diffs": item_diffs,
                "controls_rerun": new_run is not None,
                "resulting_control_status": new_run.status if new_run else "PENDING",
            })

        return {
            "invoice_id": str(invoice_id),
            "invoice_number": invoice.invoice_number,
            "has_multiple_revisions": True,
            "revisions_count": len(revisions),
            "diffs": diff_comparisons,
        }

    # =========================================================================
    # FEATURE 7: Dashboard Control Health
    # =========================================================================

    def get_dashboard_control_health(
        self,
        tenant_id: UUID,
    ) -> Dict[str, Any]:
        """Aggregate real-time control metrics and pass rates across all evaluated invoices."""
        # Query all latest control results for the tenant
        cat_stats = {
            "VENDOR": {"name": "Vendor Integrity", "total": 0, "passed": 0, "failed": 0, "warning": 0},
            "PO": {"name": "Purchase Order", "total": 0, "passed": 0, "failed": 0, "warning": 0},
            "RECEIPT": {"name": "Goods Receipt", "total": 0, "passed": 0, "failed": 0, "warning": 0},
            "FINANCIAL": {"name": "Financial & Tax", "total": 0, "passed": 0, "failed": 0, "warning": 0},
            "DUPLICATE": {"name": "Duplicate Prevention", "total": 0, "passed": 0, "failed": 0, "warning": 0},
            "RISK": {"name": "Risk & Fraud Signals", "total": 0, "passed": 0, "failed": 0, "warning": 0},
        }

        # Map control categories
        cat_map = {
            "VENDOR_EXISTS": "VENDOR",
            "VENDOR_STATUS": "VENDOR",
            "VENDOR_TAX_ID_MATCH": "VENDOR",
            "BANK_DETAILS_MATCH": "VENDOR",
            "PO_EXISTS": "PO",
            "PO_APPROVED": "PO",
            "PO_VENDOR_MATCH": "PO",
            "PO_ITEM_MATCH": "PO",
            "RECEIPT_MATCH": "RECEIPT",
            "QUANTITY_MATCH": "RECEIPT",
            "PRICE_MATCH": "FINANCIAL",
            "TAX_VALIDATION": "FINANCIAL",
            "TOTAL_VALIDATION": "FINANCIAL",
            "PAYMENT_TERMS_VALIDATION": "FINANCIAL",
            "DUPLICATE_EXACT": "DUPLICATE",
            "DUPLICATE_SEMANTIC": "DUPLICATE",
            "THRESHOLD_PROXIMITY": "RISK",
            "UNUSUAL_AMOUNT": "RISK",
        }

        # Query all control results for tenant
        results = (
            self.db.query(ControlResult.control_code, ControlResult.status, func.count(ControlResult.id))
            .filter(ControlResult.tenant_id == tenant_id)
            .group_by(ControlResult.control_code, ControlResult.status)
            .all()
        )

        total_all_checks = 0
        passed_all_checks = 0

        # Recurring failure counts by control code
        recurring_failures: Dict[str, int] = {}

        for code, status, count in results:
            cat_key = cat_map.get(code, "FINANCIAL")
            if cat_key in cat_stats:
                cat_stats[cat_key]["total"] += count
                total_all_checks += count

                if status == ControlStatus.PASS.value:
                    cat_stats[cat_key]["passed"] += count
                    passed_all_checks += count
                elif status == ControlStatus.FAIL.value:
                    cat_stats[cat_key]["failed"] += count
                    recurring_failures[code] = recurring_failures.get(code, 0) + count
                elif status == ControlStatus.WARNING.value:
                    cat_stats[cat_key]["warning"] += count

        # Compute pass rates
        categories_out = []
        for cat_key, c_data in cat_stats.items():
            tot = c_data["total"]
            pass_rate = round((c_data["passed"] / tot * 100), 1) if tot > 0 else 100.0
            categories_out.append({
                "category": cat_key,
                "name": c_data["name"],
                "total_checks": tot,
                "passed_count": c_data["passed"],
                "failed_count": c_data["failed"],
                "warning_count": c_data["warning"],
                "pass_rate_percentage": pass_rate,
            })

        overall_pass_rate = (
            round((passed_all_checks / total_all_checks * 100), 1)
            if total_all_checks > 0
            else 100.0
        )

        # Invoice Status Breakdown
        inv_counts = (
            self.db.query(Invoice.status, func.count(Invoice.id))
            .filter(Invoice.tenant_id == tenant_id)
            .group_by(Invoice.status)
            .all()
        )
        status_dict = {s: cnt for s, cnt in inv_counts}

        # Top recurring issues
        top_issues = []
        for code, fail_count in sorted(recurring_failures.items(), key=lambda x: x[1], reverse=True)[:5]:
            meta = get_control_metadata(code)
            top_issues.append({
                "control_code": code,
                "title": meta.title,
                "failure_count": fail_count,
                "why_it_matters": meta.why_it_matters,
            })

        return {
            "overall_pass_rate_percentage": overall_pass_rate,
            "total_checks_evaluated": total_all_checks,
            "categories": categories_out,
            "status_breakdown": {
                "received": status_dict.get(InvoiceStatus.RECEIVED.value, 0),
                "processing": status_dict.get(InvoiceStatus.PROCESSING.value, 0),
                "needs_attention": status_dict.get(InvoiceStatus.EXCEPTION.value, 0),
                "waiting_for_approval": status_dict.get(InvoiceStatus.AWAITING_APPROVAL.value, 0),
                "approved": status_dict.get(InvoiceStatus.APPROVED.value, 0),
                "payable": status_dict.get(InvoiceStatus.PAYABLE_CREATED.value, 0) + status_dict.get("PARTIALLY_PAID", 0),
                "paid": status_dict.get(InvoiceStatus.PAID.value, 0),
                "rejected": status_dict.get(InvoiceStatus.REJECTED.value, 0),
            },
            "top_recurring_issues": top_issues,
        }
