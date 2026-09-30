# Enterprise Accounts Payable (AP) Control System — Database Architecture Foundation

## 1. Architectural Philosophy & Core Principles

This database architecture forms the core foundation of a production-grade, enterprise **Accounts Payable Control Platform** developed for the Finathon Hackathon. 

### The Core Invariant
$$\text{RECEIVED INVOICE} \ne \text{PAYABLE OBLIGATION}$$

A submitted vendor invoice **never** automatically creates a payable ledger liability. In this system:
1. An invoice begins in a `RECEIVED` or `PROCESSING` state.
2. Invoices are validated through an automated **Control Run** comprising 10+ deterministic controls (3-way matching of quantities, prices, taxes, totals, vendor active status, duplicate checks, bank account fingerprinting, and risk threshold checks).
3. If any discrepancies occur, an `EXCEPTION` is flagged and the invoice is held.
4. If risk signals appear (e.g. semantic similarity to previous invoices or threshold proximity split billing), a `RISK_SIGNAL` is recorded.
5. If controls pass or variances fall within policy thresholds, the invoice transitions to `AWAITING_APPROVAL`.
6. Only upon explicit human sign-off via `ap.approvals` according to multi-tier `ap.approval_policies` does an entry get committed to `ap.payable_ledger`.
7. Once committed to the payable ledger, payment batches can execute partial or full disbursements recorded in `ap.payments`.
8. Every single mutation, ingestion, decision, and payment is permanently recorded in `audit.audit_logs`, protected by an engine-level PostgreSQL trigger that rejects all updates and deletes.

---

## 2. PostgreSQL Technology Stack & Extensions

- **Database Engine:** PostgreSQL 16.15 (Windows x64 / Linux compatible)
- **Primary Keys:** UUIDv4 natively generated via `gen_random_uuid()` / `uuid-ossp`
- **Monetary Precision:** Strictly `NUMERIC(18,2)` — zero `FLOAT` or `REAL` types used
- **Quantity Precision:** Strictly `NUMERIC(18,4)` for fractional inventory units
- **Percentage Precision:** Strictly `NUMERIC(8,4)` for tax rates, discounts, and variances
- **Temporal Datatypes:** `TIMESTAMPTZ` (`TIMESTAMP WITH TIME ZONE`) for all operational timestamps; `DATE` for calendar dates
- **Flexible Evidence:** `JSONB` for raw invoice extraction metadata, control run evidence, and audit change diffs
- **Semantic Vector Storage:** `pgvector` (`vector(1536)`) for AI-driven invoice layout, text, and semantic duplicate detection

### Active Extensions
| Extension | Version | Purpose |
| :--- | :--- | :--- |
| `uuid-ossp` | 1.1 | Native UUID generation functions |
| `pgcrypto` | 1.3 | Cryptographic hashing (`digest`, SHA-256) for document hashes and bank account fingerprints |
| `btree_gist` | 1.7 | Multi-column exclusion constraints and composite indexing |
| `pg_trgm` | 1.6 | Trigram similarity matching for vendor legal names and invoice numbers |
| `vector` | 0.8.6 | Vector embeddings and cosine similarity index (`ivfflat` / `hnsw`) for duplicate invoice detection |

---

## 3. Logical Schemas & 22 Database Entities

The database is partitioned into four distinct logical PostgreSQL schemas:

```
ap_control
├── identity
│   ├── tenants
│   ├── users
│   ├── roles
│   └── user_roles
├── procurement
│   ├── vendors
│   ├── purchase_orders
│   ├── purchase_order_items
│   ├── goods_receipts
│   └── goods_receipt_items
├── ap
│   ├── invoices
│   ├── invoice_revisions
│   ├── invoice_items
│   ├── control_runs
│   ├── control_results
│   ├── risk_signals
│   ├── exceptions
│   ├── approval_policies
│   ├── approvals
│   ├── payable_ledger
│   ├── payments
│   └── invoice_embeddings
└── audit
    └── audit_logs
```

