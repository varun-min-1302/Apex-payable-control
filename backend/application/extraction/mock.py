import logging
from backend.application.extraction.base import (
    InvoiceExtractor,
    PermanentExtractionError,
    TransientExtractionError,
)
from backend.application.extraction.schemas import (
    GeminiExtractionResponse,
    ExtractedField,
    ExtractedLineItem,
)

logger = logging.getLogger("ap_control.extraction.mock")

class MockInvoiceExtractor(InvoiceExtractor):
    """
    Deterministic mock extractor for development, testing, and CI.
    Produces high-fidelity structured data without consuming Gemini API quota.
    """

    def extract(
        self,
        document_bytes: bytes,
        mime_type: str,
        filename: str,
    ) -> GeminiExtractionResponse:
        logger.info(f"event=mock_invoice_extraction filename={filename} mime_type={mime_type}")

        lower_fn = filename.lower()
        if "transient_fail" in lower_fn:
            raise TransientExtractionError("Mock transient rate-limit / timeout error (503)", details={"code": 503})
        if "perm_fail" in lower_fn:
            raise PermanentExtractionError("Mock permanent unrecoverable document error (400)", details={"code": 400})

        if "arithmetic_error" in lower_fn:
            # Intentionally mismatching totals: 100,000 + 18,000 != 150,000
            return GeminiExtractionResponse(
                invoice_number=ExtractedField(value="INV-MOCK-ARITH", evidence="Invoice No: INV-MOCK-ARITH", page=1, confidence=0.98, source="MOCK"),
                invoice_date=ExtractedField(value="2026-09-25", evidence="Date: 25/09/2026", page=1, confidence=0.97, source="MOCK"),
                due_date=ExtractedField(value="2026-10-25", evidence="Due: 25/10/2026", page=1, confidence=0.95, source="MOCK"),
                vendor_name=ExtractedField(value="Apex FinTech Technologies", evidence="Apex FinTech Technologies", page=1, confidence=0.99, source="MOCK"),
                vendor_tax_id=ExtractedField(value="27AAAAA0000A1Z5", evidence="GSTIN: 27AAAAA0000A1Z5", page=1, confidence=0.99, source="MOCK"),
                purchase_order_number=ExtractedField(value="PO-2026-0001", evidence="PO Number: PO-2026-0001", page=1, confidence=0.96, source="MOCK"),
                currency=ExtractedField(value="INR", evidence="Currency: INR", page=1, confidence=0.99, source="MOCK"),
                payment_terms_days=ExtractedField(value="30", evidence="Net 30 Days", page=1, confidence=0.95, source="MOCK"),
                subtotal=ExtractedField(value="100000.00", evidence="Subtotal: 100,000.00", page=1, confidence=0.99, source="MOCK"),
                tax_total=ExtractedField(value="18000.00", evidence="Tax (18%): 18,000.00", page=1, confidence=0.98, source="MOCK"),
                grand_total=ExtractedField(value="150000.00", evidence="Grand Total: 150,000.00", page=1, confidence=0.99, source="MOCK"),
                line_items=[
                    ExtractedLineItem(
                        line_number=1,
                        description=ExtractedField(value="Cloud Compute Instance", evidence="Cloud Compute Instance", page=1, confidence=0.98, source="MOCK"),
                        quantity=ExtractedField(value="2", evidence="Qty: 2", page=1, confidence=0.99, source="MOCK"),
                        unit_price=ExtractedField(value="50000.00", evidence="Rate: 50,000.00", page=1, confidence=0.98, source="MOCK"),
                        tax_rate=ExtractedField(value="18.00", evidence="GST: 18%", page=1, confidence=0.96, source="MOCK"),
                        line_total=ExtractedField(value="100000.00", evidence="Total: 100,000.00", page=1, confidence=0.99, source="MOCK"),
                    )
                ]
            )

        if "missing_vendor" in lower_fn:
            return GeminiExtractionResponse(
                invoice_number=ExtractedField(value="INV-NO-VENDOR-1", evidence="Invoice: INV-NO-VENDOR-1", page=1, confidence=0.95, source="MOCK"),
                invoice_date=ExtractedField(value="2026-09-28", evidence="Date: 28/09/2026", page=1, confidence=0.95, source="MOCK"),
                due_date=ExtractedField(value="2026-10-28", evidence="Due: 28/10/2026", page=1, confidence=0.95, source="MOCK"),
                vendor_name=None,
                vendor_tax_id=None,
                purchase_order_number=ExtractedField(value="PO-2026-0001", evidence="PO: PO-2026-0001", page=1, confidence=0.95, source="MOCK"),
                currency=ExtractedField(value="INR", evidence="INR", page=1, confidence=0.99, source="MOCK"),
                payment_terms_days=ExtractedField(value="30", evidence="30 days", page=1, confidence=0.90, source="MOCK"),
                subtotal=ExtractedField(value="50000.00", evidence="Subtotal: 50,000.00", page=1, confidence=0.95, source="MOCK"),
                tax_total=ExtractedField(value="9000.00", evidence="Tax: 9,000.00", page=1, confidence=0.95, source="MOCK"),
                grand_total=ExtractedField(value="59000.00", evidence="Grand Total: 59,000.00", page=1, confidence=0.95, source="MOCK"),
                line_items=[]
            )

        # Standard clean extraction default
        return GeminiExtractionResponse(
            invoice_number=ExtractedField(
                value="INV-2026-1042",
                evidence="Invoice No: INV-2026-1042",
                page=1,
                confidence=0.98,
                source="MOCK",
            ),
            invoice_date=ExtractedField(
                value="2026-09-28",
                evidence="Invoice Date: 28/09/2026",
                page=1,
                confidence=0.96,
                source="MOCK",
            ),
            due_date=ExtractedField(
                value="2026-10-28",
                evidence="Payment Due Date: 28/10/2026",
                page=1,
                confidence=0.94,
                source="MOCK",
            ),
            vendor_name=ExtractedField(
                value="ABC Technologies Pvt Ltd",
                evidence="ABC Technologies Pvt Ltd",
                page=1,
                confidence=0.97,
                source="MOCK",
            ),
            vendor_tax_id=ExtractedField(
                value="27AAAAA0000A1Z5",
                evidence="GSTIN: 27AAAAA0000A1Z5",
                page=1,
                confidence=0.99,
                source="MOCK",
            ),
            purchase_order_number=ExtractedField(
                value="PO-2026-0001",
                evidence="P.O. Reference: PO-2026-0001",
                page=1,
                confidence=0.95,
                source="MOCK",
            ),
            currency=ExtractedField(
                value="INR",
                evidence="Amount in INR (₹)",
                page=1,
                confidence=0.99,
                source="MOCK",
            ),
            payment_terms_days=ExtractedField(
                value="30",
                evidence="Payment Terms: Net 30 Days",
                page=1,
                confidence=0.92,
                source="MOCK",
            ),
            subtotal=ExtractedField(
                value="100000.00",
                evidence="Subtotal: ₹100,000.00",
                page=1,
                confidence=0.98,
                source="MOCK",
            ),
            tax_total=ExtractedField(
                value="18000.00",
                evidence="GST (18%): ₹18,000.00",
                page=1,
                confidence=0.97,
                source="MOCK",
            ),
            grand_total=ExtractedField(
                value="118000.00",
                evidence="Grand Total: ₹118,000.00",
                page=1,
                confidence=0.99,
                source="MOCK",
            ),
            line_items=[
                ExtractedLineItem(
                    line_number=1,
                    description=ExtractedField(
                        value="High Performance Server Blade",
                        evidence="1. High Performance Server Blade",
                        page=1,
                        confidence=0.97,
                        source="MOCK",
                    ),
                    quantity=ExtractedField(
                        value="2",
                        evidence="Qty: 2 NOS",
                        page=1,
                        confidence=0.98,
                        source="MOCK",
                    ),
                    unit_price=ExtractedField(
                        value="40000.00",
                        evidence="Rate: ₹40,000.00",
                        page=1,
                        confidence=0.97,
                        source="MOCK",
                    ),
                    tax_rate=ExtractedField(
                        value="18.00",
                        evidence="GST: 18%",
                        page=1,
                        confidence=0.95,
                        source="MOCK",
                    ),
                    line_total=ExtractedField(
                        value="80000.00",
                        evidence="Amount: ₹80,000.00",
                        page=1,
                        confidence=0.98,
                        source="MOCK",
                    ),
                ),
                ExtractedLineItem(
                    line_number=2,
                    description=ExtractedField(
                        value="Server Rack Installation Kit",
                        evidence="2. Server Rack Installation Kit",
                        page=1,
                        confidence=0.96,
                        source="MOCK",
                    ),
                    quantity=ExtractedField(
                        value="4",
                        evidence="Qty: 4 NOS",
                        page=1,
                        confidence=0.98,
                        source="MOCK",
                    ),
                    unit_price=ExtractedField(
                        value="5000.00",
                        evidence="Rate: ₹5,000.00",
                        page=1,
                        confidence=0.96,
                        source="MOCK",
                    ),
                    tax_rate=ExtractedField(
                        value="18.00",
                        evidence="GST: 18%",
                        page=1,
                        confidence=0.95,
                        source="MOCK",
                    ),
                    line_total=ExtractedField(
                        value="20000.00",
                        evidence="Amount: ₹20,000.00",
                        page=1,
                        confidence=0.98,
                        source="MOCK",
                    ),
                ),
            ],
        )
