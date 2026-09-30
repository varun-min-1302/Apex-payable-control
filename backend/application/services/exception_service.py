from typing import Optional
from uuid import UUID
from backend.repositories.exception_repository import ExceptionRepository
from backend.application.dto.decision_dto import PendingException
from backend.database.models.ap import Exception as APException

class ExceptionService:
    def __init__(self, exception_repo: ExceptionRepository):
        self.exception_repo = exception_repo

    def process_pending_exceptions(
        self,
        tenant_id: UUID,
        invoice_id: UUID,
        control_result_map: dict[str, UUID],
        pending_exceptions: list[PendingException]
    ) -> list[APException]:
        """
        Persist pending exceptions idempotently, linking each exception to its control_result_id.
        """
        persisted = []
        for exc in pending_exceptions:
            ctrl_res_id = control_result_map.get(exc.control_code)
            record = self.exception_repo.create_or_update_exception(
                tenant_id=tenant_id,
                invoice_id=invoice_id,
                control_result_id=ctrl_res_id,
                exception_code=exc.exception_code,
                title=exc.title,
                description=exc.description,
                severity=exc.severity
            )
            persisted.append(record)
        return persisted
