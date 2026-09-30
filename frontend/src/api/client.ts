import {

  DashboardKPIs,
  ScenarioItem,
  InvoiceSummary,
  InvoiceDetail,
  ControlResult,
  ControlRunSummary,
  APException,
  Approval,
  PayableLedger,
  Payment,
  Vendor,
  PurchaseOrder,
  GoodsReceipt,
  AuditLog,
  DemoUser,
  InvoiceIntakeResponse,
  InvoiceDocument,
  InvoiceDraft,
  ConfirmDraftResponse,
  InvoiceExplanation,
  ControlGraph,
  AuditReplay,
  RevisionDiffResponse,
  DashboardControlHealth,
  InvoiceRiskProfile,
  DashboardRiskOverview,
  ScenarioSummary,
  ScenarioSimulationResponse,
  WhatIfRequest,
  WhatIfSimulationResponse,
  DemoStep

} from '../types';


const BASE_URL = '/api/v1';


class ApiClient {

  private activeUserEmail: string = 'ananya.rao@apexfin.in';
 // Default to Finance Manager

  constructor() {

    const saved = localStorage.getItem('ap_demo_user_email');

    if (saved) {

      this.activeUserEmail = saved;

    
}
  
}

  getActiveUserEmail(): string {

    return this.activeUserEmail;

  
}

  setActiveUserEmail(email: string) {

    this.activeUserEmail = email;

    localStorage.setItem('ap_demo_user_email', email);

  
}

  private async request<T>(endpoint: string, options: RequestInit = {

}): Promise<T> {

    const headers = new Headers(options.headers || {

});

    headers.set('Content-Type', 'application/json');

    headers.set('X-Demo-User-Email', this.activeUserEmail);


    const response = await fetch(`${
BASE_URL
}${
endpoint
}`, {

      ...options,
      headers,
    
});


    if (!response.ok) {

      let errorMessage = `API Error ${
response.status
}: ${
response.statusText
}`;

      try {

        const errorJson = await response.json();

        if (errorJson.detail) {

          errorMessage = typeof errorJson.detail === 'string' 
            ? errorJson.detail 
            : JSON.stringify(errorJson.detail);

        
}
      
} catch {

        // Fallback to default message
      
}
      throw new Error(errorMessage);

    
}

    return response.json();

  
}

  private async requestFormData<T>(endpoint: string, formData: FormData): Promise<T> {

    const headers = new Headers();

    headers.set('X-Demo-User-Email', this.activeUserEmail);


    const response = await fetch(`${
BASE_URL
}${
endpoint
}`, {

      method: 'POST',
      headers,
      body: formData,
    
});


    if (!response.ok) {

      let errorMessage = `API Error ${
response.status
}: ${
response.statusText
}`;

      try {

        const errorJson = await response.json();

        if (errorJson.detail) {

          errorMessage = typeof errorJson.detail === 'string'
            ? errorJson.detail
            : JSON.stringify(errorJson.detail);

        
}
      
} catch {

        // Fallback
      
}
      throw new Error(errorMessage);

    
}

    return response.json();

  
}

  // Document Intake (Phase 5A)
  async uploadInvoiceDocument(file: File, source?: string): Promise<InvoiceIntakeResponse> {

    const formData = new FormData();

    formData.append('file', file);

    if (source) formData.append('source', source);

    return this.requestFormData<InvoiceIntakeResponse>('/invoices/intake', formData);

  
}

  getDocumentUrl(documentId: string): string {

    return `${
BASE_URL
}/invoices/documents/${
documentId
}`;

  
}

  async listDocuments(): Promise<InvoiceDocument[]> {

    return this.request<InvoiceDocument[]>('/invoices/documents');

  
}

  // Phase 5B: AI Extraction & Draft Lifecycle
  async extractDocument(documentId: string, forceReextract: boolean = false): Promise<InvoiceDraft> {

    return this.request<InvoiceDraft>(`/invoices/documents/${
documentId
}/extract?force_reextract=${
forceReextract
}`, {

      method: 'POST',
    
});

  
}

  async listDrafts(status?: string): Promise<InvoiceDraft[]> {

    const qs = status ? `?status=${
encodeURIComponent(status)
}` : '';

    return this.request<InvoiceDraft[]>(`/invoices/drafts${
qs
}`);

  
}

  async getDraft(draftId: string): Promise<InvoiceDraft> {

    return this.request<InvoiceDraft>(`/invoices/drafts/${
draftId
}`);

  
}

