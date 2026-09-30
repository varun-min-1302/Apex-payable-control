import io
import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.core.config import settings
from backend.database.models.identity import Tenant, User, Role, UserRole
from backend.database.models.procurement import Vendor, PurchaseOrder, PurchaseOrderItem
from backend.database.models.ap import (
    InvoiceDocument,
    InvoiceDraft,
    Invoice,
    InvoiceRevision,
    InvoiceItem,
    PayableLedger,
    Payment,
)
from backend.database.models.audit import AuditLog
from backend.application.storage.local import LocalStorageProvider
from backend.application.extraction import (
    GeminiInvoiceExtractor,
    MockInvoiceExtractor,
    GeminiExtractionResponse,
    ExtractedField,
    ExtractedLineItem,
    PermanentExtractionError,
    TransientExtractionError,
)
from backend.application.services.invoice_extraction_service import InvoiceExtractionService
from backend.application.services.invoice_control_service import InvoiceControlService

@pytest.fixture
def test_setup(db_session: Session):
    """Sets up tenant, users, vendor, and purchase order."""
    # Ensure test tenant
    tenant = db_session.query(Tenant).first()
    assert tenant is not None, "Test tenant must be seeded."

    ap_clerk = (
        db_session.query(User)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .filter(User.tenant_id == tenant.id, Role.code == "AP_CLERK")
        .first()
    )
    auditor = (
        db_session.query(User)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .filter(User.tenant_id == tenant.id, Role.code == "AUDITOR")
        .first()
    )

    # Ensure known vendor
    vendor = (
        db_session.query(Vendor)
        .filter(Vendor.tenant_id == tenant.id)
        .first()
    )
    assert vendor is not None

    po = (
        db_session.query(PurchaseOrder)
        .filter(PurchaseOrder.tenant_id == tenant.id, PurchaseOrder.vendor_id == vendor.id)
        .first()
    )

    return {
        "tenant": tenant,
        "ap_clerk": ap_clerk,
        "auditor": auditor,
        "vendor": vendor,
        "po": po,
    }

@pytest.fixture
def sample_pdf_doc(db_session: Session, test_setup, tmp_path):
    """Creates a sample InvoiceDocument on disk and DB."""
    tenant = test_setup["tenant"]
    ap_clerk = test_setup["ap_clerk"]
    storage = LocalStorageProvider(root_dir=str(tmp_path / "storage"))

    doc_id = uuid.uuid4()
    storage_key = f"tenants/{tenant.id}/documents/{doc_id}.pdf"
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Title (Invoice) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    storage.store(storage_key, pdf_bytes, content_type="application/pdf")

    doc = InvoiceDocument(
        id=doc_id,
        tenant_id=tenant.id,
        invoice_id=None,
        original_filename="sample_invoice.pdf",
        sanitized_filename="sample_invoice.pdf",
        storage_key=storage_key,
        mime_type="application/pdf",
        file_size_bytes=len(pdf_bytes),
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        source="UPLOAD",
        status="READY_FOR_EXTRACTION",
        uploaded_by=ap_clerk.id,
    )
    db_session.add(doc)
    db_session.commit()

    from backend.api.deps import get_storage
    app.dependency_overrides[get_storage] = lambda: storage
    try:
        yield doc, storage
    finally:
        app.dependency_overrides.pop(get_storage, None)
        try:
            from backend.database.models.ap import InvoiceDraft, Invoice, InvoiceRevision, InvoiceItem, ControlRun, ControlResult
            # Find any confirmed invoice associated with doc
            fresh_doc = db_session.query(InvoiceDocument).filter(InvoiceDocument.id == doc.id).first()
            if fresh_doc and fresh_doc.invoice_id:
                inv_id = fresh_doc.invoice_id
                fresh_doc.invoice_id = None
                db_session.flush()
                db_session.query(ControlResult).filter(ControlResult.invoice_id == inv_id).delete(synchronize_session=False)
                db_session.query(ControlRun).filter(ControlRun.invoice_id == inv_id).delete(synchronize_session=False)
                for rev in db_session.query(InvoiceRevision).filter(InvoiceRevision.invoice_id == inv_id).all():
                    db_session.query(InvoiceItem).filter(InvoiceItem.invoice_revision_id == rev.id).delete(synchronize_session=False)
                db_session.query(InvoiceRevision).filter(InvoiceRevision.invoice_id == inv_id).delete(synchronize_session=False)
                db_session.query(Invoice).filter(Invoice.id == inv_id).delete(synchronize_session=False)
            db_session.query(InvoiceDraft).filter(InvoiceDraft.document_id == doc.id).delete(synchronize_session=False)
            db_session.query(InvoiceDocument).filter(InvoiceDocument.id == doc.id).delete(synchronize_session=False)
            db_session.commit()
        except Exception:
            db_session.rollback()


