"""AP Control Scenario Simulator Service.

Provides isolated, in-memory simulation of Accounts Payable controls,
"What-If" parameter perturbation, before/after diffs, and hackathon demo workflows.

CORE INVARIANT:
Simulation is strictly read-only relative to production tables.
NEVER creates invoices, payables, disbursements, or audit logs.
"""
from copy import deepcopy
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from backend.database.models.ap import (
    Invoice,
    InvoiceRevision,
    InvoiceItem,
    ControlRun,
    ControlResult,
    Exception as APException,
    RiskSignal,
)
from backend.database.models.procurement import (
    Vendor,
    PurchaseOrder,
    PurchaseOrderItem,
    GoodsReceipt,
    GoodsReceiptItem,
)
from backend.domain.controls.base import ControlContext
from backend.domain.controls.registry import default_registry
from backend.domain.decisions.invoice_decision import InvoiceDecisionEngine
from backend.application.dto.control_dto import ControlEvaluation, ToleranceConfig
from backend.application.dto.decision_dto import DecisionOutcome, InvoiceDecision
from backend.domain.risk.scoring_model import (
    RiskScoringModel,
    RiskLevel,
    RiskCategory,
    default_scoring_model,
)
from backend.api.schemas.risk_schemas import (
    ScenarioSummaryOut,
    ScenarioSimulationInputOut,
    ScenarioControlCheckOut,
    ScenarioSimulationResponseOut,
    WhatIfRequest,
    ControlImpactItemOut,
    SimulationDiffOut,
    ControlImpactMapNodeOut,
    WhatIfSimulationResponseOut,
    DemoStepOut,
    InvoiceRiskProfileOut,
    RiskFactorOut,
    ControlSummaryOut,
)