  async updateDraft(draftId: string, updates: Record<string, any>): Promise<InvoiceDraft> {

    return this.request<InvoiceDraft>(`/invoices/drafts/${
draftId
}`, {

      method: 'PUT',
      body: JSON.stringify(updates),
    
});

  
}

  async confirmDraft(draftId: string): Promise<ConfirmDraftResponse> {

    return this.request<ConfirmDraftResponse>(`/invoices/drafts/${
draftId
}/confirm`, {

      method: 'POST',
    
});

  
}

  // Auth & Personas
  async getDemoUsers(): Promise<DemoUser[]> {

    return this.request<DemoUser[]>('/auth/demo-users');

  
}

  async getMe(): Promise<any> {

    return this.request<any>('/auth/me');

  
}

  // Dashboard & Scenarios
  async getDashboardKPIs(): Promise<DashboardKPIs> {

    return this.request<DashboardKPIs>('/dashboard/kpis');

  
}

  async getScenarios(): Promise<{
 scenarios: ScenarioItem[] 
}> {

    return this.request<{
 scenarios: ScenarioItem[] 
}>('/dashboard/scenarios');

  
}

  // Invoices
  async listInvoices(params?: {
 status?: string;
 search?: string;
 limit?: number 
}): Promise<InvoiceSummary[]> {

    const query = new URLSearchParams();

    if (params?.status) query.set('status', params.status);

    if (params?.search) query.set('search', params.search);

    if (params?.limit) query.set('limit', params.limit.toString());

    const qs = query.toString() ? `?${
query.toString()
}` : '';

    const res = await this.request<any>(`/invoices${
qs
}`);

    return Array.isArray(res) ? res : (res?.invoices || []);

  
}

  async getInvoiceDetail(invoiceId: string): Promise<InvoiceDetail> {

    return this.request<InvoiceDetail>(`/invoices/${
invoiceId
}`);

  
}

  async createInvoice(payload: any): Promise<InvoiceSummary> {

    return this.request<InvoiceSummary>('/invoices', {

      method: 'POST',
      body: JSON.stringify(payload),
    
});

  
}

  async triggerControlRun(invoiceId: string, revisionId?: string): Promise<ControlRunSummary> {

    return this.request<ControlRunSummary>(`/invoices/${
invoiceId
}/control-runs`, {

      method: 'POST',
      body: JSON.stringify({
 revision_id: revisionId, ruleset_version: 'v1.0' 
}),
    
});

  
}

  async getInvoiceControlResults(invoiceId: string): Promise<ControlResult[]> {

    return this.request<ControlResult[]>(`/invoices/${
invoiceId
}/control-results`);

  
}

  // Exceptions
  async listExceptions(params?: {
 status?: string;
 severity?: string 
}): Promise<APException[]> {

    const query = new URLSearchParams();

    if (params?.status) query.set('status', params.status);

    if (params?.severity) query.set('severity', params.severity);

    const qs = query.toString() ? `?${
query.toString()
}` : '';

    return this.request<APException[]>(`/exceptions${
qs
}`);

  
}

  async resolveException(exceptionId: string, action: string, reason: string): Promise<APException> {

    return this.request<APException>(`/exceptions/${
exceptionId
}/resolve`, {

      method: 'POST',
      body: JSON.stringify({
 action, reason 
}),
    
});

  
}

  // Approvals & The Golden Transaction
  async listApprovals(params?: {
 status?: string;
 invoice_id?: string;
 all_org?: boolean 
}): Promise<Approval[]> {

    const query = new URLSearchParams();

    if (params?.status) query.set('status', params.status);

    if (params?.invoice_id) query.set('invoice_id', params.invoice_id);

    if (params?.all_org) query.set('all_org', 'true');

    const qs = query.toString() ? `?${
query.toString()
}` : '';

    return this.request<Approval[]>(`/approvals${
qs
}`);

  
}

  async decideApproval(approvalId: string, decision: 'APPROVE' | 'REJECT' | 'REQUEST_CHANGES', comments: string): Promise<any> {

    return this.request<any>(`/approvals/${
approvalId
}/decide`, {

      method: 'POST',
      body: JSON.stringify({
 decision, comments 
}),
    
});

  
}