class TestGeminiClientAndExtractor:
    """Tests 1-7: Gemini Client Abstraction and Error Handling."""

    def test_missing_api_key_raises_permanent_error(self):
        extractor = GeminiInvoiceExtractor(api_key="")
        with pytest.raises(PermanentExtractionError) as exc_info:
            extractor.extract(b"%PDF-1.4", "application/pdf", "test.pdf")
        assert "GEMINI_API_KEY is not configured" in str(exc_info.value)

    def test_unsupported_mime_type_rejected(self):
        extractor = GeminiInvoiceExtractor(api_key="mock_key")
        with pytest.raises(PermanentExtractionError) as exc_info:
            extractor.extract(b"data", "text/plain", "test.txt")
        assert "Unsupported MIME type" in str(exc_info.value)

    def test_empty_document_bytes_rejected(self):
        extractor = GeminiInvoiceExtractor(api_key="mock_key")
        with pytest.raises(PermanentExtractionError) as exc_info:
            extractor.extract(b"", "application/pdf", "test.pdf")
        assert "empty document bytes" in str(exc_info.value)

    def test_mock_extractor_success(self):
        extractor = MockInvoiceExtractor()
        res = extractor.extract(b"%PDF-1.4", "application/pdf", "invoice.pdf")
        assert res.invoice_number.value == "INV-2026-1042"
        assert res.grand_total.value == "118000.00"
        assert len(res.line_items) == 2

    def test_mock_extractor_transient_failure_simulated(self):
        extractor = MockInvoiceExtractor()
        with pytest.raises(TransientExtractionError):
            extractor.extract(b"%PDF-1.4", "application/pdf", "transient_fail.pdf")

    def test_mock_extractor_permanent_failure_simulated(self):
        extractor = MockInvoiceExtractor()
        with pytest.raises(PermanentExtractionError):
            extractor.extract(b"%PDF-1.4", "application/pdf", "perm_fail.pdf")


class TestExtractionServiceLogic:
    """Tests 8-20: Normalization, Evidence, Confidence, Arithmetic, and Vendor Match."""

    def test_decimal_normalization(self):
        norm = InvoiceExtractionService.normalize_decimal
        assert norm("1,000.50") == Decimal("1000.50")
        assert norm("₹ 1,18,000.00") == Decimal("118000.00")
        assert norm("$50.25") == Decimal("50.25")
        assert norm(1500) == Decimal("1500.00")
        assert norm(None) is None
        assert norm("invalid") is None

    def test_date_normalization(self):
        norm = InvoiceExtractionService.normalize_date
        assert norm("2026-09-28") == "2026-09-28"
        assert norm("28/09/2026") == "2026-09-28"
        assert norm("28-09-2026") == "2026-09-28"
        assert norm("2026/09/28") == "2026-09-28"
        assert norm("unknown date") is None
        assert norm(None) is None

    def test_arithmetic_discrepancy_detection(self, db_session, test_setup, sample_pdf_doc):
        doc, storage = sample_pdf_doc
        tenant = test_setup["tenant"]
        ap_clerk = test_setup["ap_clerk"]

        # Rename document filename to trigger arithmetic mismatch fixture in MockInvoiceExtractor
        doc.original_filename = "arithmetic_error.pdf"
        db_session.commit()

        service = InvoiceExtractionService(db=db_session, storage=storage, extractor=MockInvoiceExtractor())
        draft = service.extract_document(tenant.id, doc.id, ap_clerk)

        assert any("Arithmetic discrepancy" in w for w in draft.warnings)
        # Check overall confidence penalized
        assert draft.overall_confidence < Decimal("0.90")

    def test_deterministic_vendor_matching(self, db_session, test_setup, sample_pdf_doc):
        doc, storage = sample_pdf_doc
        tenant = test_setup["tenant"]
        ap_clerk = test_setup["ap_clerk"]
        vendor = test_setup["vendor"]

        service = InvoiceExtractionService(db=db_session, storage=storage, extractor=MockInvoiceExtractor())
        # Test match by tax ID
        res = service._match_vendor(tenant.id, "Random Name", vendor.tax_identifier)
        assert res["matched"] is True
        assert res["match_method"] == "TAX_ID"
        assert res["vendor_id"] == str(vendor.id)

        # Test match by exact name
        res_name = service._match_vendor(tenant.id, vendor.legal_name, "INVALID_TAX")
        assert res_name["matched"] is True
        assert res_name["match_method"] == "EXACT_NAME"

        # Test no match
        res_none = service._match_vendor(tenant.id, "Nonexistent Alien Vendor LLC", "NONEXISTENT")
        assert res_none["matched"] is False


