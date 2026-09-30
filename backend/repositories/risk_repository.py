import uuid
from decimal import Decimal
from typing import Optional, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.database.models.ap import RiskSignal
from backend.database.enums import RiskSignalStatus

class RiskRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_invoice(self, tenant_id: UUID, invoice_id: UUID) -> list[RiskSignal]:
        """Fetch all risk signals for an invoice."""
        stmt = (
            select(RiskSignal)
            .where(RiskSignal.tenant_id == tenant_id, RiskSignal.invoice_id == invoice_id)
            .order_by(RiskSignal.created_at)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_active_by_invoice_and_code(
        self,
        tenant_id: UUID,
        invoice_id: UUID,
        signal_code: str
    ) -> Optional[RiskSignal]:
        """Find an active risk signal with the given code."""
        stmt = (
            select(RiskSignal)
            .where(
                RiskSignal.tenant_id == tenant_id,
                RiskSignal.invoice_id == invoice_id,
                RiskSignal.signal_code == signal_code,
                RiskSignal.status == RiskSignalStatus.ACTIVE.value
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def create_or_update_signal(
        self,
        tenant_id: UUID,
        invoice_id: UUID,
        control_result_id: Optional[UUID],
        signal_code: str,
        category: str,
        severity: str,
        description: str,
        evidence: Optional[dict[str, Any]] = None,
        score: Optional[Decimal] = None,
        confidence: Optional[Decimal] = None
    ) -> RiskSignal:
        """
        Idempotent creation:
        If an active signal for this code already exists, update its control_result_id and evidence.
        """
        existing = self.get_active_by_invoice_and_code(tenant_id, invoice_id, signal_code)
        if existing:
            existing.control_result_id = control_result_id
            existing.description = description
            existing.evidence = evidence
            existing.severity = severity
            if score is not None:
                existing.score = score
            if confidence is not None:
                existing.confidence = confidence
            self.session.flush()
            return existing

        sig = RiskSignal(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            control_result_id=control_result_id,
            signal_code=signal_code,
            category=category,
            severity=severity,
            description=description,
            evidence=evidence,
            score=score,
            confidence=confidence,
            status=RiskSignalStatus.ACTIVE.value
        )
        self.session.add(sig)
        self.session.flush()
        return sig