  // Payable Ledger & Payments
  async listPayables(params?: {
 status?: string 
}): Promise<PayableLedger[]> {

    const query = new URLSearchParams();

    if (params?.status) query.set('status', params.status);

    const qs = query.toString() ? `?${
query.toString()
}` : '';

    return this.request<PayableLedger[]>(`/payables${
qs
}`);

  
}

  async getPayableDetail(payableId: string): Promise<PayableLedger> {

    return this.request<PayableLedger>(`/payables/${
payableId
}`);

  
}

  async recordDisbursement(payableId: string, amount: number, paymentReference: string, paymentMethod: string = 'NEFT'): Promise<Payment> {

    return this.request<Payment>(`/payables/${
payableId
}/payments`, {

      method: 'POST',
      body: JSON.stringify({

        amount,
        payment_reference: paymentReference,
        payment_method: paymentMethod,
      
}),
    
});

  
}

  // Procurement (Vendors, POs, Receipts)
  async listVendors(): Promise<Vendor[]> {

    return this.request<Vendor[]>('/vendors');

  
}

  async listPurchaseOrders(): Promise<PurchaseOrder[]> {

    return this.request<PurchaseOrder[]>('/purchase-orders');

  
}

  async listGoodsReceipts(): Promise<GoodsReceipt[]> {

    return this.request<GoodsReceipt[]>('/receipts');

  
}

  // Audit Logs
  async listAuditLogs(params?: {
 entity_type?: string;
 limit?: number 
}): Promise<AuditLog[]> {

    const query = new URLSearchParams();

    if (params?.entity_type) query.set('entity_type', params.entity_type);

    if (params?.limit) query.set('limit', params.limit.toString());

    const qs = query.toString() ? `?${
query.toString()
}` : '';

    return this.request<AuditLog[]>(`/audit/logs${
qs
}`);

  
}

  // Phase 6: Control Intelligence & Explainability
  async getInvoiceExplanation(invoiceId: string): Promise<InvoiceExplanation> {

    return this.request<InvoiceExplanation>(`/invoices/${
invoiceId
}/explanation`);

  
}

  async getInvoiceControlGraph(invoiceId: string): Promise<ControlGraph> {

    return this.request<ControlGraph>(`/invoices/${
invoiceId
}/control-graph`);

  
}

  async getInvoiceAuditReplay(invoiceId: string): Promise<AuditReplay> {

    return this.request<AuditReplay>(`/invoices/${
invoiceId
}/audit-replay`);

  
}

  async getInvoiceRevisionsDiff(invoiceId: string): Promise<RevisionDiffResponse> {

    return this.request<RevisionDiffResponse>(`/invoices/${
invoiceId
}/revisions/diff`);

  
}

  async getDashboardControlHealth(): Promise<DashboardControlHealth> {

    return this.request<DashboardControlHealth>('/dashboard/control-health');

  
}

  // Phase 7: Risk Intelligence & Scenario Simulator
  async getInvoiceRiskProfile(invoiceId: string): Promise<InvoiceRiskProfile> {

    return this.request<InvoiceRiskProfile>(`/invoices/${
invoiceId
}/risk-profile`);

  
}

  async getDashboardRiskOverview(): Promise<DashboardRiskOverview> {

    return this.request<DashboardRiskOverview>('/dashboard/risk-overview');

  
}

  async listScenarios(): Promise<ScenarioSummary[]> {

    return this.request<ScenarioSummary[]>('/scenarios');

  
}

  async getScenarioDetail(scenarioId: string): Promise<ScenarioSummary> {

    return this.request<ScenarioSummary>(`/scenarios/${
scenarioId
}`);

  
}

  async simulateScenario(scenarioId: string, overrides?: WhatIfRequest): Promise<ScenarioSimulationResponse> {

    return this.request<ScenarioSimulationResponse>(`/scenarios/${
scenarioId
}/simulate`, {

      method: 'POST',
      body: overrides ? JSON.stringify(overrides) : undefined,
    
});

  
}

  async simulateWhatIf(scenarioId: string, request: WhatIfRequest): Promise<WhatIfSimulationResponse> {

    return this.request<WhatIfSimulationResponse>(`/scenarios/${
scenarioId
}/what-if`, {

      method: 'POST',
      body: JSON.stringify(request),
    
});

  
}

  async getScenarioDemoSteps(scenarioId: string): Promise<DemoStep[]> {

    return this.request<DemoStep[]>(`/scenarios/${
scenarioId
}/demo-steps`);

  
}

}

export const api = new ApiClient();


