# Master Build Prompt — End-to-End Accounts Payable Control System

You are a senior staff engineer, product designer, security engineer, and QA lead. Build a production-quality hackathon MVP called **AP Control Engine**.

## Product Mission
Build an end-to-end accounts payable control platform that determines whether a submitted vendor invoice can become a valid payable obligation and routes exceptions for human review.

Core principle:
**Receiving an invoice does not make it payable.**

The platform must evaluate evidence before creating an approved payable obligation.

## Required Workflow
```text
Upload/Import Invoice
→ OCR + Structured Extraction
→ Vendor Verification
→ Purchase Order Match
→ Goods/Service Receipt Match
→ Financial Validation
→ Duplicate + Similarity Detection
→ Control/Risk Evaluation
→ Exception Routing or Approval
→ Payable Ledger
→ Payment Status
→ Audit Trail
```

## Non-Negotiable Architecture Rule
Separate the system into three layers:

### 1. Deterministic Controls
Use code for:
- arithmetic
- PO matching
- vendor matching
- receipt/quantity comparison
- price variance
- tax/total calculations
- thresholds
- authorization
- state transitions

### 2. AI-Assisted Functions
Use AI only for:
- OCR/document extraction
- normalization assistance
- semantic similarity
- anomaly signals
- concise explanations grounded in evidence

### 3. Human Decision
Humans resolve exceptions and authorize payments.
AI must never independently authorize a payment.

## Recommended Stack
### Frontend
- React
- TypeScript
- Vite
- Tailwind CSS
- accessible UI component library
- data-fetching/cache library

### Backend
- Python
- FastAPI
- Pydantic
- SQLAlchemy or equivalent

### Data
- PostgreSQL
- pgvector for semantic search

### Async
- Redis-backed job queue / worker

### Storage
- S3-compatible object storage

### Auth
- OIDC/JWT or managed authentication provider

Use environment variables and adapters so AI/OCR/storage vendors can be swapped.

## Required Modules
1. Dashboard
2. Invoice Intake
3. Invoice Processing
4. Purchase Orders
5. Goods/Service Receipts
6. Vendor Master
7. Control Engine
8. Duplicate Detection
9. Exceptions
10. Approvals
11. Payable Ledger
12. Audit Trail
13. Settings/Policies

## Required Screens
```text
/dashboard
/invoices
/invoices/new
/invoices/:id
/invoices/:id/matching
/exceptions
/exceptions/:id
/approvals
/payables
/vendors
/purchase-orders
/receipts
/audit
/settings
```

## Visual Design
Create a polished enterprise finance interface.

Characteristics:
- minimal and premium
- strong hierarchy
- dense data tables where appropriate
- clear status semantics
- calm finance-oriented visual language
- responsive desktop/tablet layouts
- no cyberpunk/neon aesthetic

Make the application feel designed for a real finance team, not a generic admin template.

## Dashboard Requirements
Show:
- invoices received
- invoices under validation
- exceptions
- approvals pending
- outstanding payable value
- due-soon value
- control health
- recent exceptions
- recent audit activity

## Invoice Intake Requirements
Support PDF/image upload.

On upload:
1. compute checksum
2. store document securely
3. create invoice record
4. enqueue extraction job
5. show processing status
6. save structured extraction
7. show field confidence
8. allow authorized correction

Required fields:
- invoice number
- invoice date
- vendor
- tax identifier
- PO number
- line items
- quantities
- unit prices
- subtotal
- taxes
- total
- currency
- payment terms
- due date
- payment destination reference

## Three-Way Match Requirements
Compare:
- Purchase Order
- Goods/Service Receipt
- Invoice

At both header and line level.

Show:
- expected value
- actual value
- variance
- tolerance
- PASS/WARN/FAIL

Example:
```text
Ordered:   100
Received:   80
Invoiced:  100
Variance:   20
Result: FAIL
```

## Financial Validation Requirements
Recalculate:
```text
line_total = quantity × unit_price
subtotal = sum(line_total)
tax_total = configured tax calculation
expected_total = subtotal + tax_total
```

