import hashlib
import logging
import os
import time
import uuid
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from backend.application.storage.base import DocumentStorage
from backend.application.services.document_validator import (
    validate_document,
    DocumentValidationError,
)
from backend.database.models.ap import InvoiceDocument
from backend.database.models.identity import User
from backend.repositories.audit_repository import AuditRepository
from backend.api.schemas.document_schemas import InvoiceIntakeResponse

logger = logging.getLogger("ap_control.ingestion")

class InvoiceIngestionService:
    """
    Dedicated business service for secure invoice document ingestion.
    Enforces format validation, exact duplicate detection, storage abstraction,
    atomic transaction safety with orphan file cleanup, and immutable audit logging.
    """

    def __init__(self, db: Session, storage: DocumentStorage):
        self.db = db
        self.storage = storage
        self.audit_repo = AuditRepository(db)

    def ingest_document(
        self,
        tenant_id: UUID,
        user: User,
        filename: str,
        content_type: str,
        file_bytes: bytes,
        source: str = "UPLOAD",
        correlation_id: Optional[str] = None,
    ) -> InvoiceIntakeResponse:
        start_time = time.perf_counter()
        corr_id = correlation_id or f"INGEST-{uuid.uuid4().hex[:12]}"
        file_size = len(file_bytes) if file_bytes else 0

        logger.info(
            f"event=invoice_upload_started tenant_id={tenant_id} user_id={user.id} "
            f"filename={filename} size_bytes={file_size} correlation_id={corr_id}"
        )

        # 1. Validation
        try:
            sanitized_name, valid_mime = validate_document(
                filename=filename,
                content_type=content_type,
                file_bytes=file_bytes,
            )
        except DocumentValidationError as ve:
            logger.warning(
                f"event=invoice_upload_rejected tenant_id={tenant_id} user_id={user.id} "
                f"filename={filename} error={ve} correlation_id={corr_id}"
            )
            raise ve

        # 2. SHA-256 Hashing
        sha256_hash = hashlib.sha256(file_bytes).hexdigest()

        # 3. Exact Duplicate Detection in same tenant
        existing = (
            self.db.query(InvoiceDocument)
            .filter(
                InvoiceDocument.tenant_id == tenant_id,
                InvoiceDocument.sha256_hash == sha256_hash,
            )
            .first()
        )

        if existing:
            duration = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                f"event=invoice_upload_duplicate tenant_id={tenant_id} user_id={user.id} "
                f"existing_doc_id={existing.id} hash={sha256_hash} "
                f"duration_ms={duration} correlation_id={corr_id}"
            )
            return InvoiceIntakeResponse(
                document_id=existing.id,
                tenant_id=tenant_id,
                filename=existing.original_filename,
                size_bytes=existing.file_size_bytes,
                mime_type=existing.mime_type,
                status=existing.status,
                duplicate=True,
                existing_document_id=existing.id,
                invoice_id=existing.invoice_id,
                created_at=existing.created_at,
                message="An identical document has already been uploaded.",
            )

        # 4. Storage Key Generation
        document_id = uuid.uuid4()
        _, ext = os.path.splitext(sanitized_name)
        storage_key = f"tenants/{tenant_id}/documents/{document_id}{ext.lower()}"

        # 5. Secure File Storage via Abstraction
        self.storage.store(storage_key, file_bytes, content_type=valid_mime)

        # 6. Database Persistence & Atomic Error Handling
        try:
            doc = InvoiceDocument(
                id=document_id,
                tenant_id=tenant_id,
                invoice_id=None,
                original_filename=filename,
                sanitized_filename=sanitized_name,
                storage_key=storage_key,
                mime_type=valid_mime,
                file_size_bytes=file_size,
                sha256_hash=sha256_hash,
                source=source or "UPLOAD",
                status="READY_FOR_EXTRACTION",
                uploaded_by=user.id,
            )
            self.db.add(doc)
            self.db.flush()

            # Record immutable audit event
            self.audit_repo.record_event(
                tenant_id=tenant_id,
                action="INVOICE_DOCUMENT_UPLOADED",
                entity_type="INVOICE_DOCUMENT",
                entity_id=doc.id,
                actor_user_id=user.id,
                correlation_id=corr_id,
                previous_state=None,
                new_state={
                    "status": "READY_FOR_EXTRACTION",
                    "filename": sanitized_name,
                    "size_bytes": file_size,
                    "mime_type": valid_mime,
                },
                metadata={
                    "sha256_hash": sha256_hash,
                    "storage_key": storage_key,
                    "source": source or "UPLOAD",
                    "original_filename": filename,
                    "size_bytes": file_size,
                },
            )

            self.db.commit()
            self.db.refresh(doc)

            duration = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                f"event=invoice_upload_completed tenant_id={tenant_id} doc_id={doc.id} "
                f"size_bytes={file_size} duration_ms={duration} correlation_id={corr_id}"
            )

            return InvoiceIntakeResponse(
                document_id=doc.id,
                tenant_id=tenant_id,
                filename=doc.original_filename,
                size_bytes=doc.file_size_bytes,
                mime_type=doc.mime_type,
                status=doc.status,
                duplicate=False,
                existing_document_id=None,
                invoice_id=None,
                created_at=doc.created_at,
                message="Document received and ready for extraction.",
            )

        except Exception as ex:
            self.db.rollback()
            # Attempt cleanup of the newly stored file to prevent uncontrolled orphans
            try:
                self.storage.delete(storage_key)
            except Exception as del_err:
                logger.error(
                    f"event=storage_cleanup_failed storage_key={storage_key} error={del_err}"
                )
            logger.error(
                f"event=invoice_upload_failed tenant_id={tenant_id} error={ex} correlation_id={corr_id}"
            )
            raise ex
