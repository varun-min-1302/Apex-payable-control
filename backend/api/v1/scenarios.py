"""FastAPI router for AP Control Scenario Simulator and Finathon Testing Matrix."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.deps import get_db, get_current_user
from backend.database.models.identity import User
from backend.application.services.scenario_simulator_service import ScenarioSimulatorService
from backend.api.schemas.risk_schemas import (
    ScenarioSummaryOut,
    ScenarioSimulationResponseOut,
    WhatIfRequest,
    WhatIfSimulationResponseOut,
    DemoStepOut,
)

router = APIRouter(prefix="/scenarios", tags=["Scenario Simulator & Stress Testing"])


@router.get("", response_model=List[ScenarioSummaryOut])
def list_scenarios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all predefined AP control test scenarios (Scenarios A through O).
    Includes expected outcome, primary control, and matched invoice metadata.
    """
    service = ScenarioSimulatorService(db)
    return service.list_scenarios(tenant_id=current_user.tenant_id)


@router.get("/{scenario_id}", response_model=ScenarioSummaryOut)
def get_scenario_detail(
    scenario_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve metadata and configuration for a specific scenario."""
    service = ScenarioSimulatorService(db)
    return service.get_scenario_detail(tenant_id=current_user.tenant_id, scenario_id=scenario_id)


@router.post("/{scenario_id}/simulate", response_model=ScenarioSimulationResponseOut)
def simulate_scenario(
    scenario_id: str,
    overrides: Optional[WhatIfRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Simulate scenario execution in-memory with complete 18-rule control pipeline.
    Zero-mutation: strictly read-only execution with NO database writes to invoices, payables, or audit logs.
    """
    service = ScenarioSimulatorService(db)
    try:
        return service.simulate_scenario(
            tenant_id=current_user.tenant_id,
            scenario_id=scenario_id,
            overrides=overrides,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{scenario_id}/what-if", response_model=WhatIfSimulationResponseOut)
def simulate_what_if(
    scenario_id: str,
    request: WhatIfRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Interactive 'What-If?' sandbox simulation.
    Takes parameter adjustments (quantity, price, tax rate, receipt qty) and evaluates
    before vs. after outcomes, delta score, and control impact map in memory.
    """
    service = ScenarioSimulatorService(db)
    try:
        return service.simulate_what_if(
            tenant_id=current_user.tenant_id,
            scenario_id=scenario_id,
            request=request,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{scenario_id}/demo-steps", response_model=List[DemoStepOut])
def get_scenario_demo_steps(
    scenario_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve structured step-by-step presentation narrative for hackathon/executive demo.
    """
    service = ScenarioSimulatorService(db)
    return service.get_demo_steps(tenant_id=current_user.tenant_id, scenario_id=scenario_id)