### Schema Summary:
1. **`identity` Schema:**
   - `tenants`: Multi-tenant boundary. Enforces strict tenant separation.
   - `users`: Corporate actors (AP Clerks, Procurement Managers, Finance Heads, Auditors).
   - `roles`: RBAC roles (`ADMIN`, `AP_CLERK`, `PROCUREMENT_MANAGER`, `FINANCE_MANAGER`, `FINANCE_HEAD`, `AUDITOR`).
   - `user_roles`: Many-to-many link table with composite primary key `(user_id, role_id)`.
2. **`procurement` Schema:**
   - `vendors`: Vendor master records. Contains masked bank accounts (`bank_account_last4`) and SHA-256 hash fingerprints (`bank_account_hash`). Plaintext bank numbers are never stored.
   - `purchase_orders`: Approved purchase orders with workflow status, financial totals, and terms.
   - `purchase_order_items`: PO line items with `quantity > 0`, `unit_price >= 0`, `tax_rate >= 0`, and unique `line_number` per PO.
   - `goods_receipts`: Warehouse receiving receipts linked to POs.
   - `goods_receipt_items`: Received, accepted, and rejected quantities with check constraint `accepted_quantity + rejected_quantity <= received_quantity`.
3. **`ap` Schema:**
   - `invoices`: Aggregate invoice header. Tracks invoice lifecycle, OCR extraction status, document SHA-256 hash, and points to the `current_revision_id`.
   - `invoice_revisions`: Immutable revision history. When vendors send corrected invoices, a new revision is created (`revision_number = 2`). Historical revisions are never deleted.
   - `invoice_items`: Line items extracted from the invoice revision.
   - `control_runs`: Execution runs of the validation ruleset for a specific revision.
   - `control_results`: Individual evaluation outcomes for each rule (e.g. `PO_VENDOR_MATCH`, `QUANTITY_MATCH`, `PRICE_MATCH`, `TAX_VALIDATION`, `TOTAL_VALIDATION`, `BANK_HASH_MATCH`). Stores expected vs actual values, variances, and evidence.
   - `risk_signals`: Proactive fraud and anomaly detection (e.g. `THRESHOLD_PROXIMITY`, `SEMANTIC_SIMILARITY`).
   - `exceptions`: Hard blockers halting invoice progression (e.g. `PRICE_MISMATCH`, `QUANTITY_MISMATCH`, `DUPLICATE_INVOICE`, `BANK_DETAILS_MISMATCH`).
   - `approval_policies`: Threshold-based approval matrix rules (Tier 1: < $10k, Tier 2: $10k-$50k, Tier 3: > $50k, Exception Override).
   - `approvals`: Human sign-offs recording approver identity, decision (`APPROVE`, `REJECT`), comments, and timestamps.
   - `payable_ledger`: The committed payable obligation. Has unique constraint `(tenant_id, invoice_id)` guaranteeing only one payable ledger entry exists per invoice.
   - `payments`: Financial disbursements made against payables (`OPEN`, `PARTIALLY_PAID`, `PAID`).
   - `invoice_embeddings`: Vector embeddings for semantic invoice similarity and clustering.
4. **`audit` Schema:**
   - `audit_logs`: Immutable audit trail. Protected by PostgreSQL trigger `trg_prevent_audit_log_modification` which raises an exception on any `UPDATE` or `DELETE`.

---

## 4. Multi-Tenancy Architecture

Multi-tenancy is enforced structurally:
- Every business table includes `tenant_id UUID REFERENCES identity.tenants(id) ON DELETE CASCADE`.
- Uniqueness constraints are composite with `tenant_id`:
  - `UNIQUE (tenant_id, vendor_code)`
  - `UNIQUE (tenant_id, po_number)`
  - `UNIQUE (tenant_id, invoice_number)`
  - `UNIQUE (tenant_id, payable_number)`
- Cross-tenant collisions are completely eliminated: Tenant B can use the same `invoice_number` as Tenant A without constraint conflicts or data leakage.

---

## 5. Deliberate Scenarios Matrix (Scenarios A through O)

The database seed dataset (`backend/scripts/seed.py`) implements all 15 required business scenarios:

