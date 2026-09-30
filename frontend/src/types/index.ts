export type RoleCode = 
  | 'ADMIN' 
  | 'AP_CLERK' 
  | 'PROCUREMENT_MANAGER' 
  | 'RECEIVING_USER' 
  | 'FINANCE_MANAGER' 
  | 'FINANCE_HEAD' 
  | 'AUDITOR';


export interface DemoUser {

  id: string;

  email: string;

  full_name: string;

  roles: RoleCode[];


}

export interface DashboardKPIs {

  total_invoices: number;

  awaiting_approval: number;

  open_exceptions: number;

  payable_created: number;

  paid_invoices: number;

  rejected_invoices: number;

  active_risk_signals: number;

  total_payable_liability: string | number;

  total_disbursed_amount: string | number;

  three_way_match_pass_rate_percentage: string | number;


}

export interface ScenarioItem {

  scenario_code: string;

  scenario_name: string;

  invoice_number: string;

  invoice_id: string;

  vendor_name: string;

  grand_total: string | number;

  current_status: string;

  expected_outcome: string;

  summary: string;

  has_exceptions: boolean;

  has_risk_signals: boolean;


}

export interface InvoiceSummary {

  id: string;

  tenant_id: string;

  vendor_id: string;

  purchase_order_id: string | null;

  po_number?: string | null;

  invoice_number: string;

  invoice_date: string;

  due_date: string;

  currency: string;

  status: string;

  source_type: string;

  document_hash: string | null;

  extraction_status: string;

  extraction_confidence: string | number | null;

  current_revision_id: string | null;

  grand_total: string | number;

  vendor_name: string | null;

  risk_level?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | null;

  risk_score?: number | null;

  created_at: string;


}

export interface InvoiceItem {

  id: string;

  line_number: number;

  product_code: string | null;

  description: string;

  quantity: string | number;

  unit_of_measure: string;

  unit_price: string | number;

  discount_amount: string | number;

  tax_rate: string | number;

  tax_amount: string | number;

  line_total: string | number;


}

export interface InvoiceRevision {

  id: string;

  revision_number: number;

  invoice_number: string;

  invoice_date: string;

  due_date: string;

  subtotal: string | number;

  discount_total: string | number;

  tax_total: string | number;

  grand_total: string | number;

  notes: string | null;

  items: InvoiceItem[];


}

export interface InvoiceDetail extends InvoiceSummary {

  vendor_code: string | null;

  vendor_tax_id: string | null;

  bank_account_last4: string | null;

  bank_name: string | null;

  ifsc: string | null;

  po_number: string | null;

  revisions: InvoiceRevision[];

  active_exceptions_count: number;

  active_risk_signals_count: number;


}

export interface ControlResult {

  id: string;

  control_code: string;

  category: string;

  status: 'PASS' | 'FAIL' | 'WARNING' | 'NOT_APPLICABLE' | 'ERROR';

  severity: 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

  expected_value: any;

  actual_value: any;

  variance_value: string | number | null;

  variance_percentage: string | number | null;

  message: string | null;

  evidence: any;

  rule_version: string;


}

export interface ControlRunSummary {

  run_id: string;

  invoice_id: string;

  revision_id: string;

  run_number: number;

  status: string;

  total_controls: number;

  passed_count: number;

  failed_count: number;

  warning_count: number;

  error_count: number;

  not_applicable_count: number;

  duration_ms: number;

  correlation_id: string;


}

export interface APException {

  id: string;

  tenant_id: string;

  invoice_id: string;

  control_result_id: string | null;

  exception_code: string;

  title: string;

  description: string;

  severity: string;

  status: 'OPEN' | 'IN_REVIEW' | 'RESOLVED' | 'REJECTED' | 'CANCELLED';

  assigned_to: string | null;

  assigned_to_name: string | null;

  invoice_number: string | null;

  vendor_name: string | null;

  resolution_reason: string | null;

  created_at: string;

  resolved_at: string | null;


}

export interface Approval {

  id: string;

  tenant_id: string;

  invoice_id: string;

  approval_policy_id: string;

  sequence_order: number;

  approver_user_id: string | null;

  approver_name: string | null;

  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'SKIPPED' | 'CANCELLED';

  decision: string | null;

  comments: string | null;

  decided_at: string | null;

  policy_name: string | null;

  policy_tier: number | null;

  required_role: string | null;

  invoice_number: string | null;

