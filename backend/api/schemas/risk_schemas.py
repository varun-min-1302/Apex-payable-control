"""Pydantic schemas for Phase 7 Risk Intelligence and Scenario Simulator."""
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class RiskFactorOut(BaseModel):
    code: str
    title: str
    severity: str
    category: str
    description: str
    evidence: str
    source: str
    why_it_matters: str
    recommended_action: str
    score_contribution: int


class ControlSummaryOut(BaseModel):
    passed: int
    failed: int
    warnings: int
    not_applicable: int


class InvoiceRiskProfileOut(BaseModel):
    invoice_id: UUID
    invoice_number: str
    risk_level: str  # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    risk_score: int  # 0 - 100
    risk_factors: List[RiskFactorOut]
    control_summary: ControlSummaryOut
    recommended_attention: bool
    headline: str
    summary: str


class TopRiskDriverOut(BaseModel):
    driver_code: str
    title: str
    category: str
    invoice_count: int
    percentage: float
    description: str


class HighestRiskInvoiceOut(BaseModel):
    invoice_id: UUID
    invoice_number: str
    vendor_name: str
    grand_total: Decimal
    risk_score: int
    risk_level: str
    primary_factor: str


class DashboardRiskOverviewOut(BaseModel):
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    total_evaluated: int
    average_risk_score: float
    top_risk_drivers: List[TopRiskDriverOut]
    highest_risk_invoices: List[HighestRiskInvoiceOut]


class ScenarioSummaryOut(BaseModel):
    scenario_id: str
    scenario_code: str
    scenario_name: str
    invoice_number: str
    invoice_id: Optional[UUID] = None
    expected_outcome: str
    primary_control: str
    risk_category: str
    summary: str
    description: str


class ScenarioSimulationInputOut(BaseModel):
    invoice: Dict[str, Any]
    purchase_order: Optional[Dict[str, Any]] = None
    vendor: Optional[Dict[str, Any]] = None
    goods_receipts: List[Dict[str, Any]] = Field(default_factory=list)


class ScenarioControlCheckOut(BaseModel):
    control_code: str
    title: str
    status: str
    severity: str
    variance: Optional[str] = None
    message: Optional[str] = None


class ScenarioSimulationResponseOut(BaseModel):
    scenario_id: str
    scenario_code: str
    scenario_name: str
    inputs: ScenarioSimulationInputOut
    control_checks: List[ScenarioControlCheckOut]
    risk_profile: InvoiceRiskProfileOut
    decision: str
    next_action: str


class WhatIfRequest(BaseModel):
    quantity: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    match_vendor: Optional[bool] = None
    has_po: Optional[bool] = None
    po_approved: Optional[bool] = None
    receipt_quantity: Optional[Decimal] = None
    is_duplicate: Optional[bool] = None
    bank_details_match: Optional[bool] = None


class ControlImpactItemOut(BaseModel):
    control_code: str
    title: str
    before_status: str
    after_status: str
    severity: str
    message: Optional[str] = None


class SimulationDiffOut(BaseModel):
    changed_inputs: List[Dict[str, Any]]
    affected_controls: List[ControlImpactItemOut]
    before_risk_score: int
    after_risk_score: int
    before_risk_level: str
    after_risk_level: str
    before_decision: str
    after_decision: str
    outcome_changed: bool
    risk_reduced: bool


class ControlImpactMapNodeOut(BaseModel):
    changed_input: str
    affected_controls: List[str]
    risk_category: str
    final_outcome: str


class WhatIfSimulationResponseOut(BaseModel):
    scenario_id: str
    scenario_code: str
    original_simulation: ScenarioSimulationResponseOut
    simulated_output: ScenarioSimulationResponseOut
    diff: SimulationDiffOut
    impact_map: List[ControlImpactMapNodeOut]


class DemoStepOut(BaseModel):
    step_number: int
    step_code: str
    title: str
    description: str
    action_taken: str
    result_status: str
    key_metric: str
    invoice_number: str
