from datetime import timedelta
from decimal import Decimal
from typing import Optional
from backend.domain.controls.base import BaseControl, ControlContext
from backend.domain.controls.po_controls import normalize_text
from backend.application.dto.control_dto import ControlEvaluation
from backend.database.enums import ControlCategory, ControlCode, ControlStatus, SeverityLevel

class PriceMatchControl(BaseControl):
    control_code = ControlCode.PRICE_MATCH.value
    category = ControlCategory.FINANCIAL.value

    def execute(self, context: ControlContext) -> ControlEvaluation:
        if context.purchase_order is None or not context.po_items:
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.NOT_APPLICABLE,
                severity=SeverityLevel.INFO,
                message="Cannot evaluate price match: PO items are not available.",
                rule_version=self.rule_version
            )

        discrepancies = []
        max_diff = Decimal("0.00")
        max_diff_pct = Decimal("0.0000")
        price_tol_pct = context.tolerance_config.price_variance_percentage_tolerance

        for inv_item in context.invoice_items:
            inv_pcode = (inv_item.product_code or "").strip().lower()
            inv_desc_norm = normalize_text(inv_item.description)

            # Match PO item
            matched_po = None
            for p in context.po_items:
                if inv_pcode and (p.product_code or "").strip().lower() == inv_pcode:
                    matched_po = p
                    break
                if not matched_po and inv_desc_norm and normalize_text(p.description) == inv_desc_norm:
                    matched_po = p
                    break

            if not matched_po:
                continue

            inv_price = inv_item.unit_price
            po_price = matched_po.unit_price

            if inv_price > po_price:
                diff = inv_price - po_price
                diff_pct = (
                    (diff / po_price * Decimal("100.0000")).quantize(Decimal("0.0001"))
                    if po_price > 0
                    else Decimal("100.0000")
                )
                if diff_pct > price_tol_pct:
                    discrepancies.append({
                        "line_number": inv_item.line_number,
                        "product_code": inv_item.product_code,
                        "description": inv_item.description,
                        "invoice_unit_price": float(inv_price),
                        "po_unit_price": float(po_price),
                        "variance_value": float(diff),
                        "variance_percentage": float(diff_pct)
                    })
                    if diff > max_diff:
                        max_diff = diff
                    if diff_pct > max_diff_pct:
                        max_diff_pct = diff_pct

        if discrepancies:
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.FAIL,
                severity=SeverityLevel.HIGH,
                message=(
                    f"Invoice unit price exceeds approved PO unit price on {len(discrepancies)} item(s). "
                    f"Max variance: ₹{max_diff} ({max_diff_pct}%)."
                ),
                expected_value={"tolerated_price_variance_percentage": float(price_tol_pct)},
                actual_value={"discrepancies": discrepancies},
                variance_value=max_diff.quantize(Decimal("0.01")),
                variance_percentage=max_diff_pct,
                evidence={"price_mismatches": discrepancies},
                rule_version=self.rule_version
            )

        return ControlEvaluation(
            control_code=self.control_code,
            category=self.category,
            status=ControlStatus.PASS,
            severity=SeverityLevel.INFO,
            message="Invoice unit prices match approved purchase order prices across all line items.",
            expected_value={"price_match": True},
            actual_value={"price_match": True},
            rule_version=self.rule_version
        )

