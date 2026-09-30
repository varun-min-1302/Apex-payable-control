from decimal import Decimal
from typing import Optional
from backend.domain.controls.base import BaseControl, ControlContext
from backend.domain.controls.po_controls import normalize_text
from backend.application.dto.control_dto import ControlEvaluation
from backend.database.enums import ControlCategory, ControlCode, ControlStatus, SeverityLevel

class ReceiptMatchControl(BaseControl):
    control_code = ControlCode.RECEIPT_MATCH.value
    category = ControlCategory.RECEIPT.value

    def execute(self, context: ControlContext) -> ControlEvaluation:
        if context.purchase_order is None:
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.NOT_APPLICABLE,
                severity=SeverityLevel.INFO,
                message="Cannot evaluate receipt match: PO does not exist.",
                rule_version=self.rule_version
            )

        if not context.goods_receipts:
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.FAIL,
                severity=SeverityLevel.HIGH,
                message=f"No goods receipts found for purchase order {context.purchase_order.po_number}. Goods/services have not been received.",
                expected_value={"has_goods_receipts": True},
                actual_value={"goods_receipt_count": 0},
                rule_version=self.rule_version
            )

        # Aggregate total accepted quantity across all GR items for this PO
        total_invoiced_qty = sum((item.quantity for item in context.invoice_items), Decimal("0.0000"))
        total_accepted_qty = sum((gri.accepted_quantity for gri in context.goods_receipt_items), Decimal("0.0000"))
        total_received_qty = sum((gri.received_quantity for gri in context.goods_receipt_items), Decimal("0.0000"))

        if total_invoiced_qty > total_accepted_qty:
            qty_variance = total_invoiced_qty - total_accepted_qty
            var_pct = (
                (qty_variance / total_accepted_qty * Decimal("100.0000")).quantize(Decimal("0.0001"))
                if total_accepted_qty > 0
                else Decimal("100.0000")
            )
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.FAIL,
                severity=SeverityLevel.HIGH,
                message=(
                    f"Invoiced quantity ({total_invoiced_qty}) exceeds accepted goods receipt quantity "
                    f"({total_accepted_qty}) across PO receipts. Variance: {qty_variance}."
                ),
                expected_value={"accepted_quantity": float(total_accepted_qty)},
                actual_value={"invoiced_quantity": float(total_invoiced_qty)},
                variance_value=qty_variance.quantize(Decimal("0.01")),
                variance_percentage=var_pct,
                evidence={
                    "total_received_quantity": float(total_received_qty),
                    "total_accepted_quantity": float(total_accepted_qty),
                    "receipt_count": len(context.goods_receipts)
                },
                rule_version=self.rule_version
            )

        return ControlEvaluation(
            control_code=self.control_code,
            category=self.category,
            status=ControlStatus.PASS,
            severity=SeverityLevel.INFO,
            message=(
                f"Receipt verification passed: Invoiced quantity ({total_invoiced_qty}) is within accepted "
                f"received quantity ({total_accepted_qty})."
            ),
            expected_value={"accepted_quantity": float(total_accepted_qty)},
            actual_value={"invoiced_quantity": float(total_invoiced_qty)},
            rule_version=self.rule_version
        )

class QuantityMatchControl(BaseControl):
    control_code = ControlCode.QUANTITY_MATCH.value
    category = ControlCategory.RECEIPT.value

    def execute(self, context: ControlContext) -> ControlEvaluation:
        if context.purchase_order is None or not context.po_items or not context.goods_receipt_items:
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.NOT_APPLICABLE,
                severity=SeverityLevel.INFO,
                message="Cannot evaluate line item quantity match: PO items or GR items missing.",
                rule_version=self.rule_version
            )

        # Build map of po_item_id -> total accepted quantity from GRs
        po_item_accepted_qty: dict[str, Decimal] = {}
        for gri in context.goods_receipt_items:
            key = str(gri.purchase_order_item_id)
            po_item_accepted_qty[key] = po_item_accepted_qty.get(key, Decimal("0.0000")) + gri.accepted_quantity

        discrepancies = []
        max_variance_val = Decimal("0.00")
        max_variance_pct = Decimal("0.0000")

        tolerance_pct = context.tolerance_config.quantity_variance_percentage_tolerance

        for inv_item in context.invoice_items:
            inv_pcode = (inv_item.product_code or "").strip().lower()
            inv_desc_norm = normalize_text(inv_item.description)

            # Find matching PO line
            matched_po_item = None
            for p in context.po_items:
                if inv_pcode and (p.product_code or "").strip().lower() == inv_pcode:
                    matched_po_item = p
                    break
                if not matched_po_item and inv_desc_norm and normalize_text(p.description) == inv_desc_norm:
                    matched_po_item = p
                    break

            if not matched_po_item:
                continue

            accepted = po_item_accepted_qty.get(str(matched_po_item.id), Decimal("0.0000"))
            inv_qty = inv_item.quantity

            if inv_qty > accepted:
                diff = inv_qty - accepted
                diff_pct = (
                    (diff / accepted * Decimal("100.0000")).quantize(Decimal("0.0001"))
                    if accepted > 0
                    else Decimal("100.0000")
                )
                if diff_pct > tolerance_pct:
                    discrepancies.append({
                        "line_number": inv_item.line_number,
                        "product_code": inv_item.product_code,
                        "description": inv_item.description,
                        "invoiced_quantity": float(inv_qty),
                        "accepted_quantity": float(accepted),
                        "variance_quantity": float(diff),
                        "variance_percentage": float(diff_pct)
                    })
                    if diff > max_variance_val:
                        max_variance_val = diff
                    if diff_pct > max_variance_pct:
                        max_variance_pct = diff_pct

        if discrepancies:
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.FAIL,
                severity=SeverityLevel.HIGH,
                message=(
                    f"Quantity mismatch detected on {len(discrepancies)} line item(s). "
                    f"Invoiced quantity exceeds accepted warehouse quantity."
                ),
                expected_value={"tolerated_variance_percentage": float(tolerance_pct)},
                actual_value={"discrepancies": discrepancies},
                variance_value=max_variance_val.quantize(Decimal("0.01")),
                variance_percentage=max_variance_pct,
                evidence={"item_mismatches": discrepancies},
                rule_version=self.rule_version
            )

        return ControlEvaluation(
            control_code=self.control_code,
            category=self.category,
            status=ControlStatus.PASS,
            severity=SeverityLevel.INFO,
            message="Line item quantities successfully validated against accepted goods receipt quantities.",
            expected_value={"tolerated_variance_percentage": float(tolerance_pct)},
            actual_value={"all_quantities_matched": True},
            rule_version=self.rule_version
        )
