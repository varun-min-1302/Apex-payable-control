from typing import Optional
from uuid import UUID
from backend.repositories.risk_repository import RiskRepository
from backend.application.dto.decision_dto import PendingRiskSignal
from backend.database.models.ap import RiskSignal

class RiskService:
    def __init__(self, risk_repo: RiskRepository):
        self.risk_repo = risk_repo

    def process_pending_signals(
        self,
        tenant_id: UUID,
        invoice_id: UUID,
        control_result_map: dict[str, UUID],
        pending_signals: list[PendingRiskSignal]
    ) -> list[RiskSignal]:
        """
        Persist pending risk signals idempotently, linking them to their corresponding control_result_id.
        """
        persisted = []
        for sig in pending_signals:
            ctrl_res_id = control_result_map.get(sig.signal_code)
            record = self.risk_repo.create_or_update_signal(
                tenant_id=tenant_id,
                invoice_id=invoice_id,
                control_result_id=ctrl_res_id,
                signal_code=sig.signal_code,
                category=sig.category,
                severity=sig.severity,
                description=sig.description,
                evidence=sig.evidence,
                score=sig.score,
                confidence=sig.confidence
            )
            persisted.append(record)
        return persisted