| Scenario | Invoice # | Expected State | Validation Result / Characteristics |
| :--- | :--- | :--- | :--- |
| **A: Clean 3-Way Match** | `INV-2026-0001` | `APPROVED` | All 10 controls `PASS`. Line item quantity, price, tax match PO and GR. Human approval logged. |
| **B: Quantity Mismatch** | `INV-2026-0002` | `EXCEPTION` | Invoiced Qty (100) > Accepted Qty (80). Control `QUANTITY_MATCH` fails with variance 20.0000. Exception logged. |
| **C: Price Mismatch** | `INV-2026-0003` | `EXCEPTION` | Invoiced unit price ₹1,850.00 vs PO unit price ₹1,500.00. Control `PRICE_MATCH` fails. Exception logged. |
| **D: PO Missing / Unmatched** | `INV-2026-0004` | `EXCEPTION` | `purchase_order_id` is `NULL`. Control `PO_EXISTS` fails. Exception `PO_NOT_FOUND` logged. |
| **E: Vendor Mismatch** | `INV-2026-0005` | `EXCEPTION` | Invoice references valid PO-5, but vendor on invoice differs from vendor on PO. Control `PO_VENDOR_MATCH` fails. |
| **F: Partial Receipt Matching** | `INV-2026-0006` | `AWAITING_APPROVAL`| PO Qty = 100, Partial GR Qty = 50, Invoice Qty = 50. Line match passes against partial GR. Pending approval. |
| **G: Exact Duplicate Invoice** | `INV-2026-0007` | `EXCEPTION` | Document SHA-256 hash exactly matches `INV-2026-0001`. Control `DUPLICATE_INVOICE_CHECK` fails. Exception logged. |
| **H: Semantic Duplicate** | `INV-2026-0008` | `EXCEPTION` | Near-duplicate billing against `INV-2026-0006`. `RiskSignal` of `SEMANTIC_SIMILARITY` recorded (96.5% confidence). |
| **I: Tax Calculation Error** | `INV-2026-0009` | `EXCEPTION` | Invoiced tax computed as ₹15,000.00 instead of ₹18,000.00 (18% on ₹100,000). Control `TAX_VALIDATION` fails. |
| **J: Total Calculation Error** | `INV-2026-0010` | `EXCEPTION` | Subtotal ₹50,000 + Tax ₹9,000 = ₹59,000, but invoice claims ₹64,000. Control `TOTAL_VALIDATION` fails. |
| **K: Bank Details Mismatch** | `INV-2026-0011` | `EXCEPTION` | Invoice bank hash does not match vendor master bank hash. High-risk fraud exception `BANK_DETAILS_MISMATCH`. |
| **L: Threshold Proximity** | `INV-2026-0012` | `AWAITING_APPROVAL`| Invoice total ₹99,800.00 sits just below ₹100,000 manager sign-off threshold. `RiskSignal` `THRESHOLD_PROXIMITY` logged. |
| **M: Corrected Revision 2** | `INV-2026-0013` | `APPROVED` | Revision 1 had error. Revision 2 submitted with corrected amounts (`revision_number = 2`). Controls rerun & passed. |
| **N: Payable & Partial Payment** | `INV-2026-0014` | `PAYABLE_CREATED` | Approved invoice created `PayableLedger` record (`PAY-2026-0014`). Partial NEFT payment recorded in `ap.payments`. |
| **O: Rejected Invoice** | `INV-2026-0015` | `REJECTED` | Unapproved variance rejected by Finance Manager. Full rejection audit trail recorded. |

---

## 6. How to Run Migrations, Seeds, and Tests

### Prerequisites
- Python 3.11+ (tested on Python 3.13)
- PostgreSQL 16+ running on `localhost:5432` with database `ap_control`
- Active environment with dependencies installed:
  ```bash
  pip install -r backend/requirements.txt
  ```

### 1. Run Database Migrations
Apply the full schema migration via Alembic:
```bash
# Set PYTHONPATH
$env:PYTHONPATH="d:\Projects\PA control"   # PowerShell
export PYTHONPATH="."                     # Linux / macOS

# Upgrade to latest head
alembic -c backend/alembic.ini upgrade head

# To verify clean downgrade and upgrade idempotence:
alembic -c backend/alembic.ini downgrade base
alembic -c backend/alembic.ini upgrade head
```

