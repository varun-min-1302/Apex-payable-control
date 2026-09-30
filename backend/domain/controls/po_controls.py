import re
from typing import Optional
from backend.domain.controls.base import BaseControl, ControlContext
from backend.application.dto.control_dto import ControlEvaluation
from backend.database.enums import ControlCategory, ControlCode, ControlStatus, SeverityLevel, ApprovalStatus, POStatus

def normalize_text(text: Optional[str]) -> str:
    """Normalize text for fuzzy description matching."""
    if not text:
        return ""
    return re.sub(r"[^a-zA-Z0-9]", "", text).lower()

class POExistsControl(BaseControl):
    control_code = ControlCode.PO_EXISTS.value
    category = ControlCategory.PROCUREMENT.value

    def execute(self, context: ControlContext) -> ControlEvaluation:
        if context.invoice.purchase_order_id and context.purchase_order is not None:
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.PASS,
                severity=SeverityLevel.INFO,
                message=f"Purchase order resolved: {context.purchase_order.po_number}.",
                expected_value={"purchase_order_id": str(context.invoice.purchase_order_id)},
                actual_value={"po_number": context.purchase_order.po_number},
                rule_version=self.rule_version
            )

        return ControlEvaluation(
            control_code=self.control_code,
            category=self.category,
            status=ControlStatus.FAIL,
            severity=SeverityLevel.HIGH,
            message="Invoice does not reference a valid purchase order, or the purchase order does not exist.",
            expected_value={"has_valid_po": True},
            actual_value={"purchase_order_id": str(context.invoice.purchase_order_id) if context.invoice.purchase_order_id else None},
            rule_version=self.rule_version
        )

class POApprovedControl(BaseControl):
    control_code = ControlCode.PO_APPROVED.value
    category = ControlCategory.PROCUREMENT.value

    def execute(self, context: ControlContext) -> ControlEvaluation:
        if context.purchase_order is None:
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.NOT_APPLICABLE,
                severity=SeverityLevel.INFO,
                message="Cannot verify PO approval status: PO does not exist.",
                rule_version=self.rule_version
            )

        po_appr_str = str(context.purchase_order.approval_status.value if hasattr(context.purchase_order.approval_status, "value") else context.purchase_order.approval_status)
        po_status_str = str(context.purchase_order.status.value if hasattr(context.purchase_order.status, "value") else context.purchase_order.status)

        is_approved = (
            po_appr_str == ApprovalStatus.APPROVED.value or
            po_status_str in [POStatus.APPROVED.value, POStatus.PARTIALLY_RECEIVED.value, POStatus.FULLY_RECEIVED.value]
        )

        if is_approved:
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.PASS,
                severity=SeverityLevel.INFO,
                message=f"Purchase order {context.purchase_order.po_number} is approved ({po_status_str}).",
                expected_value={"approval_status": ApprovalStatus.APPROVED.value},
                actual_value={"approval_status": po_appr_str, "status": po_status_str},
                rule_version=self.rule_version
            )

        return ControlEvaluation(
            control_code=self.control_code,
            category=self.category,
            status=ControlStatus.FAIL,
            severity=SeverityLevel.HIGH,
            message=f"Purchase order {context.purchase_order.po_number} is in '{po_status_str}' status (approval: '{po_appr_str}'). Invoices cannot be processed against unapproved POs.",
            expected_value={"approval_status": ApprovalStatus.APPROVED.value},
            actual_value={"approval_status": po_appr_str, "status": po_status_str},
            evidence={"po_number": context.purchase_order.po_number},
            rule_version=self.rule_version
        )