class TaxValidationControl(BaseControl):
    control_code = ControlCode.TAX_VALIDATION.value
    category = ControlCategory.FINANCIAL.value

    def execute(self, context: ControlContext) -> ControlEvaluation:
        # 1. Validate tax rate against approved PO contract (if PO exists)
        if context.purchase_order and context.po_items:
            po_items_by_line = {p.line_number: p for p in context.po_items}
            po_items_by_code = {p.product_code: p for p in context.po_items}
            rate_mismatches = []
            for inv_item in context.invoice_items:
                po_item = po_items_by_line.get(inv_item.line_number) or po_items_by_code.get(inv_item.product_code)
                if po_item and po_item.tax_rate is not None:
                    inv_rate = inv_item.tax_rate / Decimal("100.00") if inv_item.tax_rate > Decimal("1.0") else inv_item.tax_rate
                    po_rate = po_item.tax_rate / Decimal("100.00") if po_item.tax_rate > Decimal("1.0") else po_item.tax_rate
                    diff_rate = abs(inv_rate - po_rate)
                    if diff_rate > Decimal("0.0001"):
                        rate_mismatches.append({
                            "line_number": inv_item.line_number,
                            "product_code": inv_item.product_code,
                            "invoice_tax_rate": float(inv_rate),
                            "po_tax_rate": float(po_rate),
                            "diff": float(diff_rate)
                        })

            if rate_mismatches:
                first_mismatch = rate_mismatches[0]
                diff_pct = (Decimal(str(first_mismatch["diff"])) * Decimal("100.0000")).quantize(Decimal("0.0001"))
                return ControlEvaluation(
                    control_code=self.control_code,
                    category=self.category,
                    status=ControlStatus.FAIL,
                    severity=SeverityLevel.HIGH,
                    message=(
                        f"Invoice tax rate mismatch against approved purchase order on {len(rate_mismatches)} item(s): "
                        f"Line {first_mismatch['line_number']} tax rate {first_mismatch['invoice_tax_rate']*100:.2f}% "
                        f"differs from agreed PO rate {first_mismatch['po_tax_rate']*100:.2f}%."
                    ),
                    expected_value={"agreed_po_tax_rate": first_mismatch["po_tax_rate"]},
                    actual_value={"invoice_tax_rate": first_mismatch["invoice_tax_rate"]},
                    variance_value=Decimal(str(first_mismatch["diff"])),
                    variance_percentage=diff_pct,
                    evidence={"tax_rate_mismatches": rate_mismatches},
                    rule_version=self.rule_version
                )

        # 2. Recalculate expected tax from items and compare against header claimed tax
        calculated_tax = Decimal("0.00")
        for item in context.invoice_items:
            taxable = (item.unit_price * item.quantity) - item.discount_amount
            rate = item.tax_rate
            if rate > Decimal("1.0"):  # e.g. 18.00%
                rate = rate / Decimal("100.00")
            item_tax = (taxable * rate).quantize(Decimal("0.01"))
            calculated_tax += item_tax

        claimed_tax = context.current_revision.tax_total
        tax_diff = abs(claimed_tax - calculated_tax)
        tolerance = context.tolerance_config.tax_rounding_tolerance_amount

        if tax_diff > tolerance:
            diff_pct = (
                (tax_diff / calculated_tax * Decimal("100.0000")).quantize(Decimal("0.0001"))
                if calculated_tax > 0
                else Decimal("100.0000")
            )
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.FAIL,
                severity=SeverityLevel.HIGH,
                message=(
                    f"Invoice tax amount (₹{claimed_tax}) does not match recalculated mathematical tax "
                    f"(₹{calculated_tax}). Discrepancy: ₹{tax_diff}."
                ),
                expected_value={"calculated_tax": float(calculated_tax)},
                actual_value={"claimed_tax": float(claimed_tax)},
                variance_value=tax_diff.quantize(Decimal("0.01")),
                variance_percentage=diff_pct,
                evidence={
                    "calculated_tax": float(calculated_tax),
                    "claimed_tax": float(claimed_tax),
                    "tolerance": float(tolerance)
                },
                rule_version=self.rule_version
            )

        return ControlEvaluation(
            control_code=self.control_code,
            category=self.category,
            status=ControlStatus.PASS,
            severity=SeverityLevel.INFO,
            message=f"Tax validation passed: Claimed tax (₹{claimed_tax}) matches calculated tax (₹{calculated_tax}).",
            expected_value={"calculated_tax": float(calculated_tax)},
            actual_value={"claimed_tax": float(claimed_tax)},
            rule_version=self.rule_version
        )

