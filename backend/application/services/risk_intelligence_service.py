"""Risk Intelligence Service.

Computes deterministic risk profiles, risk signals, and dashboard risk analytics
for the Accounts Payable Control System.
"""
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database.models.ap import (
    Invoice,
    ControlRun,
    ControlResult,
    Exception as APException,
    RiskSignal,
)
from backend.database.models.procurement import Vendor
from backend.domain.risk.scoring_model import (
    RiskScoringModel,
    RiskLevel,
    RiskCategory,
    RiskFactor,
    default_scoring_model,
)
from backend.domain.controls.metadata import CONTROL_METADATA_REGISTRY
from backend.api.schemas.risk_schemas import (
    RiskFactorOut,
    ControlSummaryOut,
    InvoiceRiskProfileOut,
    TopRiskDriverOut,
    HighestRiskInvoiceOut,
    DashboardRiskOverviewOut,
)


class RiskIntelligenceService:
    def __init__(self, db: Session, scoring_model: Optional[RiskScoringModel] = None):
        self.db = db
        self.scoring_model = scoring_model or default_scoring_model

    def get_invoice_risk_profile(self, tenant_id: UUID, invoice_id: UUID) -> InvoiceRiskProfileOut:
        """Calculate the deterministic risk profile for a specific invoice."""
        invoice = self.db.query(Invoice).filter(
            Invoice.id == invoice_id,
            Invoice.tenant_id == tenant_id,
        ).first()

        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found in tenant {tenant_id}.")

        # 1. Fetch latest control results
        latest_run = (
            self.db.query(ControlRun)
            .filter(ControlRun.invoice_id == invoice_id, ControlRun.tenant_id == tenant_id)
            .order_by(ControlRun.run_number.desc())
            .first()
        )

        control_results = []
        if latest_run:
            control_results = (
                self.db.query(ControlResult)
                .filter(ControlResult.control_run_id == latest_run.id)
                .all()
            )

        # 2. Fetch active exceptions
        exceptions = (
            self.db.query(APException)
            .filter(
                APException.invoice_id == invoice_id,
                APException.tenant_id == tenant_id,
                APException.status.in_(["OPEN", "IN_REVIEW"]),
            )
            .all()
        )

        # 3. Fetch active risk signals
        risk_signals = (
            self.db.query(RiskSignal)
            .filter(
                RiskSignal.invoice_id == invoice_id,
                RiskSignal.tenant_id == tenant_id,
                RiskSignal.status == "ACTIVE",
            )
            .all()
        )

        # 4. Compute profile via deterministic scoring model
        profile_data = self.scoring_model.calculate_profile(
            control_results=control_results,
            exceptions=exceptions,
            risk_signals=risk_signals,
        )

        score = profile_data["risk_score"]
        level = profile_data["risk_level"]
        factors: List[RiskFactor] = profile_data["risk_factors"]
        c_summary = profile_data["control_summary"]
        recommended_attention = profile_data["recommended_attention"]

        # Build headline and summary
        if level == RiskLevel.CRITICAL.value:
            top_reason = factors[0].title if factors else "Critical compliance failure"
            headline = f"CRITICAL RISK ({score}/100) — Payment Blocked"
            summary = f"Invoice presents severe financial or integrity risk. Primary issue: {top_reason}."
        elif level == RiskLevel.HIGH.value:
            top_reason = factors[0].title if factors else "Major control discrepancy"
            headline = f"HIGH RISK ({score}/100) — Review Required"
            summary = f"Invoice has significant variances preventing payment authorization ({top_reason})."
        elif level == RiskLevel.MEDIUM.value:
            headline = f"MEDIUM RISK ({score}/100) — Caution Advised"
            summary = "Invoice passed mandatory 3-way controls but triggered secondary warnings or threshold rules."
        else:
            headline = f"LOW RISK ({score}/100) — Clean Evaluation"
            summary = "All mandatory purchase order, goods receipt, and vendor controls evaluated successfully."

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

        return InvoiceRiskProfileOut(
            invoice_id=invoice.id,
            invoice_number=invoice.invoice_number,
            risk_level=level,
            risk_score=score,
            risk_factors=factors_out,
            control_summary=ControlSummaryOut(**c_summary),
            recommended_attention=recommended_attention,
            headline=headline,
            summary=summary,
        )

    def get_dashboard_risk_overview(self, tenant_id: UUID) -> DashboardRiskOverviewOut:
        """Compute aggregated risk metrics across all tenant invoices."""
        invoices = (
            self.db.query(Invoice)
            .filter(Invoice.tenant_id == tenant_id)
            .all()
        )

        if not invoices:
            return DashboardRiskOverviewOut(
                critical_count=0,
                high_count=0,
                medium_count=0,
                low_count=0,
                total_evaluated=0,
                average_risk_score=0.0,
                top_risk_drivers=[],
                highest_risk_invoices=[],
            )

        critical_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0
        total_score = 0
        invoice_profiles = []

        driver_counts: Dict[str, int] = {}
        driver_meta: Dict[str, Dict[str, str]] = {}

        for inv in invoices:
            # Quick profile calculation
            profile = self.get_invoice_risk_profile(tenant_id, inv.id)
            score = profile.risk_score
            level = profile.risk_level

            total_score += score
            if level == RiskLevel.CRITICAL.value:
                critical_count += 1
            elif level == RiskLevel.HIGH.value:
                high_count += 1
            elif level == RiskLevel.MEDIUM.value:
                medium_count += 1
            else:
                low_count += 1

            vendor_name = inv.vendor.display_name or inv.vendor.legal_name if inv.vendor else "Unknown Vendor"
            curr_rev = None
            if inv.revisions:
                for r in inv.revisions:
                    if r.id == inv.current_revision_id:
                        curr_rev = r
                        break
                if not curr_rev:
                    curr_rev = inv.revisions[-1]
            grand_total = curr_rev.grand_total if curr_rev else Decimal("0.00")
            primary_factor = profile.risk_factors[0].title if profile.risk_factors else "None"

            invoice_profiles.append({
                "profile": profile,
                "invoice": inv,
                "vendor_name": vendor_name,
                "primary_factor": primary_factor,
                "grand_total": grand_total,
            })

            # Record risk drivers
            for f in profile.risk_factors:
                driver_counts[f.code] = driver_counts.get(f.code, 0) + 1
                if f.code not in driver_meta:
                    driver_meta[f.code] = {
                        "title": f.title,
                        "category": f.category,
                        "description": f.description,
                    }

        total_evaluated = len(invoices)
        avg_score = round(total_score / total_evaluated, 1) if total_evaluated > 0 else 0.0

        # Sort top drivers by frequency
        sorted_drivers = sorted(driver_counts.items(), key=lambda x: x[1], reverse=True)
        top_risk_drivers = []
        for code, count in sorted_drivers[:6]:
            meta = driver_meta.get(code, {})
            pct = round((count / total_evaluated) * 100, 1) if total_evaluated > 0 else 0.0
            top_risk_drivers.append(
                TopRiskDriverOut(
                    driver_code=code,
                    title=meta.get("title", code),
                    category=meta.get("category", RiskCategory.FINANCIAL_RISK.value),
                    invoice_count=count,
                    percentage=pct,
                    description=meta.get("description", f"Detected on {count} invoices"),
                )
            )

        # Sort highest risk invoices
        sorted_invoices = sorted(invoice_profiles, key=lambda x: x["profile"].risk_score, reverse=True)
        highest_risk_invoices = []
        for item in sorted_invoices[:5]:
            p = item["profile"]
            inv = item["invoice"]
            highest_risk_invoices.append(
                HighestRiskInvoiceOut(
                    invoice_id=inv.id,
                    invoice_number=inv.invoice_number,
                    vendor_name=item["vendor_name"],
                    grand_total=item["grand_total"],
                    risk_score=p.risk_score,
                    risk_level=p.risk_level,
                    primary_factor=item["primary_factor"],
                )
            )

        return DashboardRiskOverviewOut(
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            total_evaluated=total_evaluated,
            average_risk_score=avg_score,
            top_risk_drivers=top_risk_drivers,
            highest_risk_invoices=highest_risk_invoices,
        )