SCENARIO_DEFINITIONS = [
    {
        "id": "scenario-a",
        "code": "Scenario A",
        "name": "Clean 3-Way Match",
        "invoice_number": "INV-2026-0001",
        "expected_outcome": "APPROVED",
        "primary_control": "ALL_CONTROLS_PASS",
        "risk_category": "LOW_RISK",
        "summary": "Flawless invoice with exact purchase order and goods receipt matching.",
        "description": "Invoice matches approved PO unit price and accepted warehouse quantity across all lines. 18 deterministic controls pass.",
    },
    {
        "id": "scenario-b",
        "code": "Scenario B",
        "name": "Quantity Mismatch",
        "invoice_number": "INV-2026-0002",
        "expected_outcome": "EXCEPTION",
        "primary_control": "QUANTITY_MATCH",
        "risk_category": "RECEIPT_RISK",
        "summary": "Billed quantity exceeds warehouse accepted goods receipt quantity.",
        "description": "Vendor invoiced for 100 units, but warehouse verified and accepted only 80 units. Discrepancy triggers QUANTITY_MATCH failure.",
    },
    {
        "id": "scenario-c",
        "code": "Scenario C",
        "name": "Price Mismatch",
        "invoice_number": "INV-2026-0003",
        "expected_outcome": "EXCEPTION",
        "primary_control": "PRICE_MATCH",
        "risk_category": "FINANCIAL_RISK",
        "summary": "Invoiced unit price is higher than agreed purchase order contract price.",
        "description": "Invoice charges ₹2,000 above agreed PO price. PRICE_MATCH control blocks approval to prevent unapproved cost overruns.",
    },
    {
        "id": "scenario-d",
        "code": "Scenario D",
        "name": "PO Not Found",
        "invoice_number": "INV-2026-0004",
        "expected_outcome": "EXCEPTION",
        "primary_control": "PO_EXISTS",
        "risk_category": "PURCHASE_ORDER_RISK",
        "summary": "Invoice references non-existent or unauthorized purchase order.",
        "description": "Spend authorization control fails because referenced PO does not exist in procurement master.",
    },
    {
        "id": "scenario-e",
        "code": "Scenario E",
        "name": "Vendor Mismatch",
        "invoice_number": "INV-2026-0005",
        "expected_outcome": "EXCEPTION",
        "primary_control": "PO_VENDOR_MATCH",
        "risk_category": "VENDOR_RISK",
        "summary": "Invoice vendor does not match contracting vendor on purchase order.",
        "description": "Invoice submitted by a vendor different from the approved PO vendor. High fraud/diversion risk.",
    },
    {
        "id": "scenario-f",
        "code": "Scenario F",
        "name": "Partial Receipt Matching",
        "invoice_number": "INV-2026-0006",
        "expected_outcome": "AWAITING_APPROVAL",
        "primary_control": "RECEIPT_MATCH",
        "risk_category": "RECEIPT_RISK",
        "summary": "Invoiced quantity matches partial warehouse delivery without over-billing.",
        "description": "Total PO is 100 units, but partial shipment of 50 units was received and invoiced. Legitimate partial match passes controls.",
    },
    {
        "id": "scenario-g",
        "code": "Scenario G",
        "name": "Exact Duplicate Submission",
        "invoice_number": "INV-2026-0007",
        "expected_outcome": "EXCEPTION",
        "primary_control": "DUPLICATE_EXACT",
        "risk_category": "DUPLICATE_RISK",
        "summary": "Identical document SHA-256 hash collision with previously processed invoice.",
        "description": "SHA-256 fingerprint exactly collides with INV-2026-0001. Control engine blocks to prevent double-payment.",
    },
    {
        "id": "scenario-h",
        "code": "Scenario H",
        "name": "Semantic Duplicate Check",
        "invoice_number": "INV-2026-0008",
        "expected_outcome": "AWAITING_APPROVAL",
        "primary_control": "DUPLICATE_SEMANTIC",
        "risk_category": "DUPLICATE_RISK",
        "summary": "Near-match semantic analysis evaluates vector similarity.",
        "description": "Invoice shares similar parameters with existing bills but passes semantic duplicate thresholds.",
    },
    {
        "id": "scenario-i",
        "code": "Scenario I",
        "name": "Tax Calculation Discrepancy",
        "invoice_number": "INV-2026-0009",
        "expected_outcome": "EXCEPTION",
        "primary_control": "TAX_VALIDATION",
        "risk_category": "FINANCIAL_RISK",
        "summary": "Invoiced GST/tax rate (12%) deviates from contracted purchase order tax rate (18%).",
        "description": "Tax variance control fails to protect against input tax credit disqualification and audit penalties.",
    },
    {
        "id": "scenario-j",
        "code": "Scenario J",
        "name": "Header Total Mismatch",
        "invoice_number": "INV-2026-0010",
        "expected_outcome": "EXCEPTION",
        "primary_control": "TOTAL_VALIDATION",
        "risk_category": "FINANCIAL_RISK",
        "summary": "Grand total does not equal subtotal minus discount plus tax.",
        "description": "Internal arithmetic validation fails because header total does not match line item calculations.",
    },
    {
        "id": "scenario-k",
        "code": "Scenario K",
        "name": "Bank Details Mismatch",
        "invoice_number": "INV-2026-0011",
        "expected_outcome": "EXCEPTION",
        "primary_control": "BANK_DETAILS_MATCH",
        "risk_category": "PAYMENT_RISK",
        "summary": "Invoice remittance account differs from verified vendor master bank records.",
        "description": "Critical cyber-fraud control failure: Remittance account does not match official vendor bank records.",
    },
    {
        "id": "scenario-l",
        "code": "Scenario L",
        "name": "Threshold Proximity Warning",
        "invoice_number": "INV-2026-0012",
        "expected_outcome": "AWAITING_APPROVAL",
        "primary_control": "THRESHOLD_PROXIMITY",
        "risk_category": "APPROVAL_RISK",
        "summary": "Invoice amount is ₹10 below the ₹50,000 Tier 1 approval ceiling.",
        "description": "Generates a non-blocking warning flag to alert managers to potential deliberate limit splitting.",
    },
    {
        "id": "scenario-m",
        "code": "Scenario M",
        "name": "Revision 2 Correction",
        "invoice_number": "INV-2026-0013",
        "expected_outcome": "APPROVED",
        "primary_control": "ALL_CONTROLS_PASS",
        "risk_category": "LOW_RISK",
        "summary": "Revision 1 had price variance; Revision 2 corrected price and passed all controls.",
        "description": "Demonstrates invoice lifecycle: Initial revision had discrepancies, vendor re-issued corrected Revision 2 which cleared.",
    },
    {
        "id": "scenario-n",
        "code": "Scenario N",
        "name": "Payable & Partial Disbursement",
        "invoice_number": "INV-2026-0014",
        "expected_outcome": "PAYABLE_CREATED",
        "primary_control": "ALL_CONTROLS_PASS",
        "risk_category": "PAYMENT_RISK",
        "summary": "Approved invoice committed to payable ledger with partial payment recorded.",
        "description": "Illustrates downstream ledger behavior: Once approved, payable is created and partial disbursement recorded.",
    },
    {
        "id": "scenario-o",
        "code": "Scenario O",
        "name": "Rejected Invoice",
        "invoice_number": "INV-2026-0015",
        "expected_outcome": "REJECTED",
        "primary_control": "PRICE_MATCH",
        "risk_category": "FINANCIAL_RISK",
        "summary": "Unapproved price discrepancy was formally reviewed and rejected by finance.",
        "description": "Formal managerial rejection workflow: Variance was considered unacceptable and invoice was cancelled.",
    },
]