class TotalValidationControl(BaseControl):
    control_code = ControlCode.TOTAL_VALIDATION.value
    category = ControlCategory.FINANCIAL.value

    def execute(self, context: ControlContext) -> ControlEvaluation:
        rev = context.current_revision
        # Expected: subtotal - discount_total + tax_total
        expected_total = (rev.subtotal - rev.discount_total + rev.tax_total).quantize(Decimal("0.01"))
        actual_total = rev.grand_total.quantize(Decimal("0.01"))

        diff = abs(actual_total - expected_total)
        tolerance = context.tolerance_config.total_rounding_tolerance_amount

        if diff > tolerance:
            diff_pct = (
                (diff / expected_total * Decimal("100.0000")).quantize(Decimal("0.0001"))
                if expected_total > 0
                else Decimal("100.0000")
            )
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.FAIL,
                severity=SeverityLevel.CRITICAL,
                message=(
                    f"Invoice mathematical total mismatch: Claimed grand total (₹{actual_total}) does not equal "
                    f"subtotal (₹{rev.subtotal}) - discount (₹{rev.discount_total}) + tax (₹{rev.tax_total}) = ₹{expected_total}."
                ),
                expected_value={"expected_grand_total": float(expected_total)},
                actual_value={"claimed_grand_total": float(actual_total)},
                variance_value=diff.quantize(Decimal("0.01")),
                variance_percentage=diff_pct,
                evidence={
                    "subtotal": float(rev.subtotal),
                    "discount_total": float(rev.discount_total),
                    "tax_total": float(rev.tax_total),
                    "difference": float(diff)
                },
                rule_version=self.rule_version
            )

        return ControlEvaluation(
            control_code=self.control_code,
            category=self.category,
            status=ControlStatus.PASS,
            severity=SeverityLevel.INFO,
            message=f"Invoice total mathematical validation passed: Grand total ₹{actual_total} verified.",
            expected_value={"expected_grand_total": float(expected_total)},
            actual_value={"claimed_grand_total": float(actual_total)},
            rule_version=self.rule_version
        )

class PaymentTermsControl(BaseControl):
    control_code = ControlCode.PAYMENT_TERMS_VALIDATION.value
    category = ControlCategory.FINANCIAL.value

    def execute(self, context: ControlContext) -> ControlEvaluation:
        agreed_terms = 30
        if context.purchase_order and context.purchase_order.payment_terms_days:
            agreed_terms = context.purchase_order.payment_terms_days
        elif context.vendor and context.vendor.payment_terms_days:
            agreed_terms = context.vendor.payment_terms_days

        inv_date = context.current_revision.invoice_date
        due_date = context.current_revision.due_date

        if not inv_date or not due_date:
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.WARNING,
                severity=SeverityLevel.LOW,
                message="Invoice date or due date missing from revision.",
                rule_version=self.rule_version
            )

        actual_days = (due_date - inv_date).days
        if actual_days < (agreed_terms - 5): # Allow 5 days grace for weekend adjustments
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.WARNING,
                severity=SeverityLevel.MEDIUM,
                message=(
                    f"Invoice due date reflects payment terms of {actual_days} days, compressing agreed terms "
                    f"of {agreed_terms} days."
                ),
                expected_value={"agreed_payment_terms_days": agreed_terms},
                actual_value={"invoice_payment_terms_days": actual_days},
                evidence={"invoice_date": str(inv_date), "due_date": str(due_date)},
                rule_version=self.rule_version
            )

        return ControlEvaluation(
            control_code=self.control_code,
            category=self.category,
            status=ControlStatus.PASS,
            severity=SeverityLevel.INFO,
            message=f"Payment terms verified: {actual_days} days satisfies agreed terms ({agreed_terms} days).",
            expected_value={"agreed_payment_terms_days": agreed_terms},
            actual_value={"invoice_payment_terms_days": actual_days},
            rule_version=self.rule_version
        )