class TestWorkflowAndSecurity:
    """Tests 21-34: Security, Invariants, Draft Lifecycle, and Confirmation."""

    def test_tenant_isolation_on_extract(self, db_session, test_setup, sample_pdf_doc):
        doc, storage = sample_pdf_doc
        ap_clerk = test_setup["ap_clerk"]
        other_tenant_id = uuid.uuid4()

        service = InvoiceExtractionService(db=db_session, storage=storage, extractor=MockInvoiceExtractor())
        with pytest.raises(PermanentExtractionError) as exc:
            service.extract_document(other_tenant_id, doc.id, ap_clerk)
        assert "not found in current tenant" in str(exc.value)

    def test_idempotent_extraction_does_not_re_extract(self, db_session, test_setup, sample_pdf_doc):
        doc, storage = sample_pdf_doc
        tenant = test_setup["tenant"]
        ap_clerk = test_setup["ap_clerk"]

        mock_extractor = MagicMock(wraps=MockInvoiceExtractor())
        service = InvoiceExtractionService(db=db_session, storage=storage, extractor=mock_extractor)

        # First extraction
        draft1 = service.extract_document(tenant.id, doc.id, ap_clerk)
        assert draft1.status == "EXTRACTED"
        assert mock_extractor.extract.call_count == 1

        # Second extraction (should return existing draft without calling extractor)
        draft2 = service.extract_document(tenant.id, doc.id, ap_clerk)
        assert draft2.id == draft1.id
        assert mock_extractor.extract.call_count == 1  # Not called again!

    def test_extraction_does_not_create_invoice_or_payable(self, db_session, test_setup, sample_pdf_doc):
        doc, storage = sample_pdf_doc
        tenant = test_setup["tenant"]
        ap_clerk = test_setup["ap_clerk"]

        invoices_before = db_session.query(Invoice).count()
        payables_before = db_session.query(PayableLedger).count()

        service = InvoiceExtractionService(db=db_session, storage=storage, extractor=MockInvoiceExtractor())
        draft = service.extract_document(tenant.id, doc.id, ap_clerk)

        assert draft.status == "EXTRACTED"
        # Core Invariant check: Invoices and Payables must NOT change!
        assert db_session.query(Invoice).count() == invoices_before
        assert db_session.query(PayableLedger).count() == payables_before

    def test_human_edit_preserves_original_and_marks_human_review(self, db_session, test_setup, sample_pdf_doc):
        doc, storage = sample_pdf_doc
        tenant = test_setup["tenant"]
        ap_clerk = test_setup["ap_clerk"]

        service = InvoiceExtractionService(db=db_session, storage=storage, extractor=MockInvoiceExtractor())
        draft = service.extract_document(tenant.id, doc.id, ap_clerk)

        original_num = draft.extracted_data["invoice_number"]["value"]
        updated = service.update_draft(
            tenant_id=tenant.id,
            draft_id=draft.id,
            updates={"extracted_data": {"invoice_number": "INV-CORRECTED-999"}},
            user=ap_clerk,
        )

        assert updated.status == "IN_REVIEW"
        field_obj = updated.extracted_data["invoice_number"]
        assert field_obj["value"] == "INV-CORRECTED-999"
        assert field_obj["original_value"] == original_num
        assert field_obj["source"] == "HUMAN_REVIEW"
        assert field_obj["confidence"] == 1.0

    def test_draft_confirmation_creates_invoice_and_runs_controls(self, db_session, test_setup, sample_pdf_doc):
        doc, storage = sample_pdf_doc
        tenant = test_setup["tenant"]
        ap_clerk = test_setup["ap_clerk"]
        vendor = test_setup["vendor"]

        service = InvoiceExtractionService(db=db_session, storage=storage, extractor=MockInvoiceExtractor())
        draft = service.extract_document(tenant.id, doc.id, ap_clerk)

        # Ensure vendor is explicitly matched for confirmation
        draft.vendor_match = {
            "matched": True,
            "vendor_id": str(vendor.id),
            "vendor_name": vendor.legal_name,
            "vendor_code": vendor.vendor_code,
            "tax_identifier": vendor.tax_identifier,
        }
        # Use a unique invoice number to avoid uniqueness collision
        unique_inv_num = f"INV-CONFIRM-{uuid.uuid4().hex[:8]}"
        draft.extracted_data["invoice_number"]["value"] = unique_inv_num
        db_session.commit()

        # Confirm draft
        res = service.confirm_draft(tenant.id, draft.id, ap_clerk)

        assert res.invoice_number == unique_inv_num
        assert res.invoice_id is not None
        assert res.control_run_id is not None
        assert res.passed_controls > 0

        # Verify DB records
        inv = db_session.query(Invoice).filter(Invoice.id == res.invoice_id).first()
        assert inv is not None
        assert inv.status in ("RECEIVED", "EXCEPTION", "AWAITING_APPROVAL")
        assert inv.vendor_id == vendor.id
        assert inv.extraction_status == "COMPLETED"

        # Verify revision and items
        rev = db_session.query(InvoiceRevision).filter(InvoiceRevision.invoice_id == inv.id).first()
        assert rev is not None
        assert rev.invoice_number == unique_inv_num
        assert len(rev.items) >= 1

        # Verify document linked
        doc_refreshed = db_session.query(InvoiceDocument).filter(InvoiceDocument.id == doc.id).first()
        assert doc_refreshed.invoice_id == inv.id
        assert doc_refreshed.status == "LINKED_TO_INVOICE"

        # Verify draft marked confirmed
        draft_refreshed = db_session.query(InvoiceDraft).filter(InvoiceDraft.id == draft.id).first()
        assert draft_refreshed.status == "CONFIRMED"
        assert draft_refreshed.confirmed_invoice_id == inv.id

    def test_transaction_boundary_controls_never_run_on_uncommitted_invoice(self, db_session, test_setup, sample_pdf_doc):
        """
        Verify the strict transaction lifecycle invariant:
        BEGIN
          create ap.invoices
          create ap.invoice_revisions
          create ap.invoice_items
          link invoice_documents
          mark invoice_draft CONFIRMED
          write audit event
        COMMIT

        ONLY AFTER THE COMMIT SUCCEEDS:
          InvoiceControlService.trigger_control_run(invoice_id)
        """
        doc, storage = sample_pdf_doc
        tenant = test_setup["tenant"]
        ap_clerk = test_setup["ap_clerk"]
        vendor = test_setup["vendor"]

        service = InvoiceExtractionService(db=db_session, storage=storage, extractor=MockInvoiceExtractor())
        draft = service.extract_document(tenant.id, doc.id, ap_clerk)
        draft.vendor_match = {
            "matched": True,
            "vendor_id": str(vendor.id),
            "vendor_name": vendor.legal_name,
            "vendor_code": vendor.vendor_code,
            "tax_identifier": vendor.tax_identifier,
        }
        draft.extracted_data["invoice_number"]["value"] = f"INV-TX-BOUND-{uuid.uuid4().hex[:8]}"
        db_session.commit()

        # Track execution order: creation commit must precede trigger_control_run
        call_order = []
        original_commit = db_session.commit
        def tracked_commit():
            call_order.append("COMMIT")
            return original_commit()

        with patch.object(db_session, "commit", side_effect=tracked_commit):
            with patch.object(InvoiceControlService, "trigger_control_run") as mock_trigger:
                def fake_trigger(tenant_id, invoice_id, revision_id=None, triggered_by=None):
                    call_order.append("TRIGGER_CONTROL_RUN")
                    # At the exact instant of trigger, the invoice MUST already be saved in DB
                    inv_check = db_session.query(Invoice).filter(Invoice.id == invoice_id).first()
                    assert inv_check is not None
                    mock_run = MagicMock()
                    mock_run.id = uuid.uuid4()
                    mock_run.status = "PASSED"
                    mock_summary = MagicMock()
                    mock_summary.passed_count = 18
                    mock_summary.failed_count = 0
                    mock_summary.warning_count = 0
                    mock_decision = MagicMock()
                    mock_decision.pending_exceptions = []
                    mock_decision.pending_risk_signals = []
                    return mock_run, mock_summary, mock_decision

                mock_trigger.side_effect = fake_trigger

                service.confirm_draft(tenant.id, draft.id, ap_clerk)

                # The first COMMIT MUST occur before TRIGGER_CONTROL_RUN
                assert "COMMIT" in call_order
                assert "TRIGGER_CONTROL_RUN" in call_order
                commit_idx = call_order.index("COMMIT")
                trigger_idx = call_order.index("TRIGGER_CONTROL_RUN")
                assert commit_idx < trigger_idx, f"Creation transaction must commit before control run! Order: {call_order}"