class ScenarioSimulatorService:
    def __init__(self, db: Session, scoring_model: Optional[RiskScoringModel] = None):
        self.db = db
        self.scoring_model = scoring_model or default_scoring_model
        self.decision_engine = InvoiceDecisionEngine()

    def list_scenarios(self, tenant_id: UUID) -> List[ScenarioSummaryOut]:
        """List all 15 scenarios with matched database IDs if available."""
        summaries = []
        for s in SCENARIO_DEFINITIONS:
            inv = (
                self.db.query(Invoice)
                .filter(Invoice.invoice_number == s["invoice_number"], Invoice.tenant_id == tenant_id)
                .first()
            )
            summaries.append(
                ScenarioSummaryOut(
                    scenario_id=s["id"],
                    scenario_code=s["code"],
                    scenario_name=s["name"],
                    invoice_number=s["invoice_number"],
                    invoice_id=inv.id if inv else None,
                    expected_outcome=s["expected_outcome"],
                    primary_control=s["primary_control"],
                    risk_category=s["risk_category"],
                    summary=s["summary"],
                    description=s["description"],
                )
            )
        return summaries

    def _resolve_scenario_def(self, scenario_identifier: str) -> Dict[str, Any]:
        """Resolve a scenario definition by ID, code, or invoice number."""
        ident_clean = scenario_identifier.strip().lower().replace("_", "-")
        for s in SCENARIO_DEFINITIONS:
            if (
                s["id"].lower() == ident_clean
                or s["code"].lower() == ident_clean
                or s["code"].lower().replace(" ", "-") == ident_clean
                or s["code"].split()[-1].lower() == ident_clean
                or s["invoice_number"].lower() == ident_clean
            ):
                return s
        # Fallback to scenario A
        return SCENARIO_DEFINITIONS[0]

    def get_scenario_detail(self, tenant_id: UUID, scenario_id: str) -> ScenarioSummaryOut:
        """Get detail for a specific scenario."""
        s = self._resolve_scenario_def(scenario_id)
        inv = (
            self.db.query(Invoice)
            .filter(Invoice.invoice_number == s["invoice_number"], Invoice.tenant_id == tenant_id)
            .first()
        )
        return ScenarioSummaryOut(
            scenario_id=s["id"],
            scenario_code=s["code"],
            scenario_name=s["name"],
            invoice_number=s["invoice_number"],
            invoice_id=inv.id if inv else None,
            expected_outcome=s["expected_outcome"],
            primary_control=s["primary_control"],
            risk_category=s["risk_category"],
            summary=s["summary"],
            description=s["description"],
        )

    def _build_simulation_context(
        self,
        tenant_id: UUID,
        invoice: Invoice,
        what_if_overrides: Optional[WhatIfRequest] = None,
    ) -> tuple[ControlContext, Dict[str, Any]]:
        """Construct an in-memory ControlContext, optionally applying parameter overrides."""
        rev = None
        if invoice.revisions:
            for r in invoice.revisions:
                if r.id == invoice.current_revision_id:
                    rev = r
                    break
            if not rev:
                rev = invoice.revisions[-1]

        vendor = invoice.vendor
        po = invoice.purchase_order
        po_items = list(po.items) if po else []
        grs = list(po.goods_receipts) if po else []
        gr_items = []
        for g in grs:
            gr_items.extend(list(g.items))

        # Clone objects into transient in-memory models to guarantee zero DB mutation
        sim_rev = None
        sim_items = []
        if rev:
            sim_rev = InvoiceRevision(
                id=rev.id,
                tenant_id=rev.tenant_id,
                invoice_id=rev.invoice_id,
                revision_number=rev.revision_number,
                invoice_number=rev.invoice_number,
                invoice_date=rev.invoice_date,
                due_date=rev.due_date,
                currency=rev.currency,
                subtotal=Decimal(str(rev.subtotal)),
                tax_total=Decimal(str(rev.tax_total)),
                grand_total=Decimal(str(rev.grand_total)),
                discount_total=Decimal(str(rev.discount_total or "0.00")),
                vendor_name_as_submitted=rev.vendor_name_as_submitted,
                vendor_tax_id_as_submitted=rev.vendor_tax_id_as_submitted,
                bank_account_hash=rev.bank_account_hash,
                bank_account_last4=rev.bank_account_last4,
            )
            sim_items = [
                InvoiceItem(
                    id=it.id,
                    tenant_id=it.tenant_id,
                    invoice_revision_id=it.invoice_revision_id,
                    line_number=it.line_number,
                    description=it.description,
                    product_code=it.product_code,
                    quantity=Decimal(str(it.quantity)),
                    unit_price=Decimal(str(it.unit_price)),
                    tax_rate=Decimal(str(it.tax_rate)),
                    tax_amount=Decimal(str(it.tax_amount)),
                    discount_amount=Decimal(str(it.discount_amount or "0.00")),
                    line_total=Decimal(str(it.line_total)),
                )
                for it in rev.items
            ]

        sim_gr_items = [
            GoodsReceiptItem(
                id=gi.id,
                tenant_id=gi.tenant_id,
                goods_receipt_id=gi.goods_receipt_id,
                purchase_order_item_id=gi.purchase_order_item_id,
                accepted_quantity=Decimal(str(gi.accepted_quantity)),
                received_quantity=Decimal(str(gi.received_quantity)),
                rejected_quantity=Decimal(str(gi.rejected_quantity or "0.00")),
            )
            for gi in gr_items
        ]

        # Track what changed if overrides applied
        changes_applied = []

        has_financial_changes = (
            what_if_overrides is not None
            and any([
                what_if_overrides.quantity is not None,
                what_if_overrides.unit_price is not None,
                what_if_overrides.tax_rate is not None,
            ])
        )

        if what_if_overrides:
            # Override line item quantity
            if what_if_overrides.quantity is not None and sim_items:
                old_qty = sim_items[0].quantity
                sim_items[0].quantity = Decimal(str(what_if_overrides.quantity))
                changes_applied.append({
                    "field": "Line Item Quantity",
                    "before": f"{old_qty}",
                    "after": f"{what_if_overrides.quantity}",
                })

            # Override line item unit price
            if what_if_overrides.unit_price is not None and sim_items:
                old_price = sim_items[0].unit_price
                sim_items[0].unit_price = Decimal(str(what_if_overrides.unit_price))
                changes_applied.append({
                    "field": "Line Item Unit Price",
                    "before": f"₹{old_price}",
                    "after": f"₹{what_if_overrides.unit_price}",
                })

            # Override tax rate
            if what_if_overrides.tax_rate is not None and sim_items:
                old_tax = sim_items[0].tax_rate
                new_tax_rate = Decimal(str(what_if_overrides.tax_rate))
                rate_multiplier = new_tax_rate / Decimal("100.00") if new_tax_rate > Decimal("1.0") else new_tax_rate
                for it in sim_items:
                    it.tax_rate = rate_multiplier
                changes_applied.append({
                    "field": "Tax Rate",
                    "before": f"{old_tax}%",
                    "after": f"{new_tax_rate}%",
                })

            # Recompute all item tax amounts and revision totals consistently ONLY if financial changes occurred
            if has_financial_changes and sim_rev and sim_items:
                total_sub = Decimal("0.00")
                total_tax = Decimal("0.00")
                for it in sim_items:
                    taxable = (it.unit_price * it.quantity) - Decimal(str(it.discount_amount or "0.00"))
                    rm = it.tax_rate / Decimal("100.00") if it.tax_rate > Decimal("1.0") else it.tax_rate
                    it.tax_amount = (taxable * rm).quantize(Decimal("0.01"))
                    it.line_total = taxable + it.tax_amount
                    total_sub += taxable
                    total_tax += it.tax_amount
                sim_rev.subtotal = total_sub
                sim_rev.tax_total = total_tax
                disc = Decimal(str(sim_rev.discount_total or "0.00"))
                sim_rev.grand_total = sim_rev.subtotal + sim_rev.tax_total - disc

            # Override receipt quantity
            if what_if_overrides.receipt_quantity is not None and sim_gr_items:
                old_gr = sim_gr_items[0].accepted_quantity
                sim_gr_items[0].accepted_quantity = Decimal(str(what_if_overrides.receipt_quantity))
                changes_applied.append({
                    "field": "Goods Receipt Accepted Quantity",
                    "before": f"{old_gr}",
                    "after": f"{what_if_overrides.receipt_quantity}",
                })

            # Override PO presence
            if what_if_overrides.has_po is False:
                po = None
                po_items = []
                grs = []
                sim_gr_items = []
                changes_applied.append({
                    "field": "Purchase Order",
                    "before": "Attached",
                    "after": "Detached (Missing PO)",
                })

            # Override vendor match
            if what_if_overrides.match_vendor is True and po and po.vendor:
                old_v = vendor.display_name if vendor else "Different Vendor"
                vendor = po.vendor
                changes_applied.append({
                    "field": "Vendor Match",
                    "before": f"{old_v}",
                    "after": f"{vendor.display_name} (Matches PO)",
                })

            # Override bank details match
            if what_if_overrides.bank_details_match is True and vendor:
                if sim_rev:
                    sim_rev.bank_account_hash = vendor.bank_account_hash
                    sim_rev.bank_account_last4 = vendor.bank_account_last4
                changes_applied.append({
                    "field": "Remittance Bank Account",
                    "before": "Mismatched Account",
                    "after": "Verified Vendor Account",
                })

        context = ControlContext(
            tenant_id=tenant_id,
            invoice=invoice,
            current_revision=sim_rev,
            invoice_items=sim_items,
            vendor=vendor,
            purchase_order=po,
            po_items=po_items,
            goods_receipts=grs,
            goods_receipt_items=sim_gr_items,
            approval_policies=[],
            historical_invoices=[],
            tolerance_config=ToleranceConfig(),
        )

        # Snapshot inputs for display
        inputs_snapshot = {
            "invoice": {
                "invoice_number": invoice.invoice_number,
                "grand_total": str(sim_rev.grand_total if sim_rev else "0.00"),
                "subtotal": str(sim_rev.subtotal if sim_rev else "0.00"),
                "tax_total": str(sim_rev.tax_total if sim_rev else "0.00"),
                "item_count": len(sim_items),
                "first_item_qty": str(sim_items[0].quantity) if sim_items else "0",
                "first_item_price": str(sim_items[0].unit_price) if sim_items else "0",
            },
            "purchase_order": {
                "po_number": po.po_number,
                "grand_total": str(po.grand_total),
                "vendor_name": po.vendor.display_name if po and po.vendor else "Unknown",
            } if po else None,
            "vendor": {
                "name": vendor.display_name if vendor else "Unknown",
                "code": vendor.vendor_code if vendor else "—",
                "tax_id": vendor.tax_identifier if vendor else "—",
            } if vendor else None,
            "goods_receipts": [
                {
                    "receipt_number": g.receipt_number,
                    "accepted_qty": str(sim_gr_items[0].accepted_quantity) if sim_gr_items else "0",
                }
                for g in grs
            ],
        }

        return context, {"inputs": inputs_snapshot, "changes": changes_applied}

    def simulate_scenario(
        self,
        tenant_id: UUID,
        scenario_id: str,
        overrides: Optional[WhatIfRequest] = None,
    ) -> ScenarioSimulationResponseOut:
        """Run complete deterministic control simulation in-memory."""
        s = self._resolve_scenario_def(scenario_id)

        # Find representative invoice
        invoice = (
            self.db.query(Invoice)
            .filter(Invoice.invoice_number == s["invoice_number"], Invoice.tenant_id == tenant_id)
            .first()
        )

        if not invoice:
            # Fallback to first invoice in tenant
            invoice = self.db.query(Invoice).filter(Invoice.tenant_id == tenant_id).first()

        context, meta = self._build_simulation_context(tenant_id, invoice, overrides)

        # Execute controls in-memory
        evaluations: List[ControlEvaluation] = []
        for ctrl in default_registry.controls:
            try:
                ev = ctrl.execute(context)
            except Exception as ex:
                ev = ControlEvaluation(
                    control_code=ctrl.control_code,
                    category=ctrl.category,
                    status="ERROR",
                    severity="HIGH",
                    message=f"Simulation error: {str(ex)}",
                    rule_version=ctrl.rule_version,
                )
            evaluations.append(ev)

        # Evaluate decision
        decision = self.decision_engine.evaluate(evaluations)

        # Format control checks
        checks_out: List[ScenarioControlCheckOut] = []
        for ev in evaluations:
            status_str = ev.status.value if hasattr(ev.status, "value") else str(ev.status)
            st_upper = status_str.upper()
            status_normalized = (
                "FAILED" if st_upper in ("FAIL", "FAILED", "ERROR")
                else "PASSED" if st_upper in ("PASS", "PASSED")
                else "WARNING" if st_upper in ("WARN", "WARNING")
                else st_upper
            )
            sev_str = ev.severity.value if hasattr(ev.severity, "value") else str(ev.severity)
            checks_out.append(
                ScenarioControlCheckOut(
                    control_code=ev.control_code,
                    title=ev.control_code.replace("_", " ").title(),
                    status=status_normalized,
                    severity=sev_str.upper(),
                    variance=str(ev.variance_value) if ev.variance_value is not None else None,
                    message=ev.message,
                )
            )

        # Compute risk profile
        profile_data = self.scoring_model.calculate_profile(
            control_results=evaluations,
            exceptions=[],
            risk_signals=[],
        )

        score = profile_data["risk_score"]
        level = profile_data["risk_level"]
        factors = profile_data["risk_factors"]
        c_summary = profile_data["control_summary"]

        factors_out = [
            RiskFactorOut(
                code=f.code,
                title=f.title,
                severity=f.severity,
                category=f.category,
                description=f.description,
                evidence=f.evidence,
                source=f.source,
                why_it_matters=f.why_it_matters,
                recommended_action=f.recommended_action,
                score_contribution=f.score_contribution,
            )
            for f in factors
        ]

        risk_profile_out = InvoiceRiskProfileOut(
            invoice_id=invoice.id,
            invoice_number=invoice.invoice_number,
            risk_level=level,
            risk_score=score,
            risk_factors=factors_out,
            control_summary=ControlSummaryOut(**c_summary),
            recommended_attention=score >= 50 or level in ("HIGH", "CRITICAL"),
            headline=f"{level} RISK ({score}/100)",
            summary=f"Simulation evaluated {len(evaluations)} controls: {c_summary['passed']} passed, {c_summary['failed']} failed.",
        )

        outcome_str = decision.outcome.value if hasattr(decision.outcome, "value") else str(decision.outcome)
        next_action = (
            "Ready for managerial approval and payable creation."
            if outcome_str in ("PASS", "PASS_WITH_WARNING")
            else "Resolve exceptions with vendor or procurement before payment authorization."
        )

        return ScenarioSimulationResponseOut(
            scenario_id=s["id"],
            scenario_code=s["code"],
            scenario_name=s["name"],
            inputs=ScenarioSimulationInputOut(**meta["inputs"]),
            control_checks=checks_out,
            risk_profile=risk_profile_out,
            decision=outcome_str,
            next_action=next_action,
        )

    def simulate_what_if(
        self,
        tenant_id: UUID,
        scenario_id: str,
        request: WhatIfRequest,
    ) -> WhatIfSimulationResponseOut:
        """Run before/after simulation comparison showing input diff and control impacts."""
        s = self._resolve_scenario_def(scenario_id)

        # 1. Baseline simulation (Original)
        original = self.simulate_scenario(tenant_id, scenario_id, overrides=None)

        # 2. Simulated run with overrides
        simulated = self.simulate_scenario(tenant_id, scenario_id, overrides=request)

        # 3. Compute control diffs
        orig_map = {c.control_code: c for c in original.control_checks}
        affected_controls: List[ControlImpactItemOut] = []

        for c_sim in simulated.control_checks:
            c_orig = orig_map.get(c_sim.control_code)
            if c_orig and c_orig.status != c_sim.status:
                affected_controls.append(
                    ControlImpactItemOut(
                        control_code=c_sim.control_code,
                        title=c_sim.title,
                        before_status=c_orig.status,
                        after_status=c_sim.status,
                        severity=c_sim.severity,
                        message=c_sim.message,
                    )
                )

        # Track changed inputs
        changed_inputs = []
        if request.quantity is not None:
            changed_inputs.append({
                "parameter": "Quantity",
                "before": original.inputs.invoice.get("first_item_qty", "—"),
                "after": str(request.quantity),
            })
        if request.unit_price is not None:
            changed_inputs.append({
                "parameter": "Unit Price",
                "before": f"₹{original.inputs.invoice.get('first_item_price', '—')}",
                "after": f"₹{request.unit_price}",
            })
        if request.tax_rate is not None:
            changed_inputs.append({
                "parameter": "Tax Rate",
                "before": "Standard Rate",
                "after": f"{Decimal(str(request.tax_rate))*100}%",
            })
        if request.receipt_quantity is not None:
            changed_inputs.append({
                "parameter": "Goods Receipt Qty",
                "before": original.inputs.goods_receipts[0]["accepted_qty"] if original.inputs.goods_receipts else "—",
                "after": str(request.receipt_quantity),
            })
        if request.match_vendor is True:
            changed_inputs.append({
                "parameter": "Vendor Match",
                "before": "Different Vendor",
                "after": "Matched PO Vendor",
            })
        if request.has_po is False:
            changed_inputs.append({
                "parameter": "Purchase Order",
                "before": "Attached",
                "after": "Missing PO",
            })

        before_score = original.risk_profile.risk_score
        after_score = simulated.risk_profile.risk_score
        before_decision = original.decision
        after_decision = simulated.decision

        diff_out = SimulationDiffOut(
            changed_inputs=changed_inputs,
            affected_controls=affected_controls,
            before_risk_score=before_score,
            after_risk_score=after_score,
            before_risk_level=original.risk_profile.risk_level,
            after_risk_level=simulated.risk_profile.risk_level,
            before_decision=before_decision,
            after_decision=after_decision,
            outcome_changed=before_decision != after_decision,
            risk_reduced=after_score < before_score,
        )

        # Build impact map
        impact_map: List[ControlImpactMapNodeOut] = []
        for inp in changed_inputs:
            ctrl_names = [ac.control_code for ac in affected_controls]
            category = "FINANCIAL_RISK" if "Price" in inp["parameter"] else ("RECEIPT_RISK" if "Quantity" in inp["parameter"] else "GENERAL_RISK")
            impact_map.append(
                ControlImpactMapNodeOut(
                    changed_input=inp["parameter"],
                    affected_controls=ctrl_names or ["VERIFICATION_CHECKS"],
                    risk_category=category,
                    final_outcome=after_decision,
                )
            )

        return WhatIfSimulationResponseOut(
            scenario_id=s["id"],
            scenario_code=s["code"],
            original_simulation=original,
            simulated_output=simulated,
            diff=diff_out,
            impact_map=impact_map,
        )

    def get_demo_steps(self, tenant_id: UUID, scenario_id: str) -> List[DemoStepOut]:
        """Generate structured presentation demo steps for hackathon walkthrough."""
        s = self._resolve_scenario_def(scenario_id)
        return [
            DemoStepOut(
                step_number=1,
                step_code="INTAKE_EXTRACT",
                title="1. Invoice Intake & AI Extraction",
                description="Invoice PDF received and securely parsed by Gemini into structured fields with confidence scores.",
                action_taken="Extracted invoice number, vendor tax ID, amounts, and line items.",
                result_status="EXTRACTED",
                key_metric="98.5% confidence",
                invoice_number=s["invoice_number"],
            ),
            DemoStepOut(
                step_number=2,
                step_code="CONTROL_RUN",
                title="2. Automated Control Evaluation",
                description="The 18 deterministic financial controls execute against PO, receipt, vendor master, and duplicates.",
                action_taken=f"Evaluated scenario: {s['name']}.",
                result_status="EVALUATED",
                key_metric="18 controls checked",
                invoice_number=s["invoice_number"],
            ),
            DemoStepOut(
                step_number=3,
                step_code="RISK_EXPLANATION",
                title="3. Risk Intelligence & Scoring",
                description="Deterministic scoring calculates risk level and generates human-friendly What Happened / Why It Matters / What To Do.",
                action_taken="Evaluated variance magnitude and policy limits.",
                result_status="EXPLAINED",
                key_metric="Risk Profile Computed",
                invoice_number=s["invoice_number"],
            ),
            DemoStepOut(
                step_number=4,
                step_code="DECISION_ROUTING",
                title="4. Decision Engine & Routing",
                description="Decision engine categorizes invoice into Awaiting Approval or Exception for human resolution.",
                action_taken=f"Rendered outcome: {s['expected_outcome']}.",
                result_status=s["expected_outcome"],
                key_metric=f"Outcome: {s['expected_outcome']}",
                invoice_number=s["invoice_number"],
            ),
            DemoStepOut(
                step_number=5,
                step_code="WHAT_IF_RESOLUTION",
                title="5. What-If Simulation & Correction",
                description="Finance user simulates parameter correction (e.g. credit note or quantity alignment) in isolated simulation state.",
                action_taken="Simulated input adjustment and verified control resolution.",
                result_status="SIMULATED",
                key_metric="Risk reduced to LOW",
                invoice_number=s["invoice_number"],
            ),
            DemoStepOut(
                step_number=6,
                step_code="GOLDEN_TRANSACTION",
                title="6. Approval & Golden Transaction",
                description="Upon managerial sign-off, invoice atomically transitions to PAYABLE_CREATED in the immutable ledger.",
                action_taken="Committed to ap.payable_ledger with cryptographic audit event.",
                result_status="PAYABLE_CREATED",
                key_metric="Ledger Entry Created",
                invoice_number=s["invoice_number"],
            ),
        ]
