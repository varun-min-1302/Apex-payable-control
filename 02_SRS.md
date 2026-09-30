# End-to-End Accounts Payable Control System — Software Requirements Specification (SRS)

**Version:** 1.0

## 1. Scope
The software shall intake invoices, extract structured data, verify vendor/PO/receipt relationships, run financial and duplicate controls, route exceptions and approvals, create approved payable obligations, and preserve an audit trail.

## 2. System Actors
| Actor | Primary Permissions |
|---|---|
| AP Clerk | create/upload invoices, edit extraction fields, view assigned work |
| Procurement Manager | review PO/vendor exceptions |
| Receiving User | review receipt exceptions |
| Finance Manager | approve assigned invoices |
| Finance Head/CFO | approve high-value invoices |
| Auditor | read-only access to evidence and logs |
| Admin | configure master data, policies, roles |

## 3. Functional Requirements
### FR-001 Authentication
The system shall authenticate users and establish a role-bound session.

### FR-002 Authorization
The system shall enforce RBAC on every protected API operation.

### FR-003 Invoice Upload
The system shall accept supported invoice documents and persist their metadata and checksum.

### FR-004 Extraction
The system shall extract header fields and line items into normalized structured data.

### FR-005 Extraction Review
The system shall allow authorized users to correct extracted fields and record those corrections.

### FR-006 Vendor Matching
The system shall identify the expected vendor using exact or normalized matching and expose ambiguity when multiple candidates exist.

### FR-007 PO Matching
The system shall match an invoice to a purchase order and report match state per header and line item.

### FR-008 PO State Validation
The system shall verify that the referenced PO satisfies the configured status policy.

### FR-009 Receipt Matching
The system shall compare invoiced quantities/value against recorded receipts.

### FR-010 Tolerance Policy
The system shall support configurable amount and quantity tolerances.

### FR-011 Arithmetic Validation
The system shall independently calculate line totals, subtotal, tax, and total.

### FR-012 Price Validation
The system shall compare invoice price with agreed PO price and expose absolute and percentage variance.

### FR-013 Duplicate Detection
The system shall support document-hash, business-key, composite, and semantic similarity signals.

### FR-014 Vendor Bank Validation
The system shall compare payment destination data with the registered vendor record.

### FR-015 Control Evaluation
The system shall evaluate deterministic control rules and produce machine-readable results.

### FR-016 Risk/Signal Aggregation
The system shall aggregate control signals into a transparent review status. The score/status must be explainable.

### FR-017 Exception Creation
Any failed mandatory control shall create or attach an exception with reason, severity, owner role, and required action.

### FR-018 Workflow Routing
The system shall route an invoice based on threshold and exception rules.

### FR-019 Approval Authority
A user shall approve only within their configured authority and assigned workflow step.

### FR-020 State Machine
The invoice lifecycle shall prevent invalid transitions.

### FR-021 Payable Creation
A payable obligation shall be created only after all mandatory controls pass and required approvals are complete.

### FR-022 Due Date
The system shall calculate or store a due date based on invoice date, agreed terms, or configured policy.

### FR-023 Payment Status
The system shall allow authorized users to update payment status without editing historical approval records.

### FR-024 Audit Trail
Each material system or user action shall create an audit entry.

### FR-025 Evidence Snapshot
Approval and exception events shall retain references to the underlying control evidence at decision time.

### FR-026 Search/Filter
Users shall search by invoice number, vendor, PO, status, exception, amount, and date.

### FR-027 Dashboard
The system shall summarize invoice volumes, exceptions, pending approvals, and payable aging.

### FR-028 Notifications
The system shall support in-app notifications for assignment and workflow events.

## 4. Invoice State Model
```text
RECEIVED
  -> PROCESSING
  -> VALIDATING
  -> NEEDS_INFORMATION
  -> EXCEPTION
  -> READY_FOR_APPROVAL
  -> APPROVAL_IN_PROGRESS
  -> APPROVED
  -> PAYABLE
  -> SCHEDULED
  -> PAID
```
Terminal/reversal states as required:
```text
REJECTED
CANCELLED
ON_HOLD
```
Rules:
- RECEIVED cannot jump directly to PAYABLE.
- PAYABLE requires APPROVED.
- APPROVED requires all mandatory controls and approvals.
- PAID requires PAYABLE/SCHEDULED according to policy.