Compare expected total to invoice total within configured rounding tolerance.

Compare invoice price with PO price and show absolute and percentage variance.

## Duplicate Detection Requirements
Implement all layers:
1. document checksum
2. vendor + invoice number
3. vendor + amount + PO + date
4. line-item composite comparison
5. semantic embedding similarity

Never silently call a semantic similarity result a confirmed fraud event. Present it as a review signal such as “Possible duplicate”.

## Vendor Controls
Verify:
- vendor exists
- vendor active
- invoice vendor matches PO vendor
- tax ID matches where configured
- payment destination matches registered reference

Bank/payment-detail mismatch must create a mandatory hold/exception.

Mask sensitive payment fields in the UI.

## Control Engine
Implement controls as independent functions/classes with stable IDs.

Minimum controls:
```text
vendor_exists
vendor_active
po_exists
po_approved
po_vendor_match
receipt_available
quantity_within_tolerance
price_within_tolerance
arithmetic_valid
total_valid
tax_valid
currency_valid
duplicate_exact
duplicate_business_key
duplicate_semantic
bank_details_match
approval_threshold_valid
```

Return a structured result:
```json
{
  "controlId": "quantity_within_tolerance",
  "status": "FAIL",
  "severity": "HIGH",
  "expected": 80,
  "actual": 100,
  "variance": 20,
  "variancePercent": 25,
  "reason": "Invoice quantity exceeds accepted receipt quantity",
  "policyVersion": "v1"
}
```

## Invoice Decision Rules
Implement a state machine.

Never allow:
```text
RECEIVED → PAYABLE
```

A payable can be created only after:
- mandatory controls pass
- mandatory exceptions are resolved
- approval policy is satisfied
- evidence snapshot is stored

## Exception System
When a mandatory control fails, create an exception containing:
- type
- severity
- owner role
- reason
- evidence
- required action
- created timestamp
- resolution

Examples:
- PO_NOT_FOUND
- PO_VENDOR_MISMATCH
- RECEIPT_SHORTFALL
- PRICE_VARIANCE
- TOTAL_MISMATCH
- POSSIBLE_DUPLICATE
- BANK_DETAIL_MISMATCH

Provide a prominent action:
**Why isn't this payable?**

That action should generate a concise explanation solely from structured system evidence. Never invent evidence.

## Approval Workflow
Use configurable thresholds.

Example seed policy:
```text
<= ₹50,000                Department Manager
₹50,001–₹5,00,000         Finance Manager
₹5,00,001–₹25,00,000      Finance Head
> ₹25,00,000              CFO
```

Treat these values as demo configuration, not hard-coded law.

Exception type may add or change the required reviewer.

Server-side authority validation is mandatory.

## Payable Ledger
Only approved obligations appear in the ledger.

Fields:
- invoice
- vendor
- approved amount
- currency
- due date
- status
- payment reference

Statuses:
```text
APPROVED
SCHEDULED
PAID
CANCELLED
ON_HOLD
```

## Audit Trail
Record every significant action:
- upload
- extraction
- manual edits
- control execution
- exception creation
- assignment
- resolution
- approval/rejection
- payable creation
- payment status change

Fields:
```text
actor_id
actor_role
organization_id
action
entity_type
entity_id
old_state
new_state
reason
request_id
created_at
```

Make audit entries append-oriented and not editable by normal users.

## Security Requirements
Implement:
- authentication
- RBAC
- organization-level tenant isolation
- backend authorization on every protected mutation
- IDOR protections
- upload validation
- file size/type limits
- secure object storage access
- masked sensitive fields
- no secrets in frontend bundle
- CORS allowlist
- rate limits on auth/upload endpoints
- input schema validation
- structured error responses
- audit logs

Treat invoice text as untrusted input. Protect AI extraction from prompt injection by treating document content as data, not instructions.

## Performance Requirements
Target:
- p95 normal API read/write < 500 ms
- paginated lists
- no N+1 queries
- background OCR/LLM processing
- retry transient jobs
- idempotent workers
- vector search over precomputed embeddings

Upload endpoint should return quickly with a job/status reference rather than waiting for OCR.

