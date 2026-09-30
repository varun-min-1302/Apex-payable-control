import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, desc
from backend.database.models.ap import ControlRun, ControlResult
from backend.database.enums import ControlRunStatus
from backend.application.dto.control_dto import ControlEvaluation

class ControlRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_next_run_number(self, tenant_id: UUID, invoice_revision_id: UUID) -> int:
        """Get the next run number for an invoice revision."""
        stmt = (
            select(func.coalesce(func.max(ControlRun.run_number), 0))
            .where(
                ControlRun.tenant_id == tenant_id,
                ControlRun.invoice_revision_id == invoice_revision_id
            )
        )
        current_max = self.session.execute(stmt).scalar() or 0
        return current_max + 1

    def create_control_run(
        self,
        tenant_id: UUID,
        invoice_id: UUID,
        invoice_revision_id: UUID,
        run_number: int,
        triggered_by: Optional[UUID] = None,
        ruleset_version: str = "v1.0"
    ) -> ControlRun:
        """Create a new control run in RUNNING status."""
        run = ControlRun(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            invoice_revision_id=invoice_revision_id,
            run_number=run_number,
            status=ControlRunStatus.RUNNING.value,
            ruleset_version=ruleset_version,
            started_at=datetime.now(timezone.utc),
            triggered_by=triggered_by
        )
        self.session.add(run)
        self.session.flush()
        return run

    def update_control_run_status(
        self,
        tenant_id: UUID,
        run_id: UUID,
        status: ControlRunStatus,
        completed_at: Optional[datetime] = None
    ) -> Optional[ControlRun]:
        """Update control run outcome and completion time."""
        run = self.get_by_id(tenant_id, run_id)
        if run:
            run.status = status.value if hasattr(status, "value") else str(status)
            run.completed_at = completed_at or datetime.now(timezone.utc)
            self.session.flush()
        return run

    def get_by_id(self, tenant_id: UUID, run_id: UUID) -> Optional[ControlRun]:
        """Fetch control run with results eagerly loaded."""
        stmt = (
            select(ControlRun)
            .where(ControlRun.tenant_id == tenant_id, ControlRun.id == run_id)
            .options(selectinload(ControlRun.results))
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_latest_by_invoice(self, tenant_id: UUID, invoice_id: UUID) -> Optional[ControlRun]:
        """Fetch latest control run for an invoice."""
        stmt = (
            select(ControlRun)
            .where(ControlRun.tenant_id == tenant_id, ControlRun.invoice_id == invoice_id)
            .options(selectinload(ControlRun.results))
            .order_by(desc(ControlRun.started_at))
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def persist_evaluations(
        self,
        tenant_id: UUID,
        control_run_id: UUID,
        invoice_id: UUID,
        evaluations: list[ControlEvaluation]
    ) -> list[ControlResult]:
        """Persist a batch of control evaluations as ControlResult entities."""
        results = []
        now = datetime.now(timezone.utc)
        for ev in evaluations:
            res = ControlResult(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                control_run_id=control_run_id,
                invoice_id=invoice_id,
                control_code=ev.control_code,
                control_category=ev.category,
                status=ev.status.value if hasattr(ev.status, "value") else str(ev.status),
                severity=ev.severity.value if hasattr(ev.severity, "value") else str(ev.severity),
                expected_value=ev.expected_value,
                actual_value=ev.actual_value,
                variance_value=ev.variance_value,
                variance_percentage=ev.variance_percentage,
                evidence=ev.evidence,
                message=ev.message,
                rule_version=ev.rule_version,
                evaluated_at=now,
                created_at=now
            )
            self.session.add(res)
            results.append(res)

        self.session.flush()
        return results