## 5. Data Requirements
### Vendor
id, legal_name, normalized_name, tax_id, address, bank_account_token/reference, IFSC/reference, active_status, created_at, updated_at.

### Purchase Order
id, po_number, vendor_id, status, currency, terms, approved_by, approved_at, total, created_at.

### PO Item
id, po_id, sku_or_service_code, description, ordered_qty, unit_price, tax_rate, line_total.

### Receipt
id, po_id, receipt_number, receipt_type, status, received_at, created_by.

### Receipt Item
id, receipt_id, po_item_id, received_qty, accepted_qty, rejected_qty.

### Invoice
id, invoice_number, vendor_id, po_id, invoice_date, currency, subtotal, tax_total, grand_total, due_date, source_uri, source_hash, status, created_at.

### Invoice Item
id, invoice_id, po_item_id, description, quantity, unit_price, tax_rate, line_total.

### Control Result
id, invoice_id, control_type, status, severity, expected_value, actual_value, variance, policy_version, evidence_ref, created_at.

### Exception
id, invoice_id, type, severity, status, owner_role, assigned_to, reason, resolution, created_at, resolved_at.

### Approval
id, invoice_id, step, approver_id, decision, comment, decided_at, authority_policy_version.

### Payable
id, invoice_id, approved_amount, currency, due_date, status, created_at, payment_reference.

### Audit Log
id, actor_id, actor_role, action, entity_type, entity_id, old_state, new_state, reason, metadata_json, created_at.

## 6. Non-Functional Requirements
### NFR-001 Availability
The demo system should tolerate service restarts without losing persisted workflow state.

### NFR-002 Performance
Interactive API requests should target p95 < 500 ms for normal reads/writes, excluding long-running OCR/LLM jobs.

### NFR-003 Async Processing
Document extraction and semantic similarity jobs shall run asynchronously.

### NFR-004 Security
Sensitive data must be access-controlled and encrypted in transit; sensitive payment fields should be minimized and tokenized/masked where possible.

### NFR-005 Auditability
Audit records must be append-oriented and protected from ordinary business-user modification.

### NFR-006 Observability
Errors, workflow failures, and processing jobs must expose structured logs and correlation IDs.

### NFR-007 Scalability
The architecture shall permit horizontal scaling of API and worker processes.

### NFR-008 Usability
Core invoice-to-decision flow should be understandable without training for a first-time demo user.

## 7. Validation Rules Examples
- Invoice vendor must exist and be active.
- Referenced PO must exist and be permitted for invoicing.
- Invoice line quantity must not exceed available received quantity beyond configured tolerance unless explicitly allowed.
- Invoice unit price variance beyond configured tolerance creates exception.
- Independent total calculation must match invoice total within configured rounding tolerance.
- Duplicate signals above configured threshold create review.
- Bank-detail mismatch creates a mandatory hold.
- Approval threshold must determine required authority.

## 8. API Requirements
Representative endpoints:
```text
POST   /api/v1/invoices
GET    /api/v1/invoices
GET    /api/v1/invoices/{id}
POST   /api/v1/invoices/{id}/reprocess
POST   /api/v1/invoices/{id}/controls/run
GET    /api/v1/invoices/{id}/controls
GET    /api/v1/invoices/{id}/matches
GET    /api/v1/invoices/{id}/exceptions
POST   /api/v1/exceptions/{id}/assign
POST   /api/v1/exceptions/{id}/resolve
GET    /api/v1/approvals/my-queue
POST   /api/v1/approvals/{id}/decision
GET    /api/v1/payables
POST   /api/v1/payables/{id}/status
GET    /api/v1/audit/{entityType}/{entityId}
```

## 9. Error Handling
Errors shall use structured responses:
```json
{
  "code": "PO_NOT_FOUND",
  "message": "Referenced purchase order could not be located",
  "details": {"poNumber": "PO-2045"},
  "correlationId": "..."
}
```
No sensitive internal stack traces shall be returned to clients.