class TestFastAPIDraftEndpoints:
    """Tests 35-39: End-to-end FastAPI endpoint behavior & RBAC."""

    @pytest.fixture
    def client(self, db_session, sample_pdf_doc):
        from backend.api.deps import get_db, get_storage
        doc, storage = sample_pdf_doc
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_storage] = lambda: storage
        with TestClient(app) as c:
            yield c
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_storage, None)

    def test_extract_endpoint_success(self, client, test_setup, sample_pdf_doc):
        doc, _ = sample_pdf_doc
        ap_clerk = test_setup["ap_clerk"]

        # Run with mock provider
        with patch.object(settings, "EXTRACTION_PROVIDER", "mock"):
            res = client.post(
                f"/api/v1/invoices/documents/{doc.id}/extract",
                headers={"X-Demo-User-Email": ap_clerk.email},
            )
            assert res.status_code == 200
            data = res.json()
            assert data["document_id"] == str(doc.id)
            assert data["status"] == "EXTRACTED"
            assert data["overall_confidence"] is not None
            assert "invoice_number" in data["extracted_data"]

    def test_auditor_blocked_from_extract_and_confirm(self, client, test_setup, sample_pdf_doc):
        doc, _ = sample_pdf_doc
        auditor = test_setup["auditor"]

        res_extract = client.post(
            f"/api/v1/invoices/documents/{doc.id}/extract",
            headers={"X-Demo-User-Email": auditor.email},
        )
        assert res_extract.status_code == 403

        res_confirm = client.post(
            f"/api/v1/invoices/drafts/{uuid.uuid4()}/confirm",
            headers={"X-Demo-User-Email": auditor.email},
        )
        assert res_confirm.status_code == 403

    def test_get_and_list_drafts(self, client, test_setup, sample_pdf_doc):
        doc, _ = sample_pdf_doc
        ap_clerk = test_setup["ap_clerk"]

        with patch.object(settings, "EXTRACTION_PROVIDER", "mock"):
            # Extract first
            ext_res = client.post(
                f"/api/v1/invoices/documents/{doc.id}/extract",
                headers={"X-Demo-User-Email": ap_clerk.email},
            )
            draft_id = ext_res.json()["draft_id"]

            # List drafts
            list_res = client.get(
                "/api/v1/invoices/drafts",
                headers={"X-Demo-User-Email": ap_clerk.email},
            )
            assert list_res.status_code == 200
            assert any(d["draft_id"] == draft_id for d in list_res.json())

            # Get single draft
            get_res = client.get(
                f"/api/v1/invoices/drafts/{draft_id}",
                headers={"X-Demo-User-Email": ap_clerk.email},
            )
            assert get_res.status_code == 200
            assert get_res.json()["draft_id"] == draft_id