  vendor_name: string | null;

  invoice_amount: string | number | null;

  currency: string | null;

  created_at: string;


}

export interface Payment {

  id: string;

  payable_id: string;

  payment_reference: string;

  payment_method: string;

  amount: string | number;

  currency: string;

  payment_date: string;

  status: string;

  created_at: string;


}

export interface PayableLedger {

  id: string;

  tenant_id: string;

  invoice_id: string;

  invoice_number: string | null;

  vendor_name: string | null;

  payable_number: string;

  currency: string;

  approved_amount: string | number;

  paid_amount: string | number;

  remaining_balance: string | number;

  due_date: string;

  status: 'OPEN' | 'PARTIALLY_PAID' | 'PAID' | 'ON_HOLD' | 'CANCELLED';

  approved_at: string | null;

  created_at: string;

  payments: Payment[];


}

export interface Vendor {

  id: string;

  tenant_id: string;

  vendor_code: string;

  legal_name: string;

  display_name: string | null;

  tax_identifier: string;

  currency: string;

  payment_terms_days: number;

  status: string;

  risk_status: string;

  bank_account_last4: string | null;

  bank_name: string | null;

  ifsc: string | null;

  created_at: string;


}

export interface PurchaseOrderItem {

  id: string;

  line_number: number;

  product_code: string | null;

  description: string;

  quantity: string | number;

  unit_of_measure: string;

  unit_price: string | number;

  discount_amount: string | number;

  tax_rate: string | number;

  tax_amount: string | number;

  line_total: string | number;


}

export interface PurchaseOrder {

  id: string;

  tenant_id: string;

  vendor_id: string;

  po_number: string;

  po_date: string;

  status: string;

  currency: string;

  subtotal: string | number;

  discount_total: string | number;

  tax_total: string | number;

  grand_total: string | number;

  payment_terms_days: number;

  approved_at: string | null;

  items: PurchaseOrderItem[];


}

export interface GoodsReceiptItem {

  id: string;

  purchase_order_item_id: string;

  received_quantity: string | number;

  accepted_quantity: string | number;

  rejected_quantity: string | number;

  notes: string | null;


}

export interface GoodsReceipt {

  id: string;

  tenant_id: string;

  purchase_order_id: string;

  receipt_number: string;

  received_date: string;

  status: string;

  notes: string | null;

  items: GoodsReceiptItem[];


}

export interface AuditLog {

  id: string;

  tenant_id: string;

  action: string;

  entity_type: string;

  entity_id: string;

  actor_user_id: string | null;

  actor_name: string | null;

  correlation_id: string | null;

  previous_state: any;

  new_state: any;

  metadata_info: any;

  created_at: string;


}

export interface InvoiceIntakeResponse {

  document_id: string;

  tenant_id: string;

  filename: string;

  size_bytes: number;

  mime_type: string;

  status: string;

  duplicate: boolean;

  existing_document_id?: string | null;

  invoice_id?: string | null;

  created_at: string;

  message?: string | null;


}

export interface InvoiceDocument {

  id: string;

  tenant_id: string;

  invoice_id: string | null;

  original_filename: string;

  sanitized_filename: string;

  mime_type: string;

  file_size_bytes: number;

  status: string;

  source: string;

  uploaded_by: string | null;

  created_at: string;


}

export interface ExtractedField<T = any> {

  value: T;

  confidence: number;

  evidence_snippet?: string | null;

  bounding_box?: any | null;

  source?: 'AI' | 'HUMAN_REVIEW' | 'FALLBACK';

  original_value?: T | null;


}

export interface ExtractedLineItem {

  line_number: number;

  description: string;

  quantity: number;

  unit_price: number;

  tax_rate: number;

  line_total: number;

  confidence: number;

  evidence_snippet?: string | null;


}

export interface VendorMatchInfo {

  matched: boolean;

  vendor_id?: string | null;

  vendor_name?: string | null;

  vendor_code?: string | null;

  tax_identifier?: string | null;

  match_method?: string | null;

  similarity_score?: number | null;


}

export interface InvoiceDraft {

  draft_id: string;

  tenant_id: string;

  document_id: string;

  status: 'PENDING_REVIEW' | 'IN_REVIEW' | 'CONFIRMED' | 'REJECTED' | 'FAILED' | 'EXTRACTED';

  overall_confidence: number | null;

  field_confidences: Record<string, number>;

  warnings: string[];

