import copy
import logging
import re
import time
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from rapidfuzz import fuzz

from backend.core.config import settings
from backend.application.storage.base import DocumentStorage
from backend.application.extraction import (
    InvoiceExtractor,
    GeminiExtractionResponse,
    ExtractedField,
    ExtractedLineItem,
    VendorMatchInfo,
    ExtractionResult,
    InvoiceDraftResponse,
    ConfirmDraftResponse,
    get_extractor,
    PermanentExtractionError,
    TransientExtractionError,
)
from backend.database.models.ap import (
    InvoiceDocument,
    InvoiceDraft,
    Invoice,
    InvoiceRevision,
    InvoiceItem,
)
from backend.database.models.procurement import Vendor, PurchaseOrder
from backend.database.models.identity import User
from backend.repositories.audit_repository import AuditRepository
from backend.application.services.invoice_control_service import InvoiceControlService

logger = logging.getLogger("ap_control.extraction.service")

class InvoiceExtractionService:
    """
    Orchestration service for Phase 5B AI invoice extraction, evidence mapping,
    deterministic arithmetic validation, vendor matching, draft editing,
    and human confirmation bridging to the 18 Control Engine.
    """

    def __init__(
        self,
        db: Session,
        storage: DocumentStorage,
        extractor: Optional[InvoiceExtractor] = None,
    ):
        self.db = db
        self.storage = storage
        self.extractor = extractor or get_extractor(settings.EXTRACTION_PROVIDER)
        self.audit_repo = AuditRepository(db)

    # -------------------------------------------------------------------------
    # 1. Extraction Pipeline (Document -> AI Extraction -> Normalization -> Draft)
    # -------------------------------------------------------------------------
    def extract_document(
        self,
        tenant_id: UUID,
        document_id: UUID,
        user: User,
        force_reextract: bool = False,
    ) -> InvoiceDraft:
        """
        Extract structured invoice data from an existing InvoiceDocument.
        Idempotent: If an active draft already exists and force_reextract is False,
        returns the existing draft without re-querying Gemini or consuming tokens.
        """
        start_time = time.perf_counter()

        # 1. Verify document exists and belongs to current tenant
        doc = (
            self.db.query(InvoiceDocument)
            .filter(InvoiceDocument.id == document_id, InvoiceDocument.tenant_id == tenant_id)
            .first()
        )
        if not doc:
            raise PermanentExtractionError(
                f"Document {document_id} was not found in current tenant.",
                details={"document_id": str(document_id)}
            )

        # 2. Idempotency Check: return existing active draft unless force_reextract
        if not force_reextract:
            existing_draft = (
                self.db.query(InvoiceDraft)
                .filter(InvoiceDraft.document_id == document_id, InvoiceDraft.tenant_id == tenant_id)
                .order_by(InvoiceDraft.created_at.desc())
                .first()
            )
            if existing_draft:
                logger.info(
                    f"event=invoice_draft_cache_hit tenant_id={tenant_id} document_id={document_id} "
                    f"draft_id={existing_draft.id} status={existing_draft.status}"
                )
                return existing_draft

        # 3. Securely load document bytes via DocumentStorage abstraction
        if not self.storage.exists(doc.storage_key):
            raise PermanentExtractionError(
                "Document file is missing from underlying storage.",
                details={"storage_key": doc.storage_key}
            )
        doc_bytes = self.storage.get(doc.storage_key)

        # 4. Audit Log: Extraction Started
        self.audit_repo.record_event(
            tenant_id=tenant_id,
            action="INVOICE_EXTRACTION_STARTED",
            entity_type="INVOICE_DOCUMENT",
            entity_id=doc.id,
            actor_user_id=user.id,
            metadata={
                "provider": settings.EXTRACTION_PROVIDER,
                "model": settings.GEMINI_MODEL,
                "filename": doc.original_filename,
                "size_bytes": doc.file_size_bytes,
            },
        )

        # 5. Execute Extraction via Provider Abstraction
        try:
            raw_result: GeminiExtractionResponse = self.extractor.extract(
                document_bytes=doc_bytes,
                mime_type=doc.mime_type,
                filename=doc.original_filename,
            )
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self.audit_repo.record_event(
                tenant_id=tenant_id,
                action="INVOICE_EXTRACTION_FAILED",
                entity_type="INVOICE_DOCUMENT",
                entity_id=doc.id,
                actor_user_id=user.id,
                metadata={
                    "error": str(exc),
                    "duration_ms": duration_ms,
                    "provider": settings.EXTRACTION_PROVIDER,
                },
            )
            raise

        # 6. Normalize, Calculate Confidence, Arithmetic Check, and Vendor Match
        processed = self._process_extracted_data(raw_result, tenant_id)

        # 7. Persist InvoiceDraft
        draft = InvoiceDraft(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            document_id=doc.id,
            status="EXTRACTED",
            extracted_data=processed["extracted_data"],
            field_confidences=processed["field_confidences"],
            overall_confidence=processed["overall_confidence"],
            warnings=processed["warnings"],
            vendor_match=processed["vendor_match"],
            confirmed_invoice_id=None,
            reviewed_by=None,
            reviewed_at=None,
        )
        self.db.add(draft)

        # Update document status
        doc.status = "DRAFT_CREATED"
        self.db.flush()

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        # 8. Audit Log: Extraction Completed
        self.audit_repo.record_event(
            tenant_id=tenant_id,
            action="INVOICE_EXTRACTION_COMPLETED",
            entity_type="INVOICE_DRAFT",
            entity_id=draft.id,
            actor_user_id=user.id,
            metadata={
                "document_id": str(doc.id),
                "duration_ms": duration_ms,
                "overall_confidence": float(draft.overall_confidence) if draft.overall_confidence else None,
                "warning_count": len(draft.warnings),
                "provider": settings.EXTRACTION_PROVIDER,
            },
        )
        self.db.commit()
        return draft

    # -------------------------------------------------------------------------
    # 2. Data Processing & Independent Deterministic Validation
    # -------------------------------------------------------------------------
    def _process_extracted_data(
        self,
        raw: GeminiExtractionResponse,
        tenant_id: UUID,
    ) -> Dict[str, Any]:
        """
        Normalizes decimals and dates, calculates independent arithmetic reconciliation,
        normalizes field confidences, computes overall confidence, and matches vendors.
        """
        extracted_dict = raw.model_dump()
        warnings: List[str] = []
        field_confidences: Dict[str, float] = {}

        # Helper to extract and normalize confidence
        def get_field_conf(f_data: Optional[Dict[str, Any]]) -> float:
            if not f_data or f_data.get("value") is None:
                return 0.0
            raw_c = f_data.get("confidence", 0.0)
            return max(0.0, min(1.0, float(raw_c)))

        # Header fields normalization
        header_keys = [
            "invoice_number", "invoice_date", "due_date", "vendor_name",
            "vendor_tax_id", "purchase_order_number", "currency",
            "payment_terms_days", "subtotal", "tax_total", "grand_total"
        ]
        for key in header_keys:
            field_data = extracted_dict.get(key)
            if field_data:
                field_confidences[key] = get_field_conf(field_data)
                # Clean up string value
                if field_data.get("value"):
                    field_data["value"] = str(field_data["value"]).strip()

        # Normalize dates
        for d_key in ["invoice_date", "due_date"]:
            f = extracted_dict.get(d_key)
            if f and f.get("value"):
                norm_d = self.normalize_date(f["value"])
                if norm_d:
                    f["value"] = norm_d
                else:
                    warnings.append(f"Date field '{d_key}' with value '{f['value']}' could not be normalized.")

        # Normalize decimal amounts
        subtotal_dec = self.normalize_decimal(extracted_dict.get("subtotal", {}).get("value") if extracted_dict.get("subtotal") else None)
        tax_total_dec = self.normalize_decimal(extracted_dict.get("tax_total", {}).get("value") if extracted_dict.get("tax_total") else None)
        grand_total_dec = self.normalize_decimal(extracted_dict.get("grand_total", {}).get("value") if extracted_dict.get("grand_total") else None)

        if subtotal_dec is not None and extracted_dict.get("subtotal"):
            extracted_dict["subtotal"]["value"] = str(subtotal_dec)
        if tax_total_dec is not None and extracted_dict.get("tax_total"):
            extracted_dict["tax_total"]["value"] = str(tax_total_dec)
        if grand_total_dec is not None and extracted_dict.get("grand_total"):
            extracted_dict["grand_total"]["value"] = str(grand_total_dec)

        # Line items processing
        line_items = extracted_dict.get("line_items", [])
        line_item_sum = Decimal("0.00")
        for item in line_items:
            # Normalize line item numbers
            qty_dec = self.normalize_decimal(item.get("quantity", {}).get("value") if item.get("quantity") else None)
            unit_price_dec = self.normalize_decimal(item.get("unit_price", {}).get("value") if item.get("unit_price") else None)
            tax_rate_dec = self.normalize_decimal(item.get("tax_rate", {}).get("value") if item.get("tax_rate") else None)
            line_total_dec = self.normalize_decimal(item.get("line_total", {}).get("value") if item.get("line_total") else None)

            if qty_dec is not None and item.get("quantity"):
                item["quantity"]["value"] = str(qty_dec)
            if unit_price_dec is not None and item.get("unit_price"):
                item["unit_price"]["value"] = str(unit_price_dec)
            if tax_rate_dec is not None and item.get("tax_rate"):
                item["tax_rate"]["value"] = str(tax_rate_dec)
            if line_total_dec is not None and item.get("line_total"):
                item["line_total"]["value"] = str(line_total_dec)
                line_item_sum += line_total_dec

        # Independent Deterministic Arithmetic Validation
        arithmetic_valid = True
        if subtotal_dec is not None and tax_total_dec is not None and grand_total_dec is not None:
            expected_grand_total = subtotal_dec + tax_total_dec
            if abs(expected_grand_total - grand_total_dec) > Decimal("0.05"):
                arithmetic_valid = False
                warnings.append(
                    f"Arithmetic discrepancy: Subtotal (₹{subtotal_dec}) + Tax (₹{tax_total_dec}) "
                    f"= ₹{expected_grand_total}, but Grand Total is ₹{grand_total_dec}."
                )

        if subtotal_dec is not None and len(line_items) > 0:
            if abs(line_item_sum - subtotal_dec) > Decimal("0.05"):
                warnings.append(
                    f"Line items reconciliation: Sum of item totals (₹{line_item_sum}) "
                    f"does not match extracted subtotal (₹{subtotal_dec})."
                )

        # Vendor Matching against procurement.vendors
        vendor_name_val = extracted_dict.get("vendor_name", {}).get("value") if extracted_dict.get("vendor_name") else None
        vendor_tax_id_val = extracted_dict.get("vendor_tax_id", {}).get("value") if extracted_dict.get("vendor_tax_id") else None
        vendor_match = self._match_vendor(tenant_id, vendor_name_val, vendor_tax_id_val)
        if not vendor_match.get("matched"):
            warnings.append(f"Vendor '{vendor_name_val or 'Unknown'}' is not recognized in approved vendor records.")

        # PO Presence Check
        po_number_val = extracted_dict.get("purchase_order_number", {}).get("value") if extracted_dict.get("purchase_order_number") else None
        if po_number_val:
            po_record = (
                self.db.query(PurchaseOrder)
                .filter(PurchaseOrder.po_number == po_number_val, PurchaseOrder.tenant_id == tenant_id)
                .first()
            )
            if not po_record:
                warnings.append(f"Referenced PO '{po_number_val}' was not found in procurement records.")

        # Overall Confidence Calculation
        weights = {
            "invoice_number": 0.25,
            "grand_total": 0.25,
            "vendor_name": 0.20,
            "invoice_date": 0.15,
            "purchase_order_number": 0.15,
        }
        weighted_sum = 0.0
        total_weight = 0.0
        for k, w in weights.items():
            conf = field_confidences.get(k, 0.0)
            weighted_sum += conf * w
            total_weight += w

        overall_conf = weighted_sum / total_weight if total_weight > 0 else 0.0
        # If arithmetic discrepancy found, apply 0.15 penalty to overall confidence
        if not arithmetic_valid:
            overall_conf = max(0.0, overall_conf - 0.15)

        overall_conf = round(overall_conf, 4)

        return {
            "extracted_data": extracted_dict,
            "field_confidences": field_confidences,
            "overall_confidence": Decimal(str(overall_conf)),
            "warnings": warnings,
            "vendor_match": vendor_match,
            "arithmetic_valid": arithmetic_valid,
        }

    # -------------------------------------------------------------------------
    # 3. Deterministic Vendor Matching
    # -------------------------------------------------------------------------
    def _match_vendor(
        self,
        tenant_id: UUID,
        vendor_name: Optional[str],
        vendor_tax_id: Optional[str],
    ) -> Dict[str, Any]:
        """
        Deterministic backend search for approved vendor in procurement.vendors:
        1. Exact Tax ID / GSTIN match
        2. Exact legal or display name match (case-insensitive)
        3. Fuzzy name match (token_sort_ratio >= 85)
        """
        all_vendors = self.db.query(Vendor).filter(Vendor.tenant_id == tenant_id).all()

        # Step 1: Match by Tax Identifier
        if vendor_tax_id:
            tax_clean = vendor_tax_id.strip().upper()
            for v in all_vendors:
                if v.tax_identifier and v.tax_identifier.strip().upper() == tax_clean:
                    return {
                        "matched": True,
                        "vendor_id": str(v.id),
                        "vendor_name": v.legal_name,
                        "vendor_code": v.vendor_code,
                        "tax_identifier": v.tax_identifier,
                        "match_method": "TAX_ID",
                        "match_score": 1.0,
                    }

        # Step 2: Match by Exact Name
        if vendor_name:
            name_clean = vendor_name.strip().lower()
            for v in all_vendors:
                if v.legal_name.lower() == name_clean or (v.display_name and v.display_name.lower() == name_clean):
                    return {
                        "matched": True,
                        "vendor_id": str(v.id),
                        "vendor_name": v.legal_name,
                        "vendor_code": v.vendor_code,
                        "tax_identifier": v.tax_identifier,
                        "match_method": "EXACT_NAME",
                        "match_score": 1.0,
                    }

            # Step 3: Fuzzy Name Matching
            best_match: Optional[Vendor] = None
            best_score: float = 0.0
            for v in all_vendors:
                score1 = fuzz.token_sort_ratio(name_clean, v.legal_name.lower())
                score2 = fuzz.token_sort_ratio(name_clean, (v.display_name or "").lower()) if v.display_name else 0
                max_s = max(score1, score2)
                if max_s > best_score:
                    best_score = max_s
                    best_match = v

            if best_match and best_score >= 85.0:
                return {
                    "matched": True,
                    "vendor_id": str(best_match.id),
                    "vendor_name": best_match.legal_name,
                    "vendor_code": best_match.vendor_code,
                    "tax_identifier": best_match.tax_identifier,
                    "match_method": "FUZZY_NAME",
                    "match_score": round(best_score / 100.0, 2),
                }

        return {
            "matched": False,
            "vendor_id": None,
            "vendor_name": None,
            "vendor_code": None,
            "tax_identifier": None,
            "match_method": "NO_MATCH",
            "match_score": 0.0,
        }

    # -------------------------------------------------------------------------
    # 4. Human Review & Editing of Draft
    # -------------------------------------------------------------------------
    def update_draft(
        self,
        tenant_id: UUID,
        draft_id: UUID,
        updates: Dict[str, Any],
        user: User,
    ) -> InvoiceDraft:
        """
        Updates draft values following human review.
        Preserves original values while marking edited fields as source="HUMAN_REVIEW".
        """
        draft = (
            self.db.query(InvoiceDraft)
            .filter(InvoiceDraft.id == draft_id, InvoiceDraft.tenant_id == tenant_id)
            .first()
        )
        if not draft:
            raise PermanentExtractionError(f"Draft {draft_id} not found.")

        if draft.status == "CONFIRMED":
            raise PermanentExtractionError("Cannot edit a draft that has already been confirmed.")

        current_data = copy.deepcopy(draft.extracted_data or {})
        updated_extracted = updates.get("extracted_data") or {}

        # Merge any top-level fields passed directly
        for k in ["invoice_number", "invoice_date", "due_date", "purchase_order_number", "currency", "subtotal", "tax_total", "grand_total"]:
            if k in updates and updates[k] is not None:
                updated_extracted[k] = updates[k]

        for field_name, new_val in updated_extracted.items():
            if field_name == "line_items":
                continue
            if field_name in current_data:
                field_obj = current_data[field_name] or {}
                orig_val = field_obj.get("value")
                new_str = str(new_val) if new_val is not None else None
                if str(orig_val) != str(new_str):
                    field_obj["original_value"] = orig_val
                    field_obj["value"] = new_val
                    field_obj["source"] = "HUMAN_REVIEW"
                    field_obj["confidence"] = 1.0
                    current_data[field_name] = field_obj
            else:
                current_data[field_name] = {
                    "value": new_val,
                    "confidence": 1.0,
                    "source": "HUMAN_REVIEW",
                    "original_value": None,
                }

        # Handle line items update
        line_items_update = updates.get("line_items") or updated_extracted.get("line_items")
        if line_items_update is not None:
            if "line_items" not in current_data:
                current_data["line_items"] = {"value": [], "confidence": 1.0, "source": "HUMAN_REVIEW"}
            current_data["line_items"]["value"] = line_items_update
            current_data["line_items"]["source"] = "HUMAN_REVIEW"
            current_data["line_items"]["confidence"] = 1.0

        draft.extracted_data = current_data
        draft.status = "IN_REVIEW"
        draft.reviewed_by = user.id
        draft.reviewed_at = datetime.now(timezone.utc)

        # If user explicitly matched a vendor
        vendor_id_override = updates.get("vendor_id")
        if vendor_id_override:
            v_obj = self.db.query(Vendor).filter(Vendor.id == vendor_id_override, Vendor.tenant_id == tenant_id).first()
            if v_obj:
                draft.vendor_match = {
                    "matched": True,
                    "vendor_id": str(v_obj.id),
                    "vendor_name": v_obj.legal_name,
                    "vendor_code": v_obj.vendor_code,
                    "tax_identifier": v_obj.tax_identifier,
                    "match_method": "MANUAL_SELECT",
                    "match_score": 1.0,
                }

        self.db.flush()
        self.audit_repo.record_event(
            tenant_id=tenant_id,
            action="INVOICE_DRAFT_EDITED",
            entity_type="INVOICE_DRAFT",
            entity_id=draft.id,
            actor_user_id=user.id,
            metadata={"reviewed_by": str(user.id)},
        )
        self.db.commit()
        return draft

    # -------------------------------------------------------------------------
    # 5. Confirmation & Bridge to Deterministic Control Engine
    # -------------------------------------------------------------------------
    def confirm_draft(
        self,
        tenant_id: UUID,
        draft_id: UUID,
        user: User,
    ) -> ConfirmDraftResponse:
        """
        Converts an approved Draft into ap.invoices, ap.invoice_revisions, and ap.invoice_items.
        Atomic transaction:
        1. Validates required fields are present.
        2. Creates ap.invoices + ap.invoice_revisions + ap.invoice_items.
        3. Links invoice_documents.invoice_id = invoice.id.
        4. Marks draft as CONFIRMED.
        5. Commits transaction.
        6. AFTER COMMIT: Invokes InvoiceControlService.trigger_control_run().
        """
        draft = (
            self.db.query(InvoiceDraft)
            .filter(InvoiceDraft.id == draft_id, InvoiceDraft.tenant_id == tenant_id)
            .first()
        )
        if not draft:
            raise PermanentExtractionError(f"Draft {draft_id} not found.")

        if draft.status == "CONFIRMED":
            raise PermanentExtractionError(
                f"Draft {draft_id} has already been confirmed as invoice {draft.confirmed_invoice_id}."
            )

        data = draft.extracted_data or {}
        inv_num = data.get("invoice_number", {}).get("value") if data.get("invoice_number") else None
        inv_date_str = data.get("invoice_date", {}).get("value") if data.get("invoice_date") else None
        due_date_str = data.get("due_date", {}).get("value") if data.get("due_date") else None
        grand_total_str = data.get("grand_total", {}).get("value") if data.get("grand_total") else None

        if not inv_num:
            raise PermanentExtractionError("Invoice Number is required to confirm the invoice.")
        if not inv_date_str:
            raise PermanentExtractionError("Invoice Date is required to confirm the invoice.")
        if not grand_total_str:
            raise PermanentExtractionError("Grand Total is required to confirm the invoice.")

        # Resolve vendor
        vendor_match = draft.vendor_match or {}
        vendor_id_str = vendor_match.get("vendor_id")
        if not vendor_id_str:
            raise PermanentExtractionError(
                "A recognized vendor is required before confirming the invoice. Please select or verify the vendor."
            )
        vendor_id = UUID(vendor_id_str)

        # Resolve dates
        try:
            inv_date = date.fromisoformat(inv_date_str)
        except Exception:
            raise PermanentExtractionError(f"Invalid invoice date format: {inv_date_str}. Expected YYYY-MM-DD.")

        due_date = inv_date
        if due_date_str:
            try:
                due_date = date.fromisoformat(due_date_str)
            except Exception:
                due_date = inv_date

        subtotal_dec = self.normalize_decimal(data.get("subtotal", {}).get("value") if data.get("subtotal") else None) or Decimal("0.00")
        tax_total_dec = self.normalize_decimal(data.get("tax_total", {}).get("value") if data.get("tax_total") else None) or Decimal("0.00")
        grand_total_dec = self.normalize_decimal(grand_total_str) or (subtotal_dec + tax_total_dec)

        # Resolve PO if matched
        po_id: Optional[UUID] = None
        po_num = data.get("purchase_order_number", {}).get("value") if data.get("purchase_order_number") else None
        if po_num:
            po_record = (
                self.db.query(PurchaseOrder)
                .filter(PurchaseOrder.po_number == po_num, PurchaseOrder.tenant_id == tenant_id)
                .first()
            )
            if po_record:
                po_id = po_record.id

        doc = (
            self.db.query(InvoiceDocument)
            .filter(InvoiceDocument.id == draft.document_id)
            .first()
        )

        # ----------------- BEGIN ATOMIC TRANSACTION -----------------
        invoice_id = uuid.uuid4()
        revision_id = uuid.uuid4()

        invoice = Invoice(
            id=invoice_id,
            tenant_id=tenant_id,
            vendor_id=vendor_id,
            purchase_order_id=po_id,
            invoice_number=inv_num,
            invoice_date=inv_date,
            due_date=due_date,
            currency=data.get("currency", {}).get("value") or "INR",
            status="RECEIVED",
            current_revision_id=None,
            source_type="UPLOAD",
            source_file_name=doc.original_filename if doc else None,
            document_hash=doc.sha256_hash if doc else None,
            extraction_status="COMPLETED",
            extraction_confidence=draft.overall_confidence,
            submitted_by=user.id,
        )
        self.db.add(invoice)
        self.db.flush()

        revision = InvoiceRevision(
            id=revision_id,
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            revision_number=1,
            invoice_number=inv_num,
            invoice_date=inv_date,
            due_date=due_date,
            currency=invoice.currency,
            subtotal=subtotal_dec,
            discount_total=Decimal("0.00"),
            tax_total=tax_total_dec,
            grand_total=grand_total_dec,
            vendor_name_as_submitted=data.get("vendor_name", {}).get("value"),
            vendor_tax_id_as_submitted=data.get("vendor_tax_id", {}).get("value"),
            extraction_method=settings.EXTRACTION_PROVIDER,
            extraction_confidence=draft.overall_confidence,
            raw_extracted_data=data,
            submitted_by=user.id,
        )
        self.db.add(revision)
        self.db.flush()

        invoice.current_revision_id = revision_id
        self.db.flush()

        # Create Line Items
        raw_items = data.get("line_items", [])
        if raw_items:
            for idx, itm in enumerate(raw_items, start=1):
                qty_dec = self.normalize_decimal(itm.get("quantity", {}).get("value") if itm.get("quantity") else None) or Decimal("1.0000")
                unit_price_dec = self.normalize_decimal(itm.get("unit_price", {}).get("value") if itm.get("unit_price") else None) or Decimal("0.00")
                tax_rate_dec = self.normalize_decimal(itm.get("tax_rate", {}).get("value") if itm.get("tax_rate") else None) or Decimal("0.0000")
                line_total_dec = self.normalize_decimal(itm.get("line_total", {}).get("value") if itm.get("line_total") else None) or (qty_dec * unit_price_dec)
                desc = itm.get("description", {}).get("value") or f"Line Item #{idx}"

                item_row = InvoiceItem(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    invoice_revision_id=revision_id,
                    line_number=idx,
                    product_code=None,
                    description=desc,
                    quantity=qty_dec,
                    unit_of_measure="NOS",
                    unit_price=unit_price_dec,
                    discount_amount=Decimal("0.00"),
                    tax_rate=tax_rate_dec,
                    tax_amount=Decimal("0.00"),
                    line_total=line_total_dec,
                )
                self.db.add(item_row)
        else:
            # Fallback single item matching grand total
            fallback_item = InvoiceItem(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                invoice_revision_id=revision_id,
                line_number=1,
                product_code=None,
                description=f"Invoice #{inv_num} Services/Goods",
                quantity=Decimal("1.0000"),
                unit_of_measure="NOS",
                unit_price=subtotal_dec or grand_total_dec,
                discount_amount=Decimal("0.00"),
                tax_rate=Decimal("18.0000") if tax_total_dec > 0 else Decimal("0.0000"),
                tax_amount=tax_total_dec,
                line_total=grand_total_dec,
            )
            self.db.add(fallback_item)

        # Update document reference
        if doc:
            doc.invoice_id = invoice_id
            doc.status = "LINKED_TO_INVOICE"

        # Update draft
        draft.status = "CONFIRMED"
        draft.confirmed_invoice_id = invoice_id
        draft.reviewed_by = user.id
        draft.reviewed_at = datetime.now(timezone.utc)

        # Audit Event
        self.audit_repo.record_event(
            tenant_id=tenant_id,
            action="INVOICE_DRAFT_CONFIRMED",
            entity_type="INVOICE_DRAFT",
            entity_id=draft.id,
            actor_user_id=user.id,
            metadata={
                "invoice_id": str(invoice_id),
                "invoice_number": inv_num,
                "grand_total": str(grand_total_dec),
            },
        )

        self.db.commit()
        # ----------------- END ATOMIC TRANSACTION -----------------

        # AFTER COMMIT: Invoke existing deterministic Control Engine
        ctrl_service = InvoiceControlService(self.db)
        control_run, summary, decision = ctrl_service.trigger_control_run(
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            revision_id=revision_id,
            triggered_by=user.id,
        )
        self.db.commit()
        self.db.refresh(invoice)

        return ConfirmDraftResponse(
            draft_id=draft.id,
            invoice_id=invoice_id,
            invoice_number=inv_num,
            status=invoice.status,
            control_run_id=control_run.id if control_run else None,
            control_run_status=control_run.status if control_run else None,
            passed_controls=summary.passed_count if summary else 0,
            failed_controls=summary.failed_count if summary else 0,
            warning_controls=summary.warning_count if summary else 0,
            exception_count=len(decision.pending_exceptions) if (decision and hasattr(decision, "pending_exceptions")) else 0,
            risk_signal_count=len(decision.pending_risk_signals) if (decision and hasattr(decision, "pending_risk_signals")) else 0,
            message=f"Invoice {inv_num} confirmed successfully. 18 validation controls executed.",
        )

    # -------------------------------------------------------------------------
    # Utilities: Decimal and Date Normalization
    # -------------------------------------------------------------------------
    @staticmethod
    def normalize_decimal(val: Any) -> Optional[Decimal]:
        if val is None:
            return None
        if isinstance(val, (int, float, Decimal)):
            return Decimal(str(val)).quantize(Decimal("0.01"))
        s = str(val).strip()
        # Remove currency symbols (₹, $, €, £), commas, spaces
        cleaned = re.sub(r"[^\d.-]", "", s)
        if not cleaned:
            return None
        try:
            return Decimal(cleaned).quantize(Decimal("0.01"))
        except InvalidOperation:
            return None

    @staticmethod
    def normalize_date(val: Any) -> Optional[str]:
        if val is None:
            return None
        s = str(val).strip()
        # Check standard ISO YYYY-MM-DD
        if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
            return s
        # Common formats: DD/MM/YYYY or DD-MM-YYYY
        m = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$", s)
        if m:
            d, month, y = m.groups()
            return f"{y}-{int(month):02d}-{int(d):02d}"
        # Alternative formats: YYYY/MM/DD
        m2 = re.match(r"^(\d{4})[/-](\d{1,2})[/-](\d{1,2})$", s)
        if m2:
            y, month, d = m2.groups()
            return f"{y}-{int(month):02d}-{int(d):02d}"
        return None
