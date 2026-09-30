from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, desc, or_
from backend.database.models.ap import Invoice, InvoiceRevision, InvoiceItem
from backend.database.enums import InvoiceStatus

class InvoiceRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, tenant_id: UUID, invoice_id: UUID) -> Optional[Invoice]:
        """Fetch invoice with its revisions and items eager loaded to avoid N+1 queries."""
        stmt = (
            select(Invoice)
            .where(Invoice.tenant_id == tenant_id, Invoice.id == invoice_id)
            .options(
                selectinload(Invoice.revisions).selectinload(InvoiceRevision.items)
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_revision_by_id(self, tenant_id: UUID, revision_id: UUID) -> Optional[InvoiceRevision]:
        """Fetch invoice revision with items loaded."""
        stmt = (
            select(InvoiceRevision)
            .where(InvoiceRevision.tenant_id == tenant_id, InvoiceRevision.id == revision_id)
            .options(selectinload(InvoiceRevision.items))
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_latest_revision(self, tenant_id: UUID, invoice_id: UUID) -> Optional[InvoiceRevision]:
        """Get the latest revision for an invoice by revision_number."""
        stmt = (
            select(InvoiceRevision)
            .where(InvoiceRevision.tenant_id == tenant_id, InvoiceRevision.invoice_id == invoice_id)
            .options(selectinload(InvoiceRevision.items))
            .order_by(desc(InvoiceRevision.revision_number))
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_current_or_latest_revision(self, invoice: Invoice) -> Optional[InvoiceRevision]:
        """Resolve current revision for an invoice, falling back to highest revision number."""
        if not invoice.revisions:
            return None
        if invoice.current_revision_id:
            for r in invoice.revisions:
                if r.id == invoice.current_revision_id:
                    return r
        return max(invoice.revisions, key=lambda r: r.revision_number)

    def update_invoice_status(self, tenant_id: UUID, invoice_id: UUID, status: InvoiceStatus) -> bool:
        """Update the lifecycle status of an invoice."""
        inv = self.get_by_id(tenant_id, invoice_id)
        if inv:
            inv.status = status.value if hasattr(status, "value") else str(status)
            self.session.flush()
            return True
        return False

    def find_exact_duplicates(
        self,
        tenant_id: UUID,
        vendor_id: UUID,
        invoice_number: str,
        document_hash: Optional[str] = None,
        exclude_invoice_id: Optional[UUID] = None,
        created_before: Optional[datetime] = None
    ) -> list[Invoice]:
        """
        Check for exact duplicate indicators:
        1. Same tenant + same vendor + same invoice_number (excluding current)
        2. Same tenant + same document_hash (excluding current)
        """
        conditions = [Invoice.tenant_id == tenant_id]
        if exclude_invoice_id:
            conditions.append(Invoice.id != exclude_invoice_id)
        if created_before:
            conditions.append(
                or_(
                    Invoice.created_at < created_before,
                    (Invoice.created_at == created_before) & (Invoice.invoice_number < invoice_number)
                )
            )

        dup_or = []
        # Case 1: Same vendor + same invoice number
        dup_or.append(
            (Invoice.vendor_id == vendor_id) &
            (func.lower(Invoice.invoice_number) == invoice_number.strip().lower())
        )

        # Case 2: Exact document hash match
        if document_hash and document_hash.strip():
            dup_or.append(Invoice.document_hash == document_hash.strip())

        stmt = (
            select(Invoice)
            .where(*conditions)
            .where(or_(*dup_or))
            .options(selectinload(Invoice.revisions))
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_historical_invoices_by_vendor(
        self,
        tenant_id: UUID,
        vendor_id: UUID,
        exclude_invoice_id: Optional[UUID] = None,
        created_before: Optional[datetime] = None,
        limit: int = 50
    ) -> list[Invoice]:
        """Fetch historical invoices for the vendor to compute baseline statistics."""
        stmt = (
            select(Invoice)
            .where(Invoice.tenant_id == tenant_id, Invoice.vendor_id == vendor_id)
        )
        if exclude_invoice_id:
            stmt = stmt.where(Invoice.id != exclude_invoice_id)
        if created_before:
            stmt = stmt.where(Invoice.created_at < created_before)
        stmt = (
            stmt.options(selectinload(Invoice.revisions).selectinload(InvoiceRevision.items))
            .order_by(desc(Invoice.invoice_date))
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())
