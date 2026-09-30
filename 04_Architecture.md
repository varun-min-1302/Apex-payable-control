# End-to-End Accounts Payable Control System — Architecture Document

**Version:** 1.0

## 1. Architecture Principles
- Control decisions are deterministic and auditable.
- AI is an assistive subsystem, not payment authority.
- Workflow state is persisted server-side.
- Long-running work is asynchronous.
- Every important decision has evidence.
- Components are replaceable through interfaces/adapters.
- Least privilege and tenant isolation are enforced in the data layer.

## 2. Logical Architecture
```text
                        ┌───────────────────────┐
                        │ React + TypeScript UI │
                        └───────────┬───────────┘
                                    │ HTTPS
                                    ▼
                        ┌───────────────────────┐
                        │ API / Auth Gateway    │
                        │ FastAPI               │
                        └───────────┬───────────┘
                                    │
        ┌───────────────────────────┼────────────────────────────┐
        │                           │                            │
        ▼                           ▼                            ▼
┌───────────────┐          ┌──────────────────┐        ┌────────────────┐
│ Invoice        │          │ Control Engine   │        │ Workflow Engine│
│ Service        │          │                  │        │                │
└───────┬────────┘          └────────┬─────────┘        └────────┬───────┘
        │                            │                           │
        ▼                            ▼                           ▼
┌───────────────┐          ┌──────────────────┐        ┌────────────────┐
│ OCR/LLM Worker│          │ Rules + Matching │        │ Approval Router │
└───────┬───────┘          └────────┬─────────┘        └────────────────┘
        │                            │
        ▼                            ▼
┌───────────────┐          ┌──────────────────┐
│ Document      │          │ Similarity/Risk  │
│ Storage       │          │ Services         │
└───────┬───────┘          └────────┬─────────┘
        │                            │
        └──────────────┬─────────────┘
                       ▼
              ┌────────────────────┐
              │ PostgreSQL         │
              │ + pgvector         │
              └─────────┬──────────┘
                        │
             ┌──────────┼───────────┐
             ▼          ▼           ▼
         Payables     Audit      Analytics
```

## 3. Recommended Technology Stack
### Frontend
React, TypeScript, Vite, Tailwind CSS, accessible component library.

### Backend
FastAPI + Python.

### Database
PostgreSQL with pgvector extension where semantic similarity is needed.

### Object Storage
S3-compatible object storage or managed storage service.

### Queue
Redis-backed worker queue or managed queue. For the hackathon, a Redis worker is sufficient.

### OCR/Extraction
Provider adapter that supports OCR + structured extraction.

### Authentication
OIDC/JWT-based authentication or managed auth provider.

## 4. Backend Modules
```text
app/
  api/
  auth/
  invoices/
  vendors/
  purchase_orders/
  receipts/
  matching/
  controls/
  duplicates/
  workflow/
  approvals/
  payables/
  audit/
  notifications/
  ai/
  workers/
  common/
```

## 5. Control Engine
Control interface:
```python
class Control:
    id: str
    def evaluate(self, context) -> ControlResult: ...
```

Controls should be independently testable.

Example controls:
- vendor_exists
- vendor_active
- po_exists
- po_approved
- po_vendor_match
- receipt_available
- quantity_within_tolerance
- price_within_tolerance
- arithmetic_valid
- tax_valid
- currency_valid
- duplicate_exact
- duplicate_semantic
- bank_details_match
- approval_threshold_valid

## 6. Matching Strategy
### Stage 1: exact keys
PO number, invoice number, vendor ID.

### Stage 2: normalized matching
Whitespace, punctuation, case, known vendor aliases.

### Stage 3: candidate matching
Search candidate POs based on vendor/date/amount.

### Stage 4: semantic similarity
Use embeddings for invoice/document similarity where exact matching is insufficient.

Never let semantic similarity alone authorize a payable obligation.

## 7. Async Pipeline
```text
Upload
 ↓
Persist metadata + checksum
 ↓
Enqueue extraction job
 ↓
OCR/extraction
 ↓
Normalize
 ↓
Enqueue control evaluation
 ↓
Run deterministic controls
 ↓
Run duplicate similarity job
 ↓
Aggregate results
 ↓
Create exception OR route approval
```

## 8. Idempotency
Invoice processing endpoints and jobs must be idempotent.

Use:
- source document hash
- job ID
- idempotency key
- unique database constraints

If the same file is uploaded again, it must not create uncontrolled duplicate processing.

## 9. Multi-Tenant Data Isolation
Every business record must carry `organization_id`.

All reads/writes must enforce organization scope.

Use database-level policies where supported, plus service-layer authorization checks.

## 10. Event Model
Useful domain events:
```text
INVOICE_RECEIVED
EXTRACTION_COMPLETED
CONTROL_EVALUATION_COMPLETED
EXCEPTION_CREATED
EXCEPTION_ASSIGNED
EXCEPTION_RESOLVED
APPROVAL_REQUESTED
APPROVAL_DECIDED
PAYABLE_CREATED
PAYMENT_STATUS_CHANGED
```

Events can power notifications and future integrations.

## 11. State Transition Guard
Centralize transition validation.

```python
ALLOWED = {
  "RECEIVED": {"PROCESSING", "CANCELLED"},
  "PROCESSING": {"VALIDATING", "NEEDS_INFORMATION", "EXCEPTION"},
  "VALIDATING": {"EXCEPTION", "READY_FOR_APPROVAL"},
  "EXCEPTION": {"VALIDATING", "REJECTED", "ON_HOLD"},
  "READY_FOR_APPROVAL": {"APPROVAL_IN_PROGRESS"},
  "APPROVAL_IN_PROGRESS": {"APPROVED", "REJECTED", "EXCEPTION"},
  "APPROVED": {"PAYABLE", "CANCELLED"},
  "PAYABLE": {"SCHEDULED", "PAID", "ON_HOLD"},
  "SCHEDULED": {"PAID", "ON_HOLD"}
}
```

## 12. Evidence Model
Each control result should store:
- rule ID
- policy version
- input references
- expected value
- actual value
- computed variance
- result
- execution timestamp

This lets the UI generate a decision explanation without asking an LLM to invent it.

## 13. Data Flow for Approval
```text
Invoice
  ↓
Mandatory controls PASS
  ↓
No unresolved mandatory exceptions
  ↓
Authority policy resolves approver(s)
  ↓
Approval
  ↓
Evidence snapshot
  ↓
Create Payable
```

## 14. Deployment
Hackathon-friendly deployment:
```text
Web UI        → static/managed frontend
API           → managed container/server
Worker        → separate worker process
Postgres      → managed PostgreSQL
Redis         → managed Redis
Object Store  → managed S3-compatible storage
```

## 15. Observability
Every request/job should have:
- correlation_id
- actor_id
- organization_id
- entity_id
- job_id where applicable

Metrics:
- extraction duration
- control duration
- duplicate-search duration
- queue depth
- invoice processing latency
- API p95/p99
- exception rate
- workflow failure count
