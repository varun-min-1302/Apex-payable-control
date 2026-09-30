import hashlib
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, desc, or_

from backend.api.deps import get_db, get_current_user, require_roles, get_storage
from backend.application.storage.base import DocumentStorage
from backend.database.models.identity import User
from backend.database.models.ap import (
    Invoice,
    InvoiceRevision,
    InvoiceItem,
    InvoiceDocument,
    InvoiceDraft,
    ControlRun,
    ControlResult,
    Exception as APException,
    RiskSignal,
)
from backend.database.models.procurement import Vendor, PurchaseOrder
from backend.database.enums import InvoiceStatus, ExtractionStatus, ExceptionStatus, RiskSignalStatus
from backend.application.services.control_run_service import ControlRunService
from backend.application.services.invoice_ingestion_service import InvoiceIngestionService
from backend.application.services.invoice_extraction_service import InvoiceExtractionService
from backend.application.services.document_validator import DocumentValidationError
from backend.application.extraction import (
    InvoiceDraftResponse,
    InvoiceDraftUpdate,
    ConfirmDraftResponse,
    PermanentExtractionError,
    TransientExtractionError,
)
from backend.api.schemas.document_schemas import InvoiceIntakeResponse, InvoiceDocumentSummaryOut
from backend.api.schemas.invoice_schemas import (
    InvoiceSummaryOut,
    InvoiceDetailOut,
    InvoiceRevisionOut,
    InvoiceItemOut,
    InvoiceCreateRequest,
)
from backend.api.schemas.control_schemas import (
    ControlResultOut,
    ControlRunSummaryOut,
    TriggerControlRunRequest,
)
from backend.application.services.control_explanation_service import ControlExplanationService
from backend.application.services.risk_intelligence_service import RiskIntelligenceService
from backend.api.schemas.explanation_schemas import (
    InvoiceExplanationOut,
    ControlGraphOut,
    AuditReplayOut,
    RevisionDiffOut,
)
from backend.api.schemas.risk_schemas import InvoiceRiskProfileOut

router = APIRouter(prefix="/invoices", tags=["Invoices"])

def _to_summary_out(inv: Invoice, db: Optional[Session] = None) -> InvoiceSummaryOut:
    grand_total = Decimal("0.00")
    if inv.revisions:
        curr_rev = next((r for r in inv.revisions if r.id == inv.current_revision_id), inv.revisions[-1])
        grand_total = curr_rev.grand_total

    vendor_name = inv.vendor.display_name if inv.vendor else None

    risk_level = None
    risk_score = None
    if db:
        try:
            profile = RiskIntelligenceService(db).get_invoice_risk_profile(inv.tenant_id, inv.id)
            risk_level = profile.risk_level
            risk_score = profile.risk_score
        except Exception:
            pass

    return InvoiceSummaryOut(
        id=inv.id,
        tenant_id=inv.tenant_id,
        vendor_id=inv.vendor_id,
        purchase_order_id=inv.purchase_order_id,
        invoice_number=inv.invoice_number,
        invoice_date=inv.invoice_date,
        due_date=inv.due_date,
        currency=inv.currency,
        status=inv.status,
        source_type=inv.source_type,
        document_hash=inv.document_hash,
        extraction_status=inv.extraction_status,
        extraction_confidence=inv.extraction_confidence,
        current_revision_id=inv.current_revision_id,
        grand_total=grand_total,
        vendor_name=vendor_name,
        risk_level=risk_level,
        risk_score=risk_score,
        created_at=inv.created_at,
    )