  vendor_match?: VendorMatchInfo | null;

  extracted_data: {

    invoice_number?: ExtractedField<string>;

    invoice_date?: ExtractedField<string>;

    due_date?: ExtractedField<string>;

    vendor_name?: ExtractedField<string>;

    vendor_tax_id?: ExtractedField<string>;

    vendor_address?: ExtractedField<string>;

    customer_name?: ExtractedField<string>;

    purchase_order_number?: ExtractedField<string>;

    currency?: ExtractedField<string>;

    subtotal?: ExtractedField<number>;

    tax_total?: ExtractedField<number>;

    grand_total?: ExtractedField<number>;

    payment_terms?: ExtractedField<string>;

    bank_account_number?: ExtractedField<string>;

    bank_ifsc_or_routing?: ExtractedField<string>;

    line_items?: ExtractedField<ExtractedLineItem[]>;

    [key: string]: any;

  
};

  confirmed_invoice_id?: string | null;

  reviewed_by?: string | null;

  reviewed_at?: string | null;

  created_at: string;

  updated_at: string;


}

export interface ConfirmDraftResponse {

  draft_id: string;

  invoice_id: string;

  invoice_number: string;

  status: string;

  control_run_id?: string | null;

  control_run_status?: string | null;

  passed_controls: number;

  failed_controls: number;

  warning_controls: number;

  exception_count: number;

  risk_signal_count: number;

  message: string;


}

// -----------------------------------------------------------------------------
// Phase 6: Control Intelligence & Explainability
// -----------------------------------------------------------------------------

export interface BlockingReason {

  control_code: string;

  title: string;

  what_happened: string;

  why_it_matters: string;

  recommended_action: string;

  severity: string;

  expected: string;

  actual: string;

  variance: string;

  technical_rule: string;


}

export interface InvoiceExplanation {

  invoice_id: string;

  invoice_number: string;

  status: string;

  headline: string;

  summary: string;

  blocking_reasons: BlockingReason[];

  passed_checks: number;

  total_checks?: number;

  next_action: string;

  can_be_paid: boolean;


}

export interface ControlGraphCheck {

  control_code: string;

  title: string;

  status: string;

  severity: string;

  message?: string | null;

  expected?: string | null;

  actual?: string | null;

  variance?: string | null;

  why_it_matters?: string | null;

  recommended_action?: string | null;

  evaluated_at?: string | null;


}

export interface ControlGraphNode {

  id: string;

  label: string;

  category: string;

  order: number;

  status: string;

  total_checks: number;

  passed_count: number;

  failed_count: number;

  warning_count: number;

  summary: string;

  checks: ControlGraphCheck[];


}

export interface ControlGraph {

  invoice_id: string;

  invoice_number: string;

  current_status: string;

  nodes: ControlGraphNode[];


}

export interface AuditReplayEvent {

  id: string;

  timestamp: string;

  actor_name: string;

  actor_email?: string | null;

  actor_role: string;

  action: string;

  title: string;

  description: string;

  category: string;

  entity_type: string;

  entity_id: string;

  previous_state?: Record<string, any> | null;

  new_state?: Record<string, any> | null;

  metadata: Record<string, any>;

  technical_details: Record<string, any>;


}

export interface AuditReplay {

  invoice_id: string;

  invoice_number: string;

  events_count: number;

  timeline: AuditReplayEvent[];


}

export interface HeaderDiffItem {

  field: string;

  label: string;

  previous_value: string;

  new_value: string;


}

export interface LineItemDiff {

  line_number: number;

  change_type: string;

  description: string;

  changes?: string[] | null;

  previous: string;

  current: string;


}

export interface RevisionComparison {

  from_revision_number: number;

  to_revision_number: number;

  changed_by: string;

  changed_by_email?: string | null;

  changed_at: string;

  header_diffs: HeaderDiffItem[];

  item_diffs: LineItemDiff[];

  controls_rerun: boolean;

  resulting_control_status: string;


}

export interface RevisionDiffResponse {

  invoice_id: string;

  invoice_number: string;

  has_multiple_revisions: boolean;

  revisions_count: number;

  diffs: RevisionComparison[];


}

export interface ControlCategoryHealth {

  category: string;

  name: string;

  total_checks: number;

  passed_count: number;

  failed_count: number;

  warning_count: number;

  pass_rate_percentage: number;


}

export interface StatusBreakdown {

  received: number;

  processing: number;

