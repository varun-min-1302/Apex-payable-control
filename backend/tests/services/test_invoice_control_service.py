import pytest
from backend.application.services.invoice_control_service import InvoiceControlService
from backend.database.models.identity import Tenant
from backend.database.models.ap import Invoice
from backend.application.dto.decision_dto import DecisionOutcome

def test_invoice_control_service_facade_methods(db_session):
    tenant = db_session.query(Tenant).filter(Tenant.slug == "apex-fintech").first()
    assert tenant is not None

    inv = db_session.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0001").first()
    assert inv is not None

    service = InvoiceControlService(db_session)

    # 1. Trigger control run
    run, summary, decision = service.trigger_control_run(tenant.id, inv.id)
    assert run is not None
    assert summary.total_controls == 18
    assert decision.outcome in (DecisionOutcome.PASS, DecisionOutcome.PASS_WITH_WARNING)

    # 2. Get latest control run
    latest = service.get_latest_control_run(tenant.id, inv.id)
    assert latest is not None
    assert latest.id == run.id

    # 3. Get control run by id
    fetched_run = service.get_control_run_by_id(tenant.id, run.id)
    assert fetched_run is not None
    assert fetched_run.id == run.id

    # 4. Get control results
    results = service.get_control_results(tenant.id, inv.id)
    assert len(results) == 18

    # 5. Get exceptions and risk signals
    exceptions = service.get_exceptions(tenant.id, inv.id)
    assert isinstance(exceptions, list)
    risk_signals = service.get_risk_signals(tenant.id, inv.id)
    assert isinstance(risk_signals, list)

    # 6. Request approval routing
    plan = service.request_approval(tenant.id, inv.id)
    assert plan is not None
    assert plan.is_eligible_for_approval is True
    assert len(plan.steps) > 0
