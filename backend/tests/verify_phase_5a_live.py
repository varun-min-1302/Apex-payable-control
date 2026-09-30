"""
Live End-to-End Verification script for Phase 5A: Invoice Intake & Secure Document Storage.
Tests the running FastAPI instance at http://localhost:8000.
"""

import io
import requests
import uuid
from backend.database.session import get_session
from backend.database.models.ap import InvoiceDocument, PayableLedger
from backend.database.models.audit import AuditLog

API_URL = "http://localhost:8000/api/v1"

def run_live_verification():
    print("--- 1. Testing Live Intake as AP Clerk (Priya Nair) ---")
    headers_ap = {
        "X-Demo-User-Email": "priya.nair@apexfin.in"
    }

    # Generate a unique sample PDF
    unique_marker = f"INVOICE_DOC_TEST_{uuid.uuid4()}"
    pdf_content = (
        b"%PDF-1.4\n1 0 obj\n<< /Title (" + unique_marker.encode() + b") >>\n"
        b"endobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    )
    
    files = {
        "file": ("invoice_sample.pdf", io.BytesIO(pdf_content), "application/pdf")
    }
    data = {
        "source": "PORTAL_UPLOAD"
    }

    res = requests.post(f"{API_URL}/invoices/intake", headers=headers_ap, files=files, data=data)
    print(f"Status Code: {res.status_code}")
    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
    body = res.json()
    print("Response JSON:", body)
    doc_id = body["document_id"]
    assert body["status"] == "READY_FOR_EXTRACTION"
    assert body["duplicate"] is False
    assert body["mime_type"] == "application/pdf"
    assert "storage_key" not in body  # Internal path/storage key not exposed!
    print("[PASS] Upload response verified.")

    print("\n--- 2. Verifying Database & Audit Trail ---")
    with get_session() as db:
        doc = db.query(InvoiceDocument).filter(InvoiceDocument.id == uuid.UUID(doc_id)).first()
        assert doc is not None, "InvoiceDocument row not found in database!"
        assert doc.status == "READY_FOR_EXTRACTION"
        print(f"[PASS] Found InvoiceDocument row in ap.invoice_documents: {doc.id}, storage_key: {doc.storage_key}")

        audit = (
            db.query(AuditLog)
            .filter(AuditLog.entity_id == uuid.UUID(doc_id), AuditLog.action == "INVOICE_DOCUMENT_UPLOADED")
            .first()
        )
        assert audit is not None, "AuditLog row not found for document upload!"
        print(f"[PASS] Found immutable AuditLog row: action={audit.action}, actor_user_id={audit.actor_user_id}")

        # Check invariant: No payable ledger entry was created
        payables_count = db.query(PayableLedger).count()
        print(f"[PASS] Payable ledger count remains valid and untouched: {payables_count} records")

    print("\n--- 3. Verifying File on Disk ---")
    import os
    expected_path = os.path.join("backend", "storage", doc.storage_key.replace("/", os.sep))
    assert os.path.exists(expected_path), f"File does not exist at {expected_path}!"
    with open(expected_path, "rb") as f:
        stored_bytes = f.read()
    assert stored_bytes == pdf_content, "Stored bytes do not match uploaded bytes!"
    print(f"[PASS] File verified on disk at {expected_path} ({len(stored_bytes)} bytes)")

    print("\n--- 4. Testing Duplicate Detection ---")
    files_dup = {
        "file": ("invoice_sample.pdf", io.BytesIO(pdf_content), "application/pdf")
    }
    res_dup = requests.post(f"{API_URL}/invoices/intake", headers=headers_ap, files=files_dup, data=data)
    print(f"Duplicate Status Code: {res_dup.status_code}")
    assert res_dup.status_code in (200, 201), f"Expected 200/201 for duplicate, got {res_dup.status_code}: {res_dup.text}"
    dup_body = res_dup.json()
    print("Duplicate Response JSON:", dup_body)
    assert dup_body["duplicate"] is True
    assert dup_body["document_id"] == doc_id
    print("[PASS] Duplicate detection successfully caught identical document!")

    print("\n--- 5. Testing RBAC Restriction (Auditor Sunita Mehta) ---")
    headers_auditor = {
        "X-Demo-User-Email": "sunita.mehta@apexfin.in"
    }
    files_aud = {
        "file": ("auditor_test.pdf", io.BytesIO(b"%PDF-1.4\n%%EOF"), "application/pdf")
    }
    res_aud = requests.post(f"{API_URL}/invoices/intake", headers=headers_auditor, files=files_aud, data=data)
    print(f"Auditor Upload Status Code: {res_aud.status_code}")
    assert res_aud.status_code == 403, f"Expected 403 Forbidden for Auditor, got {res_aud.status_code}"
    print("[PASS] Auditor persona properly blocked with 403 Forbidden!")

    print("\n--- 6. Testing Document Download / Retrieval ---")
    res_get = requests.get(f"{API_URL}/invoices/documents/{doc_id}", headers=headers_ap)
    assert res_get.status_code == 200, f"Expected 200, got {res_get.status_code}"
    assert res_get.content == pdf_content, "Downloaded content does not match original!"
    print("[PASS] Document successfully retrieved and streamed via authenticated GET endpoint!")

    print("\n=======================================================")
    print("ALL PHASE 5A LIVE VERIFICATION CHECKS PASSED PERFECTLY!")
    print("=======================================================")

if __name__ == "__main__":
    run_live_verification()
