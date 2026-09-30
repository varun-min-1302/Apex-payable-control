import hashlib
import io
import os
import tempfile
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.api.deps import get_db, get_storage
from backend.application.storage.local import LocalStorageProvider
from backend.database.session import SessionLocal
from backend.database.models.identity import User, Tenant
from backend.database.models.ap import InvoiceDocument, PayableLedger, Payment
from backend.database.models.audit import AuditLog

# Real test payload bytes
VALID_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<< /Title (Invoice 101) >>\nendobj\ntrailer\n<< >>\n%%EOF"
VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
VALID_JPEG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\xff\xd9"

@pytest.fixture
def temp_storage():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        storage = LocalStorageProvider(root_dir=tmp_dir)
        yield storage

@pytest.fixture
def client(temp_storage):
    # Override storage dependency to guarantee tests never touch production storage
    app.dependency_overrides[get_storage] = lambda: temp_storage
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

# 1. Valid PDF upload
def test_valid_pdf_upload(client):
    pdf = VALID_PDF_BYTES + f"% unique {uuid.uuid4()}\n".encode()
    files = {"file": ("acme_inv_1.pdf", io.BytesIO(pdf), "application/pdf")}
    resp = client.post("/api/v1/invoices/intake", files=files, headers={"X-Demo-User-Email": "priya.nair@apexfin.in"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "READY_FOR_EXTRACTION"
    assert data["duplicate"] is False
    assert data["size_bytes"] == len(pdf)
    assert data["mime_type"] == "application/pdf"

# 2. Valid PNG upload
def test_valid_png_upload(client):
    png = VALID_PNG_BYTES + uuid.uuid4().bytes
    files = {"file": ("receipt_scan.png", io.BytesIO(png), "image/png")}
    resp = client.post("/api/v1/invoices/intake", files=files, headers={"X-Demo-User-Email": "priya.nair@apexfin.in"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "READY_FOR_EXTRACTION"
    assert data["duplicate"] is False
    assert data["mime_type"] == "image/png"

# 3. Valid JPEG upload
def test_valid_jpeg_upload(client):
    jpeg = VALID_JPEG_BYTES + uuid.uuid4().bytes
    files = {"file": ("photo_invoice.jpg", io.BytesIO(jpeg), "image/jpeg")}
    resp = client.post("/api/v1/invoices/intake", files=files, headers={"X-Demo-User-Email": "priya.nair@apexfin.in"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "READY_FOR_EXTRACTION"
    assert data["duplicate"] is False
    assert data["mime_type"] == "image/jpeg"

# 4. Invalid extension
def test_invalid_extension(client):
    files = {"file": ("script.exe", io.BytesIO(b"MZ\x90\x00fake"), "application/x-msdownload")}
    resp = client.post("/api/v1/invoices/intake", files=files, headers={"X-Demo-User-Email": "priya.nair@apexfin.in"})
    assert resp.status_code == 400
    assert "Unsupported file format" in resp.json()["detail"]

# 5. Invalid MIME/content
def test_invalid_mime(client):
    files = {"file": ("document.pdf", io.BytesIO(VALID_PDF_BYTES), "text/html")}
    resp = client.post("/api/v1/invoices/intake", files=files, headers={"X-Demo-User-Email": "priya.nair@apexfin.in"})
    assert resp.status_code == 400
    assert "Unsupported content type" in resp.json()["detail"]

# 6. Fake PDF signature
def test_fake_pdf_signature(client):
    fake_bytes = b"NOT_A_REAL_PDF_HEADER_CONTENT"
    files = {"file": ("fake.pdf", io.BytesIO(fake_bytes), "application/pdf")}
    resp = client.post("/api/v1/invoices/intake", files=files, headers={"X-Demo-User-Email": "priya.nair@apexfin.in"})
    assert resp.status_code == 400
    assert "Missing or corrupted PDF header signature" in resp.json()["detail"]

# 7. File too large (> 10 MB)
def test_file_too_large(client, monkeypatch):
    from backend.core.config import settings
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_BYTES", 100)
    files = {"file": ("oversized.pdf", io.BytesIO(VALID_PDF_BYTES + b"0" * 200), "application/pdf")}
    resp = client.post("/api/v1/invoices/intake", files=files, headers={"X-Demo-User-Email": "priya.nair@apexfin.in"})
    assert resp.status_code == 400
    assert "File is too large" in resp.json()["detail"]

# 8. SHA-256 calculation
def test_sha256_calculation(client, db):
    unique_content = f"%PDF-1.4 unique content {uuid.uuid4()} %%EOF".encode()
    expected_hash = hashlib.sha256(unique_content).hexdigest()
    files = {"file": ("hashed.pdf", io.BytesIO(unique_content), "application/pdf")}
    resp = client.post("/api/v1/invoices/intake", files=files, headers={"X-Demo-User-Email": "priya.nair@apexfin.in"})
    assert resp.status_code == 201
    doc_id = resp.json()["document_id"]
    
    doc = db.query(InvoiceDocument).filter(InvoiceDocument.id == doc_id).first()
    assert doc is not None
    assert doc.sha256_hash == expected_hash

# 9. Exact duplicate detection
def test_exact_duplicate_detection(client):
    unique_content = f"%PDF-1.4 duplicate test {uuid.uuid4()} %%EOF".encode()
    files1 = {"file": ("dup_original.pdf", io.BytesIO(unique_content), "application/pdf")}
    resp1 = client.post("/api/v1/invoices/intake", files=files1, headers={"X-Demo-User-Email": "priya.nair@apexfin.in"})
    assert resp1.status_code == 201
    doc_id1 = resp1.json()["document_id"]
    assert resp1.json()["duplicate"] is False

    # Second upload with identical bytes
    files2 = {"file": ("dup_copy.pdf", io.BytesIO(unique_content), "application/pdf")}
    resp2 = client.post("/api/v1/invoices/intake", files=files2, headers={"X-Demo-User-Email": "priya.nair@apexfin.in"})
    assert resp2.status_code == 201
    data2 = resp2.json()
    assert data2["duplicate"] is True
    assert data2["document_id"] == doc_id1
    assert data2["existing_document_id"] == doc_id1
    assert "already been uploaded" in data2["message"]

# 10. Different document with different hash
def test_different_documents_different_hashes(client):
    c1 = f"%PDF-1.4 doc1 {uuid.uuid4()} %%EOF".encode()
    c2 = f"%PDF-1.4 doc2 {uuid.uuid4()} %%EOF".encode()
    r1 = client.post("/api/v1/invoices/intake", files={"file": ("d1.pdf", io.BytesIO(c1), "application/pdf")}, headers={"X-Demo-User-Email": "priya.nair@apexfin.in"})
    r2 = client.post("/api/v1/invoices/intake", files={"file": ("d2.pdf", io.BytesIO(c2), "application/pdf")}, headers={"X-Demo-User-Email": "priya.nair@apexfin.in"})
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["document_id"] != r2.json()["document_id"]
    assert r1.json()["duplicate"] is False
    assert r2.json()["duplicate"] is False

# 11. Tenant isolation (Tenant B cannot see Tenant A document)
def test_tenant_isolation(client, db):
    # Upload as user in Apex FinTech
    content = f"%PDF-1.4 tenant isolation {uuid.uuid4()} %%EOF".encode()
    r = client.post("/api/v1/invoices/intake", files={"file": ("tenant_a.pdf", io.BytesIO(content), "application/pdf")}, headers={"X-Demo-User-Email": "priya.nair@apexfin.in"})
    assert r.status_code == 201
    doc_id = r.json()["document_id"]

    # Create temporary tenant B and user B
    tenant_b = Tenant(name="Tenant B Corp", slug=f"tenant-b-{uuid.uuid4().hex[:6]}", status="ACTIVE")
    db.add(tenant_b)
    db.flush()
    user_b = User(tenant_id=tenant_b.id, email=f"user_b_{uuid.uuid4().hex[:6]}@tenantb.com", full_name="User B", status="ACTIVE")
    db.add(user_b)
    db.commit()

    try:
        # User B attempts to access Tenant A document
        get_r = client.get(f"/api/v1/invoices/documents/{doc_id}", headers={"X-Demo-User-Email": user_b.email})
        assert get_r.status_code == 404
    finally:
        db.delete(user_b)
        db.delete(tenant_b)
        db.commit()

# 12. Unauthorized upload (no auth / invalid token)
def test_unauthorized_upload_no_auth(client):
    # Using a non-existent email
    files = {"file": ("no_auth.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
    resp = client.post("/api/v1/invoices/intake", files=files, headers={"X-Demo-User-Email": "nonexistent@nowhere.com"})
    assert resp.status_code == 401

# 13. Read-only user cannot upload (AUDITOR gets 403)
def test_readonly_auditor_cannot_upload(client):
    files = {"file": ("auditor_try.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
    resp = client.post("/api/v1/invoices/intake", files=files, headers={"X-Demo-User-Email": "sunita.mehta@apexfin.in"})
    assert resp.status_code == 403
    assert "Operation requires one of the following roles" in resp.json()["detail"]

# 14. Authorized document retrieval
def test_authorized_document_retrieval(client):
    content = f"%PDF-1.4 authorized retrieval {uuid.uuid4()} %%EOF".encode()
    r = client.post("/api/v1/invoices/intake", files={"file": ("retrieve_me.pdf", io.BytesIO(content), "application/pdf")}, headers={"X-Demo-User-Email": "priya.nair@apexfin.in"})
    assert r.status_code == 201
    doc_id = r.json()["document_id"]

    get_r = client.get(f"/api/v1/invoices/documents/{doc_id}", headers={"X-Demo-User-Email": "priya.nair@apexfin.in"})
    assert get_r.status_code == 200
    assert get_r.content == content
    assert get_r.headers["content-type"] == "application/pdf"

# 15. Unauthorized document retrieval
def test_unauthorized_document_retrieval(client):
    get_r = client.get(f"/api/v1/invoices/documents/{uuid.uuid4()}", headers={"X-Demo-User-Email": "priya.nair@apexfin.in"})
    assert get_r.status_code == 404

# 16. Audit event created
def test_audit_event_created_on_upload(client, db):
    content = f"%PDF-1.4 audit test {uuid.uuid4()} %%EOF".encode()
    r = client.post("/api/v1/invoices/intake", files={"file": ("audited.pdf", io.BytesIO(content), "application/pdf")}, headers={"X-Demo-User-Email": "priya.nair@apexfin.in"})
    assert r.status_code == 201
    doc_id = uuid.UUID(r.json()["document_id"])

    audit_entry = db.query(AuditLog).filter(AuditLog.entity_id == doc_id, AuditLog.action == "INVOICE_DOCUMENT_UPLOADED").first()
    assert audit_entry is not None
    assert audit_entry.entity_type == "INVOICE_DOCUMENT"
    assert audit_entry.new_state["filename"] == "audited.pdf"

# 17. Storage/database failure cleanup
def test_storage_cleanup_on_database_failure(client, monkeypatch, temp_storage):
    from backend.application.services.invoice_ingestion_service import InvoiceIngestionService
    
    # Simulate DB error during flush/commit
    def broken_flush(self):
        raise RuntimeError("Simulated database failure during ingestion")

    monkeypatch.setattr(Session, "flush", broken_flush)

    content = f"%PDF-1.4 rollback test {uuid.uuid4()} %%EOF".encode()
    files = {"file": ("fail_clean.pdf", io.BytesIO(content), "application/pdf")}
    
    with pytest.raises(RuntimeError):
        # Directly invoke ingestion service to test orphan cleanup logic
        from backend.database.session import SessionLocal
        from backend.database.models.identity import User
        db_s = SessionLocal()
        user = db_s.query(User).filter(User.email == "priya.nair@apexfin.in").first()
        svc = InvoiceIngestionService(db_s, temp_storage)
        svc.ingest_document(user.tenant_id, user, "fail_clean.pdf", "application/pdf", content)

    # Verify no file remains in temporary storage
    all_files = []
    for root, _, fs in os.walk(temp_storage.root_dir):
        all_files.extend(fs)
    assert len(all_files) == 0

# 18. Upload does not create payable
def test_upload_does_not_create_payable(client, db):
    count_before = db.query(PayableLedger).count()
    content = f"%PDF-1.4 no payable test {uuid.uuid4()} %%EOF".encode()
    r = client.post("/api/v1/invoices/intake", files={"file": ("no_payable.pdf", io.BytesIO(content), "application/pdf")}, headers={"X-Demo-User-Email": "priya.nair@apexfin.in"})
    assert r.status_code == 201
    count_after = db.query(PayableLedger).count()
    assert count_after == count_before

# 19. Upload does not create payment
def test_upload_does_not_create_payment(client, db):
    count_before = db.query(Payment).count()
    content = f"%PDF-1.4 no payment test {uuid.uuid4()} %%EOF".encode()
    r = client.post("/api/v1/invoices/intake", files={"file": ("no_payment.pdf", io.BytesIO(content), "application/pdf")}, headers={"X-Demo-User-Email": "priya.nair@apexfin.in"})
    assert r.status_code == 201
    count_after = db.query(Payment).count()
    assert count_after == count_before

# 20. Upload does not bypass approval or mark invoice as approved
def test_upload_does_not_bypass_approval(client, db):
    content = f"%PDF-1.4 no bypass test {uuid.uuid4()} %%EOF".encode()
    r = client.post("/api/v1/invoices/intake", files={"file": ("no_bypass.pdf", io.BytesIO(content), "application/pdf")}, headers={"X-Demo-User-Email": "priya.nair@apexfin.in"})
    assert r.status_code == 201
    doc_id = r.json()["document_id"]
    
    doc = db.query(InvoiceDocument).filter(InvoiceDocument.id == doc_id).first()
    assert doc.status == "READY_FOR_EXTRACTION"
    assert doc.status not in ("APPROVED", "PAYABLE_CREATED", "PAID")