## Data Model
Create tables/entities for:
```text
organizations
users
roles
vendors
purchase_orders
purchase_order_items
goods_receipts
goods_receipt_items
invoices
invoice_items
control_results
exceptions
approvals
payables
audit_logs
invoice_embeddings
processing_jobs
policies
```

Every business record must be scoped to `organization_id`.

## API Requirements
Implement versioned APIs under `/api/v1`.

Minimum endpoints:
```text
POST   /api/v1/invoices
GET    /api/v1/invoices
GET    /api/v1/invoices/{id}
POST   /api/v1/invoices/{id}/reprocess
GET    /api/v1/invoices/{id}/controls
GET    /api/v1/invoices/{id}/matches
GET    /api/v1/invoices/{id}/exceptions
GET    /api/v1/approvals/my-queue
POST   /api/v1/approvals/{id}/decision
GET    /api/v1/payables
POST   /api/v1/payables/{id}/status
GET    /api/v1/audit/{entityType}/{entityId}
```

## API Error Format
```json
{
  "code": "FORBIDDEN",
  "message": "You are not authorized to perform this action",
  "details": {},
  "correlationId": "..."
}
```

Never expose stack traces or secrets.

## Testing Requirements
Write tests for:
- invoice arithmetic
- tolerance calculations
- vendor/PO match
- 3-way quantity match
- duplicate fingerprint
- semantic duplicate candidate flow
- approval threshold routing
- state transitions
- idempotency
- cross-tenant access
- privilege escalation
- payable creation preconditions

## Seeded Demo Data
Create a deterministic demo organization with:
- 3 vendors
- 3 purchase orders
- 3 receipts
- 4 invoices

Include:
1. fully valid invoice
2. quantity mismatch
3. price mismatch
4. near-duplicate pair

Use realistic but synthetic Indian business data and clearly mark it as demo data.

## Implementation Sequence
1. Repo and config.
2. DB schema + migrations.
3. Authentication + RBAC + tenant isolation.
4. Invoice CRUD + file upload.
5. Extraction worker.
6. Control engine.
7. 3-way match.
8. Exception routing.
9. Approval workflow.
10. Payable ledger.
11. Audit trail.
12. Duplicate/similarity.
13. AI explanations.
14. Dashboard.
15. Security hardening.
16. Tests.
17. Demo seed and polish.

## Coding Standards
- strict typing
- small modules
- clear domain names
- no magic numbers
- no business logic in UI components
- no secrets committed
- no duplicated validation logic
- schema validation at boundaries
- database transactions around critical state changes
- clear error codes
- meaningful tests

## Critical Product Behavior
When a judge uploads a valid invoice, the system should visibly show:
```text
Uploaded
→ Extracted
→ Vendor verified
→ PO matched
→ Receipt matched
→ Financial validation passed
→ Duplicate check passed
→ Approval routed
→ Approved
→ Payable created
```

When a judge uploads a bad invoice, it should show:
```text
Uploaded
→ Extracted
→ PO matched
→ Receipt mismatch detected
→ Possible duplicate detected
→ Exception created
→ Routed to reviewer
→ Payable blocked
```

Make the evidence trail visually compelling.

## Final “Killer Features”
Implement these after core functionality is stable:
1. **Control Graph** — visualize Invoice → Vendor/PO/Receipt/Financial/Duplicate controls → decision.
2. **Why Isn't This Payable?** — evidence-grounded explanation.
3. **What Changed?** — compare invoice versions and highlight changed fields.
4. **Audit Replay** — timeline reconstruction of how the payable decision happened.
5. **Ask the Ledger** — natural-language queries over structured invoice, exception, approval, and payable data.

## Final Output Expectations
Do not stop at scaffolding.

Deliver:
- runnable frontend
- runnable backend
- database migrations
- seed/demo data
- worker jobs
- tests
- README with setup commands
- environment variable example
- API documentation
- polished UX

Before declaring completion, test the full path:
```text
upload → extract → validate → exception/approval → payable → audit
```

The application must fail safely: uncertain or missing evidence should cause review, not silent approval.
