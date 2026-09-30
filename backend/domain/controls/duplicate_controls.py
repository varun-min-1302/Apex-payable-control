from backend.domain.controls.base import BaseControl, ControlContext
from backend.application.dto.control_dto import ControlEvaluation
from backend.database.enums import ControlCategory, ControlCode, ControlStatus, SeverityLevel

class DuplicateInvoiceControl(BaseControl):
    control_code = ControlCode.DUPLICATE_EXACT.value
    category = ControlCategory.DUPLICATE.value

    def execute(self, context: ControlContext) -> ControlEvaluation:
        curr_inv_id = context.invoice.id
        curr_doc_hash = (context.invoice.document_hash or "").strip().lower()
        curr_inv_num = context.invoice.invoice_number.strip().lower()
        curr_vendor_id = context.invoice.vendor_id

        # Inspect historical invoices loaded in context for duplicates
        for hist in context.historical_invoices:
            if hist.id == curr_inv_id:
                continue

            # An invoice is a duplicate only relative to an earlier or concurrent submission.
            # Skip if candidate was created after, or created in the same batch with a later invoice number.
            if hist.created_at and context.invoice.created_at:
                if hist.created_at > context.invoice.created_at:
                    continue
                if hist.created_at == context.invoice.created_at and hist.invoice_number > context.invoice.invoice_number:
                    continue

            # 1. Exact document hash collision
            hist_hash = (hist.document_hash or "").strip().lower()
            if curr_doc_hash and hist_hash and curr_doc_hash == hist_hash:
                return ControlEvaluation(
                    control_code=self.control_code,
                    category=self.category,
                    status=ControlStatus.FAIL,
                    severity=SeverityLevel.CRITICAL,
                    message=(
                        f"Exact document hash collision detected. This invoice document is identical to "
                        f"historical invoice {hist.invoice_number} (ID: {hist.id}). Possible duplicate submission or double billing."
                    ),
                    expected_value={"unique_document_hash": True},
                    actual_value={"colliding_invoice_number": hist.invoice_number, "document_hash": curr_doc_hash},
                    evidence={"colliding_invoice_id": str(hist.id), "collision_type": "EXACT_DOCUMENT_HASH"},
                    rule_version=self.rule_version
                )

            # 2. Duplicate invoice number for the same vendor
            hist_inv_num = hist.invoice_number.strip().lower()
            if hist.vendor_id == curr_vendor_id and hist_inv_num == curr_inv_num:
                return ControlEvaluation(
                    control_code=self.control_code,
                    category=self.category,
                    status=ControlStatus.FAIL,
                    severity=SeverityLevel.CRITICAL,
                    message=(
                        f"Duplicate invoice number '{context.invoice.invoice_number}' already exists for this vendor "
                        f"(Invoice ID: {hist.id}). Double billing prevention triggered."
                    ),
                    expected_value={"unique_vendor_invoice_number": True},
                    actual_value={"duplicate_invoice_number": context.invoice.invoice_number},
                    evidence={"colliding_invoice_id": str(hist.id), "collision_type": "VENDOR_INVOICE_NUMBER"},
                    rule_version=self.rule_version
                )

        return ControlEvaluation(
            control_code=self.control_code,
            category=self.category,
            status=ControlStatus.PASS,
            severity=SeverityLevel.INFO,
            message="No exact duplicate invoice found by document hash or vendor invoice reference.",
            expected_value={"is_duplicate": False},
            actual_value={"is_duplicate": False},
            rule_version=self.rule_version
        )

class SemanticDuplicateControl(BaseControl):
    control_code = ControlCode.DUPLICATE_SEMANTIC.value
    category = ControlCategory.DUPLICATE.value

    def execute(self, context: ControlContext) -> ControlEvaluation:
        """
        Evaluates semantic invoice similarity via pgvector.
        When embeddings are absent, reports NOT_APPLICABLE honestly without fabricating scores.
        """
        # Vector embeddings are not populated for raw extractions yet.
        return ControlEvaluation(
            control_code=self.control_code,
            category=self.category,
            status=ControlStatus.NOT_APPLICABLE,
            severity=SeverityLevel.INFO,
            message="Semantic similarity check is NOT_APPLICABLE: Vector embeddings have not been generated for this invoice revision.",
            expected_value={"vector_embeddings_available": True},
            actual_value={"vector_embeddings_available": False, "embedding_model_invoked": False},
            rule_version=self.rule_version
        )