  needs_attention: number;

  waiting_for_approval: number;

  approved: number;

  payable: number;

  paid: number;

  rejected: number;


}

export interface TopRecurringIssue {

  control_code: string;

  title: string;

  failure_count: number;

  why_it_matters: string;


}

export interface DashboardControlHealth {

  overall_pass_rate_percentage: number;

  total_checks_evaluated: number;

  categories: ControlCategoryHealth[];

  status_breakdown: StatusBreakdown;

  top_recurring_issues: TopRecurringIssue[];


}

// -----------------------------------------------------------------------------
// Phase 7: Risk Intelligence & Scenario Simulator
// -----------------------------------------------------------------------------

export interface RiskFactor {

  code: string;

  title: string;

  severity: string;

  category: string;

  description: string;

  evidence: string;

  source: string;

  why_it_matters: string;

  recommended_action: string;

  score_contribution: number;


}

export interface ControlSummary {

  passed: number;

  failed: number;

  warnings: number;

  not_applicable: number;


}

export interface InvoiceRiskProfile {

  invoice_id: string;

  invoice_number: string;

  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

  risk_score: number;

  risk_factors: RiskFactor[];

  control_summary: ControlSummary;

  recommended_attention: boolean;

  headline: string;

  summary: string;


}

export interface TopRiskDriver {

  driver_code: string;

  title: string;

  category: string;

  invoice_count: number;

  percentage: number;

  description: string;


}

export interface HighestRiskInvoice {

  invoice_id: string;

  invoice_number: string;

  vendor_name: string;

  grand_total: string | number;

  risk_score: number;

  risk_level: string;

  primary_factor: string;


}

export interface DashboardRiskOverview {

  critical_count: number;

  high_count: number;

  medium_count: number;

  low_count: number;

  total_evaluated: number;

  average_risk_score: number;

  top_risk_drivers: TopRiskDriver[];

  highest_risk_invoices: HighestRiskInvoice[];


}

export interface ScenarioSummary {

  scenario_id: string;

  scenario_code: string;

  scenario_name: string;

  invoice_number: string;

  invoice_id?: string | null;

  expected_outcome: string;

  primary_control: string;

  risk_category: string;

  summary: string;

  description: string;


}

export interface ScenarioSimulationInput {

  invoice: Record<string, any>;

  purchase_order?: Record<string, any> | null;

  vendor?: Record<string, any> | null;

  goods_receipts: Record<string, any>[];


}

export interface ScenarioControlCheck {

  control_code: string;

  title: string;

  status: string;

  severity: string;

  variance?: string | null;

  message?: string | null;


}

export interface ScenarioSimulationResponse {

  scenario_id: string;

  scenario_code: string;

  scenario_name: string;

  inputs: ScenarioSimulationInput;

  control_checks: ScenarioControlCheck[];

  risk_profile: InvoiceRiskProfile;

  decision: string;

  next_action: string;


}

export interface WhatIfRequest {

  quantity?: number | string | null;

  unit_price?: number | string | null;

  tax_rate?: number | string | null;

  match_vendor?: boolean | null;

  has_po?: boolean | null;

  po_approved?: boolean | null;

  receipt_quantity?: number | string | null;

  is_duplicate?: boolean | null;

  bank_details_match?: boolean | null;


}

export interface ControlImpactItem {

  control_code: string;

  title: string;

  before_status: string;

  after_status: string;

  severity: string;

  message?: string | null;


}

export interface SimulationDiff {

  changed_inputs: Record<string, any>[];

  affected_controls: ControlImpactItem[];

  before_risk_score: number;

  after_risk_score: number;

  before_risk_level: string;

  after_risk_level: string;

  before_decision: string;

  after_decision: string;

  outcome_changed: boolean;

  risk_reduced: boolean;


}

export interface ControlImpactMapNode {

  changed_input: string;

  affected_controls: string[];

  risk_category: string;

  final_outcome: string;


}

export interface WhatIfSimulationResponse {

  scenario_id: string;

  scenario_code: string;

  original_simulation: ScenarioSimulationResponse;

  simulated_output: ScenarioSimulationResponse;

  diff: SimulationDiff;

  impact_map: ControlImpactMapNode[];


}

export interface DemoStep {

  step_number: number;

  step_code: string;

  title: string;

  description: string;

  action_taken: string;

  result_status: string;

  key_metric: string;

  invoice_number: string;


}

