from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class DashboardKPIsOut(BaseModel):
    total_invoices: int
    awaiting_approval: int
    open_exceptions: int
    payable_created: int
    paid_invoices: int
    rejected_invoices: int
    active_risk_signals: int
    total_payable_liability: Decimal
    total_disbursed_amount: Decimal
    three_way_match_pass_rate_percentage: Decimal

class ScenarioItemOut(BaseModel):
    scenario_code: str
    scenario_name: str
    invoice_number: str
    invoice_id: UUID
    vendor_name: str
    grand_total: Decimal
    current_status: str
    expected_outcome: str
    summary: str
    has_exceptions: bool
    has_risk_signals: bool

class DashboardScenariosOut(BaseModel):
    scenarios: list[ScenarioItemOut]
