"""Centralized Control Metadata Registry.

Provides finance-friendly definitions, explanations, and action recommendations
for all deterministic controls in the AP Control System.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ControlMetadata:
    control_code: str
    title: str
    category: str
    passed_message: str
    failed_message: str
    why_it_matters: str
    recommended_action: str
    technical_rule: str


CONTROL_METADATA_REGISTRY: Dict[str, ControlMetadata] = {
    "VENDOR_EXISTS": ControlMetadata(
        control_code="VENDOR_EXISTS",
        title="Vendor verified",
        category="VENDOR",
        passed_message="An active vendor record was verified in the vendor master.",
        failed_message="We could not verify this vendor in the system.",
        why_it_matters="Payments must only be disbursed to authorized and verified vendors.",
        recommended_action="Review vendor details or onboard/activate the vendor record.",
        technical_rule="Rule 1: Vendor Existence in Vendor Master",
    ),
    "VENDOR_STATUS": ControlMetadata(
        control_code="VENDOR_STATUS",
        title="Vendor active",
        category="VENDOR",
        passed_message="The vendor account is in good standing and active.",
        failed_message="This vendor account is inactive, blocked, or pending verification.",
        why_it_matters="Invoices cannot be processed for vendors that are blocked or inactive.",
        recommended_action="Contact procurement or vendor management to resolve the vendor's status.",
        technical_rule="Rule 2: Vendor Active Status Validation",
    ),
    "VENDOR_TAX_ID_MATCH": ControlMetadata(
        control_code="VENDOR_TAX_ID_MATCH",
        title="Tax identifier verified",
        category="VENDOR",
        passed_message="The invoice tax ID matches the official vendor master tax identifier.",
        failed_message="The tax identifier on the invoice does not match our vendor records.",
        why_it_matters="Tax ID discrepancies create audit compliance failures and disqualify input tax credits.",
        recommended_action="Verify the vendor's GSTIN/tax registration certificate and update vendor records.",
        technical_rule="Rule 3: Vendor Tax Identification Consistency",
    ),
    "BANK_DETAILS_MATCH": ControlMetadata(
        control_code="BANK_DETAILS_MATCH",
        title="Bank account verified",
        category="VENDOR",
        passed_message="Payment remittance bank details match verified vendor banking records.",
        failed_message="The bank account details on the invoice do not match verified vendor banking records.",
        why_it_matters="Remitting funds to unverified bank accounts carries critical fraud and payment redirection risks.",
        recommended_action="Place an immediate payment hold and perform independent verification with vendor management.",
        technical_rule="Rule 4: Remittance Bank Account Verification",
    ),
    "PO_EXISTS": ControlMetadata(
        control_code="PO_EXISTS",
        title="Purchase order referenced",
        category="PO",
        passed_message="A valid purchase order was found for this invoice.",
        failed_message="No purchase order was referenced, or the referenced purchase order does not exist.",
        why_it_matters="Invoices without purchase orders lack procurement authorization and pre-approved budget.",
        recommended_action="Contact procurement to link a valid purchase order, or return the invoice if unauthorized.",
        technical_rule="Rule 5: Purchase Order Existence Check",
    ),
    "PO_APPROVED": ControlMetadata(
        control_code="PO_APPROVED",
        title="Purchase order approved",
        category="PO",
        passed_message="The referenced purchase order is approved and authorized.",
        failed_message="The referenced purchase order has not been approved.",
        why_it_matters="An unapproved purchase order does not authorize commitment of company funds.",
        recommended_action="Ensure the purchase order completes its internal procurement approval workflow.",
        technical_rule="Rule 6: Purchase Order Authorization Status",
    ),
    "PO_VENDOR_MATCH": ControlMetadata(
        control_code="PO_VENDOR_MATCH",
        title="Vendor matches purchase order",
        category="PO",
        passed_message="The invoice vendor matches the vendor on the purchase order.",
        failed_message="The invoice was submitted by a different vendor than the one contracted on the purchase order.",
        why_it_matters="Cross-vendor billing indicates uncontracted third-party fulfillment or misdirected billing.",
        recommended_action="Confirm whether the submitting vendor is an authorized billing entity for this contract.",
        technical_rule="Rule 7: PO Contracting Vendor Validation",
    ),
    "PO_ITEM_MATCH": ControlMetadata(
        control_code="PO_ITEM_MATCH",
        title="Line items match purchase order",
        category="PO",
        passed_message="All invoice line items correspond to ordered line items on the purchase order.",
        failed_message="One or more invoiced items do not match items on the purchase order.",
        why_it_matters="Invoicing for uncontracted items or differing product codes leads to unauthorized spend.",
        recommended_action="Compare line items against the PO contract and request an amended invoice.",
        technical_rule="Rule 8: PO Line Item Specification Match",
    ),
    "RECEIPT_MATCH": ControlMetadata(
        control_code="RECEIPT_MATCH",
        title="Goods / services received",
        category="RECEIPT",
        passed_message="Warehouse or service receipt confirmed for invoiced deliverables.",
        failed_message="No goods receipt or service confirmation was found for this invoice.",
        why_it_matters="Paying before physical receipt or service sign-off risks payment for unrendered work.",
        recommended_action="Confirm delivery with receiving/warehouse and record the goods receipt in the system.",
        technical_rule="Rule 9: Goods Receipt & Delivery Confirmation",
    ),
    "QUANTITY_MATCH": ControlMetadata(
        control_code="QUANTITY_MATCH",
        title="Quantity verified",
        category="RECEIPT",
        passed_message="Invoiced quantities match accepted goods receipts.",
        failed_message="Invoiced quantity exceeds the quantity confirmed as received.",
        why_it_matters="Paying for more units than received results in direct overpayment.",
        recommended_action="Review quantities with receiving or request a corrected invoice for the received quantity.",
        technical_rule="Rule 10: 3-Way Quantity Reconciliation (PO vs GR vs Invoice)",
    ),
    "PRICE_MATCH": ControlMetadata(
        control_code="PRICE_MATCH",
        title="Unit prices verified",
        category="FINANCIAL",
        passed_message="Invoiced unit prices match agreed purchase order contracted rates.",
        failed_message="Invoiced unit prices exceed the agreed purchase order price.",
        why_it_matters="Unauthorized price increases cause budget overruns and contract non-compliance.",
        recommended_action="Request a corrected invoice or credit note from the vendor matching PO prices.",
        technical_rule="Rule 11: 3-Way Unit Price Variance Tolerance (0% Tolerance)",
    ),
    "TAX_VALIDATION": ControlMetadata(
        control_code="TAX_VALIDATION",
        title="Tax calculation verified",
        category="FINANCIAL",
        passed_message="Tax rates and total tax amounts are mathematically accurate.",
        failed_message="Invoiced tax rate or calculation differs from the required statutory calculation.",
        why_it_matters="Incorrect tax charges risk regulatory penalties and input tax credit disallowance.",
        recommended_action="Verify applicable tax rates and request an amended tax invoice.",
        technical_rule="Rule 12: Statutory Tax Arithmetic & Rate Reconciliation",
    ),
    "TOTAL_VALIDATION": ControlMetadata(
        control_code="TOTAL_VALIDATION",
        title="Invoice total verified",
        category="FINANCIAL",
        passed_message="Grand total perfectly equals line items subtotal plus tax minus discounts.",
        failed_message="Invoice grand total does not match the sum of subtotal, tax, and discount lines.",
        why_it_matters="Invoices with mathematical discrepancies cannot be balanced in the general ledger.",
        recommended_action="Request a reissued invoice with mathematically reconciled totals.",
        technical_rule="Rule 13: Header vs Line Item Mathematical Integrity",
    ),
    "PAYMENT_TERMS_VALIDATION": ControlMetadata(
        control_code="PAYMENT_TERMS_VALIDATION",
        title="Payment terms verified",
        category="FINANCIAL",
        passed_message="Payment due date conforms to agreed contract credit terms.",
        failed_message="Due date provides significantly shorter credit terms than agreed in the contract.",
        why_it_matters="Compressed payment windows disrupt working capital and cash-flow management.",
        recommended_action="Align the invoice due date with agreed contractual payment terms (e.g. Net 30/60).",
        technical_rule="Rule 14: Contractual Payment Credit Period Verification",
    ),
    "DUPLICATE_EXACT": ControlMetadata(
        control_code="DUPLICATE_EXACT",
        title="Duplicate invoice check",
        category="DUPLICATE",
        passed_message="No identical document hash or duplicate invoice number found.",
        failed_message="Identical document hash or duplicate invoice number detected in historical records.",
        why_it_matters="Duplicate invoices create an immediate risk of double disbursement.",
        recommended_action="Verify whether this invoice was already paid. Reject if duplicate, or request a new invoice.",
        technical_rule="Rule 15: Exact Duplicate Document Hash & Number Detection",
    ),
    "DUPLICATE_SEMANTIC": ControlMetadata(
        control_code="DUPLICATE_SEMANTIC",
        title="Similar invoice scan",
        category="DUPLICATE",
        passed_message="No suspicious semantic similarity with existing invoices.",
        failed_message="Unusually high semantic similarity found with another invoice.",
        why_it_matters="Slightly altered duplicate invoices may represent subtle re-billing attempts.",
        recommended_action="Inspect the flagged prior invoice to ensure this is an independent legitimate transaction.",
        technical_rule="Rule 16: Semantic & Structural Embedding Similarity Check",
    ),
    "THRESHOLD_PROXIMITY": ControlMetadata(
        control_code="THRESHOLD_PROXIMITY",
        title="Approval threshold scan",
        category="RISK",
        passed_message="Invoice amount is not artificially close to an approval threshold ceiling.",
        failed_message="Invoice total is just below a mandatory managerial approval threshold.",
        why_it_matters="Amounts just below approval tiers (e.g., ₹49,990 vs ₹50,000) may indicate approval circumvention.",
        recommended_action="Subject this invoice to higher-tier management review before sign-off.",
        technical_rule="Rule 17: Approval Threshold Proximity & Structuring Flag",
    ),
    "UNUSUAL_AMOUNT": ControlMetadata(
        control_code="UNUSUAL_AMOUNT",
        title="Statistical spend analysis",
        category="RISK",
        passed_message="Invoice amount is consistent with historical vendor spend patterns.",
        failed_message="Invoice amount deviates substantially from historical spend for this vendor.",
        why_it_matters="Unexpected spending spikes can indicate erroneous billing or unauthorized procurement.",
        recommended_action="Confirm budget availability and project manager sign-off for the elevated amount.",
        technical_rule="Rule 18: Historical Vendor Spend Anomaly Detection",
    ),
}

DEFAULT_METADATA = ControlMetadata(
    control_code="CUSTOM_CONTROL",
    title="Automated check",
    category="GENERAL",
    passed_message="Automated verification passed.",
    failed_message="Automated verification detected an issue.",
    why_it_matters="Every control verifies compliance with organizational financial policies.",
    recommended_action="Review invoice details and take appropriate corrective action.",
    technical_rule="System Financial Control Rule",
)


def get_control_metadata(control_code: str) -> ControlMetadata:
    """Retrieve human-friendly metadata for a control code."""
    return CONTROL_METADATA_REGISTRY.get(control_code, DEFAULT_METADATA)


def format_expected_value(control_code: str, expected: Optional[Dict[str, Any]]) -> str:
    if not expected:
        return "Not specified"
    if control_code == "QUANTITY_MATCH":
        qty = expected.get("po_quantity") or expected.get("received_quantity") or expected.get("expected_quantity")
        return f"{qty} units (PO / Goods Receipt)" if qty is not None else str(expected)
    if control_code == "PRICE_MATCH":
        price = expected.get("po_unit_price") or expected.get("expected_unit_price")
        return f"₹{price:,.2f} / unit (Agreed PO Contract)" if isinstance(price, (int, float, Decimal)) else str(expected)
    if control_code == "TAX_VALIDATION":
        tax = expected.get("calculated_tax") or expected.get("expected_tax")
        return f"₹{tax:,.2f} (Calculated statutory tax)" if isinstance(tax, (int, float, Decimal)) else str(expected)
    if control_code == "TOTAL_VALIDATION":
        total = expected.get("expected_grand_total") or expected.get("calculated_total")
        return f"₹{total:,.2f} (Subtotal + Tax - Discount)" if isinstance(total, (int, float, Decimal)) else str(expected)
    if control_code == "PO_EXISTS":
        return "Valid approved Purchase Order"
    if control_code == "PO_APPROVED":
        return "APPROVED status on PO"
    if control_code == "VENDOR_EXISTS":
        return "Active Vendor Record in Master"
    if control_code == "DUPLICATE_EXACT":
        return "Unique invoice number and document hash"
    if control_code == "BANK_DETAILS_MATCH":
        return "Bank account matching verified vendor profile"
    
    # Generic key-value format
    items = [f"{k}: {v}" for k, v in expected.items()]
    return ", ".join(items) if items else str(expected)


def format_actual_value(control_code: str, actual: Optional[Dict[str, Any]]) -> str:
    if not actual:
        return "Not available"
    if control_code == "QUANTITY_MATCH":
        qty = actual.get("invoiced_quantity") or actual.get("actual_quantity")
        return f"{qty} units (Invoiced)" if qty is not None else str(actual)
    if control_code == "PRICE_MATCH":
        price = actual.get("invoiced_unit_price") or actual.get("actual_unit_price")
        return f"₹{price:,.2f} / unit (Invoiced)" if isinstance(price, (int, float, Decimal)) else str(actual)
    if control_code == "TAX_VALIDATION":
        tax = actual.get("claimed_tax") or actual.get("actual_tax")
        return f"₹{tax:,.2f} (Claimed on invoice)" if isinstance(tax, (int, float, Decimal)) else str(actual)
    if control_code == "TOTAL_VALIDATION":
        total = actual.get("claimed_grand_total") or actual.get("actual_total")
        return f"₹{total:,.2f} (Claimed on invoice header)" if isinstance(total, (int, float, Decimal)) else str(actual)
    if control_code == "PO_EXISTS":
        return actual.get("purchase_order_id") or "Missing / Not found"
    if control_code == "PO_APPROVED":
        return f"Status: {actual.get('po_status', 'UNAPPROVED')}"
    if control_code == "DUPLICATE_EXACT":
        num = actual.get("colliding_invoice_number") or actual.get("duplicate_invoice_number")
        return f"Duplicate of invoice '{num}'" if num else "Duplicate document hash detected"
    if control_code == "BANK_DETAILS_MATCH":
        return actual.get("invoice_bank_hash") or "Mismatched bank details"
    
    items = [f"{k}: {v}" for k, v in actual.items()]
    return ", ".join(items) if items else str(actual)


def format_variance_str(
    variance_val: Optional[Decimal],
    variance_pct: Optional[Decimal],
    control_code: str,
) -> str:
    if variance_val is None and variance_pct is None:
        return "None"
    
    prefix = "+" if variance_val and variance_val > 0 else ""
    val_str = ""
    pct_str = ""
    if variance_val is not None:
        if control_code in ("PRICE_MATCH", "TAX_VALIDATION", "TOTAL_VALIDATION"):
            val_str = f"{prefix}₹{variance_val:,.2f}"
        elif control_code == "QUANTITY_MATCH":
            val_str = f"{prefix}{variance_val} units"
        else:
            val_str = f"{prefix}{variance_val}"
            
    if variance_pct is not None:
        pct_str = f" ({prefix}{variance_pct:.2f}%)"
        
    return f"{val_str}{pct_str}".strip() or "Detected"
