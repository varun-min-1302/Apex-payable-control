from decimal import Decimal
from backend.domain.controls.base import BaseControl, ControlContext
from backend.application.dto.control_dto import ControlEvaluation
from backend.database.enums import ControlCategory, ControlStatus, SeverityLevel

class ThresholdProximityControl(BaseControl):
    control_code = "THRESHOLD_PROXIMITY"
    category = ControlCategory.APPROVAL.value

    def execute(self, context: ControlContext) -> ControlEvaluation:
        invoice_total = context.current_revision.grand_total
        pct_buf = context.tolerance_config.threshold_proximity_percentage
        abs_buf = context.tolerance_config.threshold_proximity_absolute_amount

        # Check against approval policy thresholds
        proximity_hits = []
        for policy in context.approval_policies:
            if not policy.active:
                continue

            # Check if invoice is just under max_amount
            if policy.max_amount and policy.max_amount > invoice_total:
                threshold = policy.max_amount
                delta = threshold - invoice_total
                delta_pct = (delta / threshold * Decimal("100.0000")).quantize(Decimal("0.0001"))

                # Flag if within percentage buffer OR absolute monetary buffer
                if delta_pct <= pct_buf or delta <= abs_buf:
                    proximity_hits.append({
                        "policy_name": policy.name,
                        "threshold_amount": float(threshold),
                        "invoice_amount": float(invoice_total),
                        "proximity_delta": float(delta),
                        "delta_percentage": float(delta_pct)
                    })

        if proximity_hits:
            hit = proximity_hits[0]
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.WARNING,
                severity=SeverityLevel.MEDIUM,
                message=(
                    f"Threshold proximity warning: Invoice total (₹{invoice_total}) is within ₹{hit['proximity_delta']} "
                    f"({hit['delta_percentage']}%) of approval threshold ₹{hit['threshold_amount']} ({hit['policy_name']}). "
                    f"Possible approval split-billing or structuring."
                ),
                expected_value={"clear_of_threshold_buffer": True},
                actual_value={"proximity_hits": proximity_hits},
                variance_value=Decimal(str(hit["proximity_delta"])),
                variance_percentage=Decimal(str(hit["delta_percentage"])),
                evidence={"proximity_details": proximity_hits},
                rule_version=self.rule_version
            )

        return ControlEvaluation(
            control_code=self.control_code,
            category=self.category,
            status=ControlStatus.PASS,
            severity=SeverityLevel.INFO,
            message="Invoice amount is not within proximity of approval policy thresholds.",
            expected_value={"clear_of_threshold_buffer": True},
            actual_value={"clear_of_threshold_buffer": True},
            rule_version=self.rule_version
        )

class UnusualAmountControl(BaseControl):
    control_code = "UNUSUAL_AMOUNT"
    category = ControlCategory.FINANCIAL.value

    def execute(self, context: ControlContext) -> ControlEvaluation:
        # Filter valid historical invoices for this vendor
        hist_totals = [
            inv.revisions[0].grand_total
            for inv in context.historical_invoices
            if inv.id != context.invoice.id and inv.revisions
        ]

        # Minimum 3 historical invoices required for deterministic baseline
        if len(hist_totals) < 3:
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.NOT_APPLICABLE,
                severity=SeverityLevel.INFO,
                message=f"Insufficient historical data for vendor ({len(hist_totals)} invoices found, minimum 3 required for statistical baseline).",
                expected_value={"minimum_history_count": 3},
                actual_value={"historical_invoice_count": len(hist_totals)},
                rule_version=self.rule_version
            )

        mean_total = sum(hist_totals) / Decimal(str(len(hist_totals)))
        inv_total = context.current_revision.grand_total

        # An invoice > 300% of vendor historical average is flagged as unusual amount
        if inv_total > (mean_total * Decimal("3.00")):
            multiplier = (inv_total / mean_total).quantize(Decimal("0.01"))
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.WARNING,
                severity=SeverityLevel.MEDIUM,
                message=(
                    f"Invoice amount (₹{inv_total}) is unusually high compared to vendor historical average "
                    f"(₹{mean_total.quantize(Decimal('0.01'))}). Exceeds average by {multiplier}x."
                ),
                expected_value={"max_expected_amount": float(mean_total * Decimal("3.00"))},
                actual_value={"invoice_amount": float(inv_total), "vendor_mean_amount": float(mean_total)},
                variance_value=(inv_total - mean_total).quantize(Decimal("0.01")),
                evidence={"historical_sample_size": len(hist_totals), "multiplier": float(multiplier)},
                rule_version=self.rule_version
            )

        return ControlEvaluation(
            control_code=self.control_code,
            category=self.category,
            status=ControlStatus.PASS,
            severity=SeverityLevel.INFO,
            message="Invoice amount is within typical historical range for this vendor.",
            expected_value={"is_outlier": False},
            actual_value={"is_outlier": False},
            rule_version=self.rule_version
        )
