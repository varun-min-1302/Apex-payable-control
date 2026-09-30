import uuid
from datetime import datetime, timezone
from typing import Optional, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.database.models.ap import Exception as APException
from backend.database.enums import ExceptionStatus

class ExceptionRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_invoice(self, tenant_id: UUID, invoice_id: UUID) -> list[APException]:
        """Fetch all exceptions for an invoice."""
        stmt = (
            select(APException)
            .where(APException.tenant_id == tenant_id, APException.invoice_id == invoice_id)
            .order_by(APException.created_at)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_open_by_invoice_and_code(
        self,
        tenant_id: UUID,
        invoice_id: UUID,
        exception_code: str
    ) -> Optional[APException]:
        """Find an existing open or in-review exception with the given code."""
        stmt = (
            select(APException)
            .where(
                APException.tenant_id == tenant_id,
                APException.invoice_id == invoice_id,
                APException.exception_code == exception_code,
                APException.status.in_([ExceptionStatus.OPEN.value, ExceptionStatus.IN_REVIEW.value])
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def create_or_update_exception(
        self,
        tenant_id: UUID,
        invoice_id: UUID,
        control_result_id: Optional[UUID],
        exception_code: str,
        title: str,
        description: str,
        severity: str
    ) -> APException:
        """
        Idempotent creation:
        If an open exception for this code already exists on the invoice, update its control_result_id
        and description instead of creating a duplicate.
        """
        existing = self.get_open_by_invoice_and_code(tenant_id, invoice_id, exception_code)
        if existing:
            existing.control_result_id = control_result_id
            existing.title = title
            existing.description = description
            existing.severity = severity
            existing.updated_at = datetime.now(timezone.utc)
            self.session.flush()
            return existing

        exc = APException(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            control_result_id=control_result_id,
            exception_code=exception_code,
            title=title,
            description=description,
            severity=severity,
            status=ExceptionStatus.OPEN.value
        )
        self.session.add(exc)
        self.session.flush()
        return exc