@router.get("", response_model=list[InvoiceSummaryOut])
def list_invoices(
    status_filter: Optional[str] = Query(None, alias="status"),
    vendor_id: Optional[UUID] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List invoices for the active tenant with optional status and search filtering."""
    stmt = (
        select(Invoice)
        .where(Invoice.tenant_id == current_user.tenant_id)
        .options(selectinload(Invoice.vendor), selectinload(Invoice.revisions))
        .order_by(desc(Invoice.created_at))
    )

    if status_filter:
        stmt = stmt.where(Invoice.status == status_filter.upper())
    if vendor_id:
        stmt = stmt.where(Invoice.vendor_id == vendor_id)
    if search:
        search_term = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Invoice.invoice_number).like(search_term),
                Invoice.vendor_id.in_(
                    select(Vendor.id).where(func.lower(Vendor.legal_name).like(search_term))
                )
            )
        )

    stmt = stmt.offset(offset).limit(limit)
    invoices = db.execute(stmt).scalars().all()
    return [_to_summary_out(inv, db=db) for inv in invoices]


@router.post("", response_model=InvoiceSummaryOut, status_code=status.HTTP_201_CREATED)
def create_invoice(
    payload: InvoiceCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "AP_CLERK")),
):
    """
    Submit/intake a new invoice document shell with line items and Revision 1.
    Sets status to RECEIVED and calculates totals deterministically.
    """
    vendor = db.query(Vendor).filter(
        Vendor.tenant_id == current_user.tenant_id, Vendor.id == payload.vendor_id
    ).first()
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found.")

    doc_hash = hashlib.sha256(
        (payload.raw_document_content or f"{payload.invoice_number}_{payload.invoice_date}").encode("utf-8")
    ).hexdigest()

    inv = Invoice(
        tenant_id=current_user.tenant_id,
        vendor_id=vendor.id,
        purchase_order_id=payload.purchase_order_id,
        invoice_number=payload.invoice_number,
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        currency=payload.currency,
        status=InvoiceStatus.RECEIVED.value,
        source_type="API_UPLOAD",
        document_hash=doc_hash,
        extraction_status=ExtractionStatus.COMPLETED.value,
        extraction_confidence=Decimal("99.00"),
        submitted_by=current_user.id,
    )
    db.add(inv)
    db.flush()

    subtotal = Decimal("0.00")
    tax_total = Decimal("0.00")

    rev = InvoiceRevision(
        tenant_id=current_user.tenant_id,
        invoice_id=inv.id,
        revision_number=1,
        invoice_number=payload.invoice_number,
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        currency=payload.currency,
        subtotal=Decimal("0.00"),
        discount_total=Decimal("0.00"),
        tax_total=Decimal("0.00"),
        grand_total=Decimal("0.00"),
        vendor_name_as_submitted=vendor.legal_name,
        vendor_tax_id_as_submitted=vendor.tax_identifier,
        bank_account_last4=vendor.bank_account_last4,
        bank_account_hash=vendor.bank_account_hash,
        extraction_method="API_DIRECT",
        extraction_confidence=Decimal("99.00"),
        submitted_at=datetime.now(timezone.utc),
        submitted_by=current_user.id,
    )
    db.add(rev)
    db.flush()

    for item in payload.items:
        line_sub = (item.quantity * item.unit_price).quantize(Decimal("0.01"))
        rate = item.tax_rate if item.tax_rate <= Decimal("1.0") else item.tax_rate / Decimal("100.00")
        line_tax = (line_sub * rate).quantize(Decimal("0.01"))
        line_tot = line_sub + line_tax

        inv_item = InvoiceItem(
            tenant_id=current_user.tenant_id,
            invoice_revision_id=rev.id,
            line_number=item.line_number,
            product_code=item.product_code,
            description=item.description,
            quantity=item.quantity,
            unit_of_measure=item.unit_of_measure,
            unit_price=item.unit_price,
            discount_amount=item.discount_amount,
            tax_rate=item.tax_rate,
            tax_amount=line_tax,
            line_total=line_tot,
        )
        db.add(inv_item)
        subtotal += line_sub
        tax_total += line_tax

    rev.subtotal = subtotal
    rev.tax_total = tax_total
    rev.grand_total = subtotal + tax_total
    inv.current_revision_id = rev.id
    db.commit()

    db.refresh(inv)
    return _to_summary_out(inv)

@router.post("/intake", response_model=InvoiceIntakeResponse, status_code=status.HTTP_201_CREATED)
async def upload_invoice_intake(
    file: UploadFile = File(..., description="Invoice document file (PDF, PNG, JPG/JPEG up to 10MB)"),
    source: str = Form("UPLOAD"),
    db: Session = Depends(get_db),
    storage: DocumentStorage = Depends(get_storage),
    current_user: User = Depends(require_roles("ADMIN", "AP_CLERK", "PROCUREMENT_MANAGER", "FINANCE_MANAGER")),
):
    """
    Intake a raw invoice document (PDF, PNG, JPG/JPEG).
    Validates file headers/magic bytes, enforces 10MB limit, computes SHA-256,
    stores securely through storage abstraction, creates document metadata,
    detects exact duplicates, and writes immutable audit trail.
    Does NOT require PO or vendor; does NOT create payables or approve invoices.
    """
    file_bytes = await file.read()
    ingestion_service = InvoiceIngestionService(db, storage)
    try:
        result = ingestion_service.ingest_document(
            tenant_id=current_user.tenant_id,
            user=current_user,
            filename=file.filename or "invoice_document",
            content_type=file.content_type or "application/octet-stream",
            file_bytes=file_bytes,
            source=source,
        )
        return result
    except DocumentValidationError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

@router.get("/documents", response_model=list[InvoiceDocumentSummaryOut])
def list_invoice_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
):
    """List uploaded invoice documents for the current tenant."""
    docs = (
        db.query(InvoiceDocument)
        .filter(InvoiceDocument.tenant_id == current_user.tenant_id)
        .order_by(desc(InvoiceDocument.created_at))
        .limit(limit)
        .all()
    )
    return [InvoiceDocumentSummaryOut.model_validate(d) for d in docs]


@router.get("/documents/{document_id}")
def get_invoice_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    storage: DocumentStorage = Depends(get_storage),
    current_user: User = Depends(get_current_user),
):
    """
    Authorized document download and preview stream.
    Enforces strict tenant isolation and role authentication. Never leaks filesystem paths.
    """
    doc = (
        db.query(InvoiceDocument)
        .filter(
            InvoiceDocument.id == document_id,
            InvoiceDocument.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice document not found.",
        )

    if not storage.exists(doc.storage_key):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document binary file not found in storage.",
        )

    raw_stream = storage.get_stream(doc.storage_key)
    def stream_content():
        try:
            while chunk := raw_stream.read(65536):
                yield chunk
        finally:
            raw_stream.close()

    return StreamingResponse(
        stream_content(),
        media_type=doc.mime_type,
        headers={"Content-Disposition": f'inline; filename="{doc.sanitized_filename}"'},
    )


# =========================================================================
# Phase 5B: AI Invoice Extraction & Draft Lifecycle Endpoints
# =========================================================================

@router.post(
    "/documents/{document_id}/extract",
    response_model=InvoiceDraftResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(["AP_CLERK", "ADMIN", "FINANCE_MANAGER"]))],
)
def extract_invoice_document(
    document_id: UUID,
    force_reextract: bool = Query(False, description="Force re-extraction even if a draft exists"),
    db: Session = Depends(get_db),
    storage: DocumentStorage = Depends(get_storage),
    current_user: User = Depends(get_current_user),
):
    """
    Extract structured invoice data from an uploaded document using Gemini AI.
    Idempotent: returns existing draft if already extracted unless force_reextract is true.
    Enforces tenant isolation and RBAC.
    """
    service = InvoiceExtractionService(db=db, storage=storage)
    try:
        draft = service.extract_document(
            tenant_id=current_user.tenant_id,
            document_id=document_id,
            user=current_user,
            force_reextract=force_reextract,
        )
        return InvoiceDraftResponse(
            draft_id=draft.id,
            tenant_id=draft.tenant_id,
            document_id=draft.document_id,
            status=draft.status,
            overall_confidence=float(draft.overall_confidence) if draft.overall_confidence is not None else None,
            field_confidences=draft.field_confidences or {},
            warnings=draft.warnings or [],
            vendor_match=draft.vendor_match,
            extracted_data=draft.extracted_data or {},
            confirmed_invoice_id=draft.confirmed_invoice_id,
            reviewed_by=draft.reviewed_by,
            reviewed_at=draft.reviewed_at,
            created_at=draft.created_at,
            updated_at=draft.updated_at,
        )
    except PermanentExtractionError as pe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=pe.message,
        )
    except TransientExtractionError as te:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=te.message,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invoice extraction encountered an unexpected error. Please try again.",
        )


@router.get(
    "/drafts",
    response_model=list[InvoiceDraftResponse],
    dependencies=[Depends(require_roles(["AP_CLERK", "ADMIN", "FINANCE_MANAGER", "FINANCE_HEAD", "AUDITOR"]))],
)
def list_invoice_drafts(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List invoice drafts awaiting human review or confirmation in current tenant."""
    query = db.query(InvoiceDraft).filter(InvoiceDraft.tenant_id == current_user.tenant_id)
    if status_filter:
        query = query.filter(InvoiceDraft.status == status_filter)
    drafts = query.order_by(desc(InvoiceDraft.created_at)).limit(limit).all()

    return [
        InvoiceDraftResponse(
            draft_id=d.id,
            tenant_id=d.tenant_id,
            document_id=d.document_id,
            status=d.status,
            overall_confidence=float(d.overall_confidence) if d.overall_confidence is not None else None,
            field_confidences=d.field_confidences or {},
            warnings=d.warnings or [],
            vendor_match=d.vendor_match,
            extracted_data=d.extracted_data or {},
            confirmed_invoice_id=d.confirmed_invoice_id,
            reviewed_by=d.reviewed_by,
            reviewed_at=d.reviewed_at,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d in drafts
    ]


@router.get(
    "/drafts/{draft_id}",
    response_model=InvoiceDraftResponse,
    dependencies=[Depends(require_roles(["AP_CLERK", "ADMIN", "FINANCE_MANAGER", "FINANCE_HEAD", "AUDITOR"]))],
)
def get_invoice_draft(
    draft_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full details of an invoice draft including evidence and confidences."""
    draft = (
        db.query(InvoiceDraft)
        .filter(InvoiceDraft.id == draft_id, InvoiceDraft.tenant_id == current_user.tenant_id)
        .first()
    )
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice draft not found.",
        )

    return InvoiceDraftResponse(
        draft_id=draft.id,
        tenant_id=draft.tenant_id,
        document_id=draft.document_id,
        status=draft.status,
        overall_confidence=float(draft.overall_confidence) if draft.overall_confidence is not None else None,
        field_confidences=draft.field_confidences or {},
        warnings=draft.warnings or [],
        vendor_match=draft.vendor_match,
        extracted_data=draft.extracted_data or {},
        confirmed_invoice_id=draft.confirmed_invoice_id,
        reviewed_by=draft.reviewed_by,
        reviewed_at=draft.reviewed_at,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
    )


@router.put(
    "/drafts/{draft_id}",
    response_model=InvoiceDraftResponse,
    dependencies=[Depends(require_roles(["AP_CLERK", "ADMIN", "FINANCE_MANAGER"]))],
)
def update_invoice_draft(
    draft_id: UUID,
    payload: InvoiceDraftUpdate,
    db: Session = Depends(get_db),
    storage: DocumentStorage = Depends(get_storage),
    current_user: User = Depends(get_current_user),
):
    """
    Update editable draft fields during human review.
    Preserves original extracted values and marks modifications as HUMAN_REVIEW.
    """
    service = InvoiceExtractionService(db=db, storage=storage)
    try:
        draft = service.update_draft(
            tenant_id=current_user.tenant_id,
            draft_id=draft_id,
            updates=payload.model_dump(),
            user=current_user,
        )
        return InvoiceDraftResponse(
            draft_id=draft.id,
            tenant_id=draft.tenant_id,
            document_id=draft.document_id,
            status=draft.status,
            overall_confidence=float(draft.overall_confidence) if draft.overall_confidence is not None else None,
            field_confidences=draft.field_confidences or {},
            warnings=draft.warnings or [],
            vendor_match=draft.vendor_match,
            extracted_data=draft.extracted_data or {},
            confirmed_invoice_id=draft.confirmed_invoice_id,
            reviewed_by=draft.reviewed_by,
            reviewed_at=draft.reviewed_at,
            created_at=draft.created_at,
            updated_at=draft.updated_at,
        )
    except PermanentExtractionError as pe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=pe.message,
        )


@router.post(
    "/drafts/{draft_id}/confirm",
    response_model=ConfirmDraftResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(["AP_CLERK", "ADMIN", "FINANCE_MANAGER"]))],
)
def confirm_invoice_draft(
    draft_id: UUID,
    db: Session = Depends(get_db),
    storage: DocumentStorage = Depends(get_storage),
    current_user: User = Depends(get_current_user),
):
    """
    Human confirmation of an Invoice Draft:
    1. Converts Draft to real ap.invoices, ap.invoice_revisions, ap.invoice_items.
    2. Commits transaction.
    3. Runs 18 validation controls via Control Engine.
    """
    service = InvoiceExtractionService(db=db, storage=storage)
    try:
        return service.confirm_draft(
            tenant_id=current_user.tenant_id,
            draft_id=draft_id,
            user=current_user,
        )
    except PermanentExtractionError as pe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=pe.message,
        )
    except Exception as e:
        logger.error(f"event=draft_confirmation_failed draft_id={draft_id} error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm invoice draft: {str(e)}",
        )


# =========================================================================
# Single Invoice Parameterized Endpoints (/{invoice_id})
# Placed after specific static sub-routes (/intake, /documents, /drafts)
# to prevent parameter shadow collisions.
# =========================================================================

@router.get("/{invoice_id}", response_model=InvoiceDetailOut)
def get_invoice_detail(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full aggregate details of a specific invoice including revisions and items."""
    stmt = (
        select(Invoice)
        .where(Invoice.tenant_id == current_user.tenant_id, Invoice.id == invoice_id)
        .options(
            selectinload(Invoice.vendor),
            selectinload(Invoice.revisions).selectinload(InvoiceRevision.items),
        )
    )
    inv = db.execute(stmt).scalars().first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")

    summary = _to_summary_out(inv)

    # Active exceptions and risk signals counts
    active_exc = db.query(APException).filter(
        APException.tenant_id == current_user.tenant_id,
        APException.invoice_id == invoice_id,
        APException.status.in_([ExceptionStatus.OPEN.value, ExceptionStatus.IN_REVIEW.value])
    ).count()

    active_risk = db.query(RiskSignal).filter(
        RiskSignal.tenant_id == current_user.tenant_id,
        RiskSignal.invoice_id == invoice_id,
        RiskSignal.status == RiskSignalStatus.ACTIVE.value
    ).count()

    latest_run = db.query(ControlRun).filter(
        ControlRun.tenant_id == current_user.tenant_id,
        ControlRun.invoice_id == invoice_id
    ).order_by(desc(ControlRun.run_number)).first()

    rev_outs = []
    curr_rev_out = None
    for r in inv.revisions:
        item_outs = [InvoiceItemOut.model_validate(item) for item in r.items]
        r_out = InvoiceRevisionOut(
            id=r.id,
            revision_number=r.revision_number,
            invoice_number=r.invoice_number,
            invoice_date=r.invoice_date,
            due_date=r.due_date,
            currency=r.currency,
            subtotal=r.subtotal,
            discount_total=r.discount_total,
            tax_total=r.tax_total,
            grand_total=r.grand_total,
            vendor_name_as_submitted=r.vendor_name_as_submitted,
            vendor_tax_id_as_submitted=r.vendor_tax_id_as_submitted,
            bank_account_last4=r.bank_account_last4,
            extraction_method=r.extraction_method,
            extraction_confidence=r.extraction_confidence,
            submitted_at=r.submitted_at,
            items=item_outs
        )
        rev_outs.append(r_out)
        if r.id == inv.current_revision_id:
            curr_rev_out = r_out

    if not curr_rev_out and rev_outs:
        curr_rev_out = rev_outs[-1]

    return InvoiceDetailOut(
        **summary.model_dump(),
        current_revision=curr_rev_out,
        revisions=rev_outs,
        active_exceptions_count=active_exc,
        active_risk_signals_count=active_risk,
        latest_control_run_status=latest_run.status if latest_run else None,
    )

@router.post("/{invoice_id}/control-runs", response_model=ControlRunSummaryOut)
def trigger_control_run(
    invoice_id: UUID,
    payload: TriggerControlRunRequest = TriggerControlRunRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "AP_CLERK", "FINANCE_MANAGER")),
):
    """
    Trigger execution of the deterministic Control Engine on an invoice revision.
    Evaluates all 18 rules, records results, generates exceptions/signals, and updates invoice state.
    """
    run_service = ControlRunService(db)
    try:
        run, summary, decision = run_service.execute_control_run(
            tenant_id=current_user.tenant_id,
            invoice_id=invoice_id,
            revision_id=payload.revision_id,
            triggered_by=current_user.id,
            ruleset_version=payload.ruleset_version
        )
        db.commit()
        return ControlRunSummaryOut(
            run_id=summary.run_id,
            invoice_id=summary.invoice_id,
            revision_id=summary.revision_id,
            run_number=summary.run_number,
            status=summary.status,
            total_controls=summary.total_controls,
            passed_count=summary.passed_count,
            failed_count=summary.failed_count,
            warning_count=summary.warning_count,
            error_count=summary.error_count,
            not_applicable_count=summary.not_applicable_count,
            duration_ms=summary.duration_ms,
            correlation_id=summary.correlation_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{invoice_id}/control-results", response_model=list[ControlResultOut])
def get_invoice_control_results(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch all evaluation results from the latest control run for an invoice."""
    latest_run = (
        db.query(ControlRun)
        .filter(ControlRun.tenant_id == current_user.tenant_id, ControlRun.invoice_id == invoice_id)
        .order_by(desc(ControlRun.run_number))
        .first()
    )
    if not latest_run:
        return []

    results = (
        db.query(ControlResult)
        .filter(ControlResult.control_run_id == latest_run.id)
        .order_by(ControlResult.created_at)
        .all()
    )
    return [ControlResultOut.model_validate(r) for r in results]


@router.get("/{invoice_id}/explanation", response_model=InvoiceExplanationOut)
def get_invoice_explanation(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate deterministic, finance-friendly explanation of why an invoice can or cannot be paid.
    Explains existing decisions and controls without altering financial state.
    """
    service = ControlExplanationService(db)
    try:
        data = service.explain_invoice_payability(
            tenant_id=current_user.tenant_id,
            invoice_id=invoice_id,
        )
        return InvoiceExplanationOut(**data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{invoice_id}/control-graph", response_model=ControlGraphOut)
def get_invoice_control_graph(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the visual multi-stage Control Graph for an invoice built from actual control results.
    """
    service = ControlExplanationService(db)
    try:
        data = service.get_control_graph(
            tenant_id=current_user.tenant_id,
            invoice_id=invoice_id,
        )
        return ControlGraphOut(**data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{invoice_id}/audit-replay", response_model=AuditReplayOut)
def get_invoice_audit_replay(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the chronological timeline of actual events from the append-only audit trail.
    """
    service = ControlExplanationService(db)
    try:
        data = service.get_audit_replay(
            tenant_id=current_user.tenant_id,
            invoice_id=invoice_id,
        )
        return AuditReplayOut(**data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{invoice_id}/revisions/diff", response_model=RevisionDiffOut)
def get_invoice_revisions_diff(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve structured field and line-item comparison between persisted invoice revisions ("What Changed?").
    """
    service = ControlExplanationService(db)
    try:
        data = service.get_revision_diff(
            tenant_id=current_user.tenant_id,
            invoice_id=invoice_id,
        )
        return RevisionDiffOut(**data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{invoice_id}/risk-profile", response_model=InvoiceRiskProfileOut)
def get_invoice_risk_profile(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the deterministic multi-factor risk profile and score (0–100) for an invoice.
    Aggregates control evaluations, active exceptions, and risk signals into categorized risk factors.
    """
    service = RiskIntelligenceService(db)
    try:
        return service.get_invoice_risk_profile(
            tenant_id=current_user.tenant_id,
            invoice_id=invoice_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))