### 2. Seed Database with Realistic AP Data
Populate the database with 1 tenant, 7 roles, 9 users, 10 vendors, 30 POs, 60 PO items, 30 GRs, 60 GR items, 40 invoices, 41 revisions, 40 control runs, 400 control results, and all 15 scenarios:
```bash
python backend/scripts/seed.py
```

### 3. Verify Database Integrity & Scenarios
Run the verification check script:
```bash
python backend/scripts/verify_db.py
```

### 4. Execute Automated Pytest Suite
Run the 77-test automated verification suite covering database, controls, services, and integration scenarios:
```bash
python -m pytest backend/tests -v --cov=backend/application --cov=backend/domain --cov=backend/repositories
```

---

## 7. Phase 2: Control Engine Architecture

The Control Engine is the deterministic validation core of the Accounts Payable Control System.

### Execution Workflow
```
Invoice
   ↓
Load current invoice revision
   ↓
Load immutable ControlContext (single-query pass, Zero N+1)
   ↓
Execute 18 deterministic & risk controls
   ↓
Batch persist Control Results (ap.control_results)
   ↓
Render explainable InvoiceDecision (PASS, PASS_WITH_WARNING, EXCEPTION, ERROR)
   ↓
Generate Risk Signals (ap.risk_signals) for warnings
   ↓
Generate Exceptions (ap.exceptions) for failures
   ↓
Update Invoice Status (AWAITING_APPROVAL, EXCEPTION, etc.)
   ↓
Evaluate Approval Policies & Generate Route Steps (ap.approvals)
   ↓
Write Append-Only Audit Trail (audit.audit_logs)
```

### Core Invariant Verification
$$\text{CONTROL ENGINE} \implies \text{PAYABLE COUNT} = 0$$
The Control Engine strictly enforces that **RECEIVED INVOICE $\ne$ PAYABLE OBLIGATION**. Under no circumstance does running controls create an entry in `ap.payable_ledger`. Payable ledger entries can only be committed through explicit human approval sign-off in later workflow services.

---

## 8. Implemented Controls Suite (18 Controls)

| # | Control Code | Category | Description | Severity | Failure Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `VENDOR_EXISTS` | `VENDOR` | Validates vendor exists in master records | `CRITICAL` | `VENDOR_NOT_FOUND` |
| 2 | `VENDOR_STATUS` | `VENDOR` | Ensures vendor status is `ACTIVE` | `CRITICAL` | `VENDOR_INACTIVE` |
| 3 | `VENDOR_TAX_ID_MATCH` | `VENDOR` | Matches submitted GSTIN/tax identifier to vendor master | `HIGH` | `TAX_ID_MISMATCH` |
| 4 | `BANK_DETAILS_MATCH` | `SECURITY` | SHA-256 fingerprint verification of remittance bank details | `CRITICAL` | `BANK_DETAILS_MISMATCH` |
| 5 | `PO_EXISTS` | `PROCUREMENT` | Validates referenced purchase order exists | `CRITICAL` | `PO_NOT_FOUND` |
| 6 | `PO_APPROVED` | `PROCUREMENT` | Ensures purchase order was approved before invoice date | `CRITICAL` | `PO_NOT_APPROVED` |
| 7 | `PO_VENDOR_MATCH` | `PROCUREMENT` | Verifies invoice vendor matches PO vendor | `CRITICAL` | `VENDOR_MISMATCH` |
| 8 | `PO_ITEM_MATCH` | `PROCUREMENT` | Matches invoice line items against agreed PO lines | `HIGH` | `PO_ITEM_MISMATCH` |
| 9 | `RECEIPT_MATCH` | `RECEIPT` | Verifies warehouse delivery receipts exist for PO items | `HIGH` | `QUANTITY_MISMATCH` |
| 10 | `QUANTITY_MATCH` | `RECEIPT` | Enforces invoiced qty $\le$ accepted receipt qty (3-way match) | `HIGH` | `QUANTITY_MISMATCH` |
| 11 | `PRICE_MATCH` | `FINANCIAL` | Enforces invoiced unit price $\le$ PO unit price (within tolerance) | `HIGH` | `PRICE_MISMATCH` |
| 12 | `TAX_VALIDATION` | `FINANCIAL` | Validates line tax rates against PO contract & recalculates totals | `HIGH` | `TAX_CALCULATION_ERROR` |
| 13 | `TOTAL_VALIDATION` | `FINANCIAL` | Checks subtotal $-$ discount $+$ tax $=$ grand total | `CRITICAL` | `TOTAL_CALCULATION_ERROR` |
| 14 | `PAYMENT_TERMS` | `FINANCIAL` | Checks net terms compliance against vendor master | `LOW` | Warning / Risk Signal |
| 15 | `DUPLICATE_EXACT` | `DUPLICATE` | Checks document SHA-256 collision and vendor invoice numbers | `CRITICAL` | `DUPLICATE_INVOICE` |
| 16 | `DUPLICATE_SEMANTIC` | `DUPLICATE` | Evaluates pgvector embeddings for similarity; returns `NOT_APPLICABLE` when embeddings are empty | `MEDIUM` | Warning / Risk Signal |
| 17 | `THRESHOLD_PROXIMITY` | `APPROVAL` | Flags structuring / split billing just below policy thresholds | `MEDIUM` | Risk Signal (`THRESHOLD_PROXIMITY`) |
| 18 | `UNUSUAL_AMOUNT` | `STATISTICAL` | Flags statistical billing outliers $> 2.5\sigma$ from historical mean | `MEDIUM` | Risk Signal (`UNUSUAL_AMOUNT`) |