class POVendorMatchControl(BaseControl):
    control_code = ControlCode.PO_VENDOR_MATCH.value
    category = ControlCategory.PROCUREMENT.value

    def execute(self, context: ControlContext) -> ControlEvaluation:
        if context.purchase_order is None or context.vendor is None:
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.NOT_APPLICABLE,
                severity=SeverityLevel.INFO,
                message="Cannot verify PO-vendor match: PO or vendor record is missing.",
                rule_version=self.rule_version
            )

        if context.invoice.vendor_id == context.purchase_order.vendor_id:
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.PASS,
                severity=SeverityLevel.INFO,
                message="Invoice vendor matches purchase order vendor.",
                expected_value={"vendor_id": str(context.purchase_order.vendor_id)},
                actual_value={"vendor_id": str(context.invoice.vendor_id)},
                rule_version=self.rule_version
            )

        return ControlEvaluation(
            control_code=self.control_code,
            category=self.category,
            status=ControlStatus.FAIL,
            severity=SeverityLevel.CRITICAL,
            message="CRITICAL: Invoice vendor does not match purchase order vendor. Possible billing redirection or cross-vendor mismatch.",
            expected_value={"po_vendor_id": str(context.purchase_order.vendor_id)},
            actual_value={"invoice_vendor_id": str(context.invoice.vendor_id)},
            evidence={
                "po_number": context.purchase_order.po_number,
                "invoice_vendor_name": context.vendor.display_name if context.vendor else None
            },
            rule_version=self.rule_version
        )

class POItemMatchControl(BaseControl):
    control_code = ControlCode.PO_ITEM_MATCH.value
    category = ControlCategory.PROCUREMENT.value

    def execute(self, context: ControlContext) -> ControlEvaluation:
        if context.purchase_order is None or not context.po_items:
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.NOT_APPLICABLE,
                severity=SeverityLevel.INFO,
                message="Cannot verify item match: purchase order or PO items not available.",
                rule_version=self.rule_version
            )

        if not context.invoice_items:
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.FAIL,
                severity=SeverityLevel.HIGH,
                message="Invoice contains zero line items to match against PO.",
                expected_value={"min_items": 1},
                actual_value={"item_count": 0},
                rule_version=self.rule_version
            )

        matched_po_item_ids = set()
        unmatched_items = []
        ambiguous_items = []

        for inv_item in context.invoice_items:
            inv_pcode = (inv_item.product_code or "").strip().lower()
            inv_desc_norm = normalize_text(inv_item.description)

            # Match attempt 1: product_code
            matches = []
            if inv_pcode:
                matches = [
                    p for p in context.po_items
                    if (p.product_code or "").strip().lower() == inv_pcode
                ]

            # Match attempt 2: normalized description
            if not matches and inv_desc_norm:
                matches = [
                    p for p in context.po_items
                    if normalize_text(p.description) == inv_desc_norm
                ]

            if len(matches) == 1:
                matched_po_item_ids.add(matches[0].id)
            elif len(matches) > 1:
                ambiguous_items.append({
                    "line_number": inv_item.line_number,
                    "description": inv_item.description,
                    "matched_count": len(matches)
                })
            else:
                unmatched_items.append({
                    "line_number": inv_item.line_number,
                    "product_code": inv_item.product_code,
                    "description": inv_item.description
                })

        if unmatched_items or ambiguous_items:
            err_msg = []
            if unmatched_items:
                err_msg.append(f"{len(unmatched_items)} invoice item(s) could not be matched to any PO line item.")
            if ambiguous_items:
                err_msg.append(f"{len(ambiguous_items)} invoice item(s) had ambiguous matches across multiple PO lines.")

            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.FAIL,
                severity=SeverityLevel.HIGH,
                message=" ".join(err_msg),
                expected_value={"all_items_matched": True},
                actual_value={
                    "total_invoice_items": len(context.invoice_items),
                    "unmatched_items": unmatched_items,
                    "ambiguous_items": ambiguous_items
                },
                evidence={"po_number": context.purchase_order.po_number},
                rule_version=self.rule_version
            )

        return ControlEvaluation(
            control_code=self.control_code,
            category=self.category,
            status=ControlStatus.PASS,
            severity=SeverityLevel.INFO,
            message=f"All {len(context.invoice_items)} invoice line items successfully matched to PO lines.",
            expected_value={"all_items_matched": True},
            actual_value={"matched_item_count": len(context.invoice_items)},
            rule_version=self.rule_version
        )