---

## 9. Test Suite & Coverage Metrics

The test suite contains **100 passing automated tests** across 5 layers:
- **Database & Schema:** 20 tests (constraints, triggers, relationships, tenant isolation, seed validation)
- **Unit Controls:** 35 tests (vendor, PO, receipt, financial, duplicate, and risk controls)
- **Application Services:** 7 tests (decision engine, approval routing, facade methods)
- **Integration Scenarios (A through O):** 15 tests (end-to-end control execution for all 15 scenarios)
- **FastAPI REST API & Workflows:** 23 tests (auth, RBAC, invoices, vendors, POs, receipts, exceptions, approvals, payables, golden transaction, dashboard KPIs, audit trail)

### Coverage Report Summary
- Total Source Statements Tested: 2,091
- Application DTOs & Schemas: 100%
- Application Services: 92%
- Domain Controls & Decisions: 92%
- Repositories: 91%
- REST API Layer: 86%
- **Overall Code Coverage: 91%**

---

## 10. Phase 3: REST API Layer, RBAC & The Golden Transaction

Phase 3 implements the production-grade **FastAPI REST API layer**, exposing full AP operations, scenario inspection, real-time KPI aggregations, and strict RBAC enforcement.

### 10.1 Authentication & Multi-Persona RBAC
The system supports dual-mode identity resolution:
1. **Production Bearer JWT Tokens:** Formatted as `Authorization: Bearer <jwt_token>` issued by `/api/v1/auth/login`.
2. **Finathon Demo Persona Header:** Formatted as `X-Demo-User-Email: <user_email>`. Allows instant UI switching between predefined corporate personas:
   - `priya.nair@apexfin.in` — AP Clerk (Data entry, invoice revision uploads)
   - `vikram.malhotra@apexfin.in` — Procurement Manager (PO review, vendor exception resolution)
   - `sneha.kulkarni@apexfin.in` — Receiving Specialist (Goods receipt verification)
   - `ananya.rao@apexfin.in` — Finance Manager (Approvals up to ₹50,000, exception waivers)
   - `rohan.verma@apexfin.in` — Finance Head / CFO (High-value approvals, policy configuration)
   - `sunita.mehta@apexfin.in` — Auditor (Read-only immutable audit trail and control evidence inspection)
   - `rajesh.sharma@apexfin.in` — System Administrator (Full configuration)

### 10.2 The Golden Transaction: `PayableWorkflowService`
The Core Invariant is strictly upheld in code:
$$\text{RECEIVED INVOICE} \ne \text{PAYABLE OBLIGATION}$$

The Control Engine never creates a payable. A payable obligation is created **strictly** via the **Golden Transaction** in `PayableWorkflowService.decide_approval(...)`:
```
Manager Approves Invoice
   ↓
Verify Actor Role & Permission (FINANCE_MANAGER, FINANCE_HEAD, ADMIN)
   ↓
Verify Invoice Status is AWAITING_APPROVAL
   ↓
Record Approval Decision (APPROVED) with Timestamp & Comments
   ↓
Verify No Unresolved Exceptions Exist (Zero Open/In-Review Exceptions Gate)
   ↓
Verify All Required Tier Approvals Completed
   ↓
Atomically Insert ap.payable_ledger Entry (status: OPEN)
   ↓
Atomically Transition ap.invoices Status to PAYABLE_CREATED
   ↓
Write Audit Event PAYABLE_CREATED to Immutable Audit Trail
```

Subsequent disbursement is recorded via `PayableWorkflowService.record_disbursement(...)`:
- Verifies payable is `OPEN` or `PARTIALLY_PAID`.
- Prevents overpayment (`amount <= remaining_balance`).
- Creates `ap.payments` entry.
- Transitions payable to `PARTIALLY_PAID` or `PAID`.
- If fully settled, transitions invoice status to `PAID`.

### 10.3 API Endpoint Catalog

| Method | Endpoint | Description | Required Role(s) |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | Authenticate and obtain JWT access token | Public |
| `GET` | `/api/v1/auth/me` | Current authenticated user profile and roles | Authenticated |
| `GET` | `/api/v1/auth/demo-users` | List demo personas for quick Finathon switching | Public |
| `GET` | `/api/v1/invoices` | List invoices with status, vendor, search filters | Authenticated |
| `GET` | `/api/v1/invoices/{id}` | Detailed aggregate view of invoice, revisions, items | Authenticated |
| `POST` | `/api/v1/invoices` | Ingest new invoice shell | AP Clerk, Admin |
| `POST` | `/api/v1/invoices/{id}/control-runs` | Trigger deterministic 18-rule control run | AP Clerk, Finance Mgr, Admin |
| `GET` | `/api/v1/invoices/{id}/control-results` | Fetch evaluation results from latest control run | Authenticated |
| `GET` | `/api/v1/vendors` | List vendor master catalog | Authenticated |
| `GET` | `/api/v1/vendors/{id}` | Full vendor detail with bank fingerprint | Authenticated |
| `GET` | `/api/v1/purchase-orders` | List purchase orders with line items | Authenticated |
| `GET` | `/api/v1/purchase-orders/{id}` | Detailed PO view | Authenticated |
| `GET` | `/api/v1/receipts` | List goods/service receiving receipts | Authenticated |
| `GET` | `/api/v1/controls/catalog` | Catalog of all 18 registered control rules | Authenticated |
| `GET` | `/api/v1/exceptions` | List open/resolved exceptions | Authenticated |
| `POST` | `/api/v1/exceptions/{id}/resolve` | Resolve or waive exception with audit reason | Procurement Mgr, Finance Mgr, Admin |
| `GET` | `/api/v1/approvals` | List approval requests with status filter | Authenticated |
| `POST` | `/api/v1/approvals/{id}/decide` | **The Golden Transaction**: Approve/Reject invoice | Finance Mgr, Finance Head, Admin |
| `GET` | `/api/v1/payables` | List committed general liabilities | Authenticated |
| `GET` | `/api/v1/payables/{id}` | Detailed payable ledger entry with disbursements | Authenticated |
| `POST` | `/api/v1/payables/{id}/payments` | Record disbursement against payable | Finance Mgr, Finance Head, Admin |
| `GET` | `/api/v1/dashboard/kpis` | Real-time AP metrics, 3-way match pass rate, liability | Authenticated |
| `GET` | `/api/v1/dashboard/scenarios` | Real-time status matrix for Scenarios A through O | Authenticated |
| `GET` | `/api/v1/audit/logs` | Immutable audit trail query with entity/action filters | Auditor, Admin |

### 10.4 Starting the Server & Documentation

To launch the FastAPI ASGI server:
```powershell
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive documentation is automatically generated:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **Health Check:** `http://localhost:8000/health`


